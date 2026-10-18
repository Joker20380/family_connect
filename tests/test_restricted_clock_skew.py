import base64
import json
import os
from pathlib import Path
import subprocess

import pytest
from cryptography import x509
from cryptography.hazmat.primitives.serialization import Encoding

from control.friends.access import Rejected
from control.friends.restricted import utc
from control.friends.restricted_admin import publish_crl
from test_friends_restricted import configured, proof
from test_readiness_receipts import ready, acknowledge, challenge_ack


@pytest.fixture
def issued(tmp_path):
    service, device, original = configured(tmp_path, 1800000000, delivery_lifetime=14400,
                                          directory_lifetime=14400)
    now = original + 300
    service.access.clock = lambda: now
    target = tmp_path / 'revocations.pem'
    publish_crl(service, target, lifetime=14400)
    service.crl_source = target.read_bytes
    response = service.fetch(proof(service, device))
    return service, device, now, response


def test_fresh_issuance_backdates_all_new_time_bounds_without_extending_expiry(issued):
    service, _, now, response = issued
    certificate = x509.load_pem_x509_certificate(response['certificate'].encode())
    crl = x509.load_pem_x509_crl(response['revocations'].encode())
    assert response['issued_at'] == now - 5
    assert certificate.not_valid_before_utc == crl.last_update_utc == utc(now - 5)
    assert crl.next_update_utc == utc(now + 14395)
    assert response['expires_at'] - response['issued_at'] <= service.delivery_lifetime
    assert certificate.not_valid_after_utc == utc(response['expires_at'])


@pytest.mark.parametrize('offset', [-5, -1, 0, 5])
def test_small_clock_offset_ack_is_signed_and_correlated(ready, offset):
    service, owner, now, payload = ready
    payload['observed_at'] = now + offset
    assert acknowledge(service, owner, payload)['status'] == 'ACK_RECEIVED'


@pytest.mark.parametrize('offset', [-6, 6])
def test_ack_skew_is_bounded(ready, offset):
    service, owner, now, payload = ready
    payload['observed_at'] = now + offset
    with pytest.raises(Rejected):
        challenge_ack(service, owner, payload)


@pytest.mark.parametrize('mutation', ['revoked', 'expired', 'fetch', 'rollback'])
def test_skew_does_not_bypass_ack_security(ready, mutation):
    service, owner, now, payload = ready
    payload['observed_at'] = now - 1
    if mutation == 'revoked':
        with service.access.db() as database:
            database.execute('UPDATE restricted_grants SET revoked=1')
    elif mutation == 'expired':
        service.access.clock = lambda: payload['expires_at']
    elif mutation == 'fetch':
        payload['fetch_id'] = 'c' * 32
    else:
        acknowledge(service, owner, dict(payload, observed_at=now))
    with pytest.raises((ValueError, Rejected)):
        challenge_ack(service, owner, payload)


@pytest.fixture(scope='module')
def native_checker(tmp_path_factory):
    tool = os.environ.get('FC_TEST_GO')
    if not tool:
        pytest.skip('set FC_TEST_GO for unchanged Android validator compatibility')
    root = Path(__file__).resolve().parents[1]
    binary = tmp_path_factory.mktemp('clock-native') / 'delivery-check'
    subprocess.run([tool, 'build', '-o', str(binary), './wholedevice/testdata/delivery-check.go'],
                   cwd=root / 'carrier', check=True, capture_output=True, timeout=180)
    return binary


def native_result(binary, service, device, response, now_ns):
    request = dict(response=response, public=device.public_identity,
                   anchor=base64.b64encode(service.anchor).decode(), now_ns=now_ns)
    return subprocess.run([str(binary)], input=json.dumps(request).encode(),
                          capture_output=True, timeout=10).returncode


@pytest.mark.parametrize('milliseconds', [-5000, -715, -485, 0, 5000])
def test_unchanged_native_accepts_fresh_delivery_with_small_clock_offset(issued, native_checker, milliseconds):
    service, device, now, response = issued
    assert native_result(native_checker, service, device, response, now * 10**9 + milliseconds * 10**6) == 0


def test_original_issuance_timestamp_reproduces_export12_failure(issued, native_checker):
    service, device, now, response = issued
    response['issued_at'] = now
    assert native_result(native_checker, service, device, response, now * 10**9 - 715000000) != 0


@pytest.mark.parametrize('failure', ['too_early', 'expired', 'revoked', 'signature', 'crl_future'])
def test_unchanged_native_still_rejects_invalid_material(issued, native_checker, failure):
    service, device, now, response = issued
    now_ns = now * 10**9 - 485000000
    if failure == 'too_early':
        now_ns = now * 10**9 - 5000000001
    elif failure == 'expired':
        now_ns = response['expires_at'] * 10**9
    elif failure == 'signature':
        response['issuer'] = dict(response['issuer'], signature=base64.b64encode(bytes(64)).decode())
    else:
        original = x509.load_pem_x509_crl(response['revocations'].encode())
        builder = (x509.CertificateRevocationListBuilder().issuer_name(original.issuer)
                   .last_update(utc(now if failure == 'crl_future' else now - 5))
                   .next_update(original.next_update_utc)
                   .add_extension(x509.CRLNumber(response['minimum_crl']), False))
        if failure == 'revoked':
            certificate = x509.load_pem_x509_certificate(response['certificate'].encode())
            builder = builder.add_revoked_certificate(x509.RevokedCertificateBuilder()
                      .serial_number(certificate.serial_number).revocation_date(utc(now - 5)).build())
        response['revocations'] = builder.sign(service.signing_key, None).public_bytes(Encoding.PEM).decode()
    assert native_result(native_checker, service, device, response, now_ns) != 0
