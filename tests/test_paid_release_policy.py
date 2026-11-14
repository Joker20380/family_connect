import hashlib
import itertools
import json

import pytest

from control.friends import paid_beta, paid_beta_canary
from test_paid_android_baseline import ack_observation, paid_setup, support_observation
from test_paid_beta import NOW, event, registry, snapshot
from test_paid_beta_canary_operator import KEY, envelope
from test_paid_canary_crl import operation


def set_release(registry, code):
    access, device, _ = registry
    with access.db() as database:
        database.execute('UPDATE device_support SET app_version=?,version_code=? WHERE device=?',
                         (f'0.1.18-beta{code}', code, device.reference))


def test_exact_signed_release_descriptors_only():
    assert [(item.platform, item.version_name, item.version_code, item.apk_sha256)
            for item in paid_beta.PAID_ANDROID_RELEASES] == [
        ('android', '0.1.18-beta108', 108, '144b158fe4c07dd19a67683887558cf88a0202b937d135a9924698ffc11b4fdf'),
        ('android', '0.1.18-beta119', 119, '52a9847b74181c48808c86a0c5bf5925b53ef498eec628aef2d78d26f1c92d2d'),
        ('android', '0.1.18-beta123', 123, 'ae011307b4afc58ea211ea6c5cd27c28bc472bda6af9b19892de400a3d3de15d'),
        ('android', '0.1.18-beta125', 125, 'f1c5bf578a5ca1e8e864a60fa9ab33249807e22c4552b5da984d126720e5740c'),
    ]
    assert paid_beta.LEGACY_ANDROID_RELEASE == paid_beta.PAID_ANDROID_RELEASES[0]
    assert paid_beta.policy()['policy'] == 'android-paid-108-119-123-125-v1'


@pytest.mark.parametrize('release', paid_beta.PAID_ANDROID_RELEASES)
def test_new_payment_and_grace_match_explicit_release(registry, release):
    set_release(registry, release.version_code)
    before = snapshot(registry[0])
    applied = event(registry, apk_sha256=release.apk_sha256)
    assert applied['event']['result'] == 'APPLIED'
    assert event(registry, 'grace', 'event-grace-policy', grace_until=NOW + 7200)['event']['event_type'] == 'grace'
    after = snapshot(registry[0])
    assert all(before[name] == after[name] for name in ('devices', 'invites', 'device_support'))


@pytest.mark.parametrize('code,apk', [(108, paid_beta.PAID_ANDROID_RELEASES[1].apk_sha256),
    (119, paid_beta.PAID_ANDROID_APK_SHA256), (120, paid_beta.PAID_ANDROID_RELEASES[1].apk_sha256),
    (123, '96a4eaed68ab31313d2d5ace3136998880d2d2fb8a803bde2d30cc17816efcae'),
    (123, paid_beta.PAID_ANDROID_APK_SHA256), (123, paid_beta.PAID_ANDROID_RELEASES[1].apk_sha256),
    (119, paid_beta.PAID_ANDROID_RELEASES[2].apk_sha256),
    *[(code, paid_beta.PAID_ANDROID_RELEASES[2].apk_sha256) for code in (121, 122, 124, 999)]])
def test_wrong_release_hash_or_unknown_version_rejects_without_write(registry, code, apk):
    set_release(registry, code)
    before = snapshot(registry[0])
    with pytest.raises(paid_beta.PaidBetaError, match='APK_INVALID|BASELINE_REQUIRED'):
        event(registry, apk_sha256=apk)
    assert snapshot(registry[0]) == before


@pytest.mark.parametrize('kind', ['payment', 'grace'])
@pytest.mark.parametrize('codes', list(itertools.permutations((108, 119, 123, 125), 2)))
@pytest.mark.parametrize('source', ['support_ack', 'two_acks'])
def test_equally_latest_allowed_versions_conflict(paid_setup, kind, codes, source):
    service, device, support, now = paid_setup
    registry = service.access, device, support
    if kind == 'grace':
        event(registry, now=now)
    support_observation(paid_setup, codes[0] if source == 'support_ack' else 108,
                        0 if source == 'support_ack' else -60)
    if source == 'two_acks':
        ack_observation(paid_setup, dict(app_version=f'0.1.18-beta{codes[0]}', version_code=codes[0]))
    ack_observation(paid_setup, dict(app_version=f'0.1.18-beta{codes[1]}', version_code=codes[1]), number=2)
    before = snapshot(service.access)
    values = dict(grace_until=now + 7200) if kind == 'grace' else {}
    with pytest.raises(paid_beta.PaidBetaError, match='ANDROID_VERSION_CONFLICT'):
        event(registry, kind, 'event-conflict-policy', now=now, **values)
    assert snapshot(service.access) == before


