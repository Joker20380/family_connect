from contextlib import contextmanager
import socket
import threading
from types import SimpleNamespace

import pytest
import RNS

from messenger.mailbox import Mailbox, MailboxError
from messenger import routed
from messenger.routed import RoutedMailbox


@pytest.fixture
def cleanup_case(monkeypatch):
    calls = []
    stopped = threading.Event()
    source = SimpleNamespace(hash=b'c' * 16, direction=RNS.Destination.IN)
    mailbox = RoutedMailbox(SimpleNamespace(address=source.hash), source,
        RNS.Identity().get_public_key(), None, [('DIRECT', lambda *_: None)], threading.Lock())
    state = SimpleNamespace(failure=None, stalled=False, calls=calls, mailbox=mailbox)
    reader = threading.Thread(target=stopped.wait, name='synthetic-route-reader')
    reader.start()

    def stage(name):
        calls.append(name)
        if name == 'detach' and not state.stalled:
            stopped.set()
        if state.failure == name:
            raise OSError('synthetic private cleanup detail')

    state.socket = SimpleNamespace(close=lambda: stage('socket'))
    state.interface = SimpleNamespace(detach=lambda: stage('detach'))
    state.reader = reader
    monkeypatch.setattr(RNS.Transport, 'remove_interface', lambda _: stage('remove'))
    finish_reader = mailbox._finish_reader

    def finish(current):
        stage('join')
        finish_reader(current)

    monkeypatch.setattr(mailbox, '_finish_reader', finish)
    assert mailbox.session_lock.acquire(False)
    try:
        yield state
    finally:
        stopped.set()
        reader.join(2)
        assert not reader.is_alive()


@pytest.mark.parametrize('failure', [None, 'detach', 'socket', 'join', 'remove'])
def test_cleanup_attempts_every_resource_even_after_failure(cleanup_case, failure):
    state = cleanup_case
    state.failure = failure
    if failure is None:
        state.mailbox._disconnect(state.socket, state.interface, state.reader)
    else:
        with pytest.raises(MailboxError, match='^cleanup_incomplete$'):
            state.mailbox._disconnect(state.socket, state.interface, state.reader)
    assert state.calls == ['detach', 'socket', 'join', 'remove']
    assert state.mailbox.session_lock.acquire(False)
    state.mailbox.session_lock.release()


def test_live_reader_after_join_is_not_success(cleanup_case):
    state = cleanup_case
    state.stalled = True
    with pytest.raises(MailboxError, match='^cleanup_incomplete$'):
        state.mailbox._disconnect(state.socket, state.interface, state.reader)
    assert state.reader.is_alive()
    assert state.calls == ['detach', 'socket', 'join', 'remove']
    assert not state.mailbox.session_lock.locked()


def test_unstarted_reader_still_closes_socket_and_releases_session(cleanup_case):
    state = cleanup_case
    state.mailbox._disconnect(state.socket, None, threading.Thread(target=lambda: None))
    assert state.calls == ['socket']
    assert not state.mailbox.session_lock.locked()


@pytest.mark.parametrize('inner_failure', [None, 'timeout'])
def test_cleanup_failure_cannot_fall_back_or_return_success(cleanup_case, monkeypatch, inner_failure):
    state = cleanup_case
    state.failure = 'detach'
    state.mailbox.routes = [('DIRECT', None), ('EXISTING_EXIT', None)]

    @contextmanager
    def connection(*args, **kwargs):
        try:
            yield
        finally:
            state.mailbox._disconnect(state.socket, state.interface, state.reader)

    def exchange(*args, **kwargs):
        with connection():
            if inner_failure:
                raise MailboxError(inner_failure)
            return 'unexpected success'

    monkeypatch.setattr(Mailbox, 'exchange', exchange)
    with pytest.raises(MailboxError, match='^cleanup_incomplete$'):
        state.mailbox.exchange()
    assert state.mailbox.attempted == ['DIRECT']
    assert state.mailbox._selected is None
    assert not state.mailbox._route_lock.locked()
    assert not state.mailbox.session_lock.locked()


@pytest.mark.parametrize('failure', [None, 'registration', 'thread_start'])
def test_native_unix_interface_cleanup_and_partial_setup(chat_runtime, monkeypatch, failure):
    connection, peer = socket.socketpair()
    source = SimpleNamespace(hash=b'c' * 16, direction=RNS.Destination.IN)
    mailbox = RoutedMailbox(SimpleNamespace(address=source.hash), source,
        RNS.Identity().get_public_key(), chat_runtime, [('DIRECT', lambda *_: connection)], threading.Lock())
    mailbox._selected = mailbox.routes[0]
    interfaces = list(RNS.Transport.interfaces)
    readers = []

    @contextmanager
    def established(*args):
        yield

    class Reader(threading.Thread):
        def start(self):
            readers.append(self)
            if failure == 'thread_start':
                raise RuntimeError('synthetic startup failure')
            super().start()

    register = chat_runtime._add_interface

    def register_then_fail(interface):
        register(interface)
        raise RuntimeError('synthetic startup failure')

    monkeypatch.setattr(Mailbox, '_connection', established)
    monkeypatch.setattr(routed, 'threading', SimpleNamespace(Thread=Reader, Event=threading.Event))
    if failure == 'registration':
        monkeypatch.setattr(chat_runtime, '_add_interface', register_then_fail)
    try:
        if failure is None:
            with mailbox._connection(1, None):
                assert connection.fileno() >= 0 and mailbox.session_lock.locked()
        else:
            with pytest.raises(RuntimeError, match='synthetic startup failure'):
                with mailbox._connection(1, None):
                    pytest.fail('failed setup cannot yield a connection')
        assert connection.fileno() == -1
        assert list(RNS.Transport.interfaces) == interfaces
        assert not mailbox.session_lock.locked()
        assert all(not reader.is_alive() for reader in readers)
    finally:
        connection.close()
        peer.close()
