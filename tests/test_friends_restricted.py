import base64
import json

import pytest
from cryptography import x509
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.x509.oid import NameOID

from control.friends.access import Access, Rejected
from control.friends.restricted import RestrictedReadiness, DOMAIN, delegation, directory, iso, migrate, utc
from device_identity.device import DeviceIdentity


@pytest.fixture
def setup(tmp_path):
    return configured(tmp_path, 1800000000)


def configured(tmp_path, now):
    access = Access(tmp_path / 'access.db', clock=lambda: now)
    access.initialize()
    migrate(access)
    device = DeviceIdentity.generate()
    code = access.invite()
    challenge = access.challenge(device.public_identity, device.wireguard_public_key, 'activate', code)
    access.complete(device.prove_transport_key(challenge['challenge']), 'activate')
    signing = Ed25519PrivateKey.generate()
    root = Ed25519PrivateKey.generate()
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'unit test delegated issuer')])
    ca = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(signing.public_key())
          .serial_number(1).not_valid_before(utc(now - 10)).not_valid_after(utc(now + 86400))
          .add_extension(x509.BasicConstraints(ca=True, path_length=0), True)
          .add_extension(x509.KeyUsage(False, False, False, False, False, True, True, False, False), True)
          .add_extension(x509.SubjectKeyIdentifier.from_public_key(signing.public_key()), False)
          .sign(signing, None))
    family, gateway = 'a' * 32, 'b' * 32
    payload = json.dumps(dict(version=1, sequence=1, family=family, gateway=gateway,
                              authority=ca.public_bytes(Encoding.PEM).decode(), minimum_revision=1, issued_at=now-10, expires_at=now+86400)).encode()
    manifest = dict(payload=base64.b64encode(payload).decode(), signature=base64.b64encode(root.sign(DOMAIN + payload)).decode())
    crl = (x509.CertificateRevocationListBuilder().issuer_name(name).last_update(utc(now-1)).next_update(utc(now+3599))
           .add_extension(x509.CRLNumber(1), False).sign(signing, None))
    seed = json.dumps(dict(version=1, family=family, issued_at=iso(now-1), expires_at=iso(now+3599),
                           seeds=[dict(transport='telemost-webrtc', join_url='https://telemost.yandex.ru/j/test-only', gateway=gateway)])).encode()
    with access.db() as database:
        database.execute('INSERT INTO restricted_grants VALUES (?,?,?,?,0)', (device.reference, family, 1, now+86400))
    service = RestrictedReadiness(access, manifest=manifest, anchor=root.public_key().public_bytes_raw(), signing_key=signing,
                                 seed_source=lambda: seed, crl_source=lambda: crl.public_bytes(Encoding.PEM))
    return service, device, now


def test_backend_delivery_consumed_by_native_material(tmp_path):
    import os
    import subprocess
    import time
    from pathlib import Path
    tool = os.environ.get('FC_TEST_GO')
    if not tool:
        pytest.skip('set FC_TEST_GO to the locked Go toolchain for cross-language compatibility')
    service, device, now = configured(tmp_path, int(time.time()))
    with service.access.db() as database:
        database.execute('UPDATE restricted_grants SET revision=2')
    response = service.fetch(proof(service, device))
    value = dict(response=response, identity=base64.b64encode(device._identity.get_private_key()).decode(),
                 anchor=base64.b64encode(service.anchor).decode(), now=now)
    result = subprocess.run([tool, 'run', './wholedevice/testdata/delivery-check.go'],
                            input=json.dumps(value).encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            cwd=Path(__file__).resolve().parents[1] / 'carrier', timeout=90)
    assert result.returncode == 0 and result.stdout == b'compatible\n', 'backend/native delivery incompatibility'


def proof(service, device):
    challenge = service.challenge(device.public_identity, device.wireguard_public_key)
    return device.prove_transport_key(challenge['challenge'])


def test_active_device_public_only_and_idempotent_refresh(setup):
    service, device, now = setup
    first = service.fetch(proof(service, device))
    second = service.fetch(proof(service, device))
    assert first['certificate'] == second['certificate']
    assert first['directory'] == second['directory']
    assert first['device'] == device.reference
    certificate = x509.load_pem_x509_certificate(first['certificate'].encode())
    assert certificate.public_key().public_bytes_raw() == base64.b64decode(device.public_identity)[32:]
    assert certificate.subject.get_attributes_for_oid(NameOID.SERIAL_NUMBER)[0].value == device.reference
    assert certificate.extensions.get_extension_for_class(x509.SubjectAlternativeName).value.get_values_for_type(x509.UniformResourceIdentifier) == ['urn:family-connect:identity:' + base64.b64decode(device.public_identity).hex()]
    assert first['expires_at'] <= now+3600
    raw = json.dumps(first)
    assert len(raw) <= 65536
    for forbidden in ('private_key', 'PRIVATE KEY', 'oauth', 'access_token', 'tcp_id', 'descriptor', 'setup_id'):
        assert forbidden not in raw
    assert raw.count('https://') == 1
    delegation(first['issuer'], service.anchor, now)
    directory(json.dumps(first['directory']).encode(), 'a'*32, 'b'*32, now)


