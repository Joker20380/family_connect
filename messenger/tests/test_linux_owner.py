import json
import os
from pathlib import Path
import time
import sys
from types import SimpleNamespace

import pytest
import RNS

from device_identity.friends import load_friends_identity
from messenger.local import LocalError
from provisioning.chat_keyring import KeyringUnavailable
from provisioning.chat_owner import ChatOwner
from provisioning.chat_transport import SystemMailbox
from provisioning.friends import FriendsError


class MemoryKeyring:
    def __init__(self):
        self.keys = {}
        self.calls = []

    def key(self, device, *, create):
        self.calls.append((device, create))
        if device not in self.keys:
            if not create:
                raise KeyringUnavailable('keyring_unavailable')
            self.keys[device] = os.urandom(32)
        return self.keys[device]


@pytest.fixture
def owner_factory(tmp_path, chat_runtime):
    owners = []
    keyring = MemoryKeyring()
    def make(name='alice', device=None, vault=None):
        if device is None:
            device = load_friends_identity(tmp_path / (name + '-device'), create=True)
        friends = SimpleNamespace(_device=lambda create: device)
        owner = ChatOwner(tmp_path / name, friends, keyring=vault or keyring,
                          runtime_factory=lambda _: chat_runtime)
        owners.append(owner)
        return owner
    yield make
    for owner in owners:
        owner.close()


def test_explicit_creation_encrypted_queue_and_resume(owner_factory):
    alice, bob = owner_factory(), owner_factory('bob')
    with pytest.raises(LocalError, match='not_created'):
        alice.open()
    assert alice.keyring.calls == []
    profile = alice.open(create=True)
    peer = bob.open(create=True)
    alice.invoke('trust_contact', public=peer['public'], fingerprint=peer['fingerprint'])
    alice.invoke('rename_contact', address=peer['address'], name='Боб')
    message = alice.invoke('queue', address=peer['address'], text='PRIVATE-UTF8-Привет')
    assert alice.local._chat.durable_delivery is True
    key = alice.keyring.keys[alice.device.reference]
    alice.close()
    for path in alice.directory.rglob('*'):
        if path.is_file():
            assert key not in path.read_bytes()
            assert b'PRIVATE-UTF8' not in path.read_bytes()
    assert alice.open() == profile
    assert alice.invoke('contacts')[0]['name'] == 'Боб'
    history = alice.invoke('history', address=peer['address'], offset=0, limit=50)
    assert history['messages'][0]['id'] == message
    assert history['messages'][0]['status'] == 'queued'


@pytest.mark.parametrize('damage', ['key', 'database', 'binding', 'other_device', 'boolean_schema', 'oversize'])
def test_resume_failures_never_recreate_identity(owner_factory, damage):
    owner = owner_factory()
    profile = owner.open(create=True)
    owner.close()
    if damage == 'key':
        owner.keyring.keys.clear()
    elif damage == 'database':
        (owner.directory / 'store/history.sqlite').unlink()
    elif damage == 'binding':
        (owner.directory / 'account.json').write_text('{"schema":1,"schema":1}')
    elif damage == 'boolean_schema':
        (owner.directory / 'account.json').write_text(json.dumps({'schema': True, 'device': owner.device.reference}))
    elif damage == 'oversize':
        with (owner.directory / 'account.json').open('a') as target:
            target.write(' ' * 1025)
    else:
        other = owner_factory('other')
        owner.friends = other.friends
    with pytest.raises(LocalError):
        owner.open()
    with pytest.raises(LocalError):
        owner.open(create=True)
    assert len(profile['public']) == 128
    assert owner.local is None
    assert owner.lock is None


def test_one_owner_lock_and_no_key_replacement(owner_factory):
    first = owner_factory()
    profile = first.open(create=True)
    second = owner_factory(device=first.device, vault=first.keyring)
    calls = len(first.keyring.calls)
    with pytest.raises(LocalError, match='store_unavailable'):
        second.open()
    assert len(first.keyring.calls) == calls
    assert first.invoke('profile') == profile
    first.close()
    assert second.open() == profile


def test_commands_and_fingerprint_are_closed(owner_factory):
    owner, peer = owner_factory(), owner_factory('bob')
    owner.open(create=True)
    card = peer.open(create=True)
    with pytest.raises(LocalError, match='fingerprint_mismatch'):
        owner.invoke('trust_contact', public=card['public'], fingerprint='00' * 32)
    with pytest.raises(LocalError, match='unverified_contact'):
        owner.invoke('queue', address=card['address'], text='not trusted')
    for operation in ('open', '_chat', '__dict__', 'close', 'enrollment_proof'):
        with pytest.raises(LocalError, match='invalid_input'):
            owner.invoke(operation)
    assert owner.invoke('contacts') == []


