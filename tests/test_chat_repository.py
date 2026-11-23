from contextlib import contextmanager
import json

import pytest
import RNS

from control.friends.access import Rejected
from control.friends.chat import ChatAccess, ChatTransaction
from control.friends.chat_postgres import initialize_synthetic_chat
from control.friends import chat_service, chat_sync, support
from scripts.chat_postgres_rehearsal import activate, request, service_proof
from tests.test_enrollment_repository import access as enrollment_access, parallel, postgres_access
from tests.test_friends_chat import (
    chat, test_unactivated_device_cannot_request_challenge,
    test_challenge_cannot_bind_another_chat_key, test_device_proof_and_chat_signature_both_required,
    test_expiry_and_challenge_cap, test_same_chat_cannot_be_claimed_by_two_invited_devices,
)
from tests.test_chat_service_sender import (
    test_service_proof_idempotence_revocation_and_no_device_conversion,
    test_chat_only_support_sender_role_and_authoritative_bindings,
)
from tests.test_support_binding import (
    test_exact_registered_identities_and_full_inventory_hmac, test_disabled_support_never_changes_admission,
)


def initialize(access):
    registry = ChatAccess(access)
    if access.path is None:
        initialize_synthetic_chat(access.enrollment_repository)
    else:
        registry.initialize()
    return registry


@pytest.fixture
def registry(enrollment_access):
    return initialize(enrollment_access)


@pytest.fixture
def postgres_registry(postgres_access):
    return initialize(postgres_access)


def state(registry):
    with registry.access.read_enrollment() as transaction:
        return {table: [dict(row) for row in transaction.database.execute('SELECT * FROM ' + table + ' ORDER BY 1')]
                for table in ('devices', 'invites', 'challenges', 'chat_bindings', 'chat_challenges',
                              'chat_service_senders', 'chat_sequence')}


def configured(registry, folder, schema=2):
    sender_identity = RNS.Identity()
    sender_public = sender_identity.get_public_key().hex()
    document = dict(schema=schema, sender_public=sender_public, revision=1, enabled=True)
    if schema == 1:
        sender = activate(registry.access)
        registry.register(**request(registry, sender, sender_identity))
        document['sender_device'] = sender.reference
    else:
        chat_service.register(registry.access, **service_proof(sender_identity))
    device = activate(registry.access)
    client = registry.register(**request(registry, device, RNS.Identity()))
    path = folder / 'support.json'
    path.write_text(json.dumps(document))
    path.chmod(0o600)
    lease = registry.snapshot()
    node = dict(sequence=lease['sequence'], expires_at=lease['expires_at'], host='127.0.0.1', port=4243,
                public_key=sender_public)
    return path, document, client, node


@pytest.mark.parametrize('target', ['devices', 'invites'])
def test_revocation_rechecked_and_does_not_consume_pending_chat(registry, target):
    device = activate(registry.access)
    pending = request(registry, device, RNS.Identity())
    with registry.access.enrollment() as transaction:
        transaction.database.execute('UPDATE ' + target + ' SET revoked=1')
    before = state(registry)
    with pytest.raises(Rejected):
        registry.register(**pending)
    assert state(registry) == before


def test_one_use_concurrent_registration_and_idempotent_fresh_proof(registry):
    device, identity = activate(registry.access), RNS.Identity()
    pending = request(registry, device, identity)
    values = parallel(lambda index: registry.register(**pending), 8)
    assert len([value for value in values if value]) == 1
    assert registry.register(**request(registry, device, identity))['status'] == 'pending-node'
    assert len(state(registry)['chat_bindings']) == 1


def test_concurrent_chat_capacity_is_eight(registry):
    device, identity = activate(registry.access), RNS.Identity()
    values = parallel(lambda index: request(registry, device, identity), 12)
    assert len([value for value in values if value]) == 8
    assert len(state(registry)['chat_challenges']) == 8


def test_service_and_device_race_cannot_claim_same_identity(registry):
    identity = RNS.Identity()
    pending = request(registry, activate(registry.access), identity)
    value = service_proof(identity)

    def attempt(index):
        try:
            if index:
                chat_service.register(registry.access, **value)
            else:
                registry.register(**pending)
            return True
        except ValueError:
            return False

    assert sum(parallel(attempt, 2)) == 1
    rows = state(registry)
    assert len(rows['chat_bindings']) + len(rows['chat_service_senders']) == 1


