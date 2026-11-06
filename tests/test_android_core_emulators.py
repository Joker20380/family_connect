import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest


spec = importlib.util.spec_from_file_location('core_emulators', Path(__file__).with_name('android_core_emulators.py'))
emulators = importlib.util.module_from_spec(spec)
spec.loader.exec_module(emulators)


@pytest.mark.parametrize('result', ['PASS_POSITIVE_PATH_ONLY', 'PASS_OWNER_RACE_ONLY', 'PASS_PARTIAL_CONNECT_ONLY', 'PASS_LATE_CLOSED_OWNER_ONLY'])
def test_only_explicit_completed_runtime_scopes_are_accepted(result):
    emulators.require_success(dict(result=result))


@pytest.mark.parametrize('result', ['FAIL', 'RUNNING', 'PASS_FULL_G3'])
def test_unknown_or_incomplete_runtime_scope_is_not_accepted(result):
    with pytest.raises(AssertionError):
        emulators.require_success(dict(result=result))


def test_real_wall_clock_allows_only_bounded_read_latency_and_rounding():
    emulators.require_wall_clock(100.5, 100, 100.6)


@pytest.mark.parametrize('before,guest,after', [(100.5, 93, 100.6), (100.5, 108, 100.6), (100, 100, 104), (101, 101, 100)])
def test_skew_never_qualifies_crypto_runtime(before, guest, after):
    with pytest.raises(AssertionError, match='clock skew'):
        emulators.require_wall_clock(before, guest, after)


def test_boot_clock_observation_waits_without_writing_time(monkeypatch):
    clocks, guests, commands = iter((100, 100.1, 103, 103.1)), iter(('93', '103')), []
    def read(command, **kwargs):
        commands.append(command)
        return next(guests)
    monkeypatch.setattr(emulators.time, 'time', lambda: next(clocks))
    monkeypatch.setattr(emulators.time, 'sleep', lambda seconds: None)
    monkeypatch.setattr(emulators.subprocess, 'check_output', read)
    record = {}
    emulators.observe_wall_clock(['adb', '-s', 'owned'], record)
    assert len(record['clock_samples']) == 2 and record['guest_wall_seconds'] == 103
    assert all(command[-3:] == ['shell', 'date', '+%s'] for command in commands)


def test_persistent_boot_clock_skew_remains_failure(monkeypatch):
    ticks = iter((0, 61))
    monkeypatch.setattr(emulators.time, 'monotonic', lambda: next(ticks))
    monkeypatch.setattr(emulators.time, 'time', lambda: 100)
    monkeypatch.setattr(emulators.subprocess, 'check_output', lambda *args, **kwargs: '93')
    record = {}
    with pytest.raises(AssertionError, match='clock skew'):
        emulators.observe_wall_clock(['adb', '-s', 'owned'], record)
    assert len(record['clock_samples']) == 1


def test_real_nvidia_renderer():
    renderer = 'GLES: Google (NVIDIA Corporation), Android Emulator OpenGL ES Translator (NVIDIA GeForce GTX 1650 Ti)'
    assert emulators.require_nvidia_renderer('header\n'+renderer+'\nfooter') == renderer


@pytest.mark.parametrize('surface', [
    '', 'GLES: Google SwiftShader', 'GLES: Mesa llvmpipe', 'GLES: lavapipe',
    'GPU: NVIDIA\nGLES: Google SwiftShader', 'GLES: NVIDIA software rasterizer',
    'GLES: NVIDIA SwiftShader', 'GLES: Intel UHD Graphics',
])
def test_missing_or_software_renderer_refused(surface):
    with pytest.raises(RuntimeError, match='hardware renderer required'):
        emulators.require_nvidia_renderer(surface)


def test_only_one_emulator_per_shared_directory(tmp_path):
    with emulators.emulator_slot(tmp_path):
        with pytest.raises(RuntimeError, match='already running'):
            with emulators.emulator_slot(tmp_path):
                pytest.fail('Concurrent emulator acquired the slot')
    with emulators.emulator_slot(tmp_path):
        pass


def test_slot_released_after_failure(tmp_path):
    with pytest.raises(ValueError):
        with emulators.emulator_slot(tmp_path):
            raise ValueError('fixture interruption')
    with emulators.emulator_slot(tmp_path):
        pass


def test_network_services_must_accept_both_commands(monkeypatch):
    codes = iter((0, 20, 0, 0))
    calls = []
    def run(command, **kwargs):
        calls.append(command)
        return SimpleNamespace(returncode=next(codes), stdout='', stderr='service starting')
    monkeypatch.setattr(emulators.subprocess, 'run', run)
    monkeypatch.setattr(emulators.time, 'sleep', lambda seconds: None)
    record = {}
    emulators.configure_network(['adb', '-s', 'owned'], True, record)
    assert len(calls) == 4
    assert calls[0][-2:] == ['wifi', 'enable'] and calls[-1][-2:] == ['data', 'disable']
    assert [value['code'] for value in record['network_setup']] == [0, 20, 0, 0]


def test_network_service_failure_is_not_ignored(monkeypatch):
    ticks = iter((0, 61))
    monkeypatch.setattr(emulators.time, 'monotonic', lambda: next(ticks))
    monkeypatch.setattr(emulators.subprocess, 'run', lambda *args, **kwargs:
        SimpleNamespace(returncode=20, stdout='', stderr='service unavailable'))
    record = {}
    with pytest.raises(RuntimeError, match='network services unavailable'):
        emulators.configure_network(['adb', '-s', 'owned'], True, record)
    assert len(record['network_setup']) == 2
