from contextlib import contextmanager
import hashlib
import sqlite3
from types import SimpleNamespace

import pytest
from cryptography import x509
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding

from control.friends import paid_beta, restricted_admin as crl, restricted_sync, paid_canary_crl, support_ids
from control.friends.restricted import delegation, utc
from scripts.crl_postgres_rehearsal import initialize, publish_local_for_rehearsal
from scripts.paid_postgres_rehearsal import apply
from scripts.restricted_postgres_rehearsal import synthetic_service, issue_proof
from scripts.referral_postgres_rehearsal import NOW, proof
from tests.test_enrollment_repository import access as enrollment_access, parallel, postgres_access
from tests.test_friends_restricted import setup as legacy_setup


def setup(access):
    access.clock = lambda: NOW
    initialize(access)
    service, device = synthetic_service(access)
    response = service.fetch(issue_proof(service, device))
    return SimpleNamespace(access=access, service=service, device=device,
        certificate=x509.load_pem_x509_certificate(response['certificate'].encode()))


@pytest.fixture
def node(enrollment_access):
    return setup(enrollment_access)


@pytest.fixture
def postgres_node(postgres_access):
    return setup(postgres_access)


def prepare(node, operation_id='synthetic-crl-request', previous=None, **kwargs):
    return crl.prepare_crl(node.service, operation_id, node.service.crl_source() if previous is None else previous, **kwargs)


def state(node):
    with node.access.read_enrollment() as transaction:
        return {table: [dict(row) for row in transaction.database.execute('SELECT * FROM ' + table + ' ORDER BY 1')]
            for table in ('devices', 'invites', 'challenges', 'restricted_grants', 'restricted_certificates',
                          'restricted_crl_sequence', 'restricted_crl_publications')}


def test_candidate_is_signed_durable_and_not_published(node):
    record = prepare(node)
    parsed = x509.load_pem_x509_crl(record['payload'].encode())
    _, authority = delegation(node.service.manifest, node.service.anchor, NOW)
    assert parsed.is_signature_valid(authority.public_key())
    assert parsed.extensions.get_extension_for_class(x509.CRLNumber).value.crl_number == record['sequence'] == 2
    assert record['local_receipt'] == 0 and len(parsed) == 0
    assert record['expires_at'] - record['issued_at'] == 900
    assert record == crl.pending_crl(node.access, record['operation_id'])
    assert hashlib.sha256(record['payload'].encode()).hexdigest() == record['payload_sha256']


@pytest.mark.parametrize('mutation', ['device', 'invite', 'grant', 'revision', 'family', 'expiry'])
def test_revoked_or_outdated_certificate_is_listed(node, mutation):
    statements = dict(device='UPDATE devices SET revoked=1', invite='UPDATE invites SET revoked=1',
        grant='UPDATE restricted_grants SET revoked=1', revision='UPDATE restricted_grants SET revision=revision+1',
        family="UPDATE restricted_grants SET family='different-family'", expiry='UPDATE restricted_grants SET expires=' + str(NOW))
    with node.access.enrollment() as transaction:
        transaction.database.execute(statements[mutation])
    parsed = x509.load_pem_x509_crl(prepare(node)['payload'].encode())
    assert [record.serial_number for record in parsed] == [node.certificate.serial_number]


def test_paid_revoke_is_in_same_candidate_snapshot(node):
    if node.access.path is not None:
        with node.access.db() as database:
            paid_beta.migrate(database)
    alias = support_ids.request(node.access, dict(proof=proof(node.access, node.device, 'support'), platform='android',
        app_version='0.1.18-beta126', version_code=126))['device_support_id']
    with node.access.enrollment() as enrollment:
        apply(enrollment.paid(), alias)
        apply(enrollment.paid(), alias, 'revoke', 'synthetic-paid-revoke')
    assert x509.load_pem_x509_crl(prepare(node)['payload'].encode()).get_revoked_certificate_by_serial_number(
        node.certificate.serial_number) is not None


def test_same_operation_replays_exact_bytes_without_signing(node, monkeypatch):
    first = prepare(node)
    node.access.clock = lambda: NOW + 20
    monkeypatch.setattr(crl, 'build_crl_payload', lambda *args, **kwargs: pytest.fail('Replay must not re-sign'))
    assert prepare(node) == first
    with pytest.raises(ValueError, match='CRL operation conflict'):
        prepare(node, lifetime=1200)


