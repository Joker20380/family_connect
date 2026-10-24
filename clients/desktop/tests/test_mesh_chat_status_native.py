from concurrent.futures import ThreadPoolExecutor
import threading
import time

import pytest

from test_mesh_chat_lifetime_native import authenticated, pytestmark
from test_mesh_chat_terminal_native import exchange, held_watcher
from mesh_chat import ChatError
from mesh_ownership import Ownership, OwnershipError
import mesh_ipc
from provisioning import chat_bridge_protocol as wire


def test_control_contention_retains_authenticated_transport(authenticated, monkeypatch):
    fixture = authenticated
    exchange(fixture)
    while fixture.events.history.count('leases:1') < 4:
        fixture.events.events.get(timeout=3)
    binding, generation = fixture.owner.current, fixture.owner.generation_lease
    lane = binding.lane
    entered, resume, full = threading.Event(), threading.Event(), threading.Event()
    original_read, original_submit = mesh_ipc.receive, lane._submit
    def receive(descriptor, *args):
        reply = original_read(descriptor, *args)
        if descriptor == lane.connection.fileno() and not resume.is_set():
            assert reply['route'] == 'SERVICE_ONLY'
            entered.set()
            assert resume.wait(3)
        return reply
    def submit(action, values):
        result = original_submit(action, values)
        with lane.lock:
            if len(lane.pending) == 4:
                full.set()
        return result
    error = None
    with fixture.owner.lock, ThreadPoolExecutor(4) as executor:
        assert lane.call('route', lease=generation)['route'] == 'SERVICE_ONLY'
        monkeypatch.setattr(mesh_ipc, 'receive', receive)
        monkeypatch.setattr(lane, '_submit', submit)
        operations = [executor.submit(lane.call, 'route', lease=generation) for _ in range(4)]
        try:
            assert entered.wait(2) and full.wait(2)
            try:
                binding.native_alive()
            except ChatError as caught:
                error = caught.code
        finally:
            resume.set()
        assert all(operation.result(2)['route'] == 'SERVICE_ONLY' for operation in operations)
        assert lane.call('route', lease=generation)['route'] == 'SERVICE_ONLY'
        print('AUTHENTICATED CONTROL:', 'error=', error, 'cancelled=', binding.cancelled.is_set(),
              'opens=', fixture.events.history.count('open'), 'native_route=SERVICE_ONLY')
        assert not binding.cancelled.is_set() and error == 'BUSY_OR_UNAVAILABLE'
    exchange(fixture)
    while fixture.events.history.count('leases:1') < 7:
        fixture.events.events.get(timeout=3)
    assert fixture.owner.current is binding and fixture.owner.generation_lease == generation
    assert len(fixture.workers) == 1 and fixture.events.history.count('open') == 1
    assert 'leases:0' not in fixture.events.history
    assert lane.call('route', lease=generation)['route'] == 'SERVICE_ONLY'


def test_malformed_route_fences_then_drains_actual_native_owner(authenticated, monkeypatch):
    fixture = authenticated
    exchange(fixture)
    binding, worker, gate = fixture.owner.current, fixture.workers[0], fixture.owner.gate
    descriptor = binding.lane.connection.fileno()
    original = mesh_ipc.receive
    malformed = threading.Event()
    def receive(current, *args):
        reply = original(current, *args)
        if current == descriptor and reply.get('route') == 'SERVICE_ONLY' and not malformed.is_set():
            malformed.set()
            return dict(reply, route={})
        return reply
    sent = len(fixture.api_calls)
    with held_watcher(fixture, monkeypatch):
        monkeypatch.setattr(mesh_ipc, 'receive', receive)
        with pytest.raises(wire.BridgeError, match='DENIED'):
            exchange(fixture)
        assert malformed.is_set() and binding.lane.failure == 'DENIED'
        assert binding.closed.is_set() and binding.cancelled.is_set()
        assert len(fixture.api_calls) == sent
    fixture.events.until_all('leases:0', 'cleanup_entered')
    assert gate.active and worker.process.poll() is None
    assert (fixture.directory / 'transport.lock').read_bytes() == b'chat'
    with pytest.raises(OwnershipError, match='OWNER_BUSY'):
        Ownership('chat', fixture.directory).acquire(threading.Event(), time.monotonic() + .2)
    fixture.events.cleanup.set()
    fixture.events.until('cleaned')
    worker.process.wait(5)
    with fixture.owner.lock:
        assert fixture.owner.current is None and fixture.owner.generation_lease is None
        assert not gate.active and not fixture.owner.failed
    exchange(fixture)
    fresh = fixture.owner.current
    with pytest.raises(ChatError, match='DENIED'):
        binding.native_alive()
    assert fixture.owner.current is fresh and not fresh.cancelled.is_set()
    assert len(fixture.workers) == 2 and fixture.events.history.count('open') == 2
