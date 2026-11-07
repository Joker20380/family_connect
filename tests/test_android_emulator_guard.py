from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
import threading
from types import SimpleNamespace

import pytest


spec = importlib.util.spec_from_file_location('guard', Path(__file__).with_name('android_emulator_guard.py'))
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def frame(cpu=66, gpu=53):
    return {'cpu': [{'path': '/fixture/temp4_input', 'label': 'Core 2',
                     'raw_input': cpu * 1000, 'celsius': cpu}],
            'gpu': {'raw_input': gpu, 'celsius': gpu}, 'cpu_max_c': cpu,
            'gpu_max_c': gpu, 'error': None, 'started_monotonic': 1, 'finished_monotonic': 2}


def monitor(reader=None):
    clock, record, saved, stops = Clock(), {}, [], []
    instance = guard.Monitor(record, saved.append, stops.append, reader=reader or frame, clock=clock)
    return instance, clock, record, saved, stops


def fixture(monkeypatch, tmp_path, raw='66000', driver='coretemp', gpu='53'):
    directory = tmp_path / 'hwmon37'
    directory.mkdir()
    (directory / 'name').write_text(driver)
    if raw is not None:
        (directory / 'temp4_input').write_text(raw)
    (directory / 'temp4_label').write_text('Core 2')
    for suffix in ('max', 'crit', 'highest'):
        (directory / ('temp4_' + suffix)).write_text('999000')
    monkeypatch.setattr(guard, 'Path', lambda path: tmp_path)
    monkeypatch.setattr(guard.subprocess, 'check_output', lambda *args, **kwargs: gpu)
    return directory


@pytest.mark.parametrize('driver', ['coretemp', 'k10temp'])
@pytest.mark.parametrize('raw,expected,reason', [('66000', 66, None), ('84999', 84.999, None),
                                               ('85000', 85, 'CPU_TEMPERATURE_LIMIT'),
                                               ('94000', 94, 'CPU_TEMPERATURE_LIMIT')])
def test_raw_input_units_threshold_and_frame_interval(monkeypatch, tmp_path, driver, raw, expected, reason):
    directory = fixture(monkeypatch, tmp_path, raw, driver)
    clock, reads = Clock(), []
    original = Path.read_text

    def read(path, *args, **kwargs):
        reads.append(path.name)
        clock.now += 0.01
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, 'read_text', read)
    result = guard.read_frame(clock, clock)
    reading = result['cpu'][0]
    assert reading['raw_input'] == int(raw) and reading['celsius'] == expected
    assert reading['path'] == str(directory / 'temp4_input') and reading['label'] == 'Core 2'
    assert result['started_monotonic'] <= reading['started_monotonic'] < reading['finished_monotonic'] <= result['finished_monotonic']
    assert result['cpu_max_c'] == expected and guard.temperature_reason(result) == reason
    assert reads.count('temp4_input') == 1 and not any(name.endswith(('_max', '_crit', '_highest')) for name in reads)


@pytest.mark.parametrize('failure', ['no_driver', 'no_inputs', 'bad_integer', 'read_error', 'missing_gpu', 'bad_gpu'])
def test_sensor_unavailable_never_invents_zero(monkeypatch, tmp_path, failure):
    fixture(monkeypatch, tmp_path, None if failure == 'no_inputs' else 'bad' if failure == 'bad_integer' else '66000',
            'dell_smm' if failure == 'no_driver' else 'coretemp',
            '' if failure == 'missing_gpu' else 'N/A' if failure == 'bad_gpu' else '53')
    original = Path.read_text
    if failure == 'read_error':
        def read(path, *args, **kwargs):
            if path.name.endswith('_input'):
                raise OSError(5, 'fixture error')
            return original(path, *args, **kwargs)
        monkeypatch.setattr(Path, 'read_text', read)
    result = guard.read_frame()
    assert guard.temperature_reason(result) == 'SENSOR_UNAVAILABLE'
    assert result['cpu_max_c'] is None or result['cpu_max_c'] == 66
    assert result['gpu_max_c'] is None
    instance, clock, record, saved, stops = monitor(lambda: result)
    instance.sample('WATCH')
    assert stops[0]['reason'] == 'SENSOR_UNAVAILABLE' and stops[0]['frame'] == saved[0]['frame']


