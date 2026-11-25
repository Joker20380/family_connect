import http.client
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time

import pytest

from scripts import control_ha_legacy_http as bridge
from scripts.service_notices import Notices


CHILD = r'''
import json,os,subprocess,sys,threading,time
from pathlib import Path
root,archive,mode=Path(sys.argv[1]),sys.argv[2],sys.argv[3]
sys.path.insert(0,archive)
import friends_http as runtime
from control.friends import notices,diagnostics,technical_metadata
from scripts.service_notices import Notices
original_activate=runtime.ThreadingHTTPServer.server_activate
def activate(server):
    original_activate(server)
    (root/'port').write_text(str(server.server_port))
runtime.ThreadingHTTPServer.server_activate=activate
def wait(name):
    (root/name).touch()
    deadline=time.monotonic()+25
    while not (root/'release').exists():
        if time.monotonic()>deadline:raise TimeoutError('synthetic wait')
        time.sleep(.01)
original_write=Notices.export
def write(store,output,version=1):
    original_write(store,output,version)
    if version==1:
        if mode=='child':
            code="import sys,time;from pathlib import Path;root=Path(sys.argv[1]);(root/'export-entered').touch();deadline=time.monotonic()+20\nwhile not (root/'release').exists():\n if time.monotonic()>deadline:raise TimeoutError()\n time.sleep(.01)\n(root/'child-finished').touch()"
            subprocess.run([sys.executable,'-I','-c',code,str(root)],check=True,timeout=22)
        else:wait('export-entered')
        if mode=='failure':raise OSError('synthetic export failure')
Notices.export=write
original_publish=notices.publish
def publish(registry,output,token,value):
    return original_publish(registry,root/'public/family-connect-events-v1.json',token,value)
notices.publish=publish
if mode=='unknown-thread':
    threading.Thread(target=lambda:wait('unknown-entered'),daemon=True).start()
if mode in ('diagnostics','technical_metadata'):
    module=diagnostics if mode=='diagnostics' else technical_metadata
    original_prune=module.prune
    def prune(*args):
        wait('retention-entered')
        result=original_prune(*args)
        (root/'retention-finished').touch()
        return result
    module.prune=prune
sys.argv=['friends-http','--root',str(root),'--port','0']
runtime.main()
(root/'finished').touch()
'''


def wait_for(predicate, seconds=8):
    deadline = time.monotonic() + seconds
    while not predicate():
        assert time.monotonic() < deadline, 'bounded observation expired'
        time.sleep(.01)


def read(path):
    return json.loads(path.read_text())


@pytest.fixture
def receiver(tmp_path):
    archive = os.environ.get('FC_TEST_RECEIVER_BASELINE')
    if not archive:
        pytest.skip('requires privately retained pinned legacy archive')
    if sys.version_info[:2] != (3, 14) or not hasattr(sys, 'remote_exec'):
        pytest.skip('requires CPython 3.14 remote execution')
    store = Notices(tmp_path / 'notices.sqlite')
    store.grant('Synthetic operator', tmp_path / 'token')
    store.db.close()
    (tmp_path / 'public').mkdir(mode=0o700)
    processes = []

    def launch(mode='idle'):
        process = subprocess.Popen([sys.executable, '-I', '-c', CHILD, str(tmp_path), archive, mode],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        processes.append(process)
        wait_for(lambda: (tmp_path / 'port').exists() or process.poll() is not None)
        assert process.poll() is None, process.stderr.read().decode()
        time.sleep(.03)
        return process, int((tmp_path / 'port').read_text())

    yield tmp_path, archive, launch
    (tmp_path / 'release').touch()
    for process in processes:
        if process.poll() is None:
            process.terminate()
        try:
            process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)
        process.stderr.close()


def invoke(root, archive, process, *, mode='probe', seconds=5, name='operation', change=None):
    output = root / name
    launcher = bridge.prepare(process.pid, archive, output, mode=mode, seconds=seconds)
    if change:
        request = read(output / 'request.json')
        change(request)
        (output / 'request.json').write_text(json.dumps(request))
    sys.remote_exec(process.pid, str(launcher))
    wait_for(lambda: (output / 'entered.json').exists() or (output / 'error.json').exists())
    return output


