from contextlib import contextmanager
import json
import sqlite3
from types import SimpleNamespace

import pytest

from control.friends.access import Access, Rejected
from control.friends import diagnostics
from control.friends.referrals import RateLimited
from device_identity.device import DeviceIdentity
from scripts.diagnostics_postgres_rehearsal import initialize, report, request_value
from scripts.referral_postgres_rehearsal import NOW, proof
from tests.test_enrollment_repository import access as enrollment_access, parallel, postgres_access


def enroll(access):
    device = DeviceIdentity.generate()
    access.complete(proof(access, device, 'activate', access.invite()), 'activate')
    with access.read_enrollment() as enrollment:
        support = enrollment.diagnostics().fetch('SELECT support_id FROM device_support WHERE device=' +
                                                 enrollment.placeholder, (device.reference,))[0]['support_id']
    return SimpleNamespace(access=access, device=device, support=support)


def setup(access):
    access.clock = lambda: NOW
    initialize(access)
    return enroll(access)


@pytest.fixture
def node(enrollment_access):
    return setup(enrollment_access)


@pytest.fixture
def postgres_node(postgres_access):
    return setup(postgres_access)


def submit(node, value=None):
    return diagnostics.request_repository(node.access, request_value(node.access, node.device, value or report()))


def state(node):
    with node.access.read_enrollment() as enrollment:
        transaction = diagnostics.DiagnosticsTransaction(enrollment.database, enrollment.placeholder)
        return {table: transaction.fetch('SELECT * FROM ' + table + ' ORDER BY 1')
            for table in ('snapshots', 'challenges', 'devices', 'invites', 'device_support')}


@pytest.mark.parametrize('platform', ['android', 'linux', 'windows'])
def test_latest_only_bound_to_support_and_device(node, platform):
    candidate = report(platform=platform)
    assert submit(node, candidate) == dict(schema=1, report_id=candidate['report_id'], stored_at=NOW)
    assert diagnostics.read_repository(node.access, node.support)['report'] == candidate
    other = enroll(node.access)
    assert diagnostics.read_repository(node.access, other.support) is None
    submit(other)
    node.access.clock = lambda: NOW + 60
    submit(node, report(sequence=2))
    rows = state(node)['snapshots']
    assert len(rows) == 2 and set(rows[0]) == {'device', 'support', 'received', 'report'}
    assert diagnostics.read_repository(node.access, node.support)['report']['report_id'] == report(2)['report_id']
    assert diagnostics.read_repository(node.access, other.support)['report'] == report()


def test_proof_binds_raw_bytes_and_is_one_use(node):
    value = request_value(node.access, node.device, report())
    before = state(node)
    with pytest.raises(Rejected):
        diagnostics.request_repository(node.access, value | {'report': value['report'] + ' '})
    assert state(node) == before
    diagnostics.request_repository(node.access, value)
    before = state(node)
    with pytest.raises(Rejected):
        diagnostics.request_repository(node.access, value)
    assert state(node) == before


def test_fresh_proof_semantic_duplicate_preserves_original_receipt_and_ttl(node):
    receipt = submit(node)
    node.access.clock = lambda: NOW + 59
    assert submit(node, dict(reversed(list(report().items())))) == receipt
    assert state(node)['snapshots'][0]['received'] == NOW
    value = request_value(node.access, node.device, report(version_code=127))
    before = state(node)
    with pytest.raises(Rejected):
        diagnostics.request_repository(node.access, value)
    assert state(node) == before


@pytest.mark.parametrize('mode', ['one_proof', 'identical', 'conflict'])
def test_concurrent_requests_serialize_proof_and_report(node, mode):
    values = [request_value(node.access, node.device, report(version_code=126 + (index if mode == 'conflict' else 0)))
              for index in range(6)]
    if mode == 'one_proof':
        values = [values[0]] * 6
    results = parallel(lambda index: diagnostics.request_repository(node.access, values[index]), 6)
    assert sum(result is not None for result in results) == (6 if mode == 'identical' else 1)
    assert len(state(node)['snapshots']) == 1


def test_rate_limit_rolls_back_proof_and_same_proof_can_retry_before_expiry(node):
    submit(node)
    value = request_value(node.access, node.device, report(sequence=2))
    node.access.clock = lambda: NOW + 59
    before = state(node)
    with pytest.raises(RateLimited):
        diagnostics.request_repository(node.access, value)
    assert state(node) == before
    node.access.clock = lambda: NOW + 60
    assert diagnostics.request_repository(node.access, value)['stored_at'] == NOW + 60


def test_global_capacity_counts_devices_and_releases_expired_slots(node, monkeypatch):
    monkeypatch.setattr(diagnostics, 'MAX_DEVICES', 1)
    submit(node)
    other = enroll(node.access)
    value = request_value(node.access, other.device, report())
    before = state(node)
    with pytest.raises(RateLimited):
        diagnostics.request_repository(node.access, value)
    assert state(node) == before
    node.access.clock = lambda: NOW + diagnostics.RETENTION + 1
    submit(other)
    assert len(state(node)['snapshots']) == 1
    assert diagnostics.read_repository(node.access, node.support) is None