@pytest.mark.parametrize('stage', ['bind', 'consume_challenge', 'add_service', 'revoke_service', 'advance_sequence', 'enroll_support'])
def test_write_failure_is_atomic(registry, tmp_path, monkeypatch, stage):
    path, policy, client, node = configured(registry, tmp_path)
    if stage in ('bind', 'consume_challenge'):
        pending = request(registry, activate(registry.access), RNS.Identity())
        attempt = lambda: registry.register(**pending)
    elif stage == 'add_service':
        value = service_proof(RNS.Identity())
        attempt = lambda: chat_service.register(registry.access, **value)
    elif stage == 'revoke_service':
        attempt = lambda: chat_service.revoke(registry.access, policy['sender_public'])
    elif stage == 'advance_sequence':
        attempt = registry.snapshot
    else:
        attempt = lambda: support.enroll(registry.access, path, client['device'], client['chat_public'], node['expires_at'])
    before = state(registry)
    original = getattr(ChatTransaction, stage)

    def fail_after(self, *args):
        original(self, *args)
        raise RuntimeError('synthetic write failure')

    with monkeypatch.context() as patch:
        patch.setattr(ChatTransaction, stage, fail_after)
        with pytest.raises(RuntimeError):
            attempt()
    assert state(registry) == before
    attempt()


@pytest.mark.parametrize('operation', ['register', 'service', 'revoke', 'snapshot', 'support'])
def test_lost_commit_ack_requires_readback_or_idempotent_retry(registry, tmp_path, monkeypatch, operation):
    path, policy, client, node = configured(registry, tmp_path)
    if operation == 'register':
        device, identity = activate(registry.access), RNS.Identity()
        pending = request(registry, device, identity)
        attempt = lambda: registry.register(**pending)
    elif operation == 'service':
        value = service_proof(RNS.Identity())
        attempt = lambda: chat_service.register(registry.access, **value)
    elif operation == 'revoke':
        attempt = lambda: chat_service.revoke(registry.access, policy['sender_public'])
    elif operation == 'snapshot':
        attempt = registry.snapshot
    else:
        attempt = lambda: support.enroll(registry.access, path, client['device'], client['chat_public'], node['expires_at'])
    original = registry.access.enrollment

    @contextmanager
    def lost_ack():
        with original() as transaction:
            yield transaction
        raise ConnectionError('synthetic commit ACK loss')

    with monkeypatch.context() as patch:
        patch.setattr(registry.access, 'enrollment', lost_ack)
        with pytest.raises(ConnectionError):
            attempt()
    committed = state(registry)
    if operation == 'register':
        with pytest.raises(Rejected):
            attempt()
        registry.register(**request(registry, device, identity))
        assert state(registry)['chat_bindings'] == committed['chat_bindings']
    elif operation == 'snapshot':
        assert committed['chat_sequence'][0]['value'] == node['sequence'] + 1
        assert registry.snapshot()['sequence'] == node['sequence'] + 2
    else:
        attempt()
        assert state(registry) == committed


@pytest.mark.parametrize('schema', [1, 2])
def test_support_uses_single_writer_transaction_and_rechecks_sender(registry, tmp_path, monkeypatch, schema):
    path, policy, client, node = configured(registry, tmp_path, schema)
    original = registry.access.enrollment
    calls = []

    @contextmanager
    def revoke_before_acquiring():
        calls.append(1)
        with original() as transaction:
            if schema == 1:
                transaction.revoke_device(policy['sender_device'])
            else:
                transaction.chat().revoke_service(policy['sender_public'])
        with original() as transaction:
            yield transaction

    with monkeypatch.context() as patch:
        patch.setattr(registry.access, 'enrollment', revoke_before_acquiring)
        with pytest.raises(ValueError):
            support.enroll(registry.access, path, client['device'], client['chat_public'], node['expires_at'])
    assert calls == [1]
    assert next(row for row in state(registry)['chat_bindings'] if row['device'] == client['device'])['support_sender'] is None


@pytest.mark.parametrize('schema', [1, 2])
def test_support_binding_is_immutable_and_inventory_does_not_enroll(registry, tmp_path, schema):
    path, policy, client, node = configured(registry, tmp_path, schema)
    before = state(registry)
    support.configuration(registry.access, path, client['device'], client['chat_public'], node['expires_at'])
    assert state(registry) == before
    def status():
        return next(row['state'] for row in support.bindings(registry.access, b'h' * 32, path, node)['devices']
                    if row['device'] == client['device'])
    assert status() == 'support_not_enrolled'
    support.enroll(registry.access, path, client['device'], client['chat_public'], node['expires_at'])
    assert status() == 'verified'
    other = service_proof(RNS.Identity())
    chat_service.register(registry.access, **other)
    path.write_text(json.dumps(dict(schema=2, sender_public=other['public'], revision=2, enabled=True)))
    with pytest.raises(ValueError):
        support.enroll(registry.access, path, client['device'], client['chat_public'], node['expires_at'])
    assert status() == 'support_not_enrolled'


