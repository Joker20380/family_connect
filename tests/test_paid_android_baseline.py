import json

import pytest

from control.friends import paid_beta
from test_paid_beta_readiness import paid_setup, payment


def support_observation(setup, code, offset=0, version=None):
    service, device, _, now = setup
    with service.access.db() as database:
        database.execute('UPDATE device_support SET app_version=?,version_code=?,last_seen=? WHERE device=?',
            (version or f'0.1.18-beta{code}', code, now + offset, device.reference))


def ack_observation(setup, value, offset=0, number=1):
    service, device, _, now = setup
    with service.access.db() as database:
        database.execute('INSERT INTO restricted_readiness_results(nonce,correlation,device,challenge_at,ack,ack_at) VALUES (?,?,?,?,?,?)',
            (f'{number:064x}', f'{number:032x}', device.reference, now - 10, json.dumps(value), now + offset))


def assert_denied(setup, reason='ANDROID_BASELINE_REQUIRED'):
    with pytest.raises(paid_beta.PaidBetaError, match=reason):
        payment(setup)
    with paid_beta.connection(setup[0].access.path) as database:
        for table in sorted(paid_beta.TABLES):
            assert database.execute('SELECT count(*) FROM ' + table).fetchone()[0] == 0


def test_exact108_support_and_hash_accept_without_schema_or_registry_migration(paid_setup):
    assert paid_beta.PAID_ANDROID_VERSION == '0.1.18-beta108'
    assert paid_beta.PAID_ANDROID_VERSION_CODE == 108
    assert paid_beta.PAID_ANDROID_APK_SHA256 == '144b158fe4c07dd19a67683887558cf88a0202b937d135a9924698ffc11b4fdf'
    assert paid_beta.COHORT_LIMIT == 10
    service, device, _, _ = paid_setup
    with paid_beta.connection(service.access.path) as database:
        schema = list(database.execute('SELECT type,name,sql FROM sqlite_master ORDER BY type,name'))
        preserved = {table: list(database.execute('SELECT * FROM ' + table))
                     for table in ('devices', 'invites', 'restricted_grants', 'device_support')}
        paid_beta.confirm_android_baseline(database, device.reference)
    assert payment(paid_setup)['event']['result'] == 'APPLIED'
    with paid_beta.connection(service.access.path) as database:
        assert list(database.execute('SELECT type,name,sql FROM sqlite_master ORDER BY type,name')) == schema
        assert all(list(database.execute('SELECT * FROM ' + table)) == rows for table, rows in preserved.items())


@pytest.mark.parametrize('old_code', [106, 107])
def test_newer_exact108_ack_supersedes_older_support(paid_setup, old_code):
    support_observation(paid_setup, old_code, -60)
    ack_observation(paid_setup, dict(app_version='0.1.18-beta108', version_code=108))
    assert payment(paid_setup)['event']['result'] == 'APPLIED'


@pytest.mark.parametrize('old_code', [106, 107])
@pytest.mark.parametrize('source', ['support', 'ack'])
def test_newer_old_version_rejects_stale108(paid_setup, old_code, source):
    ack_observation(paid_setup, dict(app_version='0.1.18-beta108', version_code=108), -60)
    if source == 'support':
        support_observation(paid_setup, old_code, 1)
    else:
        ack_observation(paid_setup, dict(app_version=f'0.1.18-beta{old_code}', version_code=old_code), 1, 2)
    assert_denied(paid_setup)


@pytest.mark.parametrize('code', [106, 107])
def test_latest_old_support_rejected(paid_setup, code):
    support_observation(paid_setup, code)
    assert_denied(paid_setup)


def test_missing_observation_rejected(paid_setup):
    with paid_setup[0].access.db() as database:
        database.execute('UPDATE device_support SET last_seen=NULL')
    assert_denied(paid_setup)


@pytest.mark.parametrize('observation', [
    {}, dict(app_version='0.1.18-beta108'), dict(version_code=108),
    dict(app_version='0.1.18-beta108', version_code='108'),
    dict(app_version='0.1.18-beta108', version_code=True),
    dict(app_version='0.1.18-beta108-other', version_code=108),
])
def test_latest_inexact_or_missing_version_rejected(paid_setup, observation):
    ack_observation(paid_setup, observation, 1)
    assert_denied(paid_setup)


@pytest.mark.parametrize('reverse', [False, True])
def test_all_latest_ack_ties_checked_not_arbitrary_first(paid_setup, reverse):
    support_observation(paid_setup, 106, -60)
    codes = [107, 108] if reverse else [108, 107]
    for number, code in enumerate(codes, 1):
        ack_observation(paid_setup, dict(app_version=f'0.1.18-beta{code}', version_code=code), number=number)
    assert_denied(paid_setup)


def test_support_ack_tie_conflict_rejected(paid_setup):
    support_observation(paid_setup, 107)
    ack_observation(paid_setup, dict(app_version='0.1.18-beta108', version_code=108))
    assert_denied(paid_setup)


def test_agreeing_latest_observations_accepted(paid_setup):
    for number in (1, 2):
        ack_observation(paid_setup, dict(app_version='0.1.18-beta108', version_code=108), number=number)
    assert payment(paid_setup)['event']['result'] == 'APPLIED'


def test_malformed_stale_ack_does_not_override_latest_support(paid_setup):
    ack_observation(paid_setup, ['malformed'], -60)
    assert payment(paid_setup)['event']['result'] == 'APPLIED'


def test_malformed_latest_ack_rejected(paid_setup):
    ack_observation(paid_setup, ['malformed'], 1)
    assert_denied(paid_setup, 'INVALID_VERSION_OBSERVATION')
