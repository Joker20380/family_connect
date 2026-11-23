from contextlib import contextmanager
import json
import sqlite3
from types import SimpleNamespace

import pytest

from control.friends.access import Access, EnrollmentTransaction, Rejected
from control.friends import technical_metadata as metadata
from control.friends.referrals import RateLimited
from device_identity.device import DeviceIdentity
from scripts.metadata_postgres_rehearsal import initialize, report, request_value
from scripts.referral_postgres_rehearsal import NOW, proof
from tests.test_enrollment_repository import access as enrollment_access, parallel, postgres_access
from tests.test_technical_metadata import setup as legacy_setup, report as legacy_report


def enroll(access):
    device = DeviceIdentity.generate()
    access.complete(proof(access, device, 'activate', access.invite()), 'activate')
    return device


def setup(access):
    access.clock = lambda: NOW
    initialize(access)
    return SimpleNamespace(access=access, device=enroll(access))


@pytest.fixture
def node(enrollment_access):
    return setup(enrollment_access)


@pytest.fixture
def postgres_node(postgres_access):
    return setup(postgres_access)


def submit(node, value=None):
    return metadata.request_repository(node.access, request_value(node.access, node.device, value or report()))


def state(node):
    with node.access.read_enrollment() as enrollment:
        transaction = metadata.MetadataTransaction(enrollment.database, enrollment.placeholder)
        return {table: transaction.fetch('SELECT * FROM ' + table + ' ORDER BY 1')
            for table in ('device_metadata', 'challenges', 'devices', 'invites', 'device_support')}


def test_latest_only_exact_digest_receipt_and_identity_isolation(node):
    response = submit(node)
    assert response == submit(node)
    assert response['received_at'] == NOW
    assert len(state(node)['device_metadata']) == 1
    other = SimpleNamespace(access=node.access, device=enroll(node.access))
    submit(other)
    assert {row['device'] for row in metadata.read_repository(node.access)} == {node.device.reference, other.device.reference}
    node.access.clock = lambda: NOW + 60
    submit(node, report(sequence=2, now=NOW + 60))
    assert len(state(node)['device_metadata']) == 2
    assert set(state(node)['device_metadata'][0]) == {'device', 'epoch', 'sequence', 'digest', 'enabled', 'received', 'payload'}


def test_proof_binds_bytes_and_is_consumed_once_with_metadata(node):
    value = request_value(node.access, node.device, report())
    before = state(node)
    changed = value | {'report': value['report'].replace('Synthetic device', 'Changed device')}
    with pytest.raises(Rejected):
        metadata.request_repository(node.access, changed)
    assert state(node) == before
    metadata.request_repository(node.access, value)
    before = state(node)
    with pytest.raises(Rejected):
        metadata.request_repository(node.access, value)
    assert state(node) == before


@pytest.mark.parametrize('mode', ['one_proof', 'identical', 'conflict'])
def test_concurrent_reports_serialize_without_duplicate_or_conflicting_state(node, mode):
    values = []
    for index in range(6):
        candidate = report()
        if mode == 'conflict':
            candidate['observations']['profile']['values']['model'] = 'Synthetic ' + str(index)
        values.append(request_value(node.access, node.device, candidate))
    if mode == 'one_proof':
        values = [values[0]] * 6
    results = parallel(lambda index: metadata.request_repository(node.access, values[index]), 6)
    assert sum(result is not None for result in results) == (6 if mode == 'identical' else 1)
    assert len(state(node)['device_metadata']) == 1


def test_rate_limit_rolls_back_proof_but_revoke_bypasses_it(node):
    submit(node)
    value = request_value(node.access, node.device, report(sequence=2))
    before = state(node)
    with pytest.raises(RateLimited):
        metadata.request_repository(node.access, value)
    assert state(node) == before
    assert submit(node, report(epoch=2, operation='revoke'))['consent'] == 'revoked'
    with pytest.raises(Rejected):
        metadata.request_repository(node.access, value)
    assert metadata.read_repository(node.access)[0]['observations'] == {}


def test_concurrent_sample_and_revoke_always_leave_consent_revoked(node):
    values = [request_value(node.access, node.device, report()),
              request_value(node.access, node.device, report(epoch=2, operation='revoke'))]
    results = parallel(lambda index: metadata.request_repository(node.access, values[index]), 2)
    assert results[1]['consent'] == 'revoked'
    row = metadata.read_repository(node.access)[0]
    assert row['consent_epoch'] == 2 and row['consent'] == 'revoked' and row['observations'] == {}