def test_owner_exposes_only_validated_audio_and_requires_radio_confirmation(owner_factory):
    import base64
    owner, peer = owner_factory(), owner_factory('bob')
    owner.open(create=True)
    card = peer.open(create=True)
    owner.invoke('trust_contact', public=card['public'], fingerprint=card['fingerprint'])
    voice = (Path(__file__).parent / 'fixtures/voice-tone.opus').read_bytes()
    message = owner.invoke('queue_audio', address=card['address'], audio=base64.b64encode(voice).decode())
    assert base64.b64decode(owner.invoke('audio', message_id=message)['audio']) == voice
    with pytest.raises(LocalError):
        owner.invoke('queue_radio', address=card['address'], audio=base64.b64encode(bytes(8)).decode(),
                     mode=7, confirmed=False)
    radio = owner.invoke('queue_radio', address=card['address'], audio=base64.b64encode(bytes(8)).decode(),
                         mode=7, confirmed=True)
    assert owner.invoke('audio', message_id=radio)['mode'] == 7
    assert owner.invoke('voice_settings') == {'mode': 16, 'confirmed': []}
    owner.invoke('voice_mode', mode=7)
    owner.invoke('voice_confirm', address=card['address'])
    owner.close()
    owner.open()
    assert owner.invoke('voice_settings') == {'mode': 7, 'confirmed': [card['address']]}
    with pytest.raises(LocalError):
        owner.invoke('voice_mode', mode=True)
    with pytest.raises(LocalError):
        owner.invoke('voice_confirm', address='0' * 32)


def test_missing_computer_identity_does_not_touch_vault(tmp_path):
    def missing(create):
        assert create is False
        raise FileNotFoundError()
    vault = MemoryKeyring()
    owner = ChatOwner(tmp_path / 'chat', SimpleNamespace(_device=missing), keyring=vault)
    with pytest.raises(LocalError, match='identity_unavailable'):
        owner.open(create=True)
    assert not owner.directory.exists()
    assert vault.calls == []


def test_system_mailbox_expiry_and_private_route(owner_factory, chat_runtime):
    owner = owner_factory()
    owner.open(create=True)
    node = dict(host='127.0.0.1', port=12345, public_key=RNS.Identity().get_public_key().hex(),
                expires_at=int(time.time()) + 100)
    carrier = SystemMailbox(owner.local._chat, node, chat_runtime)
    try:
        assert carrier.routes[0][0] == 'SYSTEM'
        carrier.expires = time.time() - 1
        with pytest.raises(Exception, match='access_denied'):
            carrier.exchange()
    finally:
        carrier.close()
    assert carrier.source not in RNS.Transport.destinations


def test_authorization_denial_stops_old_lease_but_transient_refresh_keeps_it(owner_factory, monkeypatch):
    owner = owner_factory()
    owner.open(create=True)
    owner.carrier = SimpleNamespace(route='SYSTEM', close=lambda: None)
    owner.node = dict(expires_at=time.time() + 10)
    flags = []
    owner.local.delivery_update = lambda **values: flags.append(values)
    owner.local.delivery_state = lambda: dict(attached=True)
    owner.local.request_sync = lambda: None
    class HTTP:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
    owner.friends.http_factory = HTTP
    error = ['service_unavailable']
    class Client:
        def __init__(self, *args):
            pass
        def register_chat(self, local):
            raise FriendsError(error[0])
    monkeypatch.setattr('provisioning.chat_owner.FriendsClient', Client)
    owner.tick(online=True, visible=True)
    assert flags[-1]['online'] is True
    assert owner.node is not None
    error[0] = 'access_rejected'
    owner.next_enrollment = 0
    owner.tick(online=True, visible=True)
    assert owner.node is None
    assert flags[-1]['online'] is False


def test_locked_or_nontext_vault_entry_is_never_replaced(monkeypatch):
    from provisioning.chat_keyring import ChatKeyring
    class Cancel:
        def cancel(self):
            pass
    service = SimpleNamespace(lookup_sync=lambda *args: None, search_sync=lambda *args: [object()])
    def forbidden(*args):
        raise AssertionError('existing vault entry must not be overwritten')
    service.store_sync = forbidden
    secret = SimpleNamespace(Schema=SimpleNamespace(new=lambda *args: object()),
        SchemaFlags=SimpleNamespace(NONE=0), SchemaAttributeType=SimpleNamespace(STRING=0),
        Service=SimpleNamespace(__gtype__=object(), open_sync=lambda *args: service),
        ServiceFlags=SimpleNamespace(OPEN_SESSION=1), SearchFlags=SimpleNamespace(ALL=1))
    monkeypatch.setitem(sys.modules, 'gi', SimpleNamespace(require_version=lambda *args: None))
    monkeypatch.setitem(sys.modules, 'gi.repository', SimpleNamespace(Gio=SimpleNamespace(Cancellable=Cancel), Secret=secret))
    with pytest.raises(KeyringUnavailable, match='keyring_unavailable'):
        ChatKeyring().key('synthetic', create=True)


