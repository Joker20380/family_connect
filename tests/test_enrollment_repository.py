import base64
from concurrent.futures import ThreadPoolExecutor
import hashlib
import os
from pathlib import Path
import threading
import time
import uuid

import pytest

from control.friends.access import Access, Rejected, SQLiteEnrollment
from control.friends.enrollment_postgres import PostgresEnrollment, PostgresEnrollmentTransaction
from device_identity.device import DeviceIdentity
from test_friends_access import (
    proof,
    test_single_use_invite_and_perpetual_device,
    test_parallel_claims_grant_only_one_device,
    test_signature_purpose_and_revocation,
    test_operator_revocation_is_monotonic_and_rejects_pending_proof,
    test_shorter_challenge_expires_at_server_deadline,
    test_device_status_unknown_registered_and_invite_revoked as sqlite_status_contract,
    test_device_status_does_not_consume_invite_and_rejects_replay,
)


def postgres_store():
    if not os.environ.get('FC_HA_PG_PORT'):
        pytest.skip('Run scripts.enrollment_postgres_rehearsal for real PostgreSQL contracts')
    repository = PostgresEnrollment(port=int(os.environ['FC_HA_PG_PORT']),
        schema='ha_enrollment_' + uuid.uuid4().hex,
        password=Path(os.environ['FC_HA_PG_PASSWORD_FILE']).read_text().strip())
    repository.initialize_synthetic()
    return Access(None, clock=lambda: 1000, enrollment_repository=repository)


@pytest.fixture(params=['sqlite', 'postgres'])
def access(request, tmp_path):
    if request.param == 'postgres':
        return postgres_store()
    result = Access(tmp_path / 'registry.sqlite', clock=lambda: 1000)
    result.initialize()
    return result


@pytest.fixture
def postgres_access():
    return postgres_store()


def peer(access):
    return Access(access.path, clock=access.clock, enrollment_repository=access.enrollment_repository)


def parallel(attempt, count):
    barrier = threading.Barrier(count)

    def call(index):
        barrier.wait(timeout=10)
        try:
            return attempt(index)
        except Rejected:
            return None

    with ThreadPoolExecutor(count) as pool:
        return list(pool.map(call, range(count)))


def test_one_proof_consumed_by_only_one_api(access):
    device = DeviceIdentity.generate()
    pending = proof(access, device, access.invite())
    results = parallel(lambda index: peer(access).complete(pending, 'activate'), 8)
    assert sum(result is not None for result in results) == 1
    with access.enrollment() as transaction:
        assert transaction.challenge(hashlib.sha256(pending['challenge'].encode()).hexdigest())['used'] == 1
        assert transaction.device(device.reference) is not None


def test_challenge_limit_is_atomic_across_apis(access):
    device = DeviceIdentity.generate()
    public = (base64.b64encode(device.public_identity).decode()
              if isinstance(device.public_identity, bytes) else device.public_identity)
    results = parallel(lambda index: peer(access).challenge(public, device.wireguard_public_key, 'status'), 16)
    assert sum(result is not None for result in results) == 8
    with access.enrollment() as transaction:
        assert transaction.pending_challenges(device.reference) == 8


def test_status_is_single_use_across_apis(access):
    device = DeviceIdentity.generate()
    pending = proof(access, device, purpose='status')
    results = parallel(lambda index: peer(access).status(pending), 8)
    assert [result for result in results if result is not None] == [dict(
        device=device.reference, registered=False, revoked=False, active=False)]


def test_failed_support_allocation_rolls_back_entire_activation(access, monkeypatch):
    device = DeviceIdentity.generate()
    invitation = access.invite()
    pending = proof(access, device, invitation)
    adapter = PostgresEnrollmentTransaction if access.path is None else SQLiteEnrollment

    def fail(transaction, device):
        raise RuntimeError('synthetic allocation failure')

    with monkeypatch.context() as patch:
        patch.setattr(adapter, 'registered', fail)
        with pytest.raises(RuntimeError, match='synthetic allocation failure'):
            access.complete(pending, 'activate')
    with access.enrollment() as transaction:
        assert transaction.device(device.reference) is None
        assert transaction.invitation(access.code_hash(invitation))['device'] is None
        assert transaction.challenge(hashlib.sha256(pending['challenge'].encode()).hexdigest())['used'] == 0
    assert access.complete(pending, 'activate')['device'] == device.reference


def test_support_collision_keeps_transaction_usable(access, monkeypatch):
    first, second = DeviceIdentity.generate(), DeviceIdentity.generate()
    with monkeypatch.context() as patch:
        patch.setattr('secrets.choice', lambda alphabet: '2')
        access.complete(proof(access, first, access.invite()), 'activate')
    choices = iter('2' * 8 + '3' * 8)
    with monkeypatch.context() as patch:
        patch.setattr('secrets.choice', lambda alphabet: next(choices))
        access.complete(proof(access, second, access.invite()), 'activate')
    with access.enrollment() as transaction:
        assert transaction.registered(first.reference) == 'FC-2222-2222'
        assert transaction.registered(second.reference) == 'FC-3333-3333'


