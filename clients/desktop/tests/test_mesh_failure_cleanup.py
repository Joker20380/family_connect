import json
import subprocess
import sys
import threading

import pytest

from test_mesh_service import FakeMaterials, FakeNetwork, FakeWorker, materials, wait_for
import backend
import mesh_service as service


def exited_worker(monkeypatch, primary='WORKER_EXITED'):
    popen = subprocess.Popen
    monkeypatch.setattr(service.subprocess, 'Popen', lambda *args, **kwargs: popen(
        [sys.executable, '-c', 'raise SystemExit(7)'], **kwargs))
    worker = service.NativeWorker()
    assert worker.process.wait(timeout=2) == 7
    worker.chat.reader.join(2)
    assert not worker.chat.reader.is_alive()
    original_call = worker.call
    if primary != 'WORKER_EXITED':
        def call(action, start=None):
            if action == 'start':
                return dict(ok=True, state='FAILED', error=primary, snapshot={})
            return original_call(action, start)
        worker.call = call
    return worker


def supervisor_for(network, worker):
    supervisor = service.Supervisor(network, FakeMaterials())
    supervisor.worker_factory = lambda: worker
    return supervisor


@pytest.mark.parametrize('primary', ['WORKER_EXITED', 'NETWORK_TIMEOUT'])
def test_reaped_nonzero_worker_preserves_primary_and_allows_recovery(monkeypatch, primary):
    worker = exited_worker(monkeypatch, primary)
    network = FakeNetwork()
    supervisor = supervisor_for(network, worker)
    assert supervisor.start(materials())
    try:
        wait_for(lambda: supervisor.state in ('RESTORING', 'FAILED'))
        status = supervisor.status()
        assert status['first_reason'] == primary
        assert status['state'] == 'RESTORING'
        assert status['reason'] == primary and status['attempt'] == 1
        assert supervisor.session is None
        assert network.operations == ['guard', 'detach']
        assert worker.process.stdin.closed and worker.process.stdout.closed
        assert not worker.chat.reader.is_alive() and worker.chat.connection.fileno() == -1
    finally:
        supervisor.stop()
    assert supervisor.state == 'DISCONNECTED'


@pytest.mark.parametrize('stage', ['reap', 'reader', 'detach', 'binding'])
def test_primary_and_cleanup_failure_are_separate_and_never_retry(monkeypatch, stage):
    worker = exited_worker(monkeypatch, 'NETWORK_TIMEOUT')
    network = FakeNetwork()
    calls = []
    if stage == 'reap':
        def unreaped(timeout):
            calls.append('wait')
            raise subprocess.TimeoutExpired('synthetic', timeout)
        monkeypatch.setattr(worker.process, 'wait', unreaped)
    elif stage == 'reader':
        monkeypatch.setattr(worker.chat.reader, 'is_alive', lambda: True)
    elif stage == 'detach':
        def detach():
            network.operations.append('detach')
            raise OSError('private synthetic exception must not be exported')
        network.detach = detach
    else:
        class BrokenBinding:
            def __init__(self, *args):
                pass
            def close(self):
                calls.append('binding')
                raise RuntimeError('private synthetic exception must not be exported')
        monkeypatch.setattr(service, 'Binding', BrokenBinding)
    supervisor = supervisor_for(network, worker)
    assert supervisor.start(materials())
    try:
        wait_for(lambda: supervisor.state == 'FAILED')
        status = supervisor.status()
        assert status['first_reason'] == 'NETWORK_TIMEOUT'
        assert status['reason'] == 'CLEANUP_PENDING'
        expected = dict(reap='WORKER_REAP_FAILED', reader='WORKER_READER_FAILED',
                        detach='NETWORK_DETACH_FAILED', binding='CHAT_BINDING_CLEANUP_FAILED')[stage]
        assert expected in [event['reason'] for event in status['events']]
        assert 'private' not in json.dumps(status)
        assert supervisor.session is None and supervisor.attempt == 1
        assert network.operations == ['guard', 'detach']
        assert worker.process.stdin.closed and worker.process.stdout.closed
    finally:
        supervisor.stop()
    assert supervisor.state == 'FAILED' and supervisor.reason == 'CLEANUP_PENDING'
    assert supervisor.first_reason == 'NETWORK_TIMEOUT'
    assert supervisor.attempt == 1 and 'cleanup' not in network.operations


