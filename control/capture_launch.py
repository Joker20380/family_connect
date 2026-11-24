"""Pinned same-host guardian launch; trusted coordinator entrypoint, never a deployment tool."""
from contextlib import contextmanager, ExitStack
import fcntl
import hashlib
import io
import json
import os
from pathlib import Path
import re
import resource
import signal
import socket
import stat
import subprocess
import sys
import time
import zipfile

from .capture_gate import Gate, GateError, require
from . import capture_group as group

SOURCES = ('control/capture_gate.py', 'control/capture_group.py', 'control/capture_launch.py')
MAIN = b'from control.capture_launch import guardian_main\nraise SystemExit(guardian_main())\n'
SEALS = fcntl.F_SEAL_WRITE | fcntl.F_SEAL_GROW | fcntl.F_SEAL_SHRINK | fcntl.F_SEAL_SEAL
NAMESPACES = ('mnt', 'pid', 'user', 'time')
LIMIT = 262144


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def sha(value):
    require(type(value) is str and re.fullmatch('[0-9a-f]{64}', value), 'LAUNCH_SHA')
    return value


def absolute(value):
    require(type(value) is str and value.startswith('/') and not value.startswith('//') and
            value == os.path.normpath(value) and '\x00' not in value and value != '/', 'LAUNCH_PATH')
    return value