@pytest.mark.parametrize('mutation', [
    'UPDATE devices SET revoked=1',
    'UPDATE invites SET revoked=1',
    'UPDATE restricted_grants SET revoked=1',
    'UPDATE restricted_grants SET expires=1',
    'UPDATE restricted_grants SET revision=revision+1',
    "UPDATE restricted_grants SET family='cccccccccccccccccccccccccccccccc'",
])
def test_authorization_rechecked_after_challenge(setup, mutation):
    service, device, _ = setup
    request = proof(service, device)
    with service.access.db() as database:
        database.execute(mutation)
    with pytest.raises(Rejected):
        service.fetch(request)


def test_wrong_device_and_replay_expired_challenge(setup):
    service, device, now = setup
    request = proof(service, device)
    other = DeviceIdentity.generate()
    with pytest.raises(Rejected):
        service.fetch(other.prove_transport_key(request['challenge']))
    service.fetch(request)
    with pytest.raises(Rejected):
        service.fetch(request)
    request = proof(service, device)
    service.access.clock = lambda: now+101
    with pytest.raises(Rejected):
        service.fetch(request)


def test_purpose_is_not_normal_provisioning(setup):
    service, device, _ = setup
    challenge = service.access.challenge(device.public_identity, device.wireguard_public_key, 'nl')
    with pytest.raises(Rejected):
        service.fetch(device.prove_transport_key(challenge['challenge']))


def test_seed_failure_does_not_consume_proof_or_issue_certificate(setup):
    service, device, _ = setup
    request = proof(service, device)
    good = service.seed_source
    service.seed_source = lambda: b'{}'
    with pytest.raises(ValueError):
        service.fetch(request)
    with service.access.db() as database:
        assert database.execute('SELECT COUNT(*) FROM restricted_certificates').fetchone()[0] == 0
    service.seed_source = good
    service.fetch(request)


def test_request_limits_and_trust_bounds(setup):
    service, device, now = setup
    for _ in range(8):
        proof(service, device)
    with pytest.raises(RuntimeError):
        proof(service, device)
    with pytest.raises(ValueError):
        directory(b' ' * 8193, 'a'*32, 'b'*32, now)
    original = json.loads(service.seed_source())
    for change in ({'expires_at': iso(now+3601)}, {'family': 'c'*32}, {'signature': 'unsupported'}):
        with pytest.raises(ValueError):
            directory(json.dumps(dict(original, **change)).encode(), 'a'*32, 'b'*32, now)
    service.anchor = bytes(32)
    with pytest.raises(Exception):
        service.challenge(device.public_identity, device.wireguard_public_key)


def test_revoked_certificate_not_reissued_as_bypass(setup):
    service, device, now = setup
    first = service.fetch(proof(service, device))
    certificate = x509.load_pem_x509_certificate(first['certificate'].encode())
    trust, ca = delegation(service.manifest, service.anchor, now)
    crl = (x509.CertificateRevocationListBuilder().issuer_name(ca.subject).last_update(utc(now)).next_update(utc(now+3600))
           .add_extension(x509.CRLNumber(2), False).add_revoked_certificate(x509.RevokedCertificateBuilder()
           .serial_number(certificate.serial_number).revocation_date(utc(now)).build()).sign(service.signing_key, None))
    service.crl_source = lambda: crl.public_bytes(Encoding.PEM)
    with pytest.raises(Rejected):
        service.fetch(proof(service, device))


