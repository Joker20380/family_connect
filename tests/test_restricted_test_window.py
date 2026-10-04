import base64
import json

import pytest
from cryptography import x509
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from control.friends.restricted import DOMAIN, RestrictedReadiness, directory, iso, utc
from control.friends.restricted_admin import publish_crl
from test_friends_restricted import configured, proof


def long_window(tmp_path, *, lifetime=14400):
    service, device, now = configured(tmp_path, 1800000000, delivery_lifetime=lifetime,
                                     directory_lifetime=14400)
    target = tmp_path / 'revocations.pem'
    publish_crl(service, target, lifetime=14400)
    service.crl_source = target.read_bytes
    return service, device, now


def test_four_hour_delivery_and_default_opt_in(tmp_path):
    service, device, now = long_window(tmp_path, lifetime=3600)
    short = service.fetch(proof(service, device))
    assert short['expires_at'] == now + 3600
    service.delivery_lifetime = 14400
    extended = service.fetch(proof(service, device))
    assert extended['expires_at'] == now + 14399
    assert extended['certificate'] != short['certificate']
    assert x509.load_pem_x509_certificate(extended['certificate'].encode()).not_valid_after_utc == utc(now + 14399)
    repeated = service.fetch(proof(service, device))
    assert repeated['certificate'] == extended['certificate']
    assert repeated['revision'] == extended['revision'] == short['revision'] == 1
    assert repeated['device'] == device.reference
    with service.access.db() as database:
        assert database.execute('SELECT COUNT(*) FROM restricted_certificates').fetchone()[0] == 2


@pytest.mark.parametrize('boundary', ['directory', 'crl', 'grant', 'issuer'])
def test_shortest_material_still_caps_long_delivery(tmp_path, boundary):
    service, device, now = long_window(tmp_path)
    if boundary == 'directory':
        seed = json.loads(service.seed_source())
        seed['expires_at'] = iso(now + 600)
        service.seed_source = lambda: json.dumps(seed).encode()
    elif boundary == 'crl':
        target = tmp_path / 'revocations.pem'
        publish_crl(service, target, lifetime=900)
    elif boundary == 'grant':
        with service.access.db() as database:
            database.execute('UPDATE restricted_grants SET expires=?', (now + 600,))
    else:
        root = Ed25519PrivateKey.generate()
        trust = json.loads(base64.b64decode(service.manifest['payload']))
        trust['expires_at'] = now + 600
        payload = json.dumps(trust).encode()
        service.anchor = root.public_key().public_bytes_raw()
        service.manifest = dict(payload=base64.b64encode(payload).decode(),
                                signature=base64.b64encode(root.sign(DOMAIN + payload)).decode())
    response = service.fetch(proof(service, device))
    assert response['expires_at'] == now + (900 if boundary == 'crl' else 600)


def test_four_hour_directory_exact_boundary(tmp_path):
    service, _, now = long_window(tmp_path)
    seed = json.loads(service.seed_source())
    seed.update(issued_at=iso(now), expires_at=iso(now + 14400))
    raw = json.dumps(seed).encode()
    directory(raw, 'a' * 32, 'b' * 32, now + 14399)
    with pytest.raises(ValueError):
        directory(raw, 'a' * 32, 'b' * 32, now + 14400)
    seed['expires_at'] = iso(now + 14401)
    with pytest.raises(ValueError):
        directory(json.dumps(seed).encode(), 'a' * 32, 'b' * 32, now)


@pytest.mark.parametrize('lifetime', [0, 3601, 14401, True, 14400.0, '14400', None])
def test_delivery_policy_rejects_invalid_configuration(tmp_path, lifetime):
    service, _, _ = configured(tmp_path, 1800000000)
    with pytest.raises(ValueError):
        RestrictedReadiness(service.access, manifest=service.manifest, anchor=service.anchor,
                            signing_key=service.signing_key, seed_source=service.seed_source,
                            crl_source=service.crl_source, delivery_lifetime=lifetime)