def test_competing_and_identical_requests_are_serialized(node):
    results = parallel(lambda index: prepare(node), 6)
    assert all(result == results[0] for result in results)
    raw = results[0]['payload'].encode()

    def attempt(index):
        try:
            return prepare(node, 'competing-crl-' + str(index), raw)
        except ValueError:
            return None

    results = parallel(attempt, 6)
    assert sum(result is not None for result in results) == 1
    assert len(state(node)['restricted_crl_publications']) == 2


def test_only_latest_candidate_can_be_acknowledged_and_expiry_does_not_refresh_it(node):
    first = prepare(node)
    second = prepare(node, 'newer-crl-candidate', first['payload'].encode())
    assert prepare(node) == first
    with pytest.raises(ValueError, match='stale or inconsistent'):
        crl.pending_crl(node.access, first['operation_id'])
    with pytest.raises(ValueError, match='stale or inconsistent'):
        crl.acknowledge_crl(node.access, first['operation_id'], first['payload_sha256'])
    with pytest.raises(ValueError, match='CRL receipt mismatch'):
        crl.acknowledge_crl(node.access, second['operation_id'], '0' * 64)
    node.access.clock = lambda: second['expires_at']
    assert prepare(node, second['operation_id'], first['payload'].encode()) == second
    with pytest.raises(ValueError, match='stale or inconsistent'):
        crl.pending_crl(node.access, second['operation_id'])
    third = prepare(node, 'after-expired-candidate', second['payload'].encode())
    assert third['sequence'] == second['sequence'] + 1 and third['expires_at'] > second['expires_at']


@pytest.mark.parametrize('method', ['reserve', 'record', 'acknowledge'])
def test_database_failure_rolls_back_candidate_sequence_or_receipt(node, monkeypatch, method):
    if method == 'acknowledge':
        candidate = prepare(node)
        attempt = lambda: crl.acknowledge_crl(node.access, candidate['operation_id'], candidate['payload_sha256'])
    else:
        attempt = lambda: prepare(node)
    before = state(node)
    adapter = type(node.access.enrollment_repository).__name__
    if method == 'reserve' and adapter == 'PostgresEnrollment':
        from control.friends.crl_postgres import PostgresCRLTransaction
        target = PostgresCRLTransaction
    else:
        target = crl.CRLTransaction
    original = getattr(target, method)

    def fail(self, *args):
        original(self, *args)
        raise RuntimeError('synthetic CRL transaction failure')

    with monkeypatch.context() as patch:
        patch.setattr(target, method, fail)
        with pytest.raises(RuntimeError, match='synthetic CRL transaction failure'):
            attempt()
    assert state(node) == before
    attempt()


@pytest.mark.parametrize('phase', ['prepare', 'receipt'])
def test_lost_commit_ack_requires_idempotent_readback(node, monkeypatch, phase):
    if phase == 'receipt':
        record = prepare(node)
        attempt = lambda: crl.acknowledge_crl(node.access, record['operation_id'], record['payload_sha256'])
    else:
        attempt = lambda: prepare(node)
    original = node.access.enrollment

    @contextmanager
    def lost_ack():
        with original() as enrollment:
            yield enrollment
        raise RuntimeError('synthetic lost CRL commit ACK')

    with monkeypatch.context() as patch:
        patch.setattr(node.access, 'enrollment', lost_ack)
        with pytest.raises(RuntimeError, match='synthetic lost CRL commit ACK'):
            attempt()
    committed = state(node)
    attempt()
    assert state(node) == committed


@pytest.mark.parametrize('failure', ['file_fsync', 'replace', 'directory_fsync', 'receipt'])
def test_file_failure_never_invents_receipt_and_retries_exact_payload(node, tmp_path, monkeypatch, failure):
    record = prepare(node)
    target = tmp_path / 'revocations.pem'
    original_fsync = restricted_sync.os.fsync
    calls = []

    def failing_fsync(descriptor):
        calls.append(descriptor)
        if len(calls) == (1 if failure == 'file_fsync' else 2):
            raise OSError('synthetic CRL fsync failure')
        return original_fsync(descriptor)

    def fail(*args, **kwargs):
        raise OSError('synthetic CRL publication failure')

    with monkeypatch.context() as patch:
        if failure in ('file_fsync', 'directory_fsync'):
            patch.setattr(restricted_sync.os, 'fsync', failing_fsync)
        elif failure == 'replace':
            patch.setattr(restricted_sync.os, 'replace', fail)
        else:
            patch.setattr(crl, 'acknowledge_crl', fail)
        with pytest.raises(OSError, match='synthetic CRL'):
            publish_local_for_rehearsal(node.access, record['operation_id'], target)
    assert crl.pending_crl(node.access, record['operation_id']) == record
    assert target.exists() == (failure in ('directory_fsync', 'receipt'))
    if target.exists():
        assert target.read_bytes() == record['payload'].encode()
    repaired = publish_local_for_rehearsal(node.access, record['operation_id'], target)
    assert repaired['local_receipt'] == 1
    assert target.read_bytes() == record['payload'].encode()
    assert publish_local_for_rehearsal(node.access, record['operation_id'], target) == repaired


