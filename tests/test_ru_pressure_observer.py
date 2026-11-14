import importlib.util
import json
import os
from pathlib import Path

import pytest


SPEC = importlib.util.spec_from_file_location('ru_pressure_observer', Path(__file__).parents[1] / 'scripts/ru_pressure_observer.py')
observer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(observer)


@pytest.mark.parametrize('kind,role', [('F', 0), ('F', 1), ('F', 2), ('F', 3), ('F', 4), ('R', 1), ('R', 2), ('Q', 0), ('Q', 1), ('Q', 2)])
def test_numeric_phase_contract(kind, role):
    assert observer.phase(f'EV {kind} 123 {role} 456 -5 78') == dict(
        kind=kind, mono_ns=123, phase=role, duration_ns=456, result=-5, bytes=78)


@pytest.mark.parametrize('line', ['EV F 1 5 2 0 0', 'EV F 1 1 -2 0 0', 'EV R 1 1 2 0 -1', 'EV Q 1 1 secret 0 0'])
def test_invalid_phase_fails_visible(line):
    with pytest.raises(ValueError):
        observer.phase(line)


def test_unrecognized_output_not_saved():
    assert observer.phase('private content or arguments') is None


def test_proc_only_reads_counter_files(tmp_path):
    target = tmp_path / '42'
    target.mkdir()
    fields = ['0'] * 22
    fields[0], fields[9], fields[11], fields[12], fields[19], fields[21] = 'S', '7', '11', '13', '17', '19'
    (target / 'stat').write_text('42 (process (nested)) ' + ' '.join(fields))
    (target / 'status').write_text('VmRSS: 123 kB\nVmSwap: 456 kB\nUid: 789\n')
    (target / 'io').write_text('read_bytes: 3\nwrite_bytes: 5\nsyscr: 99\n')
    (target / 'cgroup').write_text('0::/system.slice/example.service\n')
    (target / 'cmdline').write_text('NEVER_READ_PRIVATE_ARGUMENT')
    result = observer.process(target)
    assert result == dict(pid=42, name='process (nested)', state='S', majflt=7, cpu_ticks=24,
                          start_ticks=17, rss_pages=19, VmRSS=123, VmSwap=456, read_bytes=3,
                          write_bytes=5, cgroup='/system.slice/example.service')


def test_health_excludes_identity_and_content(tmp_path):
    state = dict(observed_at=20, records={'private-device': dict(
        decision=dict(valid_until=100, public_key='private-key'),
        applied=dict(allowed=True, result='applied'))})
    (tmp_path / 'transport-state.json').write_text(json.dumps(state))
    (tmp_path / 'transport-attempt.json').write_text(json.dumps(dict(observed_at=21, result='applied')))
    assert observer.health(tmp_path) == dict(observed_at=20, attempt='applied', attempt_at=21,
                                            records=1, allowed=1, applied=1, lease_min=100, lease_max=100)


def test_first_failure_filtered_without_modifying_original(tmp_path):
    path = tmp_path / 'transport-failure.json'
    raw = json.dumps(dict(elapsed=9, budget=8, secret='PRIVATE', calls=[dict(duration=3, role='decision', command='PRIVATE')] * 30))
    path.write_text(raw)
    result = observer.first_failure(path)
    assert result['elapsed'] == 9
    assert len(result['calls']) == 24
    assert 'PRIVATE' not in json.dumps(result)
    assert path.read_text() == raw
    assert len(result['sha256']) == 64


@pytest.mark.parametrize('name,journal', [('kworker/1', False), ('jbd2/vda1-8', True)])
def test_kernel_threads_skip_user_memory_and_group_reads(tmp_path, name, journal):
    target = tmp_path / '42'
    target.mkdir()
    fields = ['0'] * 22
    fields[0], fields[6] = 'S', str(0x00200000)
    (target / 'stat').write_text('42 (' + name + ') ' + ' '.join(fields))
    if journal:
        (target / 'io').write_text('write_bytes: 123\n')
    result = observer.process(target)
    assert result['kernel'] is True and result['kernel_io_sampled'] == journal
    assert result['cgroup'] == '/'
    assert result.get('write_bytes') == (123 if journal else None)
    assert 'VmSwap' not in result


