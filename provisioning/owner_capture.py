"""Admission for OWNER projection collectors, including their manual Python callers."""
from contextlib import contextmanager
from contextvars import ContextVar
from functools import lru_cache, wraps
import json
import os
from pathlib import Path
import stat
import threading

from control.capture_gate import CURRENT, Gate, GateError, external_operation, require


INSTALLED_GATE = Path('/var/lib/fc-support-bindings/capture-owner-collectors')
INSTALLED_APP = Path('/opt/family-connect-support/app')
INSTALLED_BINDING = Path('/opt/family-connect-support/owner-collectors-capture.json')
SCOPE = ContextVar('owner_collector_admission', default=None)


@lru_cache(maxsize=8)
def gate_for(directory):
    try:
        return Gate(directory)
    except OSError:
        raise GateError('OWNER_CAPTURE_UNAVAILABLE') from None


def installed_pins():
    try:
        require(all(not parent.is_symlink() for parent in INSTALLED_BINDING.parents),
                'OWNER_CAPTURE_BINDING_PATH')
        descriptor = os.open(INSTALLED_BINDING, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
        with os.fdopen(descriptor, 'rb') as stream:
            info = os.fstat(stream.fileno())
            require(stat.S_ISREG(info.st_mode) and info.st_uid == os.geteuid() and
                    stat.S_IMODE(info.st_mode) == 0o600 and info.st_nlink == 1 and
                    0 < info.st_size <= 4096, 'OWNER_CAPTURE_BINDING_PERMISSIONS')
            raw = stream.read(4097)
        binding = json.loads(raw)
        require(type(binding) is dict and set(binding) == {'schema', 'application', 'gate', 'pins'} and
                type(binding['schema']) is int and binding['schema'] == 1 and
                binding['application'] == str(INSTALLED_APP) and binding['gate'] == str(INSTALLED_GATE),
                'OWNER_CAPTURE_BINDING_INVALID')
        pins = binding['pins']
        require(type(pins) is dict and set(pins) == {'.', 'admission.lock', 'operations.lock', 'pending'} and
                all(type(value) is list and len(value) == 2 and
                    all(type(number) is int and number >= 0 for number in value) for value in pins.values()),
                'OWNER_CAPTURE_BINDING_INVALID')
        require(raw == (json.dumps(binding, sort_keys=True, separators=(',', ':')) + '\n').encode(),
                'OWNER_CAPTURE_BINDING_ENCODING')
        return {name: tuple(value) for name, value in pins.items()}
    except GateError:
        raise
    except (OSError, ValueError, TypeError, RecursionError):
        raise GateError('OWNER_CAPTURE_BINDING_UNAVAILABLE') from None


def configured_gate():
    directory = os.environ.get('FC_OWNER_CAPTURE_GATE') or None
    source = Path(__file__).absolute()
    if INSTALLED_APP in (source.parent.parent, source.resolve().parent.parent):
        require(directory in (None, str(INSTALLED_GATE)), 'OWNER_CAPTURE_CONFIGURATION_CHANGED')
        pins = installed_pins()
        gate = gate_for(str(INSTALLED_GATE))
        require(gate.pins == pins, 'OWNER_CAPTURE_BINDING_CHANGED')
        try:
            with gate.opened():
                return gate
        except GateError:
            raise
        except OSError:
            raise GateError('OWNER_CAPTURE_UNAVAILABLE') from None
    return gate_for(directory)


@contextmanager
def operation():
    gate = configured_gate()
    previous = SCOPE.get()
    if gate.directory is not None:
        if previous is None:
            require(CURRENT.get() is None, 'OWNER_CAPTURE_FOREIGN_CONTEXT')
        else:
            require(previous['active'] and previous['pid'] == os.getpid() and
                    previous['thread'] == threading.get_ident() and
                    previous['operation'] is CURRENT.get(), 'OWNER_CAPTURE_STALE_CONTEXT')
    with gate.operation() as admitted, external_operation():
        if previous is not None or gate.directory is None:
            yield admitted
            return
        scope = dict(active=True, pid=os.getpid(), thread=threading.get_ident(), operation=admitted)
        token = SCOPE.set(scope)
        try:
            yield admitted
        finally:
            scope['active'] = False
            SCOPE.reset(token)


def admitted(function):
    @wraps(function)
    def wrapped(*arguments, **keywords):
        with operation():
            return function(*arguments, **keywords)
    return wrapped
