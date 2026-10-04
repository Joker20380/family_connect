import base64
import json
import os
from pathlib import Path
import subprocess
import time

import pytest
from cryptography import x509
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat

from control.friends.access import Rejected
from control.friends.restricted import DOMAIN, delegation, utc
from control.friends.restricted_admin import grant, publish_crl
from device_identity.device import DeviceIdentity
from test_friends_restricted import configured, proof

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def tools(tmp_path_factory):
    go = os.environ.get('FC_TEST_GO')
    if not go:
        pytest.skip('set FC_TEST_GO for native authority compatibility')
    folder = tmp_path_factory.mktemp('native-authority-tools')
    environment = dict(os.environ, CGO_ENABLED='0', GOTOOLCHAIN='local')
    result = {'go': go}
    legacy = folder / 'legacy.go'
    legacy.write_bytes((ROOT / 'carrier/cmd/native-authority-check/testdata/legacy.go.txt').read_bytes())
    for name, source in (('legacy', str(legacy)), ('current', './cmd/native-authority-check'),
                         ('delivery', './wholedevice/testdata/delivery-check.go')):
        binary = folder / name
        if name == 'current' and os.environ.get('FC_TEST_NATIVE_CHECKER'):
            result[name] = Path(os.environ['FC_TEST_NATIVE_CHECKER']).resolve()
            continue
        subprocess.run([go, 'build', '-trimpath', '-buildvcs=false', '-o', str(binary), source],
                       cwd=ROOT / 'carrier', env=environment, check=True, capture_output=True, timeout=120)
        result[name] = binary
    return result


def fixture(tmp_path, *, sequence=2, revision=2, crl_number=19, floor=1, family=None,
            crl_lifetime=900, gateway_lifetime=3600, delivery_lifetime=3600, directory_lifetime=3600):
    now = int(time.time())
    service, owner, _ = configured(tmp_path, now, delivery_lifetime=delivery_lifetime,
                                    directory_lifetime=directory_lifetime)
    root = Ed25519PrivateKey.from_private_bytes(bytes([41]) * 32)
    gateway = DeviceIdentity.generate()
    payload = json.loads(base64.b64decode(service.manifest['payload']))
    payload.update(sequence=sequence, gateway=gateway.reference, minimum_revision=floor)
    if family is not None:
        payload['family'] = family
    raw = json.dumps(payload).encode()
    service.anchor = root.public_key().public_bytes_raw()
    service.manifest = dict(payload=base64.b64encode(raw).decode(), signature=base64.b64encode(root.sign(DOMAIN + raw)).decode())
    service.eligible_devices = frozenset([owner.reference])
    with service.access.db() as database:
        database.execute('UPDATE restricted_grants SET family=?', (payload['family'],))
    if revision != 1:
        grant(service.access, owner.reference, payload['family'], payload['expires_at'], revision)
    seed = json.loads(service.seed_source())
    seed['family'] = payload['family']
    seed['seeds'][0]['gateway'] = gateway.reference
    service.seed_source = lambda: json.dumps(seed).encode()
    crl_path = tmp_path / 'revocations.pem'
    crl_path.write_bytes(service.crl_source())
    crl_path.chmod(0o600)
    service.crl_source = crl_path.read_bytes
    for expected in range(2, crl_number + 1):
        assert publish_crl(service, crl_path, lifetime=crl_lifetime) == expected
    trust, authority = delegation(service.manifest, service.anchor, now)
    gateway_certificate = service._issue(dict(public=gateway.public_identity, device=gateway.reference,
                                             family=trust['family'], revision=floor), authority,
                                         now, now + gateway_lifetime, 'gateway')
    private = Ed25519PrivateKey.from_private_bytes(gateway._identity.get_private_key()[32:])
    profile = dict(certificate=gateway_certificate.public_bytes(Encoding.PEM).decode(),
                   private_key=private.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()).decode(),
                   authority=trust['authority'], family=trust['family'], gateway=trust['gateway'],
                   minimum_revision=floor, minimum_crl=crl_number, revocations=service.crl_source().decode())
    return service, owner, now, profile


