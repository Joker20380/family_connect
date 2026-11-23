from contextlib import contextmanager
from copy import copy
import sqlite3

import pytest
from cryptography import x509

from control.friends import readiness_receipts as receipts, support_ids
from control.friends.access import Rejected
from control.friends.restricted import ChallengeUnavailable, RestrictedTransaction, migrate, utc
from control.friends.restricted_admin import grant
from scripts.paid_postgres_rehearsal import apply
from scripts.restricted_postgres_rehearsal import NOW, initialize, synthetic_service, issue_proof, receipt, ack_proof
from scripts.referral_postgres_rehearsal import proof
from tests.test_enrollment_repository import access as enrollment_access, parallel, peer, postgres_access
from tests.test_friends_restricted import (
    test_active_device_public_only_and_idempotent_refresh,
    test_wrong_device_and_replay_expired_challenge,
    test_purpose_is_not_normal_provisioning,
    test_request_limits_and_trust_bounds,
)
from tests.test_readiness_receipts import (
    test_authenticated_ack_and_owner_bound_safe_readback,
    test_failed_import_ack_never_claims_ready,
    test_proof_binds_exact_payload_and_cannot_replay,
    test_strict_schema_redaction,
)
from tests.test_restricted_gateway_selection import pair


@pytest.fixture
def setup(enrollment_access):
    access = enrollment_access
    access.clock = lambda: NOW
    if access.path is None:
        initialize(access.enrollment_repository)
    else:
        migrate(access)
    service, device = synthetic_service(access)
    return service, device, NOW


@pytest.fixture
def postgres_setup(postgres_access):
    postgres_access.clock = lambda: NOW
    initialize(postgres_access.enrollment_repository)
    service, device = synthetic_service(postgres_access)
    return service, device, NOW


@pytest.fixture
def ready(setup):
    service, device, now = setup
    response = service.fetch(issue_proof(service, device, 'a' * 32), request_id='b' * 32)
    return service, device, now, receipt(response)


def state(service):
    with service.access.enrollment() as transaction:
        return {table: [dict(row) for row in transaction.database.execute('SELECT * FROM ' + table + ' ORDER BY 1')]
                for table in ('devices', 'invites', 'challenges', 'restricted_grants', 'restricted_challenges',
                              'restricted_certificates', 'restricted_readiness_results')}


def independent(service):
    result = copy(service)
    result.access = peer(service.access)
    return result


@pytest.mark.parametrize('mutation', ['UPDATE devices SET revoked=1', 'UPDATE invites SET revoked=1',
    'UPDATE restricted_grants SET revoked=1', 'UPDATE restricted_grants SET revision=revision+1',
    'UPDATE restricted_grants SET expires=1', "UPDATE restricted_grants SET family='other'"])
def test_authorization_rechecked_without_consuming_proof(setup, mutation):
    service, device, now = setup
    pending = issue_proof(service, device)
    with service.access.enrollment() as transaction:
        transaction.database.execute(mutation)
    before = state(service)
    with pytest.raises(Rejected):
        service.fetch(pending)
    assert state(service) == before


def test_concurrent_proof_use_and_fresh_retry_reuse_certificate(setup):
    service, device, now = setup
    pending = issue_proof(service, device, 'a' * 32)
    results = parallel(lambda index: independent(service).fetch(pending, request_id='b' * 32), 8)
    accepted = [value for value in results if value is not None]
    assert len(accepted) == 1
    fresh = service.fetch(issue_proof(service, device))
    assert fresh['certificate'] == accepted[0]['certificate']
    assert len(state(service)['restricted_certificates']) == 1


