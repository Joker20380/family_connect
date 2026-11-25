from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import threading
import time

import pytest
import RNS
from LXMF.LXMPeer import LXMPeer

from messenger.codec import address, PUT_PATH
from messenger.relay import ClosedRelay, Spool
from scripts import control_ha_legacy_support as admission
from scripts import control_ha_mailbox_fence as barrier


GENERATION = 'a' * 64


def wait_for(predicate):
    deadline = time.monotonic() + 5
    while not predicate():
        assert time.monotonic() < deadline
        time.sleep(.005)


@pytest.fixture
def mailbox(tmp_path, chat_runtime):
    support, peer = RNS.Identity(), RNS.Identity()
    spool = Spool(tmp_path / 'spool')
    relay = ClosedRelay(RNS.Identity(), spool, allowed_public=[support.get_public_key(), peer.get_public_key()])
    fence = barrier.SupportFence(relay, support.get_public_key(), GENERATION, admission.binding(os.getpid()))
    try:
        yield relay, support, peer, fence
    finally:
        if fence.phase in ('HELD', 'ABORTING'):
            wait_for(lambda: fence.abort(GENERATION))
        RNS.Transport.deregister_destination(relay.destination)
        spool.close()


def envelope(recipient):
    return address(recipient.get_public_key()) + os.urandom(160)


def send(relay, sender, recipient):
    return relay.respond(PUT_PATH, envelope(recipient), b'q' * 16, sender, time.time())


def test_saved_bound_callbacks_and_methods_are_fenced_without_changing_handler_registry(mailbox):
    relay, support, peer, fence = mailbox
    handlers = {key: list(value) for key, value in relay.destination.request_handlers.items()}
    saved_callback = handlers[RNS.Identity.truncated_hash(PUT_PATH.encode())][1]
    saved_put, saved_get = relay.spool.put, relay.spool.get
    fence.install()
    assert saved_callback(PUT_PATH, envelope(peer), None, support, 0) == ['unavailable']
    with pytest.raises(barrier.AdmissionClosed):
        saved_put(support.hash, envelope(peer))
    with pytest.raises(barrier.AdmissionClosed):
        saved_get(address(support.get_public_key()), [None, None])
    assert relay.destination.request_handlers == handlers
    assert send(relay, peer, support)[0] == 'stored'
    result = fence.observe()
    assert result['in_process_drained'] and result['denied'] == 3
    assert not any(result[key] for key in ('cross_host_bound', 'restart_protected',
                                          'external_settlement_proven', 'activation_ready', 'capture_permitted'))
    assert support.get_public_key().hex() not in json.dumps(result)


def test_support_get_cannot_purge_but_unrelated_recipient_can_continue(mailbox):
    relay, support, peer, fence = mailbox
    incoming = relay.spool.put(peer.hash, envelope(support))
    outgoing = relay.spool.put(support.hash, envelope(peer))
    fence.install()
    assert relay.respond(LXMPeer.MESSAGE_GET_PATH, [None, [incoming]], None, support, 0) == LXMPeer.ERROR_NO_ACCESS
    assert relay.respond(LXMPeer.MESSAGE_GET_PATH, [None, [outgoing]], None, peer, 0) == []
    assert relay.spool.stats()['count'] == 1
    assert fence.abort(GENERATION)
    assert relay.spool.get(address(support.get_public_key()), [None, None]) == [incoming]


@pytest.mark.parametrize('operation', ['put', 'get'])
def test_preexisting_native_transaction_finishes_before_drain_without_timeout_cancellation(mailbox, operation):
    relay, support, peer, fence = mailbox
    incoming = relay.spool.put(peer.hash, envelope(support))
    callback, arguments = ((relay.spool.put, (support.hash, envelope(peer))) if operation == 'put' else
                           (relay.spool.get, (address(support.get_public_key()), [None, [incoming]])))
    with ThreadPoolExecutor(max_workers=1) as executor:
        with relay.spool.lock:
            future = executor.submit(callback, *arguments)
            wait_for(lambda: fence.old_frames() == 1)
            fence.install()
            observed = fence.drain(.03)
            assert not observed['in_process_drained'] and observed['old_target_frames'] == 1
            assert not future.done()
            with pytest.raises(barrier.AdmissionClosed):
                callback(*arguments)
        future.result(timeout=3)
        assert fence.drain(2)['in_process_drained']
    assert relay.spool.stats()['count'] == (2 if operation == 'put' else 0)


def test_old_respond_waiting_before_spool_entry_is_drained_and_cannot_write(mailbox):
    relay, support, peer, fence = mailbox
    captured = relay.respond
    with ThreadPoolExecutor(max_workers=1) as executor:
        with relay.rate_lock:
            future = executor.submit(captured, PUT_PATH, envelope(peer), None, support, 0)
            wait_for(lambda: fence.old_frames() == 1)
            fence.install()
            assert not fence.drain(.02)['in_process_drained']
        assert future.result(timeout=3) == ['unavailable']
    assert fence.drain(2)['in_process_drained']
    assert relay.spool.stats()['count'] == 0


