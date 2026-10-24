import base64
from concurrent.futures import ThreadPoolExecutor
import copy
import os
from pathlib import Path
import sys
import threading
import time
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'linux'))
from mesh_chat_service import ServiceHost, ServiceOwner
from mesh_materials import MaterialsError
from provisioning.chat_bridge import ChatBridge
from provisioning import chat_bridge_protocol as wire
from provisioning.chat_transport import ProtectedMailbox, _DirectDeadline
from messenger.mailbox import MailboxError
from test_mesh_chat_host import DEVICE, Lane, body


def wait(predicate):
    deadline = time.monotonic() + 5
    while not predicate():
        assert time.monotonic() < deadline
        time.sleep(.01)


def material():
    return dict(identity=base64.b64encode(b'x' * 64).decode(), wireguard_public=base64.b64encode(b'w' * 32).decode())


class Gate:
    def __init__(self, role):
        assert role == 'chat'
        self.active, self.descriptor, self.reserved, self.finished = False, None, False, False

    def acquire(self, cancel, deadline):
        assert not self.active and not self.finished and not cancel.is_set()
        self.active = True

    def preempted(self):
        return self.reserved

    def finish(self):
        assert self.active
        self.active, self.finished = False, True

    def close(self):
        assert not self.active


class Materials:
    def __init__(self):
        self.calls = []
        self.error = None
        self.hold = None

    def resolve(self, supplied, underlying, cancel, deadline, required):
        self.calls.append(copy.deepcopy(supplied))
        assert required and underlying == 2 and supplied['anchor'] == 'packaged-root-anchor'
        if self.hold is not None:
            self.hold.set()
            while not cancel.is_set():
                time.sleep(.01)
        if cancel.is_set():
            raise MaterialsError('CANCELLED')
        if self.error:
            raise MaterialsError(self.error)
        return dict(identity='private-synthetic-test-key', anchor=supplied['anchor'],
                    readiness=dict(device=DEVICE, expires_at=int(time.time()) + 60))


class ServiceLane(Lane):
    def call(self, action, **values):
        result = super().call(action, **values)
        if action == 'acquire':
            result['route'] = 'CONNECTING'
        return result


class Worker:
    def __init__(self, gate):
        assert gate.active
        self.gate, self.chat = gate, ServiceLane()
        self.closed = False
        self.fail = False

    def close(self):
        assert not self.gate.finished
        self.closed = True
        if self.fail:
            raise RuntimeError('CLEANUP_PENDING')


@pytest.fixture
def service(tmp_path):
    materials, workers, gates = Materials(), [], []
    network = dict(index=2, name='synthetic-underlay', addresses=['192.0.2.1'])
    def worker(gate):
        value = Worker(gate)
        workers.append(value)
        return value
    def gate(role):
        value = Gate(role)
        gates.append(value)
        return value
    owner = ServiceOwner(materials, 'packaged-root-anchor', underlying=SimpleNamespace(read=lambda _: dict(network)),
                         ownership_factory=gate, worker_factory=worker)
    host = ServiceHost(tmp_path / 'service.sock', os.getuid(), owner)
    host.start()
    bridge = ChatBridge(DEVICE, _paths=[], _root_uid=os.getuid())
    bridge.service_path = host.endpoint
    bridge.configure(material)
    yield SimpleNamespace(owner=owner, host=host, bridge=bridge, materials=materials, workers=workers, gates=gates, network=network)
    bridge.close()
    owner.cancel.set()
    host.close()
    if owner.failed:
        with pytest.raises(RuntimeError, match='CLEANUP_UNCONFIRMED'):
            owner.close()
    else:
        owner.close()
    assert not host.active and not host.thread.is_alive() and not owner.watcher.is_alive()
    for value in workers:
        for peer in value.chat.peers:
            peer.close()


def test_service_api_and_real_mailbox_fd_without_packet_owner(service):
    bridge = service.bridge
    assert bridge.request(wire.PATHS[0], body(), 5)[0] == 200
    assert bridge.route == 'SERVICE_ONLY'
    assert len(service.workers) == 1 and service.gates[0].active
    with bridge.open_service_mailbox(time.monotonic() + 3, threading.Event()) as channel:
        channel.settimeout(2)
        wait(lambda: service.workers[0].chat.peers)
        service.workers[0].chat.peers[0].sendall(b'mailbox')
        assert channel.recv(7) == b'mailbox'
    service.workers[0].chat.peers[0].close()
    wait(lambda: not service.workers[0].chat.leases and not service.workers[0].chat.streams)
    assert len(service.materials.calls) == 1
    assert service.materials.calls[0]['profile'] == 'P0'


