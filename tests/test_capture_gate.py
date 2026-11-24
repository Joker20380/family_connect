import contextlib
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import threading
import time

import pytest

from control.capture_gate import Busy, Gate, GateError, external_operation, initialize

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def gate(tmp_path):
    return initialize(tmp_path / 'capture')


def pending(gate):
    return list((gate.directory / 'pending').iterdir())


def test_clean_nested_operations_use_one_marker(gate):
    with gate.operation() as operation:
        assert len(pending(gate)) == 1
        with Gate(gate.directory).operation() as nested:
            assert operation is nested and len(pending(gate)) == 1
        with Gate().operation() as disabled:
            assert disabled is operation
    assert not pending(gate)
    with gate.drain(.1):
        with pytest.raises(Busy):
            with gate.operation():
                pytest.fail('admitted')


def test_disabled_gate_creates_nothing_and_cannot_drain(tmp_path):
    with Gate().operation():
        with external_operation():
            pass
    assert list(tmp_path.iterdir()) == []
    with pytest.raises(GateError):
        with Gate().drain(.1):
            pytest.fail('disabled drain')


@pytest.mark.parametrize('caught', [True, False])
def test_ambiguous_external_operation_survives_caught_error(gate, caught):
    with contextlib.suppress(TimeoutError):
        with gate.operation():
            try:
                with external_operation():
                    raise TimeoutError('private-error')
            except TimeoutError:
                if not caught:
                    raise
    assert len(pending(gate)) == 1
    assert b'private-error' not in pending(gate)[0].read_bytes()
    with pytest.raises(GateError, match='UNSETTLED_OPERATION'):
        with gate.drain(.1):
            pytest.fail('uncertain drain')
    with gate.operation():
        pass
    assert len(pending(gate)) == 1


def test_unknown_pending_entry_refuses_without_removal(gate):
    path = gate.directory / 'pending/unknown'
    path.write_text('private')
    with pytest.raises(GateError, match='UNSETTLED_OPERATION'):
        with gate.drain(.1):
            pytest.fail('unknown accepted')
    assert path.read_text() == 'private'


@pytest.mark.parametrize('target', ['.', 'admission.lock', 'operations.lock', 'pending'])
def test_pinned_inode_replacement_refuses(gate, target):
    path = gate.directory / target
    displaced = path.with_name(path.name + '-old')
    path.rename(displaced)
    if target in ('.', 'pending'):
        path.mkdir(mode=0o700)
    else:
        path.touch(mode=0o600)
    with pytest.raises(GateError, match='GATE_REPLACED'):
        with gate.operation():
            pytest.fail('replaced')


@pytest.mark.parametrize('target,mode', [('.', 0o777), ('pending', 0o755), ('admission.lock', 0o666)])
def test_unsafe_modes_refuse(gate, target, mode):
    (gate.directory / target).chmod(mode)
    with pytest.raises(GateError, match='GATE_PERMISSIONS'):
        with gate.operation():
            pytest.fail('unsafe mode')


def test_symlink_hardlink_and_nonempty_lock_refuse(gate, tmp_path):
    path = gate.directory / 'admission.lock'
    path.write_text('not a lock')
    with pytest.raises(GateError):
        Gate(gate.directory)
    path.write_bytes(b'')
    os.link(path, tmp_path / 'alias')
    with pytest.raises(GateError):
        Gate(gate.directory)
    path.unlink()
    path.symlink_to(tmp_path / 'alias')
    with pytest.raises(OSError):
        Gate(gate.directory)


@pytest.mark.parametrize('timeout', [0, -1, True, float('inf'), float('nan'), 5.01])
def test_invalid_drain_timeout(gate, timeout):
    with pytest.raises(GateError, match='DRAIN_DEADLINE'):
        with gate.drain(timeout):
            pytest.fail('deadline')


def test_drain_timeout_releases_admission_without_killing_writer(gate):
    ready, finish = threading.Event(), threading.Event()
    def write():
        with gate.operation():
            ready.set()
            assert finish.wait(3)
    writer = threading.Thread(target=write)
    writer.start()
    assert ready.wait(2)
    try:
        with pytest.raises(Busy, match='DRAIN_TIMEOUT'):
            with gate.drain(.03):
                pytest.fail('writer was active')
        assert writer.is_alive()
        with gate.operation():
            pass
    finally:
        finish.set()
        writer.join(3)
    assert not writer.is_alive() and not pending(gate)


