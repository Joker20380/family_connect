from concurrent.futures import ThreadPoolExecutor
import json
import os
import queue
import socket
import threading
import time

import httpx
import pytest

from test_mesh_chat import lane, read, respond
from test_mesh_chat_host import DEVICE, body
from mesh_chat import ChatError, ChatLane, MAX_FRAME
import mesh_ipc
from mesh_chat_host import Binding, Host
from provisioning.chat_bridge import ChatBridge, ChatHTTP
from provisioning import chat_bridge_protocol as wire
from provisioning.friends import FriendsError
from test_mesh_chat_service import service, material


def binding_for(instance):
    start = dict(readiness={'device': DEVICE}, identity='private-synthetic-test-key', anchor='synthetic-anchor',
                 resolver='1.1.1.1:53', underlying_index=2)
    binding = Binding(instance, start, threading.Event(), 'SERVICE_ONLY')
    binding.generation_lease = 1
    binding.ready.set()
    return binding


def test_pending_control_limit_is_not_terminal(lane):
    instance, peer = lane
    binding = binding_for(instance)
    error = None
    with ThreadPoolExecutor(4) as executor:
        operations = [executor.submit(instance.call, 'route', lease=1) for _ in range(4)]
        requests = [read(peer) for _ in operations]
        assert all(request['action'] == 'route' for request in requests)
        assert len(instance.pending) == 4
        try:
            result = binding.native_alive()
        except ChatError as caught:
            error, result = caught.code, None
        finally:
            for request in requests:
                respond(peer, request, route='SERVICE_ONLY')
        assert all(operation.result(2)['route'] == 'SERVICE_ONLY' for operation in operations)
        health = executor.submit(instance.call, 'route', lease=1)
        respond(peer, read(peer), route='SERVICE_ONLY')
        assert health.result(2)['route'] == 'SERVICE_ONLY'
    print('CONTROL:', 'error=', error, 'result=', result, 'cancelled=', binding.cancelled.is_set(),
          'lane_closed=', instance.closed.is_set(), 'route=SERVICE_ONLY')
    assert error == 'BUSY_OR_UNAVAILABLE' and result is None
    assert not binding.cancelled.is_set() and not binding.closed.is_set()


@pytest.mark.parametrize('boundary', ['bridge', 'http'])
def test_malformed_route_keeps_denied_at_user_boundary(lane, tmp_path, boundary):
    instance, peer = lane
    binding = binding_for(instance)
    host = Host(tmp_path / 'chat.sock', os.geteuid(), lambda: binding)
    host.start()
    bridge = ChatBridge(DEVICE, _paths=[host.endpoint], _root_uid=os.geteuid())
    direct_attempts = []
    def unavailable(request):
        direct_attempts.append(request.url.path)
        raise httpx.ConnectError('unavailable before send')
    def invoke(direct):
        if boundary == 'bridge':
            return bridge.request(wire.PATHS[0], body(), 3)
        with ChatHTTP(direct, bridge).stream('POST', wire.PATHS[0], json=json.loads(body())):
            pytest.fail('malformed route must not deliver HTTP')
    try:
        with httpx.Client(base_url='https://185.251.89.19:8443', transport=httpx.MockTransport(unavailable)) as direct:
            with ThreadPoolExecutor(1) as executor:
                pending = executor.submit(invoke, direct)
                request = read(peer)
                assert request['action'] == 'route'
                respond(peer, request, route={'malformed': True})
                with pytest.raises((wire.BridgeError, FriendsError)) as failure:
                    pending.result(3)
        assert instance.failure == 'DENIED' and instance.closed.is_set()
        assert binding.closed.is_set() and binding.cancelled.is_set()
        assert not instance.pending and instance.identifier == 1
        assert direct_attempts == ([wire.PATHS[0]] if boundary == 'http' else [])
        code = failure.value.code if boundary == 'bridge' else str(failure.value)
        print('MALFORMED:', boundary, 'native=DENIED', 'user=', code, 'native_http_requests=0')
        assert code == ('DENIED' if boundary == 'bridge' else 'access_rejected')
    finally:
        bridge.close()
        host.close()
        binding.close()


