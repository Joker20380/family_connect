import json
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
import RNS
from LXMF.LXMPeer import LXMPeer

from messenger.codec import address
from messenger.relay import ClosedRelay, PUT_PATH, Spool
from messenger.tests.test_control_ha_mailbox_fence import GENERATION, envelope, wait_for
from scripts import control_ha_legacy_support as admission
from scripts import control_ha_mailbox_fence as barrier
from scripts import control_ha_mailbox_links as lineage


@pytest.fixture
def mailbox(tmp_path, chat_runtime):
    support, peer = RNS.Identity(), RNS.Identity()
    spool = Spool(tmp_path / 'spool')
    relay = ClosedRelay(RNS.Identity(), spool, allowed_public=[support.get_public_key(), peer.get_public_key()])
    fence = lineage.SupportLinkFence(relay, support.get_public_key(), GENERATION, admission.binding(os.getpid()))
    try:
        yield relay, support, peer, fence
    finally:
        for name, function in fence.functions.items():
            function.__code__ = fence.originals[name].__code__
        fence.link_class.__init__.__code__ = fence.constructor.__code__
        for module, slot in ((fence.module, barrier.SLOT), (fence.link_module, lineage.SLOT)):
            if vars(module).get(slot) is fence:
                delattr(module, slot)
        RNS.Transport.deregister_destination(relay.destination)
        spool.close()


def native_link(relay, identity):
    link = RNS.Link(owner=relay.destination)
    link.destination = relay.destination
    link.link_id = link.hash = os.urandom(16)
    link.mdu = RNS.Link.MDU
    link.status = RNS.Link.ACTIVE
    link._Link__remote_identity = identity
    return link


def dispatch(link, data, monkeypatch, path=PUT_PATH):
    monkeypatch.setattr(RNS.Packet, 'send', lambda packet: None)
    link.handle_request(os.urandom(16), [0, RNS.Identity.truncated_hash(path.encode()), data])


@pytest.mark.parametrize('operation', ['put', 'purge'])
def test_reclosure_finishes_admitted_work_before_reporting_drain(mailbox, monkeypatch, operation):
    relay, support, peer, fence = mailbox
    incoming = relay.spool.put(peer.hash, envelope(support))
    fence.install()
    fence.open_after_local_drain(GENERATION)
    accepted, release = threading.Event(), threading.Event()
    original = fence.originals['respond']

    def held(*arguments):
        if arguments[4] is support:
            accepted.set()
            assert release.wait(5)
        return original(*arguments)

    monkeypatch.setitem(fence.originals, 'respond', held)
    link = native_link(relay, support)
    path = PUT_PATH if operation == 'put' else LXMPeer.MESSAGE_GET_PATH
    data = envelope(peer) if operation == 'put' else [None, [incoming]]
    with ThreadPoolExecutor(max_workers=1) as pool:
        active = pool.submit(dispatch, link, data, monkeypatch, path)
        try:
            assert accepted.wait(5)
            closed = fence.reclose(GENERATION)
            assert closed['new_link_admission'] == 'CLOSED'
            assert closed['accepted_target_work'] == 1
            assert closed['opening_invalidated'] and not closed['in_process_drained']
            dispatch(native_link(relay, support), envelope(peer), monkeypatch)
            dispatch(native_link(relay, peer), envelope(support), monkeypatch)
            assert relay.spool.stats()['count'] == 2
        finally:
            release.set()
        active.result(timeout=5)
    closed = fence.reclose(GENERATION)
    assert closed['in_process_drained'] and closed['accepted_target_work'] == 0
    assert relay.spool.stats()['count'] == (3 if operation == 'put' else 1)
    dispatch(link, envelope(peer), monkeypatch)
    assert relay.spool.stats()['count'] == (3 if operation == 'put' else 1)
    with pytest.raises(ValueError, match='ONE_OPEN_ONLY'):
        fence.open_after_local_drain(GENERATION)
    with pytest.raises(ValueError, match='OPEN_LINEAGE_REQUIRES_GUARD'):
        fence.abort(GENERATION)


