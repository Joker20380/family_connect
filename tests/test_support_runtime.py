import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import uuid

import pytest

from control.capture_gate import Busy, Gate, GateError


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests/fixtures/support_runtime.py'
INTERPRETER = os.environ.get('FC_TEST_SUPPORT_PYTHON', sys.executable)


def wait(predicate, seconds=12):
    deadline = time.monotonic() + seconds
    while not predicate():
        assert time.monotonic() < deadline, 'bounded fixture wait'
        time.sleep(.02)


@pytest.fixture
def launch(tmp_path):
    processes = []

    def start(mode):
        with (tmp_path / 'output').open('wb') as output:
            process = subprocess.Popen([INTERPRETER, '-I', '-B', str(FIXTURE), str(tmp_path), mode],
                                       stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
        processes.append(process)
        wait(lambda: (tmp_path / 'ready').exists() or process.poll() is not None)
        return process

    yield start
    (tmp_path / 'release').touch()
    for process in processes:
        if process.poll() is None:
            process.terminate()
        try:
            process.wait(8)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(5)


def finished(process, root):
    assert process.wait(12) == 0, (root / 'output').read_text()
    result = json.loads((root / 'result.json').read_bytes())
    assert result['threads'] == result['native_threads'] == 1
    assert result['hooks_restored']
    return result


def persisted(root, ratchet=False):
    code = ('import sys;from pathlib import Path;from RNS.vendor import umsgpack;'
            'root=Path(sys.argv[1]);data=umsgpack.unpackb((root/"runtime/storage/known_destinations").read_bytes());'
            'assert data[b"d"*16][2]==(root/"public").read_bytes();assert data[b"d"*16][3]==b"synthetic-lifecycle";'
            'assert len(list(Path("/proc/self/task").iterdir()))==1;')
    if ratchet:
        code += ('data=umsgpack.unpackb((root/"runtime/storage/ratchets"/(b"d"*16).hex()).read_bytes());'
                 'assert data["ratchet"]==b"r"*32;')
    subprocess.run([INTERPRETER, '-I', '-c', code, str(root)], check=True, capture_output=True, timeout=10)


def test_idle_native_runtime_releases_gate_only_after_all_jobs_and_final_flush(launch, tmp_path):
    process = launch('idle')
    assert process.poll() is None, (tmp_path / 'output').read_text()
    assert json.loads((tmp_path / 'loops.json').read_bytes()) == ['producer'] * 3 + ['queue']
    gate = Gate(tmp_path / 'gate')
    with pytest.raises(Busy):
        with gate.drain(.05):
            pytest.fail('runtime is still a writer')
    process.terminate()
    assert finished(process, tmp_path)['result'] == 'PASS'
    with gate.drain(.2):
        pass
    persisted(tmp_path)


@pytest.mark.parametrize('mode', ['periodic', 'queue', 'queue-descendant', 'async'])
def test_stop_waits_for_admitted_and_descendant_writes(launch, tmp_path, mode):
    process = launch(mode)
    wait(lambda: (tmp_path / 'writer-entered').exists())
    process.terminate()
    wait(lambda: (tmp_path / 'closing').exists())
    process.send_signal(signal.SIGINT)
    process.send_signal(signal.SIGTERM)
    time.sleep(.3)
    assert process.poll() is None and not (tmp_path / 'result.json').exists()
    with pytest.raises(Busy):
        with Gate(tmp_path / 'gate').drain(.05):
            pytest.fail('admitted writer has not finished')
    (tmp_path / 'release').touch()
    assert finished(process, tmp_path)['result'] == 'PASS'
    if mode == 'queue-descendant':
        assert (tmp_path / 'packet-second').exists() and (tmp_path / 'descendant-finished').exists()
    with Gate(tmp_path / 'gate').drain(.2):
        pass
    persisted(tmp_path, ratchet=mode != 'periodic')


def test_final_exit_write_is_inside_runtime_admission(launch, tmp_path):
    process = launch('exit-wait')
    process.terminate()
    wait(lambda: (tmp_path / 'exit-entered').exists())
    with pytest.raises(Busy):
        with Gate(tmp_path / 'gate').drain(.05):
            pytest.fail('exit persistence has not finished')
    (tmp_path / 'release').touch()
    assert finished(process, tmp_path)['result'] == 'PASS'
    persisted(tmp_path)


@pytest.mark.parametrize('mode,reason', [
    ('exit-failure', 'RNS_PERSISTENCE_UNCERTAIN'),
    ('thread-failure', 'RNS_PERSISTENCE_UNCERTAIN'),
    ('fsync-failure', 'synthetic fsync failure'),
    ('unsafe-state', 'RNS_STATE_SHAPE'),
    ('replaced-state', 'RNS_STATE_REPLACED'),
    ('caught-close-failure', 'RNS_PERSISTENCE_UNCERTAIN'),
    ('startup-failure', 'synthetic startup failure'),
    ('application-failure', 'synthetic application failure'),
])
def test_failures_keep_uncertainty_after_owned_threads_finish(launch, tmp_path, mode, reason):
    process = launch(mode)
    if process.poll() is None:
        process.terminate()
        (tmp_path / 'release').touch()
    result = finished(process, tmp_path)
    assert result['result'] == 'REFUSED' and result['reason'] == reason
    with pytest.raises(GateError, match='UNSETTLED_OPERATION'):
        with Gate(tmp_path / 'gate').drain(.2):
            pytest.fail('uncertainty was discarded')


@pytest.mark.parametrize('mode,reason', [('source-drift', 'RNS_SOURCE_PIN'),
                                       ('loaded-drift', 'RNS_LOADED_CODE'),
                                       ('outbound-enabled', 'RNS_QUEUE_SHAPE')])
def test_unsupported_runtime_refuses_before_starting_or_admitting(launch, tmp_path, mode, reason):
    process = launch(mode)
    assert process.wait(5) == 0
    result = json.loads((tmp_path / 'result.json').read_bytes())
    assert result['result'] == 'REFUSED' and result['reason'] == reason
    assert result['threads'] == result['native_threads'] == 1
    assert not (tmp_path / 'runtime').exists()
    with Gate(tmp_path / 'gate').drain(.2):
        pass


def test_process_death_does_not_settle_runtime_writes(launch, tmp_path):
    process = launch('async')
    wait(lambda: (tmp_path / 'writer-entered').exists())
    process.kill()
    assert process.wait(5) == -signal.SIGKILL
    with pytest.raises(GateError, match='UNSETTLED_OPERATION'):
        with Gate(tmp_path / 'gate').drain(.2):
            pytest.fail('killed runtime cannot authorize capture')


def test_native_systemd_waits_for_background_ratchet_beyond_old_timeout(tmp_path):
    if os.environ.get('FC_TEST_SYSTEMD_SUPPORT_DRAIN') != '1':
        pytest.skip('requires an owned user-systemd service')
    unit = 'fc-ha02-rns-lifecycle-' + uuid.uuid4().hex + '.service'

    def systemctl(*args):
        return subprocess.run(['systemctl', '--user', *args], capture_output=True,
                              text=True, check=True, timeout=15).stdout

    properties = [line for line in (ROOT / 'deploy/support-chat/family-connect-support.service').read_text().splitlines()
                  if line.startswith(('KillMode=', 'KillSignal=', 'SendSIGKILL=', 'TimeoutStopSec='))]
    assert set(properties) == {'KillMode=mixed', 'KillSignal=SIGTERM', 'SendSIGKILL=no', 'TimeoutStopSec=infinity'}
    command = ['systemd-run', '--user', '--quiet', '--unit=' + unit,
               '--property=Type=exec', '--property=Restart=no', '--property=UMask=0077']
    command.extend('--property=' + value for value in properties)
    if os.environ.get('FC_TEST_SUPPORT_ARCHIVE'):
        command.append('--setenv=FC_TEST_SUPPORT_ARCHIVE=' + os.environ['FC_TEST_SUPPORT_ARCHIVE'])
    command.extend([INTERPRETER, '-I', '-B', str(FIXTURE), str(tmp_path), 'async'])
    try:
        subprocess.run(command, check=True, capture_output=True, timeout=15)
        wait(lambda: (tmp_path / 'writer-entered').exists())
        systemctl('stop', '--no-block', unit)
        wait(lambda: (tmp_path / 'closing').exists())
        time.sleep(41)
        state = systemctl('show', unit, '--property=ActiveState,SubState,MainPID,Result')
        assert 'ActiveState=deactivating' in state and 'SubState=stop-sigterm' in state
        assert not (tmp_path / 'result.json').exists()
        with pytest.raises(Busy):
            with Gate(tmp_path / 'gate').drain(.05):
                pytest.fail('systemd must not interrupt the pending ratchet write')
        (tmp_path / 'release').touch()
        wait(lambda: (tmp_path / 'result.json').exists())
        wait(lambda: 'MainPID=0' in systemctl('show', unit, '--property=MainPID'))
        result = json.loads((tmp_path / 'result.json').read_bytes())
        assert result == {'result': 'PASS', 'threads': 1, 'native_threads': 1, 'hooks_restored': True}
        assert 'Result=success' in systemctl('show', unit, '--property=Result')
        assert 'ExecMainStatus=0' in systemctl('show', unit, '--property=ExecMainStatus')
        with Gate(tmp_path / 'gate').drain(.2):
            pass
        persisted(tmp_path, ratchet=True)
    finally:
        (tmp_path / 'release').touch()
        subprocess.run(['systemctl', '--user', 'stop', unit], capture_output=True, timeout=15)
        subprocess.run(['systemctl', '--user', 'reset-failed', unit], capture_output=True, timeout=10)
