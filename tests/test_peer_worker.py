import importlib.util
from pathlib import Path
import subprocess
import select
import sys
import threading
from unittest.mock import patch


spec = importlib.util.spec_from_file_location(
    'peer_worker', Path(__file__).parents[1] / 'deploy/product-peer-worker/worker.py')
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)


def test_success_and_failure():
    assert worker.run_cycle([sys.executable, '-c', 'pass'], 2) == 0
    assert worker.run_cycle([sys.executable, '-c', 'raise SystemExit(7)'], 2) == 7


def test_timeout_reaps_process():
    assert worker.run_cycle([sys.executable, '-c', 'import time; time.sleep(10)'], .1) == 124


def test_timeout_kills_group():
    with patch.object(worker.subprocess, 'Popen') as launch, patch.object(worker.os, 'killpg') as kill:
        launch.return_value.pid = 12345
        launch.return_value.wait.side_effect = [subprocess.TimeoutExpired('child', 1), -9]
        assert worker.run_cycle(['child'], 1) == 124
        kill.assert_called_once_with(12345, worker.signal.SIGKILL)
        assert launch.return_value.wait.call_count == 2
        launch.assert_called_once_with(['child'], start_new_session=True,
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def test_retry_and_stop(capsys):
    stop = threading.Event()
    outcomes = iter([OSError(), 1, 0])

    def cycle(command, timeout):
        outcome = next(outcomes)
        if isinstance(outcome, Exception):
            raise outcome
        if outcome == 0:
            stop.set()
        return outcome

    with patch.object(worker, 'run_cycle', side_effect=cycle) as run:
        worker.run_loop(['child'], stop, interval=0)
    assert run.call_count == 3
    assert '"exit_code": 127' in capsys.readouterr().out


def test_already_stopped_does_not_start():
    stop = threading.Event()
    stop.set()
    with patch.object(worker, 'run_cycle') as run:
        worker.run_loop(['child'], stop)
    run.assert_not_called()


def test_process_disappears_during_timeout():
    with patch.object(worker.subprocess, 'Popen') as launch, patch.object(
            worker.os, 'killpg', side_effect=ProcessLookupError):
        launch.return_value.wait.side_effect = [subprocess.TimeoutExpired('child', 1), 0]
        assert worker.run_cycle(['child'], 1) == 124
        assert launch.return_value.wait.call_count == 2


def test_sigterm_finishes_cycle_without_another_start():
    source = '''
import sys, time
sys.path.insert(0, sys.argv.pop(1))
import worker
def cycle(command, timeout):
    print('cycle-started', flush=True)
    time.sleep(.2)
    print('cycle-finished', flush=True)
    return 0
worker.run_cycle = cycle
worker.main()
'''
    process = subprocess.Popen(
        [sys.executable, '-c', source, str(Path(spec.origin).parent),
         '--database', 'unused', '--gateways', 'unused'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        assert select.select([process.stdout], [], [], 3)[0]
        assert process.stdout.readline().strip() == 'cycle-started'
        process.terminate()
        output, error = process.communicate(timeout=3)
        assert process.returncode == 0, error
        assert 'cycle-finished' in output
        assert 'cycle-started' not in output
    finally:
        if process.poll() is None:
            process.kill()
        process.wait()