def test_background_preferences_preserve_identity_and_stop_hidden_delivery(owner_factory):
    owner = owner_factory()
    profile = owner.open(create=True)
    assert owner.invoke('delivery_settings') == dict(background=True, notifications=True)
    owner.invoke('background_delivery', enabled=False)
    owner.invoke('notification_settings', enabled=False)
    with pytest.raises(LocalError):
        owner.invoke('background_delivery', enabled=1)
    owner.close()
    assert owner.open() == profile
    assert owner.invoke('delivery_settings') == dict(background=False, notifications=False)
    owner.carrier = SimpleNamespace(route='SYSTEM', close=lambda: None)
    owner.node = dict(expires_at=time.time() + 100)
    flags, syncs = [], []
    owner.local.delivery_update = lambda **values: flags.append(values)
    owner.local.delivery_state = lambda: dict(attached=True, running=False, pending=False)
    owner.local.request_sync = lambda: syncs.append(True)
    owner.tick(online=True, visible=False, background=True)
    assert flags[-1] == dict(online=False, foreground=False)
    assert syncs == []
    owner.invoke('background_delivery', enabled=True)
    owner.tick(online=True, visible=False, background=True)
    assert flags[-1] == dict(online=True, foreground=True)
    assert len(syncs) == 1
    owner.tick(online=True, visible=False, background=True)
    assert len(syncs) == 1
    owner.tick(online=False, visible=False, background=True)
    assert flags[-1]['online'] is False


def test_service_events_refresh_bound_revision_fence_and_failure_preserves_cache(owner_factory):
    owner = owner_factory()
    owner.open(create=True)
    now = int(time.time())
    event = dict(id='a' * 32, kind='information', title='Original', body='Public body', author='Operator',
                 created=now - 10, expires=now + 100, platforms=['linux'], revision=1, updated=now - 10, editor='Operator')
    calls = []
    owner.friends.http_factory = lambda: None
    def fetch(factory):
        calls.append(True)
        return [dict(event)]
    owner.events_fetcher = fetch
    owner.next_enrollment = time.monotonic() + 1000
    owner.tick(online=True, visible=False, background=True)
    first = owner.invoke('notification_snapshot')['batches'][0]
    assert first['peer'] == 'service' and first['receipts'][0]['revision'] == 1
    owner.tick(online=True, visible=False, background=True)
    assert len(calls) == 1
    event.update(revision=2, title='Revised', updated=now)
    owner.next_events = 0
    owner.tick(online=True, visible=False, background=True)
    owner.invoke('notification_posted', peer='service', receipts=first['receipts'])
    assert owner.invoke('service_events')[0]['notified'] is False
    second = owner.invoke('notification_snapshot')['batches'][0]
    owner.invoke('notification_posted', peer='service', receipts=second['receipts'])
    assert owner.invoke('service_events')[0]['notified'] is True
    assert owner.invoke('notification_snapshot')['batches'] == []
    owner.events_fetcher = lambda _: (_ for _ in ()).throw(OSError('unavailable'))
    owner.next_events = 0
    assert owner.tick(online=True, visible=True)['events_unavailable']
    assert owner.invoke('service_events')[0]['title'] == 'Revised'
    owner.close()
    owner.open()
    assert owner.invoke('service_events')[0]['notified'] is True


def test_notification_command_cannot_mark_a_different_peer(owner_factory):
    owner = owner_factory()
    owner.open(create=True)
    for peer, receipts in [('shell://execute', []), ('service', [{'id': 'a', 'revision': True}]),
                           ('a' * 32, [{'id': 'a', 'revision': 1, 'extra': 'command'}])]:
        with pytest.raises(LocalError):
            owner.invoke('notification_posted', peer=peer, receipts=receipts)
    assert owner.invoke('notification_posted', peer='a' * 32, receipts=[]) is True


def test_private_edit_notification_ack_is_revision_fenced(owner_factory):
    alice, bob = owner_factory('notice-alice'), owner_factory('notice-bob')
    first, second = alice.open(create=True), bob.open(create=True)
    alice.invoke('trust_contact', public=second['public'], fingerprint=second['fingerprint'])
    bob.invoke('trust_contact', public=first['public'], fingerprint=first['fingerprint'])
    alice.invoke('inbox')
    message = bob.invoke('queue', address=first['address'], text='PRIVATE-INITIAL')
    alice.local._chat.receive(bob.local._store.begin_attempt(message)[1])
    original = alice.invoke('notification_snapshot')['batches'][0]
    assert 'PRIVATE' not in json.dumps(original)
    alice.invoke('notification_posted', peer='0' * 32, receipts=original['receipts'])
    assert not alice.invoke('inbox')[0]['notified']
    edit = bob.invoke('edit_message', address=first['address'], message_id=message, text='PRIVATE-EDIT')
    alice.local._chat.receive(bob.local._store.begin_attempt(edit)[1])
    alice.invoke('notification_posted', peer=second['address'], receipts=original['receipts'])
    assert not alice.invoke('inbox')[0]['notified']
    alice.invoke('visible_read', peer=second['address'], receipts=original['receipts'])
    assert not alice.invoke('inbox')[0]['read']
    revised = alice.invoke('notification_snapshot')['batches'][0]
    assert revised['receipts'] != original['receipts']
    alice.invoke('notification_posted', peer=second['address'], receipts=revised['receipts'])
    assert alice.invoke('inbox')[0]['notified']
    alice.invoke('visible_read', peer=second['address'], receipts=revised['receipts'])
    assert alice.invoke('inbox')[0]['read']
