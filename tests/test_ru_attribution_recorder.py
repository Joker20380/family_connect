import importlib.util
import json
from pathlib import Path
import select
import subprocess
import sys

import pytest


SPEC = importlib.util.spec_from_file_location('attribution', Path(__file__).parents[1] / 'scripts/ru_attribution_recorder.py')
recorder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(recorder)


def row(stamp, kind, subject=42, birth=100, first=0, second=0, third=0, sequence=None):
    return (stamp, 0, stamp if sequence is None else sequence, kind, subject, birth,
            first, second, third, 0, 0)


def reduce(rows):
    return recorder.analyze([(*record[:2], index + 1, *record[3:])
                             for index, record in enumerate(sorted(rows))])


def test_overlapping_scheduler_reclaim_and_io_not_added():
    value = reduce([row(0, 6), row(1, 4), row(2, 1), row(3, 12, subject=1),
                    row(7, 14, subject=1), row(8, 2), row(9, 3), row(10, 5), row(11, 7)])
    assert value['union_ns']['blocked'] == 6
    assert value['union_ns']['runnable'] == 1
    assert value['union_ns']['reclaim'] == 9
    assert value['blocked_service_overlap_ns'] == 4
    assert value['phase_scheduler_overlap_ns'] == 7
    assert value['phase_unclassified_ns'] == 4
    assert value['origin'].startswith('UNKNOWN')


def test_request_partial_requeue_merge_free_and_pointer_reuse():
    value = reduce([row(1, 11), row(2, 12), row(3, 14, first=50, second=100),
                    row(4, 13), row(6, 12), row(9, 14, first=50, second=50), row(10, 16),
                    row(11, 11, birth=101), row(12, 15, birth=101),
                    row(13, 11, birth=102), row(14, 16, birth=102)])
    assert value['union_ns']['device_queue'] == 3
    assert value['union_ns']['device_service'] == 5
    assert value['observations']['partial_completion'] == 1
    assert 'partial_completion' not in value['issues']
    assert value['issues']['merged_unknown_destination'] == 1
    assert value['issues']['free_without_final_completion'] == 1
    assert value['open_intervals'] == 0


def test_pid_reuse_and_mid_operation_attach_cannot_pair():
    value = reduce([row(1, 6), row(2, 7, birth=101), row(3, 3), row(4, 19)])
    assert not value['intervals']
    assert value['issues']['unpaired_end'] == 2
    assert value['issues']['task_exit_with_open_interval'] == 1


def test_cgroup_recreation_and_unknown_initial_generation():
    value = reduce([row(1, 10, first=5, second=10), row(2, 17, subject=5),
                    row(3, 10, first=5, second=20), row(4, 18, subject=5),
                    row(5, 17, subject=5), row(6, 10, first=5, second=30)])
    assert [item['generation'] for item in value['writers']] == ['initial_unknown_generation', 2, 5]
    assert [item['syscall_bytes'] for item in value['writers']] == [10, 20, 30]


def test_order_duplicates_loss_and_bounded_open_state():
    rows = [row(index + 1, 6, subject=index) for index in range(300)]
    value = recorder.analyze([*reversed(rows), rows[0], row(400, 23, first=7)])
    assert value['open_intervals'] == 256
    assert value['issues']['analysis_map_capacity'] == 44
    assert value['issues']['duplicate'] == 1
    assert value['issues']['producer_loss'] == 7
    assert value['issues']['sequence_gap_or_reorder'] == 1


@pytest.mark.parametrize('line', [b'private text', b'E 1 0 1 99 1 1 0 0 0 0 0',
                                 b'E -1 0 1 1 1 1 0 0 0 0 0'])
def test_non_protocol_rejected(line):
    with pytest.raises(ValueError):
        recorder.event(line)


def test_first_receipt_filters_and_preserves_original(tmp_path):
    failure = tmp_path / 'failure'
    raw = b'{"elapsed":9,"budget":8,"pid":42,"secret":"NEVER"}'
    failure.write_bytes(raw)
    value = recorder.failure_receipt(failure)
    assert failure.read_bytes() == raw
    assert 'NEVER' not in json.dumps(value)
    assert value['budget'] == 8 and len(value['sha256']) == 64


def command(source):
    return [sys.executable, '-u', '-c', source]