def native(binary, tmp_path, profile, certificate):
    profile_path, certificate_path = tmp_path / 'gateway.json', tmp_path / 'canary.pem'
    profile_path.write_text(json.dumps(profile)); profile_path.chmod(0o600)
    certificate_path.write_text(certificate); certificate_path.chmod(0o600)
    return subprocess.run([str(binary), str(profile_path), str(certificate_path)], cwd='/',
                          stdin=subprocess.DEVNULL, capture_output=True, timeout=10)


def delivery(binary, service, owner, now, response, *, public_only=False):
    payload = dict(response=response, identity=base64.b64encode(owner._identity.get_private_key()).decode(),
                   anchor=base64.b64encode(service.anchor).decode(), now=now)
    if public_only:
        payload['public'] = owner.public_identity
    return subprocess.run([str(binary)], input=json.dumps(payload).encode(), cwd='/', capture_output=True, timeout=10)


def test_long_testing_window_preserves_native_expiry_checks(tools, tmp_path):
    service, owner, now, profile = fixture(tmp_path, crl_number=2, crl_lifetime=3600,
                                          gateway_lifetime=14400)
    response = service.fetch(proof(service, owner))
    assert response['expires_at'] == now + 3599
    result = native(tools['current'], tmp_path, profile, response['certificate'])
    assert result.returncode == 0 and json.loads(result.stdout)['status'] == 'PASS'
    assert delivery(tools['delivery'], service, owner, now + 1800, response, public_only=True).returncode == 0
    assert delivery(tools['delivery'], service, owner, now + 3599, response, public_only=True).returncode != 0


def test_four_hour_real_delivery_cross_language(tools, tmp_path):
    service, owner, now, profile = fixture(tmp_path, crl_number=2, crl_lifetime=14400,
                                          gateway_lifetime=14400, delivery_lifetime=14400,
                                          directory_lifetime=14400)
    response = service.fetch(proof(service, owner))
    assert response['expires_at'] == now + 14399
    result = native(tools['current'], tmp_path, profile, response['certificate'])
    assert result.returncode == 0 and json.loads(result.stdout)['status'] == 'PASS'
    assert delivery(tools['delivery'], service, owner, now, response).returncode == 0
    for observed in (now, now + 7200, now + 14398):
        assert delivery(tools['delivery'], service, owner, observed, response, public_only=True).returncode == 0
    for observed in (now - 1, now + 14399, now + 14400):
        assert delivery(tools['delivery'], service, owner, observed, response, public_only=True).returncode != 0
    overlong = dict(response, expires_at=now + 14401)
    assert delivery(tools['delivery'], service, owner, now, overlong, public_only=True).returncode != 0
    trust, authority = delegation(service.manifest, service.anchor, now)
    crl = (x509.CertificateRevocationListBuilder().issuer_name(authority.subject)
           .last_update(utc(now)).next_update(utc(now + 14401))
           .add_extension(x509.CRLNumber(response['minimum_crl']), False).sign(service.signing_key, None))
    overlong = dict(response, revocations=crl.public_bytes(Encoding.PEM).decode())
    assert delivery(tools['delivery'], service, owner, now, overlong, public_only=True).returncode != 0
    assert trust['expires_at'] > response['expires_at']


@pytest.mark.parametrize('sequence,revision,crl_number,old_exit', [(1,1,1,0), (2,2,2,1), (2,2,19,1), (37,37,43,1), (2,1,19,0)])
def test_same_python_native_delivery_fixture(tools, tmp_path, sequence, revision, crl_number, old_exit):
    service, owner, now, profile = fixture(tmp_path, sequence=sequence, revision=revision, crl_number=crl_number)
    trust, _, _, _, observed = service._trust(now)
    assert trust['sequence'] == sequence and observed == crl_number
    with service.access.db() as database:
        assert service._grant(database, owner.reference, now)['revision'] == revision
    response = service.fetch(proof(service, owner))
    assert response['revision'] == revision and response['minimum_crl'] == crl_number
    before = native(tools['legacy'], tmp_path, profile, response['certificate'])
    assert before.returncode == old_exit
    after = native(tools['current'], tmp_path, profile, response['certificate'])
    assert after.returncode == 0 and json.loads(after.stdout)['status'] == 'PASS'
    parsed = delivery(tools['delivery'], service, owner, now, response)
    assert parsed.returncode == 0 and parsed.stdout == b'compatible\n'
    assert delivery(tools['delivery'], service, owner, now, response, public_only=True).returncode == 0
    payload = json.loads(json.dumps(response))
    payload['revision'] = revision + 1
    assert delivery(tools['delivery'], service, owner, now, payload).returncode == 1