def response(port):
    connection = http.client.HTTPConnection('127.0.0.1', port, timeout=3)
    connection.request('GET', '/')
    result = connection.getresponse().status
    connection.close()
    return result


def publication(root, port):
    connection = http.client.HTTPConnection('127.0.0.1', port, timeout=8)
    value = dict(id='a' * 32, kind='information', title='Synthetic', body='Not production',
                 platforms=['android'], days=1)
    connection.request('POST', '/friends/notices/publish', json.dumps(value), headers={
        'Authorization': 'Bearer ' + (root / 'token').read_text().strip(), 'Content-Type': 'application/json'})
    wait_for(lambda: (root / 'export-entered').exists())
    return connection


def test_probe_returns_to_same_live_legacy_runtime(receiver):
    root, archive, launch = receiver
    process, port = launch()
    before = bridge.binding(process.pid)
    output = invoke(root, archive, process)
    wait_for(lambda: (output / 'result.json').exists() or (output / 'error.json').exists())
    assert not (output / 'error.json').exists(), read(output / 'error.json')
    assert read(output / 'result.json')['result'] == 'PROBE_RETURNING'
    assert read(output / 'result.json')['capture_permitted'] is False
    assert process.poll() is None and bridge.binding(process.pid) == before
    assert response(port) == 501


def test_idle_stop_exits_naturally_with_preserved_legacy_uncertainty(receiver):
    root, archive, launch = receiver
    process, port = launch()
    output = invoke(root, archive, process, mode='stop')
    assert process.wait(timeout=8) == 0, process.stderr.read().decode()
    assert (root / 'finished').exists()
    assert read(output / 'quiescent.json')['children'] == 0
    assert read(output / 'legacy-uncertainty.json')['capture_permitted'] is False
    with pytest.raises(ConnectionRefusedError):
        socket.create_connection(('127.0.0.1', port), timeout=1)


@pytest.mark.parametrize('mode,status', [('export', 200), ('child', 200), ('failure', 503)])
def test_admitted_native_export_and_child_finish_before_main_exit(receiver, mode, status):
    root, archive, launch = receiver
    process, port = launch(mode)
    connection = publication(root, port)
    output = invoke(root, archive, process, mode='stop')
    assert not (output / 'result.json').exists() and process.poll() is None
    (root / 'release').touch()
    assert connection.getresponse().status == status
    connection.close()
    assert process.wait(timeout=8) == 0, process.stderr.read().decode()
    assert read(output / 'result.json')['result'] == 'RETURN_TO_EXIT'
    assert (output / 'legacy-uncertainty.json').exists()
    assert (root / 'public/family-connect-events-v2.json').exists() == (status == 200)
    if mode == 'child':
        assert (root / 'child-finished').exists()


@pytest.mark.parametrize('mode', ['diagnostics', 'technical_metadata'])
def test_stop_joins_in_flight_retention_without_forced_exit(receiver, mode):
    root, archive, launch = receiver
    process, port = launch(mode)
    wait_for(lambda: (root / 'retention-entered').exists())
    output = invoke(root, archive, process, mode='stop')
    wait_for(lambda: (output / 'draining-retention.json').exists())
    assert process.poll() is None and not (output / 'quiescent.json').exists()
    (root / 'release').touch()
    assert process.wait(timeout=8) == 0
    assert (root / 'retention-finished').exists()