def test_capture_never_replaces_existing_file(tmp_path):
    path = tmp_path / 'first.json'
    observer.save(path, dict(first=True))
    with pytest.raises(FileExistsError):
        observer.save(path, dict(first=False))
    assert json.loads(path.read_bytes()) == dict(first=True)
    assert path.stat().st_mode & 0o777 == 0o600


def test_capture_rejects_symlink_and_excess_bytes(tmp_path, monkeypatch):
    target = tmp_path / 'target'
    target.write_text('unchanged')
    link = tmp_path / 'link'
    link.symlink_to(target)
    with pytest.raises(OSError):
        observer.save(link, {})
    monkeypatch.setattr(observer, 'CAPTURE_BYTES', 16)
    with pytest.raises(ValueError, match='capture_budget'):
        observer.save(tmp_path / 'large', dict(data='x' * 20))
    assert target.read_text() == 'unchanged'
    assert not (tmp_path / 'large').exists()


def test_sample_size_counts_omissions_and_keeps_watcher_first(monkeypatch):
    monkeypatch.setattr(observer, 'SAMPLE_BYTES', 180)
    value = dict(processes=[dict(pid=42)] + [dict(pid=43, payload='x' * 200)],
                 cgroups={'large': 'x' * 200}, processes_omitted=0, cgroups_omitted=0)
    result = observer.bounded_sample(value)
    assert len(observer.encode(result)) <= 180
    assert result['processes'] == [dict(pid=42)]
    assert result['processes_omitted'] == 1
    assert result['cgroups_omitted'] == 1


def test_read_budget(tmp_path):
    path = tmp_path / 'counter'
    path.write_text('abc')
    assert observer.text(path, 3) == 'abc'
    with pytest.raises(ValueError, match='counter_too_large'):
        observer.text(path, 2)


@pytest.mark.parametrize('reason', ['first_failure', 'watcher_changed', 'memory_floor', 'sample_cost_limit', 'no_phase_events'])
def test_bounded_loop_stops_without_touching_gateway(tmp_path, monkeypatch, reason):
    node = tmp_path / 'node'
    node.mkdir()
    output = tmp_path / 'capture'
    output.mkdir()
    trace = tmp_path / 'trace.bt'
    trace.write_text('qualification placeholder')
    failure = node / 'transport-failure.json'
    if reason == 'first_failure':
        failure.write_text('{"elapsed":9,"budget":8}')
    old_node = sorted(path.name for path in node.iterdir())
    monkeypatch.setattr(observer, 'NODE', node)
    monkeypatch.setattr(observer.subprocess, 'check_output', lambda *args, **kwargs: b'fixture')
    monkeypatch.setattr(observer, 'process', lambda path: dict(start_ticks=1))
    ticks = iter(range(0, 1000, 10))
    monkeypatch.setattr(observer.time, 'monotonic', lambda: next(ticks))
    current = dict(processes=[dict(pid=42, start_ticks=1)], mem=dict(MemAvailable=1000000), sample_seconds=0.01, sample_cpu_seconds=0.01)
    if reason == 'watcher_changed':
        current['processes'][0]['start_ticks'] = 2
    if reason == 'memory_floor':
        current['mem']['MemAvailable'] = 100
    if reason == 'sample_cost_limit':
        current['sample_cpu_seconds'] = 0.21
    monkeypatch.setattr(observer, 'sample', lambda watcher: current)

    def health():
        assert reason != 'first_failure', 'failure evidence must precede potentially broken state reads'
        return dict(attempt='applied')

    monkeypatch.setattr(observer, 'health', health)
    descriptor, writer = os.pipe()
    os.close(writer)

    class Tracer:
        pid = 999999
        returncode = None
        stdout = os.fdopen(descriptor, 'rb')

        def poll(self):
            return self.returncode

        def wait(self, timeout):
            self.returncode = 0

    tracer = Tracer()
    monkeypatch.setattr(observer.subprocess, 'Popen', lambda *args, **kwargs: tracer)
    signals = []
    monkeypatch.setattr(observer.os, 'killpg', lambda pid, signal: signals.append((pid, signal)))
    code = observer.run(output, 180, 42, trace)
    final = json.loads((output / 'final.json').read_bytes())
    assert final['summary']['reason'] == reason
    assert code == (1 if reason == 'no_phase_events' else 0)
    assert signals == [(999999, observer.signal.SIGINT)]
    assert sorted(path.name for path in node.iterdir()) == old_node
    if failure.exists():
        assert failure.read_text() == '{"elapsed":9,"budget":8}'
