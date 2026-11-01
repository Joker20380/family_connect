import base64
import copy
import os

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey

from fleet.contracts import FleetError, canonical
from fleet.materials import SLOTS, open_envelope, public_hex, seal
from fleet.rehearsal_materials import MaterialStore, bind_enrollment, possession_payload


@pytest.fixture
def material():
    authority = Ed25519PrivateKey.generate()
    identity = Ed25519PrivateKey.generate()
    node = X25519PrivateKey.generate()
    binding = dict(instance_id='fleet-rehearsal-001', logical_gateway='fleet-rehearsal', ipv4='8.8.8.8',
                   bundle_a='gw-'+'a'*32, bundle_b='gw-'+'b'*32,
                   enrollment_public_key=public_hex(identity.public_key()), material_public_key=public_hex(node.public_key()))
    slots = {name: ('disposable-test-secret-'+name).encode() for name in SLOTS}
    envelope = seal(binding, slots, authority, issued_at=1000, expires_at=1200)
    challenge = 'f'*64
    node_body = dict(schema=1, scope='rehearsal', public_key=binding['enrollment_public_key'], enrolled_at=1000,
                     transport_issuance=False, binding=dict(instance_id=binding['instance_id'],
                     logical_gateway=binding['logical_gateway'], ipv4=binding['ipv4'], bundle_id=binding['bundle_a'],
                     provider='test', region='test', roles=['awg','tcp','mesh']))
    node_receipt = dict(body=node_body, signature=base64.b64encode(authority.sign(canonical(node_body))).decode())
    enrollment = bind_enrollment(binding, challenge, identity.sign(possession_payload(binding, challenge)), authority, node_receipt)
    return authority, node, binding, slots, envelope, enrollment


def test_roundtrip_and_no_plaintext_receipt(material):
    authority, node, binding, slots, envelope, enrollment = material
    decoded, receipt = open_envelope(envelope, binding, node, authority.public_key(), permit_expires_at=1300, now=1001)
    assert decoded == slots
    assert all(value not in canonical(receipt) and value not in canonical(envelope) for value in slots.values())
    assert seal(binding, slots, authority, issued_at=1000, expires_at=1200) != envelope


@pytest.mark.parametrize('field,value', [('instance_id','fleet-rehearsal-other'), ('bundle_a','gw-'+'c'*32),
    ('ipv4','1.1.1.1'), ('enrollment_public_key','0'*64), ('material_public_key','0'*64)])
def test_wrong_binding(material, field, value):
    authority, node, binding, slots, envelope, enrollment = material
    with pytest.raises(FleetError):
        open_envelope(envelope, dict(binding, **{field:value}), node, authority.public_key(), permit_expires_at=1300, now=1001)


@pytest.mark.parametrize('change', ['node', 'signer', 'ciphertext', 'header', 'expiry', 'future', 'permit'])
def test_rejections(material, change):
    authority, node, binding, slots, envelope, enrollment = material
    envelope = copy.deepcopy(envelope)
    now, expiry = 1001, 1300
    if change == 'node':
        node = X25519PrivateKey.generate()
    if change == 'signer':
        authority = Ed25519PrivateKey.generate()
    if change == 'ciphertext':
        envelope['body']['ciphertext'] = 'AAAA'
    if change == 'header':
        envelope['body']['header']['nonce'] = '0'*64
    if change == 'expiry':
        now = 1200
    if change == 'future':
        now = 999
    if change == 'permit':
        expiry = 1100
    with pytest.raises(FleetError):
        open_envelope(envelope, binding, node, authority.public_key(), permit_expires_at=expiry, now=now)


def test_store_replay_modes_and_retirement(material, tmp_path):
    authority, node, binding, slots, envelope, enrollment = material
    tmp_path.chmod(0o700)
    store = MaterialStore(tmp_path, binding, authority.public_key(), node, enrollment,
                          service_gid=os.getgid(), uid=os.getuid(), custody_gid=os.getgid())
    receipt = store.deliver(envelope, permit_expires_at=1300, now=1001)
    for name in SLOTS:
        path = tmp_path/'slots'/name
        assert path.read_bytes() == slots[name]
        assert path.stat().st_mode & 0o777 == (0o600 if name in ('awg-material','publisher-material') else 0o640)
    with pytest.raises(FleetError, match='replay'):
        store.deliver(envelope, permit_expires_at=1300, now=1001)
    for path in tmp_path.glob('*.json'):
        assert all(value not in path.read_bytes() for value in slots.values())
    store.retire()
    assert not (tmp_path/'slots').exists()
    assert len(receipt['slots']) == 4


def test_rfc7748_public_vector():
    private = X25519PrivateKey.from_private_bytes(bytes.fromhex('77076d0a7318a57d3c16c17251b26645df4c2f87ebc0992ab177fba51db92c2a'))
    assert public_hex(private.public_key()) == '8520f0098930a754748b7ddcb43ef75a0dbf3a0d26381af4eba4a98eaa9b4e6a'
