from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import sqlite3
import threading

import pytest

from control.friends import paid_beta, subscription, transport_policy
from control.friends.access import Access, Rejected
from control.friends.paid_postgres import initialize_synthetic_paid
from device_identity.device import DeviceIdentity
from test_enrollment_repository import postgres_store

NOW = 1800000000


def new_store(backend, tmp_path):
    if backend == 'postgres':
        access = postgres_store()
        initialize_synthetic_paid(access.enrollment_repository)
    else:
        access = Access(tmp_path / 'paid.sqlite')
        access.initialize()
        with access.db() as database:
            paid_beta.migrate(database)
    access.clock = lambda: NOW
    return access


@pytest.fixture(params=['sqlite', 'postgres'])
def access(request, tmp_path):
    return new_store(request.param, tmp_path)


def activate(access, device=None, code=126):
    device = device or DeviceIdentity.generate()
    challenge = access.challenge(device.public_identity, device.wireguard_public_key, 'activate', access.invite())
    access.complete(device.prove_transport_key(challenge['challenge']), 'activate')
    with access.enrollment() as transaction:
        support = transaction.registered(device.reference)
        placeholder = transaction.placeholder
        transaction.database.execute(f'UPDATE device_support SET platform={placeholder},app_version={placeholder},'
            f'version_code={placeholder},last_seen={placeholder} WHERE device={placeholder}',
            ('android', f'0.1.18-beta{code}', code, NOW, device.reference))
    return device, support


def event(access, support, kind='payment', event_id='synthetic-event-0001', now=NOW, **values):
    if kind == 'payment':
        values = dict(period_start=NOW, paid_until=NOW + 3600,
                      apk_sha256=paid_beta.PAID_ANDROID_RELEASES[-1].apk_sha256) | values
    with access.enrollment() as transaction:
        return paid_beta.apply_event(transaction.paid(), support, kind, event_id, 'synthetic-receipt', now=now, **values)


def proof(access, device):
    challenge = access.challenge(device.public_identity, device.wireguard_public_key, 'subscription')
    return device.prove_transport_key(challenge['challenge'])


def rows(access):
    with access.enrollment() as transaction:
        return {table: [dict(row) for row in transaction.database.execute('SELECT * FROM ' + table + ' ORDER BY 1')]
                for table in ('paid_beta_events', 'paid_beta_subscriptions')}


def parallel(attempt, count):
    barrier = threading.Barrier(count)

    def call(index):
        barrier.wait(timeout=10)
        try:
            return attempt(index)
        except (paid_beta.PaidBetaError, Rejected) as error:
            return error

    with ThreadPoolExecutor(count) as pool:
        return list(pool.map(call, range(count)))


def test_duplicate_ack_loss_and_terminal_revoke(access):
    device, support = activate(access)
    first = event(access, support)
    assert not first['duplicate']
    event(access, support, 'revoke', 'synthetic-revoke-0001')
    before = rows(access)
    duplicate = event(access, support, now=NOW + 7200)
    assert duplicate['duplicate'] and duplicate['event'] == first['event']
    assert rows(access) == before
    with pytest.raises(paid_beta.PaidBetaError, match='REVOCATION_TERMINAL'):
        event(access, support, event_id='synthetic-renew-0002')
    result = subscription.request(access, proof(access, device))
    assert result['subscription']['version'] == 2
    assert result['subscription']['effective_state'] == 'revoked'
    assert result['subscription']['paid_allow'] is False


@pytest.mark.parametrize('kind', ['payment', 'revoke'])
def test_failure_after_ledger_append_rolls_back_every_write(access, monkeypatch, kind):
    device, support = activate(access)
    if kind == 'revoke':
        event(access, support)
    before = rows(access)

    def fail(transaction, record):
        assert transaction.event(record['event_id']) is not None
        raise RuntimeError('synthetic-last-step-failure')

    with monkeypatch.context() as patch:
        patch.setattr(paid_beta.PaidTransaction, 'save_subscription', fail)
        with pytest.raises(RuntimeError, match='synthetic-last-step-failure'):
            event(access, support, kind, 'synthetic-rollback-0001')
    assert rows(access) == before
    assert event(access, support, kind, 'synthetic-rollback-0001')['duplicate'] is False