def test_watcher_then_audit_66_to_94_saves_the_deciding_frame_once():
    inputs = iter([frame(66), frame(94)])
    instance, clock, record, saved, stops = monitor(lambda: next(inputs))
    instance.sample('WATCH')
    with pytest.raises(guard.GuardStopped, match='CPU_TEMPERATURE_LIMIT'):
        instance.audit('READY_STAGE')
    assert len([item for item in saved if 'frame' in item]) == 2
    assert record['guard_stop']['frame'] == record['guard_last_frame'] == saved[1]['frame'] == stops[0]['frame']
    assert stops[0]['frame']['cpu'][0]['raw_input'] == 94000
    assert saved[2]['stop'] == stops[0]
    saved[1]['frame']['cpu_max_c'] = 0
    assert record['guard_stop']['frame']['cpu_max_c'] == 94


@pytest.mark.parametrize('cpu,gpu,reason', [(84, 80, 'GPU_TEMPERATURE_LIMIT'), (85, 79, 'CPU_TEMPERATURE_LIMIT')])
def test_limit_reason_is_specific(cpu, gpu, reason):
    instance, clock, record, saved, stops = monitor(lambda: frame(cpu, gpu))
    instance.sample('WATCH')
    assert stops[0]['reason'] == reason
    assert 'host_safety_abort' not in record


def test_unknown_monitor_error_is_filtered_and_saved():
    def broken():
        raise RuntimeError('private diagnostic must not be copied')
    instance, clock, record, saved, stops = monitor(broken)
    instance.sample('WATCH')
    assert stops[0]['reason'] == 'MONITOR_ERROR'
    assert stops[0]['frame']['cpu_max_c'] is None
    assert stops[0]['frame']['started_monotonic'] <= stops[0]['frame']['finished_monotonic']
    assert 'private' not in json.dumps(record)


def test_save_failure_still_stops_and_retains_exact_frame():
    instance, clock, record, saved, stops = monitor()
    def broken(payload):
        raise OSError(5, 'write failed')
    instance.save = broken
    instance.sample('WATCH')
    assert stops[0]['reason'] == 'MONITOR_ERROR'
    assert record['guard_stop']['frame'] == record['guard_last_frame']


def test_preparation_attempt_cleanup_and_overall_deadlines_are_distinct():
    instance, clock, record, saved, stops = monitor()
    instance.sample('PREPARATION')
    began = clock.now
    clock.now += guard.PREPARATION_SECONDS - 0.001
    attempt_deadline = instance.begin_attempt()
    for offset in [180, guard.CANDIDATE_SECONDS, guard.ATTEMPT_SECONDS - 0.001]:
        clock.now = began + guard.PREPARATION_SECONDS - 0.001 + offset
        instance.check_deadline()
        assert stops == []
    clock.now = attempt_deadline
    instance.check_deadline()
    assert stops[-1]['reason'] == 'TEST_LIFETIME_EXCEEDED' and stops[-1]['limit'] == 'attempt'
    assert stops[-1]['frame'] == record['guard_last_frame']
    instance.begin_cleanup()
    cleanup_deadline = instance.deadline
    instance.begin_cleanup()
    assert instance.deadline == cleanup_deadline
    clock.now = cleanup_deadline
    instance.check_deadline()
    assert stops[-1]['limit'] == 'cleanup'
    clock.now = instance.overall_deadline
    instance.check_deadline()
    assert stops[-1]['limit'] == 'overall'
    assert record['guard_stop']['limit'] == 'attempt'
    assert record['guard_budgets']['overall_seconds'] == 705


def test_preparation_expiry_and_repeat_attempt_cannot_extend_deadlines():
    instance, clock, record, saved, stops = monitor()
    clock.now = instance.deadline
    instance.check_deadline()
    assert stops[-1]['limit'] == 'preparation'
    with pytest.raises(guard.GuardStopped):
        instance.begin_attempt()
    fresh, clock, record, saved, stops = monitor()
    fresh.begin_attempt()
    with pytest.raises(guard.GuardStopped):
        fresh.begin_attempt()


