import os
import threading
import time
from types import SimpleNamespace

import pytest
import RNS

from messenger.chat import Chat
from messenger.delivery import DeliveryController
from messenger.local import LocalChat, LocalError, contact_card
from messenger.mailbox import ExchangeResult, Mailbox, MailboxError, SyncResult
from messenger.store import Store


def wait_for(predicate):
    end = time.monotonic() + 3
    while time.monotonic() < end:
        if predicate(): return
        time.sleep(.005)
    assert predicate()


def result(pending=0, more=False):
    return ExchangeResult(SyncResult(0, 0, 0, 0), 0, pending, more)


class Exchange:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
    def exchange(self, *, timeout, cancel):
        self.calls.append(time.monotonic())
        value = self.responses.pop(0)
        if isinstance(value, Exception): raise value
        return value


def test_batches_drain_then_idle_without_polling():
    mailbox = Exchange([result(5), result(1), result()])
    controller = DeliveryController(mailbox, cooldown=.02, max_backoff=.08)
    try:
        controller.request_sync(); controller.update(online=True)
        time.sleep(.04); assert not mailbox.calls
        controller.update(foreground=True)
        wait_for(lambda: len(mailbox.calls) == 3 and not controller.snapshot()['running'])
        for _ in range(20): controller.update(online=True, foreground=True)
        time.sleep(.1); assert len(mailbox.calls) == 3
        assert not controller.snapshot()['pending'] and controller.snapshot()['error'] is None
    finally: assert controller.close()


@pytest.mark.parametrize('code', ['rate_limited', 'busy'])
def test_transient_retries_are_finite_and_preserve_backoff(code):
    mailbox = Exchange([MailboxError(code)] * 3)
    controller = DeliveryController(mailbox, cooldown=.04, max_backoff=.2, max_retries=2)
    try:
        controller.update(online=True, foreground=True)
        wait_for(lambda: controller.snapshot()['failures'] == 3)
        time.sleep(.2); assert len(mailbox.calls) == 3
        assert mailbox.calls[1] - mailbox.calls[0] >= .035
        assert mailbox.calls[2] - mailbox.calls[1] >= .075
        assert not controller.snapshot()['pending']
        assert controller.snapshot()['error'] == code
    finally: assert controller.close()


@pytest.mark.parametrize('failure,code', [(MailboxError('access_denied'), 'access_denied'),
    (MailboxError('invalid_response'), 'invalid_response'), (OSError('private text/path'), 'exchange_failed')])
def test_permanent_and_storage_failures_wait_for_an_event(failure, code):
    mailbox = Exchange([failure, result()])
    controller = DeliveryController(mailbox, cooldown=.02, max_backoff=.08)
    try:
        controller.update(online=True, foreground=True)
        wait_for(lambda: controller.snapshot()['error'] is not None)
        time.sleep(.1); assert len(mailbox.calls) == 1
        assert controller.snapshot()['error'] == code
        controller.request_sync()
        wait_for(lambda: controller.snapshot()['result'] is not None)
        assert controller.snapshot()['failures'] == 0
    finally: assert controller.close()


def test_lifecycle_events_do_not_reset_the_backoff():
    mailbox = Exchange([MailboxError('timeout'), result()])
    controller = DeliveryController(mailbox, cooldown=.15, max_backoff=.3)
    try:
        controller.update(online=True, foreground=True)
        wait_for(lambda: controller.snapshot()['error'] == 'timeout')
        for _ in range(20):
            controller.update(online=False); controller.update(online=True); controller.request_sync()
        time.sleep(.04); assert len(mailbox.calls) == 1
        wait_for(lambda: len(mailbox.calls) == 2)
        assert mailbox.calls[1] - mailbox.calls[0] >= .14
    finally: assert controller.close()


def test_background_cancels_running_exchange_and_suppresses_late_result():
    started, release = threading.Event(), threading.Event()
    cancellations = []
    class Slow:
        def exchange(self, *, timeout, cancel):
            cancellations.append(cancel); started.set(); release.wait(2)
            return result(pending=10)
    controller = DeliveryController(Slow(), cooldown=.02, max_backoff=.08)
    try:
        controller.update(online=True, foreground=True); assert started.wait(1)
        controller.update(foreground=False)
        assert cancellations[0].is_set()
        release.set(); wait_for(lambda: not controller.snapshot()['running'])
        assert controller.snapshot()['result'] is None
        time.sleep(.06); assert len(cancellations) == 1
    finally: release.set(); assert controller.close()