def test_reclosure_before_open_permanently_invalidates_generation(mailbox):
    relay, support, peer, fence = mailbox
    fence.install()
    with pytest.raises(ValueError, match='GENERATION_MISMATCH'):
        fence.reclose('0' * 64)
    assert fence.reclose(GENERATION)['opening_invalidated']
    with pytest.raises(ValueError, match='ONE_OPEN_ONLY'):
        fence.open_after_local_drain(GENERATION)


@pytest.mark.parametrize('birth', ['before', 'held', 'unidentified'])
def test_old_links_never_gain_support_admission_after_local_open(mailbox, monkeypatch, birth):
    relay, support, peer, fence = mailbox
    if birth == 'before':
        link = native_link(relay, support)
    fence.install()
    if birth != 'before':
        link = native_link(relay, support if birth == 'held' else None)
    assert fence.open_after_local_drain(GENERATION)['new_link_admission'] == 'OPEN_LOCAL_ONLY'
    link._Link__remote_identity = support
    dispatch(link, envelope(peer), monkeypatch)
    assert relay.spool.stats()['count'] == 0
    assert fence.observe()['denied'] == 1
    dispatch(native_link(relay, peer), envelope(support), monkeypatch)
    assert relay.spool.stats()['count'] == 1


def test_fresh_native_link_put_and_purge_work_but_saved_direct_paths_remain_closed(mailbox, monkeypatch):
    relay, support, peer, fence = mailbox
    incoming = relay.spool.put(peer.hash, envelope(support))
    saved_put, saved_get, saved_response = relay.spool.put, relay.spool.get, relay.respond
    fence.install()
    observed = fence.open_after_local_drain(GENERATION)
    assert not any(observed[key] for key in ('cross_host_bound', 'restart_protected',
                                            'external_settlement_proven', 'activation_ready', 'capture_permitted'))
    assert support.get_public_key().hex() not in json.dumps(observed)
    fresh = native_link(relay, support)
    dispatch(fresh, envelope(peer), monkeypatch)
    dispatch(fresh, [None, [incoming]], monkeypatch, LXMPeer.MESSAGE_GET_PATH)
    assert relay.spool.stats()['count'] == 1
    with pytest.raises(barrier.AdmissionClosed):
        saved_put(support.hash, envelope(peer))
    with pytest.raises(barrier.AdmissionClosed):
        saved_get(address(support.get_public_key()), [None, None])
    assert saved_response(PUT_PATH, envelope(peer), None, support, 0) == ['unavailable']
    assert getattr(fence.context, 'link', None) is None
    with pytest.raises(ValueError, match='OPEN_LINEAGE_REQUIRES_GUARD'):
        fence.abort(GENERATION)
    with pytest.raises(ValueError, match='ONE_OPEN_ONLY'):
        fence.open_after_local_drain(GENERATION)


@pytest.mark.parametrize('operation', ['put', 'purge'])
def test_captured_native_dispatch_stays_fenced_after_close_and_open(mailbox, monkeypatch, operation):
    relay, support, peer, fence = mailbox
    incoming = relay.spool.put(peer.hash, envelope(support))
    link = native_link(relay, support)
    entered, release = threading.Event(), threading.Event()
    original_log = RNS.log

    def pause(message, *arguments, **keywords):
        if str(message).startswith('Handling request '):
            entered.set()
            assert release.wait(5)
        return original_log(message, *arguments, **keywords)

    monkeypatch.setattr(RNS, 'log', pause)
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(dispatch, link, envelope(peer) if operation == 'put' else [None, [incoming]],
                                 monkeypatch, PUT_PATH if operation == 'put' else LXMPeer.MESSAGE_GET_PATH)
        try:
            assert entered.wait(3)
            fence.install()
            fence.open_after_local_drain(GENERATION)
            link.status = RNS.Link.CLOSED
        finally:
            release.set()
        future.result(timeout=3)
    assert relay.spool.stats()['count'] == 1
    assert fence.observe()['denied'] == 1