@pytest.mark.parametrize('phase', ['preparation', 'attempt', 'cleanup'])
def test_thermal_control_remains_active_in_all_phases(phase):
    instance, clock, record, saved, stops = monitor(lambda: frame(94))
    if phase != 'preparation':
        instance.begin_attempt()
    if phase == 'cleanup':
        instance.begin_cleanup()
    instance.sample('WATCH')
    assert stops[0]['reason'] == 'CPU_TEMPERATURE_LIMIT' and stops[0]['phase'] == phase


def test_close_joins_monitor_and_preserves_last_frame_without_an_extra_read():
    sampled = threading.Event()
    calls = []
    def reader():
        calls.append(True)
        sampled.set()
        return frame()
    instance, clock, record, saved, stops = monitor(reader)
    instance.start()
    assert sampled.wait(1)
    assert instance.close()
    last = deepcopy(record['guard_last_frame'])
    assert record['guard_monitor_joined'] and all(not thread.is_alive() for thread in instance.threads)
    count = len(calls)
    assert instance.close() and len(calls) == count and record['guard_last_frame'] == last
    with pytest.raises(guard.GuardStopped, match='MONITOR_CLOSED'):
        instance.audit('AFTER_CLOSE')
    assert len(calls) == count


def test_join_failure_is_monitor_error_with_last_frame(monkeypatch):
    instance, clock, record, saved, stops = monitor()
    instance.sample('LAST')
    joins = []
    instance.threads = [SimpleNamespace(join=joins.append, is_alive=lambda: True)]
    monkeypatch.setattr(guard, 'JOIN_SECONDS', 0)
    assert not instance.close()
    assert stops[0]['reason'] == 'MONITOR_ERROR' and stops[0]['frame'] == saved[0]['frame']
    assert joins == [0] and record['guard_monitor_joined'] is False


def test_cleanup_keeps_original_stop_and_uses_a_new_complete_frame():
    inputs = iter([frame(94), frame(66)])
    instance, clock, record, saved, stops = monitor(lambda: next(inputs))
    instance.sample('WATCH')
    first = deepcopy(record['guard_stop'])
    instance.begin_cleanup()
    instance.sample('CLEANUP')
    assert instance.close()
    assert record['guard_stop'] == first
    assert record['guard_last_frame']['cpu_max_c'] == 66
    snapshot = instance.snapshot()
    snapshot['guard_stop']['frame']['cpu_max_c'] = 0
    assert record['guard_stop']['frame']['cpu_max_c'] == 94


def test_close_does_not_hide_an_expired_cleanup_deadline():
    instance, clock, record, saved, stops = monitor()
    instance.sample('LAST')
    instance.begin_cleanup()
    clock.now = instance.deadline
    assert instance.close()
    assert stops[0]['reason'] == 'TEST_LIFETIME_EXCEEDED' and stops[0]['limit'] == 'cleanup'


def test_watchdog_stops_hung_sampling_without_waiting_for_the_reader():
    blocked, release = threading.Event(), threading.Event()
    instance, clock, record, saved, stops = monitor()
    instance.sample('LAST_COMPLETED')
    previous = deepcopy(record['guard_last_frame'])
    def reader():
        blocked.set()
        assert release.wait(2)
        return frame()
    def stopped(event):
        stops.append(event)
        release.set()
    instance.reader, instance.on_stop = reader, stopped
    instance.begin_attempt()
    instance.start()
    try:
        assert blocked.wait(1)
        clock.now = instance.overall_deadline
        instance.check_deadline()
        assert stops[0]['reason'] == 'TEST_LIFETIME_EXCEEDED'
        assert stops[0]['limit'] == 'overall' and stops[0]['frame'] == previous
        assert stops[0]['frame_is_last_completed']
    finally:
        release.set()
        assert instance.close()


def test_samples_are_serialized_between_watcher_and_stage():
    entered, release = threading.Event(), threading.Event()
    calls = []
    def reader():
        calls.append(True)
        if len(calls) == 1:
            entered.set()
            assert release.wait(2)
            return frame(66)
        return frame(94)
    instance, clock, record, saved, stops = monitor(reader)
    watcher = threading.Thread(target=lambda: instance.sample('WATCH'))
    stage = threading.Thread(target=lambda: instance.sample('STAGE'))
    watcher.start()
    assert entered.wait(1)
    stage.start()
    release.set()
    watcher.join(1)
    stage.join(1)
    assert not watcher.is_alive() and not stage.is_alive()
    assert len(calls) == 2 and stops[0]['frame'] == saved[1]['frame']


