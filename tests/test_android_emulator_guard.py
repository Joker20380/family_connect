import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest


spec = importlib.util.spec_from_file_location('emulator_guard', Path(__file__).with_name('android_emulator_guard.py'))
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


def exercise(monkeypatch, directory, gpu='53', elapsed=0):
    process = SimpleNamespace(pid=123, exited=False)
    process.poll = lambda: 0 if process.exited else None
    sleeps, stopped, commands = [], [], []

    class ImmediateThread:
        def __init__(self, target, daemon):
            assert daemon is True
            self.target = target

        def start(self):
            self.target()

    def sleep(seconds):
        sleeps.append(seconds)
        process.exited = True

    def stop(owned):
        assert owned is process
        stopped.append(True)
        process.exited = True

    def spawn(command, **kwargs):
        commands.append(command)
        return process

    ticks = iter((0, elapsed, elapsed))
    monkeypatch.setattr(guard, 'Path', lambda path: directory)
    monkeypatch.setattr(guard, 'threading', SimpleNamespace(Thread=ImmediateThread))
    monkeypatch.setattr(guard, 'time', SimpleNamespace(monotonic=lambda: next(ticks), sleep=sleep))
    monkeypatch.setattr(guard, 'subprocess', SimpleNamespace(Popen=spawn, STDOUT=-2, check_output=lambda *args, **kwargs: gpu))
    monkeypatch.setattr(guard, 'stop', stop)
    record = {}
    guard.start(['not-executed'], {}, None, record)
    assert commands == [['systemd-run', '--user', '--scope', '--quiet', '-p', 'CPUQuota=100%', '--', 'not-executed']]
    return record, stopped, sleeps


def sensor(tmp_path, driver='coretemp', raw='66000'):
    directory = tmp_path / 'hwmon37'
    directory.mkdir()
    (directory / 'name').write_text(driver)
    if raw is not None:
        (directory / 'temp4_input').write_text(raw)
    for suffix in ('max', 'crit', 'highest'):
        (directory / ('temp4_' + suffix)).write_text('999000')
    return directory


@pytest.mark.parametrize('driver', ['coretemp', 'k10temp'])
@pytest.mark.parametrize('raw,expected,stop_expected', [('66000', 66, False), ('84999', 84.999, False), ('85000', 85, True), ('94000', 94, True)])
def test_current_input_units_maximum_and_unchanged_threshold(monkeypatch, tmp_path, driver, raw, expected, stop_expected):
    directory = sensor(tmp_path, driver, raw)
    (directory / 'temp1_input').write_text('62000')
    record, stopped, sleeps = exercise(monkeypatch, tmp_path)
    assert record['peak_cpu_c'] == expected
    assert bool(stopped) is stop_expected
    assert sleeps == ([] if stop_expected else [3])
    if stop_expected:
        assert record['guard_cpu_c'] == expected
        assert record['host_safety_abort'] is True


@pytest.mark.parametrize('failure', ['no_driver', 'no_inputs', 'missing_name', 'bad_integer', 'read_error'])
def test_missing_or_unreadable_temperature_stops_without_inventing_zero(monkeypatch, tmp_path, failure):
    directory = sensor(tmp_path, 'dell_smm' if failure == 'no_driver' else 'coretemp',
                       None if failure == 'no_inputs' else 'invalid' if failure == 'bad_integer' else '66000')
    if failure == 'missing_name':
        (directory / 'name').unlink()
    if failure == 'read_error':
        original_read = Path.read_text
        def fail_input(path, *args, **kwargs):
            if path.name == 'temp4_input':
                raise OSError(5, 'fixture read error')
            return original_read(path, *args, **kwargs)
        monkeypatch.setattr(Path, 'read_text', fail_input)
    record, stopped, sleeps = exercise(monkeypatch, tmp_path)
    assert record == {'host_safety_monitor_failed': True}
    assert stopped == [True] and sleeps == []


@pytest.mark.parametrize('gpu,elapsed', [('80', 0), ('53', 180)])
def test_other_guard_limits_unchanged(monkeypatch, tmp_path, gpu, elapsed):
    sensor(tmp_path)
    record, stopped, sleeps = exercise(monkeypatch, tmp_path, gpu, elapsed)
    assert record['host_safety_abort'] is True
    assert stopped == [True] and sleeps == []


def test_missing_gpu_stops_without_fabricated_peak(monkeypatch, tmp_path):
    sensor(tmp_path)
    record, stopped, sleeps = exercise(monkeypatch, tmp_path, gpu='')
    assert record == {'host_safety_monitor_failed': True}
    assert stopped == [True] and sleeps == []
