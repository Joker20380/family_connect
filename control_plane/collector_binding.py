"""Mandatory role-specific admission for the installed OWNER user collectors."""
from contextlib import contextmanager
from contextvars import ContextVar
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import threading

from control.capture_gate import CURRENT, Gate, GateError, external_operation, require


INSTALLED_APP = Path('/home/joker/PycharmProjects/family_connect')
INSTALLED_BINDING = Path('/etc/family-connect/owner-user-collectors.json')
BINDING_UID = 0
BASELINE = 'owner-user-collectors-mandatory-v1'
ROLES = ('inventory', 'probe')
SOURCE_NAMES = (
    'control/capture_gate.py', 'control/friends/__init__.py', 'control/friends/pseudonyms.py',
    'control_plane/collector_binding.py', 'control_plane/collector_admission.py',
    'control_plane/collect_inventory.py', 'control_plane/collect_technical_metadata.py',
    'control_plane/monitor_inventory.py', 'control_plane/probe_network.py',
    'control_plane/apps/__init__.py', 'control_plane/apps/console/__init__.py',
    'control_plane/apps/console/collector.py', 'control_plane/apps/console/network_probe.py',
    *('control_plane/apps/console/' + name + '_collector.py' for name in
      ('metrics', 'transport', 'subscription', 'technical_metadata')),
)
SCOPE = ContextVar('owner_user_collector_admission', default=None)


def read_regular(path, owner, mode=None, limit=256 * 1024):
    require(all(not parent.is_symlink() for parent in path.parents), 'COLLECTOR_BINDING_PATH')
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    with os.fdopen(descriptor, 'rb') as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_uid == owner and before.st_nlink == 1 and
                not before.st_mode & 0o7002 and 0 <= before.st_size <= limit and
                (mode is None or stat.S_IMODE(before.st_mode) == mode), 'COLLECTOR_BINDING_PERMISSIONS')
        raw = stream.read(limit + 1)
        after = os.fstat(stream.fileno())
    fields = ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns', 'st_mode', 'st_uid', 'st_nlink')
    require(len(raw) == before.st_size and all(getattr(before, name) == getattr(after, name) for name in fields),
            'COLLECTOR_BINDING_CHANGED')
    return raw


def installed_binding():
    raw = read_regular(INSTALLED_BINDING, BINDING_UID, 0o644, 16384)
    binding = json.loads(raw)
    require(type(binding) is dict and set(binding) == {'schema', 'baseline', 'application', 'uid', 'sources', 'gates'} and
            type(binding['schema']) is int and binding['schema'] == 1 and binding['baseline'] == BASELINE and
            binding['application'] == str(INSTALLED_APP) and type(binding['uid']) is int and
            binding['uid'] == os.geteuid(), 'COLLECTOR_BINDING_INVALID')
    require(raw == (json.dumps(binding, sort_keys=True, separators=(',', ':')) + '\n').encode(),
            'COLLECTOR_BINDING_ENCODING')
    sources = binding['sources']
    require(type(sources) is dict and set(sources) == set(SOURCE_NAMES) and
            all(type(value) is str and re.fullmatch('[a-f0-9]{64}', value) for value in sources.values()),
            'COLLECTOR_SOURCE_COVERAGE')
    for name, expected in sources.items():
        require(hashlib.sha256(read_regular(INSTALLED_APP / name, binding['uid'])).hexdigest() == expected,
                'COLLECTOR_SOURCE_CHANGED')
    gates = binding['gates']
    require(type(gates) is dict and set(gates) == set(ROLES), 'COLLECTOR_ROLE_COVERAGE')
    for entry in gates.values():
        require(type(entry) is dict and set(entry) == {'directory', 'pins'} and
                type(entry['directory']) is str and Path(entry['directory']).is_absolute() and
                '..' not in Path(entry['directory']).parts, 'COLLECTOR_GATE_BINDING')
        require(type(entry['pins']) is dict and set(entry['pins']) == {'.', 'pending', 'admission.lock', 'operations.lock'} and
                all(type(value) is list and len(value) == 2 and
                    all(type(number) is int and number >= 0 for number in value) for value in entry['pins'].values()),
                'COLLECTOR_GATE_PINS')
    require(gates['inventory']['directory'] != gates['probe']['directory'], 'COLLECTOR_ROLE_ALIAS')
    return binding


@lru_cache(maxsize=8)
def gate_for(directory):
    return Gate(directory)


def configured_gate(role):
    try:
        require(role in ROLES, 'COLLECTOR_ROLE')
        directory = os.environ.get('FC_CONTROL_CAPTURE_GATE') or None
        source = Path(__file__).absolute()
        if INSTALLED_APP in (source.parent.parent, source.resolve().parent.parent):
            entry = installed_binding()['gates'][role]
            require(directory in (None, entry['directory']), 'COLLECTOR_CONFIGURATION_CHANGED')
            gate = gate_for(entry['directory'])
            require(gate.pins == {name: tuple(value) for name, value in entry['pins'].items()},
                    'COLLECTOR_GATE_REPLACED')
            with gate.opened():
                return gate
        return gate_for(directory)
    except GateError:
        raise
    except (OSError, ValueError, TypeError, RecursionError):
        raise GateError('COLLECTOR_BINDING_UNAVAILABLE') from None


@contextmanager
def operation(role):
    gate = configured_gate(role)
    previous = SCOPE.get()
    if gate.directory is not None:
        if previous is None:
            require(CURRENT.get() is None, 'COLLECTOR_FOREIGN_CONTEXT')
        else:
            require(previous['active'] and previous['pid'] == os.getpid() and
                    previous['thread'] == threading.get_ident() and previous['role'] == role and
                    previous['operation'] is CURRENT.get(), 'COLLECTOR_STALE_CONTEXT')
    with gate.operation() as admitted, external_operation():
        if previous is not None or gate.directory is None:
            yield admitted
            return
        scope = dict(active=True, pid=os.getpid(), thread=threading.get_ident(), role=role, operation=admitted)
        token = SCOPE.set(scope)
        try:
            yield admitted
        finally:
            scope['active'] = False
            SCOPE.reset(token)
