import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from types import SimpleNamespace

import pytest

from test_mesh_service import FakeMaterials, FakeNetwork, materials, wait_for
from test_mesh_chat_service import Gate
import mesh_service
from mesh_chat_service import ServiceOwner
from provisioning import chat_bridge_protocol as wire


def scripted_worker(monkeypatch, reply, *, hold_after_ack=False):
    code = '''
import os, sys, threading, time
sys.path.insert(0, sys.argv[1])
import mesh_ipc
while True:
    request = mesh_ipc.receive(0, mesh_ipc.MAX_REQUEST, time.monotonic() + 30)
    if request['action'] == 'stop':
        if sys.argv[2] == 'eof':
            raise SystemExit(0)
        import json
        reply = json.loads(sys.argv[2])
        reply.setdefault('schema', 1)
        reply.setdefault('id', request['id'])
        mesh_ipc.send(1, reply, mesh_ipc.MAX_REPLY, time.monotonic() + 2)
        if reply.get('ok') is True and reply.get('state') == 'DISCONNECTED' and sys.argv[3] == 'False':
            raise SystemExit(0)
        threading.Event().wait(30)
    else:
        mesh_ipc.send(1, dict(schema=1, id=request['id'], ok=True, state='FAILED'), mesh_ipc.MAX_REPLY, time.monotonic() + 2)
'''
    popen = subprocess.Popen
    encoded = reply if isinstance(reply, str) else json.dumps(reply)
    with monkeypatch.context() as patch:
        patch.setattr(mesh_service.subprocess, 'Popen', lambda *args, **kwargs: popen(
            [sys.executable, '-c', code, str(Path(mesh_service.__file__).parent), encoded, str(hold_after_ack)], **kwargs))
        worker = mesh_service.NativeWorker()
    worker.call('status')
    signals = []
    for name in ('terminate', 'kill'):
        original = getattr(worker.process, name)
        def signal(*args, _name=name, _original=original, **kwargs):
            signals.append(_name)
            return _original(*args, **kwargs)
        monkeypatch.setattr(worker.process, name, signal)
    return worker, signals


def assert_contained(worker):
    assert worker.process.poll() is not None
    assert worker.process.stdin.closed and worker.process.stdout.closed
    assert not worker.chat.reader.is_alive()
    assert worker.chat.connection.fileno() == -1


@pytest.mark.parametrize('reply', [dict(ok=False, state='DISCONNECTED'), dict(ok=True, state='STOPPING'),
                                   dict(ok='true', state='DISCONNECTED'), dict(schema=True, ok=True, state='DISCONNECTED'), 'eof'])
def test_containment_without_valid_drain_retains_service_admission(monkeypatch, reply):
    before = len(os.listdir('/proc/self/fd'))
    worker, signals = scripted_worker(monkeypatch, reply)
    owner = ServiceOwner(None, 'synthetic-anchor')
    gate = Gate('chat')
    gate.acquire(threading.Event(), time.monotonic() + 1)
    owner.gate, owner.worker = gate, worker
    try:
        with pytest.raises(RuntimeError, match='CLEANUP_UNCONFIRMED'):
            owner.close()
        assert owner.failed and gate.active and owner.current is None
        assert owner.binding() is None and not owner.watcher.is_alive()
        assert not gate.finished
        with pytest.raises(wire.BridgeError):
            owner.prepare({}, threading.Event(), time.monotonic() + 1)
        assert_contained(worker)
        result = worker.close()
        assert result.process_contained and not result.drain_acknowledged
        assert not result.admission_release_safe and worker.close() is result
        previous = list(signals)
        with pytest.raises(RuntimeError, match='CLEANUP_UNCONFIRMED'):
            owner.close()
        assert signals == previous and signals.count('terminate') <= 1 and signals.count('kill') <= 1
    finally:
        owner.stopped.set()
        owner.watcher.join(2)
        worker.close()
        if gate.active:
            gate.finish()
    assert len(os.listdir('/proc/self/fd')) == before


def test_valid_stop_reply_releases_admission_without_process_leaks(monkeypatch):
    before = len(os.listdir('/proc/self/fd'))
    worker, signals = scripted_worker(monkeypatch, dict(ok=True, state='DISCONNECTED'))
    owner = ServiceOwner(None, 'synthetic-anchor')
    gate = Gate('chat')
    gate.acquire(threading.Event(), time.monotonic() + 1)
    owner.gate, owner.worker = gate, worker
    owner.close()
    result = worker.close()
    assert result.process_contained and result.drain_acknowledged and result.admission_release_safe
    assert worker.close() is result and not signals
    assert not gate.active and owner.gate is None and owner.worker is None
    assert not owner.failed and not owner.watcher.is_alive()
    assert_contained(worker)
    owner.close()
    assert len(os.listdir('/proc/self/fd')) == before


def test_forced_exit_after_stop_reply_does_not_release_admission(monkeypatch):
    worker, signals = scripted_worker(monkeypatch, dict(ok=True, state='DISCONNECTED'), hold_after_ack=True)
    owner = ServiceOwner(None, 'synthetic-anchor')
    gate = Gate('chat')
    gate.acquire(threading.Event(), time.monotonic() + 1)
    owner.gate, owner.worker = gate, worker
    try:
        with pytest.raises(RuntimeError, match='CLEANUP_UNCONFIRMED'):
            owner.close()
        result = worker.close()
        assert result.process_contained and not result.admission_release_safe
        assert signals == ['terminate'] and owner.failed and gate.active
        assert_contained(worker)
    finally:
        worker.close()
        gate.finish()


@pytest.mark.parametrize('primary', ['WORKER_EXITED', 'NETWORK_TIMEOUT'])
def test_packet_force_containment_preserves_primary_and_allows_retry(monkeypatch, primary):
    worker, signals = scripted_worker(monkeypatch, dict(ok=False, state='DISCONNECTED'))
    original = worker.call
    def call(action, start=None):
        if action == 'start':
            return dict(ok=True, state='FAILED', error=primary, snapshot={})
        return original(action, start)
    worker.call = call
    network = FakeNetwork()
    supervisor = mesh_service.Supervisor(network, FakeMaterials())
    supervisor.worker_factory = lambda: worker
    assert supervisor.start(materials())
    try:
        wait_for(lambda: supervisor.state in ('RESTORING', 'FAILED'))
        assert supervisor.first_reason == supervisor.reason == primary
        assert supervisor.state == 'RESTORING' and supervisor.attempt == 1
        assert network.operations == ['guard', 'detach'] and supervisor.session is None
        assert worker.close().process_contained and not worker.close().drain_acknowledged
        assert signals == ['terminate']
        assert_contained(worker)
    finally:
        assert supervisor.stop()


def test_binding_close_failure_still_contains_service_worker(monkeypatch):
    worker, signals = scripted_worker(monkeypatch, dict(ok=True, state='DISCONNECTED'))
    def failed_close():
        raise RuntimeError('synthetic binding failure')
    owner = ServiceOwner(None, 'synthetic-anchor')
    gate = Gate('chat')
    gate.acquire(threading.Event(), time.monotonic() + 1)
    owner.gate, owner.worker = gate, worker
    owner.current = SimpleNamespace(close=failed_close)
    try:
        with pytest.raises(RuntimeError, match='CLEANUP_UNCONFIRMED'):
            owner.close()
        assert owner.failed and gate.active and owner.current is None
        assert_contained(worker)
    finally:
        worker.close()
        gate.finish()