@pytest.mark.parametrize('installed', [False, True])
def test_constructor_started_before_open_never_acquires_new_lineage(mailbox, monkeypatch, installed):
    relay, support, peer, fence = mailbox
    entered, release = threading.Event(), threading.Event()
    if installed:
        fence.install()

    def trace(frame, event, argument):
        if frame.f_code is fence.constructor.__code__ and event == 'call':
            entered.set()
            assert release.wait(5)
        return trace

    def create():
        sys.settrace(trace)
        try:
            return native_link(relay, support)
        finally:
            sys.settrace(None)

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(create)
        try:
            assert entered.wait(3)
            if not installed:
                fence.install()
            fence.open_after_local_drain(GENERATION)
        finally:
            release.set()
        old = future.result(timeout=3)
    dispatch(old, envelope(peer), monkeypatch)
    assert relay.spool.stats()['count'] == 0


def test_old_native_transaction_blocks_open_until_actual_commit(mailbox):
    relay, support, peer, fence = mailbox
    with ThreadPoolExecutor(max_workers=1) as executor:
        with relay.spool.lock:
            future = executor.submit(relay.spool.put, support.hash, envelope(peer))
            wait_for(lambda: fence.old_frames() == 1)
            fence.install()
            with pytest.raises(ValueError, match='OLD_WORK_NOT_DRAINED'):
                fence.open_after_local_drain(GENERATION)
            assert fence.epoch is None
        assert len(future.result(timeout=3)) == 32
    fence.open_after_local_drain(GENERATION)
    assert relay.spool.stats()['count'] == 1


def test_generation_drift_and_loaded_link_code_drift_refuse_open(mailbox, monkeypatch):
    relay, support, peer, fence = mailbox
    fence.install()
    with pytest.raises(ValueError, match='GENERATION_MISMATCH'):
        fence.open_after_local_drain('b' * 64)
    with monkeypatch.context() as patch:
        patch.setattr(RNS.Link, 'handle_request', lambda *arguments: None)
        with pytest.raises(ValueError, match='LINK_CODE_CHANGED'):
            fence.open_after_local_drain(GENERATION)
    assert fence.epoch is None
    assert fence.abort(GENERATION)
    assert fence.abort(GENERATION)
    assert lineage.SLOT not in vars(fence.link_module)


def test_fresh_link_keeps_native_membership_enforcement(mailbox, monkeypatch):
    relay, support, peer, fence = mailbox
    fence.install()
    fence.open_after_local_drain(GENERATION)
    fresh = native_link(relay, support)
    del relay.allowed[support.hash]
    dispatch(fresh, envelope(peer), monkeypatch)
    assert relay.spool.stats()['count'] == 0
    assert getattr(fence.context, 'link', None) is None


def test_native_callback_failure_clears_direct_write_context(mailbox, monkeypatch):
    relay, support, peer, fence = mailbox
    fence.install()
    with monkeypatch.context() as patch:
        patch.setattr(lineage, 'LINK_SHA256', '0' * 64)
        with pytest.raises(ValueError, match='LINK_SOURCE_PIN'):
            fence.open_after_local_drain(GENERATION)
    assert fence.epoch is None
    fence.open_after_local_drain(GENERATION)

    def fail(*arguments):
        raise OSError('SYNTHETIC_NATIVE_FAILURE')

    monkeypatch.setitem(fence.originals, 'respond', fail)
    with pytest.raises(OSError, match='SYNTHETIC_NATIVE_FAILURE'):
        dispatch(native_link(relay, support), envelope(peer), monkeypatch)
    assert getattr(fence.context, 'link', None) is None
    with pytest.raises(barrier.AdmissionClosed):
        relay.spool.put(support.hash, envelope(peer))


def test_abort_keeps_constructor_dispatcher_until_entered_wrapper_returns(mailbox):
    relay, support, peer, fence = mailbox
    entered, release = threading.Event(), threading.Event()
    fence.install()

    def trace(frame, event, argument):
        if frame.f_code is lineage.guarded_init.__code__ and event == 'call':
            entered.set()
            assert release.wait(5)
        return trace

    def create():
        sys.settrace(trace)
        try:
            return native_link(relay, support)
        finally:
            sys.settrace(None)

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(create)
        try:
            assert entered.wait(3)
            assert fence.abort(GENERATION) is False
            assert vars(fence.link_module)[lineage.SLOT] is fence
        finally:
            release.set()
        assert future.result(timeout=3).owner is relay.destination
    assert fence.abort(GENERATION)
    assert lineage.SLOT not in vars(fence.link_module)