def test_guard_latched_after_receipt_eviction_and_first_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(recorder, 'BATCH_BYTES', 64)
    calls = []

    def cpu_clock():
        calls.append(None)
        return 0 if len(calls) == 1 else .3

    monkeypatch.setattr(recorder.time, 'process_time', cpu_clock)
    failure = tmp_path / 'failure'
    source = '''
import signal
signal.signal(signal.SIGINT, signal.SIG_IGN)
print('E 1 0 1 20 0 0 0 0 0 0 0', flush=True)
for index in range(2, 1000):
    print(f'E {index} 0 {index} 10 1 1 1 1 0 0 0', flush=True)
print('E 1000 0 1000 21 0 0 0 0 0 0 0', flush=True)
'''
    value = recorder.record(command(source), failure, 5,
                            ready=lambda: failure.write_text('{"budget":8,"elapsed":9}'))
    assert value['batch_count'] > 60
    assert all(batch['cpu'] == 0 for batch in value['batches'])
    assert value['stop_reason'] == 'first_failure'
    assert value['guard_violations'][0]['stage'] == 'batch'
    assert not value['budget_ok']
    assert value['drain_complete']


def test_accounting_map_is_bounded_and_overflow_visible(tmp_path):
    source = '''
for cpu in range(300):
    print(f'E 1 {cpu} 1 10 1 1 1 1 0 0 0')
print('E 2 0 2 21 0 0 0 0 0 0 0')
'''
    value = recorder.record(command(source), tmp_path / 'failure', 5)
    assert len(value['parsed_counts']) == 256
    assert value['accounting_overflow'] > 0
    assert value['invalid'] > 0
    assert not value['complete']


def test_terminal_counter_duplicate_is_not_overwritten(tmp_path):
    source = "print('C 0 6 64 64\\nC 0 6 63 63\\nE 1 0 0 21 0 0 0 0 0 0 0')"
    value = recorder.record(command(source), tmp_path / 'failure', 5)
    assert value['producer_counts'] == [dict(cpu=0, kind=6, hits=64, attempted=64)]
    assert value['invalid'] == 1
    assert not value['complete']


def test_real_pipe_drains_sigint_tail_and_preserves_first_failure(tmp_path):
    failure = tmp_path / 'failure'
    source = '''
import json, os, signal, time
from pathlib import Path
path = Path(%r)
def stop(*unused):
    path.with_name('second-failure').write_text(json.dumps(dict(elapsed=10,budget=8)))
    for index in range(2, 102):
        print(f'E {index} 0 {index} 20 0 0 0 0 0 0 0', flush=True)
    print('E 102 0 102 21 0 0 0 0 0 0 0', flush=True)
    raise SystemExit(0)
signal.signal(signal.SIGINT, stop)
print('E 1 0 1 20 0 0 0 0 0 0 0', flush=True)
pending = path.with_name('failure.pending')
pending.write_text(json.dumps(dict(elapsed=9,budget=8)))
pending.replace(path)
while True: time.sleep(.01)
''' % str(failure)
    value = recorder.record(command(source), failure, 5)
    assert value['stop_reason'] == 'first_failure'
    assert value['events_seen'] == 102
    assert value['drain_complete'] and value['complete'] and value['budget_ok']
    assert value['eof'] and value['end_marker'] and value['child_returncode'] == 0
    assert not value['forced'] and value['stop_elapsed'] < recorder.STOP_SECONDS
    assert value['first_failure'] == recorder.failure_receipt(failure)
    assert json.loads(failure.read_text()) == dict(elapsed=9, budget=8)
    assert json.loads(failure.with_name('second-failure').read_text())['elapsed'] == 10