@pytest.mark.parametrize('stage', ['add_certificate', 'fetched', 'acknowledge', 'correlate'])
def test_failed_write_rolls_back_entire_issuance_or_ack(setup, monkeypatch, stage):
    service, device, now = setup
    if stage == 'correlate':
        attempt = lambda: issue_proof(service, device, 'a' * 32)
    else:
        pending = issue_proof(service, device, 'a' * 32)
        if stage == 'acknowledge':
            payload = receipt(service.fetch(pending, request_id='b' * 32))
            value = dict(proof=ack_proof(service, device, payload), receipt=payload)
            attempt = lambda: receipts.acknowledge(service, value)
        else:
            attempt = lambda: service.fetch(pending, request_id='b' * 32)
    original = getattr(RestrictedTransaction, stage)
    before = state(service)

    def fail_after(self, *args):
        original(self, *args)
        raise RuntimeError('synthetic write failure')

    with monkeypatch.context() as patch:
        patch.setattr(RestrictedTransaction, stage, fail_after)
        with pytest.raises(RuntimeError):
            attempt()
    assert state(service) == before
    attempt()


def test_duplicate_correlation_rolls_back_new_challenge(setup):
    service, device, now = setup
    issue_proof(service, device, 'a' * 32)
    before = state(service)
    with pytest.raises(ChallengeUnavailable) as error:
        issue_proof(service, device, 'a' * 32)
    assert error.value.stage == 'correlation_store'
    assert state(service) == before


@pytest.mark.parametrize('operation', ['fetch', 'ack'])
def test_commit_ack_loss_uses_readback_and_new_proof(ready, monkeypatch, operation):
    service, device, now, payload = ready
    original = service.access.enrollment
    if operation == 'fetch':
        value = issue_proof(service, device, 'c' * 32)
        attempt = lambda target: target.fetch(value, request_id='d' * 32)
    else:
        value = dict(proof=ack_proof(service, device, payload), receipt=payload)
        attempt = lambda target: receipts.acknowledge(target, value)

    @contextmanager
    def lost_ack():
        with original() as transaction:
            yield transaction
        raise ConnectionError('synthetic commit ACK loss')

    with monkeypatch.context() as patch:
        patch.setattr(service.access, 'enrollment', lost_ack)
        with pytest.raises(ConnectionError):
            attempt(service)
    with pytest.raises(Rejected):
        attempt(independent(service))
    if operation == 'fetch':
        before = state(service)['restricted_certificates']
        fresh = service.fetch(issue_proof(service, device))
        assert fresh['certificate'] == before[0]['certificate']
        assert state(service)['restricted_certificates'] == before
    else:
        assert receipts.readback(service, 'a' * 32, device.reference)['receipt'] == payload


def test_concurrent_capacity_cannot_exceed_eight(setup):
    service, device, now = setup

    def attempt(index):
        try:
            return issue_proof(independent(service), device)
        except ChallengeUnavailable as error:
            assert error.reason == 'CHALLENGE_CAPACITY_EXHAUSTED'

    results = parallel(attempt, 12)
    assert len([value for value in results if value is not None]) == 8
    assert sum(not row['used'] for row in state(service)['challenges']) == 8


def test_receipt_retention_has_deterministic_ties_and_age_bound(setup):
    service, device, now = setup
    with service.access.enrollment() as transaction:
        store = transaction.restricted()
        for index in range(18):
            token = format(index, '032x')
            receipts.challenge(store, token, token, device.reference, now)
    rows = state(service)['restricted_readiness_results']
    assert [row['correlation'] for row in rows] == [format(index, '032x') for index in (*range(15), 17)]
    with service.access.enrollment() as transaction:
        receipts.challenge(transaction.restricted(), 'f' * 32, 'f' * 32, device.reference, now + 86401)
    assert len(state(service)['restricted_readiness_results']) == 1


@pytest.mark.parametrize('all_activated', [False, True])
def test_auto_enrollment_and_all_activated_preserve_grant_policy(setup, all_activated):
    service, device, now = setup
    with service.access.enrollment() as transaction:
        transaction.database.execute('DELETE FROM restricted_grants')
    service.all_activated = all_activated
    service.eligible_devices = None if all_activated else frozenset([device.reference])
    service.fetch(issue_proof(service, device))
    grants = state(service)['restricted_grants']
    assert len(grants) == (0 if all_activated else 1)
    if grants:
        assert grants[0]['expires'] is None
    grant(service.access, device.reference, 'a' * 32, now + 1)
    service.access.clock = lambda: now + 2
    if all_activated:
        service.fetch(issue_proof(service, device))
    else:
        with pytest.raises(Rejected):
            issue_proof(service, device)
    with service.access.enrollment() as transaction:
        transaction.restricted_admin().revoke_grant(device.reference)
    with pytest.raises(Rejected):
        issue_proof(service, device)


