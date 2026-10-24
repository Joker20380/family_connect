from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import os
from queue import Queue
import socket
import threading
import time
from types import SimpleNamespace

import pytest

from test_mesh_chat_host import bridge, body
from test_mesh_chat_service import service
from provisioning import chat_bridge_protocol as wire


@pytest.fixture(autouse=True)
def no_public_resource_leaks():
    before = {thread for thread in threading.enumerate() if thread.name.startswith('fc-chat-')}
    descriptors = len(os.listdir('/proc/self/fd'))
    yield
    assert {thread for thread in threading.enumerate() if thread.name.startswith('fc-chat-')} == before
    assert len(os.listdir('/proc/self/fd')) == descriptors


@pytest.fixture(params=['probe', 'prepare'])
def public(request):
    if request.param == 'probe':
        client, host, binding, lane = request.getfixturevalue('bridge')
        return SimpleNamespace(client=client, host=host, lane=lane, action='probe',
                               route='EXISTING_EXIT', generation=0, open=client.open_mailbox)
    setup = request.getfixturevalue('service')
    setup.bridge._service(time.monotonic() + 5)
    with setup.host.lock:
        handlers = list(setup.host.active.values())
    for handler in handlers:
        handler.join(5)
        assert not handler.is_alive()
    return SimpleNamespace(client=setup.bridge, host=setup.host, lane=setup.workers[0].chat,
                           action='prepare', route='SERVICE_ONLY', generation=1,
                           open=setup.bridge.open_service_mailbox)


def raw_open(public):
    deadline = time.monotonic() + 10
    with public.client._connection(public.host.endpoint, deadline) as connection:
        public.client._request(connection, 'open', deadline, _route=public.route)
        return wire.receive_socket(connection)