def test_close_timeout_retains_store_until_worker_finishes(tmp_path, monkeypatch, chat_runtime):
    key = os.urandom(32)
    local = LocalChat(tmp_path/'chat', key, create=True)
    profile = local.profile()
    source = SimpleNamespace(hash=bytes.fromhex(profile['address']), direction=RNS.Destination.IN)
    started, release = threading.Event(), threading.Event()
    def slow(self, **kwargs):
        started.set(); release.wait(2)
        assert self.chat.store.contacts() == {}
        return result()
    monkeypatch.setattr(Mailbox, 'exchange', slow)
    local.attach_delivery(source, RNS.Identity().get_public_key(), cooldown=.02, max_backoff=.08)
    try:
        local.delivery_update(online=True, foreground=True); assert started.wait(1)
        with pytest.raises(LocalError, match='^close_pending$'): local.close(timeout=0)
        with pytest.raises(LocalError, match='^closing$'): local.profile()
        with pytest.raises(LocalError, match='^store_unavailable$'): LocalChat(tmp_path/'chat', key, create=False)
    finally:
        release.set(); local.close()
    resumed = LocalChat(tmp_path/'chat', key, create=False)
    try: assert resumed.profile() == profile
    finally: resumed.close()


def test_local_committed_queue_wakes_attached_worker(tmp_path, monkeypatch, chat_runtime):
    local = LocalChat(tmp_path/'chat', os.urandom(32), create=True)
    profile = local.profile()
    peer = contact_card(RNS.Identity().get_public_key().hex())
    local.trust_contact(peer['public'], peer['fingerprint'])
    source = SimpleNamespace(hash=bytes.fromhex(profile['address']), direction=RNS.Destination.IN)
    observed = []
    def exchange(mailbox, **kwargs):
        ids = mailbox.chat.store.pending_outbox(); observed.append(ids)
        for ident in ids:
            token, _ = mailbox.chat.store.begin_attempt(ident)
            mailbox.chat.store.finish_attempt(ident, token, delivered=False, relayed=True)
        return ExchangeResult(SyncResult(0,0,0,0), len(ids), 0, False)
    monkeypatch.setattr(Mailbox, 'exchange', exchange)
    try:
        local.attach_delivery(source, RNS.Identity().get_public_key(), cooldown=.02, max_backoff=.08)
        local.delivery_update(online=True, foreground=True)
        wait_for(lambda: observed == [[]])
        ident = local.queue(peer['address'], 'new work')
        wait_for(lambda: local.delivery_state()['result'] is not None and
                 local.delivery_state()['result']['relayed'] == 1)
        assert local.history(peer['address'])['messages'][0]['status'] == 'relayed'
        state = local.delivery_state()
        assert state['attached'] and state['result']['relayed'] == 1
    finally: local.close()


def test_pending_selection_skips_received_relayed_and_current_attempt(tmp_path, chat_runtime):
    key = os.urandom(32); store = Store(tmp_path/'chat', key); chat = Chat(store)
    public = RNS.Identity().get_public_key(); peer = chat.trust_contact(public)
    ids = [chat.queue(peer, str(i)) for i in range(3)]
    token, raw = store.begin_attempt(ids[0])
    second, _ = store.begin_attempt(ids[1]); store.finish_attempt(ids[1], second, delivered=False, relayed=True)
    assert store.pending_outbox() == [ids[2]]
    store.close()
    store = Store(tmp_path/'chat', key, create=False)
    try:
        assert store.pending_outbox() == [ids[0], ids[2]]
        retry, again = store.begin_attempt(ids[0]); assert raw == again and retry != token
        assert not store.finish_attempt(ids[0], token, delivered=True)
    finally: store.close()


@pytest.mark.parametrize('limits', [{'cooldown':0}, {'timeout':31}, {'max_retries':True},
    {'max_retries':6}, {'max_backoff':1}, {'timeout':float('nan')}])
def test_invalid_limits(limits):
    with pytest.raises(ValueError): DeliveryController(Exchange([]), **limits)
