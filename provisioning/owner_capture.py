"""Admission for OWNER projection collectors, including their manual Python callers."""
from contextlib import contextmanager
from contextvars import ContextVar
from functools import lru_cache, wraps
import os
from pathlib import Path
import threading

from control.capture_gate import CURRENT, Gate, external_operation, require


INSTALLED_GATE = Path('/var/lib/family-connect/capture/owner-collectors')
SCOPE = ContextVar('owner_collector_admission', default=None)


@lru_cache(maxsize=8)
def gate_for(directory):
    return Gate(directory)


def configured_gate():
    directory = os.environ.get('FC_OWNER_CAPTURE_GATE') or None
    if os.path.lexists(INSTALLED_GATE) and (os.geteuid() == 0 or INSTALLED_GATE.stat().st_uid == os.geteuid()):
        require(directory in (None, str(INSTALLED_GATE)), 'OWNER_CAPTURE_CONFIGURATION_CHANGED')
        directory = str(INSTALLED_GATE)
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
