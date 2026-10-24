from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import os
from queue import Queue
import socket
import threading
import time
from types import SimpleNamespace

import pytest

from test_chat_direct import integration, enroll
from provisioning import chat_bridge_protocol as wire


@pytest.fixture(autouse=True)
def no_direct_resource_leaks():
    prefixes = ('fc-chat-', 'fc-direct-')
    before = {thread for thread in threading.enumerate() if thread.name.startswith(prefixes)}
    descriptors = len(os.listdir('/proc/self/fd'))
    yield
    assert {thread for thread in threading.enumerate() if thread.name.startswith(prefixes)} == before
    assert len(os.listdir('/proc/self/fd')) == descriptors


@pytest.fixture
def authorized(integration, monkeypatch):
    enroll(integration)
    assert integration.api.calls == list(wire.PATHS)
    with integration.host.lock:
        handlers = list(integration.host.active.values())
    for handler in handlers:
        handler.join(5)
        assert not handler.is_alive()
    backing = SimpleNamespace(opens=[], active=set())

    @contextmanager
    def operation(cancel, deadline, **fields):
        assert fields == dict(action='open', host=integration.api.node['host'],
                              port=integration.api.node['port'])
        local, peer = socket.socketpair()
        opened = SimpleNamespace(peer=peer, handler=threading.current_thread(), closed=threading.Event())
        backing.opens.append(opened)
        backing.active.add(local)
        try:
            yield {}, local
        finally:
            local.close()
            peer.close()
            backing.active.remove(local)
            opened.closed.set()

    monkeypatch.setattr(integration.native, 'operation', operation)
    integration.backing = backing
    yield integration
    for opened in backing.opens:
        try:
            opened.peer.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        opened.peer.close()
    integration.host.close()
    assert not backing.active
    assert all(opened.closed.is_set() and not opened.handler.is_alive() for opened in backing.opens)
    assert integration.api.calls == list(wire.PATHS)