@contextlib.contextmanager
def child(command, *arguments):
    process = subprocess.Popen([sys.executable, *command, *map(str, arguments)], cwd=ROOT,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        yield process
    finally:
        if process.poll() is None:
            process.kill()
        process.communicate(timeout=3)


def line(process):
    assert select.select([process.stdout], [], [], 3)[0], 'missing bounded response'
    result = process.stdout.readline()
    assert result, process.stderr.read()
    return result


GUARD = ['-m', 'scripts.control_ha_capture_guard']


def test_guard_waits_for_admitted_writer_and_refuses_new_admission(gate):
    ready, finish = threading.Event(), threading.Event()
    def write():
        with gate.operation():
            ready.set()
            assert finish.wait(4)
    writer = threading.Thread(target=write)
    writer.start()
    assert ready.wait(2)
    try:
        with child(GUARD, '--gate', gate.directory) as coordinator:
            deadline = time.monotonic() + 2
            while True:
                try:
                    with gate.operation():
                        pass
                except Busy:
                    break
                assert time.monotonic() < deadline
                time.sleep(.005)
            assert not select.select([coordinator.stdout], [], [], .03)[0]
            finish.set()
            receipt = json.loads(line(coordinator))
            assert receipt['status'] == 'LOCAL_DRAINED' and receipt['capture_permitted'] is False
            with pytest.raises(Busy):
                with gate.operation():
                    pytest.fail('admitted while held')
            coordinator.stdin.write('RELEASE ' + receipt['operation'] + '\n')
            coordinator.stdin.flush()
            assert json.loads(line(coordinator))['status'] == 'RELEASED'
            assert coordinator.wait(timeout=2) == 0
    finally:
        finish.set()
        writer.join(3)
    with gate.operation():
        pass


@pytest.mark.parametrize('failure', ['eof', 'kill', 'deadline', 'bad-token'])
def test_guard_failure_releases_own_locks(gate, failure):
    with child(GUARD, '--gate', gate.directory, '--hold-seconds', .15 if failure == 'deadline' else 2) as coordinator:
        assert json.loads(line(coordinator))['status'] == 'LOCAL_DRAINED'
        if failure == 'eof':
            coordinator.stdin.close()
            coordinator.stdin = None
        elif failure == 'kill':
            coordinator.kill()
        elif failure == 'bad-token':
            coordinator.stdin.write('RELEASE wrong\n')
            coordinator.stdin.flush()
        status = coordinator.wait(timeout=3)
        assert status == {'eof': 0, 'kill': -signal.SIGKILL, 'deadline': -signal.SIGALRM, 'bad-token': 1}[failure]
    with gate.operation():
        pass
    assert not pending(gate)


def test_two_coordinators_cannot_steal_each_others_boundary(gate):
    with child(GUARD, '--gate', gate.directory) as coordinator:
        line(coordinator)
        with child(GUARD, '--gate', gate.directory) as other:
            assert json.loads(line(other))['status'] == 'REFUSED'
            assert other.wait(timeout=2) == 1
        with pytest.raises(Busy):
            with gate.operation():
                pytest.fail('second coordinator released first')


def test_guard_setup_cannot_extend_total_deadline(gate):
    program = '''
import time
from scripts import control_ha_capture_guard as guard
original = guard.Gate
def delayed(path):
    time.sleep(.8)
    return original(path)
guard.Gate = delayed
guard.main()
'''
    with child(['-c', program], '--gate', gate.directory,
               '--drain-seconds', .5, '--hold-seconds', .6) as coordinator:
        receipt = json.loads(line(coordinator))
        assert 0 < receipt['hold_seconds'] <= .3
        assert coordinator.wait(timeout=.5) == -signal.SIGALRM
    with gate.operation():
        pass


@pytest.mark.parametrize('setup', [
    'signal.pthread_sigmask(signal.SIG_BLOCK, [signal.SIGALRM])',
    'signal.signal(signal.SIGALRM, signal.SIG_IGN)',
])
def test_guard_refuses_unusable_inherited_alarm(gate, setup):
    program = 'import signal;from scripts import control_ha_capture_guard as guard;' + setup + ';guard.main()'
    with child(['-c', program], '--gate', gate.directory) as coordinator:
        output, error = coordinator.communicate(timeout=2)
        assert coordinator.returncode != 0 and 'ALARM_NOT_EXCLUSIVE' in error and not output
    with gate.operation():
        pass


def test_writer_death_leaves_durable_uncertainty_not_a_false_drain(gate):
    program = ('import sys;from control.capture_gate import Gate\n'
               'with Gate(sys.argv[1]).operation():\n print("ready",flush=True);sys.stdin.readline()\n')
    with child(['-c', program], gate.directory) as writer:
        assert line(writer).strip() == 'ready'
        writer.kill()
        writer.wait(timeout=2)
    assert len(pending(gate)) == 1
    with child(GUARD, '--gate', gate.directory) as coordinator:
        assert json.loads(line(coordinator))['status'] == 'REFUSED'
        assert coordinator.wait(timeout=2) == 1
    assert len(pending(gate)) == 1


def test_initialization_never_overwrites_existing_state(gate):
    before = {name: (gate.directory / name).stat().st_ino for name in ('admission.lock', 'operations.lock')}
    with pytest.raises(FileExistsError):
        initialize(gate.directory)
    assert before == {name: (gate.directory / name).stat().st_ino for name in before}