def test_concurrent_duplicate_event_commits_once(access):
    device, support = activate(access)
    results = parallel(lambda index: event(access, support), 8)
    assert all(isinstance(result, dict) for result in results)
    assert sum(not result['duplicate'] for result in results) == 1
    snapshot = rows(access)
    assert len(snapshot['paid_beta_events']) == 1
    assert snapshot['paid_beta_subscriptions'][0]['version'] == 1


def test_concurrent_payload_conflict_commits_once(access):
    device, support = activate(access)
    results = parallel(lambda index: event(access, support, paid_until=NOW + 3600 + index), 2)
    assert sum(isinstance(result, dict) for result in results) == 1
    assert [str(result) for result in results if isinstance(result, Exception)] == ['EVENT_ID_CONFLICT']
    assert len(rows(access)['paid_beta_events']) == 1


def test_cohort_limit_concurrent_independent_connections(access):
    devices = [activate(access) for index in range(12)]
    results = parallel(lambda index: event(access, devices[index][1], event_id=f'synthetic-cohort-{index:04}'), 12)
    assert sum(isinstance(result, dict) for result in results) == paid_beta.COHORT_LIMIT
    assert all(str(result) == 'COHORT_LIMIT' for result in results if isinstance(result, Exception))
    assert len(rows(access)['paid_beta_events']) == len(rows(access)['paid_beta_subscriptions']) == 10


def test_subscription_proof_is_single_use_across_apis(access):
    device, support = activate(access)
    event(access, support)
    pending = proof(access, device)
    results = parallel(lambda index: subscription.request(access, pending), 8)
    assert sum(isinstance(result, dict) for result in results) == 1
    assert all(isinstance(result, Rejected) for result in results if not isinstance(result, dict))


@pytest.mark.parametrize('failure', ['missing', 'partial', 'columns', 'sql'])
def test_failed_projection_consumes_proof_without_failing_open(access, monkeypatch, failure):
    device, support = activate(access)
    pending = proof(access, device)
    if failure == 'sql':
        def fail(database, device, now):
            database.database.execute('SELECT * FROM nonexistent_synthetic_table')
        monkeypatch.setattr(subscription, 'snapshot', fail)
    else:
        with access.enrollment() as transaction:
            transaction.database.execute('DROP TABLE paid_beta_events')
            if failure == 'missing':
                transaction.database.execute('DROP TABLE paid_beta_subscriptions')
            if failure == 'columns':
                transaction.database.execute('CREATE TABLE paid_beta_events(event_id TEXT)')
    expected = subscription.Unsupported if failure == 'missing' else subscription.Unavailable
    with pytest.raises(expected):
        subscription.request(access, pending)
    with pytest.raises(Rejected):
        subscription.request(access, pending)
    with access.enrollment() as transaction:
        assert transaction.challenge(hashlib.sha256(pending['challenge'].encode()).hexdigest())['used'] == 1


@pytest.mark.parametrize('mutation,reason', [
    ("UPDATE paid_beta_events SET new_state='grace'", 'PAID_EVENT_IMMUTABLE'),
    ('DELETE FROM paid_beta_events', 'PAID_EVENT_IMMUTABLE'),
    ('DELETE FROM paid_beta_subscriptions', 'PAID_COHORT_RETAINED'),
    ("UPDATE paid_beta_subscriptions SET device='different-device'", 'PAID_DEVICE_IMMUTABLE'),
    ("UPDATE paid_beta_subscriptions SET state='active',revoked_at=NULL", 'PAID_REVOKED'),
])
def test_native_immutable_ledger_and_terminal_constraints(access, mutation, reason):
    device, support = activate(access)
    event(access, support)
    if reason == 'PAID_REVOKED':
        event(access, support, 'revoke', 'synthetic-revoke-0001')
    before = rows(access)
    if access.path is None:
        from psycopg import Error
    else:
        Error = sqlite3.Error
    with pytest.raises(Error, match=reason):
        with access.enrollment() as transaction:
            transaction.database.execute(mutation)
    assert rows(access) == before


