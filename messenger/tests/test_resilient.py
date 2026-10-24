import os
import time

import LXMF
import pytest
import RNS

from messenger import codec
from messenger.chat import Chat
from messenger.store import Store


@pytest.fixture
def peers(tmp_path, chat_runtime):
    result = [Chat(Store(tmp_path / name, os.urandom(32)), durable_delivery=True,
                   version=71) for name in ('alice', 'bob', 'publisher')]
    for sender in result:
        for recipient in result:
            if sender != recipient:
                sender.trust_contact(recipient.public)
    yield result
    for peer in result:
        peer.store.close()


def event(**changes):
    now = int(time.time())
    return dict(dict(event_id='ab' * 16, revision=1, kind='update', title='Test update',
                     body='Synthetic announcement; not an APK', created=now, expires=now + 3600,
                     platforms=['android'], min_version=1, max_version=99), **changes)


def packed(peer, ident):
    return bytes.fromhex(next(message['packed'] for message in peer.store.messages() if message['id'] == ident))


def test_pinned_publisher_not_contact_or_display_name(peers):
    alice, bob, publisher = peers
    notice = event()
    ident = publisher.queue_service(bob.address, notice)
    raw = packed(publisher, ident)
    with pytest.raises(ValueError, match='not pinned'):
        bob.receive(raw)
    bob.pin_service_publisher(publisher.public)
    assert bob.receive(raw)
    assert not bob.receive(raw)
    assert bob.store.inbox() == []
    saved = bob.store.service_events()
    assert len(saved) == 1 and saved[0]['event_id'] == notice['event_id']
    assert saved[0]['lxmf_id'] == ident and saved[0]['publisher'] == publisher.address.hex()
    assert not saved[0]['read'] and not saved[0]['notified']
    with pytest.raises(ValueError, match='not pinned'):
        bob.receive(packed(alice, alice.queue_service(bob.address, notice)))
    RNS.Identity.remember(None, publisher.address, publisher.public)
    assert LXMF.LXMessage.unpack_from_bytes(raw).signature_validated


def test_atomic_receipt_and_lost_ack_reuse_identical_bytes(peers):
    alice, bob, publisher = peers
    ident = alice.queue(bob.address, 'durable secret')
    old, raw = alice.store.begin_attempt(ident)
    assert bob.receive(raw)
    receipt = next(message for message in bob.store.messages() if message.get('kind') == 'stored')
    receipt_id = receipt['id']
    token, ack = bob.store.begin_attempt(receipt_id)
    bob.store.finish_attempt(receipt_id, token, delivered=False, relayed=True)
    assert not bob.receive(raw)
    assert packed(bob, receipt_id) == ack
    assert receipt_id in bob.store.pending_outbox()
    assert len(bob.store.inbox()) == 1
    assert not bob.store.inbox()[0]['read'] and not bob.store.inbox()[0]['notified']
    assert alice.receive(ack)
    assert not alice.receive(ack)
    assert not alice.store.finish_attempt(ident, old, delivered=False)
    assert alice.store.messages()[0]['status'] == 'recipient_stored'
    assert len(alice.store.messages()) == 1
    with pytest.raises(ValueError):
        alice.receive(codec.pack(publisher.identity, alice.public, '', codec.fields_for(dict(kind='stored', target=ident))))


def test_commit_failure_never_acknowledges(peers, monkeypatch):
    alice, bob, publisher = peers
    ident = alice.queue(bob.address, 'must remain queued')
    original = bob.store._put
    def fail_receipt(ident, value):
        if isinstance(value, dict) and value.get('kind') == 'stored':
            raise OSError('synthetic full disk')
        original(ident, value)
    monkeypatch.setattr(bob.store, '_put', fail_receipt)
    with pytest.raises(OSError):
        bob.receive(packed(alice, ident))
    assert bob.store.messages() == []
    assert alice.store.pending_outbox() == [ident]


def test_service_revision_expiry_applicability_and_tamper(peers):
    alice, bob, publisher = peers
    bob.pin_service_publisher(publisher.public)
    notice = event(revision=2)
    raw = packed(publisher, publisher.queue_service(bob.address, notice))
    assert bob.receive(raw)
    for changes in (dict(revision=1), dict(body='conflict'), dict(expires=int(time.time()) - 1, created=int(time.time()) - 10),
                    dict(min_version=100, max_version=101), dict(platforms=['linux'])):
        with pytest.raises(ValueError):
            bob.receive(packed(publisher, publisher.queue_service(bob.address, dict(notice, **changes))))
    altered = bytearray(raw)
    altered[32] ^= 1
    with pytest.raises(ValueError):
        bob.receive(bytes(altered))
    assert len(bob.store.service_events()) == 1
    assert bob.store.service_events()[0]['revision'] == 2


