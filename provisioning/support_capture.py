"""Optional support-worker admission, independent of the panel's IPC request lifetime."""
from functools import wraps

from control.capture_gate import external_operation


def admitted(function):
    @wraps(function)
    def guarded(self, *args, **kwargs):
        with self.capture_gate.operation(), external_operation():
            return function(self, *args, **kwargs)
    return guarded
