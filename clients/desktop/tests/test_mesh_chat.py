import base64
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import socket
import sys
import threading
import time

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'linux'))
import mesh_chat as chat
import mesh_ipc as ipc
import mesh_service as service


@pytest.fixture
def lane():
    parent, peer = socket.socketpair()
    instance = chat.ChatLane(parent)
    yield instance, peer
    instance.close()
    peer.close()
    instance.reader.join(5)
    assert not instance.reader.is_alive()
    assert instance.connection.fileno() == -1


def read(peer):
    return ipc.receive(peer.fileno(), chat.MAX_FRAME, time.monotonic() + 4)


def respond(peer, request, **fields):
    ipc.send(peer.fileno(), dict(schema=1, id=request['id'], ok=True, **fields), chat.MAX_FRAME, time.monotonic() + 4)


def test_out_of_order_mailbox_is_duplex(lane):
    instance, peer = lane
    with ThreadPoolExecutor(2) as pool:
        reading = pool.submit(instance.call, 'read', stream=1, size=4, budget_ms=1000)
        request = read(peer)
        writing = pool.submit(instance.call, 'write', stream=1, data=base64.b64encode(b'abcd').decode(), budget_ms=1000)
        other = read(peer)
        assert request['action'] == 'read' and other['action'] == 'write'
        respond(peer, other, count=4)
        assert writing.result(2)['count'] == 4
        assert not reading.done()
        respond(peer, request, count=4, data=base64.b64encode(b'abcd').decode())
        assert reading.result(2)['data'] == b'abcd'


def test_cancel_uses_reserved_lane_and_consumes_reply(lane):
    instance, peer = lane
    cancel = threading.Event()
    with ThreadPoolExecutor(1) as pool:
        pending = pool.submit(instance.call, 'open', lease=1, budget_ms=30000, cancel=cancel)
        request = read(peer)
        cancel.set()
        cancellation = read(peer)
        assert cancellation['action'] == 'cancel' and cancellation['target'] == request['id']
        respond(peer, cancellation)
        ipc.send(peer.fileno(), dict(schema=1, id=request['id'], ok=False, error='CANCELLED'), chat.MAX_FRAME, time.monotonic() + 4)
        with pytest.raises(chat.ChatError, match='CANCELLED'):
            pending.result(2)
    assert not instance.closed.is_set()
    assert not instance.pending


def test_cancel_after_open_releases_late_resource(lane):
    instance, peer = lane
    cancel = threading.Event()
    with ThreadPoolExecutor(1) as pool:
        pending = pool.submit(instance.call, 'open', lease=1, budget_ms=30000, cancel=cancel)
        request = read(peer)
        cancel.set()
        cancellation = read(peer)
        respond(peer, cancellation)
        respond(peer, request, stream=request['id'])
        closing = read(peer)
        assert closing['action'] == 'close' and closing['stream'] == request['id']
        respond(peer, closing)
        with pytest.raises(chat.ChatError, match='CANCELLED'):
            pending.result(2)


@pytest.mark.parametrize('change', [{'schema': True}, {'id': True}, {'ok': 1}, {'route': {}}, {'route': 'P1'},
                                   {'error': 'TOKEN=secret'}, {'extra': 'secret'}])
def test_malformed_response_closes_only_lane(lane, change):
    instance, peer = lane
    with ThreadPoolExecutor(1) as pool:
        pending = pool.submit(instance.call, 'route', lease=1)
        request = read(peer)
        reply = dict(schema=1, id=request['id'], ok=True, route='EXISTING_EXIT')
        reply.update(change)
        ipc.send(peer.fileno(), reply, chat.MAX_FRAME, time.monotonic() + 4)
        with pytest.raises(chat.ChatError, match='DENIED'):
            pending.result(2)
    assert instance.closed.is_set()


@pytest.mark.parametrize('reply', [dict(count=2, data='YQ=='), dict(count=True), dict(count=0, eof=1),
                                   dict(count=1, data='YR=='), dict(count=1, data='not base64')])
def test_mailbox_payload_limits(reply):
    with pytest.raises(ipc.ProtocolError):
        chat.checked_reply(dict(schema=1, id=1, ok=True, **reply), 1, 'read')


def test_jobs_bounded_with_independent_control_capacity(lane):
    instance, peer = lane
    with ThreadPoolExecutor(chat.MAX_JOBS + 1) as pool:
        pending = []
        for _ in range(chat.MAX_JOBS):
            pending.append(pool.submit(instance.call, 'request', lease=1, path='/friends/chat/challenge', budget_ms=30000))
            read(peer)
        with pytest.raises(chat.ChatError, match='BUSY_OR_UNAVAILABLE'):
            instance.call('open', lease=1, budget_ms=30000)
        control = pool.submit(instance.call, 'route', lease=1)
        request = read(peer)
        respond(peer, request, route='EXISTING_EXIT')
        assert control.result(2)['route'] == 'EXISTING_EXIT'
        instance.close()
        for operation in pending:
            with pytest.raises(chat.ChatError, match='UNAVAILABLE'):
                operation.result(2)


def test_private_native_lane_does_not_stop_vpn_control(monkeypatch):
    binary = os.environ.get('FC_TEST_MESH_WORKER')
    if not binary:
        pytest.skip('Set FC_TEST_MESH_WORKER to the current sealed Linux build')
    monkeypatch.setattr(service, 'WORKER', binary)
    worker = service.NativeWorker()
    try:
        assert worker.call('status')['state'] == 'DISCONNECTED'
        with pytest.raises(chat.ChatError, match='BUSY_OR_UNAVAILABLE'):
            worker.chat.call('open', lease=1, budget_ms=1000)
        assert worker.call('status')['ok'] is True
        worker.chat.close()
        worker.chat.reader.join(2)
        assert not worker.chat.reader.is_alive()
        assert worker.call('status')['ok'] is True
    finally:
        worker.close()
    assert worker.process.returncode == 0


def test_native_rejects_bad_chat_frame_without_killing_control(monkeypatch):
    binary = os.environ.get('FC_TEST_MESH_WORKER')
    if not binary:
        pytest.skip('Set FC_TEST_MESH_WORKER to the current sealed Linux build')
    monkeypatch.setattr(service, 'WORKER', binary)
    worker = service.NativeWorker()
    try:
        with pytest.raises(chat.ChatError, match='UNAVAILABLE'):
            worker.chat.call('route', lease=1, arbitrary_command='/bin/sh')
        assert worker.call('status')['ok'] is True
    finally:
        worker.close()
    assert worker.process.returncode == 0
