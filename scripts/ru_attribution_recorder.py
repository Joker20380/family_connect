"""Qualification-only numeric event recorder; never modifies the observed process."""

import argparse
from collections import Counter, deque
import hashlib
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import time


RING = 4096
MAP_KEYS = 256
BATCH_BYTES = 65536
CPU_LIMIT = 0.2
WALL_LIMIT = 10
STOP_SECONDS = 8
CAPTURE_BYTES = 8 * 1024 * 1024
ERROR_BYTES = 1024 * 1024
KINDS = frozenset(range(1, 29))


def event(line):
    fields = line.split()
    if len(fields) != 12 or fields[0] != b'E':
        raise ValueError('non_numeric_protocol')
    numbers = tuple(int(field) for field in fields[1:])
    if any(number < 0 or number >= 2**64 for number in numbers[:-1]):
        raise ValueError('invalid_unsigned_field')
    if not -(2**63) <= numbers[-1] < 2**64 or numbers[3] not in KINDS:
        raise ValueError('invalid_event')
    return numbers


def union_ns(intervals):
    total = 0
    right = -1
    for begin, end in sorted(intervals):
        if begin > end:
            raise ValueError('reversed_interval')
        total += max(0, end - max(begin, right))
        right = max(right, end)
    return total


def overlaps(left, right):
    return [(max(begin, other_begin), min(end, other_end))
            for begin, end in left for other_begin, other_end in right
            if max(begin, other_begin) < min(end, other_end)]


def analyze(records):
    """Reduce retained events only; no extrapolation across loss or ring eviction."""
    pending = {}
    intervals = []
    issues = Counter()
    observations = Counter()
    groups = {}
    seen = set()
    sequences = {}
    writers = Counter()
    request_owners = Counter()

    def begin(key, stamp, kind):
        if key in pending:
            issues['replaced_unpaired_begin'] += 1
        elif len(pending) >= MAP_KEYS:
            issues['analysis_map_capacity'] += 1
            return
        pending[key] = (stamp, kind)

    def finish(key, stamp):
        value = pending.pop(key, None)
        if value is None:
            issues['unpaired_end'] += 1
        elif value[0] > stamp:
            issues['reversed_pair'] += 1
        else:
            intervals.append(dict(kind=value[1], begin=value[0], end=stamp,
                                  identity=list(key)))

    for record in sorted(records):
        stamp, cpu, sequence, kind, subject, birth, first, second, third, fourth, result = record
        identity = (cpu, sequence)
        if identity in seen:
            issues['duplicate'] += 1
            continue
        seen.add(identity)
        previous = sequences.get(cpu)
        if previous is not None and sequence != previous + 1:
            issues['sequence_gap_or_reorder'] += 1
        sequences[cpu] = sequence
        task = ('task', subject, birth)
        request = ('request', subject, birth)
        if 11 <= kind <= 16 and birth == 0:
            issues['unknown_request_generation'] += 1
            continue
        if kind == 1:
            begin(task, stamp, 'runnable' if first else 'blocked')
        elif kind == 2:
            if task in pending and pending[task][1] == 'blocked':
                finish(task, stamp)
                begin(task, stamp, 'runnable')
            elif task not in pending:
                issues['wake_without_switch_out'] += 1
                begin(task, stamp, 'runnable')
        elif kind == 3:
            finish(task, stamp)
        elif kind in (4, 6, 8):
            begin((kind, subject, birth), stamp,
                  {4: 'reclaim', 6: 'fsync', 8: 'rename'}[kind])
        elif kind in (5, 7, 9):
            finish((kind - 1, subject, birth), stamp)
            if kind in (7, 9) and result != 0:
                issues['failed_syscall'] += 1
        elif kind == 10:
            writers[(first, groups.get(first, 'initial_unknown_generation'))] += second
        elif kind in (11, 12, 13):
            if request in pending:
                finish(request, stamp)
            elif kind != 11:
                issues['request_attached_mid_lifecycle'] += 1
            begin(request, stamp, 'device_service' if kind == 12 else 'device_queue')
            if kind == 12:
                request_owners[(third, groups.get(third, 'initial_unknown_generation'))] += first
        elif kind == 14:
            if first > second:
                issues['completion_exceeds_remaining'] += 1
            if first >= second:
                finish(request, stamp)
            else:
                observations['partial_completion'] += 1
        elif kind in (15, 16):
            if request in pending:
                pending.pop(request)
                issues['merged_unknown_destination' if kind == 15 else 'free_without_final_completion'] += 1
        elif kind == 17:
            if len(groups) >= MAP_KEYS and subject not in groups:
                issues['cgroup_map_capacity'] += 1
            else:
                groups[subject] = stamp
        elif kind == 18:
            groups.pop(subject, None)
        elif kind == 19:
            for key in list(pending):
                if key[0] != 'request' and key[1:] == (subject, birth):
                    pending.pop(key)
                    issues['task_exit_with_open_interval'] += 1
        elif kind == 23:
            issues['producer_loss'] += max(1, first)
    by_kind = {}
    for interval in intervals:
        by_kind.setdefault(interval['kind'], []).append((interval['begin'], interval['end']))
    phases = by_kind.get('fsync', []) + by_kind.get('rename', [])
    waits = by_kind.get('runnable', []) + by_kind.get('blocked', [])
    explained = union_ns(overlaps(phases, waits))
    return dict(intervals=intervals, issues=dict(issues), observations=dict(observations), open_intervals=len(pending),
                union_ns={kind: union_ns(values) for kind, values in by_kind.items()},
                phase_scheduler_overlap_ns=explained,
                phase_unclassified_ns=union_ns(phases) - explained,
                blocked_service_overlap_ns=union_ns(overlaps(by_kind.get('blocked', []),
                                                            by_kind.get('device_service', []))),
                writers=[dict(cgroup=key[0], generation=key[1], syscall_bytes=count)
                         for key, count in writers.items()],
                request_owners=[dict(cgroup=key[0], generation=key[1], issued_bytes=count)
                                for key, count in request_owners.items()],
                origin='UNKNOWN: executor and bio blkcg do not prove original data producer',
                scope='retained events only; overlap is not a causal decomposition')


