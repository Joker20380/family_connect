from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import sqlite3

import pytest

from control.friends import paid_beta, support_ids
from control.friends.access import Access
from device_identity.device import DeviceIdentity

NOW = 1800000000


def activated_device(access, *, code=106):
    device = DeviceIdentity.generate()
    challenge = access.challenge(device.public_identity, device.wireguard_public_key, 'activate', access.invite())
    access.complete(device.prove_transport_key(challenge['challenge']), 'activate')
    with access.db() as database:
        support = support_ids.registered(database, device.reference)
        database.execute('UPDATE device_support SET platform=?,app_version=?,version_code=?,last_seen=? WHERE device=?',
            ('android', paid_beta.VERSION if code == 106 else '0.1.18-beta84', code, NOW, device.reference))
    return device, support


@pytest.fixture
def registry(tmp_path):
    access = Access(tmp_path / 'access.db', clock=lambda: NOW)
    access.initialize()
    device, support = activated_device(access)
    with paid_beta.connection(access.path, write=True) as database:
        paid_beta.migrate(database)
    return access, device, support


def event(registry, kind='payment', event_id='event-00000001', *, now=NOW, **values):
    access, _, support = registry
    if kind == 'payment':
        values = dict(period_start=now, paid_until=now + 3600, apk_sha256=paid_beta.APK_SHA256) | values
    with paid_beta.connection(access.path, write=True) as database:
        return paid_beta.apply_event(database, support, kind, event_id, 'synthetic-receipt', now=now, **values)


def snapshot(access):
    with paid_beta.connection(access.path) as database:
        return {table: [tuple(row) for row in database.execute('SELECT * FROM ' + table + ' ORDER BY 1')]
                for table in ('devices', 'invites', 'device_support', 'paid_beta_subscriptions', 'paid_beta_events')}


def test_migration_idempotent_empty_cohort_preserves_registry(registry):
    access, device, _ = registry
    before = snapshot(access)
    with paid_beta.connection(access.path, write=True) as database:
        paid_beta.migrate(database)
        paid_beta.migrate(database)
        assert not list(database.execute('PRAGMA foreign_key_check'))
        assert paid_beta.effective_subscription_state(database, device.reference, NOW) is None
    assert snapshot(access) == before


def test_missing_schema_is_legacy_partial_schema_fails_closed(tmp_path):
    access = Access(tmp_path / 'access.db', clock=lambda: NOW)
    access.initialize()
    device, _ = activated_device(access)
    with paid_beta.connection(access.path, write=True) as database:
        assert paid_beta.effective_subscription_state(database, device.reference, NOW) is None
        database.execute('CREATE TABLE paid_beta_events (event_id TEXT)')
        with pytest.raises(paid_beta.PaidBetaError, match='INCOMPLETE'):
            paid_beta.effective_subscription_state(database, device.reference, NOW)


@pytest.mark.parametrize('state,offset,allowed,effective', [
    ('active', 3599, True, 'active'), ('active', 3600, False, 'expired'),
    ('trial', 3599, True, 'trial'), ('trial', 3600, False, 'expired'),
    ('grace', 7199, True, 'grace'), ('grace', 7200, False, 'expired'),
    ('expired', 0, False, 'expired'), ('revoked', 0, False, 'revoked'),
    ('revoked', 8000, False, 'revoked'), ('active', 4000, False, 'expired'),
])
def test_effective_state_exclusive_boundaries(registry, state, offset, allowed, effective):
    access, device, _ = registry
    event(registry)
    with paid_beta.connection(access.path, write=True) as database:
        database.execute('UPDATE paid_beta_subscriptions SET state=?,grace_until=?,revoked_at=? WHERE device=?',
            (state, NOW + 7200, NOW if state == 'revoked' else None, device.reference))
        result = paid_beta.effective_subscription_state(database, device.reference, NOW + offset)
        assert (result.state, result.allowed) == (effective, allowed)
        assert result.expires_at == (NOW + (7200 if state == 'grace' else 3600) if allowed else None)
    before = snapshot(access)
    with paid_beta.connection(access.path) as database:
        paid_beta.effective_subscription_state(database, device.reference, NOW + 10000)
    assert snapshot(access) == before


