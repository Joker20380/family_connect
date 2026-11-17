import contextlib
import errno
import importlib.util
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import threading

import pytest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('tcp_fixture_readiness', ROOT / 'pilot/android-tcp/readiness.py')
readiness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(readiness)
pytestmark = pytest.mark.skipif(sys.platform != 'linux', reason='Linux /proc ownership contract')


@contextlib.contextmanager
def child(script, *arguments):
    process = subprocess.Popen([sys.executable, '-u', '-c', script, *map(str, arguments)],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        yield process
    finally:
        if process.poll() is None:
            process.kill()
        process.wait(timeout=5)
        for stream in (process.stdin, process.stdout, process.stderr):
            stream.close()


@pytest.fixture
def receipt(tmp_path):
    return readiness.Receipt(tmp_path / 'lifecycle.json')


def test_reservation_accepts_closed_reusable_connection_not_live_listener(receipt):
    with socket.socket() as listener:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind(('0.0.0.0', 0))
        listener.listen()
        port = listener.getsockname()[1]
        with socket.create_connection(('127.0.0.1', port), timeout=2) as client:
            accepted, _ = listener.accept()
            with accepted:
                accepted.shutdown(socket.SHUT_WR)
                assert client.recv(1) == b''
    assert not readiness.listening_inodes('self', port)
    with socket.socket() as old_reservation:
        with pytest.raises(OSError) as failure:
            old_reservation.bind(('0.0.0.0', port))
        assert failure.value.errno == errno.EADDRINUSE
    with readiness.reserve_endpoint(port, receipt) as reservation:
        assert reservation.getsockname()[1] == port
        assert any(state['state'] == '06' for state in receipt.events[-1]['previous'])
        with socket.socket() as competitor:
            competitor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            with pytest.raises(OSError):
                competitor.bind(('0.0.0.0', port))
    with socket.socket() as next_peer:
        next_peer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        next_peer.bind(('0.0.0.0', port))
        next_peer.listen()
        with pytest.raises(RuntimeError, match='unavailable'):
            with readiness.reserve_endpoint(port, receipt):
                pytest.fail('must not reserve a live reusable listener')
        assert next_peer.fileno() >= 0
    assert not readiness.listening_inodes('self', port)


def test_old_probe_accepts_foreign_listener_after_child_bind_failure(receipt):
    with socket.socket() as foreign:
        foreign.bind(('0.0.0.0', 0))
        foreign.listen()
        port = foreign.getsockname()[1]
        script = '''
import socket,sys
listener=socket.socket()
try: listener.bind(('0.0.0.0',int(sys.argv[1])))
except OSError as error:
 print('bind_failed:'+str(error.errno),flush=True)
 sys.stdin.readline()
 sys.exit(7)
raise AssertionError('collision was not reproduced')
'''
        with child(script, port) as process:
            assert process.stdout.readline().strip() == 'bind_failed:98'
            assert process.poll() is None
            with socket.create_connection(('127.0.0.1', port), timeout=1):
                old_probe_would_yield = True
            assert old_probe_would_yield
            assert not readiness.owned_listener(process, port)
            with pytest.raises(RuntimeError, match='readiness timeout'):
                readiness.wait_ready(process, port, receipt, timeout=.1)
            process.stdin.write('\n')
            process.stdin.flush()
            assert process.wait(timeout=5) == 7
            with pytest.raises(RuntimeError, match='exited before readiness.*returncode=7'):
                readiness.wait_ready(process, port, receipt, timeout=1)
        with socket.create_connection(('127.0.0.1', port), timeout=1):
            pass
        assert all(event['event'] != 'owned_listener' for event in receipt.events)


def test_positive_owned_endpoint_then_early_exit_is_not_ready(receipt):
    script = '''
import socket,sys
listener=socket.socket();listener.bind(('0.0.0.0',0));listener.listen()
print(listener.getsockname()[1],flush=True)
sys.stdin.readline()
sys.exit(9)
'''
    with child(script) as process:
        port = int(process.stdout.readline())
        readiness.wait_ready(process, port, receipt, timeout=1)
        assert readiness.owned_listener(process, port)
        process.stdin.write('\n')
        process.stdin.flush()
        assert process.wait(timeout=5) == 9
        with pytest.raises(RuntimeError, match='returncode=9'):
            readiness.require_ready(process, port, receipt)
    assert not readiness.listening_inodes('self', port)


@pytest.mark.parametrize('ipv6_only', [False, True])
def test_ipv6_wildcard_requires_actual_ipv4_reachability(receipt, ipv6_only):
    script = '''
import socket,sys
listener=socket.socket(socket.AF_INET6)
listener.setsockopt(socket.IPPROTO_IPV6,socket.IPV6_V6ONLY,int(sys.argv[1]))
listener.bind(('::',0));listener.listen()
print(listener.getsockname()[1],flush=True)
sys.stdin.readline()
'''
    with child(script, int(ipv6_only)) as process:
        port = int(process.stdout.readline())
        assert readiness.owned_listener(process, port)
        if ipv6_only:
            with pytest.raises(RuntimeError, match='does not accept IPv4'):
                readiness.wait_ready(process, port, receipt, timeout=1)
        else:
            readiness.wait_ready(process, port, receipt, timeout=1)


@pytest.fixture
def fixture_module(monkeypatch):
    monkeypatch.setitem(sys.modules, 'readiness', readiness)
    spec = importlib.util.spec_from_file_location('android_tcp_fixture', ROOT / 'pilot/android-tcp/fixture.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setenv('GITHUB_ACTIONS', 'true')
    return module


def fake_peer(root, exit_early=False):
    binary = root / 'clients/android/awg-generated/xray-peer'
    binary.parent.mkdir(parents=True, exist_ok=True)
    binary.write_text(f'#!{sys.executable}\n' + '''
import json,socket,sys,threading
config=json.load(sys.stdin)
''' + ('sys.exit(23)\n' if exit_early else '''
listener=socket.socket()
listener.bind(('0.0.0.0',config['inbounds'][0]['port']))
listener.listen()
threading.Event().wait()
'''))
    binary.chmod(0o700)


@pytest.mark.parametrize('body_error', [False, True])
def test_fixture_cleanup_recreate_and_no_own_listeners(fixture_module, tmp_path, body_error):
    fake_peer(tmp_path)
    for _ in range(2):
        try:
            with fixture_module.peers(tmp_path) as counts:
                counts.begin_tests()
                process = counts.process
                events = counts.receipt.events
                ports = [event['port'] for event in events if event['event'] == 'server_started']
                tcp_ports = [event['port'] for event in events
                             if event['event'] == 'server_started' and event['label'] != 'dns']
                assert len(set([51900, *tcp_ports])) == 4
                assert 'instrumentation_start' in [event['event'] for event in events]
                if body_error:
                    raise ValueError('synthetic instrumentation failure')
        except ValueError as error:
            assert body_error and str(error) == 'synthetic instrumentation failure'
        assert process.poll() is not None
        assert not Path(f'/proc/{process.pid}').exists()
        for port in [51900, *ports]:
            assert not readiness.listening_inodes('self', port, any_address=True)
        assert not any(thread.name.startswith('fc-tcp-fixture-') for thread in threading.enumerate())
        assert json.loads((tmp_path / 'android-tcp-peer-result.json').read_text()) == dict(http=0, dns=0)
        assert sum(event['event'] == 'peer_reaped' for event in events) == 1
        assert sum(event['event'] == 'server_closed' for event in events) == 4


def test_fixture_child_early_exit_fails_before_instrumentation(fixture_module, tmp_path):
    fake_peer(tmp_path, exit_early=True)
    with pytest.raises(RuntimeError, match='returncode=23'):
        with fixture_module.peers(tmp_path):
            pytest.fail('must not yield a broken fixture')
    events = json.loads((tmp_path / 'android-tcp-lifecycle.json').read_text())['events']
    assert not any(event['event'] == 'instrumentation_start' for event in events)
    assert sum(event['event'] == 'peer_reaped' for event in events) == 1
    assert sum(event['event'] == 'server_closed' for event in events) == 4
    assert not readiness.listening_inodes('self', 51900)
    assert not readiness.listening_inodes('self', 51902)


@pytest.mark.parametrize('port', [51900, 51902])
def test_occupied_fixed_endpoint_never_kills_foreign_listener(fixture_module, tmp_path, port):
    fake_peer(tmp_path)
    with socket.socket() as foreign:
        foreign.bind(('0.0.0.0', port))
        foreign.listen()
        with pytest.raises((RuntimeError, OSError)):
            with fixture_module.peers(tmp_path):
                pytest.fail('must not start instrumentation')
        assert foreign.fileno() >= 0
        assert readiness.listening_inodes('self', port) == {str(os.fstat(foreign.fileno()).st_ino)}
        events = json.loads((tmp_path / 'android-tcp-lifecycle.json').read_text())['events']
        assert not any(event['event'] in ('spawned', 'instrumentation_start') for event in events)
    assert not readiness.listening_inodes('self', 51900)
    assert not readiness.listening_inodes('self', 51902)


def test_small_diagnostics_and_runtime_barrier_remain_required():
    from scripts.client_ci_scope import platforms
    assert platforms(['tests/test_android_tcp_fixture.py'])['android']
    workflow = (ROOT / '.github/workflows/clients.yml').read_text()
    diagnostics = workflow.split('name: FamilyConnect-Android-runtime-diagnostics', 1)[1].split('- uses:', 1)[0]
    for filename in ('android-tcp-lifecycle.json', 'android-tcp-peer.log',
                     'android-tcp-peer-result.json', 'android-tcp-runner.log'):
        assert filename in diagnostics
    runner = (ROOT / 'pilot/android-awg/run.py').read_text()
    assert runner.index('counts.begin_tests()') < runner.index("result=subprocess.run(['gradle'")
