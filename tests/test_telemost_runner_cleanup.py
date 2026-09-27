import importlib.util
from pathlib import Path
import subprocess
import shlex
import sys
from unittest.mock import Mock

import pytest


def runner_module():
    path = Path(__file__).resolve().parents[1] / 'pilot/android-telemost/live.py'
    spec = importlib.util.spec_from_file_location('telemost_live_runner', path)
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


def reaper():
    return runner_module().reap_remote


def test_completed_remote_preserves_exit():
    remote = Mock()
    remote.wait.return_value = 1
    assert reaper()(remote) == 1
    remote.terminate.assert_not_called()
    remote.kill.assert_not_called()


def test_android_incremental_read_cannot_capture_missing_file_error():
    command = runner_module().android_evidence_command('test-adb', 42)
    script = command[-1]
    assert script == 'test -f files/evidence.jsonl && tail -c +43 files/evidence.jsonl 2>/dev/null'


@pytest.mark.parametrize('force', [False, True])
def test_observer_timeout_reaps_but_never_masks_failure(force):
    remote = Mock()
    timeout = subprocess.TimeoutExpired(['test-only-ssh'], 15)
    remote.wait.side_effect = [timeout, timeout, -9] if force else [timeout, -15]
    with pytest.raises(RuntimeError, match='REMOTE_OBSERVER_TIMEOUT_AFTER_CLEANUP'):
        reaper()(remote)
    remote.terminate.assert_called_once()
    assert remote.kill.call_count == int(force)


def test_independent_observer_preserves_remote_failure(tmp_path, monkeypatch):
    module = runner_module()
    monkeypatch.setattr(module.subprocess, 'check_output', lambda *args, **kwargs:
                        '{"B.jsonl":"{\\"event\\":\\"summary\\"}\\n","B.stderr":"test failure","exit.code":"1"}')
    remote = module.IndependentEcho(['test-only-ssh'], '/tmp/test-only-echo', tmp_path)
    assert remote.collect() == 1
    assert remote.returncode == 1
    assert (tmp_path / 'B.stderr').read_text() == 'test failure'


def test_independent_observer_room_only_in_stdin(tmp_path, monkeypatch):
    module = runner_module()
    execute = Mock()
    monkeypatch.setattr(module.subprocess, 'run', execute)
    remote = module.IndependentEcho(['test-only-ssh'], '/tmp/test-only-echo', tmp_path)
    room = 'NOT-A-REAL-ROOM-TEST-ONLY'
    remote.start(room, ['./telemost-live', '--mode', 'vp8'])
    arguments, options = execute.call_args
    assert room not in ' '.join(arguments[0])
    assert options['input'] == room + '\n'
    assert options['timeout'] == 30 and options['check'] is True
    assert 'exit.pending' in arguments[0][-1]


def test_independent_observer_collects_incrementally(tmp_path, monkeypatch):
    module = runner_module()
    responses = iter(['{"B.jsonl":"first\\n"}', '{"B.jsonl":"second\\n","exit.code":"0"}'])
    execute = Mock(side_effect=lambda *args, **kwargs: next(responses))
    monkeypatch.setattr(module.subprocess, 'check_output', execute)
    remote = module.IndependentEcho(['test-only-ssh'], '/tmp/test-only-echo', tmp_path)
    assert remote.collect() is None
    assert remote.collect() == 0
    assert (tmp_path / 'B.jsonl').read_text() == 'first\nsecond\n'
    assert "'B.jsonl': 6" in shlex.split(execute.call_args.args[0][-1])[-1]


@pytest.mark.parametrize('extra', [[], ['--family-dir', '/unused'],
                                    ['--tcp-test-loopback-port', '65536']])
def test_tcp_requires_authenticated_exclusive_mode(extra, monkeypatch):
    module = runner_module()
    monkeypatch.setattr(sys, 'argv', ['live.py', '--binary', '/unused', '--out', '/unused',
                                     '--tcp-config', '/unused', *extra])
    remote = Mock()
    monkeypatch.setattr(module.subprocess, 'check_output', remote)
    with pytest.raises(SystemExit) as caught:
        module.main()
    assert caught.value.code == 2
    remote.assert_not_called()