def test_tombstone_survives_restart_prune_delayed_reports_and_requires_new_epoch(node):
    submit(node, report(epoch=2, operation='revoke'))
    node.access = Access(node.access.path, clock=lambda: NOW + 10 * metadata.RETENTION,
                         enrollment_repository=node.access.enrollment_repository)
    metadata.prune_repository(node.access)
    for candidate in (report(sequence=100), report(epoch=2, sequence=2)):
        value = request_value(node.access, node.device, candidate)
        before = state(node)
        with pytest.raises(Rejected):
            metadata.request_repository(node.access, value)
        assert state(node) == before
    assert submit(node, report(epoch=3, now=int(node.access.clock())))['consent'] == 'enabled'


def test_per_group_expiry_is_not_renewed_by_read_prune_or_duplicate(node):
    candidate = report()
    observation = candidate['observations']['network']
    observation['age_ms'] = (metadata.RETENTION - 10) * 1000
    observation['sampled_at_ms'] -= observation['age_ms']
    response = submit(node, candidate)
    node.access.clock = lambda: NOW + 11
    before = state(node)
    row = metadata.read_repository(node.access)[0]
    assert 'network' not in row['observations'] and 'profile' in row['observations']
    assert state(node) == before
    metadata.prune_repository(node.access)
    assert 'network' not in json.loads(state(node)['device_metadata'][0]['payload'])
    node.access.clock = lambda: NOW + metadata.RETENTION
    metadata.prune_repository(node.access)
    assert submit(node, candidate) == response
    assert metadata.read_repository(node.access)[0]['observations'] == {}
    assert len(state(node)['device_metadata']) == 1


@pytest.mark.parametrize('offset', [-864000000, 864000000])
def test_clock_skew_preserves_reported_age_and_server_retention(node, offset):
    candidate = report()
    for observation in candidate['observations'].values():
        observation['sampled_at_ms'] += offset
        observation['age_ms'] = 60000
    submit(node, candidate)
    observation = metadata.read_repository(node.access)[0]['observations']['profile']
    assert observation['clock_status'] == 'clock_skew'
    assert observation['expires_at'] == NOW + metadata.RETENTION - 60


def test_capacity_concurrency_retains_floors_and_allows_existing_revoke(node, monkeypatch):
    monkeypatch.setattr(metadata, 'MAX_DEVICES', 1)
    devices = [node.device, enroll(node.access)]
    values = [request_value(node.access, device, report()) for device in devices]
    results = parallel(lambda index: metadata.request_repository(node.access, values[index]), 2)
    assert sum(result is not None for result in results) == 1
    device = devices[next(index for index, result in enumerate(results) if result is not None)]
    metadata.request_repository(node.access, request_value(node.access, device, report(epoch=2, operation='revoke')))
    metadata.prune_repository(node.access)
    assert len(state(node)['device_metadata']) == 1


@pytest.mark.parametrize('phase', ['consume', 'save', 'prune'])
def test_failures_rollback_proof_payload_and_retention(node, monkeypatch, phase):
    if phase == 'prune':
        submit(node)
        node.access.clock = lambda: NOW + metadata.RETENTION
        attempt = lambda: metadata.prune_repository(node.access)
        target, method = metadata.MetadataTransaction, 'expire'
    else:
        value = request_value(node.access, node.device, report())
        attempt = lambda: metadata.request_repository(node.access, value)
        target, method = ((EnrollmentTransaction, 'consume_challenge') if phase == 'consume'
                          else (metadata.MetadataTransaction, 'save'))
    before = state(node)
    original = getattr(target, method)

    def fail(self, *args):
        original(self, *args)
        raise RuntimeError('synthetic metadata failure')

    with monkeypatch.context() as patch:
        patch.setattr(target, method, fail)
        with pytest.raises(RuntimeError, match='synthetic metadata failure'):
            attempt()
    assert state(node) == before
    attempt()


