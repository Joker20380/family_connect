from concurrent.futures import ThreadPoolExecutor
import base64
import json
import threading

from test_mesh_chat_lifetime_native import authenticated, pytestmark
from test_mesh_chat_terminal_native import exchange
from provisioning import chat_bridge_protocol as wire
import mesh_ipc
from mesh_chat import ChatError


def test_operation_release_waits_for_real_control_capacity(authenticated, monkeypatch):
    fixture = authenticated
    exchange(fixture)
    while fixture.events.history.count('leases:1') < 4:
        fixture.events.events.get(timeout=3)
    binding, generation = fixture.owner.current, fixture.owner.generation_lease
    lane = binding.lane
    operation = binding.acquire(fixture.device.reference, threading.Event(), 3000)
    body = dict(public_identity=fixture.device.public_identity, wireguard_public_key=fixture.device.wireguard_public_key,
                chat_public=fixture.chat_identity.get_public_key().hex())
    assert lane.call('request', lease=operation, path=wire.PATHS[0], data=base64.b64encode(json.dumps(body).encode()).decode(), budget_ms=3000)['status'] == 200
    entered, resume, full, attempted, watcher = (threading.Event() for _ in range(5))
    original_read, original_submit = mesh_ipc.receive, lane._submit
    def receive(descriptor, *args):
        reply = original_read(descriptor, *args)
        if descriptor == lane.connection.fileno() and not resume.is_set():
            entered.set()
            assert resume.wait(3)
        return reply
    def submit(action, values):
        try:
            result = original_submit(action, values)
        except ChatError:
            if action == 'release':
                attempted.set()
            raise
        with lane.lock:
            if len(lane.pending) == 4:
                full.set()
        if threading.current_thread() is fixture.owner.watcher:
            watcher.set()
        return result
    if hasattr(lane, 'capacity'):
        original_wait = lane.capacity.wait
        def wait(timeout=None):
            attempted.set()
            return original_wait(timeout)
        monkeypatch.setattr(lane.capacity, 'wait', wait)
    with fixture.owner.lock:
        monkeypatch.setattr(mesh_ipc, 'receive', receive)
        monkeypatch.setattr(lane, '_submit', submit)
    with ThreadPoolExecutor(4) as executor:
        assert watcher.wait(2) and entered.wait(2)
        controls = [executor.submit(lane.call, 'route', lease=generation) for _ in range(3)]
        try:
            assert entered.wait(2) and full.wait(2)
            pending = executor.submit(binding.release, operation)
            assert attempted.wait(2)
        finally:
            resume.set()
        assert all(control.result(2)['route'] == 'SERVICE_ONLY' for control in controls)
        pending.result(2)
        try:
            route = lane.call('route', lease=operation)['route']
        except ChatError as error:
            route = error.code
        print('RELEASE CONTROL: operation_route=', route, 'opens=', fixture.events.history.count('open'))
        assert route == 'UNAVAILABLE'
    while fixture.events.history.count('leases:1') < 5:
        fixture.events.events.get(timeout=3)
    assert fixture.owner.current is binding and fixture.events.history.count('open') == 1
    assert lane.call('route', lease=generation)['route'] == 'SERVICE_ONLY'
