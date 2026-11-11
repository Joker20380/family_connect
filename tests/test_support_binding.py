import hashlib
import hmac
import json

import pytest

from control.friends.support import bindings, configuration, enroll
from tests.test_friends_chat import registry, activated, request, SigningChat


def configured(registry, tmp_path, *, enrolled=True):
    sender_device, client_device = activated(registry), activated(registry)
    sender, client = SigningChat(), SigningChat()
    registered = []
    for device, chat in ((sender_device, sender), (client_device, client)):
        registered.append(registry.register(**request(registry, device, chat)))
    path = tmp_path / 'support.json'
    policy = dict(schema=1, sender_device=registered[0]['device'], sender_public=sender.profile()['public'], revision=1, enabled=True)
    path.write_text(json.dumps(policy))
    path.chmod(0o600)
    lease = registry.snapshot()
    node = dict(sequence=lease['sequence'], expires_at=lease['expires_at'], host='127.0.0.1', port=4243,
                public_key=SigningChat().profile()['public'])
    if enrolled:
        enroll(registry.access, path, registered[1]['device'], registered[1]['chat_public'], node['expires_at'])
    return path, policy, registered[1], node


def test_legacy_chat_is_not_a_verified_support_recipient(registry, tmp_path):
    path, policy, client, node = configured(registry, tmp_path, enrolled=False)
    def state():
        return next(row['state'] for row in bindings(registry.access, b'h' * 32, path, node)['devices']
                    if row['device'] == client['device'])
    assert state() == 'support_not_enrolled'
    configuration(registry.access, path, client['device'], client['chat_public'], node['expires_at'])
    assert state() == 'support_not_enrolled'
    enroll(registry.access, path, client['device'], client['chat_public'], node['expires_at'])
    assert state() == 'verified'
    with registry.access.db() as database:
        database.execute('UPDATE chat_bindings SET support_sender=? WHERE device=?', ('00' * 64, client['device']))
    assert state() == 'support_not_enrolled'
    with pytest.raises(ValueError):
        enroll(registry.access, path, client['device'], client['chat_public'], node['expires_at'])


def test_additive_enrollment_migration_preserves_legacy_identities(registry, tmp_path):
    configured(registry, tmp_path, enrolled=False)
    with registry.access.db() as database:
        before = [tuple(row) for row in database.execute('SELECT device,public FROM chat_bindings ORDER BY device')]
        database.execute('ALTER TABLE chat_bindings DROP COLUMN support_sender')
    registry.initialize()
    registry.initialize()
    with registry.access.db() as database:
        assert [tuple(row) for row in database.execute('SELECT device,public FROM chat_bindings ORDER BY device')] == before
        assert not any(row[0] for row in database.execute('SELECT support_sender FROM chat_bindings'))


def test_exact_registered_identities_and_full_inventory_hmac(registry, tmp_path):
    path, policy, client, node = configured(registry, tmp_path)
    role = configuration(registry.access, path, client['device'], client['chat_public'], node['expires_at'])
    assert role['sender_public'] == policy['sender_public']
    key = b'h' * 32
    snapshot = bindings(registry.access, key, path, node)
    expected = hmac.new(key, client['device'].encode(), hashlib.sha256).hexdigest()
    matched = next(row for row in snapshot['devices'] if row['pseudonym'] == expected)
    assert matched == dict(pseudonym=expected, device=client['device'], public=client['chat_public'], state='verified')
    assert 'sequence' not in snapshot['node']
    with pytest.raises(ValueError):
        configuration(registry.access, path, client['device'], policy['sender_public'], node['expires_at'])
    with pytest.raises(ValueError):
        bindings(registry.access, key, path, dict(node, sequence=node['sequence'] + 1))


def test_revoked_or_unregistered_official_sender_is_refused(registry, tmp_path):
    path, policy, client, node = configured(registry, tmp_path)
    with registry.access.db() as database:
        database.execute('UPDATE devices SET revoked=1 WHERE device=?', (policy['sender_device'],))
    for operation in (lambda: bindings(registry.access, b'h' * 32, path, node),
                      lambda: configuration(registry.access, path, client['device'], client['chat_public'], node['expires_at'])):
        with pytest.raises(ValueError):
            operation()


def test_disabled_support_never_changes_admission(registry, tmp_path):
    path, policy, client, node = configured(registry, tmp_path)
    before = registry.desired_members()
    path.write_text(json.dumps(dict(policy, enabled=False, revision=2)))
    assert not configuration(registry.access, path, client['device'], client['chat_public'], node['expires_at'])['enabled']
    assert all(row['state'] == 'revoked' for row in bindings(registry.access, b'h' * 32, path, node)['devices'])
    assert registry.desired_members() == before


def test_private_projection_export_uses_existing_key_and_ack(registry, tmp_path):
    from control.friends.support import publish
    path, policy, client, node = configured(registry, tmp_path)
    path.rename(tmp_path / 'chat-support.json')
    key = tmp_path / 'support-inventory-hmac.key'
    key.write_bytes(b'h' * 32)
    key.chmod(0o600)
    publish(registry.access, tmp_path, node)
    output = tmp_path / 'support-bindings.json'
    assert output.stat().st_mode & 0o077 == 0
    prior = output.read_bytes()
    document = json.loads(prior)
    assert document == bindings(registry.access, key.read_bytes(), tmp_path / 'chat-support.json', node)
    with pytest.raises(ValueError):
        publish(registry.access, tmp_path, dict(node, sequence=node['sequence'] + 1))
    assert output.read_bytes() == prior
    key.chmod(0o644)
    with pytest.raises(ValueError):
        publish(registry.access, tmp_path, node)
    assert output.read_bytes() == prior