def test_unexpected_body_exception_is_packet_failure_even_with_dead_worker(monkeypatch):
    worker = exited_worker(monkeypatch)
    original_call = worker.call
    def call(action, start=None):
        if action == 'start':
            raise KeyError('synthetic session body')
        return original_call(action, start)
    worker.call = call
    supervisor = supervisor_for(FakeNetwork(), worker)
    assert supervisor.start(materials())
    try:
        wait_for(lambda: supervisor.state == 'FAILED')
        assert supervisor.first_reason == supervisor.reason == 'PACKET_OR_IPC_FAILED'
        assert supervisor.session is None
    finally:
        assert supervisor.stop()


def test_prepare_failure_is_attempt_zero_not_session_failure():
    network = FakeNetwork()
    def prepare():
        raise OSError('synthetic setup failure')
    network.prepare = prepare
    supervisor = supervisor_for(network, None)
    assert supervisor.start(materials())
    try:
        wait_for(lambda: supervisor.state == 'FAILED')
        assert supervisor.first_reason == supervisor.reason == 'NETWORK_SETUP_FAILED'
        assert supervisor.attempt == 0 and supervisor.session is None
    finally:
        assert supervisor.stop()


def test_disconnect_during_close_never_overlaps_or_repeats_close():
    network = FakeNetwork()
    entered, release = threading.Event(), threading.Event()
    worker = FakeWorker(network, 'FAILED', 'NETWORK_TIMEOUT')
    def close():
        worker.calls.append('close')
        entered.set()
        assert release.wait(2)
    worker.close = close
    supervisor = supervisor_for(network, worker)
    assert supervisor.start(materials()) and entered.wait(2)
    stopping = threading.Thread(target=supervisor.stop)
    stopping.start()
    try:
        wait_for(supervisor.cancel.is_set)
        assert not supervisor.start(materials())
    finally:
        release.set()
        stopping.join(3)
    assert not stopping.is_alive() and supervisor.session is None
    assert supervisor.state == 'DISCONNECTED' and supervisor.attempt == 1
    assert worker.calls.count('close') == network.operations.count('detach') == 1


def test_old_session_close_cannot_detach_next_generation():
    network = FakeNetwork()
    old = service.PacketSession(network, FakeMaterials(), threading.Event(), 1)
    old.close()
    current = service.PacketSession(network, FakeMaterials(), threading.Event(), 2)
    network.operations.append('new-generation')
    old.close()
    assert network.operations == ['detach', 'new-generation']
    current.close()
    assert network.operations == ['detach', 'new-generation', 'detach']


def test_retry_starts_only_after_reap_reader_and_detach(monkeypatch):
    worker = exited_worker(monkeypatch, 'NETWORK_TIMEOUT')
    network = FakeNetwork()
    supervisor = supervisor_for(network, worker)
    workers = []
    def factory():
        if workers:
            assert network.operations == ['guard', 'detach']
            assert worker.process.stdin.closed and worker.process.stdout.closed
            assert not worker.chat.reader.is_alive()
        current = worker if not workers else FakeWorker(network)
        workers.append(current)
        return current
    supervisor.worker_factory = factory
    assert supervisor.start(materials())
    try:
        wait_for(lambda: supervisor.state == 'CONNECTED')
        assert supervisor.first_reason == 'NETWORK_TIMEOUT'
        assert supervisor.attempt == len(workers) == 2
    finally:
        assert supervisor.stop()
    assert network.operations.count('detach') == 2