def test_runner_uses_same_frame_and_bounded_forced_exit(monkeypatch, tmp_path):
    monkeypatch.setitem(sys.modules, 'android_emulator_guard', guard)
    specification = importlib.util.spec_from_file_location('cold_runner', Path(__file__).with_name('android_cold_runtime.py'))
    runner = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(runner)
    monkeypatch.setattr(runner, 'WORK', tmp_path)
    monkeypatch.setattr(runner, 'AUTH', tmp_path)
    monkeypatch.setattr(runner, 'record', {'phase': 'TEST', 'owns_stand': False})
    monkeypatch.setattr(runner, 'observe_resources', lambda: {'memory_kib': {'MemAvailable': 9000000}})
    stopped, exits = [], []
    process = SimpleNamespace(pid=123, poll=lambda: None)
    monkeypatch.setattr(runner, 'owned_processes', [process])
    monkeypatch.setattr(guard, 'stop', lambda owned: stopped.append(owned))
    monkeypatch.setattr(runner.os, 'killpg', lambda pid, signal: stopped.append(pid))
    monkeypatch.setattr(runner.os, '_exit', exits.append)
    instance = guard.Monitor(runner.record, runner.save_guard, runner.aborted, reader=frame, clock=Clock())
    monkeypatch.setattr(runner, 'monitor', instance)
    selected = runner.audit('STAGE')
    saved = json.loads((tmp_path / 'resources.jsonl').read_text())
    assert saved['frame'] == selected == runner.record['guard_last_frame']
    instance.clock.now = instance.overall_deadline
    instance.check_deadline()
    evidence = json.loads((tmp_path / 'guard-stop-TEST_LIFETIME_EXCEEDED-overall.json').read_text())
    assert evidence['stop']['frame'] == selected
    assert stopped == [process, 123] and exits == [124]
    assert json.loads((tmp_path / 'receipt.json').read_text())['guard_stop'] == evidence['stop']


def test_runner_rejects_preserved_output_before_monitor_or_cleanup(monkeypatch, tmp_path):
    monkeypatch.setitem(sys.modules, 'android_emulator_guard', guard)
    specification = importlib.util.spec_from_file_location('cold_runner', Path(__file__).with_name('android_cold_runtime.py'))
    runner = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(runner)
    (tmp_path / 'local-auth').mkdir()
    (tmp_path / 'receipt.json').write_text('preserved evidence')
    def forbidden(*args, **kwargs):
        pytest.fail('Monitor must not start for preserved output')
    monkeypatch.setattr(guard, 'Monitor', forbidden)
    with pytest.raises(AssertionError, match='UNUSED_RUNTIME_OUTPUT_DIRECTORY_REQUIRED'):
        runner.main(tmp_path)
    assert (tmp_path / 'receipt.json').read_text() == 'preserved evidence'
    assert not (tmp_path / 'local-auth/stop').exists()


def test_runner_forced_exit_survives_unwritable_evidence(monkeypatch, tmp_path):
    monkeypatch.setitem(sys.modules, 'android_emulator_guard', guard)
    specification = importlib.util.spec_from_file_location('cold_runner', Path(__file__).with_name('android_cold_runtime.py'))
    runner = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(runner)
    monkeypatch.setattr(runner, 'WORK', tmp_path / 'missing')
    monkeypatch.setattr(runner, 'AUTH', tmp_path / 'missing')
    monkeypatch.setattr(runner, 'record', {'phase': 'TEST'})
    stopped, exits = [], []
    process = SimpleNamespace(pid=123, poll=lambda: None)
    monkeypatch.setattr(runner, 'owned_processes', [process])
    monkeypatch.setattr(guard, 'stop', stopped.append)
    monkeypatch.setattr(runner.os, 'killpg', lambda pid, signal: stopped.append(pid))
    monkeypatch.setattr(runner.os, '_exit', exits.append)
    instance = guard.Monitor(runner.record, runner.save_guard, runner.aborted, reader=frame, clock=Clock())
    monkeypatch.setattr(runner, 'monitor', instance)
    instance.clock.now = instance.overall_deadline
    instance.check_deadline()
    assert stopped == [process, 123] and exits == [124]
    assert runner.record['guard_stop']['reason'] == 'TEST_LIFETIME_EXCEEDED'
    assert runner.record['guard_evidence_error'] == 'FileNotFoundError'
    assert runner.record['stop_marker_error'] == 'FileNotFoundError'