@pytest.mark.parametrize('mutation', ["SET payload='changed'", 'SET sequence=sequence+1', 'SET local_receipt=0', 'DELETE'])
def test_candidate_and_receipt_are_monotonic(node, mutation):
    import psycopg
    record = prepare(node)
    crl.acknowledge_crl(node.access, record['operation_id'], record['payload_sha256'])
    before = state(node)
    query = 'DELETE FROM restricted_crl_publications' if mutation == 'DELETE' else 'UPDATE restricted_crl_publications ' + mutation
    with pytest.raises((sqlite3.IntegrityError, psycopg.errors.CheckViolation)):
        with node.access.enrollment() as transaction:
            transaction.database.execute(query)
    assert state(node) == before


@pytest.mark.parametrize('damage', ['signer', 'previous_signature', 'future_previous', 'sequence_limit', 'sequence_divergence'])
def test_bad_authority_continuity_and_sequence_refuse_before_mutation(node, damage):
    previous = node.service.crl_source()
    if damage == 'signer':
        node.service.signing_key = Ed25519PrivateKey.generate()
    elif damage in ('previous_signature', 'future_previous', 'sequence_limit'):
        original = x509.load_pem_x509_crl(previous)
        after = NOW + 10 if damage == 'future_previous' else NOW - 1
        number = crl.CRL_LIMIT - 1 if damage == 'sequence_limit' else 1
        signer = Ed25519PrivateKey.generate() if damage == 'previous_signature' else node.service.signing_key
        previous = (x509.CertificateRevocationListBuilder().issuer_name(original.issuer).last_update(utc(after))
            .next_update(utc(NOW + 1000)).add_extension(x509.CRLNumber(number), False).sign(signer, None).public_bytes(Encoding.PEM))
    else:
        with node.access.enrollment() as transaction:
            transaction.database.execute('UPDATE restricted_crl_sequence SET sequence=20')
    before = state(node)
    with pytest.raises(ValueError):
        prepare(node, previous=previous)
    assert state(node) == before


def test_clock_sampled_after_lock_and_read_only_candidate(node, monkeypatch):
    original = node.access.enrollment

    @contextmanager
    def delayed():
        with original() as enrollment:
            node.access.clock = lambda: NOW + 100
            yield enrollment

    with monkeypatch.context() as patch:
        patch.setattr(node.access, 'enrollment', delayed)
        record = prepare(node)
    assert record['issued_at'] >= NOW + 90
    monkeypatch.setattr(node.access, 'enrollment', lambda: pytest.fail('Read-only candidate used writer'))
    assert crl.pending_crl(node.access, record['operation_id']) == record


def test_clock_change_while_building_rolls_back(node, monkeypatch):
    original = crl.build_crl_payload
    before = state(node)

    def late(*args, **kwargs):
        raw, metadata = original(*args, **kwargs)
        node.access.clock = lambda: metadata['next_update']
        return raw, metadata

    monkeypatch.setattr(crl, 'build_crl_payload', late)
    with pytest.raises(ValueError, match='CRL preparation clock changed'):
        prepare(node)
    assert state(node) == before


def test_no_legacy_or_remote_publication_from_outbox(node, tmp_path, monkeypatch):
    before = set(tmp_path.iterdir())
    node.service.crl_source = lambda: pytest.fail('Publisher must refuse before reading CRL')
    with pytest.raises(NotImplementedError, match='fenced'):
        crl.publish_crl(node.service, tmp_path / 'revocations.pem')
    monkeypatch.setattr(restricted_sync, 'from_env', lambda *args: pytest.fail('No issuer file read'))
    for operation in (restricted_sync.sync, restricted_sync.check):
        with pytest.raises(NotImplementedError, match='fenced'):
            operation(node.access, '186.246.45.246', tmp_path / 'key', tmp_path / 'hosts')
    operator = object.__new__(paid_canary_crl.Operation)
    operator.config = SimpleNamespace(service=node.service)
    with pytest.raises(NotImplementedError, match='fenced'), operator.locked():
        pytest.fail('No local flock for PG or synthetic outbox')
    assert set(tmp_path.iterdir()) == before