def failure_receipt(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as stream:
        raw = stream.read(65537)
    if len(raw) > 65536:
        raise ValueError('failure_file_size')
    value = json.loads(raw)
    result = dict(sha256=hashlib.sha256(raw).hexdigest())
    for name in ('elapsed', 'budget', 'pid'):
        number = value.get(name)
        if isinstance(number, (int, float)) and not isinstance(number, bool):
            result[name] = number
    return result


def encode(value):
    return json.dumps(value, separators=(',', ':'), allow_nan=False).encode()


def save(path, value):
    raw = encode(value)
    if len(raw) > CAPTURE_BYTES:
        raise ValueError('capture_budget')
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'wb') as stream:
        stream.write(raw)


def signal_child(child, signum):
    try:
        os.killpg(child.pid, signum)
    except ProcessLookupError:
        pass


def record(command, failure, seconds, stop_requested=lambda: False, ready=lambda: None,
           invalid_record=lambda raw: None, attached=lambda: None,
           event_received=lambda value: None, prepare_stop=None, stop_ready=lambda: True,
           environment=None, error_received=lambda raw: None, legacy_read_warning=False):
    """Drain both pipes until EOF AND child exit, or report an explicit incomplete tail."""
    ring = deque(maxlen=RING)
    batches = deque(maxlen=60)
    started = time.monotonic()
    child = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             start_new_session=True, bufsize=0, env=environment)
    selector = selectors.DefaultSelector()
    for stream in (child.stdout, child.stderr):
        os.set_blocking(stream.fileno(), False)
        selector.register(stream, selectors.EVENT_READ)
    buffer = b''
    errors = hashlib.sha256()
    error_bytes = 0
    warning_bytes = 0
    count = 0
    first = None
    stop_at = None
    reason = None
    forced = False
    invalid = 0
    end_marker = False
    ready_seen = False
    cpu_total = 0.0
    batch_count = 0
    cpu_max = wall_max = 0.0
    guard_violations = []
    producer_counts = {}
    parsed_counts = Counter()
    attached_seen = False
    signalled = False
    stdout_bytes = wire_records = accounting_overflow = 0
    try:
        while selector.get_map() or child.poll() is None:
            batch_start, cpu_start = time.monotonic(), time.process_time()
            if stop_at is None:
                if failure.exists():
                    try:
                        first = failure_receipt(failure)
                        reason = 'first_failure'
                    except (OSError, ValueError):
                        reason = 'invalid_failure'
                elif stop_requested():
                    reason = 'SIGTERM'
                elif batch_start - started >= seconds:
                    reason = 'duration'
                elif child.poll() is not None:
                    reason = 'tracer_exit'
                if reason:
                    stop_at = batch_start
                    if prepare_stop is not None:
                        prepare_stop()
            if stop_at is not None and not signalled and stop_ready():
                if child.poll() is None:
                    signal_child(child, signal.SIGINT)
                signalled = True
            if stop_at is not None and batch_start - stop_at >= STOP_SECONDS - 2:
                forced = True
                signal_child(child, signal.SIGKILL)
                break
            for key, _ in selector.select(0.05):
                raw = os.read(key.fd, BATCH_BYTES)
                if not raw:
                    selector.unregister(key.fileobj)
                    continue
                if key.fileobj is child.stderr:
                    if error_bytes < 4096:
                        error_received(raw[:4096 - error_bytes])
                    errors.update(raw)
                    error_bytes += len(raw)
                    if legacy_read_warning and raw == b'WARNING: Addrspace is not set\n':
                        warning_bytes += len(raw)
                        continue
                    if reason is None:
                        reason = 'tracer_error'
                    if error_bytes > ERROR_BYTES:
                        reason = 'stderr_budget'
                        forced = True
                        break
                else:
                    stdout_bytes += len(raw)
                    buffer += raw
                    lines = buffer.split(b'\n')
                    buffer = lines.pop()
                    for line in lines:
                        if not line.strip():
                            continue
                        try:
                            if line == b'__BPFTRACE_NOTIFY_PROBES_ATTACHED':
                                if attached_seen:
                                    raise ValueError('duplicate_attach')
                                attached_seen = True
                                attached()
                                continue
                            if line.startswith(b'C '):
                                fields = tuple(int(field) for field in line.split()[1:])
                                if len(fields) != 4 or min(fields) < 0 or max(fields) >= 2**64 or len(producer_counts) >= 256 or fields[:2] in producer_counts:
                                    raise ValueError('invalid_accounting')
                                producer_counts[fields[:2]] = fields[2:]
                                continue
                            wire_records += 1
                            value = event(line)
                            if value[3] == 20 and not ready_seen:
                                ready()
                                ready_seen = True
                            end_marker |= value[3] == 21
                            key = (value[1], value[3])
                            if key not in parsed_counts and len(parsed_counts) >= 256:
                                accounting_overflow += 1
                                raise ValueError('accounting_capacity')
                            parsed_counts[key] += 1
                            event_received(value)
                            ring.append(value)
                            count += 1
                        except ValueError:
                            if invalid < 4:
                                invalid_record(line[:256])
                            invalid += 1
                            reason = reason or 'invalid_protocol'
                    if len(buffer) > BATCH_BYTES:
                        reason = 'line_budget'
                        forced = True
                        break
            cpu, wall = time.process_time() - cpu_start, time.monotonic() - batch_start
            cpu_total += cpu
            batch_count += 1
            cpu_max, wall_max = max(cpu_max, cpu), max(wall_max, wall)
            batches.append(dict(cpu=cpu, wall=wall))
            if cpu > CPU_LIMIT or wall > WALL_LIMIT:
                reason = 'batch_cost_limit'
                if not guard_violations:
                    guard_violations.append(dict(stage='batch', cpu=cpu, wall=wall))
            if forced:
                break
        eof = not selector.get_map()
    finally:
        selector.close()
        if child.poll() is None:
            forced = True
            signal_child(child, signal.SIGKILL)
        try:
            child.wait(timeout=0.5)
        except subprocess.TimeoutExpired:
            forced = True
        child.stdout.close()
        child.stderr.close()
    reduction_start, reduction_cpu = time.monotonic(), time.process_time()
    analysis = analyze(ring)
    reduction = dict(cpu=time.process_time() - reduction_cpu, wall=time.monotonic() - reduction_start)
    if reduction['cpu'] > CPU_LIMIT or reduction['wall'] > WALL_LIMIT:
        guard_violations.append(dict(stage='reduction', **reduction))
    drain_complete = eof and not buffer and not forced and child.returncode == 0 and end_marker
    return dict(schema=1, boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                started_mono=started, elapsed=time.monotonic() - started,
                stop_elapsed=None if stop_at is None else time.monotonic() - stop_at,
                stop_reason=reason or 'tracer_exit', first_failure=first,
                events=list(ring), events_seen=count, evicted=max(0, count - RING),
                wire_records=wire_records, stdout_bytes=stdout_bytes, accounting_overflow=accounting_overflow,
                batches=list(batches), processing_cpu=cpu_total, reduction=reduction,
                batch_count=batch_count, batch_cpu_max=cpu_max, batch_wall_max=wall_max,
                analysis=analysis, stderr_bytes=error_bytes, stderr_sha256=errors.hexdigest(),
                known_warning_bytes=warning_bytes,
                invalid=invalid, partial_line_bytes=len(buffer), eof=eof,
                attached=attached_seen, guard_violations=guard_violations,
                producer_counts=[dict(cpu=key[0], kind=key[1], hits=value[0], attempted=value[1])
                                 for key, value in sorted(producer_counts.items())],
                parsed_counts=[dict(cpu=key[0], kind=key[1], count=value)
                               for key, value in sorted(parsed_counts.items())],
                child_returncode=child.returncode, forced=forced, end_marker=end_marker,
                drain_complete=drain_complete,
                complete=drain_complete and reason != 'invalid_failure' and not error_bytes and not invalid and not analysis['issues']
                and not analysis['open_intervals'] and count <= RING,
                budget_ok=not guard_violations)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--failure', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seconds', type=int, default=30)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if not Path('/run/fc-attribution-disposable-vm').is_file():
        parser.error('qualification VM marker required; no production launcher')
    if not 1 <= args.seconds <= 86400 or not args.command or args.failure.exists():
        parser.error('invalid duration/command or pre-existing authoritative failure')
    stopping = []
    signal.signal(signal.SIGTERM, lambda *_: stopping.append(True))
    result = record(args.command, args.failure, args.seconds, lambda: bool(stopping))
    started, cpu = time.monotonic(), time.process_time()
    save(args.output, result)
    cost = dict(cpu=time.process_time() - cpu, wall=time.monotonic() - started)
    save(args.output.with_suffix('.save-cost.json'), cost)
    return 0 if result['drain_complete'] and result['budget_ok'] and cost['cpu'] <= CPU_LIMIT and cost['wall'] <= WALL_LIMIT else 1


if __name__ == '__main__':
    raise SystemExit(main())