def test_payment_atomic_hash_only_audit_and_replay(registry):
    access, device, support = registry
    original = snapshot(access)
    first = event(registry)
    before = snapshot(access)
    duplicate = event(registry)
    assert duplicate['duplicate'] and duplicate['event'] == first['event']
    with paid_beta.connection(access.path, write=True) as database:
        late = paid_beta.apply_event(database, support, 'payment', 'event-00000001', 'synthetic-receipt', now=NOW + 9999,
            period_start=NOW, paid_until=NOW + 3600, apk_sha256=paid_beta.APK_SHA256)
    assert late['duplicate'] and snapshot(access) == before
    assert first['event']['reference_hash'] == hashlib.sha256(b'synthetic-receipt').hexdigest()
    assert first['event']['previous_state'] is None and first['event']['new_state'] == 'active'
    for table in ('devices', 'invites', 'device_support'):
        assert snapshot(access)[table] == original[table]
    with paid_beta.connection(access.path) as database:
        raw = '\n'.join(database.iterdump())
        paid = json.dumps({table: before[table] for table in paid_beta.TABLES})
        assert support not in paid and 'synthetic-receipt' not in raw
        assert paid_beta.status(database, support, NOW)['entitlement_until'] == NOW + 3600
    assert device.reference == first['event']['device']


@pytest.mark.parametrize('change', ['reference', 'device', 'paid_until', 'event_type'])
def test_reused_event_id_conflict_has_no_mutation(registry, change):
    access, _, support = registry
    event(registry)
    if change == 'device':
        _, support = activated_device(access)
    before = snapshot(access)
    with pytest.raises(paid_beta.PaidBetaError, match='EVENT_ID_CONFLICT'):
        with paid_beta.connection(access.path, write=True) as database:
            if change == 'event_type':
                paid_beta.apply_event(database, support, 'revoke', 'event-00000001', 'synthetic-receipt', now=NOW)
            else:
                paid_beta.apply_event(database, support, 'payment', 'event-00000001', 'other' if change == 'reference' else 'synthetic-receipt',
                    now=NOW, period_start=NOW, paid_until=NOW + (7200 if change == 'paid_until' else 3600), apk_sha256=paid_beta.APK_SHA256)
    assert snapshot(access) == before


def test_event_and_subscription_rollback_together(registry):
    access, _, _ = registry
    with paid_beta.connection(access.path, write=True) as database:
        database.execute("CREATE TRIGGER synthetic_failure BEFORE INSERT ON paid_beta_subscriptions BEGIN SELECT RAISE(ABORT,'synthetic'); END")
    before = snapshot(access)
    with pytest.raises(sqlite3.IntegrityError):
        event(registry)
    assert snapshot(access) == before


def test_concurrent_duplicate_applies_once(registry):
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: event(registry), range(2)))
    assert sorted(result['duplicate'] for result in results) == [False, True]
    access, _, _ = registry
    assert len(snapshot(access)['paid_beta_events']) == 1
    with paid_beta.connection(access.path) as database:
        assert database.execute('SELECT version FROM paid_beta_subscriptions').fetchone()[0] == 1


def test_concurrent_tenth_slot_and_full_cohort_renewal(registry):
    access, _, _ = registry
    members = [registry]
    for _ in range(10):
        device, support = activated_device(access)
        members.append((access, device, support))
    for number, member in enumerate(members[:9]):
        event(member, event_id=f'payment-{number:08d}')
    def attempt(number):
        try:
            return event(members[number], event_id=f'payment-{number:08d}')['event']['result']
        except paid_beta.PaidBetaError as error:
            return str(error)
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(attempt, (9, 10))) == ['APPLIED', 'COHORT_LIMIT']
    event(registry, event_id='renewal-00000001', now=NOW + 60)
    assert len(snapshot(access)['paid_beta_subscriptions']) == 10
    assert len(snapshot(access)['paid_beta_events']) == 11


def test_foreign_keys_audit_and_cohort_cannot_be_removed(registry):
    access, device, _ = registry
    event(registry)
    for statement in ('DELETE FROM paid_beta_events', "UPDATE paid_beta_events SET result='APPLIED'",
                      'DELETE FROM paid_beta_subscriptions', "UPDATE paid_beta_subscriptions SET device='" + 'f' * 32 + "'"):
        with pytest.raises(sqlite3.IntegrityError):
            with paid_beta.connection(access.path, write=True) as database:
                database.execute(statement)
    with pytest.raises(sqlite3.IntegrityError):
        with paid_beta.connection(access.path, write=True) as database:
            database.execute('INSERT INTO paid_beta_subscriptions VALUES (?,?,?,?,?,?,?,?,?,?)',
                ('f' * 32, 'active', NOW, NOW + 3600, None, NOW, NOW, 1, 'foreign-event', None))
    with paid_beta.connection(access.path) as database:
        assert database.execute('SELECT device FROM paid_beta_subscriptions').fetchone()[0] == device.reference