@pytest.mark.parametrize('atomic', [False, True], ids=['visible-final', 'pending-replace'])
@pytest.mark.parametrize('prefix', ['', '{"elapsed":'], ids=['empty', 'partial'])
def test_failure_publication_boundary_is_interprocess_and_atomic(tmp_path, monkeypatch, atomic, prefix):
    failure = tmp_path / 'failure'
    pending = tmp_path / 'failure.pending'
    payload = '{"elapsed":9,"budget":8}'
    publisher_source = '''
import select, sys
from pathlib import Path
def receive():
    assert select.select([sys.stdin], [], [], 2)[0], 'publisher_handshake_timeout'
    assert sys.stdin.readline() == 'continue\\n'
receive()
target = Path(%r)
with target.open('w') as stream:
    stream.write(%r)
    stream.flush()
    print('prepared', flush=True)
    receive()
    stream.write(%r)
if %r:
    target.replace(Path(%r))
print('published', flush=True)
''' % (str(pending if atomic else failure), prefix, payload[len(prefix):], atomic, str(failure))
    publisher = subprocess.Popen(command(publisher_source), stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    transitions = []
    reads = []
    original = recorder.failure_receipt

    def exchange(expected):
        publisher.stdin.write('continue\n')
        publisher.stdin.flush()
        assert select.select([publisher.stdout], [], [], 2)[0], 'parent_handshake_timeout'
        assert publisher.stdout.readline().strip() == expected
        transitions.append(expected)

    def ready():
        exchange('prepared')
        assert (pending if atomic else failure).read_text() == prefix

    def stop_requested():
        if atomic and transitions == ['prepared']:
            assert not failure.exists() and pending.exists()
            assert not reads
            transitions.append('pending_not_published')
            exchange('published')
        return False

    def read(path):
        reads.append(path.read_bytes())
        try:
            return original(path)
        finally:
            if not atomic:
                exchange('published')

    monkeypatch.setattr(recorder, 'failure_receipt', read)
    tracer = '''
import signal
def stop(*unused):
    print('E 2 0 2 21 0 0 0 0 0 0 0', flush=True)
    raise SystemExit(0)
signal.signal(signal.SIGINT, stop)
print('E 1 0 1 20 0 0 0 0 0 0 0', flush=True)
signal.pause()
'''
    try:
        value = recorder.record(command(tracer), failure, 5, stop_requested, ready)
        output, error = publisher.communicate(timeout=2)
        assert publisher.returncode == 0 and not output and not error
    finally:
        if publisher.poll() is None:
            publisher.kill()
        publisher.communicate(timeout=2)
    assert failure.read_text() == payload
    assert reads == [(payload if atomic else prefix).encode()]
    assert value['stop_reason'] == ('first_failure' if atomic else 'invalid_failure')
    assert value['complete'] is atomic
    assert value['first_failure'] == (original(failure) if atomic else None)
    assert value['events_seen'] == 2 and value['end_marker'] and value['eof']
    assert value['child_returncode'] == 0 and value['drain_complete'] and not value['forced']
    assert value['stop_elapsed'] < recorder.STOP_SECONDS
    assert transitions == (['prepared', 'pending_not_published', 'published'] if atomic else ['prepared', 'published'])


def test_corrupt_published_failure_remains_negative_without_retry(tmp_path, monkeypatch):
    failure = tmp_path / 'failure'
    original = recorder.failure_receipt
    reads = []

    def read(path):
        reads.append(path)
        return original(path)

    monkeypatch.setattr(recorder, 'failure_receipt', read)
    source = '''
import signal
def stop(*unused):
    print('E 2 0 2 21 0 0 0 0 0 0 0', flush=True)
    raise SystemExit(0)
signal.signal(signal.SIGINT, stop)
print('E 1 0 1 20 0 0 0 0 0 0 0', flush=True)
signal.pause()
'''
    value = recorder.record(command(source), failure, 5, ready=lambda: failure.write_text('{'))
    assert reads == [failure] and failure.read_text() == '{'
    assert value['stop_reason'] == 'invalid_failure' and value['first_failure'] is None
    assert not value['complete'] and value['drain_complete']
    assert value['eof'] and value['child_returncode'] == 0
    assert not value['forced'] and value['stop_elapsed'] < recorder.STOP_SECONDS


@pytest.mark.parametrize('exit_code,tail,complete', [(0, '\n', True), (2, '\n', False), (0, '', False)])
def test_real_eof_and_nonzero_exit(tmp_path, exit_code, tail, complete):
    source = f"import sys; sys.stdout.write({('E 1 0 1 21 0 0 0 0 0 0 0' + tail)!r}); sys.exit({exit_code})"
    value = recorder.record(command(source), tmp_path / 'failure', 5)
    assert value['drain_complete'] is complete
    assert value['child_returncode'] == exit_code


def test_inherited_pipe_no_eof_is_bounded_incomplete(tmp_path, monkeypatch):
    monkeypatch.setattr(recorder, 'STOP_SECONDS', 2.2)
    ready = []
    source = "import os,signal,time; signal.signal(signal.SIGINT,signal.SIG_IGN); child=os.fork(); time.sleep(30) if child==0 else print('E 1 0 1 20 0 0 0 0 0 0 0',flush=True)"
    value = recorder.record(command(source), tmp_path / 'failure', 5,
                            lambda: bool(ready), lambda: ready.append(True))
    assert value['stop_elapsed'] < 1
    assert not value['drain_complete'] and value['forced']


def test_real_burst_eviction_and_tracer_error_visible(tmp_path):
    source = "import sys; [print(f'E {index} 0 {index} 20 0 0 0 0 0 0 0') for index in range(5000)]; print('E 5000 0 5000 21 0 0 0 0 0 0 0'); sys.stderr.write('test error')"
    value = recorder.record(command(source), tmp_path / 'failure', 5)
    assert value['events_seen'] == 5001 and value['evicted'] == 905
    assert len(value['events']) == 4096 and len(value['batches']) <= 60
    assert value['stderr_bytes'] == 10 and not value['complete']


def test_resource_guard_stops_without_raising_limit(tmp_path, monkeypatch):
    monkeypatch.setattr(recorder, 'CPU_LIMIT', 0)
    source = "import signal,time; signal.signal(signal.SIGINT,lambda *unused:exit(0)); print('E 1 0 1 20 0 0 0 0 0 0 0',flush=True); time.sleep(30)"
    value = recorder.record(command(source), tmp_path / 'failure', 5)
    assert value['stop_reason'] == 'batch_cost_limit'
    assert not value['budget_ok']


def test_exclusive_output(tmp_path):
    target = tmp_path / 'final.json'
    recorder.save(target, dict(first=True))
    with pytest.raises(FileExistsError):
        recorder.save(target, dict(first=False))
    assert json.loads(target.read_text()) == dict(first=True)


def test_unknown_request_generation_is_not_paired():
    value = reduce([row(1, 11, birth=0), row(2, 12, birth=0), row(3, 14, birth=0)])
    assert not value['intervals']
    assert value['issues']['unknown_request_generation'] == 3


def test_sigterm_request_drains_boundary_event_once(tmp_path):
    ready = []
    source = '''
import signal,time
def stop(*unused):
    print('E 4 0 4 21 0 0 0 0 0 0 0',flush=True)
    raise SystemExit(0)
signal.signal(signal.SIGINT,stop)
print('E 1 0 1 17 9 0 0 0 0 0 0',flush=True)
print('E 2 0 2 20 0 0 0 0 0 0 0',flush=True)
print('E 3 0 3 20 0 0 0 0 0 0 0',flush=True)
time.sleep(30)
'''
    value = recorder.record(command(source), tmp_path / 'failure', 5,
                            lambda: bool(ready), lambda: ready.append(True))
    assert ready == [True]
    assert value['stop_reason'] == 'SIGTERM' and value['drain_complete']
    assert value['events_seen'] == 4


def test_oversized_line_stops_without_unbounded_memory(tmp_path):
    source = "import sys,time; sys.stdout.write('x'*131074); sys.stdout.flush(); time.sleep(30)"
    value = recorder.record(command(source), tmp_path / 'failure', 5)
    assert value['stop_reason'] == 'line_budget'
    assert not value['drain_complete'] and value['partial_line_bytes'] <= recorder.BATCH_BYTES * 2


def test_missing_end_and_open_phase_are_visible(tmp_path):
    value = recorder.record(command("print('E 1 0 1 6 42 10 0 0 0 0 0')"), tmp_path / 'failure', 5)
    assert value['analysis']['open_intervals'] == 1
    assert value['eof'] and not value['end_marker'] and not value['complete']


def test_blank_tracer_lines_do_not_hide_non_numeric_content(tmp_path):
    value = recorder.record(command("print('\\nE 1 0 1 21 0 0 0 0 0 0 0\\n')"), tmp_path / 'failure', 5)
    assert value['drain_complete'] and value['invalid'] == 0
    value = recorder.record(command("print('not an event\\nE 1 0 1 21 0 0 0 0 0 0 0')"), tmp_path / 'failure', 5)
    assert value['invalid'] == 1 and not value['complete']
