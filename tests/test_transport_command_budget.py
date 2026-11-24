import os
import signal
import subprocess
import sys
import time

import pytest

from control.friends import transport_gateway as module


@pytest.mark.parametrize('spawn_delay,seconds', [(.35, .6), (.3, .2)])
def test_spawn_consumes_same_deadline(tmp_path, monkeypatch, spawn_delay, seconds):
    marker = tmp_path / 'late-actuation'
    original = subprocess.Popen
    children = []

    def delayed_spawn(*arguments, **keywords):
        time.sleep(spawn_delay)
        child = original(*arguments, **keywords)
        children.append(child)
        return child

    monkeypatch.setattr(module.subprocess, 'Popen', delayed_spawn)
    token = module.CURRENT_OPERATION.set(module.Operation(seconds))
    try:
        with pytest.raises((TimeoutError, subprocess.TimeoutExpired)):
            module.execute([sys.executable, '-c',
                'import pathlib,sys,time;time.sleep(.4 if sys.argv[2]=="long" else .1);'
                'pathlib.Path(sys.argv[1]).touch()', str(marker),
                'long' if seconds == .6 else 'short'])
        assert not marker.exists(), 'child received the pre-spawn budget again'
        assert all(child.poll() is not None for child in children)
    finally:
        module.CURRENT_OPERATION.reset(token)
        for child in children:
            if child.poll() is None:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait(timeout=2)


def test_exited_leader_with_open_descendant_pipe_is_killed(tmp_path):
    marker = tmp_path / 'descendant-late-write'
    token = module.CURRENT_OPERATION.set(module.Operation(.15))
    try:
        with pytest.raises(subprocess.TimeoutExpired):
            module.execute([sys.executable, '-c',
                'import subprocess,sys;subprocess.Popen([sys.executable,"-c",'
                '"import pathlib,sys,time;time.sleep(.4);pathlib.Path(sys.argv[1]).touch()",sys.argv[1]])',
                str(marker)])
    finally:
        module.CURRENT_OPERATION.reset(token)
    time.sleep(.5)
    assert not marker.exists()


def test_command_boundaries_and_no_raw_output():
    operation = module.Operation()
    token = module.CURRENT_OPERATION.set(operation)
    try:
        assert module.execute([sys.executable, '-c',
            'import sys;print("private-output");print("private-error",file=sys.stderr)']) == b'private-output\n'
    finally:
        module.CURRENT_OPERATION.reset(token)
    details = operation.calls[0]['process']
    assert details['spawn']['completed'] and details['communicate']['completed']
    assert details['communicate']['remaining'] < details['spawn']['remaining']
    assert details['stdout_bytes'] == 15 and details['stderr_bytes'] == 14
    assert details['returncode'] == 0 and 'private-' not in repr(details)


def test_cleanup_cannot_replace_primary_exit_failure(monkeypatch):
    def missing_group(pid, number):
        raise ProcessLookupError()

    monkeypatch.setattr(module.os, 'killpg', missing_group)
    operation = module.Operation()
    token = module.CURRENT_OPERATION.set(operation)
    try:
        with pytest.raises(subprocess.CalledProcessError) as failure:
            module.execute([sys.executable, '-c', 'raise SystemExit(23)'])
        assert failure.value.returncode == 23
    finally:
        module.CURRENT_OPERATION.reset(token)
    assert operation.calls[0]['process']['reaped'] is True


def test_cleanup_does_not_drain_inherited_pipes(monkeypatch):
    original = subprocess.Popen
    calls = []

    class Child(original):
        def communicate(self, *arguments, **keywords):
            calls.append(keywords.get('timeout'))
            if len(calls) > 1:
                pytest.fail('cleanup attempted an unbounded second pipe drain')
            return super().communicate(*arguments, **keywords)

    monkeypatch.setattr(module.subprocess, 'Popen', Child)
    token = module.CURRENT_OPERATION.set(module.Operation(.1))
    try:
        with pytest.raises(subprocess.TimeoutExpired):
            module.execute([sys.executable, '-c', 'import time;time.sleep(5)'])
    finally:
        module.CURRENT_OPERATION.reset(token)
    assert len(calls) == 1
