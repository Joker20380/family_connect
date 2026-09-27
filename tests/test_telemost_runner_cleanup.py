import importlib.util
from pathlib import Path
import subprocess
import sys
from unittest.mock import Mock

import pytest


def reaper():
    path = Path(__file__).resolve().parents[1] / 'pilot/android-telemost/live.py'
    spec = importlib.util.spec_from_file_location('telemost_live_runner', path)
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module.reap_remote


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