@contextmanager
def held_closed_probe(setup, monkeypatch):
    host, client = setup.host, setup.direct
    state = SimpleNamespace(connection=None, handler=None, eof=threading.Event(),
                            closed=threading.Event(), release=threading.Event(),
                            opening=threading.Event(), admission=Queue(), observed=False,
                            open_requests=0)
    original_lock = host.lock
    original_close, original_write = socket.socket.close, wire.write
    original_complete, original_request = client._complete_control, client._request

    class ObservedLock:
        def __enter__(self):
            if threading.current_thread() is host.thread and state.closed.is_set() and not state.observed:
                state.observed = True
                acquired = original_lock.acquire(blocking=False)
                state.admission.put('acquired' if acquired else 'waiting')
                if acquired:
                    return self
            original_lock.acquire()
            return self

        def __exit__(self, *unused):
            original_lock.release()

    def write(connection, value):
        if (threading.current_thread().name == 'fc-chat-operation' and state.connection is None
                and value == dict(schema=1, id=1, ok=True, route='DIRECT')):
            state.connection, state.handler = connection, threading.current_thread()
        original_write(connection, value)

    def close(connection):
        original_close(connection)
        if connection is state.connection and threading.current_thread() is state.handler:
            state.closed.set()
            assert state.release.wait(15)

    def complete(*args):
        original_complete(*args)
        assert state.closed.wait(3)
        state.eof.set()

    def request(connection, action, *args, **kwargs):
        if action == 'open':
            state.open_requests += 1
            state.opening.set()
        return original_request(connection, action, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(host, 'lock', ObservedLock())
        patch.setattr(socket.socket, 'close', close)
        patch.setattr(wire, 'write', write)
        patch.setattr(client, '_complete_control', complete)
        patch.setattr(client, '_request', request)
        try:
            yield state
        finally:
            state.release.set()
            if state.handler is not None:
                state.handler.join(5)
                assert not state.handler.is_alive()


def test_direct_closed_probe_serializes_fourth_mailbox(authorized, monkeypatch):
    setup = authorized
    channels = [setup.direct.open_mailbox(time.monotonic() + 25, threading.Event()) for _ in range(3)]
    try:
        with ThreadPoolExecutor(1) as pool, held_closed_probe(setup, monkeypatch) as barrier:
            opened = pool.submit(setup.direct.open_mailbox, time.monotonic() + 10, threading.Event())
            assert barrier.closed.wait(3) and barrier.eof.wait(3) and barrier.opening.wait(3)
            assert barrier.connection.fileno() == -1 and barrier.handler.is_alive()
            assert len(setup.host.active) == 4 and len(setup.backing.active) == 3
            admission = barrier.admission.get(timeout=3)
            if admission == 'acquired':
                with pytest.raises(OSError) as failure:
                    opened.result(3)
                pytest.fail(f'DIRECT EOF observed with active4: dependent open rejected {failure.value!r}; '
                            f'native opens={len(setup.backing.opens)}, API sends={len(setup.api.calls)}')
            assert admission == 'waiting' and not opened.done()
            barrier.release.set()
            channels.append(opened.result(5))
            assert barrier.open_requests == 1
        assert len(setup.host.active) == 4 and len(setup.backing.active) == 4
        assert len(setup.backing.opens) == 4
        channels[-1].settimeout(2)
        setup.backing.opens[-1].peer.settimeout(2)
        channels[-1].sendall(b'upload')
        assert setup.backing.opens[-1].peer.recv(6) == b'upload'
        setup.backing.opens[-1].peer.sendall(b'download')
        assert channels[-1].recv(8) == b'download'
        with pytest.raises(OSError):
            setup.direct.open_mailbox(time.monotonic() + 1, threading.Event())
        assert len(setup.backing.opens) == 4 and len(setup.host.active) == 4
        channels.pop(0).close()
        first = setup.backing.opens[0]
        first.peer.shutdown(socket.SHUT_RDWR)
        first.peer.close()
        first.handler.join(5)
        assert not first.handler.is_alive() and first.closed.is_set()
        assert len(setup.host.active) == 3 and len(setup.backing.active) == 3
        channels.append(setup.direct.open_mailbox(time.monotonic() + 5, threading.Event()))
        assert len(setup.host.active) == 4 and len(setup.backing.active) == 4
        assert len(setup.backing.opens) == 5 and not setup.direct.connections
    finally:
        for channel in channels:
            channel.close()


@pytest.mark.parametrize('ending', ['cancel', 'client_close', 'deadline', 'host_close'])
def test_direct_closed_completion_interruptions_are_bounded(authorized, monkeypatch, ending):
    setup = authorized
    channels = [setup.direct.open_mailbox(time.monotonic() + 25, threading.Event()) for _ in range(3)]
    cancelled, stopped = threading.Event(), threading.Event()
    original_stop = setup.host.stop.set

    def stop():
        original_stop()
        stopped.set()

    monkeypatch.setattr(setup.host.stop, 'set', stop)
    try:
        with ThreadPoolExecutor(2) as pool, held_closed_probe(setup, monkeypatch) as barrier:
            deadline = time.monotonic() + (0.7 if ending == 'deadline' else 10)
            opened = pool.submit(setup.direct.open_mailbox, deadline, cancelled)
            assert barrier.closed.wait(3) and barrier.eof.wait(3) and barrier.opening.wait(3)
            assert barrier.admission.get(timeout=3) == 'waiting'
            assert len(setup.host.active) == 4 and not opened.done()
            closing = None
            if ending == 'cancel':
                cancelled.set()
            elif ending == 'client_close':
                setup.direct.close()
            elif ending == 'host_close':
                closing = pool.submit(setup.host.close)
                assert stopped.wait(3) and not closing.done()
                assert len(setup.host.active) == 4 and barrier.handler.is_alive()
                barrier.release.set()
            with pytest.raises(OSError) as failure:
                opened.result(6)
            if ending in ('cancel', 'client_close'):
                assert failure.value.code == 'CANCELLED'
            elif ending == 'deadline':
                assert isinstance(failure.value, TimeoutError) or getattr(failure.value, 'code', None) == 'DEADLINE'
            if closing is None:
                assert len(setup.host.active) == 4 and barrier.handler.is_alive()
                closing = pool.submit(setup.host.close)
                assert stopped.wait(3) and not closing.done()
                barrier.release.set()
            closing.result(5)
            assert barrier.open_requests == 1
        assert not setup.host.active and not setup.backing.active and not setup.direct.connections
        assert len(setup.backing.opens) == 3
        assert not setup.host.thread.is_alive()
    finally:
        for channel in channels:
            channel.close()
