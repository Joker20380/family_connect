from contextlib import contextmanager
import json
import re

import pytest

from control.friends import paid_beta, support_admin, support_ids
from control.friends.access import Rejected
from control.friends.support_postgres import initialize_synthetic_support
from device_identity.device import DeviceIdentity
from scripts.support_postgres_rehearsal import READSIDE_FIXTURE_DDL
from tests.test_enrollment_repository import access as enrollment_access, parallel, peer, postgres_access
from tests.test_support_ids import proof, request


@pytest.fixture
def access(enrollment_access):
    if enrollment_access.path is None:
        initialize_synthetic_support(enrollment_access.enrollment_repository)
    return enrollment_access


@pytest.fixture
def postgres_support(postgres_access):
    initialize_synthetic_support(postgres_access.enrollment_repository)
    return postgres_access


def enroll(access):
    device = DeviceIdentity.generate()
    access.complete(proof(access, device, 'activate', access.invite()), 'activate')
    with access.enrollment() as transaction:
        support = transaction.registered(device.reference)
    return device, support


def state(access):
    with access.enrollment() as transaction:
        return {table: [dict(row) for row in transaction.database.execute('SELECT * FROM ' + table + ' ORDER BY 1')]
                for table in ('invites', 'devices', 'challenges', 'device_support', 'field_support_audit')}


def readside(access):
    with access.enrollment() as transaction:
        for statement in READSIDE_FIXTURE_DDL:
            transaction.database.execute(statement)


def ack(access, device, *, correlation='receipt', seen=999, raw=None, expires=1001):
    if raw is None:
        raw = json.dumps(dict(app_version='0.1.18-beta58', version_code=58, result='READY'))
    with access.enrollment() as transaction:
        transaction.database.execute('INSERT INTO restricted_readiness_results'
            '(correlation,nonce,device,challenge_at,ack,ack_at,expires) VALUES (' +
            ','.join([transaction.placeholder] * 7) + ')',
            (correlation, correlation, device.reference, 998, raw, seen, expires))


def test_empty_inventory_and_absent_readside_tables(access):
    expected = dict(total=0, non_revoked=0, revoked=0, support_ids=0, platform_known=0,
                    platform_unknown=0, version_known=0, version_unknown=0)
    assert support_ids.inventory(access) == support_ids.backfill(access) == expected
    device, support = enroll(access)
    before = state(access)
    result = support_ids.lookup(access, support.lower(), [])
    assert result['restricted_readiness'] == 'UNKNOWN'
    assert result['family_state'] == 'NOT_PROVISIONED'
    assert result['active'] and not result['field_admission']
    assert state(access) == before


def test_atomic_backfill_preserves_aliases_bindings_and_revoked_devices(access):
    identities = [enroll(access) for index in range(8)]
    access.revoke_device(identities[-1][0].reference)
    with access.enrollment() as transaction:
        transaction.database.execute('DELETE FROM device_support WHERE device=' + transaction.placeholder,
                                     (identities[0][0].reference,))
    before = state(access)
    results = parallel(lambda index: support_ids.backfill(peer(access)), 8)
    expected = dict(total=8, non_revoked=7, revoked=1, support_ids=8, platform_known=0,
                    platform_unknown=8, version_known=0, version_unknown=8)
    assert all(value == expected for value in results)
    after = state(access)
    assert len({row['support_id'] for row in after['device_support']}) == 8
    assert all(re.fullmatch(support_ids.PATTERN, row['support_id']) for row in after['device_support'])
    assert all(row in after['device_support'] for row in before['device_support'])
    for table in before.keys() - {'device_support'}:
        assert before[table] == after[table]


def test_request_proof_is_single_use_and_result_is_safe(access):
    device, support = enroll(access)
    value = request(access, device)
    results = parallel(lambda index: support_ids.request(peer(access), value), 8)
    assert [item for item in results if item is not None] == [dict(schema=1, device_support_id=support)]
    before = state(access)
    with pytest.raises(Rejected):
        support_ids.request(access, value)
    safe = support_ids.lookup(access, support, [])
    assert safe['platform'] == 'android' and safe['version_code'] == 59
    assert safe['last_seen'] == 1000 and safe['observation_source'] == 'support_request'
    assert device.reference not in json.dumps(safe)
    assert state(access) == before


