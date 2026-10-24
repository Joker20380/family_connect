import base64
import copy
import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from device_identity.friends import load_friends_identity
from provisioning.friends_catalog import DOMAIN, verify_catalog, verify
from provisioning.friends_owner import FriendsOwner
from provisioning.friends_store import FriendsConfigurationStore

FIXTURE = json.loads((Path(__file__).parent/'fixtures/desktop-friends-catalog-v2.json').read_text())


@pytest.fixture
def state(tmp_path):
    device = load_friends_identity(tmp_path/'identity', create=True)
    signer = Ed25519PrivateKey.from_private_bytes(bytes([9])*32)
    anchor = signer.public_key().public_bytes_raw()
    store = FriendsConfigurationStore(tmp_path/'identity', device, anchor)
    def reply(sequence=2, country='nl', mutate=None):
        value = copy.deepcopy(FIXTURE['vectors'][0]['reply'])
        payload = json.loads(base64.b64decode(value['catalog']['payload']))
        payload['sequence'] = sequence
        if mutate is not None:
            mutate(payload)
        raw = json.dumps(payload, separators=(',', ':')).encode()
        value['catalog'] = dict(payload=base64.b64encode(raw).decode(), signature=base64.b64encode(signer.sign(DOMAIN+raw)).decode())
        value.update(device=device.reference, country=country, address='10.83.0.2/32' if country == 'nl' else '10.84.0.2/32')
        return value
    return store, reply, tmp_path


def inventory(path):
    return {file.name:hashlib.sha256(file.read_bytes()).hexdigest() for file in path.iterdir() if file.is_file()}


def test_public_floor_is_not_an_authenticated_device_profile(state):
    store, reply, _ = state
    response = reply()
    floor = verify_catalog(response['catalog'], store.anchor)
    assert floor.sequence == 2 and not hasattr(floor, 'tcp') and not hasattr(floor, 'awg')
    response['device'] = '0'*32
    with pytest.raises(ValueError):
        verify(response, store.anchor, store.device.reference, 'nl', store.device._wireguard_key.private_bytes_raw())


def test_service_floor_preserves_identity_and_old_profiles_and_blocks_manual_rollback(state):
    store, reply, _ = state
    store.accept('nl', lambda *_:reply())
    before = inventory(store.path)
    envelope = reply(3)['catalog']
    store.merge_catalog_floor(envelope)
    after = inventory(store.path)
    assert {name:after[name] for name in before} == before
    assert set(after)-set(before) == {'friends.catalog-floor.json', 'friends.catalog-floor.json.initialized'}
    assert (store.path/'friends.catalog-floor.json').stat().st_mode & 0o777 == 0o600
    assert set(json.loads((store.path/'friends.catalog-floor.json').read_text())) == {'schema','device','catalog'}
    received = []
    def stale(floor, digest):
        received.append((floor,digest))
        return reply(2,'ru')
    with pytest.raises(ValueError):
        store.accept('ru', stale)
    assert received == [(3,verify_catalog(envelope,store.anchor).catalog_hash)]
    assert inventory(store.path) == after
    assert store.signed_floors() == [envelope]


def test_lower_root_floor_never_downgrades_newer_user_floor_and_merge_is_idempotent(state):
    store, reply, _ = state
    store.accept('nl', lambda *_:reply(4))
    store.merge_catalog_floor(reply(3)['catalog'])
    before = inventory(store.path)
    store.merge_catalog_floor(reply(2)['catalog'])
    store.merge_catalog_floor(None)
    assert inventory(store.path) == before
    assert verify_catalog(store.signed_floors()[0],store.anchor).sequence == 4


def test_same_sequence_changed_signed_body_rejected_without_touching_old_state(state):
    store, reply, _ = state
    store.merge_catalog_floor(reply(3)['catalog'])
    before = inventory(store.path)
    changed = reply(3, mutate=lambda payload:payload['gateways'][0]['tcp'].update(port=8443))['catalog']
    with pytest.raises(ValueError):
        store.merge_catalog_floor(changed)
    assert inventory(store.path) == before