def test_unfinished_handler_aborts_before_retention_or_listener_changes(receiver):
    root, archive, launch = receiver
    process, port = launch('export')
    connection = publication(root, port)
    output = invoke(root, archive, process, mode='stop', seconds=1)
    wait_for(lambda: (output / 'error.json').exists())
    error = read(output / 'error.json')
    assert error.pop('failure_site')['function'] == 'require'
    assert error == dict(reason='HANDLERS_UNFINISHED', exception_type='ValueError',
                         irreversible=False, capture_permitted=False)
    assert not (output / 'legacy-uncertainty.json').exists()
    assert response(port) == 501
    (root / 'release').touch()
    assert connection.getresponse().status == 200
    connection.close()
    retry = invoke(root, archive, process, mode='stop', name='retry')
    assert process.wait(timeout=8) == 0
    assert read(retry / 'result.json')['result'] == 'RETURN_TO_EXIT'


@pytest.mark.parametrize('mutation,reason', [('expired', 'EXPIRED_REQUEST'), ('binding', 'PROCESS_BINDING'),
                                           ('source', 'BRIDGE_PIN'), ('unknown', 'REQUEST_FIELDS')])
def test_stale_or_unbound_request_does_not_stop_legacy_runtime(receiver, mutation, reason):
    root, archive, launch = receiver
    process, port = launch()
    def change(request):
        if mutation == 'expired':
            request['deadline'] = time.monotonic() - 1
        elif mutation == 'binding':
            request['binding']['start'] = '0'
        elif mutation == 'source':
            request['source_sha256'] = '0' * 64
        else:
            request['unknown'] = True
    output = invoke(root, archive, process, mode='stop', change=change)
    assert read(output / 'error.json')['reason'] == reason
    assert process.poll() is None and response(port) == 501


def test_unknown_background_thread_refuses_before_any_stop(receiver):
    root, archive, launch = receiver
    process, port = launch('unknown-thread')
    output = invoke(root, archive, process, mode='stop')
    assert read(output / 'error.json')['reason'] == 'UNKNOWN_THREAD'
    assert response(port) == 501


def test_probe_pauses_new_handlers_then_restores_admission(receiver):
    root, archive, launch = receiver
    process, port = launch('export')
    connection = publication(root, port)
    output = invoke(root, archive, process)
    with socket.create_connection(('127.0.0.1', port), timeout=1) as queued:
        queued.sendall(b'GET / HTTP/1.0\r\n\r\n')
        queued.settimeout(.1)
        with pytest.raises(TimeoutError):
            queued.recv(1)
        (root / 'release').touch()
        assert connection.getresponse().status == 200
        queued.settimeout(3)
        assert queued.recv(2048).startswith(b'HTTP/1.0 501')
    connection.close()
    assert read(output / 'result.json')['retention_unchanged'] is True
    assert process.poll() is None


def test_partial_headers_abort_without_killing_the_request(receiver):
    root, archive, launch = receiver
    process, port = launch()
    with socket.create_connection(('127.0.0.1', port), timeout=2) as partial:
        partial.sendall(b'GET / HTTP/1.0\r\n')
        time.sleep(.05)
        output = invoke(root, archive, process, mode='stop', seconds=1)
        wait_for(lambda: (output / 'error.json').exists())
        assert read(output / 'error.json')['reason'] == 'HANDLERS_UNFINISHED'
        partial.sendall(b'\r\n')
        assert partial.recv(2048).startswith(b'HTTP/1.0 501')
    assert response(port) == 501


@pytest.mark.parametrize('mode', ['replay', 'source-changed', 'receipt-unwritable', 'request-missing'])
def test_launcher_failures_do_not_escape_into_product_main_loop(receiver, mode):
    root, archive, launch = receiver
    process, port = launch()
    output = root / 'operation'
    launcher = bridge.prepare(process.pid, archive, output)
    if mode == 'replay':
        sys.remote_exec(process.pid, str(launcher))
        wait_for(lambda: (output / 'result.json').exists())
    elif mode == 'source-changed':
        with (output / 'bridge.py').open('ab') as destination:
            destination.write(b'\nCHANGED = True\n')
    elif mode == 'receipt-unwritable':
        (output / 'claimed.json').mkdir()
    else:
        (output / 'request.json').unlink()
    sys.remote_exec(process.pid, str(launcher))
    time.sleep(.65)
    assert process.poll() is None, process.stderr.read().decode()
    assert response(port) == 501
