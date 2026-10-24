import base64
import array
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import socket
import sys
import threading
import time

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'linux'))
from mesh_chat import ChatError
from mesh_chat_host import Binding, Host
from provisioning import chat_bridge_protocol as wire
from provisioning.chat_bridge import ChatBridge

PUBLIC = bytes(range(64))
DEVICE = hashlib.sha256(PUBLIC).hexdigest()[:32]


def body():
    return json.dumps(dict(public_identity=base64.b64encode(PUBLIC).decode(), wireguard_public_key=base64.b64encode(b'w' * 32).decode(), chat_public='a' * 128)).encode()


class Lane:
    def __init__(self):
        self.lock = threading.Lock()
        self.next = 0
        self.leases, self.streams, self.peers = set(), {}, []
        self.requests = []
        self.release_count = 0
        self.block_api = False
        self.api_started = threading.Event()
        self.cancelled = threading.Event()

    def call(self, action, *, cancel=None, **values):
        if cancel is not None and cancel.is_set():
            raise ChatError('CANCELLED')
        if action == 'acquire':
            assert set(values['acquire']) == {'readiness', 'identity', 'anchor', 'resolver', 'underlying_index'}
            assert values['acquire']['identity'] == 'private-synthetic-test-key'
            with self.lock:
                self.next += 1
                self.leases.add(self.next)
                return dict(lease=self.next, route='EXISTING_EXIT')
        if action == 'release':
            with self.lock:
                self.leases.discard(values['lease'])
                self.release_count += 1
            return {}
        if action == 'request':
            self.requests.append(values)
            self.api_started.set()
            if self.block_api:
                while not cancel.is_set():
                    time.sleep(.01)
                self.cancelled.set()
                raise ChatError('CANCELLED')
            return dict(status=200, data=b'{"status":"synthetic"}')
        if action == 'open':
            local, peer = socket.socketpair()
            local.settimeout(.05)
            with self.lock:
                self.next += 1
                self.streams[self.next] = local
                self.peers.append(peer)
                return dict(stream=self.next)
        if action == 'close':
            with self.lock:
                channel = self.streams.pop(values['stream'], None)
            if channel is not None:
                channel.close()
            return {}
        channel = self.streams[values['stream']]
        while not cancel.is_set():
            try:
                if action == 'read':
                    data = channel.recv(values['size'])
                    return dict(data=data, count=len(data), eof=not data)
                if action == 'write':
                    data = base64.b64decode(values['data'])
                    return dict(count=channel.send(data))
                if action == 'finish':
                    channel.shutdown(socket.SHUT_WR)
                    return {}
                raise AssertionError(action)
            except TimeoutError:
                continue
        raise ChatError('CANCELLED')


@pytest.fixture
def bridge(tmp_path):
    tmp_path.chmod(0o700)
    lane = Lane()
    start = dict(readiness={'device': DEVICE}, identity='private-synthetic-test-key', anchor='synthetic-anchor', resolver='1.1.1.1:53', underlying_index=2)
    binding = Binding(lane, start, threading.Event())
    binding.ready.set()
    host = Host(tmp_path / 'chat.sock', os.getuid(), lambda: binding)
    host.start()
    client = ChatBridge(DEVICE, _paths=[host.endpoint], _root_uid=os.geteuid())
    yield client, host, binding, lane
    client.close()
    binding.close()
    host.close()
    for peer in lane.peers:
        peer.close()
    assert not lane.leases and not lane.streams
    assert not host.active and not host.thread.is_alive()
    assert not host.endpoint.exists()


def test_authenticated_api_keeps_private_material_inside_parent(bridge):
    client, _, _, lane = bridge
    status, result = client.request('/friends/chat/challenge', body(), 2)
    assert status == 200 and json.loads(result) == {'status': 'synthetic'}
    assert lane.requests[0]['path'] == '/friends/chat/challenge'
    assert base64.b64decode(lane.requests[0]['data']) == body()
    assert 'identity' not in lane.requests[0]


def test_complete_exit_error_response_never_replays_on_service_only(bridge):
    client, _, _, lane = bridge
    original = lane.call
    def reply(action, **values):
        result = original(action, **values)
        if action == 'request':
            result['status'] = 503
        return result
    lane.call = reply
    client.configure(lambda: pytest.fail('completed EXIT response replayed through service-only'))
    assert client.request('/friends/chat/challenge', body(), 2)[0] == 503
    assert len(lane.requests) == 1 and client.route == 'EXISTING_EXIT'


