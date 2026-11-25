import http.client
from http.server import BaseHTTPRequestHandler
import json
import os
from pathlib import Path
import signal
import socket
import struct
import subprocess
import sys
import time
import uuid

import pytest

from control.capture_gate import Busy, GateError, initialize
from control.friends import http_lifecycle
from scripts.package_friends_http import build
from scripts.service_notices import Notices


ROOT = Path(__file__).resolve().parents[1]
CHILD = r'''
import importlib.util, json, os, signal, subprocess, sys, time
from pathlib import Path
root = Path(sys.argv[1])
sys.path.insert(0, sys.argv[2])
from control.friends import http_lifecycle, notices, diagnostics, technical_metadata
from scripts.service_notices import Notices
original_activate = http_lifecycle.DrainingHTTPServer.server_activate
def activate(server):
    original_activate(server)
    (root / 'port').write_text(str(server.server_port))
http_lifecycle.DrainingHTTPServer.server_activate = activate
def pause(name):
    (root / name).touch()
    if mode == 'child-process':
        code = "import os,sys,time;from pathlib import Path;root=Path(sys.argv[1]);(root/'child-pid').write_text(str(os.getpid()));deadline=time.monotonic()+20\nwhile not (root/'release').exists():\n if time.monotonic()>deadline:raise TimeoutError()\n time.sleep(.01)\n(root/'child-finished').touch()"
        subprocess.run([sys.executable, '-I', '-c', code, str(root)], check=True, timeout=22)
        return
    deadline = time.monotonic() + 20
    while not (root / 'release').exists():
        if time.monotonic() >= deadline:
            raise TimeoutError('synthetic boundary expired')
        time.sleep(.01)
mode = sys.argv[3]
original_write = Notices._write_feed
def write(store, output, version, now):
    original_write(store, output, version, now)
    if version == 1:
        pause('export-entered')
        if mode == 'export-error':
            raise OSError('synthetic export failure')
Notices._write_feed = write
original_publish = notices.publish
def publish(registry, output, token, value):
    return original_publish(registry, root / 'public/family-connect-events-v1.json', token, value)
notices.publish = publish
if mode in ('diagnostics', 'technical_metadata'):
    module = diagnostics if mode == 'diagnostics' else technical_metadata
    original_prune = module.prune
    def prune(*args):
        pause('retention-entered')
        result = original_prune(*args)
        (root / 'retention-finished').touch()
        return result
    module.prune = prune
if sys.argv[2].endswith('.pyz'):
    import friends_http as runtime
else:
    spec = importlib.util.spec_from_file_location('runtime', Path(sys.argv[2]) / 'deploy/friends/access-api.py')
    runtime = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runtime)
sys.argv = ['friends-http', '--root', str(root), '--port', '0', '--capture-gate', str(root / 'gate')]
runtime.main()
(root / 'finished').touch()
'''


def wait_for(predicate, seconds=8):
    deadline = time.monotonic() + seconds
    while not predicate():
        assert time.monotonic() < deadline, 'bounded observation expired'
        time.sleep(.01)


def listening(port):
    return any(fields[1].endswith(':' + f'{port:04X}') and fields[3] == '0A'
               for line in Path('/proc/net/tcp').read_text().splitlines()[1:]
               if (fields := line.split()))


@pytest.fixture
def receiver(tmp_path):
    gate = initialize(tmp_path / 'gate')
    store = Notices(tmp_path / 'notices.sqlite')
    store.grant('Synthetic operator', tmp_path / 'token')
    store.db.close()
    (tmp_path / 'public').mkdir(mode=0o700)
    processes = []

    def launch(mode='export', source=ROOT):
        process = subprocess.Popen([sys.executable, '-I', '-c', CHILD, str(tmp_path), str(source), mode],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        processes.append(process)
        wait_for(lambda: (tmp_path / 'port').exists() or process.poll() is not None)
        assert process.poll() is None, process.stderr.read().decode()
        return process, int((tmp_path / 'port').read_text())

    yield tmp_path, gate, launch
    (tmp_path / 'release').touch()
    for process in processes:
        if process.poll() is None:
            process.send_signal(signal.SIGTERM)
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)
        process.stderr.close()


