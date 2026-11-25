import http.client
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import sqlite3
import subprocess
import sys
import time
import uuid

import pytest

from scripts import control_ha_receiver_replace as replace


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests/fixtures/receiver_replacement.py'


def wait_for(predicate, seconds=10):
    deadline = time.monotonic() + seconds
    while not predicate():
        assert time.monotonic() < deadline, 'bounded fixture wait'
        time.sleep(.03)


def ready(port):
    try:
        return replace.request(port) == (400, {'error': 'invalid-request'})
    except (OSError, ValueError, http.client.HTTPException):
        return False


@pytest.fixture
def service(tmp_path):
    baseline = os.environ.get('FC_TEST_RECEIVER_BASELINE')
    candidate = os.environ.get('FC_TEST_HTTP_RUNTIME')
    if not baseline or not candidate or os.environ.get('FC_TEST_SYSTEMD_HTTP_DRAIN') != '1':
        pytest.skip('requires pinned private archives and owned user-systemd fixtures')
    unit = 'fc-ha-replace-test-' + uuid.uuid4().hex + '.service'
    directory = Path(os.environ['XDG_RUNTIME_DIR']) / 'systemd/user'
    directory.mkdir(parents=True, exist_ok=True)
    unit_path = directory / unit
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        port = listener.getsockname()[1]
    data = tmp_path / 'data'
    data.mkdir(mode=0o700)
    with sqlite3.connect(data / 'preserved.sqlite') as database:
        database.execute('CREATE TABLE history(value INTEGER)')
        database.execute('INSERT INTO history VALUES(1)')
    command = f'{sys.executable} {FIXTURE} {baseline} --root {data} --port {port}'
    unit_path.write_text('[Service]\nType=simple\nRestart=no\nExecStart=' + command + '\n')
    manager = replace.Manager(unit, user=True)
    try:
        manager.call('daemon-reload')
        manager.call('start', unit)
        wait_for(lambda: manager.state()['ActiveState'] == 'active')
        wait_for(lambda: ready(port))
        output = tmp_path / 'replacement'
        plan = replace.prepare(manager, baseline, candidate, output)
        yield manager, plan, output, data
    finally:
        manager.call('stop', unit, '--no-block')
        deadline = time.monotonic() + 5
        while manager.state()['MainPID'] != '0' and time.monotonic() < deadline:
            time.sleep(.05)
        if manager.state()['MainPID'] != '0':
            manager.call('kill', '--signal=SIGKILL', unit)
        unit_path.unlink()
        shutil.rmtree(Path(str(unit_path) + '.d'), ignore_errors=True)
        manager.call('daemon-reload')
        subprocess.run([*manager.command, 'reset-failed', unit], capture_output=True)


@pytest.mark.parametrize('attempt', range(5))
def test_real_pair_activation_retains_old_source_and_blocks_gate(service, attempt):
    manager, plan, root, data = service
    result = replace.Replacement(root).run()
    assert result == 'ACCEPTED'
    state = manager.state()
    assert int(state['MainPID']) != plan['old_binding']['pid']
    assert all(state[key] == value for key, value in replace.SETTINGS.items())
    assert replace.argv(int(state['MainPID'])) == plan['new_argv']
    assert replace.digest(plan['baseline']) == replace.bridge.BASELINE
    assert len(list((Path(plan['gate']) / 'pending').iterdir())) == 1
    accepted = json.loads((root / 'accepted.json').read_text())
    assert accepted['capture_permitted'] is False and accepted['data_restored'] is False
    assert replace.Replacement(root).run() == 'ALREADY_ACCEPTED'
    assert manager.state()['MainPID'] == state['MainPID']


@pytest.mark.parametrize('fault', ['fail-candidate', 'ignore-gate'])
def test_native_failure_restores_only_code_and_unit_preserving_new_writes(service, fault):
    manager, plan, root, data = service
    (data / fault).touch()
    assert replace.Replacement(root).run() == 'ROLLED_BACK'
    state = manager.state()
    assert replace.argv(int(state['MainPID'])) == plan['old_argv']
    assert all(state[key] == plan['before'][key] for key in replace.CONFIG)
    assert not Path(plan['dropin']).exists()
    with sqlite3.connect(data / 'preserved.sqlite') as database:
        assert database.execute('SELECT value FROM history').fetchall() == [(1,), (2,)]
    assert len(list((Path(plan['gate']) / 'pending').iterdir())) == 1
    assert replace.Replacement(root).run() == 'ROLLED_BACK'


def test_explicit_post_acceptance_rollback_is_code_only(service):
    manager, plan, root, data = service
    replacement = replace.Replacement(root)
    assert replacement.run() == 'ACCEPTED'
    replacement.record('rollback-intent', reason='TEST_RECOVERY')
    assert replacement.run() == 'ROLLED_BACK'
    assert replace.argv(int(manager.state()['MainPID'])) == plan['old_argv']
    with sqlite3.connect(data / 'preserved.sqlite') as database:
        assert database.execute('SELECT value FROM history').fetchall() == [(1,), (2,)]


@pytest.mark.parametrize('submit', [False, True])
def test_recovery_reconciles_prior_drain_before_reporting_rollback(service, submit):
    manager, plan, root, data = service
    replacement = replace.Replacement(root)
    launcher = replace.bridge.prepare(plan['old_binding']['pid'], plan['baseline'], root / 'drain',
                                      mode='stop', seconds=2)
    replacement.record('drain-intent', launcher=str(launcher))
    if submit:
        sys.remote_exec(plan['old_binding']['pid'], str(launcher))
    assert replacement.run(recover=True) == 'ROLLED_BACK'
    assert replace.argv(int(manager.state()['MainPID'])) == plan['old_argv']
    assert replacement.has('old-exited') if submit else replacement.has('aborted')
    assert not Path(plan['dropin']).exists()
    with sqlite3.connect(data / 'preserved.sqlite') as database:
        assert database.execute('SELECT value FROM history').fetchall() == [(1,)]


