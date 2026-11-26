"""Bounded local admission/drain helper; not an all-writer or fleet capture permit."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import secrets
import signal
import stat
import sys
import time

from control.capture_gate import Gate, GateError, initialize, require


REASONS = frozenset(('CAPTURE_ALREADY_PENDING', 'DRAIN_TIMEOUT', 'UNSETTLED_OPERATION',
    'GATE_PATH', 'GATE_PERMISSIONS', 'GATE_LOCK_SHAPE', 'GATE_REPLACED', 'DRAIN_DEADLINE',
    'DRAIN_INSIDE_OPERATION', 'GUARD_EXPIRED', 'GUARD_PROTOCOL', 'PIPE_PROTOCOL_REQUIRED'))
MAX_PENDING = 256


def refusal_evidence(gate):
    result = dict(schema=1, scope='AFTER_REFUSAL_NON_ATOMIC', observed_at_ns=time.time_ns(),
                  capture_permitted=False, settlement_proven=False, marker_contents_read=False)
    if gate is None:
        return dict(result, status='GATE_NOT_OPENED', complete=False)
    try:
        with gate.opened() as descriptors:
            records = []
            complete = True
            with os.scandir(descriptors['pending']) as entries:
                for entry in entries:
                    if len(records) == MAX_PENDING:
                        complete = False
                        break
                    information = entry.stat(follow_symlinks=False)
                    records.append(dict(name_sha256=hashlib.sha256(os.fsencode(entry.name)).hexdigest(),
                        inode=information.st_ino, device=information.st_dev, size=information.st_size,
                        kind=stat.S_IFMT(information.st_mode), links=information.st_nlink,
                        uid=information.st_uid, modified_at_ns=information.st_mtime_ns,
                        changed_at_ns=information.st_ctime_ns))
            result.update(status='OBSERVED', complete=complete, pins=gate.pins,
                          pending_entries=sorted(records, key=lambda item: item['name_sha256']))
    except (GateError, OSError) as error:
        result.update(status='UNAVAILABLE', complete=False, error_type=type(error).__name__)
    return result


def refusal(error, gate):
    reason = str(error) if isinstance(error, GateError) and str(error) in REASONS else 'GATE_IO_REFUSED'
    evidence = refusal_evidence(gate)
    raw = json.dumps(evidence, sort_keys=True, separators=(',', ':')).encode()
    return dict(status='REFUSED', reason=reason, error_type=type(error).__name__,
                errno=error.errno if type(error.errno) is int else None, capture_permitted=False, evidence=evidence,
                evidence_sha256=hashlib.sha256(raw).hexdigest())


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
    gate = None
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
    except (GateError, OSError) as error:
        print(json.dumps(refusal(error, gate)), flush=True)
        raise SystemExit(1) from None
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


if __name__ == '__main__':
    main()