def publication(root, port):
    connection = http.client.HTTPConnection('127.0.0.1', port, timeout=8)
    value = dict(id='a' * 32, kind='information', title='Synthetic', body='Not production',
                 platforms=['android'], days=1)
    connection.request('POST', '/friends/notices/publish', json.dumps(value), headers={
        'Authorization': 'Bearer ' + (root / 'token').read_text().strip(),
        'Content-Type': 'application/json'})
    wait_for(lambda: (root / 'export-entered').exists())
    return connection


def stop_and_observe(process, port, signum=signal.SIGTERM):
    process.send_signal(signum)
    wait_for(lambda: not listening(port))
    assert process.poll() is None
    with pytest.raises(ConnectionRefusedError), socket.create_connection(('127.0.0.1', port), timeout=1):
        pass


@pytest.mark.parametrize('signum', [signal.SIGTERM, signal.SIGINT])
def test_stop_finishes_admitted_native_export_before_exit(receiver, signum):
    root, gate, launch = receiver
    process, port = launch()
    connection = publication(root, port)
    stop_and_observe(process, port, signum)
    process.send_signal(signal.SIGTERM)
    process.send_signal(signal.SIGINT)
    assert not (root / 'finished').exists()
    with pytest.raises(Busy), gate.drain(.02):
        pass
    (root / 'release').touch()
    assert connection.getresponse().status == 200
    connection.close()
    assert process.wait(timeout=8) == 0, process.stderr.read().decode()
    assert (root / 'finished').exists()
    assert [json.loads(path.read_text())['version'] for path in sorted((root / 'public').glob('*.json'))] == [1, 2]
    with gate.drain(.1):
        pass


@pytest.mark.parametrize('mode', ['export-error', 'killed'])
def test_failed_or_killed_drain_never_clears_uncertainty(receiver, mode):
    root, gate, launch = receiver
    process, port = launch(mode)
    connection = publication(root, port)
    stop_and_observe(process, port)
    if mode == 'killed':
        process.kill()
        assert process.wait(timeout=3) == -signal.SIGKILL
        assert not (root / 'finished').exists()
    else:
        (root / 'release').touch()
        assert connection.getresponse().status == 503
        assert process.wait(timeout=8) == 0
    connection.close()
    assert (root / 'public/family-connect-events-v1.json').exists()
    assert not (root / 'public/family-connect-events-v2.json').exists()
    with pytest.raises(GateError, match='UNSETTLED_OPERATION'), gate.drain(.02):
        pass


@pytest.mark.parametrize('mode', ['diagnostics', 'technical_metadata'])
def test_stop_joins_real_retention_worker_and_gate_scope(receiver, mode):
    root, gate, launch = receiver
    process, port = launch(mode)
    wait_for(lambda: (root / 'retention-entered').exists())
    stop_and_observe(process, port)
    with pytest.raises(Busy), gate.drain(.02):
        pass
    (root / 'release').touch()
    assert process.wait(timeout=8) == 0, process.stderr.read().decode()
    assert (root / 'retention-finished').exists() and (root / 'finished').exists()
    with gate.drain(.1):
        pass


def test_incomplete_headers_have_a_deadline_during_stop(receiver):
    root, gate, launch = receiver
    process, port = launch()
    connection = socket.create_connection(('127.0.0.1', port), timeout=1)
    connection.sendall(b'POST /friends/notices/publish HTTP/1.1\r\n')
    wait_for(lambda: len(list(Path(f'/proc/{process.pid}/task').iterdir())) == 4)
    stop_and_observe(process, port)
    assert process.wait(timeout=7) == 0, process.stderr.read().decode()
    connection.close()
    assert (root / 'finished').exists()
    with gate.drain(.1):
        pass


@pytest.mark.parametrize('failure', ['bind', 'second-retention'])
def test_partial_startup_cleans_workers_listener_and_signal_handlers(failure, monkeypatch):
    original = {signum: signal.getsignal(signum) for signum in (signal.SIGTERM, signal.SIGINT)}
    workers = []
    ports = []
    original_activate = http_lifecycle.DrainingHTTPServer.server_activate

    def activate(server):
        original_activate(server)
        ports.append(server.server_port)

    monkeypatch.setattr(http_lifecycle.DrainingHTTPServer, 'server_activate', activate)

    def first():
        worker = http_lifecycle.Retention()
        workers.append(worker.start(worker.wait, name='synthetic-retention'))
        return worker

    def second():
        raise RuntimeError('synthetic startup failure')

    with socket.socket() as occupied:
        occupied.bind(('127.0.0.1', 0))
        occupied.listen()
        port = occupied.getsockname()[1] if failure == 'bind' else 0
        with pytest.raises(OSError if failure == 'bind' else RuntimeError):
            http_lifecycle.serve(('127.0.0.1', port), BaseHTTPRequestHandler, (first, second))
    assert len(workers) == (0 if failure == 'bind' else 1)
    assert all(worker.is_set() and not worker.worker.is_alive() for worker in workers)
    assert all(not listening(port) for port in ports)
    assert all(signal.getsignal(signum) == previous for signum, previous in original.items())