def test_stop_rpc_failure_can_terminate_and_reap_running_child(monkeypatch):
    popen = subprocess.Popen
    monkeypatch.setattr(service.subprocess, 'Popen', lambda *args, **kwargs: popen(
        [sys.executable, '-c', 'import time; time.sleep(60)'], **kwargs))
    worker = service.NativeWorker()
    def unavailable(*args):
        raise EOFError('synthetic stop RPC unavailable')
    worker.call = unavailable
    try:
        worker.close()
        assert worker.process.returncode is not None
        assert worker.process.stdin.closed and worker.process.stdout.closed
        assert not worker.chat.reader.is_alive() and worker.chat.connection.fileno() == -1
    finally:
        if worker.process.poll() is None:
            worker.process.kill()
            worker.process.wait(timeout=2)


def test_descriptor_failure_still_closes_other_pipe_and_reader(monkeypatch):
    worker = exited_worker(monkeypatch)
    original = worker.process.stdin
    class UnclosedPipe:
        closed = False
        def close(self):
            raise OSError('synthetic descriptor failure')
    worker.process.stdin = UnclosedPipe()
    try:
        with pytest.raises(service.SessionFailure) as captured:
            worker.close()
        assert captured.value.code == 'CLEANUP_PENDING'
        assert captured.value.cleanup_reason == 'WORKER_DESCRIPTOR_FAILED'
        assert worker.process.stdout.closed and not worker.chat.reader.is_alive()
    finally:
        original.close()


def test_failed_session_close_is_not_replayed_after_resources_change():
    network = FakeNetwork()
    attempts = []
    def detach():
        attempts.append('detach')
        raise OSError('synthetic unconfirmed cleanup')
    network.detach = detach
    session = service.PacketSession(network, FakeMaterials(), threading.Event(), 1)
    with pytest.raises(service.SessionFailure, match='CLEANUP_PENDING'):
        session.close()
    network.detach = lambda: pytest.fail('stale close touched a replacement')
    with pytest.raises(service.SessionFailure, match='CLEANUP_PENDING'):
        session.close()
    assert attempts == ['detach'] and not session.cleanup_confirmed


def test_final_network_failsafe_keeps_primary_and_records_own_stage():
    network = FakeNetwork()
    worker = FakeWorker(network, 'FAILED', 'FAMILY_REJECTED')
    def cleanup():
        network.operations.append('cleanup')
        raise RuntimeError('synthetic failsafe failure')
    network.cleanup = cleanup
    supervisor = supervisor_for(network, worker)
    assert supervisor.start(materials())
    try:
        wait_for(lambda: supervisor.state == 'FAILED')
    finally:
        assert not supervisor.stop()
    status = supervisor.status()
    assert status['first_reason'] == 'FAMILY_REJECTED'
    assert status['reason'] == 'CLEANUP_PENDING'
    assert status['events'][-2]['reason'] == 'NETWORK_CLEANUP_FAILED'
    assert supervisor.session is None and network.operations == ['guard', 'detach', 'cleanup']


@pytest.mark.parametrize('code', ['CHAT_BINDING_CLEANUP_FAILED', 'WORKER_REAP_FAILED',
    'WORKER_READER_FAILED', 'WORKER_DESCRIPTOR_FAILED', 'WORKER_CLEANUP_FAILED',
    'NETWORK_DETACH_FAILED', 'NETWORK_CLEANUP_FAILED'])
def test_cleanup_stages_survive_strict_desktop_diagnostics(code):
    assert code in backend.DesktopDiagnostics.CODES
    collector = backend.DesktopDiagnostics('test')
    collector.sample('FAILED', 'mesh', service=dict(state='FAILED', reason=code,
        first_reason='NETWORK_TIMEOUT', attempt=1, native={}))
    record = json.loads(collector.export())['ring']
    assert record['first_failure'] == 'NETWORK_TIMEOUT'
    assert record['events'][-1]['reason_code'] == code