def test_new119_ack_overrides_old108_and_requires119_hash(paid_setup):
    service, device, support, now = paid_setup
    registry = service.access, device, support
    ack_observation(paid_setup, dict(app_version='0.1.18-beta119', version_code=119), 1)
    with pytest.raises(paid_beta.PaidBetaError, match='APK_INVALID'):
        event(registry, now=now)
    assert event(registry, now=now, apk_sha256=paid_beta.PAID_ANDROID_RELEASES[1].apk_sha256)['event']['result'] == 'APPLIED'


@pytest.mark.parametrize('name,code', [('0.1.18-beta119', 108), ('0.1.18-beta108', 119),
    ('0.1.18-beta119', '119'), ('0.1.18-beta120', 120), ('0.1.18-beta123', 119),
    ('0.1.18-beta119', 123), ('0.1.18-beta123', '123'), ('0.1.18-beta124', 124)])
def test_latest_pair_must_match_one_descriptor(paid_setup, name, code):
    service, device, support, now = paid_setup
    ack_observation(paid_setup, dict(app_version=name, version_code=code), 1)
    before = snapshot(service.access)
    with pytest.raises(paid_beta.PaidBetaError, match='ANDROID_BASELINE_REQUIRED'):
        event((service.access, device, support), now=now)
    assert snapshot(service.access) == before


def test_exact108_grace_replay_after_upgrade_expiry_and_revoke(registry):
    event(registry)
    initial = event(registry, 'grace', 'event-grace-policy', grace_until=NOW + 7200)
    set_release(registry, 119)
    event(registry, 'revoke', 'event-revoke-policy')
    before = snapshot(registry[0])
    assert event(registry, 'grace', 'event-grace-policy', now=NOW + 8000,
                 grace_until=NOW + 7200) == dict(initial, duplicate=True)
    assert snapshot(registry[0]) == before


@pytest.mark.parametrize('state', ['active', 'expired', 'explicit_expire', 'revoked', 'identity_revoked'])
def test_exact108_replay_after119_preserves_payload_receipt_and_state(registry, state):
    initial = event(registry)
    payload = dict(device=registry[1].reference, event_type='payment', event_id='event-00000001',
                   period_start=NOW, paid_until=NOW + 3600, grace_until=None,
                   reference_hash=hashlib.sha256(b'synthetic-receipt').hexdigest(),
                   apk_sha256=paid_beta.PAID_ANDROID_APK_SHA256)
    assert initial['event']['payload_hash'] == hashlib.sha256(json.dumps(payload, sort_keys=True,
        separators=(',', ':')).encode()).hexdigest()
    set_release(registry, 119)
    if state in ('explicit_expire', 'revoked'):
        event(registry, 'revoke' if state == 'revoked' else 'expire', 'event-terminal-policy')
    if state == 'identity_revoked':
        with registry[0].db() as database:
            database.execute('UPDATE devices SET revoked=1')
    before = snapshot(registry[0])
    replay = event(registry, now=NOW + (7200 if state == 'expired' else 1),
                   period_start=NOW, paid_until=NOW + 3600)
    assert replay == dict(initial, duplicate=True)
    assert snapshot(registry[0]) == before


@pytest.mark.parametrize('code', [106, 120, 121, 122, 124])
def test_grace_keeps_version_eligibility(registry, code):
    event(registry)
    set_release(registry, code)
    before = snapshot(registry[0])
    with pytest.raises(paid_beta.PaidBetaError, match='BASELINE_REQUIRED'):
        event(registry, 'grace', 'event-grace-policy', grace_until=NOW + 7200)
    assert snapshot(registry[0]) == before


@pytest.mark.parametrize('code', [119, 123])
def test_canary_lookup_and_old_permit_remain108_only(registry, code):
    permit = envelope(registry)
    set_release(registry, code)
    before = snapshot(registry[0])
    with pytest.raises(paid_beta.PaidBetaError, match='BASELINE_REQUIRED'):
        paid_beta_canary.lookup(registry[0].path, registry[2], KEY, NOW)
    with pytest.raises(paid_beta.PaidBetaError, match='APK_INVALID'):
        paid_beta_canary.apply(registry[0].path, KEY, permit, NOW)
    assert snapshot(registry[0]) == before


@pytest.mark.parametrize('code', [119, 123])
def test_crl_canary_precondition_still_requires108(operation, code):
    registry = operation.service.access, operation.device, operation.support
    set_release(registry, code)
    with paid_beta.connection(registry[0].path) as database:
        with pytest.raises(paid_beta.PaidBetaError, match='BASELINE_REQUIRED'):
            operation.engine.preconditions(database, operation.now)