def test_lost_activation_reply_requires_new_status_proof(access):
    device = DeviceIdentity.generate()
    invitation = access.invite()
    pending = proof(access, device, invitation)
    original = access.complete(pending, 'activate')
    with pytest.raises(Rejected):
        peer(access).complete(pending, 'activate')
    assert peer(access).status(proof(peer(access), device, purpose='status'))['active'] is True
    assert peer(access).complete(proof(peer(access), device, purpose='nl'), 'nl') == original


def test_invite_revoke_and_status_contract(access):
    if access.path is not None:
        sqlite_status_contract(access)
        return
    device = DeviceIdentity.generate()
    assert not access.status(proof(access, device, purpose='status'))['registered']
    invitation = access.invite()
    access.complete(proof(access, device, invitation), 'activate')
    with access.enrollment() as transaction:
        transaction.database.execute('UPDATE invites SET revoked=1 WHERE hash=%s', (access.code_hash(invitation),))
    status = access.status(proof(access, device, purpose='status'))
    assert status == dict(device=device.reference, registered=True, revoked=True, active=False)


def test_pending_activation_rejects_invite_revocation(access):
    device = DeviceIdentity.generate()
    invitation = access.invite()
    pending = proof(access, device, invitation)
    with access.enrollment() as transaction:
        transaction.database.execute(f'UPDATE invites SET revoked=1 WHERE hash={transaction.placeholder}',
            (access.code_hash(invitation),))
    with pytest.raises(Rejected):
        access.complete(pending, 'activate')


def test_installation_without_invitation_cannot_enroll(access):
    device = DeviceIdentity.generate()
    for purpose in ('activate', 'register', 'nl'):
        with pytest.raises(Rejected):
            proof(access, device, purpose=purpose)
    with access.enrollment() as transaction:
        assert transaction.database.execute('SELECT COUNT(*) AS total FROM devices').fetchone()['total'] == 0


def test_different_device_cannot_spend_a_challenge(access):
    device, other = DeviceIdentity.generate(), DeviceIdentity.generate()
    pending = proof(access, device, access.invite())
    with pytest.raises(Rejected):
        access.complete(other.prove_transport_key(pending['challenge']), 'activate')
    assert access.complete(pending, 'activate')['device'] == device.reference


def test_database_failure_never_falls_back_to_sqlite(postgres_access):
    access = postgres_access
    with pytest.raises(NotImplementedError, match='Legacy SQLite writers'):
        with access.db():
            pytest.fail('No implicit legacy database')
    with pytest.raises(NotImplementedError):
        access.initialize()
    access.enrollment_repository.schema = 'ha_enrollment_' + uuid.uuid4().hex
    with pytest.raises(Exception) as failure:
        access.invite()
    assert type(failure.value).__name__ == 'UndefinedTable'


def test_postgres_schema_marker_is_mandatory(postgres_access):
    access = postgres_access
    with access.enrollment() as transaction:
        transaction.database.execute('UPDATE ha_enrollment_schema SET version=2')
    with pytest.raises(RuntimeError, match='schema mismatch'):
        access.invite()


def test_postgres_lock_loss_is_bounded_and_rolls_back(postgres_access):
    access = postgres_access
    import psycopg
    from control.friends.enrollment_postgres import LOCK_ID
    repository = access.enrollment_repository
    with repository.connect() as holder:
        repository.configure(holder)
        holder.execute('SELECT pg_advisory_xact_lock(%s)', (LOCK_ID,))
        started = time.monotonic()
        with pytest.raises(psycopg.errors.LockNotAvailable):
            access.invite()
        assert time.monotonic() - started < 8
    with access.enrollment() as transaction:
        assert transaction.database.execute('SELECT COUNT(*) AS total FROM invites').fetchone()['total'] == 0
        assert transaction.database.execute('SHOW synchronous_commit').fetchone()['synchronous_commit'] == 'on'
        assert transaction.database.execute('SHOW transaction_isolation').fetchone()['transaction_isolation'] == 'read committed'
    assert access.invite().startswith('FC-')


@pytest.mark.parametrize('changes', [dict(port=0), dict(port=True), dict(schema='public'), dict(password='')])
def test_postgres_rejects_non_rehearsal_configuration(changes):
    settings = dict(port=15432, schema='ha_enrollment_' + 'a' * 32, password='synthetic-only')
    with pytest.raises(ValueError):
        PostgresEnrollment(**(settings | changes))


def test_no_ambiguous_sqlite_repository_selection(tmp_path):
    with pytest.raises(ValueError):
        Access(None)
    with pytest.raises(ValueError):
        Access(tmp_path / 'access.sqlite', enrollment_repository=object())