def test_retention_exact_boundary_and_read_without_pruning_or_writer(node, monkeypatch):
    submit(node)
    before = state(node)
    with monkeypatch.context() as patch:
        patch.setattr(node.access, 'enrollment', lambda: pytest.fail('Read must not take writer lock'))
        node.access.clock = lambda: NOW + diagnostics.RETENTION
        assert diagnostics.read_repository(node.access, node.support) is not None
        node.access.clock = lambda: NOW + diagnostics.RETENTION + 1
        assert diagnostics.read_repository(node.access, node.support) is None
    assert state(node) == before
    diagnostics.prune_repository(node.access)
    after = state(node)
    assert after.pop('snapshots') == []
    before.pop('snapshots')
    assert after == before
    diagnostics.prune_repository(node.access)


@pytest.mark.parametrize('pruned', [False, True])
def test_existing_snapshot_contract_allows_fresh_signed_resubmission_after_ttl(node, pruned):
    submit(node)
    node.access.clock = lambda: NOW + diagnostics.RETENTION + 1
    if pruned:
        diagnostics.prune_repository(node.access)
    assert submit(node)['stored_at'] == NOW + diagnostics.RETENTION + 1
    assert diagnostics.read_repository(node.access, node.support)['report'] == report()


@pytest.mark.parametrize('method', ['save', 'expire'])
def test_failure_after_report_write_or_prune_rolls_back_everything(node, monkeypatch, method):
    submit(node)
    node.access.clock = lambda: NOW + diagnostics.RETENTION + 1
    value = request_value(node.access, node.device, report(sequence=2))
    before = state(node)
    original = getattr(diagnostics.DiagnosticsTransaction, method)

    def broken(self, *args):
        original(self, *args)
        raise RuntimeError('synthetic diagnostics failure')

    with monkeypatch.context() as patch:
        patch.setattr(diagnostics.DiagnosticsTransaction, method, broken)
        with pytest.raises(RuntimeError, match='synthetic diagnostics failure'):
            diagnostics.request_repository(node.access, value)
    assert state(node) == before
    diagnostics.request_repository(node.access, value)


@pytest.mark.parametrize('committed', [False, True])
def test_commit_failure_and_lost_ack_have_distinct_recovery(node, monkeypatch, committed):
    value = request_value(node.access, node.device, report())
    before = state(node)
    original = node.access.enrollment

    @contextmanager
    def broken():
        with original() as enrollment:
            yield enrollment
            if not committed:
                raise RuntimeError('synthetic before commit')
        raise RuntimeError('synthetic lost ACK')

    with monkeypatch.context() as patch:
        patch.setattr(node.access, 'enrollment', broken)
        with pytest.raises(RuntimeError, match='synthetic'):
            diagnostics.request_repository(node.access, value)
    if committed:
        with pytest.raises(Rejected):
            diagnostics.request_repository(node.access, value)
        node.access.clock = lambda: NOW + 10
        assert submit(node)['stored_at'] == NOW
    else:
        assert state(node) == before
        diagnostics.request_repository(node.access, value)
    assert len(state(node)['snapshots']) == 1


@pytest.mark.parametrize('revocation', ['device', 'invite'])
def test_revoke_after_challenge_refuses_without_consuming_proof(node, revocation):
    value = request_value(node.access, node.device, report())
    with node.access.enrollment() as enrollment:
        enrollment.database.execute('UPDATE ' + ('devices' if revocation == 'device' else 'invites') + ' SET revoked=1')
    before = state(node)
    with pytest.raises(Rejected):
        diagnostics.request_repository(node.access, value)
    assert state(node) == before


@pytest.mark.parametrize('delay', [60, 101])
def test_time_and_proof_expiry_checked_after_wait(node, monkeypatch, delay):
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
        assert diagnostics.request_repository(node.access, value)['stored_at'] == NOW + delay
    else:
        with pytest.raises(Rejected):
            diagnostics.request_repository(node.access, value)
        assert state(node) == before


def test_concurrent_prune_and_new_report_leave_new_report(node):
    submit(node)
    node.access.clock = lambda: NOW + diagnostics.RETENTION + 1
    value = request_value(node.access, node.device, report(sequence=2))
    operations = [lambda: diagnostics.request_repository(node.access, value), lambda: diagnostics.prune_repository(node.access)]
    parallel(lambda index: operations[index](), 2)
    assert diagnostics.read_repository(node.access, node.support)['report'] == report(sequence=2)


def test_concurrent_revoke_and_report_never_accepts_post_revoke_retry(node):
    value = request_value(node.access, node.device, report())
    operations = [lambda: diagnostics.request_repository(node.access, value),
                  lambda: node.access.revoke_device(node.device.reference)]
    parallel(lambda index: operations[index](), 2)
    with pytest.raises(Rejected):
        submit(node)
    assert state(node)['devices'][0]['revoked'] == 1


