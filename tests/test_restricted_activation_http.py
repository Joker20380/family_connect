import json
import time

from cryptography import x509
from cryptography.hazmat.primitives.serialization import Encoding

from control.friends.restricted import delegation, iso, utc
from device_identity.device import DeviceIdentity
from test_friends_http_runtime import request, running, runtime


def activated_device(runtime):
    device = DeviceIdentity.generate()
    access = runtime['access']
    challenge = access.challenge(device.public_identity, device.wireguard_public_key, 'activate', access.invite())
    access.complete(device.prove_transport_key(challenge['challenge']), 'activate')
    return device


def challenge(runtime, device):
    return request(runtime['backend'], '/friends/restricted-readiness/challenge',
                   body=dict(public_identity=device.public_identity, wireguard_public_key=device.wireguard_public_key))


def enable(runtime):
    (runtime['state'] / 'admission.json').write_bytes(b'{"version":2,"eligibility":"all_activated"}')


def test_packaged_http_new_policy_without_reenrollment_or_grant(runtime):
    device = activated_device(runtime)
    with running(runtime):
        assert challenge(runtime, device)[0] == 403
        enable(runtime)
        status, raw = challenge(runtime, device)
        assert status == 200
        proof = device.prove_transport_key(json.loads(raw)['challenge'])
        status, raw = request(runtime['backend'], '/friends/restricted-readiness', body=proof)
        assert status == 200 and json.loads(raw)['device'] == device.reference
        assert request(runtime['backend'], '/friends/restricted-readiness', body=proof)[0] == 403
        assert challenge(runtime, DeviceIdentity.generate())[0] == 403
        with runtime['access'].db() as database:
            assert database.execute('SELECT COUNT(*) FROM restricted_grants WHERE device=?', (device.reference,)).fetchone()[0] == 0


def test_packaged_http_revocation_between_proof_steps(runtime):
    device = activated_device(runtime)
    enable(runtime)
    with running(runtime):
        status, raw = challenge(runtime, device)
        assert status == 200
        proof = device.prove_transport_key(json.loads(raw)['challenge'])
        with runtime['access'].db() as database:
            database.execute('UPDATE invites SET revoked=1 WHERE device=?', (device.reference,))
        assert request(runtime['backend'], '/friends/restricted-readiness', body=proof)[0] == 403


def test_request_cannot_select_policy_and_invalid_configuration_fails_closed(runtime):
    device = activated_device(runtime)
    with running(runtime):
        body = dict(public_identity=device.public_identity, wireguard_public_key=device.wireguard_public_key,
                    eligibility='all_activated')
        assert request(runtime['backend'], '/friends/restricted-readiness/challenge', body=body)[0] == 400
        (runtime['state'] / 'admission.json').write_bytes(b'{"version":2,"eligibility":"anonymous"}')
        assert challenge(runtime, device)[0] == 503


def test_packaged_http_accepts_current_four_hour_crl(runtime):
    service = runtime['restricted']
    now = int(time.time())
    trust, authority = delegation(service.manifest, service.anchor, now)
    crl = (x509.CertificateRevocationListBuilder().issuer_name(authority.subject)
           .last_update(utc(now - 1)).next_update(utc(now + 14399))
           .add_extension(x509.CRLNumber(2), False).sign(service.signing_key, None))
    (runtime['state'] / 'revocations.pem').write_bytes(crl.public_bytes(Encoding.PEM))
    directory = json.loads(service.seed_source())
    directory.update(issued_at=iso(now - 1), expires_at=iso(now + 14399))
    (runtime['state'] / 'directory.json').write_text(json.dumps(directory))
    runtime['environment']['FC_FRIENDS_RESTRICTED_DELIVERY_LIFETIME'] = '14400'
    device = activated_device(runtime)
    enable(runtime)
    with running(runtime):
        status, raw = challenge(runtime, device)
        assert status == 200
        status, raw = request(runtime['backend'], '/friends/restricted-readiness',
                              body=device.prove_transport_key(json.loads(raw)['challenge']))
        assert status == 200
        delivery = json.loads(raw)
        assert delivery['expires_at'] > now + 3600
        assert delivery['expires_at'] <= min(now + 14400, trust['expires_at'])
