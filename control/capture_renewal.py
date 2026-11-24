"""Read-only renewal settlement guard; success of one RPC is not transaction settlement."""
from contextlib import contextmanager, ExitStack
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat

from .capture_gate import Busy, identity, require, safe


def absolute(value):
    require(type(value) is str and value.startswith('/') and not value.startswith('//') and
            value == os.path.normpath(value) and value != '/' and '\x00' not in value, 'RENEWAL_PATH')
    return value


def validate(binding):
    require(type(binding) is dict and set(binding) == {'config', 'config_sha256', 'state', 'pins'}, 'RENEWAL_BINDING')
    absolute(binding['config'])
    absolute(binding['state'])
    require(type(binding['config_sha256']) is str and re.fullmatch('[0-9a-f]{64}', binding['config_sha256']),
            'RENEWAL_CONFIG_SHA')
    require(type(binding['pins']) is dict and set(binding['pins']) == {'.', 'operation.lock'}, 'RENEWAL_PINS')
    for pair in binding['pins'].values():
        require(type(pair) is list and len(pair) == 2 and
                all(type(number) is int and number >= 0 for number in pair) and pair[1] > 0, 'RENEWAL_PIN')
    require(binding['pins']['.'] != binding['pins']['operation.lock'], 'RENEWAL_PIN_ALIAS')
    return binding


def opened(stack, spelling, *, directory=False):
    parts = Path(absolute(spelling)).parts[1:]
    descriptor = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    stack.callback(os.close, descriptor)
    for index, part in enumerate(parts):
        flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK
        if directory or index < len(parts) - 1:
            flags |= os.O_DIRECTORY
        descriptor = os.open(part, flags, dir_fd=descriptor)
        stack.callback(os.close, descriptor)
    return descriptor


def unique(pairs):
    result = {}
    for name, value in pairs:
        require(name not in result, 'RENEWAL_DUPLICATE_FIELD')
        result[name] = value
    return result


def stamp(info):
    return info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_gid, info.st_nlink, info.st_size, info.st_mtime_ns, info.st_ctime_ns


class RenewalState:
    def __init__(self, binding):
        self.binding = json.loads(json.dumps(validate(binding)))
        self.snapshot = None

    def configuration(self):
        with ExitStack() as stack:
            descriptor = opened(stack, self.binding['config'])
            before = os.fstat(descriptor)
            require(stat.S_ISREG(before.st_mode) and before.st_uid == os.geteuid() and
                    stat.S_IMODE(before.st_mode) == 0o600 and before.st_nlink == 1 and
                    0 < before.st_size <= 65536, 'RENEWAL_CONFIG_FILE')
            raw = os.pread(descriptor, 65537, 0)
            require(len(raw) == before.st_size and stamp(before) == stamp(os.fstat(descriptor)) and
                    hashlib.sha256(raw).hexdigest() == self.binding['config_sha256'], 'RENEWAL_CONFIG_CHANGED')
            config = json.loads(raw, object_pairs_hook=unique)
            require(type(config) is dict and type(config.get('schema')) is int and config['schema'] == 1 and
                    config.get('role') in ('RU', 'NL') and config.get('state') == self.binding['state'], 'RENEWAL_CONFIG_STATE')
            return stamp(before)

    @contextmanager
    def inspected(self):
        with ExitStack() as stack:
            config = self.configuration()
            directory = opened(stack, self.binding['state'], directory=True)
            safe(os.fstat(directory), True)
            require(list(identity(os.fstat(directory))) == self.binding['pins']['.'], 'RENEWAL_STATE_REPLACED')
            lock = os.open('operation.lock', os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK,
                           dir_fd=directory)
            stack.callback(os.close, lock)
            safe(os.fstat(lock))
            require(list(identity(os.fstat(lock))) == self.binding['pins']['operation.lock'], 'RENEWAL_LOCK_REPLACED')
            yield directory, lock, config

    def quiet(self, directory):
        before = stamp(os.fstat(directory))
        with os.scandir(directory) as entries:
            names = []
            for entry in entries:
                require(len(names) < 3 and entry.name in {'operation.lock', 'completed.json', 'archive'},
                        'RENEWAL_TRANSACTION_UNSETTLED')
                names.append(entry.name)
        require('operation.lock' in names, 'RENEWAL_LOCK_MISSING')
        observed = {}
        for name in sorted(names):
            info = os.stat(name, dir_fd=directory, follow_symlinks=False)
            require(info.st_uid == os.geteuid() and stat.S_IMODE(info.st_mode) ==
                    (0o700 if name == 'archive' else 0o600), 'RENEWAL_STATE_PERMISSIONS')
            require(stat.S_ISDIR(info.st_mode) if name == 'archive' else
                    stat.S_ISREG(info.st_mode) and info.st_nlink == 1, 'RENEWAL_STATE_TYPE')
            observed[name] = stamp(info)
        require(before == stamp(os.fstat(directory)), 'RENEWAL_STATE_CHANGED')
        return before, observed

    def verify(self):
        require(self.snapshot is not None, 'RENEWAL_NOT_HELD')
        with self.inspected() as (directory, lock, config):
            require((config, self.quiet(directory)) == self.snapshot, 'RENEWAL_STATE_CHANGED')

    @contextmanager
    def hold(self):
        require(self.snapshot is None, 'RENEWAL_ALREADY_HELD')
        with self.inspected() as (directory, lock, config):
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise Busy('RENEWAL_OPERATION_RUNNING') from None
            self.snapshot = config, self.quiet(directory)
            try:
                self.verify()
                yield self
                self.verify()
            finally:
                self.snapshot = None