def test_missing_alias_does_not_allocate_or_consume_proof(access):
    device, support = enroll(access)
    value = request(access, device)
    with access.enrollment() as transaction:
        transaction.database.execute('DELETE FROM device_support')
    before = state(access)
    with pytest.raises(RuntimeError, match='Support inventory mismatch'):
        support_ids.request(access, value)
    assert state(access) == before
    support_ids.backfill(access)
    assert support_ids.request(access, value)['device_support_id']


def test_observation_failure_rolls_back_proof_and_metadata(access, monkeypatch):
    device, support = enroll(access)
    value = request(access, device)
    before = state(access)
    original = support_ids.SupportTransaction.observe_request

    def fail_after(self, *args):
        original(self, *args)
        raise RuntimeError('synthetic observation failure')

    with monkeypatch.context() as patch:
        patch.setattr(support_ids.SupportTransaction, 'observe_request', fail_after)
        with pytest.raises(RuntimeError, match='synthetic observation failure'):
            support_ids.request(access, value)
    assert state(access) == before
    assert support_ids.request(access, value) == dict(schema=1, device_support_id=support)


def test_backfill_failure_rolls_back_entire_batch(access, monkeypatch):
    readside(access)
    for index in range(2):
        device, support = enroll(access)
        ack(access, device, correlation=f'receipt-{index}')
    with access.enrollment() as transaction:
        transaction.database.execute('DELETE FROM device_support')
    before = state(access)
    original = support_ids.SupportTransaction.observe_receipt
    calls = []

    def fail_after(self, *args):
        original(self, *args)
        calls.append(True)
        if len(calls) == 2:
            raise RuntimeError('synthetic batch failure')

    with monkeypatch.context() as patch:
        patch.setattr(support_ids.SupportTransaction, 'observe_receipt', fail_after)
        with pytest.raises(RuntimeError, match='synthetic batch failure'):
            support_ids.backfill(access)
    assert state(access) == before
    assert support_ids.backfill(access)['version_known'] == 2


def test_collision_exhaustion_preserves_alias_and_retries(access, monkeypatch):
    first, first_support = enroll(access)
    second, second_support = enroll(access)
    with access.enrollment() as transaction:
        transaction.database.execute('DELETE FROM device_support WHERE device=' + transaction.placeholder, (second.reference,))
    before = state(access)
    characters = first_support[3:].replace('-', '')
    repeated = iter(characters * 32)
    with monkeypatch.context() as patch:
        patch.setattr(support_ids.secrets, 'choice', lambda alphabet: next(repeated))
        with pytest.raises(RuntimeError, match='Support ID allocation unavailable'):
            support_ids.backfill(access)
    assert state(access) == before
    successive = iter(characters + second_support[3:].replace('-', ''))
    with monkeypatch.context() as patch:
        patch.setattr(support_ids.secrets, 'choice', lambda alphabet: next(successive))
        support_ids.backfill(access)
    assert support_ids.lookup(access, first_support, [])['active']
    assert support_ids.lookup(access, second_support, [])['active']


def test_response_loss_requires_fresh_proof_but_preserves_id(access, monkeypatch):
    device, support = enroll(access)
    value = request(access, device)
    original = access.enrollment

    @contextmanager
    def lose_response():
        with original() as transaction:
            yield transaction
        raise RuntimeError('synthetic committed response lost')

    with monkeypatch.context() as patch:
        patch.setattr(access, 'enrollment', lose_response)
        with pytest.raises(RuntimeError, match='synthetic committed response lost'):
            support_ids.request(access, value)
    with pytest.raises(Rejected):
        support_ids.request(peer(access), value)
    assert support_ids.request(access, request(access, device)) == dict(schema=1, device_support_id=support)