@pytest.mark.parametrize('failure', ['signature','extra','device-response','invalid-template','large','foreign-anchor'])
def test_invalid_public_floor_cannot_become_a_migration(state, failure):
    store, reply, _ = state
    envelope = reply()['catalog']
    before = inventory(store.path)
    if failure == 'signature':envelope['signature'] = base64.b64encode(bytes(64)).decode()
    elif failure == 'extra':envelope['device'] = store.device.reference
    elif failure == 'device-response':envelope = reply()
    elif failure == 'invalid-template':envelope = reply(mutate=lambda payload:payload.update(access='public'))['catalog']
    elif failure == 'large':envelope['payload'] = base64.b64encode(bytes(8193)).decode()
    else:store.anchor = Ed25519PrivateKey.generate().public_key().public_bytes_raw()
    with pytest.raises(ValueError):
        store.merge_catalog_floor(envelope)
    assert inventory(store.path) == before


@pytest.mark.parametrize('after_rename', [False, True])
def test_interrupted_floor_migration_keeps_profiles_and_retries_atomically(state, monkeypatch, after_rename):
    store, reply, _ = state
    store.accept('nl',lambda *_:reply(2))
    before = inventory(store.path)
    replace = os.replace
    def interrupted(*args, **kwargs):
        if after_rename:
            replace(*args, **kwargs)
        raise OSError('synthetic migration interruption')
    with monkeypatch.context() as context:
        context.setattr(os,'replace',interrupted)
        with pytest.raises(OSError):
            store.merge_catalog_floor(reply(3)['catalog'])
    after = inventory(store.path)
    assert {name:after[name] for name in before} == before
    store.merge_catalog_floor(reply(3)['catalog'])
    assert store.signed_floors() == [reply(3)['catalog']]
    assert not list(store.path.glob('.friends-floor-*'))


def test_concurrent_floor_merges_keep_the_highest_verified_sequence(state):
    store, reply, _ = state
    with ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(lambda sequence:store.merge_catalog_floor(reply(sequence)['catalog']),[2,4,3,5,2,4]))
    assert verify_catalog(store.signed_floors()[0],store.anchor).sequence == 5


@pytest.mark.parametrize('damage',['missing','symlink','mode','owner-binding'])
def test_damaged_floor_prevents_http_and_is_not_silently_reset(state, damage):
    store, reply, folder = state
    store.merge_catalog_floor(reply(3)['catalog'])
    path = store.path/'friends.catalog-floor.json'
    if damage == 'missing':path.unlink()
    elif damage == 'symlink':
        external = folder/'copy.json'; external.write_bytes(path.read_bytes()); path.unlink(); path.symlink_to(external)
    elif damage == 'mode':path.chmod(0o644)
    else:
        record=json.loads(path.read_text()); record['device']='0'*32;path.write_text(json.dumps(record))
    with pytest.raises((ValueError,OSError)):
        store.accept('nl',lambda *_:pytest.fail('No HTTP after damaged floor'))


def test_auto_handoff_uses_supplemental_floor_without_replacing_keys(state):
    store, reply, folder = state
    store.accept('nl',lambda *_:reply(2))
    store.merge_catalog_floor(reply(3)['catalog'])
    anchor=folder/'anchor';anchor.write_text(base64.b64encode(store.anchor).decode())
    owner=FriendsOwner(store.path,anchor,http_factory=lambda:pytest.fail('Auto handoff must not fetch'))
    before=inventory(store.path)
    retained=[]
    class Driver:
        def start_auto(self,material):
            assert material['normal_floors']==[reply(3)['catalog']]
            retained.append(material)
            return dict(state='CONNECTING',desired_connected=True)
    owner.connect_auto('nl',Driver())
    assert inventory(store.path)==before and retained==[{}]


def test_invalid_root_floor_is_rejected_before_configuration_http(state):
    store, reply, folder = state
    anchor=folder/'anchor';anchor.write_text(base64.b64encode(store.anchor).decode())
    owner=FriendsOwner(store.path,anchor,http_factory=lambda:pytest.fail('No HTTP before root floor validation'))
    class Driver:
        def normal_catalog(self):
            return dict(payload='bad',signature='bad')
    with pytest.raises(ValueError):
        owner.configuration('nl',Driver())