def test_certificate_revoke_cannot_be_bypassed_with_fresh_proof(setup):
    service, device, now = setup
    response = service.fetch(issue_proof(service, device))
    leaf = x509.load_pem_x509_certificate(response['certificate'].encode())
    previous = x509.load_pem_x509_crl(service.crl_source())
    crl = (x509.CertificateRevocationListBuilder().issuer_name(previous.issuer).last_update(utc(now)).next_update(utc(now + 3000))
        .add_extension(x509.CRLNumber(2), False)
        .add_revoked_certificate(x509.RevokedCertificateBuilder().serial_number(leaf.serial_number).revocation_date(utc(now)).build())
        .sign(service.signing_key, None))
    from cryptography.hazmat.primitives.serialization import Encoding
    service.crl_source = lambda: crl.public_bytes(Encoding.PEM)
    pending = issue_proof(service, device)
    before = state(service)
    with pytest.raises(Rejected):
        service.fetch(pending)
    assert state(service) == before


@pytest.mark.parametrize('reverse', [False, True])
def test_gateway_bound_fetch_ack_and_readback(ready, reverse):
    primary, device, now, payload = ready
    secondary, _ = pair(primary)
    service, wrong = (secondary, primary) if reverse else (primary, secondary)
    pending = issue_proof(service, device, 'c' * 32)
    with pytest.raises(Rejected):
        wrong.fetch(pending, request_id='d' * 32)
    response = service.fetch(pending, request_id='d' * 32)
    payload = receipt(response, 'c' * 32, 'd' * 32)
    with pytest.raises(Rejected):
        ack_proof(wrong, device, payload)
    value = dict(proof=ack_proof(service, device, payload), receipt=payload)
    with pytest.raises(Rejected):
        receipts.acknowledge(wrong, value)
    receipts.acknowledge(service, value)
    assert receipts.readback(wrong, 'c' * 32, device.reference)['status'] == 'UNKNOWN'
    assert receipts.readback(service, 'c' * 32, device.reference)['receipt'] == payload


@pytest.mark.parametrize('mutation', ['device', 'invite', 'grant', 'revision', 'fetch', 'floor', 'expiry', 'skew'])
def test_ack_revalidates_authority_without_consuming_proof(ready, mutation):
    service, device, now, payload = ready
    value = dict(proof=ack_proof(service, device, payload), receipt=dict(payload))
    if mutation in ('device', 'invite', 'grant', 'revision'):
        statement = dict(device='UPDATE devices SET revoked=1', invite='UPDATE invites SET revoked=1',
            grant='UPDATE restricted_grants SET revoked=1', revision='UPDATE restricted_grants SET revision=revision+1')[mutation]
        with service.access.enrollment() as transaction:
            transaction.database.execute(statement)
    else:
        key, replacement = dict(fetch=('fetch_id', 'd' * 32), floor=('minimum_crl', payload['minimum_crl'] + 1),
            expiry=('expires_at', payload['expires_at'] + 1), skew=('observed_at', now + 6))[mutation]
        value['receipt'][key] = replacement
    before = state(service)
    with pytest.raises(Rejected):
        receipts.acknowledge(service, value)
    assert state(service) == before


def test_concurrent_ack_and_revoke_readback(ready):
    service, device, now, payload = ready
    value = dict(proof=ack_proof(service, device, payload), receipt=payload)
    results = parallel(lambda index: receipts.acknowledge(independent(service), value), 8)
    assert len([result for result in results if result is not None]) == 1
    assert receipts.readback(service, 'a' * 32, device.reference)['status'] == 'ACK_RECEIVED'
    service.access.revoke_device(device.reference)
    assert receipts.readback(service, 'a' * 32, device.reference)['status'] == 'ACK_PENDING'