def test_native_cohort_trigger_guards_direct_writers(access):
    devices = [activate(access) for index in range(12)]

    def insert(index):
        try:
            with access.enrollment() as transaction:
                transaction.paid().save_subscription(dict(device=devices[index][0].reference,
                    new_state='active', period_start=NOW, paid_until=NOW + 3600, grace_until=None,
                    applied_at=NOW, event_id=f'synthetic-direct-{index:04}'))
            return True
        except Exception as error:
            assert 'PAID_COHORT_LIMIT' in str(error)
            return False

    assert sum(parallel(insert, 12)) == 10


def test_noncohort_and_exclusive_expiry_projection(access):
    device, support = activate(access)
    assert subscription.request(access, proof(access, device))['cohort'] is False
    event(access, support)
    event(access, support, 'grace', 'synthetic-grace-0001', grace_until=NOW + 7200)
    for offset, allowed in ((7199, True), (7200, False)):
        with access.enrollment() as transaction:
            result = subscription.snapshot(transaction.paid(), device.reference, NOW + offset)
            assert result['subscription']['paid_allow'] is allowed
            for node in transport_policy.NODES:
                envelope = transport_policy.read_snapshot(transaction.paid(), node, NOW + offset)
                transport_policy.validate(envelope, node, NOW + offset)
                decision = envelope['decisions'][0]
                assert decision['allowed'] is allowed
                assert decision['valid_until'] <= NOW + offset + 120
                if allowed:
                    assert decision['valid_until'] == NOW + 7200


def test_android_latest_observation_and_mesh_revocation(access):
    device, support = activate(access)
    with access.enrollment() as transaction:
        transaction.database.execute('CREATE TABLE restricted_readiness_results(device TEXT,ack TEXT,ack_at BIGINT)')
        placeholder = transaction.placeholder
        transaction.database.execute(f'INSERT INTO restricted_readiness_results VALUES ({placeholder},{placeholder},{placeholder})',
            (device.reference, json.dumps(dict(app_version='0.1.18-beta125', version_code=125)), NOW))
    with pytest.raises(paid_beta.PaidBetaError, match='ANDROID_VERSION_CONFLICT'):
        event(access, support)
    with access.enrollment() as transaction:
        transaction.database.execute('DELETE FROM restricted_readiness_results')
        transaction.database.execute('CREATE TABLE restricted_grants(device TEXT,revoked BIGINT)')
        placeholder = transaction.placeholder
        transaction.database.execute(f'INSERT INTO restricted_grants VALUES ({placeholder},1)', (device.reference,))
    with pytest.raises(paid_beta.PaidBetaError, match='EXISTING_MESH_REVOCATION'):
        event(access, support)
    assert not rows(access)['paid_beta_events']


def test_sqlite_postgres_exact_ledger_and_all_node_projection_parity(tmp_path):
    stores = [new_store(backend, tmp_path) for backend in ('sqlite', 'postgres')]
    device = DeviceIdentity.generate()
    supports = [activate(access, device)[1] for access in stores]
    for access in stores:
        with access.enrollment() as transaction:
            transaction.database.execute("UPDATE devices SET tcp='00000000-0000-4000-8000-000000000001'")
    for kind, values in [('payment', {}), ('grace', dict(grace_until=NOW + 7200)), ('expire', {}), ('revoke', {})]:
        results = [event(access, support, kind, 'synthetic-parity-' + kind, **values)
                   for access, support in zip(stores, supports)]
        assert results[0] == results[1]
        assert rows(stores[0]) == rows(stores[1])
        snapshots = []
        for access in stores:
            with access.enrollment() as transaction:
                snapshots.append((subscription.snapshot(transaction.paid(), device.reference, NOW),
                    [transport_policy.read_snapshot(transaction.paid(), node, NOW) for node in transport_policy.NODES]))
        assert snapshots[0] == snapshots[1]