@pytest.mark.parametrize('phase', ['old-exited', 'install-intent', 'candidate-start-intent', 'accepted'])
def test_controller_death_resumes_without_a_second_writer(service, phase):
    manager, plan, root, data = service
    code = '''
import os,signal,sys
sys.path.insert(0,sys.argv[1])
import controller
original=controller.Replacement.record
def record(self,name,**value):
    original(self,name,**value)
    if name==sys.argv[3]:os.kill(os.getpid(),signal.SIGKILL)
controller.Replacement.record=record
controller.Replacement(sys.argv[2]).run()
'''
    process = subprocess.run([sys.executable, '-I', '-c', code, str(root), str(root), phase],
                             capture_output=True, timeout=20)
    assert process.returncode == -signal.SIGKILL, process.stderr.decode()
    result = replace.Replacement(root).run()
    assert result in ('ACCEPTED', 'ALREADY_ACCEPTED')
    assert replace.argv(int(manager.state()['MainPID'])) == plan['new_argv']
    with sqlite3.connect(data / 'preserved.sqlite') as database:
        assert database.execute('SELECT value FROM history').fetchall() == [(1,), (2,)]


@pytest.mark.parametrize('name', ['friends-http.pyz', 'receiver.conf', 'control_ha_legacy_http.py', 'controller.py'])
def test_staged_source_drift_refuses_before_touching_running_service(service, name):
    manager, plan, root, data = service
    with (root / name).open('ab') as target:
        target.write(b'\nCHANGED = True\n')
    with pytest.raises(ValueError, match='PINS'):
        replace.Replacement(root).run()
    assert manager.state() == plan['before']
    assert not (root / 'drain-intent.json').exists()


def test_unknown_dropin_is_preserved_and_refused(service):
    manager, plan, root, data = service
    target = Path(plan['dropin'])
    target.parent.mkdir(exist_ok=True)
    target.write_text('[Service]\nEnvironment=UNEXPECTED=1\n')
    with pytest.raises(ValueError, match='DROPIN_CHANGED'):
        replace.Replacement(root).run()
    assert target.read_text() == '[Service]\nEnvironment=UNEXPECTED=1\n'
    assert manager.state()['MainPID'] == str(plan['old_binding']['pid'])


def test_unloaded_foreign_dropin_refuses_without_daemon_reload(service):
    manager, plan, root, data = service
    directory = Path(plan['dropin']).parent
    directory.mkdir(exist_ok=True)
    (directory / 'foreign.conf').write_text('[Service]\nEnvironment=UNEXPECTED=1\n')
    with pytest.raises(ValueError, match='UNEXPECTED_DISK_DROPIN'):
        replace.Replacement(root).run()
    assert manager.state()['MainPID'] == str(plan['old_binding']['pid'])


@pytest.mark.parametrize('phase', ['old-exited', 'candidate-start-intent', 'rollback-dropin-removed'])
def test_independent_systemd_guard_resumes_controller_death(service, phase):
    manager, plan, root, data = service
    if phase.startswith('rollback'):
        (data / 'ignore-gate').touch()
    guard = 'fc-ha-replace-guard-test-' + uuid.uuid4().hex + '.service'
    try:
        subprocess.run(['systemd-run', '--user', '--quiet', '--unit=' + guard,
                        '--property=Type=exec', '--property=Restart=on-failure',
                        '--property=RemainAfterExit=yes',
                        '--property=RestartSec=200ms', '--property=RestartPreventExitStatus=78',
                        '--property=StartLimitIntervalSec=0', sys.executable,
                        str(ROOT / 'tests/fixtures/receiver_replacement_controller.py'), str(root), phase],
                       capture_output=True, check=True, timeout=10)
        receipt = 'rolled-back.json' if phase.startswith('rollback') else 'accepted.json'
        wait_for(lambda: (root / receipt).exists(), seconds=30)
        wait_for(lambda: manager.call('show', guard, '--property=SubState', '--value').stdout.strip() == b'exited')
        assert (root / 'fault-consumed').exists()
        assert manager.call('show', guard, '--property=NRestarts', '--value').stdout.strip() == b'1'
        assert manager.call('show', guard, '--property=ExecMainStatus', '--value').stdout.strip() == b'0'
        expected = plan['old_argv'] if phase.startswith('rollback') else plan['new_argv']
        assert replace.argv(int(manager.state()['MainPID'])) == expected
        with sqlite3.connect(data / 'preserved.sqlite') as database:
            assert database.execute('SELECT value FROM history').fetchall() == [(1,), (2,)]
    finally:
        subprocess.run([*manager.command, 'stop', guard], capture_output=True, timeout=10)
        subprocess.run([*manager.command, 'reset-failed', guard], capture_output=True, timeout=10)


def test_slow_legacy_request_aborts_without_changing_service_or_data(service):
    manager, plan, root, data = service
    with socket.create_connection(('127.0.0.1', plan['port']), timeout=2) as partial:
        partial.sendall(b'GET / HTTP/1.0\r\n')
        time.sleep(.1)
        assert replace.Replacement(root).run() == 'ABORTED'
        assert manager.state()['MainPID'] == str(plan['old_binding']['pid'])
        assert not Path(plan['dropin']).exists()
        partial.sendall(b'\r\n')
        assert partial.recv(2048).startswith(b'HTTP/1.0 501')
