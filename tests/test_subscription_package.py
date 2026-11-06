import json
import time

import pytest

from control.friends import paid_beta
from messenger.store import Store
from messenger.subscription_view import decode_response
from test_friends_http_runtime import ingress, request, running, runtime


def ownership(runtime, number, purpose='subscription'):
    device = runtime['canary']
    status, raw = request(number, '/friends/challenge', body=dict(
        public_identity=device.public_identity, wireguard_public_key=device.wireguard_public_key,
        purpose=purpose, invitation=''))
    assert status == 200
    return device.prove_transport_key(json.loads(raw)['challenge'])


def protected(runtime):
    with runtime['access'].db() as database:
        names = [row[0] for row in database.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name!='challenges'")]
        return {name: [tuple(row) for row in database.execute('SELECT * FROM ' + name + ' ORDER BY 1')]
                for name in names}


@pytest.mark.parametrize('state', ['outside', 'active', 'expired'])
def test_packaged_http_to_encrypted_projection(runtime, tmp_path, state):
    device = runtime['canary']
    now = int(time.time())
    with runtime['access'].db() as database:
        paid_beta.migrate(database)
        if state != 'outside':
            database.execute('UPDATE device_support SET platform=?,app_version=?,version_code=?,last_seen=? WHERE device=?',
                             ('android', paid_beta.PAID_ANDROID_VERSION, paid_beta.PAID_ANDROID_VERSION_CODE, now, device.reference))
            support = database.execute('SELECT support_id FROM device_support WHERE device=?', (device.reference,)).fetchone()[0]
            paid_beta.apply_event(database, support, 'payment', 'synthetic-package-payment', 'synthetic-reference',
                                  period_start=now, paid_until=now + 3600,
                                  apk_sha256=paid_beta.PAID_ANDROID_APK_SHA256, now=now)
            if state == 'expired':
                paid_beta.apply_event(database, support, 'expire', 'synthetic-package-expired', 'synthetic-reference', now=now)
    before = protected(runtime)
    with running(runtime):
        number = runtime['backend']
        proof = ownership(runtime, number)
        status, raw = request(number, '/friends/device/subscription', body=proof)
        assert status == 200
        assert request(number, '/friends/device/subscription', body=proof)[0] == 403
        assert request(number, '/friends/device/subscription', body=ownership(runtime, number, 'status'))[0] == 403
        forged = ownership(runtime, number)
        forged['device'] = 'another-device'
        assert request(number, '/friends/device/subscription', body=forged)[0] == 403
        registration_status, registration = request(number, '/friends/device/status', body=ownership(runtime, number, 'status'))
        assert registration_status == 200
        assert json.loads(registration) == dict(device=device.reference, registered=True, revoked=False, active=True)
    assert protected(runtime) == before
    confirmed, observed, event = decode_response(raw, device.reference)
    assert observed >= now
    assert b'reference_hash' not in raw and b'payload_hash' not in raw
    store_path, key = tmp_path / 'encrypted', bytes(range(32))
    store = Store(store_path, key, create=True)
    try:
        store.accept_confirmed_subscription(confirmed, device=device.reference, confirmed_at=observed, event=event)
        view = store.subscription_status(device.reference)
        assert view['cohort'] == (state != 'outside')
        if state == 'outside':
            assert view['snapshot'] is None and view['notice'] is None
        else:
            assert view['snapshot']['effective_state'] == state
            assert view['notice']['subscription_event'] == ('activated' if state == 'active' else 'expire')
    finally:
        store.close()
    reopened = Store(store_path, key, create=False)
    try:
        assert reopened.subscription_status(device.reference) == view
        reopened.accept_confirmed_subscription(confirmed, device=device.reference, confirmed_at=observed, event=event)
        assert reopened.subscription_status(device.reference) == view
    finally:
        reopened.close()


def test_packaged_http_subscription_via_standard_ingress(runtime):
    with runtime['access'].db() as database:
        paid_beta.migrate(database)
    with running(runtime), ingress(runtime, True) as number:
        status, raw = request(number, '/friends/device/subscription', body=ownership(runtime, number))
        assert status == 200
        assert decode_response(raw, runtime['canary'].reference)[0]['cohort'] is False
