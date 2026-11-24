"""Bounded local admission/drain helper; not an all-writer or fleet capture permit."""
import argparse
import json
from pathlib import Path
import resource
import secrets
import signal
import sys
import time

from control.capture_gate import Gate, GateError, initialize, require


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gate', type=Path, required=True)
    parser.add_argument('--initialize', action='store_true')
    parser.add_argument('--drain-seconds', type=float, default=5)
    parser.add_argument('--hold-seconds', type=float, default=2)
    arguments = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    require(signal.getsignal(signal.SIGALRM) == signal.SIG_DFL and
            signal.SIGALRM not in signal.pthread_sigmask(signal.SIG_BLOCK, []) and
            signal.getitimer(signal.ITIMER_REAL) == (0, 0), 'ALARM_NOT_EXCLUSIVE')
    require(0 < arguments.drain_seconds <= 5 and 0 < arguments.hold_seconds <= 2, 'GUARD_DEADLINE')
    deadline = time.monotonic() + arguments.drain_seconds + arguments.hold_seconds
    signal.setitimer(signal.ITIMER_REAL, arguments.drain_seconds + arguments.hold_seconds)
    try:
        if arguments.initialize:
            initialize(arguments.gate)
            print(json.dumps(dict(status='INITIALIZED', capture_permitted=False)))
            return
        require(not sys.stdout.isatty() and not sys.stdin.isatty(), 'PIPE_PROTOCOL_REQUIRED')
        gate = Gate(arguments.gate)
        operation = secrets.token_hex(16)
        with gate.drain(arguments.drain_seconds):
            remaining = min(arguments.hold_seconds, deadline - time.monotonic())
            require(remaining > 0, 'GUARD_EXPIRED')
            signal.setitimer(signal.ITIMER_REAL, remaining)
            print(json.dumps(dict(status='LOCAL_DRAINED', operation=operation, pins=gate.pins,
                                  hold_seconds=remaining, capture_permitted=False)), flush=True)
            reply = sys.stdin.buffer.readline(80)
            require(reply in (b'', ('RELEASE ' + operation + '\n').encode()), 'GUARD_PROTOCOL')
        print(json.dumps(dict(status='RELEASED', capture_permitted=False)), flush=True)
    except (GateError, OSError):
        print(json.dumps(dict(status='REFUSED', capture_permitted=False)), flush=True)
        raise SystemExit(1) from None
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


if __name__ == '__main__':
    main()
