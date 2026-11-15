import pytest

from control.friends import paid_beta
from test_paid_android_baseline import ack_observation, paid_setup, support_observation
from test_paid_beta import NOW, event, registry, snapshot
from test_paid_release_policy import set_release
from test_paid123_package import activation, invoke, own_subscription, projection, setup, utc
from test_paid_policy_package import packages
from test_friends_http_runtime import running, runtime


RELEASE = next(item for item in paid_beta.PAID_ANDROID_RELEASES if item.version_code == 126)
UNSIGNED126 = '645ef3970cd1264c8d24237752319cb454184fe6fa2ce8cbb6a9ed8a1c2822b1'


@pytest.mark.parametrize('latest', ['support', 'ack'])
def test_latest126_requires_final_signed_bytes(paid_setup, latest):
    service, device, support, now = paid_setup
    support_observation(paid_setup, 126 if latest == 'support' else 125,
                        1 if latest == 'support' else -1)
    ack_observation(paid_setup, dict(app_version=f'0.1.18-beta{125 if latest == "support" else 126}',
                                    version_code=125 if latest == 'support' else 126),
                    -1 if latest == 'support' else 1)
    before = snapshot(service.access)
    with pytest.raises(paid_beta.PaidBetaError, match='APK_INVALID'):
        event((service.access, device, support), now=now, apk_sha256=UNSIGNED126)
    assert snapshot(service.access) == before
    assert event((service.access, device, support), now=now,
                 apk_sha256=RELEASE.apk_sha256)['event']['result'] == 'APPLIED'


@pytest.mark.parametrize('apk', [UNSIGNED126, '0' * 64,
                               *[release.apk_sha256 for release in paid_beta.PAID_ANDROID_RELEASES
                                 if release.version_code != 126]])
def test_unsigned_or_other_release_hash_does_not_admit126(registry, apk):
    set_release(registry, 126)
    before = snapshot(registry[0])
    with pytest.raises(paid_beta.PaidBetaError, match='APK_INVALID'):
        event(registry, apk_sha256=apk)
    assert snapshot(registry[0]) == before


@pytest.mark.parametrize('version,code', [
    ('0.1.18-beta125', 126), ('0.1.18-beta126', 125),
    ('0.1.18-beta126', '126'), ('0.1.18-beta126-other', 126),
    ('0.1.18-beta127', 127),
])
def test_inexact126_version_pair_is_not_admitted(paid_setup, version, code):
    service, device, support, now = paid_setup
    ack_observation(paid_setup, dict(app_version=version, version_code=code), 1)
    before = snapshot(service.access)
    with pytest.raises(paid_beta.PaidBetaError, match='BASELINE_REQUIRED'):
        event((service.access, device, support), now=now, apk_sha256=RELEASE.apk_sha256)
    assert snapshot(service.access) == before


def test_active126_access_stays_independent_of_apk_version(registry):
    set_release(registry, 126)
    event(registry, apk_sha256=RELEASE.apk_sha256)
    set_release(registry, 999)
    with paid_beta.connection(registry[0].path) as database:
        assert paid_beta.effective_subscription_state(database, registry[1].reference, NOW).allowed
        assert not paid_beta.effective_subscription_state(database, registry[1].reference, NOW + 3600).allowed


def test_packaged126_first_payment_renewal_grace_and_replay(setup):
    runtime, http, operator, support, now = setup
    access = runtime['access']
    with access.db() as database:
        database.execute('UPDATE device_support SET app_version=?,version_code=?', (RELEASE.version_name, 126))
    before = snapshot(access)
    commands = [activation(support, now, code=126, event='first126'),
                activation(support, now, code=126, event='renewal126', until=now + 7200),
                ['grace', '--support-id', support, '--event-id', 'grace126', '--reference', 'synthetic-only',
                 '--grace-until', utc(now + 10800)]]
    with running(runtime):
        for revision, command in enumerate(commands, 1):
            original = invoke(operator, access.path, command, clock=now)
            assert original['event']['result'] == 'APPLIED'
            protected = snapshot(access)
            assert invoke(operator, access.path, command, clock=now + 12000) == dict(original, duplicate=True)
            assert snapshot(access) == protected
            assert own_subscription(runtime)['subscription']['version'] == revision
            assert len(projection(http, access.path)['history']['events']) == revision
        protected = snapshot(access)
        changed = commands[1].copy()
        changed[-1] = UNSIGNED126
        invoke(operator, access.path, changed, reason='EVENT_ID_CONFLICT')
        invoke(operator, access.path, activation(support, now, code=126, event='short126'),
               reason='PAYMENT_MUST_NOT_SHORTEN')
        invoke(operator, access.path, ['grace', '--support-id', support, '--event-id', 'short-grace126',
               '--reference', 'synthetic-only', '--grace-until', utc(now + 8000)], reason='GRACE_MUST_NOT_SHORTEN')
        assert snapshot(access) == protected
    after = snapshot(access)
    assert all(before[name] == after[name] for name in ('devices', 'invites', 'device_support'))


@pytest.mark.parametrize('old_code', [108, 119, 123, 125])
@pytest.mark.parametrize('terminal', [False, True])
def test_old_payment_and_grace_replay_after126_preserves_receipts(setup, old_code, terminal):
    runtime, _, operator, support, now = setup
    access = runtime['access']
    with access.db() as database:
        database.execute('UPDATE device_support SET app_version=?,version_code=?',
                         (f'0.1.18-beta{old_code}', old_code))
    payment = activation(support, now, code=old_code)
    original = invoke(operator, access.path, payment, clock=now)
    grace = ['grace', '--support-id', support, '--event-id', 'old-grace126', '--reference', 'synthetic-only',
             '--grace-until', utc(now + 7200)]
    original_grace = invoke(operator, access.path, grace, clock=now)
    with access.db() as database:
        database.execute('UPDATE device_support SET app_version=?,version_code=?', (RELEASE.version_name, 126))
    if terminal:
        invoke(operator, access.path, ['revoke', '--support-id', support, '--event-id', 'terminal126',
               '--reference', 'synthetic-only'])
    before = snapshot(access)
    assert invoke(operator, access.path, payment, clock=now + 8000) == dict(original, duplicate=True)
    assert invoke(operator, access.path, grace, clock=now + 8000) == dict(original_grace, duplicate=True)
    changed = payment.copy()
    changed[-1] = RELEASE.apk_sha256
    invoke(operator, access.path, changed, reason='EVENT_ID_CONFLICT')
    if terminal:
        invoke(operator, access.path, activation(support, now, code=126, event='after-revoke126', until=now + 9000),
               reason='REVOCATION_TERMINAL')
    assert snapshot(access) == before
