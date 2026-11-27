"""Admission for complete operator-side collector cycles and manual entrypoints."""
from contextlib import contextmanager
import fcntl
import os
import sys

from control.capture_gate import Busy, GateError
from control_plane.collector_binding import operation


@contextmanager
def cycle_lock(base, name):
    collision = None
    role = {'monitor.lock': 'inventory', 'network-probe.lock': 'probe'}[name]
    with operation(role):
        local = base / '.local'
        if any(parent.is_symlink() for parent in (local, *local.parents)):
            raise ValueError('Unsafe local directory')
        local.mkdir(mode=0o700, exist_ok=True)
        descriptor = os.open(local / name, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        with os.fdopen(descriptor, 'w') as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                collision = error
            else:
                yield
    if collision is not None:
        raise collision


def run_cli(callback):
    try:
        return callback() or 0
    except Busy:
        print('CAPTURE_BUSY', file=sys.stderr)
        return 75
    except GateError:
        print('CAPTURE_UNAVAILABLE', file=sys.stderr)
        return 1
