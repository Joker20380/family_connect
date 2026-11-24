import json
import socket
import time
import uuid

import pytest
import RNS

from messenger.local import LocalChat, LocalError
from messenger.support import accept
from messenger.tests.test_offline import Peer
from provisioning.chat_transport import SystemMailbox
from provisioning.support_worker import SupportOwner, SupportStore, SupportError


@pytest.fixture
def support(tmp_path):
    store = SupportStore(tmp_path / 'support', b's' * 32, create=True)
    public = store.chat_identity().get_public_key().hex()
    owner = SupportOwner(store, public)
    clients = [LocalChat(tmp_path / name, name.encode() * 32, create=True) for name in ('a', 'b')]
    for client in clients:
        client._chat.durable_delivery = True
    node = dict(host='127.0.0.1', port=4243, public_key=RNS.Identity().get_public_key().hex(), expires_at=int(time.time()) + 119)
    snapshot = dict(schema=1, sequence=1, expires_at=node['expires_at'], sender_public=public, node=node,
                    devices=[dict(pseudonym=str(index) * 64, device=str(index) * 32,
                                  public=client.profile()['public'], state='verified') for index, client in enumerate(clients, 1)])
    owner.update(snapshot)
    for index, client in enumerate(clients, 1):
        accept(client._store, dict(schema=1, device=str(index) * 32, chat_public=client.profile()['public'],
                                  sender_public=public, enabled=True, revision=1, expires_at=node['expires_at']),
               str(index) * 32, client.profile()['public'])
    yield owner, clients, snapshot
    for client in clients:
        client.close()
    store.close()


def queued(owner, client, text='synthetic private support'):
    request = dict(pseudonym='1' * 64, address=client.profile()['address'], request_id=str(uuid.uuid4()), actor='1', text=text)
    return request, owner.send(**request)['id']


def test_atomic_idempotency_and_encrypted_history(support, tmp_path):
    owner, clients, snapshot = support
    request, ident = queued(owner, clients[0])
    assert owner.send(**request)['id'] == ident
    with pytest.raises(SupportError, match='request_conflict'):
        owner.send(**dict(request, text='different'))
    assert len(owner.history('1' * 64)['messages']) == 1
    assert not owner.history('2' * 64)['messages']
    assert request['text'].encode() not in (tmp_path / 'support/history.sqlite').read_bytes()
    owner.store.close()
    with_store = SupportStore(tmp_path / 'support', b's' * 32, create=False)
    try:
        resumed = SupportOwner(with_store, snapshot['sender_public'])
        assert resumed.send(**request)['id'] == ident
        assert resumed.store.pending_outbox() == [ident]
    finally:
        with_store.close()


@pytest.mark.parametrize('change,code', [('revoked', 'revoked'), ('changed', 'identity_changed'), ('missing', 'unconfirmed')])
def test_queued_identity_never_redirected_or_unrevoked(support, change, code):
    owner, clients, snapshot = support
    queued(owner, clients[0])
    snapshot = json.loads(json.dumps(snapshot))
    snapshot['sequence'] += 1
    if change == 'revoked':
        snapshot['devices'][0]['state'] = 'revoked'
    elif change == 'changed':
        snapshot['devices'][0]['public'] = RNS.Identity().get_public_key().hex()
    else:
        snapshot['devices'].pop(0)
    owner.update(snapshot)
    assert owner.binding('1' * 64)['state'] == code
    assert owner.store.pending_outbox() == []
    with pytest.raises(SupportError, match=code):
        queued(owner, clients[0])
    if change != 'missing':
        snapshot['sequence'] += 1
        snapshot['devices'][0].update(public=clients[0].profile()['public'], state='verified')
        owner.update(snapshot)
        assert owner.binding('1' * 64)['state'] == code


def test_unverified_sender_and_revoked_role(support):
    owner, clients, snapshot = support
    assert clients[0].contacts()[0]['official_support'] is True
    forged = RNS.Identity()
    from messenger.codec import pack
    with pytest.raises(ValueError):
        clients[0]._chat.receive(pack(forged, bytes.fromhex(clients[0].profile()['public']), 'forgery'))
    clients[0].queue(owner.chat.address.hex(), 'queued reply')
    from messenger.support import role
    value = dict(role(clients[0]._store), enabled=False, revision=2)
    accept(clients[0]._store, value, '1' * 32, clients[0].profile()['public'])
    assert clients[0]._store.pending_outbox() == []
    clients[0].trust_contact(owner.chat.public.hex(), clients[0].contacts()[0]['fingerprint'])
    with pytest.raises(LocalError):
        clients[0].queue(owner.chat.address.hex(), 'must not bypass revocation')
    with pytest.raises(ValueError, match='revoked'):
        accept(clients[0]._store, dict(value, enabled=True, revision=3), '1' * 32, clients[0].profile()['public'])


def test_real_mailbox_two_recipients_and_storage_ack(support, tmp_path, chat_runtime):
    owner, clients, snapshot = support
    allowed = tmp_path / 'allowed.json'
    allowed.write_text(json.dumps([owner.chat.public.hex()] + [client.profile()['public'] for client in clients]))
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        port = probe.getsockname()[1]
    node = Peer('budget-node', tmp_path / 'node', port, script='closed_peer.py', extra=[str(allowed)])
    lease = dict(host='127.0.0.1', port=port, public_key=node.info['public'], expires_at=int(time.time()) + 119)
    carriers = [SystemMailbox(owner.chat, lease, chat_runtime)] + [SystemMailbox(client._chat, lease, chat_runtime) for client in clients]
    try:
        request, ident = queued(owner, clients[0])
        assert owner.history('1' * 64)['messages'][0]['status'] == 'queued'
        assert carriers[0].exchange(timeout=20).relayed == 1
        assert owner.history('1' * 64)['messages'][0]['status'] == 'relayed'
        assert carriers[2].exchange(timeout=20).received.stored == 0
        assert not clients[1].history(owner.chat.address.hex())['messages']
        assert carriers[1].exchange(timeout=20).received.stored == 1
        carriers[0].exchange(timeout=20)
        assert owner.history('1' * 64)['messages'][0]['status'] == 'recipient_stored'
        assert owner.send(**request)['id'] == ident
        assert len(clients[0].history(owner.chat.address.hex())['messages']) == 1
        reply = clients[0].queue(owner.chat.address.hex(), 'synthetic reply')
        carriers[1].exchange(timeout=20)
        carriers[0].exchange(timeout=20)
        history = owner.history('1' * 64)['messages']
        assert [message['id'] for message in history] == [ident, reply]
        assert history[1]['status'] == 'received'
        assert not owner.history('2' * 64)['messages']
    finally:
        for carrier in carriers:
            carrier.close()
        node.close()
