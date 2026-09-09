import base64
import json
import os
from concurrent.futures import ThreadPoolExecutor

import pytest
import RNS

from device_identity.device import DeviceIdentity, load_or_create, verify_transport_key_proof

CHALLENGE = base64.b64encode(bytes(range(32))).decode()


def test_reference_rns_verifies_identity_and_independent_transport_binding(tmp_path):
    device = load_or_create(tmp_path / 'device')
    restored = load_or_create(tmp_path / 'device')
    assert restored.reference == device.reference
    assert restored.wireguard_public_key == device.wireguard_public_key
    assert verify_transport_key_proof(device.prove_transport_key(CHALLENGE),
                                      expected_challenge=CHALLENGE) == device.reference
    public = base64.b64decode(device.public_identity)
    assert base64.b64decode(device.wireguard_public_key) != public[:32]
    # Import using upstream, not a mock or another Family Connect implementation.
    upstream = RNS.Identity.from_bytes((tmp_path / 'device/reticulum.key').read_bytes())
    assert upstream.hash.hex() == device.reference
    payload = b'opaque control payload'
    assert upstream.decrypt(upstream.encrypt(payload)) == payload
    proof_json = json.dumps(device.prove_transport_key(CHALLENGE))
    for name in ('reticulum.key', 'wireguard.key'):
        raw = (tmp_path / 'device' / name).read_bytes()
        assert base64.b64encode(raw).decode() not in proof_json
        assert os.stat(tmp_path / 'device' / name).st_mode & 0o777 == 0o600


@pytest.mark.parametrize('field,value', [
    ('wireguard_public_key', base64.b64encode(b'x' * 32).decode()),
    ('challenge', base64.b64encode(b'y' * 32).decode()),
    ('signature', base64.b64encode(b'z' * 64).decode()),
    ('audience', 'other-service'), ('schema_version', True),
    ('transport', 'other'), ('private_key', 'must not be accepted'),
])
def test_proof_tampering_rejected(field, value):
    proof = DeviceIdentity.generate().prove_transport_key(CHALLENGE)
    proof[field] = value
    with pytest.raises(ValueError):
        verify_transport_key_proof(proof, expected_challenge=CHALLENGE)


def test_other_identity_cannot_sign_existing_binding():
    device = DeviceIdentity.generate()
    other = DeviceIdentity.generate()
    proof = device.prove_transport_key(CHALLENGE)
    proof['signature'] = other.prove_transport_key(CHALLENGE)['signature']
    with pytest.raises(ValueError):
        verify_transport_key_proof(proof, expected_challenge=CHALLENGE)


def test_missing_identity_is_not_silently_replaced(tmp_path):
    directory = tmp_path / 'device'
    load_or_create(directory)
    (directory / 'reticulum.key').unlink()
    with pytest.raises(ValueError, match='missing permanent identity'):
        load_or_create(directory)
    assert not (directory / 'reticulum.key').exists()


@pytest.mark.parametrize('unsafe', ['permissions', 'symlink', 'hardlink', 'corrupt'])
def test_unsafe_existing_key_fails_closed(tmp_path, unsafe):
    directory = tmp_path / 'device'
    load_or_create(directory)
    key = directory / 'reticulum.key'
    if unsafe == 'permissions':
        key.chmod(0o644)
    elif unsafe == 'symlink':
        key.rename(directory / 'original')
        key.symlink_to(directory / 'original')
    elif unsafe == 'hardlink':
        os.link(key, directory / 'copy')
    else:
        key.write_bytes(b'broken')
    before = key.read_bytes()
    with pytest.raises((ValueError, OSError)):
        load_or_create(directory)
    assert key.read_bytes() == before


def test_unsafe_directory_rejected(tmp_path):
    directory = tmp_path / 'device'
    directory.mkdir(mode=0o755)
    with pytest.raises(ValueError, match='unsafe identity directory'):
        load_or_create(directory)


def test_concurrent_enrollment_keeps_one_identity(tmp_path):
    with ThreadPoolExecutor(max_workers=4) as executor:
        devices = list(executor.map(lambda _: load_or_create(tmp_path / 'device'), range(8)))
    assert len({device.reference for device in devices}) == 1
    assert len({device.wireguard_public_key for device in devices}) == 1