@contextmanager
def held_reply(public, monkeypatch):
    release, received = threading.Event(), threading.Event()
    phases = Queue()
    state = SimpleNamespace(connection=None, handler=None, release=release,
                            received=received, phases=phases, watched=False)
    original_write, original_read = wire.write, wire.read
    original_recv, original_request = socket.socket.recv, public.client._request

    def write(connection, value):
        original_write(connection, value)
        if (threading.current_thread().name == 'fc-chat-operation' and value.get('ok') is True
                and state.handler is None):
            state.handler = threading.current_thread()
            assert release.wait(8)

    def read(connection, deadline):
        reply = original_read(connection, deadline)
        if connection is state.connection:
            received.set()
        return reply

    def recv(connection, *args, **kwargs):
        if connection is state.connection and received.is_set() and not state.watched:
            state.watched = True
            phases.put('completion')
        return original_recv(connection, *args, **kwargs)

    def request(connection, action, *args, **kwargs):
        if action == public.action:
            state.connection = connection
        elif action == 'open':
            phases.put('open')
        return original_request(connection, action, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(wire, 'write', write)
        patch.setattr(wire, 'read', read)
        patch.setattr(socket.socket, 'recv', recv)
        patch.setattr(public.client, '_request', request)
        try:
            yield state
        finally:
            release.set()
            if state.handler is not None:
                state.handler.join(5)
                assert not state.handler.is_alive()


def test_control_completion_fences_fourth_mailbox(public, monkeypatch):
    channels = [raw_open(public) for _ in range(3)]
    with public.host.lock:
        first_handler = next(iter(public.host.active.values()))
    try:
        with ThreadPoolExecutor(1) as pool, held_reply(public, monkeypatch) as barrier:
            opened = pool.submit(public.open, time.monotonic() + 6, threading.Event())
            phase = barrier.phases.get(timeout=5)
            assert barrier.received.is_set()
            assert len(public.host.active) == 4
            assert len(public.lane.leases) == 3 + public.generation
            if phase == 'open':
                with pytest.raises(OSError) as failure:
                    opened.result(5)
                pytest.fail(f'{public.action} reply admitted dependent open before cleanup: {failure.value!r}')
            assert phase == 'completion' and not opened.done()
            barrier.release.set()
            channels.append(opened.result(5))
        assert len(public.host.active) == 4
        assert len(public.lane.leases) == 4 + public.generation
        assert len(public.lane.peers) == 4 and not public.lane.requests
        with pytest.raises(OSError):
            public.open(time.monotonic() + 1, threading.Event())
        assert len(public.lane.peers) == 4
        channels.pop(0).close()
        public.lane.peers[0].close()
        first_handler.join(5)
        assert not first_handler.is_alive() and len(public.host.active) == 3
        channels.append(public.open(time.monotonic() + 5, threading.Event()))
        assert len(public.host.active) == 4 and len(public.lane.peers) == 5
        assert len(public.lane.leases) == 4 + public.generation
        assert not public.client.connections and not public.lane.requests
    finally:
        for channel in channels:
            channel.close()


@pytest.mark.parametrize('ending', ['cancel', 'client_close', 'deadline', 'host_close'])
def test_control_completion_interruptions_are_bounded(public, monkeypatch, ending):
    cancelled = threading.Event()
    with ThreadPoolExecutor(2) as pool, held_reply(public, monkeypatch) as barrier:
        deadline = time.monotonic() + (0.5 if ending == 'deadline' else 5)
        opened = pool.submit(public.open, deadline, cancelled)
        assert barrier.phases.get(timeout=3) == 'completion'
        assert len(public.host.active) == 1 and not opened.done()
        closing = None
        if ending == 'cancel':
            cancelled.set()
        elif ending == 'client_close':
            public.client.close()
        elif ending == 'host_close':
            closing = pool.submit(public.host.close)
        expected = 'DEADLINE' if ending == 'deadline' else 'CANCELLED'
        with pytest.raises(OSError) as failure:
            opened.result(3)
        if ending != 'host_close':
            assert failure.value.code == expected
        assert len(public.host.active) == 1
        assert barrier.handler.is_alive()
        if closing is not None:
            assert not closing.done()
        assert not public.lane.requests and not public.lane.peers
        assert len(public.lane.leases) == public.generation
        assert not public.client.connections
        barrier.release.set()
        if closing is not None:
            closing.result(3)
    assert not public.host.active


def test_control_completion_before_single_http_send(public, monkeypatch):
    channels = [raw_open(public) for _ in range(3)]
    try:
        with ThreadPoolExecutor(1) as pool, held_reply(public, monkeypatch) as barrier:
            reply = pool.submit(public.client.request, wire.PATHS[0], body(), 5)
            assert barrier.phases.get(timeout=3) == 'completion'
            assert not reply.done() and not public.lane.requests
            assert len(public.host.active) == 4
            barrier.release.set()
            assert reply.result(3)[0] == 200
        assert len(public.lane.requests) == 1
    finally:
        for channel in channels:
            channel.close()


@pytest.mark.parametrize('code', ['DENIED', 'CONFLICT', 'DEADLINE', 'CANCELLED'])
def test_control_terminal_reason_does_not_wait_for_cleanup(public, monkeypatch, code):
    original_write = wire.write
    release, sent = threading.Event(), threading.Event()
    handlers = []

    def write(connection, value):
        if threading.current_thread().name != 'fc-chat-operation':
            return original_write(connection, value)
        handlers.append(threading.current_thread())
        original_write(connection, dict(schema=1, id=value['id'], ok=False, error=code))
        sent.set()
        assert release.wait(5)

    monkeypatch.setattr(wire, 'write', write)
    try:
        with ThreadPoolExecutor(1) as pool:
            opened = pool.submit(public.open, time.monotonic() + 3, threading.Event())
            assert sent.wait(2)
            with pytest.raises(wire.BridgeError, match=code):
                opened.result(2)
            assert len(public.host.active) == 1 and handlers[0].is_alive()
            assert not public.lane.requests and not public.lane.peers
    finally:
        release.set()
        for handler in handlers:
            handler.join(3)
            assert not handler.is_alive()


def test_control_trailing_bytes_fail_closed_without_open(public, monkeypatch):
    original_write = wire.write

    def write(connection, value):
        original_write(connection, value)
        if threading.current_thread().name == 'fc-chat-operation':
            connection.sendall(b'!')

    monkeypatch.setattr(wire, 'write', write)
    with pytest.raises(wire.BridgeError, match='DENIED'):
        public.open(time.monotonic() + 3, threading.Event())
    assert not public.lane.requests and not public.lane.peers


def test_eof_and_slot_removal_share_admission_lock(public, monkeypatch):
    channels = [raw_open(public) for _ in range(3)]
    removing, release, next_open = threading.Event(), threading.Event(), threading.Event()
    close_locked = []
    original_close, original_request = socket.socket.close, public.client._request

    class HeldRemoval(dict):
        def pop(self, connection, default=None):
            if not removing.is_set():
                removing.set()
                assert release.wait(5)
            return super().pop(connection, default)

    def close(connection):
        if connection in public.host.active:
            close_locked.append(public.host.lock.locked())
        return original_close(connection)

    def request(connection, action, *args, **kwargs):
        if action == 'open':
            next_open.set()
        return original_request(connection, action, *args, **kwargs)

    with public.host.lock:
        public.host.active = HeldRemoval(public.host.active)
    monkeypatch.setattr(socket.socket, 'close', close)
    monkeypatch.setattr(public.client, '_request', request)
    try:
        with ThreadPoolExecutor(1) as pool:
            opened = pool.submit(public.open, time.monotonic() + 5, threading.Event())
            try:
                assert removing.wait(3) and next_open.wait(3)
                assert close_locked == [True]
                assert len(public.host.active) == 4 and not opened.done()
                assert len(public.lane.peers) == 3
            finally:
                release.set()
            channels.append(opened.result(3))
        assert len(public.host.active) == 4 and len(public.lane.peers) == 4
    finally:
        release.set()
        for channel in channels:
            channel.close()
