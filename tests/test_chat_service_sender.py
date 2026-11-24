import json

import pytest

from control.friends.chat_service import message, register, revoke
from control.friends.support import bindings, enroll
from provisioning.support_identity import initialize
from messenger.store import Store
from tests.test_friends_chat import registry, activated, request, SigningChat


def grant(registry, identity):
    public = identity.profile()['public']
    register(registry.access, public, identity.identity.sign(message(public)).hex())
    return public


def test_service_membership_renews_without_device_invite_or_vpn_grant(registry):
    public = grant(registry, SigningChat())
    for now in (1000, 1081, 1162):
        registry.access.clock = lambda: now
        lease = registry.snapshot()
        assert lease['public_keys'] == [public]
        assert lease['expires_at'] == now + 100
    with registry.access.db() as database:
        for table in ('devices', 'invites', 'chat_bindings'):
            assert database.execute('SELECT COUNT(*) FROM ' + table).fetchone()[0] == 0


def test_service_proof_idempotence_revocation_and_no_device_conversion(registry):
    identity = SigningChat()
    public = grant(registry, identity)
    assert grant(registry, identity) == public
    with pytest.raises(ValueError):
        register(registry.access, public, '00' * 64)
    revoke(registry.access, public)
    assert registry.snapshot()['public_keys'] == []
    with pytest.raises(ValueError):
        grant(registry, identity)
    client = SigningChat()
    registry.register(**request(registry, activated(registry), client))
    with pytest.raises(ValueError):
        grant(registry, client)
    with pytest.raises(ValueError):
        registry.register(**request(registry, activated(registry), identity))


def test_chat_only_support_sender_role_and_authoritative_bindings(registry, tmp_path):
    public = grant(registry, SigningChat())
    client = registry.register(**request(registry, activated(registry), SigningChat()))
    path = tmp_path / 'support.json'
    path.write_text(json.dumps(dict(schema=2, sender_public=public, revision=1, enabled=True)))
    path.chmod(0o600)
    lease = registry.snapshot()
    node = dict(sequence=lease['sequence'], expires_at=lease['expires_at'], host='127.0.0.1', port=4243,
                public_key=SigningChat().profile()['public'])
    role = enroll(registry.access, path, client['device'], client['chat_public'], node['expires_at'])
    assert role['schema'] == 1 and role['sender_public'] == public
    snapshot = bindings(registry.access, b'h' * 32, path, node)
    assert len(snapshot['devices']) == 1
    assert snapshot['devices'][0]['state'] == 'verified'
    revoke(registry.access, public)
    with pytest.raises(ValueError):
        enroll(registry.access, path, client['device'], client['chat_public'], node['expires_at'])
    with pytest.raises(ValueError):
        bindings(registry.access, b'h' * 32, path, node)


def test_one_time_identity_initialization_preserves_key_and_encrypted_history(registry, tmp_path):
    directory = tmp_path / 'official'
    initialize(directory)
    proof = json.loads((directory / 'registration.json').read_text())
    register(registry.access, **proof)
    before = {path.name: path.read_bytes() for path in directory.iterdir() if path.is_file()}
    with pytest.raises(FileExistsError):
        initialize(directory)
    assert before == {path.name: path.read_bytes() for path in directory.iterdir() if path.is_file()}
    store = Store(directory / 'history', (directory / 'store.key').read_bytes(), create=False)
    try:
        assert store.chat_identity(create=False).get_public_key().hex() == proof['public']
    finally:
        store.close()
    assert all(path.stat().st_mode & 0o077 == 0 for path in directory.iterdir())