@pytest.mark.parametrize('operation', ['sample', 'revoke'])
def test_lost_commit_ack_requires_fresh_proof_but_same_report_not_new_consent(node, monkeypatch, operation):
    candidate = report(operation=operation)
    value = request_value(node.access, node.device, candidate)
    original = node.access.enrollment

    @contextmanager
    def lost_ack():
        with original() as enrollment:
            yield enrollment
        raise RuntimeError('synthetic metadata lost ACK')

    with monkeypatch.context() as patch:
        patch.setattr(node.access, 'enrollment', lost_ack)
        with pytest.raises(RuntimeError, match='synthetic metadata lost ACK'):
            metadata.request_repository(node.access, value)
    committed = state(node)
    with pytest.raises(Rejected):
        metadata.request_repository(node.access, value)
    assert state(node) == committed
    node.access.clock = lambda: NOW + 20
    assert submit(node, candidate)['received_at'] == NOW
    assert state(node)['device_metadata'] == committed['device_metadata']


@pytest.mark.parametrize('revocation', ['device', 'invite'])
def test_revocation_after_challenge_prevents_metadata_and_proof_commit(node, revocation):
    value = request_value(node.access, node.device, report())
    with node.access.enrollment() as enrollment:
        enrollment.database.execute('UPDATE ' + ('devices' if revocation == 'device' else 'invites') + ' SET revoked=1')
    before = state(node)
    with pytest.raises(Rejected):
        metadata.request_repository(node.access, value)
    assert state(node) == before


@pytest.mark.parametrize('delay', [60, 101])
def test_time_and_proof_expiry_are_checked_after_writer_wait(node, monkeypatch, delay):
    value = request_value(node.access, node.device, report())
    before = state(node)
    original = node.access.enrollment

    @contextmanager
    def delayed():
        with original() as enrollment:
            node.access.clock = lambda: NOW + delay
            yield enrollment

    monkeypatch.setattr(node.access, 'enrollment', delayed)
    if delay == 60:
        assert metadata.request_repository(node.access, value)['received_at'] == NOW + delay
    else:
        with pytest.raises(Rejected):
            metadata.request_repository(node.access, value)
        assert state(node) == before


@pytest.mark.parametrize('mutation', ['epoch', 'sequence', 'digest', 'received', 'payload', 'delete', 'resurrect'])
def test_schema_prevents_version_floor_loss_and_retention_resurrection(node, mutation):
    import psycopg
    submit(node, report(epoch=2, sequence=2))
    if mutation == 'resurrect':
        submit(node, report(epoch=2, sequence=3, operation='revoke'))
    if mutation == 'payload':
        payload = state(node)['device_metadata'][0]['payload']
        node.access.clock = lambda: NOW + metadata.RETENTION
        metadata.prune_repository(node.access)
    before = state(node)
    with pytest.raises((sqlite3.IntegrityError, psycopg.errors.CheckViolation)):
        with node.access.enrollment() as enrollment:
            if mutation == 'payload':
                enrollment.database.execute('UPDATE device_metadata SET payload=' + enrollment.placeholder, (payload,))
            else:
                query = {'epoch': 'UPDATE device_metadata SET epoch=1', 'sequence': 'UPDATE device_metadata SET sequence=1',
                    'digest': "UPDATE device_metadata SET digest='different'", 'received': 'UPDATE device_metadata SET received=received+1',
                    'delete': 'DELETE FROM device_metadata', 'resurrect': 'UPDATE device_metadata SET enabled=1,sequence=sequence+1'}[mutation]
                enrollment.database.execute(query)
    assert state(node) == before


def test_read_only_snapshot_does_not_prune_or_take_writer_lock(node, monkeypatch):
    submit(node)
    node.access.clock = lambda: NOW + metadata.RETENTION
    before = state(node)
    monkeypatch.setattr(node.access, 'enrollment', lambda: pytest.fail('Read must not use writer'))
    assert metadata.read_repository(node.access)[0]['observations'] == {}
    assert state(node) == before


def test_legacy_path_cannot_consume_proof_or_create_split_database(node, tmp_path, monkeypatch):
    value = request_value(node.access, node.device, report())
    before = state(node)
    target = tmp_path / 'forbidden-metadata.sqlite'
    monkeypatch.setattr(node.access, 'complete', lambda *args, **kwargs: pytest.fail('No proof use before refusal'))
    with pytest.raises(NotImplementedError):
        metadata.request(node.access, target, value)
    assert not target.exists() and state(node) == before