def test_grant_revision_and_crl_publication(setup, tmp_path):
    from control.friends.restricted_admin import grant, publish_crl
    service, device, now = setup
    first = service.fetch(proof(service, device))
    old = x509.load_pem_x509_certificate(first['certificate'].encode())
    grant(service.access, device.reference, 'a'*32, now+600)
    target = tmp_path / 'revocations.pem'
    publish_crl(service, target)
    service.crl_source = target.read_bytes
    assert x509.load_pem_x509_crl(target.read_bytes()).get_revoked_certificate_by_serial_number(old.serial_number) is not None
    second = service.fetch(proof(service, device))
    assert second['revision'] == 2 and second['certificate'] != first['certificate']
    assert second['expires_at'] <= now+600
    with service.access.db() as database:
        database.execute('UPDATE devices SET revoked=1')
    publish_crl(service, target)
    latest = x509.load_pem_x509_certificate(second['certificate'].encode())
    assert x509.load_pem_x509_crl(target.read_bytes()).get_revoked_certificate_by_serial_number(latest.serial_number) is not None
    with pytest.raises(Rejected):
        service.challenge(device.public_identity, device.wireguard_public_key)


def test_http_routes_bounds_and_disabled_feature(setup, monkeypatch):
    import importlib.util
    import io
    from pathlib import Path
    import control.friends.restricted as restricted
    service, device, _ = setup
    spec = importlib.util.spec_from_file_location('restricted_http_test', Path('deploy/friends/access-api.py'))
    api = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api)
    api.access = service.access
    monkeypatch.setattr(restricted, 'from_env', lambda access: service)

    def call(path, body, size=None):
        handler = object.__new__(api.Handler)
        handler.path = path
        raw = json.dumps(body).encode()
        handler.headers = {'Content-Type': 'application/json', 'Content-Length': str(len(raw) if size is None else size)}
        handler.rfile = io.BytesIO(raw)
        handler.connection = type('Socket', (), {'settimeout': lambda self, value: None})()
        replies = []
        handler.reply = lambda status, value: replies.append((status, value))
        handler.do_POST()
        return replies[0]

    status, challenge = call('/friends/restricted-readiness/challenge', dict(public_identity=device.public_identity, wireguard_public_key=device.wireguard_public_key))
    assert status == 200
    status, reply = call('/friends/restricted-readiness', device.prove_transport_key(challenge['challenge']))
    assert status == 200 and reply['device'] == device.reference
    assert call('/friends/restricted-readiness', {}, 8193)[0] == 400
    for _ in range(8):
        proof(service, device)
    assert call('/friends/restricted-readiness/challenge', dict(public_identity=device.public_identity, wireguard_public_key=device.wireguard_public_key)) == (503, {'error': 'unavailable'})
    monkeypatch.setattr(restricted, 'from_env', lambda access: (_ for _ in ()).throw(KeyError('not configured')))
    assert call('/friends/restricted-readiness', {}) == (503, {'error': 'unavailable'})


def test_existing_activation_automatically_maps_to_authorized_family(setup):
    service, device, _ = setup
    with service.access.db() as database:
        database.execute('DELETE FROM restricted_grants')
    with pytest.raises(Rejected):
        proof(service, device)
    service.eligible_devices = {device.reference}
    assert service.fetch(proof(service, device))['device'] == device.reference
    with service.access.db() as database:
        database.execute('UPDATE restricted_grants SET revoked=1')
    with pytest.raises(Rejected):
        proof(service, device)


def test_gateway_sync_only_exports_directory_preserves_key_and_rejects_rollback(setup, tmp_path):
    from control.friends.restricted_sync import gateway
    from control.friends.restricted_admin import publish_crl
    service, _, now = setup
    trust, _ = delegation(service.manifest, service.anchor, now)
    old = service.crl_source().decode()
    profile = tmp_path / 'gateway.json'
    profile.write_text(json.dumps(dict(authority=trust['authority'], revocations=old, minimum_crl=1,
                                      family=trust['family'], gateway=trust['gateway'], private_key='unit-only-marker')))
    profile.chmod(0o600)
    seed = tmp_path / 'directory.json'
    seed.write_bytes(service.seed_source())
    seed.chmod(0o600)
    target = tmp_path / 'revocations.pem'
    publish_crl(service, target)
    request = json.dumps(dict(revocations=target.read_text())).encode()
    result = gateway(profile, seed, request, now)
    assert result == service.seed_source() and b'unit-only-marker' not in result
    assert json.loads(profile.read_bytes())['private_key'] == 'unit-only-marker'
    assert json.loads(profile.read_bytes())['minimum_crl'] == 2
    prior = profile.read_bytes()
    with pytest.raises(ValueError):
        gateway(profile, seed, json.dumps(dict(revocations=old)).encode(), now)
    assert profile.read_bytes() == prior
    with pytest.raises(ValueError):
        gateway(profile, seed, b' ' * 20001, now)


def test_public_crl_response_cannot_include_trailing_material(setup):
    service, device, _ = setup
    original = service.crl_source()
    service.crl_source = lambda: original + b'non-public trailing material'
    with pytest.raises(ValueError):
        proof(service, device)
