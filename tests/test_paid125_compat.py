import base64
import json
from pathlib import Path

import pytest

from control.friends import paid_beta
from test_paid_android_baseline import ack_observation, paid_setup, support_observation
from test_paid_beta import NOW, event, registry, snapshot
from test_paid_release_policy import set_release
from test_paid123_package import activation, invoke, own_subscription, projection, setup, utc
from test_paid_policy_package import packages
from test_friends_http_runtime import running, runtime


RELEASE = next(item for item in paid_beta.PAID_ANDROID_RELEASES if item.version_code == 125)


def test_public_android_descriptor_is_exactly_admitted_by_paid_policy():
    root = Path(__file__).resolve().parents[1]
    envelope = json.loads((root / 'updates/android-friends-v2.json').read_text())
    public = json.loads(base64.b64decode(envelope['payload'], validate=True))
    assert public['package'] == 'com.familyconnect.app.friends'
    descriptor = paid_beta.AndroidRelease('android', public['version'], public['version_code'], public['sha256'])
    assert descriptor in paid_beta.PAID_ANDROID_RELEASES


@pytest.mark.parametrize('latest', ['support', 'ack'])
def test_latest125_observation_wins_over_stale_supported_and_unknown(paid_setup, latest):
    service, device, support, now = paid_setup
    support_observation(paid_setup, 125 if latest == 'support' else 999, 1 if latest == 'support' else -1)
    ack_observation(paid_setup, dict(app_version='0.1.18-beta108', version_code=108), -2)
    code = 999 if latest == 'support' else 125
    ack_observation(paid_setup, dict(app_version=f'0.1.18-beta{code}', version_code=code),
                    -1 if latest == 'support' else 1, number=2)
    result = event((service.access, device, support), now=now, apk_sha256=RELEASE.apk_sha256)
    assert result['event']['result'] == 'APPLIED'


@pytest.mark.parametrize('version,code,apk,reason', [
    ('0.1.18-beta125', 125, '0' * 64, 'APK_INVALID'),
    ('0.1.18-beta125', 123, RELEASE.apk_sha256, 'BASELINE_REQUIRED'),
    ('0.1.18-beta123', 125, RELEASE.apk_sha256, 'BASELINE_REQUIRED'),
    ('0.1.18-beta125', '125', RELEASE.apk_sha256, 'BASELINE_REQUIRED'),
    ('0.1.18-beta126', 126, RELEASE.apk_sha256, 'BASELINE_REQUIRED'),
])
def test_inexact125_rejected_without_mutation(paid_setup, version, code, apk, reason):
    service, device, support, now = paid_setup
    ack_observation(paid_setup, dict(app_version=version, version_code=code), 1)
    before = snapshot(service.access)
    with pytest.raises(paid_beta.PaidBetaError, match=reason):
        event((service.access, device, support), now=now, apk_sha256=apk)
    assert snapshot(service.access) == before


def test_active_access_does_not_depend_on_apk_eligibility(registry):
    set_release(registry, 125)
    event(registry, apk_sha256=RELEASE.apk_sha256)
    set_release(registry, 999)
    with paid_beta.connection(registry[0].path) as database:
        assert paid_beta.effective_subscription_state(database, registry[1].reference, NOW).allowed
        assert not paid_beta.effective_subscription_state(database, registry[1].reference, NOW + 3600).allowed


def test_actual125_packages_first_payment_renewal_grace_and_period_guards(setup):
    runtime, http, operator, support, now = setup
    access = runtime['access']
    with access.db() as database:
        database.execute('UPDATE device_support SET app_version=?,version_code=?', (RELEASE.version_name, 125))
    before = snapshot(access)
    with running(runtime):
        for revision, command in enumerate([
            activation(support, now, code=125),
            activation(support, now, code=125, event='renewal125', until=now + 7200),
            ['grace', '--support-id', support, '--event-id', 'grace125', '--reference', 'synthetic-only',
             '--grace-until', utc(now + 10800)],
        ], 1):
            assert invoke(operator, access.path, command)['event']['result'] == 'APPLIED'
            own = own_subscription(runtime)
            observed = projection(http, access.path)
            assert own['subscription']['version'] == revision
            assert len(observed['history']['events']) == revision
            assert any(not row['cohort'] for row in observed['devices'])
        protected = snapshot(access)
        invoke(operator, access.path, activation(support, now, code=125, event='shorten125'), reason='PAYMENT_MUST_NOT_SHORTEN')
        invoke(operator, access.path, ['grace', '--support-id', support, '--event-id', 'short-grace125',
               '--reference', 'synthetic-only', '--grace-until', utc(now + 8000)], reason='GRACE_MUST_NOT_SHORTEN')
        assert snapshot(access) == protected
    after = snapshot(access)
    assert all(before[name] == after[name] for name in ('devices', 'invites', 'device_support'))


@pytest.mark.parametrize('old_code', [108, 119, 123])
@pytest.mark.parametrize('terminal', [False, True])
def test_actual_old_payment_and_grace_replay_after125(setup, old_code, terminal):
    runtime, _, operator, support, now = setup
    access = runtime['access']
    with access.db() as database:
        database.execute('UPDATE device_support SET app_version=?,version_code=?', (f'0.1.18-beta{old_code}', old_code))
    payment = activation(support, now, code=old_code)
    original = invoke(operator, access.path, payment, clock=now)
    grace = ['grace', '--support-id', support, '--event-id', 'old-grace125', '--reference', 'synthetic-only',
             '--grace-until', utc(now + 7200)]
    original_grace = invoke(operator, access.path, grace, clock=now)
    with access.db() as database:
        database.execute('UPDATE device_support SET app_version=?,version_code=?', (RELEASE.version_name, 125))
    if terminal:
        invoke(operator, access.path, ['revoke', '--support-id', support, '--event-id', 'terminal125', '--reference', 'synthetic-only'])
    before = snapshot(access)
    assert invoke(operator, access.path, payment, clock=now + 8000) == dict(original, duplicate=True)
    assert invoke(operator, access.path, grace, clock=now + 8000) == dict(original_grace, duplicate=True)
    changed = payment.copy()
    changed[-1] = RELEASE.apk_sha256
    invoke(operator, access.path, changed, reason='EVENT_ID_CONFLICT')
    if terminal:
        invoke(operator, access.path, activation(support, now, code=125, event='after-revoke125', until=now + 9000),
               reason='REVOCATION_TERMINAL')
    assert snapshot(access) == before