def test_readonly_snapshot_is_enforced_and_does_not_block_writer(setup):
    service, device, now = setup
    with service.access.read_enrollment() as transaction:
        assert transaction.device(device.reference)['revoked'] == 0
        if service.access.path is None:
            assert transaction.database.execute('SHOW transaction_read_only').fetchone()['transaction_read_only'] == 'on'
            peer(service.access).revoke_device(device.reference)
            assert transaction.device(device.reference)['revoked'] == 0
    errors = (sqlite3.OperationalError,)
    if service.access.path is None:
        import psycopg
        errors = (psycopg.errors.ReadOnlySqlTransaction,)
    with pytest.raises(errors):
        with service.access.read_enrollment() as transaction:
            transaction.revoke_device(device.reference)


def test_paid_boundary_and_revocation_are_preserved(setup):
    service, device, now = setup
    first = service.fetch(issue_proof(service, device))
    support = support_ids.request(service.access, dict(proof=proof(service.access, device, 'support'), platform='android',
        app_version='0.1.18-beta126', version_code=126))['device_support_id']
    with service.access.enrollment() as transaction:
        apply(transaction.paid(), support, paid_until=now + 60)
    response = service.fetch(issue_proof(service, device))
    assert response['expires_at'] == now + 60
    assert response['certificate'] != first['certificate']
    pending = issue_proof(service, device)
    service.access.clock = lambda: now + 60
    with pytest.raises(Rejected):
        service.fetch(pending)


def test_expired_authority_after_transaction_wait_is_refused(setup, monkeypatch):
    service, device, now = setup
    original = service.access.enrollment

    @contextmanager
    def delayed():
        with original() as transaction:
            service.access.clock = lambda: now + 4000
            yield transaction

    before = state(service)
    monkeypatch.setattr(service.access, 'enrollment', delayed)
    with pytest.raises(Rejected):
        issue_proof(service, device)
    assert state(service) == before


@pytest.mark.parametrize('marker', ['missing', 'wrong', 'paid'])
def test_postgres_guards_never_fallback_to_unpaid_or_sqlite(postgres_setup, marker):
    service, device, now = postgres_setup
    pending = issue_proof(service, device)
    with service.access.enrollment() as transaction:
        if marker == 'missing':
            transaction.database.execute('DROP TABLE ha_restricted_schema')
        elif marker == 'wrong':
            transaction.database.execute("UPDATE ha_restricted_schema SET purpose='wrong'")
        else:
            transaction.database.execute('DROP TABLE paid_beta_subscriptions CASCADE')
            transaction.database.execute('DROP TABLE paid_beta_events')
    before = state(service)
    import psycopg
    for attempt in (lambda: issue_proof(service, device), lambda: service.fetch(pending),
                    lambda: receipts.readback(service, 'a' * 32, device.reference)):
        with pytest.raises((RuntimeError, ValueError, psycopg.Error)):
            attempt()
    assert state(service) == before


@pytest.mark.parametrize('stage', ['fetched', 'acknowledge'])
def test_postgres_backend_loss_rolls_back_certificate_receipt_and_proof(postgres_setup, monkeypatch, stage):
    service, device, now = postgres_setup
    pending = issue_proof(service, device, 'a' * 32)
    attempt = lambda: service.fetch(pending, request_id='b' * 32)
    if stage == 'acknowledge':
        payload = receipt(attempt())
        value = dict(proof=ack_proof(service, device, payload), receipt=payload)
        attempt = lambda: receipts.acknowledge(service, value)
    original = getattr(RestrictedTransaction, stage)
    before = state(service)

    def terminate_after(self, *args):
        original(self, *args)
        with service.access.enrollment_repository.connect() as killer:
            pid = self.database.execute('SELECT pg_backend_pid() AS pid').fetchone()['pid']
            assert killer.execute('SELECT pg_terminate_backend(%s,1000) AS stopped', (pid,)).fetchone()['stopped']
        self.database.execute('SELECT 1')

    import psycopg
    with monkeypatch.context() as patch:
        patch.setattr(RestrictedTransaction, stage, terminate_after)
        with pytest.raises(psycopg.OperationalError):
            attempt()
    assert state(service) == before
    attempt()
