import json
import time

import pytest
from cryptography import x509

from control.friends import paid_beta
from test_friends_http_runtime import request, running, runtime


@pytest.mark.parametrize('action', ['expire', 'revoke'])
def test_packaged_http_paid_gate_and_non_cohort_isolation(runtime, action):
    access, device = runtime['access'], runtime['canary']
    now = int(time.time())
    with access.db() as database:
        database.execute('UPDATE device_support SET platform=?,app_version=?,version_code=106,last_seen=? WHERE device=?',
            ('android', paid_beta.VERSION, now, device.reference))
        support = database.execute('SELECT support_id FROM device_support WHERE device=?', (device.reference,)).fetchone()[0]
    (runtime['state'] / 'admission.json').write_text('{"version":2,"eligibility":"all_activated"}')
    with paid_beta.connection(access.path, write=True) as database:
        paid_beta.apply_event(database, support, 'payment', 'payment-http-001', 'opaque-receipt', now=now,
            period_start=now, paid_until=now + 600, apk_sha256=paid_beta.APK_SHA256)
    identity = dict(public_identity=device.public_identity, wireguard_public_key=device.wireguard_public_key)
    with running(runtime):
        status, raw = request(runtime['backend'], '/friends/restricted-readiness/challenge', body=identity)
        assert status == 200
        proof = device.prove_transport_key(json.loads(raw)['challenge'])
        status, raw = request(runtime['backend'], '/friends/restricted-readiness', body=proof)
        assert status == 200 and support.encode() not in raw
        delivery = json.loads(raw)
        assert delivery['expires_at'] == now + 600
        assert x509.load_pem_x509_certificate(delivery['certificate'].encode()).not_valid_after_utc.timestamp() == now + 600
        assert request(runtime['backend'], '/friends/restricted-readiness', body=proof)[0] == 403
        status, raw = request(runtime['backend'], '/friends/restricted-readiness/challenge', body=identity)
        assert status == 200
        pending = device.prove_transport_key(json.loads(raw)['challenge'])
        with paid_beta.connection(access.path, write=True) as database:
            paid_beta.apply_event(database, support, action, 'event-http-' + action, 'opaque-receipt', now=now)
        assert request(runtime['backend'], '/friends/restricted-readiness', body=pending)[0] == 403
        assert request(runtime['backend'], '/friends/restricted-readiness/challenge', body=identity)[0] == 403
        assert request(runtime['backend'], '/friends/restricted-readiness/challenge', body=runtime['identities']['non_canary'][0])[0] == 200