def test_mailbox_fd_is_real_duplex_and_preserves_half_close(bridge):
    client, _, _, lane = bridge
    channel = client.open_mailbox(time.monotonic() + 5, threading.Event())
    assert channel.family == socket.AF_UNIX and not os.get_inheritable(channel.fileno())
    channel.settimeout(3)
    peer = lane.peers[0]
    peer.settimeout(3)
    upload, download = bytes(range(256)) * 256, bytes(reversed(range(256))) * 256
    def remote():
        received = bytearray()
        while len(received) < len(upload):
            received.extend(peer.recv(16384))
        assert bytes(received) == upload
        assert peer.recv(1) == b''
        peer.sendall(download)
        peer.shutdown(socket.SHUT_WR)
    with ThreadPoolExecutor(1) as pool:
        future = pool.submit(remote)
        channel.sendall(upload)
        channel.shutdown(socket.SHUT_WR)
        received = bytearray()
        while len(received) < len(download):
            part = channel.recv(16384)
            assert part
            received.extend(part)
        assert bytes(received) == download
        future.result(3)
    channel.close()


def test_device_and_payload_identity_are_bound(bridge):
    client, host, _, lane = bridge
    foreign = ChatBridge('f' * 32, _paths=[host.endpoint], _root_uid=os.geteuid())
    with pytest.raises(wire.BridgeError, match='DENIED'):
        foreign.request('/friends/chat/challenge', body(), 1)
    request = dict(schema=1, id=1, action='request', device=DEVICE, budget_ms=1000, path='/friends/chat/challenge',
                   data=base64.b64encode(json.dumps(dict(public_identity=base64.b64encode(b'x' * 64).decode())).encode()).decode())
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.connect(str(host.endpoint))
        wire.write(connection, request)
        reply = wire.read(connection, time.monotonic() + 2)
        assert reply['ok'] is False and reply['error'] == 'DENIED'
    assert not lane.requests


def test_disconnected_or_retired_binding_cannot_open_new_work(bridge):
    client, _, binding, lane = bridge
    binding.ready.clear()
    with pytest.raises(wire.BridgeError):
        client.open_mailbox(time.monotonic() + 1, threading.Event())
    binding.close()
    binding.ready.set()
    with pytest.raises(wire.BridgeError):
        client.open_mailbox(time.monotonic() + 1, threading.Event())
    assert not lane.peers and not lane.leases


def test_client_disconnect_cancels_api_and_releases_lease(bridge):
    client, _, _, lane = bridge
    lane.block_api = True
    with ThreadPoolExecutor(1) as pool:
        future = pool.submit(client.request, '/friends/chat/challenge', body(), 30)
        assert lane.api_started.wait(2)
        client.close()
        with pytest.raises(OSError):
            future.result(3)
        assert lane.cancelled.wait(2)


def test_binding_teardown_interrupts_mailbox_not_a_new_session(bridge):
    client, host, binding, lane = bridge
    channel = client.open_mailbox(time.monotonic() + 10, threading.Event())
    channel.settimeout(3)
    binding.close()
    replacement = Binding(lane, dict(readiness={'device': DEVICE}, identity='private-synthetic-test-key',
                                    anchor='synthetic-anchor', resolver='1.1.1.1:53', underlying_index=2), threading.Event())
    replacement.ready.set()
    host.provider = lambda: replacement
    assert channel.recv(1) == b''
    channel.close()
    assert client.request('/friends/chat/challenge', body(), 2)[0] == 200
    assert not replacement.closed.is_set()
    replacement.close()


def test_cancel_interrupts_public_open_while_waiting_for_native(bridge, monkeypatch):
    client, _, _, lane = bridge
    started, cancelled = threading.Event(), threading.Event()
    original = lane.call
    def block_open(action, *, cancel=None, **values):
        if action == 'open':
            started.set()
            while not cancel.is_set():
                time.sleep(.01)
            raise ChatError('CANCELLED')
        return original(action, cancel=cancel, **values)
    monkeypatch.setattr(lane, 'call', block_open)
    with ThreadPoolExecutor(1) as pool:
        future = pool.submit(client.open_mailbox, time.monotonic() + 30, cancelled)
        assert started.wait(2)
        cancelled.set()
        with pytest.raises(wire.BridgeError, match='CANCELLED'):
            future.result(2)