def test_old_notice_suppressed_without_claiming_notification_success(peers):
    alice, bob, publisher = peers
    bob.pin_service_publisher(publisher.public)
    notice = event(created=int(time.time()) - 90000)
    bob.receive(packed(publisher, publisher.queue_service(bob.address, notice)))
    saved = bob.store.service_events()[0]
    assert saved['notification_suppressed'] and not saved['notified'] and not saved['read']


def test_restart_stable_identity_queue_ciphertext_and_epoch(tmp_path, chat_runtime):
    key = os.urandom(32)
    store = Store(tmp_path / 'chat', key)
    alice = Chat(store, durable_delivery=True)
    recipient = RNS.Identity().get_public_key()
    alice.trust_contact(recipient)
    ident = alice.queue(codec.address(recipient), 'restart-private-text')
    old, raw = store.begin_attempt(ident)
    public = alice.public
    store.close()
    assert b'restart-private-text' not in (tmp_path / 'chat/history.sqlite').read_bytes()
    store = Store(tmp_path / 'chat', key, create=False)
    try:
        resumed = Chat(store, create_identity=False, durable_delivery=True)
        assert resumed.public == public and store.pending_outbox() == [ident]
        token, retry = store.begin_attempt(ident)
        assert retry == raw and token != old
        assert not store.finish_attempt(ident, old, delivered=True)
        assert store.finish_attempt(ident, token, delivered=False, relayed=True)
        assert store.pending_outbox() == []
    finally:
        store.close()


def test_quota_rolls_back_received_message_and_notice(peers, monkeypatch):
    alice, bob, publisher = peers
    bob.pin_service_publisher(publisher.public)
    for index in range(999):
        bob.store.add(dict(id=str(index), peer=alice.address.hex(), text='old', timestamp=1), b'x' * 100, outgoing=False)
    raw = packed(publisher, publisher.queue_service(bob.address, event()))
    with pytest.raises(ValueError, match='quota'):
        bob.receive(raw)
    assert len(bob.store.messages()) == 999 and bob.store.service_events() == []


def test_expiry_is_visible_not_deletion_and_high_water_persists(peers, monkeypatch):
    alice, bob, publisher = peers
    ident = alice.queue(bob.address, 'expiring')
    now = time.time()
    monkeypatch.setattr('messenger.store.time.time', lambda: now + 8 * 86400)
    assert alice.store.pending_outbox() == []
    assert alice.store.messages()[0]['status'] == 'expired'
    assert packed(alice, ident)
    with pytest.raises(ValueError):
        alice.store.begin_attempt(ident)
    monkeypatch.setattr('messenger.store.time.time', lambda: now)
    bob.pin_service_publisher(publisher.public)
    notice = event(revision=3)
    bob.receive(packed(publisher, publisher.queue_service(bob.address, notice)))
    monkeypatch.setattr('messenger.store.time.time', lambda: now + 7200)
    assert bob.store.service_events() == []
    updated_expiry = dict(notice, revision=2, expires=int(now) + 8000)
    with pytest.raises(ValueError, match='Stale'):
        bob.receive(packed(publisher, publisher.queue_service(bob.address, updated_expiry)))


def test_new_lxmf_id_same_event_revision_preserves_notification_flags(peers):
    alice, bob, publisher = peers
    bob.pin_service_publisher(publisher.public)
    notice = event()
    first = publisher.queue_service(bob.address, notice)
    bob.receive(packed(publisher, first))
    saved = bob.store.service_events()[0]
    bob.store.service_mark([saved['id']], 'notified')
    second = publisher.queue_service(bob.address, notice)
    assert second != first
    bob.receive(packed(publisher, second))
    assert len(bob.store.service_events()) == 1
    assert bob.store.service_events()[0]['notified']
    assert not bob.store.service_events()[0]['read']


@pytest.mark.parametrize('fields', [dict(fc=True, type='stored', target='aa'*32),
    dict(fc=1, type='stored', target='aa'*32, command='execute'),
    dict(fc=1, type='service', event={}), dict(fc=1, type='other')])
def test_delivery_fields_do_not_weaken_parser(fields):
    with pytest.raises(ValueError):
        codec.parse_fields({LXMF.FIELD_CUSTOM_DATA: fields}, '')