@pytest.mark.parametrize('damage', ['missing', 'wrong'])
def test_required_schema_marker_refuses_before_proof_use(node, damage):
    import psycopg
    value = request_value(node.access, node.device, report())
    with node.access.enrollment() as enrollment:
        enrollment.database.execute('DROP TABLE ha_metadata_schema' if damage == 'missing'
                                    else "UPDATE ha_metadata_schema SET purpose='wrong'")
    before = state(node)
    with pytest.raises((RuntimeError, sqlite3.OperationalError, psycopg.errors.UndefinedTable)):
        metadata.request_repository(node.access, value)
    assert state(node) == before


@pytest.mark.parametrize('mutation', ['boolean', 'ip', 'duplicate', 'oversize', 'wrong_id', 'unknown'])
def test_validation_refuses_without_consuming_proof(node, mutation):
    value = request_value(node.access, node.device, report())
    candidate = json.loads(value['report'])
    if mutation == 'boolean':
        candidate['sequence'] = True
    elif mutation == 'ip':
        candidate['ip'] = '203.0.113.1'
    elif mutation == 'wrong_id':
        candidate['report_id'] = '0' * 32
    elif mutation == 'unknown':
        candidate['observations']['profile']['values']['imei'] = 'forbidden'
    value['report'] = json.dumps(candidate)
    if mutation == 'duplicate':
        value['report'] = '{"schema":1,' + value['report'][1:]
    elif mutation == 'oversize':
        value['report'] = ' ' * (metadata.MAX_REPORT + 1)
    before = state(node)
    with pytest.raises(ValueError):
        metadata.request_repository(node.access, value)
    assert state(node) == before


@pytest.mark.parametrize('method', ['save', 'expire'])
def test_postgres_backend_loss_preserves_consent_and_proof(postgres_node, monkeypatch, method):
    import psycopg
    node = postgres_node
    if method == 'expire':
        submit(node)
        node.access.clock = lambda: NOW + metadata.RETENTION
        attempt = lambda: metadata.prune_repository(node.access)
    else:
        value = request_value(node.access, node.device, report(operation='revoke'))
        attempt = lambda: metadata.request_repository(node.access, value)
    before = state(node)
    original = getattr(metadata.MetadataTransaction, method)

    def kill(self, *args):
        original(self, *args)
        with node.access.enrollment_repository.connect() as killer:
            pid = self.database.execute('SELECT pg_backend_pid() AS pid').fetchone()['pid']
            assert killer.execute('SELECT pg_terminate_backend(%s,1000) AS stopped', (pid,)).fetchone()['stopped']
        self.database.execute('SELECT 1')

    with monkeypatch.context() as patch:
        patch.setattr(metadata.MetadataTransaction, method, kill)
        with pytest.raises(psycopg.OperationalError):
            attempt()
    assert state(node) == before
    attempt()


def test_postgres_truncate_cannot_discard_tombstones(postgres_node):
    import psycopg
    submit(postgres_node, report(operation='revoke'))
    before = state(postgres_node)
    with pytest.raises(psycopg.errors.CheckViolation):
        with postgres_node.access.enrollment() as enrollment:
            enrollment.database.execute('TRUNCATE device_metadata')
    assert state(postgres_node) == before


def test_legacy_minimal_access_api_and_file_failure_keep_existing_boundary(legacy_setup, monkeypatch):
    access, device, path, clock = legacy_setup
    value = request_value(access, device, legacy_report())
    minimal = SimpleNamespace(path=access.path, complete=access.complete, clock=access.clock)
    original = metadata.MetadataTransaction.save

    def fail(self, *args):
        original(self, *args)
        raise RuntimeError('synthetic separate file failure')

    with monkeypatch.context() as patch:
        patch.setattr(metadata.MetadataTransaction, 'save', fail)
        with pytest.raises(RuntimeError, match='synthetic separate file failure'):
            metadata.request(minimal, path, value)
    assert metadata.read_all(path, clock[0]) == []
    with pytest.raises(Rejected):
        metadata.request(minimal, path, value)
    response = metadata.request(minimal, path, request_value(access, device, legacy_report()))
    assert response['consent'] == 'enabled' and path.stat().st_mode & 0o777 == 0o600