def test_client_reset_during_drain_preserves_unknown_ack(receiver):
    root, gate, launch = receiver
    process, port = launch()
    connection = publication(root, port)
    stop_and_observe(process, port)
    connection.sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))
    connection.close()
    (root / 'release').touch()
    assert process.wait(timeout=8) == 0, process.stderr.read().decode()
    assert len(list((root / 'public').glob('*.json'))) == 2
    with pytest.raises(GateError, match='UNSETTLED_OPERATION'), gate.drain(.02):
        pass


def test_closed_package_runs_real_lifecycle_and_exports(receiver, tmp_path):
    root, gate, launch = receiver
    candidate = tmp_path / 'candidate'
    build(candidate)
    process, port = launch(source=candidate / 'friends-http.pyz')
    connection = publication(root, port)
    stop_and_observe(process, port)
    (root / 'release').touch()
    assert connection.getresponse().status == 200
    connection.close()
    assert process.wait(timeout=8) == 0, process.stderr.read().decode()
    with gate.drain(.1):
        pass
    assert (candidate / 'http-graceful-stop.conf').read_text() == (
        '[Service]\nKillMode=mixed\nKillSignal=SIGTERM\nSendSIGKILL=no\nTimeoutStopSec=infinity\n')


@pytest.mark.skipif(os.environ.get('FC_TEST_SYSTEMD_HTTP_DRAIN') != '1', reason='requires owned user-systemd fixture')
def test_real_systemd_stop_preserves_admitted_child_process(receiver):
    root, gate, _ = receiver
    unit = 'fc-ha-http-drain-' + uuid.uuid4().hex + '.service'
    properties = (ROOT / 'deploy/friends/restricted/http-graceful-stop.conf').read_text().splitlines()[1:]

    def manager(*arguments):
        return subprocess.run(['systemctl', '--user', *arguments, unit], capture_output=True, timeout=10)

    try:
        command = ['systemd-run', '--user', '--quiet', '--unit=' + unit, '--property=Type=exec',
                   '--property=Restart=no', *['--property=' + value for value in properties],
                   sys.executable, '-I', '-c', CHILD, str(root), str(ROOT), 'child-process']
        result = subprocess.run(command, capture_output=True, timeout=10)
        assert result.returncode == 0, result.stderr.decode()
        wait_for(lambda: (root / 'port').exists())
        port = int((root / 'port').read_text())
        connection = publication(root, port)
        wait_for(lambda: (root / 'child-pid').exists())
        before = manager('show', '--property=MainPID,KillMode,KillSignal,SendSIGKILL,TimeoutStopUSec')
        values = dict(line.split('=', 1) for line in before.stdout.decode().splitlines())
        assert values['KillMode'] == 'mixed' and values['KillSignal'] == '15'
        assert values['SendSIGKILL'] == 'no' and values['TimeoutStopUSec'] == 'infinity'
        main_pid = int(values['MainPID'])
        child_pid = int((root / 'child-pid').read_text())
        assert Path(f'/proc/{child_pid}/cgroup').read_text() == Path(f'/proc/{main_pid}/cgroup').read_text()
        assert manager('stop', '--no-block').returncode == 0
        wait_for(lambda: not listening(port))
        state = manager('show', '--property=ActiveState,SubState').stdout.decode()
        assert 'ActiveState=deactivating' in state and 'SubState=stop-sigterm' in state
        assert Path(f'/proc/{child_pid}').exists() and Path(f'/proc/{main_pid}').exists()
        with pytest.raises(Busy), gate.drain(.02):
            pass
        (root / 'release').touch()
        assert connection.getresponse().status == 200
        connection.close()
        wait_for(lambda: not Path(f'/proc/{main_pid}').exists())
        assert (root / 'child-finished').exists() and (root / 'finished').exists()
        assert not Path(f'/proc/{child_pid}').exists()
        with gate.drain(.1):
            pass
    finally:
        (root / 'release').touch()
        manager('stop')
        manager('reset-failed')
