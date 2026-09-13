"""Bounded recovery experiment. Caller must exclusively own the pinned connection.

Callbacks must be bounded. Production integration additionally requires the real
broker lease, committed revision/expiry checks and cancellation on user disconnect.
This module neither edits routes nor decides to switch transport/profile.
"""
from dataclasses import dataclass
import time


@dataclass(frozen=True)
class Result:
    healthy: bool
    elapsed: float
    resets: int
    probes: int
    reason: str


def recover(probe, reset, authorized, *, cancelled=lambda: False, timeout=20.0,
            clock=time.monotonic, pause=time.sleep):
    if not 0 < timeout <= 30:
        raise ValueError('Recovery budget must be within (0,30] seconds')
    start = clock()
    deadline = start + timeout
    failures = resets = probes = 0
    next_reset = start
    def result(healthy, reason):
        return Result(healthy, round(clock()-start, 4), resets, probes, reason)
    while clock() < deadline:
        if cancelled() or not authorized():
            return result(False, 'ownership_or_cancellation')
        ok = probe()
        probes += 1
        # A probe can block while the caller cancels or changes the active revision.
        if cancelled() or not authorized():
            return result(False, 'ownership_or_cancellation')
        if clock() >= deadline:
            break
        if ok:
            return result(True, 'healthy')
        failures += 1
        if failures >= 3 and resets < 2 and clock() >= next_reset:
            reset()  # Caller holds ownership; errors propagate, never silently retry.
            resets += 1
            failures = 0
            next_reset = clock() + 10
        remaining = deadline-clock()
        if remaining > 0:
            pause(min(0.2, remaining))
    return result(False, 'deadline')