def test_public_admission_is_bounded_to_four_live_mailboxes(bridge):
    client, host, _, lane = bridge
    channels = []
    try:
        for _ in range(4):
            channels.append(client.open_mailbox(time.monotonic() + 5, threading.Event()))
        assert len(host.active) == 4 and len(lane.leases) == 4
        with pytest.raises(OSError):
            client.open_mailbox(time.monotonic() + 1, threading.Event())
        assert len(lane.peers) == 4
    finally:
        for channel in channels:
            channel.close()


def test_existing_exit_does_not_accept_a_native_service_only_result(bridge, monkeypatch):
    client, _, _, lane = bridge
    original = lane.call
    def wrong_route(action, **values):
        result = original(action, **values)
        return dict(result, route='SERVICE_ONLY') if action == 'acquire' else result
    monkeypatch.setattr(lane, 'call', wrong_route)
    with pytest.raises(wire.BridgeError):
        client.request('/friends/chat/challenge', body(), 2)
    assert not lane.leases and not lane.requests and lane.release_count == 1


def test_two_active_vpn_owners_fail_closed_without_api_mutation(bridge, tmp_path):
    _, host, binding, lane = bridge
    other = Host(tmp_path / 'other.sock', os.getuid(), lambda: binding)
    other.start()
    client = ChatBridge(DEVICE, _paths=[host.endpoint, other.endpoint], _root_uid=os.getuid())
    try:
        with pytest.raises(wire.BridgeError, match='DENIED'):
            client.request('/friends/chat/challenge', body(), 2)
        assert not lane.leases and not lane.requests
    finally:
        client.close()
        other.close()


def test_mailbox_lifetime_expires_without_leaking_resources(bridge):
    client, host, _, lane = bridge
    channel = client.open_mailbox(time.monotonic() + .5, threading.Event())
    channel.settimeout(2)
    try:
        assert channel.recv(1) == b''
        limit = time.monotonic() + 2
        while host.active and time.monotonic() < limit:
            time.sleep(.01)
        assert not host.active and not lane.leases and not lane.streams
    finally:
        channel.close()


@pytest.mark.parametrize('kind', ['duplicate', 'inet', 'file'])
def test_rejected_descriptor_sets_are_closed(kind):
    before = len(os.listdir('/proc/self/fd'))
    control, peer = socket.socketpair()
    channel = socket.socket(socket.AF_INET if kind == 'inet' else socket.AF_UNIX, socket.SOCK_STREAM)
    descriptor = os.open('/dev/null', os.O_RDONLY) if kind == 'file' else channel.fileno()
    try:
        values = [descriptor, descriptor] if kind == 'duplicate' else [descriptor]
        control.sendmsg([b'F'], [(socket.SOL_SOCKET, socket.SCM_RIGHTS, array.array('i', values))])
        with pytest.raises(OSError):
            wire.receive_socket(peer)
    finally:
        if kind == 'file':
            os.close(descriptor)
        channel.close()
        control.close()
        peer.close()
    assert len(os.listdir('/proc/self/fd')) == before


@pytest.mark.parametrize('change', [{'device': True}, {'budget_ms': 0}, {'budget_ms': 30001}, {'action': 'exec'},
                                   {'path': '/admin'}, {'underlying_index': 1}, {'identity': 'secret'}, {'id': True}])
def test_public_protocol_rejects_privileged_overrides(change):
    request = dict(schema=1, id=1, action='open', device=DEVICE, budget_ms=1000)
    request.update(change)
    with pytest.raises((ValueError, wire.BridgeError)):
        wire.validate(request)


def test_peer_uid_mismatch_never_calls_provider(tmp_path):
    parent, peer = socket.socketpair()
    host = Host(tmp_path / 'unused.sock', os.getuid() + 1, lambda: pytest.fail('unauthorized provider access'))
    host._serve(parent)
    assert peer.recv(1) == b''
    peer.close()


def test_unsafe_endpoint_is_not_replaced(tmp_path):
    endpoint = tmp_path / 'chat.sock'
    endpoint.write_text('do not remove')
    host = Host(endpoint, os.getuid(), lambda: None)
    with pytest.raises(ValueError):
        host.start()
    assert endpoint.read_text() == 'do not remove'
