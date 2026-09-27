import importlib.util
from pathlib import Path
import subprocess
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