def test_preemption_drains_old_generation_then_allows_new_demand(service):
    service.bridge.request(wire.PATHS[0], body(), 5)
    previous = service.owner.current
    first = service.workers[0]
    service.gates[0].reserved = True
    wait(lambda: service.gates[0].finished)
    assert first.closed and previous.closed.is_set()
    with pytest.raises(wire.BridgeError):
        previous.acquire(DEVICE, threading.Event(), 1000)
    service.bridge.request(wire.PATHS[0], body(), 5)
    assert service.owner.current is not previous and len(service.workers) == 2


def test_concurrent_api_requests_share_one_generation(service):
    with ThreadPoolExecutor(3) as pool:
        replies = list(pool.map(lambda _: service.bridge.request(wire.PATHS[0], body(), 5), range(3)))
    assert all(reply[0] == 200 for reply in replies)
    assert len(service.workers) == len(service.gates) == len(service.materials.calls) == 1
    wait(lambda: not service.workers[0].chat.leases)


@pytest.mark.parametrize('change', ['underlying', 'expiry', 'shutdown'])
def test_generation_cannot_restore_after_underlying_expiry_or_shutdown(service, change):
    service.bridge.request(wire.PATHS[0], body(), 5)
    previous = service.owner.current
    if change == 'underlying':
        service.network['addresses'] = ['192.0.2.2']
        wait(lambda: service.gates[0].finished)
    elif change == 'expiry':
        previous.material['readiness']['expires_at'] = 1
        service.materials.error = 'EXPIRED_ON_IMPORT'
        with pytest.raises(wire.BridgeError, match='DENIED'):
            service.bridge.request(wire.PATHS[0], body(), 5)
    else:
        service.owner.close()
    assert previous.closed.is_set()


@pytest.mark.parametrize('error', ['AUTHORIZATION_REJECTED', 'EXPIRED_ON_IMPORT', 'NATIVE_VALIDATION_FAILED', 'CANCELLED', 'DEADLINE'])
def test_rejected_material_never_opens_worker(service, error):
    service.materials.error = error
    expected = error if error in ('CANCELLED', 'DEADLINE') else 'DENIED'
    with pytest.raises(wire.BridgeError, match=expected):
        service.bridge.request(wire.PATHS[0], body(), 3)
    assert not service.workers
    wait(lambda: service.gates[0].finished)


def test_cancel_during_bootstrap_no_late_worker(service):
    service.materials.hold = threading.Event()
    failures = []
    def request():
        try:
            service.bridge.request(wire.PATHS[0], body(), 5)
        except OSError as error:
            failures.append(error)
    thread = threading.Thread(target=request)
    thread.start()
    assert service.materials.hold.wait(2)
    service.gates[0].reserved = True
    thread.join(5)
    assert not thread.is_alive() and failures and not service.workers
    wait(lambda: service.gates[0].finished)


def test_cleanup_failure_is_sticky_not_a_new_owner(service):
    service.bridge.request(wire.PATHS[0], body(), 5)
    service.workers[0].fail = True
    service.gates[0].reserved = True
    wait(lambda: service.owner.failed)
    with pytest.raises(wire.BridgeError):
        service.bridge.request(wire.PATHS[0], body(), 3)
    assert len(service.workers) == 1 and not service.gates[0].finished


@pytest.mark.parametrize('field', ['anchor', 'profile', 'endpoint', 'command', 'resolver', 'underlying_index', 'path'])
def test_public_service_preparation_rejects_untrusted_overrides(field):
    request = dict(schema=1, id=1, device=DEVICE, action='prepare', budget_ms=1000, **material(), **{field: 'untrusted'})
    with pytest.raises(ValueError):
        wire.validate_service(request)


@pytest.mark.parametrize('code', ['DENIED', 'CONFLICT', 'INVALID_RESPONSE', 'DEADLINE', 'CANCELLED'])
def test_existing_exit_terminal_cannot_advance_to_service_only(code):
    def reject(*args):
        raise wire.BridgeError(code)
    mailbox = object.__new__(ProtectedMailbox)
    mailbox.bridge = SimpleNamespace(open_mailbox=reject)
    with pytest.raises(_DirectDeadline if code == 'DEADLINE' else MailboxError) as failure:
        mailbox._existing(time.monotonic() + 2, threading.Event())
    assert str(failure.value) not in ('unavailable', 'timeout')