def test_reopening_repository_preserves_receipts_and_support_binding(node):
    receipt = submit(node)
    node.access = Access(node.access.path, clock=lambda: NOW + 10,
                         enrollment_repository=node.access.enrollment_repository)
    assert submit(node) == receipt
    assert diagnostics.read_repository(node.access, node.support)['report'] == report()


def test_unregistered_device_cannot_obtain_diagnostics_challenge(node):
    device = DeviceIdentity.generate()
    before = state(node)
    with pytest.raises(Rejected):
        request_value(node.access, device, report())
    assert state(node) == before


@pytest.mark.parametrize('mutation', ['consent', 'boolean', 'ip', 'duplicate', 'oversize', 'id', 'unknown'])
def test_validation_rejects_without_consuming_proof(node, mutation):
    value = request_value(node.access, node.device, report())
    candidate = report()
    if mutation == 'consent':
        candidate['consent'] = False
    elif mutation == 'boolean':
        candidate['version_code'] = True
    elif mutation == 'ip':
        candidate['metrics']['ip'] = '203.0.113.1'
    elif mutation == 'id':
        candidate['report_id'] = 'invalid'
    elif mutation == 'unknown':
        candidate['raw_log'] = 'forbidden'
    value['report'] = json.dumps(candidate)
    if mutation == 'duplicate':
        value['report'] = '{"schema":1,' + value['report'][1:]
    elif mutation == 'oversize':
        value['report'] = ' ' * (diagnostics.MAX_REPORT + 1)
    before = state(node)
    with pytest.raises(ValueError):
        diagnostics.request_repository(node.access, value)
    assert state(node) == before


@pytest.mark.parametrize('damage', ['missing', 'wrong'])
def test_schema_gate_refuses_before_proof_use(node, damage):
    import psycopg
    value = request_value(node.access, node.device, report())
    with node.access.enrollment() as enrollment:
        enrollment.database.execute('DROP TABLE ha_diagnostics_schema' if damage == 'missing'
                                    else "UPDATE ha_diagnostics_schema SET purpose='wrong'")
    before = state(node)
    with pytest.raises((RuntimeError, sqlite3.OperationalError, psycopg.errors.UndefinedTable)):
        diagnostics.request_repository(node.access, value)
    assert state(node) == before


def test_legacy_split_store_refuses_canonical_access_before_proof_or_file(node, tmp_path, monkeypatch):
    value = request_value(node.access, node.device, report())
    before = state(node)
    target = tmp_path / 'forbidden.sqlite'
    monkeypatch.setattr(node.access, 'complete', lambda *args, **kwargs: pytest.fail('Proof use before gate'))
    with pytest.raises(NotImplementedError):
        diagnostics.request(node.access, target, value)
    assert not target.exists() and state(node) == before


@pytest.mark.parametrize('method', ['save', 'expire'])
def test_backend_loss_rolls_back_snapshot_and_proof(postgres_node, monkeypatch, method):
    import psycopg
    node = postgres_node
    submit(node)
    node.access.clock = lambda: NOW + diagnostics.RETENTION + 1
    value = request_value(node.access, node.device, report(sequence=2))
    before = state(node)
    original = getattr(diagnostics.DiagnosticsTransaction, method)

    def kill(self, *args):
        original(self, *args)
        with node.access.enrollment_repository.connect() as killer:
            pid = self.database.execute('SELECT pg_backend_pid() AS pid').fetchone()['pid']
            assert killer.execute('SELECT pg_terminate_backend(%s,1000) AS stopped', (pid,)).fetchone()['stopped']
        self.database.execute('SELECT 1')

    with monkeypatch.context() as patch:
        patch.setattr(diagnostics.DiagnosticsTransaction, method, kill)
        with pytest.raises(psycopg.OperationalError):
            diagnostics.request_repository(node.access, value)
    assert state(node) == before
    diagnostics.request_repository(node.access, value)


def test_legacy_failure_keeps_existing_separate_proof_commit(tmp_path, monkeypatch):
    access = Access(tmp_path / 'legacy.sqlite', clock=lambda: NOW)
    access.initialize()
    device = DeviceIdentity.generate()
    access.complete(proof(access, device, 'activate', access.invite()), 'activate')
    value = request_value(access, device, report())
    target = tmp_path / 'diagnostics.sqlite'

    def broken(*args):
        raise RuntimeError('synthetic disk failure')

    with monkeypatch.context() as patch:
        patch.setattr(diagnostics.DiagnosticsTransaction, 'save', broken)
        with pytest.raises(RuntimeError, match='synthetic disk failure'):
            diagnostics.request(access, target, value)
    with pytest.raises(Rejected):
        diagnostics.request(access, target, value)
    response = diagnostics.request(access, target, request_value(access, device, report()))
    assert response['stored_at'] == NOW and target.stat().st_mode & 0o777 == 0o600
    with access.db() as database:
        assert database.execute("SELECT 1 FROM sqlite_master WHERE name='ha_diagnostics_schema'").fetchone() is None