@pytest.mark.parametrize('operation', ['register', 'support', 'bindings'])
def test_fresh_clock_after_transaction_wait(registry, tmp_path, monkeypatch, operation):
    path, policy, client, node = configured(registry, tmp_path)
    pending = request(registry, activate(registry.access), RNS.Identity())
    original = registry.access.read_enrollment if operation == 'bindings' else registry.access.enrollment
    before = state(registry)

    @contextmanager
    def delayed():
        with original() as transaction:
            registry.access.clock = lambda: node['expires_at']
            yield transaction

    monkeypatch.setattr(registry.access, 'read_enrollment' if operation == 'bindings' else 'enrollment', delayed)
    with pytest.raises(ValueError):
        if operation == 'register':
            registry.register(**pending)
        elif operation == 'support':
            support.enroll(registry.access, path, client['device'], client['chat_public'], node['expires_at'])
        else:
            support.bindings(registry.access, b'h' * 32, path, node)
    assert state(registry) == before


def test_concurrent_sequences_and_membership_capacity(registry):
    assert sorted(value['sequence'] for value in parallel(lambda index: registry.snapshot(), 12)) == list(range(1, 13))
    with registry.access.enrollment() as transaction:
        for index in range(550):
            transaction.chat().add_service(format(index, '0128x'))
    assert len(registry.snapshot()['public_keys']) == 550
    with registry.access.enrollment() as transaction:
        transaction.chat().add_service('f' * 128)
    before = state(registry)
    with pytest.raises(Rejected):
        registry.snapshot()
    assert state(registry) == before


def test_service_identity_never_allocates_device_or_transport(registry):
    value = service_proof(RNS.Identity())
    chat_service.register(registry.access, **value)
    assert registry.snapshot()['public_keys'] == [value['public']]
    rows = state(registry)
    assert not any(rows[table] for table in ('devices', 'invites', 'challenges', 'chat_bindings'))


@pytest.mark.parametrize('marker', ['missing', 'wrong'])
def test_postgres_missing_marker_refuses_all_operations(postgres_registry, tmp_path, marker):
    registry = postgres_registry
    path, policy, client, node = configured(registry, tmp_path)
    with registry.access.enrollment() as transaction:
        transaction.database.execute('DROP TABLE ha_chat_schema' if marker == 'missing' else
                                     "UPDATE ha_chat_schema SET purpose='wrong'")
    before = state(registry)
    import psycopg
    for attempt in (registry.snapshot, registry.desired_members,
                    lambda: support.enroll(registry.access, path, client['device'], client['chat_public'], node['expires_at']),
                    lambda: chat_service.revoke(registry.access, policy['sender_public'])):
        with pytest.raises((RuntimeError, psycopg.Error)):
            attempt()
    assert state(registry) == before


def test_postgres_file_and_mailbox_publishers_refuse_before_io(postgres_registry, tmp_path, monkeypatch):
    registry = postgres_registry
    before = state(registry)
    monkeypatch.setattr(chat_sync, 'ROOT', tmp_path / 'missing')
    for attempt in (lambda: chat_sync.synchronize(registry), lambda: chat_sync._synchronize(registry),
                    lambda: support.publish(registry.access, tmp_path / 'missing', {})):
        with pytest.raises(NotImplementedError, match='fenced authority'):
            attempt()
    assert state(registry) == before
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('stage', ['consume_challenge', 'enroll_support', 'advance_sequence'])
def test_postgres_backend_loss_rolls_back(postgres_registry, tmp_path, monkeypatch, stage):
    registry = postgres_registry
    path, policy, client, node = configured(registry, tmp_path)
    pending = request(registry, activate(registry.access), RNS.Identity())
    if stage == 'consume_challenge':
        attempt = lambda: registry.register(**pending)
    elif stage == 'enroll_support':
        attempt = lambda: support.enroll(registry.access, path, client['device'], client['chat_public'], node['expires_at'])
    else:
        attempt = registry.snapshot
    original = getattr(ChatTransaction, stage)
    before = state(registry)

    def terminate_after(self, *args):
        original(self, *args)
        with registry.access.enrollment_repository.connect() as killer:
            pid = self.database.execute('SELECT pg_backend_pid() AS pid').fetchone()['pid']
            assert killer.execute('SELECT pg_terminate_backend(%s,1000) AS stopped', (pid,)).fetchone()['stopped']
        self.database.execute('SELECT 1')

    import psycopg
    with monkeypatch.context() as patch:
        patch.setattr(ChatTransaction, stage, terminate_after)
        with pytest.raises(psycopg.OperationalError):
            attempt()
    assert state(registry) == before
    attempt()