class StatusWorker:
    def __init__(self, gate):
        self.gate = gate
        parent, self.peer = socket.socketpair()
        self.chat = ChatLane(parent)
        self.chat.peers = [self.peer]
        self.hold = threading.Event()
        self.controls = queue.Queue()
        self.writer = threading.Lock()
        self.malformed = False
        self.leases = set()
        self.requests = []
        self.acquisitions = []
        self.closed = threading.Event()
        self.thread = threading.Thread(target=self.run)
        self.thread.start()

    def reply(self, request, **fields):
        with self.writer:
            respond(self.peer, request, **fields)

    def run(self):
        try:
            while True:
                request = mesh_ipc.receive(self.peer.fileno(), MAX_FRAME, time.monotonic() + 10)
                if request['action'] == 'route':
                    if self.hold.is_set():
                        self.controls.put(request)
                    else:
                        self.reply(request, route={} if self.malformed else 'SERVICE_ONLY')
                elif request['action'] == 'acquire':
                    self.acquisitions.append(request.get('generation'))
                    self.leases.add(request['id'])
                    self.reply(request, lease=request['id'], route='SERVICE_ONLY')
                elif request['action'] == 'release':
                    self.leases.discard(request['lease'])
                    self.reply(request)
                elif request['action'] == 'request':
                    self.requests.append(request['path'])
                    self.reply(request, status=200)
                else:
                    raise AssertionError(request['action'])
        except (EOFError, OSError):
            pass

    def close(self):
        assert not self.gate.finished
        self.chat.close()
        self.chat.reader.join(3)
        self.thread.join(3)
        assert not self.chat.reader.is_alive() and not self.thread.is_alive()
        self.peer.close()
        self.closed.set()


def wire_generation(service):
    def worker(gate):
        created = StatusWorker(gate)
        service.workers.append(created)
        return created
    service.owner.worker_factory = worker
    binding = service.owner.prepare(dict(material(), device=DEVICE), threading.Event(), time.monotonic() + 3)
    return binding, service.workers[0]


@pytest.mark.parametrize('caller', ['prepare', 'probe', 'binding', 'watcher', 'acquire'])
def test_control_contention_callers_keep_generation(service, monkeypatch, caller):
    binding, worker = wire_generation(service)
    checked = threading.Event()
    original = binding.native_alive
    def observed():
        try:
            return original()
        finally:
            if threading.current_thread() is service.owner.watcher:
                checked.set()
    with ThreadPoolExecutor(4) as executor:
        with service.owner.lock:
            worker.hold.set()
            operations = [executor.submit(worker.chat.call, 'route', lease=binding.generation_lease) for _ in range(4)]
            requests = [worker.controls.get(timeout=2) for _ in operations]
            monkeypatch.setattr(binding, 'native_alive', observed)
        try:
            touched = service.owner.touched
            if caller == 'watcher':
                assert checked.wait(2)
            else:
                with pytest.raises(ChatError, match='BUSY_OR_UNAVAILABLE'):
                    if caller == 'prepare':
                        service.owner.prepare(dict(material(), device=DEVICE), threading.Event(), time.monotonic() + 2)
                    elif caller == 'probe':
                        binding.probe(DEVICE)
                    elif caller == 'binding':
                        service.owner.binding()
                    else:
                        binding.acquire(DEVICE, threading.Event(), 1000)
            assert service.owner.touched == touched
            assert service.owner.watcher.is_alive() and not binding.cancelled.is_set()
            assert worker.acquisitions == [None] and worker.leases == {binding.generation_lease}
        finally:
            worker.hold.clear()
            for request in requests:
                worker.reply(request, route='SERVICE_ONLY')
            assert all(operation.result(2)['route'] == 'SERVICE_ONLY' for operation in operations)
    assert service.bridge.request(wire.PATHS[0], body(), 3)[0] == 200
    assert service.owner.current is binding and len(service.workers) == 1
    assert worker.acquisitions == [None, binding.generation_lease]