def read_file(spelling, *, private=False):
    parts = Path(absolute(spelling)).parts[1:]
    with ExitStack() as stack:
        directory = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
        stack.callback(os.close, directory)
        for part in parts[:-1]:
            directory = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                                dir_fd=directory)
            stack.callback(os.close, directory)
        descriptor = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK,
                             dir_fd=directory)
        stack.callback(os.close, descriptor)
        before = os.fstat(descriptor)
        require(stat.S_ISREG(before.st_mode) and before.st_uid in (0, os.geteuid()) and before.st_nlink == 1 and
                not before.st_mode & 0o7022 and 0 < before.st_size <= LIMIT, 'LAUNCH_FILE')
        if private:
            require(before.st_uid == os.geteuid() and stat.S_IMODE(before.st_mode) == 0o600, 'LAUNCH_PRIVATE')
        with os.fdopen(os.dup(descriptor), 'rb') as source:
            raw = source.read(LIMIT + 1)
        after = os.fstat(descriptor)
        require(len(raw) == before.st_size and
                (before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
                (after.st_size, after.st_mtime_ns, after.st_ctime_ns), 'LAUNCH_FILE_CHANGED')
        return raw


def sealed(stack, raw):
    descriptor = os.memfd_create('fc-guardian', os.MFD_CLOEXEC | os.MFD_ALLOW_SEALING)
    stack.callback(os.close, descriptor)
    with os.fdopen(os.dup(descriptor), 'wb') as output:
        output.write(raw)
    os.fchmod(descriptor, 0o444)
    fcntl.fcntl(descriptor, fcntl.F_ADD_SEALS, SEALS)
    os.lseek(descriptor, 0, os.SEEK_SET)
    return descriptor


def read_sealed(descriptor):
    require(fcntl.fcntl(descriptor, fcntl.F_GET_SEALS) & SEALS == SEALS, 'LAUNCH_UNSEALED')
    size = os.fstat(descriptor).st_size
    require(0 < size <= LIMIT, 'LAUNCH_SEALED_BOUNDS')
    raw = os.pread(descriptor, LIMIT + 1, 0)
    require(len(raw) == size, 'LAUNCH_SEALED_BOUNDS')
    return raw


def namespaces():
    result = {}
    for name in NAMESPACES:
        info = os.stat('/proc/self/ns/' + name)
        result[name] = [info.st_dev, info.st_ino]
    return result


def mappings():
    return {name: digest(Path('/proc/self/' + name + '_map').read_bytes()) for name in ('uid', 'gid')}


def runtime_sha(descriptor):
    with os.fdopen(os.dup(descriptor), 'rb') as source:
        source.seek(0)
        return hashlib.file_digest(source, 'sha256').hexdigest()


def parse(raw):
    try:
        return json.loads(raw, object_pairs_hook=group.unique)
    except (ValueError, UnicodeError):
        raise GateError('LAUNCH_JSON') from None


def validate(binding):
    require(type(binding) is dict and set(binding) ==
            {'schema', 'source_sha256', 'runtime_sha256', 'namespaces', 'mappings', 'coordinator', 'guardians'},
            'LAUNCH_BINDING')
    require(type(binding['schema']) is int and binding['schema'] == 1, 'LAUNCH_SCHEMA')
    sha(binding['source_sha256'])
    sha(binding['runtime_sha256'])
    require(type(binding['namespaces']) is dict and set(binding['namespaces']) == set(NAMESPACES), 'LAUNCH_NAMESPACES')
    for pair in binding['namespaces'].values():
        require(type(pair) is list and len(pair) == 2 and all(type(number) is int and number >= 0 for number in pair)
                and pair[1] > 0, 'LAUNCH_NAMESPACE_PIN')
    require(type(binding['mappings']) is dict and set(binding['mappings']) == {'uid', 'gid'}, 'LAUNCH_MAPPINGS')
    for value in binding['mappings'].values():
        sha(value)
    require(type(binding['coordinator']) is list and len(binding['coordinator']) == 2 and
            all(type(number) is int and 0 <= number < 2**32 - 1 for number in binding['coordinator']), 'LAUNCH_COORDINATOR')
    guardians = binding['guardians']
    require(type(guardians) is list and 2 <= len(guardians) <= 8, 'LAUNCH_GUARDIANS')
    all_pins = []
    for item in guardians:
        require(type(item) is dict and set(item) == {'uid', 'gid', 'groups', 'gate', 'pins'}, 'LAUNCH_GUARDIAN')
        require(all(type(item[name]) is int and 0 < item[name] < 2**32 - 1 for name in ('uid', 'gid')), 'LAUNCH_IDENTITY')
        require(type(item['groups']) is list and len(item['groups']) <= 32 and
                all(type(number) is int and 0 < number < 2**32 - 1 for number in item['groups']) and
                item['groups'] == sorted(set(item['groups'])), 'LAUNCH_GROUPS')
        absolute(item['gate'])
        all_pins.extend(tuple(pair) for pair in group.pins(item['pins']).values())
    require(len({item['gate'] for item in guardians}) == len(guardians) and
            len(set(all_pins)) == len(all_pins), 'LAUNCH_GATE_ALIAS')
    return binding


def archive(raw):
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as source:
            require(len(source.infolist()) == len(SOURCES) + 2 and
                    set(source.namelist()) == {*SOURCES, 'control/', '__main__.py'}, 'LAUNCH_ARCHIVE_MEMBERS')
            require(all(info.file_size <= LIMIT and not info.flag_bits & 1 and
                        info.compress_type == zipfile.ZIP_STORED for info in source.infolist()), 'LAUNCH_ARCHIVE_BOUNDS')
            require(source.read('__main__.py') == MAIN and source.read('control/') == b'', 'LAUNCH_ARCHIVE_ENTRY')
            for name in SOURCES:
                require(source.read(name), 'LAUNCH_ARCHIVE_EMPTY')
    except (ValueError, zipfile.BadZipFile):
        raise GateError('LAUNCH_ARCHIVE') from None


def trusted_entrypoint(source_sha256):
    origin = getattr(__loader__, 'archive', '')
    require(re.fullmatch(r'/proc/self/fd/[0-9]+', origin), 'LAUNCH_TRUSTED_ENTRYPOINT')
    require(all(getattr(sys.modules[name[:-3].replace('/', '.')].__loader__, 'archive', None) == origin
                for name in SOURCES), 'LAUNCH_COORDINATOR_IMPORTS')
    require(digest(read_sealed(int(origin.rsplit('/', 1)[1]))) == source_sha256, 'LAUNCH_COORDINATOR_SOURCE')


def local_binding(binding):
    require(binding['namespaces'] == namespaces() and binding['mappings'] == mappings(), 'LAUNCH_HOST_BINDING')
    require(list((os.getuid(), os.getgid())) == binding['coordinator'] and
            len(set(os.getresuid())) == len(set(os.getresgid())) == 1, 'LAUNCH_COORDINATOR_IDENTITY')
    if os.geteuid() != 0:
        require(all(item['uid'] == os.geteuid() and item['gid'] == os.getegid() and
                    item['groups'] == sorted(os.getgroups()) for item in binding['guardians']), 'LAUNCH_PRIVILEGE')
    else:
        trusted_entrypoint(binding['source_sha256'])


@contextmanager
def launch(binding_path, binding_sha256, source_path):
    children, participants = [], []
    with ExitStack() as stack:
        try:
            raw = read_file(binding_path, private=True)
            require(digest(raw) == sha(binding_sha256), 'LAUNCH_BINDING_SHA')
            binding = validate(parse(raw))
            local_binding(binding)
            source = read_file(source_path)
            require(digest(source) == binding['source_sha256'], 'LAUNCH_SOURCE_SHA')
            archive(source)
            source_fd = sealed(stack, source)
            executable = os.open('/proc/self/exe', os.O_RDONLY | os.O_CLOEXEC)
            stack.callback(os.close, executable)
            require(not os.fstat(executable).st_mode & 0o7022, 'LAUNCH_RUNTIME_PERMISSIONS')
            require(runtime_sha(executable) == binding['runtime_sha256'], 'LAUNCH_RUNTIME_SHA')
            deadline = time.monotonic_ns() + 3 * group.NANOSECONDS
            for item in binding['guardians']:
                parent, child = group.channel_pair()
                stack.callback(parent.close)
                stack.callback(child.close)
                request = dict(binding=binding, selected=item, coordinator=list(group.identity()),
                               binding_sha256=binding_sha256)
                request_fd = sealed(stack, json.dumps(request, sort_keys=True, allow_nan=False).encode())
                options = dict(user=item['uid'], group=item['gid'], extra_groups=item['groups']) if os.geteuid() == 0 else {}
                process = subprocess.Popen(['/proc/self/fd/' + str(executable), '-I', '-S', '-B',
                    '/proc/self/fd/' + str(source_fd), str(source_fd), str(request_fd), str(child.fileno())],
                    executable='/proc/self/fd/' + str(executable), cwd='/', env={'LANG': 'C.UTF-8'},
                    close_fds=True, pass_fds=(source_fd, request_fd, child.fileno(), executable),
                    stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **options)
                children.append(process)
                child.close()
                participants.append(group.Participant(parent, (process.pid, item['uid'], item['gid']), group.pins(item['pins'])))
            for participant in participants:
                group.wait([participant.channel], deadline)
                ready = group.receive(participant.channel, participant.identity)
                require(ready == dict(status='READY', binding_sha256=binding_sha256), 'LAUNCH_READY')
            yield participants
        finally:
            for participant in participants:
                participant.channel.close()
            for process in children:
                if process.poll() is None:
                    process.terminate()
            for process in children:
                try:
                    process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=1)


