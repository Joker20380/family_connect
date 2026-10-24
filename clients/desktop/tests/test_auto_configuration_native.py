import base64
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import threading
import time

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.exceptions import InvalidSignature
import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'clients/linux'))
import mesh_materials
from auto_configuration import NativeConfiguration, NormalOwner, verified
from auto_policy import Context, Failure
from provisioning import friends_catalog

FIXTURE = json.loads((ROOT / 'tests/fixtures/desktop-friends-catalog-v2.json').read_text())
DOMAIN = b'family-connect/invited-test/v1\0'
PUBLIC = b'x' * 64
SIGNER = Ed25519PrivateKey.from_private_bytes(b'n' * 32)


def signed(payload):
    return dict(payload=base64.b64encode(payload).decode(), signature=base64.b64encode(SIGNER.sign(DOMAIN + payload)).decode())


def three_gateway_catalog():
    payload = json.loads(base64.b64decode(FIXTURE['vectors'][0]['reply']['catalog']['payload']))
    original = next(gateway for gateway in payload['gateways'] if gateway['country'] == 'nl')
    payload['gateways'] = [copy.deepcopy(original) for _ in range(3)]
    payload['gateways'][2]['country'] = 'de'
    payload['sequence'] = 3
    return signed(json.dumps(payload, separators=(',', ':')).encode())


def test_signed_three_gateway_model_catalog_reaches_legacy_list_rejection(monkeypatch):
    envelope = three_gateway_catalog()
    anchor = SIGNER.public_key().public_bytes_raw()
    raw = base64.b64decode(envelope['payload'])
    assert len(raw) <= 8192
    Ed25519PublicKey.from_public_bytes(anchor).verify(base64.b64decode(envelope['signature']), DOMAIN + raw)
    inspected = []
    original = friends_catalog._catalog
    def checked(payload, floor, previous_hash):
        inspected.append(json.loads(payload)['gateways'])
        return original(payload, floor, previous_hash)
    monkeypatch.setattr(friends_catalog, '_catalog', checked)
    with pytest.raises(ValueError, match='Invalid Friends catalog floor'):
        friends_catalog.verify_catalog(envelope, anchor)
    assert len(inspected) == 1 and [gateway['country'] for gateway in inspected[0]] == ['nl', 'nl', 'de']


def test_native_rejects_valid_signature_with_three_legacy_gateways(native):
    response = copy.deepcopy(FIXTURE['vectors'][0]['reply'])
    response['device'] = hashlib.sha256(PUBLIC).hexdigest()[:32]
    response['catalog'] = signed(base64.b64decode(response['catalog']['payload']))
    request = dict(schema=1, id=1, action='inspect', public=base64.b64encode(PUBLIC).decode(),
                   anchor=base64.b64encode(SIGNER.public_key().public_bytes_raw()).decode(), country='nl',
                   response=response, floors=[response['catalog']])
    assert native(request, threading.Event(), time.monotonic() + 5)['ok']
    response['catalog'] = three_gateway_catalog()
    reply = native(request, threading.Event(), time.monotonic() + 5)
    assert reply == dict(schema=1, id=1, ok=False, code='CONFIGURATION')


@pytest.fixture
def native(monkeypatch):
    artifact = os.environ.get('FC_TEST_MESH_WORKER')
    if not artifact:
        pytest.skip('Requires exact native worker with normal configuration protocol')
    monkeypatch.setattr(mesh_materials, 'WORKER', str(Path(artifact).resolve(strict=True)))
    return NativeConfiguration()


@pytest.mark.parametrize('invalid', [None, 'wireguard', 'floor'])
def test_offline_native_preflight_validates_keys_and_floors_without_authorizing_or_persisting(native, tmp_path, invalid):
    storage = mesh_materials.CacheStore(tmp_path, 1000, expected_owner=os.getuid())
    private = X25519PrivateKey.from_private_bytes(b'v'*32)
    material = dict(identity=base64.b64encode(b'z'*64).decode(), wireguard_private=base64.b64encode(b'v'*32).decode(),
        wireguard_public=base64.b64encode(private.public_key().public_bytes_raw()).decode(),
        anchor=base64.b64encode(SIGNER.public_key().public_bytes_raw()).decode(), country='nl', normal_floors=[])
    if invalid == 'wireguard':
        material['wireguard_public'] = base64.b64encode(b'b'*32).decode()
    elif invalid == 'floor':
        material['normal_floors'] = [dict(payload='e30=', signature=base64.b64encode(bytes(64)).decode())]
    before = copy.deepcopy(material)
    try:
        owner = NormalOwner(storage, native)
        if invalid:
            with pytest.raises(Failure, match='CONFIGURATION'):
                owner.validate(material, Context(10000))
        else:
            owner.validate(material, Context(10000))
        assert material == before and storage.read() is None
    finally:
        storage.close()


@pytest.mark.parametrize('case', FIXTURE['vectors'], ids=lambda case: case['name'])
def test_native_authentication_and_shared_profile_validator_match_existing_vectors(native, case):
    reply = copy.deepcopy(case['reply'])
    if reply['device'] == FIXTURE['device']:
        reply['device'] = hashlib.sha256(PUBLIC).hexdigest()[:32]
    payload = base64.b64decode(reply['catalog']['payload'])
    try:
        Ed25519PublicKey.from_public_bytes(base64.b64decode(FIXTURE['anchor'])).verify(base64.b64decode(reply['catalog']['signature']), DOMAIN + payload)
    except InvalidSignature:
        reply['catalog'] = dict(payload=base64.b64encode(payload).decode(), signature=base64.b64encode(bytes(64)).decode())
    else:
        reply['catalog'] = signed(payload)
    floor = json.loads(base64.b64decode(FIXTURE['vectors'][0]['reply']['catalog']['payload']))
    floor['sequence'] = case['floor']
    if case.get('previous_hash') == '0' * 64:
        floor['gateways'][0]['tcp']['server_name'] = 'different.example.org'
    seed = reply['catalog'] if case['floor'] == 2 and case.get('previous_hash') != '0' * 64 else signed(json.dumps(floor, separators=(',', ':')).encode())
    request = dict(schema=1, id=1, action='inspect', public=base64.b64encode(PUBLIC).decode(),
                   anchor=base64.b64encode(SIGNER.public_key().public_bytes_raw()).decode(), country=reply['country'],
                   response=reply, floors=[seed])

    def check():
        result = native(request, threading.Event(), time.monotonic() + 5)
        return verified(result, 1, reply['country'], base64.b64decode(FIXTURE['wireguard_key']))

    if not case['valid']:
        with pytest.raises((Failure, ValueError)):
            check()
    else:
        profile = check()
        assert profile.sequence == 2 and profile.country == reply['country']
        assert 'LOCAL_DEVICE_KEY' not in profile.awg and 'DEVICE_CREDENTIAL' not in profile.tcp
