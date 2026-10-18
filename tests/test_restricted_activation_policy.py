import base64
import json

import pytest
from cryptography import x509
from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat

from control.friends.access import Rejected
from control.friends.restricted import ChallengeUnavailable, admission_policy, delegation, from_env, iso, utc
from control.friends.restricted_admin import publish_crl
from device_identity.device import DeviceIdentity
from test_friends_restricted import configured, proof


@pytest.fixture
def activated(tmp_path):
    service, device, now = configured(tmp_path, 1800000000, delivery_lifetime=14400, directory_lifetime=14400)
    service.all_activated = True
    return service, device, now


def grant_rows(service):
    with service.access.db() as database:
        return [tuple(row) for row in database.execute('SELECT * FROM restricted_grants ORDER BY device')]


def activate(service):
    device = DeviceIdentity.generate()
    challenge = service.access.challenge(device.public_identity, device.wireguard_public_key, 'activate', service.access.invite())
    service.access.complete(device.prove_transport_key(challenge['challenge']), 'activate')
    return device


def test_explicit_policy_and_legacy_compatibility():
    assert admission_policy(b'{"version":2,"eligibility":"all_activated"}') == (None, True)
    assert admission_policy(b'{"devices":[]}') == ([], False)
    assert admission_policy(b'{"devices":["*"]}') == (['*'], False)


@pytest.mark.parametrize('value', [
    {'version': True, 'eligibility': 'all_activated'},
    {'version': 1, 'eligibility': 'all_activated'},
    {'version': 2, 'eligibility': 'anonymous'},
    {'version': 2, 'eligibility': 'all_activated', 'devices': ['*']},
    {'eligibility': 'all_activated'},
    {'devices': [None]},
    None,
    [],
    'all_activated',
])
def test_unknown_or_ambiguous_policy_rejected(value):
    with pytest.raises(ValueError):
        admission_policy(json.dumps(value).encode())


def test_duplicate_policy_fields_rejected():
    with pytest.raises(ValueError):
        admission_policy(b'{"version":2,"version":2,"eligibility":"all_activated"}')


def test_real_configuration_loader_selects_explicit_v2(activated, tmp_path, monkeypatch):
    service, _, _ = activated
    material = tmp_path / 'restricted'
    material.mkdir(mode=0o700)
    files = {
        'admission.json': b'{"version":2,"eligibility":"all_activated"}',
        'anchor.pub': base64.b64encode(service.anchor),
        'issuer.json': json.dumps(service.manifest).encode(),
        'issuer.key': service.signing_key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()),
        'directory.json': service.seed_source(),
        'revocations.pem': service.crl_source(),
    }
    for name, raw in files.items():
        path = material / name
        path.write_bytes(raw)
        path.chmod(0o600)
    monkeypatch.setenv('FC_FRIENDS_RESTRICTED_DIR', str(material))
    monkeypatch.setenv('FC_FRIENDS_RESTRICTED_DELIVERY_LIFETIME', '14400')
    loaded = from_env(service.access)
    assert loaded.all_activated is True and loaded.eligible_devices is None
    assert loaded.delivery_lifetime == 14400
    newcomer = activate(loaded)
    before = grant_rows(loaded)
    assert loaded.fetch(proof(loaded, newcomer))['device'] == newcomer.reference
    assert grant_rows(loaded) == before


def test_existing_and_future_activated_devices_need_no_grant(activated):
    service, device, _ = activated
    with service.access.db() as database:
        database.execute('DELETE FROM restricted_grants')
    assert service.fetch(proof(service, device))['device'] == device.reference
    newcomer = activate(service)
    assert service.fetch(proof(service, newcomer))['device'] == newcomer.reference
    assert grant_rows(service) == []


def test_unknown_identity_remains_unauthorized(activated):
    service, _, _ = activated
    with pytest.raises(Rejected):
        proof(service, DeviceIdentity.generate())


def test_legacy_expiry_is_not_new_policy_entitlement_expiry(activated):
    service, device, _ = activated
    with service.access.db() as database:
        database.execute('UPDATE restricted_grants SET expires=1')
    before = grant_rows(service)
    assert service.fetch(proof(service, device))['device'] == device.reference
    assert grant_rows(service) == before
    service.all_activated = False
    with pytest.raises(Rejected):
        proof(service, device)