def test_callback_not_yet_entered_is_refused_while_held_but_abort_is_not_a_handoff(mailbox):
    relay, support, peer, fence = mailbox
    captured = relay.respond
    fence.install()
    assert fence.drain(0)['in_process_drained']
    time.sleep(.03)
    assert captured(PUT_PATH, envelope(peer), None, support, 0) == ['unavailable']
    assert fence.abort(GENERATION)
    assert captured(PUT_PATH, envelope(peer), None, support, 0)[0] == 'stored'
    with pytest.raises(ValueError, match='FENCE_NOT_HELD'):
        fence.observe()


def test_native_rns_dispatch_already_captured_callback_cannot_write_even_after_link_close(mailbox, monkeypatch):
    relay, support, peer, fence = mailbox
    entered, release = threading.Event(), threading.Event()
    link = RNS.Link(owner=relay.destination)
    link.destination = relay.destination
    link.link_id = link.hash = b'l' * 16
    link.mdu = RNS.Link.MDU
    link.status = RNS.Link.ACTIVE
    link._Link__remote_identity = support
    original_log = RNS.log

    def pause_dispatch(message, *arguments, **keywords):
        if str(message).startswith('Handling request '):
            entered.set()
            assert release.wait(5)
        return original_log(message, *arguments, **keywords)

    responses = []
    monkeypatch.setattr(RNS, 'log', pause_dispatch)
    monkeypatch.setattr(RNS.Packet, 'send', lambda packet: responses.append(packet.data))
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(link.handle_request, b'q' * 16,
                                 [0, RNS.Identity.truncated_hash(PUT_PATH.encode()), envelope(peer)])
        try:
            assert entered.wait(3)
            fence.install()
            assert fence.observe()['in_process_drained']
            link.status = RNS.Link.CLOSED
        finally:
            release.set()
        future.result(timeout=3)
    assert responses and relay.spool.stats()['count'] == 0
    assert fence.observe()['denied'] == 1


def test_native_tcp_request_delayed_until_sender_disconnect_is_refused_while_held(mailbox):
    relay, support, peer, fence = mailbox
    received, release = threading.Event(), threading.Event()
    captured = relay.spool.put
    blob = envelope(peer)
    with socket.socket() as listener, ThreadPoolExecutor(max_workers=1) as executor:
        listener.bind(('127.0.0.1', 0))
        listener.listen(1)
        listener.settimeout(3)

        def consume():
            with listener.accept()[0] as connection:
                connection.settimeout(3)
                raw = connection.makefile('rb').read(len(blob))
                assert raw == blob and connection.recv(1) == b''
                received.set()
                assert release.wait(5)
                with pytest.raises(barrier.AdmissionClosed):
                    captured(support.hash, raw)

        future = executor.submit(consume)
        try:
            with socket.create_connection(listener.getsockname(), timeout=3) as connection:
                connection.sendall(blob)
            assert received.wait(3)
            fence.install()
            assert fence.observe()['in_process_drained']
        finally:
            release.set()
        future.result(timeout=3)
    assert relay.spool.stats()['count'] == 0


def test_other_spool_even_same_sender_is_not_fenced(mailbox, tmp_path):
    relay, support, peer, fence = mailbox
    other = Spool(tmp_path / 'unrelated')
    fence.install()
    try:
        assert len(other.put(support.hash, envelope(peer))) == 32
        assert other.stats()['count'] == 1
        assert relay.spool.stats()['count'] == 0
    finally:
        other.close()


def test_generation_replay_cannot_release_and_successful_abort_restores_exact_codes(mailbox):
    relay, support, peer, fence = mailbox
    originals = {name: function.__code__ for name, function in fence.functions.items()}
    fence.install()
    with pytest.raises(ValueError, match='GENERATION_MISMATCH'):
        fence.abort('b' * 64)
    assert send(relay, support, peer) == ['unavailable']
    assert fence.abort(GENERATION) and fence.abort(GENERATION)
    assert all(function.__code__ is originals[name] for name, function in fence.functions.items())
    assert not hasattr(fence.module, barrier.SLOT)
    with pytest.raises(ValueError, match='ONE_USE'):
        fence.install()


def test_abort_keeps_dispatcher_until_already_entered_guard_resumes(mailbox):
    relay, support, peer, fence = mailbox
    entered, release = threading.Event(), threading.Event()
    captured = relay.spool.put
    fence.install()

    def traced_call():
        def trace(frame, event, argument):
            if event == 'call' and frame.f_code is barrier.guarded_put.__code__:
                entered.set()
                assert release.wait(5)
            return trace
        sys.settrace(trace)
        try:
            return captured(support.hash, envelope(peer))
        finally:
            sys.settrace(None)

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(traced_call)
        try:
            assert entered.wait(3)
            assert not fence.abort(GENERATION)
            assert getattr(fence.module, barrier.SLOT) is fence
        finally:
            release.set()
        assert len(future.result(timeout=3)) == 32
    assert fence.abort(GENERATION)
    assert not hasattr(fence.module, barrier.SLOT)


