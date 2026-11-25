import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
from types import SimpleNamespace
import uuid

import pytest

from control.capture_gate import Busy, Gate, GateError
from provisioning import support_lifecycle as lifecycle
from provisioning.support_worker import SupportStore


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests/fixtures/support_lifecycle.py'
INTERPRETER = os.environ.get('FC_TEST_SUPPORT_PYTHON', sys.executable)


def wait_for(predicate, seconds=15):
    deadline = time.monotonic() + seconds
    while not predicate():
        assert time.monotonic() < deadline, 'bounded fixture wait'
        time.sleep(.02)


@pytest.fixture
def launch(tmp_path):
    processes = []

    def start(mode):
        output = (tmp_path / 'output').open('wb')
        process = subprocess.Popen([INTERPRETER, '-B', str(FIXTURE), str(tmp_path), mode],
                                   stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
        output.close()
        processes.append(process)
        wait_for(lambda: (tmp_path / ('startup-entered' if mode == 'startup' else 'ready')).exists()
                 or process.poll() is not None)
        assert process.poll() is None, (tmp_path / 'output').read_text()
        return process

    yield start
    (tmp_path / 'release').touch()
    for process in processes:
        if process.poll() is None:
            process.terminate()
        try:
            process.wait(10)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(5)


def assert_finished(process, root, *, committed=False):
    assert process.wait(10) == 0, (root / 'output').read_text()
    assert (root / 'finished').exists() and (root / 'store-closed').exists()
    assert not (root / 'worker.sock').exists()
    if os.environ.get('FC_TEST_SUPPORT_ARCHIVE'):
        assert (root / 'archive-qualified').exists()
    store = SupportStore(root / 'store', b's' * 32, create=False)
    try:
        assert store._get('lifecycle-synthetic') == ({'completed': True} if committed else None)
    finally:
        store.close()


@pytest.mark.parametrize('mode', ['exchange', 'exchange-failure'])
def test_stop_waits_for_delivery_child_and_keeps_failure_pending(launch, tmp_path, mode):
    process = launch(mode)
    wait_for(lambda: (tmp_path / 'child-pid').exists())
    process.terminate()
    wait_for(lambda: not (tmp_path / 'worker.sock').exists())
    for signum in (signal.SIGINT, signal.SIGTERM):
        process.send_signal(signum)
    time.sleep(1.2)
    assert process.poll() is None and not (tmp_path / 'store-closed').exists()
    os.kill(int((tmp_path / 'child-pid').read_text()), 0)
    gate = Gate(tmp_path / 'gate')
    with pytest.raises(Busy):
        with gate.drain(.05):
            pytest.fail('delivery has not returned')
    (tmp_path / 'release').touch()
    assert_finished(process, tmp_path, committed=True)
    assert (tmp_path / 'child-finished').exists()
    if mode == 'exchange-failure':
        with pytest.raises(GateError, match='UNSETTLED_OPERATION'):
            with gate.drain(.2):
                pytest.fail('local exit is not an external acknowledgement')
    else:
        with gate.drain(.2):
            pass


def test_stop_finishes_admitted_ipc_commit_before_exit(launch, tmp_path):
    process = launch('ipc')
    with socket.socket(socket.AF_UNIX) as connection:
        connection.settimeout(10)
        connection.connect(str(tmp_path / 'worker.sock'))
        connection.sendall(b'{"operation":"notification_cursor","arguments":{}}\n')
        wait_for(lambda: (tmp_path / 'ipc-entered').exists())
        process.terminate()
        process.send_signal(signal.SIGINT)
        time.sleep(.2)
        assert process.poll() is None and not (tmp_path / 'store-closed').exists()
        (tmp_path / 'release').touch()
        assert json.loads(connection.recv(4096))['ok']
    assert_finished(process, tmp_path, committed=True)


def test_runtime_lifetime_prevents_capture_before_store_close(launch, tmp_path):
    process = launch('idle')
    gate = Gate(tmp_path / 'gate')
    time.sleep(.3)
    with pytest.raises(Busy):
        with gate.drain(.05):
            pytest.fail('idle RNS jobs are still writers')
    process.terminate()
    assert_finished(process, tmp_path)
    with gate.drain(.2):
        pass


def test_support_store_stays_open_until_async_rns_write_finishes(launch, tmp_path):
    process = launch('runtime-async')
    wait_for(lambda: (tmp_path / 'runtime-writer-entered').exists())
    process.terminate()
    wait_for(lambda: not (tmp_path / 'worker.sock').exists())
    time.sleep(.3)
    assert process.poll() is None and not (tmp_path / 'store-closed').exists()
    with pytest.raises(Busy):
        with Gate(tmp_path / 'gate').drain(.05):
            pytest.fail('support runtime still owns a pending write')
    (tmp_path / 'release').touch()
    assert_finished(process, tmp_path)
    assert (tmp_path / 'runtime-writer-finished').exists()
    code = ('import sys;from pathlib import Path;from RNS.vendor import umsgpack;'
            'root=Path(sys.argv[1]);data=umsgpack.unpackb((root/"runtime/storage/ratchets"/(b"d"*16).hex()).read_bytes());'
            'assert data["ratchet"]==b"r"*32')
    subprocess.run([INTERPRETER, '-I', '-c', code, str(tmp_path)], check=True, capture_output=True, timeout=10)
    with Gate(tmp_path / 'gate').drain(.2):
        pass


def test_support_exit_persistence_failure_is_not_clean_capture(launch, tmp_path):
    process = launch('runtime-exit-failure')
    process.terminate()
    assert process.wait(12) != 0
    assert (tmp_path / 'store-closed').exists()
    assert 'RNS_PERSISTENCE_UNCERTAIN' in (tmp_path / 'output').read_text()
    with pytest.raises(GateError, match='UNSETTLED_OPERATION'):
        with Gate(tmp_path / 'gate').drain(.2):
            pytest.fail('failed RNS persistence must remain unsettled')


def test_startup_signal_finishes_initialization_without_opening_listener(launch, tmp_path):
    process = launch('startup')
    process.terminate()
    process.send_signal(signal.SIGINT)
    time.sleep(.2)
    assert process.poll() is None and not (tmp_path / 'ready').exists()
    (tmp_path / 'release').touch()
    assert_finished(process, tmp_path)
    assert not (tmp_path / 'ready').exists()


def test_partial_header_is_bounded_but_not_interrupted_by_termination(launch, tmp_path):
    process = launch('idle')
    with socket.socket(socket.AF_UNIX) as connection:
        connection.connect(str(tmp_path / 'worker.sock'))
        connection.sendall(b'{')
        time.sleep(.3)
        process.terminate()
        time.sleep(.3)
        assert process.poll() is None
        assert_finished(process, tmp_path)


def test_drain_never_treats_false_close_as_completion():
    calls = []

    def close(**kwargs):
        calls.append(kwargs)
        return len(calls) == 35

    lifecycle.drain_delivery(SimpleNamespace(close=close))
    assert calls == [{'timeout': 1}] * 35


def test_invalid_gate_is_not_retried_as_busy_or_success():
    def close():
        raise GateError('GATE_PERMISSIONS')

    with pytest.raises(GateError, match='GATE_PERMISSIONS'):
        lifecycle.close_store(SimpleNamespace(close=close))


def test_socket_replacement_is_preserved(tmp_path):
    path = tmp_path / 'socket'
    with socket.socket(socket.AF_UNIX) as original, socket.socket(socket.AF_UNIX) as replacement:
        original.bind(str(path))
        info = path.lstat()
        path.unlink()
        replacement.bind(str(path))
        lifecycle.unlink_socket(path, (info.st_dev, info.st_ino))
        assert path.exists()
    path.unlink()
    lifecycle.unlink_socket(path, (info.st_dev, info.st_ino))


def test_signal_handlers_restored_on_failure():
    before = {signum: signal.getsignal(signum) for signum in (signal.SIGTERM, signal.SIGINT)}
    with pytest.raises(ValueError):
        with lifecycle.stop_requested() as stopped:
            signal.raise_signal(signal.SIGTERM)
            signal.raise_signal(signal.SIGINT)
            assert stopped.is_set()
            raise ValueError()
    assert {signum: signal.getsignal(signum) for signum in before} == before


def test_actual_systemd_stop_preserves_child_beyond_old_deadlines(tmp_path):
    if os.environ.get('FC_TEST_SYSTEMD_SUPPORT_DRAIN') != '1':
        pytest.skip('requires an owned user-systemd service')
    unit = 'fc-support-lifecycle-test-' + uuid.uuid4().hex + '.service'
    settings = (ROOT / 'deploy/support-chat/family-connect-support.service').read_text().splitlines()
    paired = [line for line in settings if line.startswith(('KillMode=', 'KillSignal=', 'SendSIGKILL=', 'TimeoutStopSec='))]
    assert set(paired) == {'KillMode=mixed', 'KillSignal=SIGTERM', 'SendSIGKILL=no', 'TimeoutStopSec=infinity'}
    directory = Path(os.environ['XDG_RUNTIME_DIR']) / 'systemd/user'
    directory.mkdir(parents=True, exist_ok=True)
    unit_path = directory / unit
    archive = os.environ.get('FC_TEST_SUPPORT_ARCHIVE')
    environment = 'Environment=' + json.dumps('FC_TEST_SUPPORT_ARCHIVE=' + archive) + '\n' if archive else ''
    unit_path.write_text('[Service]\nType=exec\nRestart=no\n' + environment + '\n'.join(paired) + '\nExecStart=' +
                         f'{INTERPRETER} -B {FIXTURE} {tmp_path} exchange\n')

    def systemctl(*args):
        return subprocess.run(['systemctl', '--user', *args], capture_output=True, text=True, check=True, timeout=10).stdout

    try:
        systemctl('daemon-reload')
        systemctl('start', unit)
        wait_for(lambda: (tmp_path / 'child-pid').exists())
        systemctl('stop', '--no-block', unit)
        time.sleep(41)
        state = systemctl('show', unit, '--property=ActiveState,SubState,MainPID,Result')
        assert 'ActiveState=deactivating' in state and 'SubState=stop-sigterm' in state
        assert 'Result=success' in state
        os.kill(int((tmp_path / 'child-pid').read_text()), 0)
        assert not (tmp_path / 'store-closed').exists()
        (tmp_path / 'release').touch()
        wait_for(lambda: (tmp_path / 'finished').exists())
        wait_for(lambda: 'MainPID=0' in systemctl('show', unit, '--property=MainPID'))
        assert (tmp_path / 'child-finished').exists() and (tmp_path / 'committed').exists()
        if archive:
            assert (tmp_path / 'archive-qualified').exists()
        assert 'ExecMainStatus=0' in systemctl('show', unit, '--property=ExecMainStatus')
        assert 'Result=success' in systemctl('show', unit, '--property=Result')
        store = SupportStore(tmp_path / 'store', b's' * 32, create=False)
        try:
            assert store._get('lifecycle-synthetic') == {'completed': True}
        finally:
            store.close()
        with Gate(tmp_path / 'gate').drain(.2):
            pass
    finally:
        (tmp_path / 'release').touch()
        subprocess.run(['systemctl', '--user', 'stop', unit], capture_output=True, timeout=15)
        subprocess.run(['systemctl', '--user', 'reset-failed', unit], capture_output=True, timeout=10)
        unit_path.unlink()
        systemctl('daemon-reload')
