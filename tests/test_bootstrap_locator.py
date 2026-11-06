import base64
import json

import pytest
from cryptography import x509
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.x509.oid import ExtendedKeyUsageOID

from control.friends.bootstrap_locator import DOMAIN, issue
from control.friends.restricted import delegation, utc
from test_friends_restricted import configured


@pytest.fixture
def locator_source(tmp_path):
    service, _, now = configured(tmp_path, 1800000000)
    _, authority = delegation(service.manifest, service.anchor, now)
    certificate = (x509.CertificateBuilder().subject_name(authority.subject).issuer_name(authority.subject)
                   .public_key(Ed25519PrivateKey.generate().public_key()).serial_number(123)
                   .not_valid_before(utc(now - 1)).not_valid_after(utc(now + 600))
                   .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), False)
                   .add_extension(x509.SubjectAlternativeName([x509.DNSName('gateway.family-connect.test')]), False)
                   .sign(service.signing_key, None)).public_bytes(Encoding.PEM).decode()
    return service, now, certificate


def test_locator_uses_existing_root_delegation_and_issuer(locator_source):
    service, now, certificate = locator_source
    encoded = issue(service, service.seed_source(), certificate, 1)
    result = json.loads(encoded)
    assert result['issuer'] == service.manifest
    payload = base64.b64decode(result['payload'])
    service.signing_key.public_key().verify(base64.b64decode(result['signature']), DOMAIN + payload)
    value = json.loads(payload)
    assert value['expires_at'] == now + 600
    assert value['purpose'] == 'family-connect-provisioning-v1'
    assert 'private' not in encoded.decode().lower()
    assert set(value) == {'version', 'purpose', 'sequence', 'issued_at', 'expires_at', 'gateway_id', 'room', 'server_certificate'}


@pytest.mark.parametrize('case', ['missing_seed', 'wrong_node', 'future_seed', 'expired_seed', 'sequence', 'issuer_key', 'revoked_server', 'expired_crl'])
def test_locator_rejects_invalid_authority_or_seed(locator_source, case):
    service, now, certificate = locator_source
    seed, sequence = json.loads(service.seed_source()), 1
    if case == 'missing_seed':
        seed = {}
    elif case == 'wrong_node':
        seed['seeds'][0]['gateway'] = 'c' * 32
    elif case == 'future_seed':
        seed['issued_at'] = utc(now + 1).isoformat()
    elif case == 'expired_seed':
        seed['expires_at'] = utc(now).isoformat()
    elif case == 'sequence':
        sequence = 0
    elif case == 'issuer_key':
        service.signing_key = Ed25519PrivateKey.generate()
    else:
        _, authority = delegation(service.manifest, service.anchor, now)
        builder = x509.CertificateRevocationListBuilder().issuer_name(authority.subject).last_update(utc(now - 2)).next_update(utc(now - 1 if case == 'expired_crl' else now + 500)).add_extension(x509.CRLNumber(1), False)
        if case == 'revoked_server':
            builder = builder.add_revoked_certificate(x509.RevokedCertificateBuilder().serial_number(123).revocation_date(utc(now - 1)).build())
        raw = builder.sign(service.signing_key, None).public_bytes(Encoding.PEM)
        service.crl_source = lambda: raw
    with pytest.raises(ValueError):
        issue(service, json.dumps(seed).encode(), certificate, sequence)