def test_readiness_is_not_platform_evidence_or_newer_request_override(access):
    readside(access)
    device, support = enroll(access)
    ack(access, device)
    counts = support_ids.backfill(access)
    assert counts['platform_unknown'] == counts['version_known'] == 1
    with access.enrollment() as transaction:
        with pytest.raises(paid_beta.PaidBetaError, match='ANDROID_BASELINE_REQUIRED'):
            paid_beta.confirmed_android_release(transaction.paid(), device.reference)
    value = dict(request(access, device), app_version='0.1.18-beta126', version_code=126)
    support_ids.request(access, value)
    support_ids.backfill(access)
    safe = support_ids.lookup(access, support, [])
    assert safe['version_code'] == 126 and safe['last_seen'] == 1000
    assert safe['restricted_readiness'] == 'READY'
    with access.enrollment() as transaction:
        assert paid_beta.confirmed_android_release(transaction.paid(), device.reference).version_code == 126
    access.clock = lambda: 1001
    assert support_ids.lookup(access, support, [])['restricted_readiness'] == 'EXPIRED'


@pytest.mark.parametrize('raw,seen', [('[1]', 999), ('null', 999), ('broken', 999), ('{}', 999),
    ('{"app_version":"valid","version_code":true}', 999), ('{"app_version":"bad url","version_code":1}', 999),
    ('{"app_version":"valid","version_code":1}', None), ('{"app_version":"valid","version_code":1}', -1)])
def test_invalid_optional_receipt_is_not_observation(access, raw, seen):
    readside(access)
    device, support = enroll(access)
    ack(access, device, raw=raw, seen=seen)
    assert support_ids.backfill(access)['version_known'] == 0
    assert support_ids.lookup(access, support, [])['restricted_readiness'] == 'UNKNOWN'


def test_receipt_null_order_and_ties_are_backend_independent(access):
    readside(access)
    device, support = enroll(access)
    ack(access, device, correlation='null', seen=None)
    ack(access, device, correlation='b', raw=json.dumps(dict(app_version='b', version_code=2)))
    ack(access, device, correlation='a', raw=json.dumps(dict(app_version='a', version_code=1)))
    support_ids.backfill(access)
    assert support_ids.lookup(access, support, [])['app_version'] == 'a'
    ack(access, device, correlation='latest', seen=1000, raw='[]')
    assert support_ids.lookup(access, support, [])['restricted_readiness'] == 'UNKNOWN'


@pytest.mark.parametrize('revoked', ['device', 'invitation', 'missing-invitation'])
def test_revoked_or_missing_registration_cannot_update(access, revoked):
    device, support = enroll(access)
    value = request(access, device)
    with access.enrollment() as transaction:
        if revoked == 'device':
            transaction.revoke_device(device.reference)
        else:
            statement = 'UPDATE invites SET revoked=1' if revoked == 'invitation' else 'DELETE FROM invites'
            transaction.database.execute(statement + ' WHERE device=' + transaction.placeholder, (device.reference,))
    before = state(access)
    with pytest.raises(Rejected):
        support_ids.request(access, value)
    assert not support_ids.lookup(access, support, [], all_activated=True)['field_admission']
    assert state(access) == before


@pytest.mark.parametrize('grant_state,expected', [('absent', 'ELIGIBLE'), ('active', 'ELIGIBLE'),
    ('expired', 'ELIGIBLE'), ('revoked', 'REVOKED')])
def test_all_activated_lookup_preserves_existing_admission_rules(access, grant_state, expected):
    readside(access)
    device, support = enroll(access)
    if grant_state != 'absent':
        with access.enrollment() as transaction:
            transaction.database.execute('INSERT INTO restricted_grants VALUES (' +
                ','.join([transaction.placeholder] * 5) + ')',
                (device.reference, 'synthetic-only', 1, 999 if grant_state == 'expired' else 1001, int(grant_state == 'revoked')))
    before = state(access)
    safe = support_ids.lookup(access, support, [], all_activated=True)
    assert safe['family_state'] == expected
    assert safe['field_admission'] == (expected == 'ELIGIBLE')
    explicit = support_ids.lookup(access, support, [device.reference])
    assert explicit['field_admission']
    assert explicit['family_state'] == dict(absent='NOT_PROVISIONED', active='ACTIVE', expired='EXPIRED', revoked='REVOKED')[grant_state]
    assert state(access) == before