@pytest.mark.parametrize('mutation', ['crl_above_floor', 'zero_family'])
def test_legacy_negative_precondition_reproduced(tools, tmp_path, mutation):
    service, owner, _, profile = fixture(tmp_path, revision=1, family='0'*32 if mutation == 'zero_family' else None)
    response = service.fetch(proof(service, owner))
    if mutation == 'crl_above_floor':
        profile['minimum_crl'] = 18
    assert native(tools['legacy'], tmp_path, profile, response['certificate']).returncode == 1
    assert native(tools['current'], tmp_path, profile, response['certificate']).returncode == 0


@pytest.mark.parametrize('mutation,stage', [('revision_rollback','device_admission'), ('crl_rollback','configuration'),
                                         ('wrong_family','device_admission'), ('wrong_gateway','gateway_binding')])
def test_native_required_floor_and_binding_negatives(tools, tmp_path, mutation, stage):
    service, owner, _, profile = fixture(tmp_path)
    response = service.fetch(proof(service, owner))
    if mutation == 'revision_rollback':
        profile['minimum_revision'] = 3
    elif mutation == 'crl_rollback':
        profile['minimum_crl'] = 20
    elif mutation == 'wrong_family':
        profile['family'] = 'f'*32
    else:
        profile['gateway'] = 'f'*32
    result = native(tools['current'], tmp_path, profile, response['certificate'])
    assert result.returncode == 1 and json.loads(result.stdout)['stage'] == stage


def test_python_revocation_and_native_current_revision(tools, tmp_path):
    service, owner, now, profile = fixture(tmp_path)
    response = service.fetch(proof(service, owner))
    with service.access.db() as database:
        database.execute('UPDATE restricted_grants SET revoked=1')
    assert publish_crl(service, tmp_path/'revocations.pem') == 20
    profile.update(revocations=service.crl_source().decode(), minimum_crl=20)
    with pytest.raises(Rejected):
        service.challenge(owner.public_identity, owner.wireguard_public_key)
    result = native(tools['current'], tmp_path, profile, response['certificate'])
    assert result.returncode == 1 and json.loads(result.stdout)['stage'] == 'device_admission'
    response.update(revocations=service.crl_source().decode(), minimum_crl=20)
    assert delivery(tools['delivery'], service, owner, now, response).returncode == 1


@pytest.mark.parametrize('mutation', ['grant_expired', 'delegation_expired', 'grant_below_minimum', 'challenge_old_revision'])
def test_producer_rejects_stale_authority(tmp_path, mutation):
    service, owner, now, _ = fixture(tmp_path, floor=2 if mutation == 'grant_below_minimum' else 1,
                                     revision=1 if mutation == 'grant_below_minimum' else 2)
    if mutation == 'grant_expired':
        with service.access.db() as database:
            database.execute('UPDATE restricted_grants SET expires=?', (now,))
    elif mutation == 'delegation_expired':
        with pytest.raises(ValueError):
            delegation(service.manifest, service.anchor, now+86400)
        return
    elif mutation == 'challenge_old_revision':
        old_proof = proof(service, owner)
        grant(service.access, owner.reference, json.loads(base64.b64decode(service.manifest['payload']))['family'], now+3600)
        with pytest.raises(Rejected):
            service.fetch(old_proof)
        return
    with pytest.raises((Rejected, ValueError)):
        service.challenge(owner.public_identity, owner.wireguard_public_key)


def test_renewal_revokes_old_certificate_without_reset(tools, tmp_path):
    service, owner, now, profile = fixture(tmp_path, revision=1)
    old = service.fetch(proof(service, owner))
    trust, _ = delegation(service.manifest, service.anchor, now)
    grant(service.access, owner.reference, trust['family'], trust['expires_at'])
    assert publish_crl(service, tmp_path/'revocations.pem') == 20
    profile.update(revocations=service.crl_source().decode(), minimum_crl=20)
    assert native(tools['current'], tmp_path, profile, old['certificate']).returncode == 1
    renewed = service.fetch(proof(service, owner))
    assert renewed['revision'] == 2
    assert native(tools['current'], tmp_path, profile, renewed['certificate']).returncode == 0
    assert delivery(tools['delivery'], service, owner, now, renewed).returncode == 0