@pytest.mark.parametrize('changes', [dict(operation_id=''), dict(operation_id='bad operation'),
    dict(operation_id=True), dict(previous_crl=b''), dict(previous_crl='not-bytes'),
    dict(lifetime=True), dict(lifetime=899), dict(lifetime=900.0)])
def test_invalid_prepare_is_atomic(node, changes):
    before = state(node)
    arguments = dict(operation_id='synthetic-crl-request', previous_crl=node.service.crl_source()) | changes
    with pytest.raises(ValueError):
        crl.prepare_crl(node.service, **arguments)
    assert state(node) == before


@pytest.mark.parametrize('damage', ['missing', 'wrong'])
def test_postgres_crl_marker_required(postgres_node, damage):
    import psycopg
    with postgres_node.access.enrollment() as transaction:
        transaction.database.execute('DROP TABLE ha_crl_schema' if damage == 'missing' else "UPDATE ha_crl_schema SET purpose='wrong'")
    with pytest.raises(psycopg.errors.UndefinedTable if damage == 'missing' else RuntimeError):
        prepare(postgres_node)


@pytest.mark.parametrize('phase', ['record', 'acknowledge'])
def test_postgres_backend_loss_preserves_prior_state(postgres_node, monkeypatch, phase):
    import psycopg
    node = postgres_node
    if phase == 'acknowledge':
        record = prepare(node)
        attempt = lambda: crl.acknowledge_crl(node.access, record['operation_id'], record['payload_sha256'])
    else:
        attempt = lambda: prepare(node)
    before = state(node)
    original = getattr(crl.CRLTransaction, phase)

    def kill(self, *args):
        original(self, *args)
        with node.access.enrollment_repository.connect() as killer:
            pid = self.database.execute('SELECT pg_backend_pid() AS pid').fetchone()['pid']
            assert killer.execute('SELECT pg_terminate_backend(%s,1000) AS stopped', (pid,)).fetchone()['stopped']
        self.database.execute('SELECT 1')

    with monkeypatch.context() as patch:
        patch.setattr(crl.CRLTransaction, phase, kill)
        with pytest.raises(psycopg.OperationalError):
            attempt()
    assert state(node) == before
    attempt()


def test_postgres_candidate_cannot_be_truncated(postgres_node):
    import psycopg
    prepare(postgres_node)
    before = state(postgres_node)
    with pytest.raises(psycopg.errors.CheckViolation):
        with postgres_node.access.enrollment() as transaction:
            transaction.database.execute('TRUNCATE restricted_crl_publications')
    assert state(postgres_node) == before


@pytest.mark.parametrize('committed', [False, True])
def test_legacy_file_ahead_or_ack_loss_never_rewinds_sequence(legacy_setup, tmp_path, monkeypatch, committed):
    service, device, now = legacy_setup
    target = tmp_path / 'revocations.pem'
    target.write_bytes(service.crl_source())
    service.crl_source = target.read_bytes
    original = service.access.enrollment

    @contextmanager
    def interrupted():
        with original() as enrollment:
            yield enrollment
            if not committed:
                raise RuntimeError('synthetic legacy commit failure')
        raise RuntimeError('synthetic legacy lost ACK')

    with monkeypatch.context() as patch:
        patch.setattr(service.access, 'enrollment', interrupted)
        with pytest.raises(RuntimeError, match='synthetic legacy'):
            crl.publish_crl(service, target)
    assert x509.load_pem_x509_crl(target.read_bytes()).extensions.get_extension_for_class(x509.CRLNumber).value.crl_number == 2
    with service.access.read_enrollment() as enrollment:
        assert enrollment.crl().sequence() == (2 if committed else 0)
    assert crl.publish_crl(service, target) == 3
    with service.access.read_enrollment() as enrollment:
        assert enrollment.crl().sequence() == 3


def test_legacy_publisher_samples_clock_after_writer_acquisition(legacy_setup, tmp_path, monkeypatch):
    service, device, now = legacy_setup
    original = service.access.enrollment

    @contextmanager
    def delayed():
        with original() as enrollment:
            service.access.clock = lambda: now + 100
            yield enrollment

    monkeypatch.setattr(service.access, 'enrollment', delayed)
    target = tmp_path / 'revocations.pem'
    crl.publish_crl(service, target)
    assert x509.load_pem_x509_crl(target.read_bytes()).last_update_utc >= utc(now + 90)