def guardian_main():
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    try:
        require(len(sys.argv) == 4 and all(value.isascii() and value.isdecimal() for value in sys.argv[1:]), 'LAUNCH_ARGV')
        source_fd, request_fd, channel_fd = map(int, sys.argv[1:])
        require(len({source_fd, request_fd, channel_fd}) == 3 and min(source_fd, request_fd, channel_fd) > 2, 'LAUNCH_FDS')
        require(signal.getsignal(signal.SIGALRM) == signal.SIG_DFL and
                signal.SIGALRM not in signal.pthread_sigmask(signal.SIG_BLOCK, []) and
                signal.getitimer(signal.ITIMER_REAL) == (0, 0), 'LAUNCH_ALARM')
        signal.setitimer(signal.ITIMER_REAL, 3)
        request = parse(read_sealed(request_fd))
        require(type(request) is dict and set(request) == {'binding', 'selected', 'coordinator', 'binding_sha256'}, 'LAUNCH_REQUEST')
        binding = validate(request['binding'])
        sha(request['binding_sha256'])
        item = request['selected']
        require(item in binding['guardians'] and os.getresuid() == (item['uid'],) * 3 and
                os.getresgid() == (item['gid'],) * 3 and sorted(os.getgroups()) == item['groups'], 'LAUNCH_CHILD_IDENTITY')
        require(type(request['coordinator']) is list and len(request['coordinator']) == 3 and
                type(request['coordinator'][0]) is int and request['coordinator'][0] > 0 and
                request['coordinator'][1:] == binding['coordinator'], 'LAUNCH_PARENT_IDENTITY')
        require(binding['namespaces'] == namespaces() and binding['mappings'] == mappings(), 'LAUNCH_CHILD_HOST')
        require(digest(read_sealed(source_fd)) == binding['source_sha256'], 'LAUNCH_CHILD_SOURCE')
        with open('/proc/self/exe', 'rb') as executable:
            require(hashlib.file_digest(executable, 'sha256').hexdigest() == binding['runtime_sha256'], 'LAUNCH_CHILD_RUNTIME')
        gate = Gate(item['gate'])
        require(group.pins(gate.pins) == group.pins(item['pins']), 'LAUNCH_CHILD_GATE')
        channel = socket.socket(fileno=channel_fd)
        group.configure(channel)
        group.send(channel, dict(status='READY', binding_sha256=request['binding_sha256']))
        signal.setitimer(signal.ITIMER_REAL, 0)
        group.serve(gate, channel, request['coordinator'], item['pins'])
        return 0
    except (OSError, ValueError, TypeError, KeyError):
        return 1