@pytest.mark.parametrize('mutation', [
    'UPDATE devices SET revoked=1',
    'UPDATE invites SET revoked=1',
    'DELETE FROM invites',
    'UPDATE restricted_grants SET revoked=1',
    'UPDATE restricted_grants SET revision=revision+1',
    'UPDATE restricted_grants SET revision=0',
    "UPDATE restricted_grants SET family='cccccccccccccccccccccccccccccccc'",
])
def test_authentication_rechecked_between_challenge_and_fetch(activated, mutation):
    service, device, _ = activated
    request = proof(service, device)
    with service.access.db() as database:
        database.execute(mutation)
    before = grant_rows(service)
    with pytest.raises(Rejected):
        service.fetch(request)
    assert grant_rows(service) == before


def test_wrong_identity_and_replay_still_rejected(activated):
    service, device, _ = activated
    request = proof(service, device)
    other = activate(service)
    with pytest.raises(Rejected):
        service.fetch(other.prove_transport_key(request['challenge']))
    service.fetch(request)
    with pytest.raises(Rejected):
        service.fetch(request)


def test_expired_crl_does_not_revoke_entitlement_or_bypass_crypto(activated):
    service, device, now = activated
    first = service.fetch(proof(service, device))
    before = grant_rows(service)
    later = now + 14460
    service.access.clock = lambda: later
    with pytest.raises(ChallengeUnavailable) as rejected:
        proof(service, device)
    assert rejected.value.reason == 'AUTHORITY_UNAVAILABLE'
    assert grant_rows(service) == before
    trust, authority = delegation(service.manifest, service.anchor, later)
    crl = (x509.CertificateRevocationListBuilder().issuer_name(authority.subject)
           .last_update(utc(later - 1)).next_update(utc(later + 14399))
           .add_extension(x509.CRLNumber(2), False).sign(service.signing_key, None))
    service.crl_source = lambda: crl.public_bytes(Encoding.PEM)
    directory = dict(version=1, family=trust['family'], issued_at=iso(later - 1), expires_at=iso(later + 14399),
                     seeds=[dict(transport='telemost-webrtc', join_url='https://telemost.yandex.ru/j/test-only', gateway=trust['gateway'])])
    service.seed_source = lambda: json.dumps(directory).encode()
    second = service.fetch(proof(service, device))
    assert second['device'] == first['device'] and second['revision'] == first['revision']
    assert second['expires_at'] > first['expires_at']
    assert second['expires_at'] <= later + 14400
    assert grant_rows(service) == before


def test_ungranted_device_revocation_is_in_crl(activated, tmp_path):
    service, _, now = activated
    device = activate(service)
    delivery = service.fetch(proof(service, device))
    certificate = x509.load_pem_x509_certificate(delivery['certificate'].encode())
    with service.access.db() as database:
        database.execute('UPDATE devices SET revoked=1 WHERE device=?', (device.reference,))
    target = tmp_path / 'new-crl.pem'
    publish_crl(service, target, lifetime=14400)
    crl = x509.load_pem_x509_crl(target.read_bytes())
    assert crl.get_revoked_certificate_by_serial_number(certificate.serial_number) is not None
    assert (crl.next_update_utc - crl.last_update_utc).total_seconds() == 14400
    assert now < int(crl.next_update_utc.timestamp()) <= now + 14400
    with pytest.raises(Rejected):
        proof(service, device)


def test_support_eligibility_is_not_crypto_readiness(activated):
    from control.friends import support_ids
    service, _, _ = activated
    device = activate(service)
    with service.access.db() as database:
        support = support_ids.registered(database, device.reference)
    before = support_ids.lookup(service.access, support, ())
    assert before['family_state'] == 'NOT_PROVISIONED'
    after = support_ids.lookup(service.access, support, (), all_activated=True)
    assert after['family_state'] == 'ELIGIBLE' and after['field_admission']
    assert after['restricted_readiness'] == 'UNKNOWN'
    with service.access.db() as database:
        database.execute('UPDATE devices SET revoked=1 WHERE device=?', (device.reference,))
    revoked = support_ids.lookup(service.access, support, (), all_activated=True)
    assert revoked['family_state'] == 'REVOKED' and not revoked['field_admission']


def test_old_field_writer_cannot_overwrite_activation_policy(activated, tmp_path):
    from control.friends import support_admin, support_ids
    service, device, _ = activated
    policy = tmp_path / 'admission.json'
    raw = b'{"version":2,"eligibility":"all_activated"}'
    policy.write_bytes(raw)
    with service.access.db() as database:
        support = support_ids.registered(database, device.reference)
    before = grant_rows(service)
    with pytest.raises(ValueError):
        support_admin.change(service.access, policy, support, False)
    assert policy.read_bytes() == raw and grant_rows(service) == before