def test_revoke_and_observation_serialize(access):
    device, support = enroll(access)
    value = request(access, device)
    results = parallel(lambda index: support_ids.request(peer(access), value) if index == 0
                       else peer(access).revoke_device(device.reference), 2)
    safe = support_ids.lookup(access, support, [])
    assert safe['revoked'] and not safe['active']
    assert safe['version_code'] == (None if results[0] is None else 59)
    with pytest.raises(Rejected):
        support_ids.request(access, value)


@pytest.mark.parametrize('field,value', [('platform', 'unknown'), ('app_version', 'bad url'),
    ('version_code', True), ('version_code', 0), ('version_code', 2147483648)])
def test_invalid_request_does_not_consume_proof(access, field, value):
    device, support = enroll(access)
    body = request(access, device)
    before = state(access)
    with pytest.raises(Rejected):
        support_ids.request(access, dict(body, **{field: value}))
    assert state(access) == before
    assert support_ids.request(access, body)['device_support_id'] == support


@pytest.mark.parametrize('mismatch', ['wrong', 'missing'])
def test_postgres_marker_cannot_be_bypassed(postgres_support, mismatch):
    import psycopg
    access = postgres_support
    device, support = enroll(access)
    body = request(access, device)
    before = state(access)
    with access.enrollment() as transaction:
        if mismatch == 'missing':
            transaction.database.execute('DROP TABLE ha_support_schema')
        else:
            transaction.database.execute('UPDATE ha_support_schema SET purpose=%s', ('wrong-purpose',))
    for attempt in (lambda: support_ids.backfill(access), lambda: support_ids.inventory(access),
                    lambda: support_ids.lookup(access, support, []), lambda: support_ids.request(access, body)):
        with pytest.raises(psycopg.errors.UndefinedTable if mismatch == 'missing' else RuntimeError):
            attempt()
    assert state(access) == before


def test_postgres_field_operator_refuses_before_any_file_io(postgres_support, tmp_path, monkeypatch):
    device, support = enroll(postgres_support)
    before = state(postgres_support)
    files = sorted(tmp_path.iterdir())
    monkeypatch.setattr(support_admin.os, 'open', lambda *args, **kwargs: pytest.fail('No FIELD filesystem access allowed'))
    for enabled in (True, False):
        with pytest.raises(NotImplementedError, match='fenced file/grant migration'):
            support_admin.change(postgres_support, tmp_path / 'nonexistent.json', support, enabled, 2000)
    assert sorted(tmp_path.iterdir()) == files
    assert state(postgres_support) == before


def test_postgres_backend_loss_rolls_back_observation_and_proof(postgres_support, monkeypatch):
    import psycopg
    access = postgres_support
    device, support = enroll(access)
    value = request(access, device)
    before = state(access)
    original = support_ids.SupportTransaction.observe_request

    def terminate_after(self, *args):
        original(self, *args)
        with access.enrollment_repository.connect() as killer:
            pid = self.database.execute('SELECT pg_backend_pid() AS pid').fetchone()['pid']
            assert killer.execute('SELECT pg_terminate_backend(%s,1000) AS stopped', (pid,)).fetchone()['stopped']
        self.database.execute('SELECT 1')

    with monkeypatch.context() as patch:
        patch.setattr(support_ids.SupportTransaction, 'observe_request', terminate_after)
        with pytest.raises(psycopg.OperationalError):
            support_ids.request(access, value)
    assert state(access) == before
    assert support_ids.request(access, value)['device_support_id'] == support