@pytest.mark.parametrize('change', ['source', 'loaded', 'instance', 'process', 'generation'])
def test_prestate_mismatch_refuses_before_mutation(mailbox, monkeypatch, change):
    relay, support, peer, fence = mailbox
    process, generation = admission.binding(os.getpid()), GENERATION
    if change == 'source':
        monkeypatch.setattr(admission, 'read', lambda *args: b'wrong source')
    elif change == 'loaded':
        monkeypatch.setattr(Spool, 'put', lambda *args: None)
    elif change == 'instance':
        monkeypatch.setattr(relay.spool, 'get', lambda *args: None)
    elif change == 'process':
        process['start'] = '0'
    else:
        generation = '../wrong'
    with pytest.raises(ValueError):
        barrier.SupportFence(relay, support.get_public_key(), generation, process)
    assert not hasattr(fence.module, barrier.SLOT)


def test_drift_after_install_refuses_observation_and_does_not_silently_restore(mailbox):
    relay, support, peer, fence = mailbox
    fence.install()
    function = fence.functions['put']
    function.__code__ = fence.originals['put'].__code__
    try:
        with pytest.raises(ValueError, match='FENCE_CHANGED'):
            fence.observe()
        with pytest.raises(ValueError, match='FENCE_CHANGED'):
            fence.abort(GENERATION)
    finally:
        function.__code__ = barrier.guarded_put.__code__


@pytest.mark.parametrize('change', ['class', 'instance', 'registry'])
def test_drift_between_preparation_and_install_is_rejected_before_hooking(mailbox, monkeypatch, change):
    relay, support, peer, fence = mailbox
    if change == 'class':
        monkeypatch.setattr(Spool, 'put', lambda *args: None)
    elif change == 'instance':
        monkeypatch.setattr(relay.spool, 'get', lambda *args: None)
    else:
        monkeypatch.setitem(relay.destination.request_handlers, b'new', [PUT_PATH, relay.respond, 0, None, False])
    with pytest.raises(ValueError):
        fence.install()
    assert fence.phase == 'NEW' and not hasattr(fence.module, barrier.SLOT)


@pytest.mark.parametrize('seconds', [-1, True, float('inf'), float('nan'), 61])
def test_invalid_drain_interval_never_releases(mailbox, seconds):
    relay, support, peer, fence = mailbox
    fence.install()
    with pytest.raises(ValueError, match='DRAIN_INTERVAL'):
        fence.drain(seconds)
    assert send(relay, support, peer) == ['unavailable']


def request(root, command):
    with socket.socket(socket.AF_UNIX) as client:
        client.settimeout(4)
        client.connect(str(root / 'control.sock'))
        client.sendall(json.dumps(command).encode() + b'\n')
        return json.loads(client.makefile('rb').readline(8192))


def test_controller_sigkill_leaves_native_mailbox_fenced_and_independent_abort_recovers(tmp_path):
    fixture = Path(__file__).resolve().parents[2] / 'tests' / 'fixtures' / 'mailbox_fence.py'
    process = subprocess.Popen([sys.executable, str(fixture), str(tmp_path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    controller = None
    try:
        wait_for(lambda: (tmp_path / 'ready').exists() or process.poll() is not None)
        assert process.poll() is None, process.communicate(timeout=2)
        code = ('import json,socket,sys,time;from pathlib import Path\n'
                'root=Path(sys.argv[1]);client=socket.socket(socket.AF_UNIX);client.connect(str(root/"control.sock"))\n'
                'client.sendall(b\'{"action":"hold"}\\n\');response=json.loads(client.makefile("rb").readline())\n'
                'assert response["in_process_drained"];(root/"controller-ready").touch();time.sleep(30)\n')
        controller = subprocess.Popen([sys.executable, '-c', code, str(tmp_path)])
        wait_for(lambda: (tmp_path / 'controller-ready').exists() or controller.poll() is not None)
        assert controller.poll() is None
        controller.kill()
        controller.wait(timeout=3)
        time.sleep(.1)
        assert request(tmp_path, dict(action='put-support')) == ['unavailable']
        assert request(tmp_path, dict(action='put-peer')) == ['stored']
        observed = request(tmp_path, dict(action='status'))
        assert observed['in_process_drained'] and not observed['activation_ready']
        assert request(tmp_path, dict(action='abort', generation='b' * 64)) == dict(error='GENERATION_MISMATCH')
        assert request(tmp_path, dict(action='abort', generation=GENERATION)) == dict(restored=True)
        assert request(tmp_path, dict(action='put-support')) == ['stored']
        assert request(tmp_path, dict(action='stop')) == dict(count=2)
        assert process.wait(timeout=5) == 0
        reopened = Spool(tmp_path / 'spool')
        try:
            assert reopened.stats()['count'] == 2
        finally:
            reopened.close()
    finally:
        if controller is not None and controller.poll() is None:
            controller.kill()
            controller.wait(timeout=3)
        if process.poll() is None:
            process.kill()
            process.wait(timeout=3)