def test_subscription_snapshot_cannot_split_event_and_revision(access, monkeypatch):
    device, support = activate(access)
    event(access, support)
    pending = proof(access, device)
    reading, release, writing, written = (threading.Event() for index in range(4))
    original = paid_beta.effective_subscription_state

    def held(database, device, now):
        reading.set()
        assert release.wait(3)
        return original(database, device, now)

    def writer():
        writing.set()
        event(access, support, event_id='synthetic-concurrent-renew', paid_until=NOW + 7200)
        written.set()

    monkeypatch.setattr(paid_beta, 'effective_subscription_state', held)
    with ThreadPoolExecutor(2) as executor:
        reader = executor.submit(subscription.request, access, pending)
        try:
            assert reading.wait(2)
            changing = executor.submit(writer)
            assert writing.wait(1) and not written.wait(0.05)
        finally:
            release.set()
        result = reader.result(timeout=5)
        changing.result(timeout=5)
    assert result['subscription']['version'] == 1
    assert result['event']['event_id'] == result['subscription']['last_event_id'] == 'synthetic-event-0001'
    assert result['subscription']['paid_until'] == NOW + 3600
    assert rows(access)['paid_beta_subscriptions'][0]['version'] == 2


@pytest.mark.parametrize('target', ['devices', 'invites'])
def test_identity_revocation_denies_paid_projection_and_new_payment(access, target):
    device, support = activate(access)
    event(access, support)
    pending = proof(access, device)
    with access.enrollment() as transaction:
        transaction.database.execute(f'UPDATE {target} SET revoked=1')
    with pytest.raises(Rejected):
        subscription.request(access, pending)
    with pytest.raises(paid_beta.PaidBetaError, match='ACTIVE_IDENTITY_REQUIRED'):
        event(access, support, event_id='synthetic-after-identity-revoke')
    with access.enrollment() as transaction:
        for node in transport_policy.NODES:
            decision = transport_policy.read_snapshot(transaction.paid(), node, NOW)['decisions'][0]
            assert not decision['identity_allowed'] and not decision['allowed']


def test_postgres_native_cohort_trigger_without_repository_lock(tmp_path):
    access = new_store('postgres', tmp_path)
    from control.friends.paid_postgres import PostgresPaidTransaction
    from psycopg import errors
    repository = access.enrollment_repository
    devices = [activate(access) for index in range(12)]

    def insert(index):
        try:
            with repository.connect() as database:
                repository.configure(database)
                PostgresPaidTransaction(database).save_subscription(dict(device=devices[index][0].reference,
                    new_state='active', period_start=NOW, paid_until=NOW + 3600, grace_until=None,
                    applied_at=NOW, event_id=f'synthetic-direct-{index:04}'))
            return True
        except errors.RaiseException as error:
            assert 'PAID_COHORT_LIMIT' in str(error)
            return False

    assert sum(parallel(insert, 12)) == 10


@pytest.mark.parametrize('mutation,reason', [
    ('TRUNCATE paid_beta_events', 'PAID_EVENT_IMMUTABLE'),
    ('TRUNCATE paid_beta_subscriptions', 'PAID_COHORT_RETAINED'),
])
def test_postgres_truncate_cannot_erase_ledger(tmp_path, mutation, reason):
    access = new_store('postgres', tmp_path)
    from psycopg import errors
    device, support = activate(access)
    event(access, support)
    before = rows(access)
    with pytest.raises(errors.RaiseException, match=reason):
        with access.enrollment() as transaction:
            transaction.database.execute(mutation)
    assert rows(access) == before


def test_postgres_requires_synthetic_paid_marker(tmp_path):
    access = new_store('postgres', tmp_path)
    device, support = activate(access)
    with access.enrollment() as transaction:
        transaction.database.execute("UPDATE ha_paid_schema SET purpose='production-not-authorized'")
    with pytest.raises(paid_beta.PaidBetaError, match='PAID_REHEARSAL_SCHEMA_MISMATCH'):
        event(access, support)
    assert not rows(access)['paid_beta_events']