@pytest.mark.parametrize('networks,accepted', [
    (['CELLULAR'], True), (['WIFI'], False), (['CELLULAR','WIFI'], False),
    (['VPN'], False), ([], False), (['CELLULAR_BACKGROUND'], False)])
def test_cold_cellular_only_requires_one_real_connected_foreground_network(monkeypatch, networks, accepted):
    monkeypatch.setitem(sys.modules, 'android_emulator_guard', guard)
    specification = importlib.util.spec_from_file_location('cold_runner', Path(__file__).with_name('android_cold_runtime.py'))
    runner = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(runner)
    lines = []
    for network in networks:
        foreground = '' if network.endswith('_BACKGROUND') else '&FOREGROUND'
        transport = network.removesuffix('_BACKGROUND')
        lines.append('NetworkAgentInfo{ state: CONNECTED/CONNECTED Transports: '+transport+
                     ' Capabilities: INTERNET&NOT_RESTRICTED&NOT_VPN'+foreground+' }')
    assert runner.cellular_only('\n'.join(lines)) is accepted
    rules = runner.direct_rules('DROP')
    assert rules == [
        ['shell','iptables','-I','OUTPUT','-d','185.251.89.19','-p','tcp','--dport','8443','-j','DROP'],
        ['shell','iptables','-I','OUTPUT','-d','186.246.45.246','-p','tcp','--dport','4242','-j','DROP']]
    with pytest.raises(AssertionError):runner.direct_rules('ACCEPT')


def test_child_created_during_guard_stop_is_not_left_running(monkeypatch):
    monkeypatch.setitem(sys.modules, 'android_emulator_guard', guard)
    specification = importlib.util.spec_from_file_location('cold_runner', Path(__file__).with_name('android_cold_runtime.py'))
    runner = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(runner)
    stopped, created = [], []
    process = object()
    monkeypatch.setattr(guard, 'stop', stopped.append)
    def create():
        created.append(True)
        runner.record['guard_stop'] = {'reason': 'CPU_TEMPERATURE_LIMIT'}
        return process
    with pytest.raises(guard.GuardStopped):
        runner.own_start(create)
    assert stopped == [process] and runner.owned_processes == [process]
    with pytest.raises(guard.GuardStopped):
        runner.own_start(create)
    assert created == [True]


@pytest.mark.parametrize('failure,reason', [(None, None), ('gpu', 'GPU_TEMPERATURE_LIMIT'),
                                         ('sensor', 'SENSOR_UNAVAILABLE'), ('monitor', 'MONITOR_ERROR')])
def test_explicit_cpu_observation_override_keeps_other_stops(failure, reason):
    value = frame(94, 80 if failure == 'gpu' else 53)
    if failure in ('sensor', 'monitor'):
        value['error'] = {'reason': reason}
    clock, record, saved, stops = Clock(), {}, [], []
    instance = guard.Monitor(record, saved.append, stops.append, reader=lambda: value,
                             clock=clock, cpu_temperature_stop=False)
    selected = instance.sample('WATCH')
    assert selected['cpu_max_c'] == 94 and selected['cpu_temperature_limit_observed']
    assert selected['cpu_temperature_stop_enabled'] is False
    assert selected == saved[0]['frame'] == record['guard_last_frame']
    assert record['guard_budgets']['cpu_temperature_stop_enabled'] is False
    if reason:
        assert stops[0]['reason'] == reason
    else:
        assert stops == []
        clock.now = instance.overall_deadline
        instance.check_deadline()
        assert stops[0]['reason'] == 'TEST_LIFETIME_EXCEEDED'