def test_expire_grace_reactivate_revoke_terminal_and_no_automatic_trial(registry):
    access, _, support = registry
    event(registry)
    event(registry, 'expire', 'expire-00000001')
    with paid_beta.connection(access.path) as database:
        assert not paid_beta.status(database, support, NOW)['paid_allow']
    event(registry, 'grace', 'grace-00000001', grace_until=NOW + 7200)
    with paid_beta.connection(access.path) as database:
        assert paid_beta.status(database, support, NOW)['effective_state'] == 'grace'
    with paid_beta.connection(access.path, write=True) as database:
        paid_beta.apply_event(database, support, 'payment', 'payment-00000002', 'receipt', now=NOW,
            period_start=NOW, paid_until=NOW + 10000, apk_sha256=paid_beta.APK_SHA256)
    event(registry, 'revoke', 'revoke-00000001')
    before = snapshot(access)
    for kind, values in [('payment', {}), ('grace', dict(grace_until=NOW + 20000)), ('expire', {})]:
        with pytest.raises(paid_beta.PaidBetaError, match='REVOCATION_TERMINAL'):
            event(registry, kind, 'terminal-' + kind, **values)
    with pytest.raises(paid_beta.PaidBetaError, match='INVALID_EVENT_TYPE'):
        event(registry, 'trial', 'trial-00000001')
    assert snapshot(access) == before
    assert event(registry, 'revoke', 'revoke-00000001')['duplicate']


@pytest.mark.parametrize('mutation', [
    'UPDATE devices SET revoked=1', 'UPDATE invites SET revoked=1', 'DELETE FROM invites',
    "UPDATE device_support SET version_code=84,app_version='0.1.18-beta84'",
    "UPDATE device_support SET platform='linux'", 'UPDATE device_support SET last_seen=NULL',
])
def test_existing_active_android106_only(registry, mutation):
    access, _, _ = registry
    with access.db() as database:
        database.execute(mutation)
    before = snapshot(access)
    with pytest.raises(paid_beta.PaidBetaError):
        event(registry)
    assert snapshot(access) == before


@pytest.mark.parametrize('kind,values', [('grace', dict(grace_until=NOW + 7200)), ('expire', {}), ('revoke', {})])
def test_only_payment_enrolls(registry, kind, values):
    with pytest.raises(paid_beta.PaidBetaError, match='COHORT_ENROLLMENT_REQUIRES_PAYMENT'):
        event(registry, kind, **values)


@pytest.mark.parametrize('value', ['2027-01-15T08:00:00', '2027-01-15T08:00:00+01:00', '2027-02-31T00:00:00Z',
                                  '2027-01-15T08:00:00.1Z', '1970-01-01T00:00:00Z extra', None])
def test_utc_parser_is_strict(value):
    with pytest.raises(paid_beta.PaidBetaError):
        paid_beta.parse_utc(value)


@pytest.mark.parametrize('now', [True, -1, 1.5, '1000', None, paid_beta.MAX_TIME + 1])
def test_server_clock_is_strict(registry, now):
    access, device, _ = registry
    with paid_beta.connection(access.path) as database, pytest.raises(paid_beta.PaidBetaError):
        paid_beta.effective_subscription_state(database, device.reference, now)


@pytest.mark.parametrize('values', [
    dict(apk_sha256='0' * 64), dict(paid_until=NOW), dict(period_start=NOW + 1),
    dict(period_start=NOW + 3600), dict(paid_until=True), dict(grace_until=NOW + 7200),
    dict(event_id='short'), dict(event_id='payment-FC-2222-2222'),
])
def test_invalid_payment_cannot_enroll_or_write_audit(registry, values):
    before = snapshot(registry[0])
    with pytest.raises(paid_beta.PaidBetaError):
        event(registry, **values)
    assert snapshot(registry[0]) == before


@pytest.mark.parametrize('kind,values', [
    ('payment', dict(paid_until=NOW + 1800)),
    ('payment', dict(period_start=NOW - 1)),
    ('grace', dict(grace_until=NOW + 1800)),
])
def test_operator_cannot_shorten_existing_paid_boundary(registry, kind, values):
    event(registry)
    before = snapshot(registry[0])
    with pytest.raises(paid_beta.PaidBetaError, match='MUST_NOT_SHORTEN'):
        event(registry, kind, 'event-shortened-0001', **values)
    assert snapshot(registry[0]) == before
