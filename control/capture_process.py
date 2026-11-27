"""Linux kernel kill deadline for dedicated capture processes, including blocked cleanup."""
from contextlib import contextmanager
import ctypes
import math
import resource
import signal
import sys


class SignalEvent(ctypes.Structure):
    _fields_ = [('value', ctypes.c_void_p), ('signo', ctypes.c_int), ('notify', ctypes.c_int),
               ('padding', ctypes.c_char * (64 - ctypes.sizeof(ctypes.c_void_p) - 8))]


class TimeSpec(ctypes.Structure):
    _fields_ = [('seconds', ctypes.c_long), ('nanoseconds', ctypes.c_long)]


class TimerSpec(ctypes.Structure):
    _fields_ = [('interval', TimeSpec), ('value', TimeSpec)]


@contextmanager
def hard_deadline(seconds):
    if sys.platform != 'linux' or type(seconds) not in (float, int) or not math.isfinite(seconds) or not 0 < seconds <= 121:
        raise ValueError('FLEET_PROCESS_DEADLINE')
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    library = ctypes.CDLL(None, use_errno=True)
    library.timer_create.argtypes = (ctypes.c_int, ctypes.POINTER(SignalEvent), ctypes.POINTER(ctypes.c_void_p))
    library.timer_settime.argtypes = (ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(TimerSpec), ctypes.c_void_p)
    library.timer_delete.argtypes = (ctypes.c_void_p,)
    event = SignalEvent(signo=signal.SIGKILL, notify=0)
    timer = ctypes.c_void_p()
    if library.timer_create(1, ctypes.byref(event), ctypes.byref(timer)) != 0:
        raise OSError('FLEET_KERNEL_TIMER_UNAVAILABLE')
    nanoseconds = max(1, math.ceil(seconds * 1_000_000_000))
    spec = TimerSpec(value=TimeSpec(*divmod(nanoseconds, 1_000_000_000)))
    original = None
    try:
        if library.timer_settime(timer, 0, ctypes.byref(spec), None) != 0:
            raise OSError('FLEET_KERNEL_TIMER_UNAVAILABLE')
        yield
    except BaseException as error:
        original = error
        raise
    finally:
        if library.timer_delete(timer) != 0:
            if original is None:
                raise OSError('FLEET_KERNEL_TIMER_CLEANUP')
            original.add_note('FLEET_KERNEL_TIMER_CLEANUP')