def test_watcher_handles_protocol_denial_and_old_result_is_generation_local(service):
    binding, worker = wire_generation(service)
    with service.owner.lock:
        worker.malformed = True
    assert worker.closed.wait(3)
    with service.owner.lock:
        assert service.owner.current is None and service.gates[0].finished
    assert service.owner.watcher.is_alive() and not service.owner.failed
    assert binding.closed.is_set() and worker.chat.failure == 'DENIED'
    with pytest.raises(ChatError, match='DENIED'):
        binding.probe(DEVICE)
    assert not worker.requests
    assert service.bridge.request(wire.PATHS[0], body(), 3)[0] == 200
    fresh = service.owner.current
    with pytest.raises(ChatError, match='DENIED'):
        binding.native_alive()
    assert service.owner.current is fresh and not fresh.cancelled.is_set()


@pytest.mark.parametrize('code', ['DENIED', 'CONFLICT', 'DEADLINE', 'CANCELLED'])
def test_terminal_native_status_keeps_original_type_after_cleanup(lane, code):
    instance, peer = lane
    binding = binding_for(instance)
    with ThreadPoolExecutor(1) as executor:
        pending = executor.submit(binding.native_alive)
        request = read(peer)
        mesh_ipc.send(peer.fileno(), dict(schema=1, id=request['id'], ok=False, error=code), MAX_FRAME, time.monotonic() + 2)
        with pytest.raises(ChatError, match=code):
            pending.result(2)
    binding.close()
    with pytest.raises(ChatError, match=code):
        binding.probe(DEVICE)
    assert binding.cancelled.is_set()


@pytest.mark.parametrize('phase', ['acquire', 'request'])
def test_denial_during_late_operation_result_is_not_replaced_by_cancellation(lane, tmp_path, monkeypatch, phase):
    instance, peer = lane
    binding = binding_for(instance)
    original = instance.call
    entered, resume = threading.Event(), threading.Event()
    def call(action, **values):
        result = original(action, **values)
        if action == phase:
            entered.set()
            assert resume.wait(3)
        return result
    monkeypatch.setattr(instance, 'call', call)
    host = Host(tmp_path / 'late.sock', os.geteuid(), lambda: binding)
    host.start()
    bridge = ChatBridge(DEVICE, _paths=[host.endpoint], _root_uid=os.geteuid())
    bridge.ROUTE = binding.route
    actions = []
    try:
        with ThreadPoolExecutor(2) as executor:
            pending = executor.submit(bridge.request, wire.PATHS[0], body(), 5)
            while True:
                request = read(peer)
                actions.append(request['action'])
                if request['action'] == 'acquire':
                    assert request['generation'] == binding.generation_lease
                    respond(peer, request, route='SERVICE_ONLY', lease=request['id'])
                elif request['action'] == 'request':
                    respond(peer, request, status=200)
                else:
                    assert request['action'] == 'route'
                    respond(peer, request, route='SERVICE_ONLY')
                if request['action'] == phase:
                    break
            assert entered.wait(2)
            check = executor.submit(binding.native_alive)
            request = read(peer)
            assert request['action'] == 'route'
            respond(peer, request, route={})
            with pytest.raises(ChatError, match='DENIED'):
                check.result(2)
            resume.set()
            with pytest.raises(wire.BridgeError, match='DENIED'):
                pending.result(2)
        assert actions.count('request') == (1 if phase == 'request' else 0)
        assert binding.closed.is_set() and instance.closed.is_set()
    finally:
        resume.set()
        bridge.close()
        host.close()
        binding.close()
