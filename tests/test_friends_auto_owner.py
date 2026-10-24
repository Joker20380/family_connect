import base64
import copy
import hashlib
import json
from pathlib import Path

import pytest

from device_identity.friends import load_friends_identity
from provisioning.friends_owner import FriendsOwner

FIXTURE = json.loads((Path(__file__).parent / 'fixtures/desktop-friends-catalog-v2.json').read_text())


@pytest.fixture
def existing(tmp_path):
    path = tmp_path / 'identity'
    device = load_friends_identity(path, create=True)
    anchor = tmp_path / 'update.pub'
    anchor.write_text(FIXTURE['anchor'])
    owner = FriendsOwner(path, anchor, http_factory=lambda: pytest.fail('Handoff must not fetch on an unprotected GUI socket'))
    store = owner._store()
    for country in ('ru', 'nl'):
        reply = copy.deepcopy(FIXTURE['vectors'][0]['reply'])
        reply.update(device=device.reference, country=country, address='10.83.0.2/32' if country == 'nl' else '10.84.0.2/32')
        store.accept(country, lambda floor, digest: reply)
    return owner, path, device


def inventory(path):
    return {file.name: hashlib.sha256(file.read_bytes()).hexdigest() for file in path.iterdir() if file.is_file()}


def test_auto_handoff_retains_exact_existing_identity_and_both_floors(existing):
    owner, path, device = existing
    before = inventory(path)
    retained = []

    class Driver:
        def start_auto(self, material):
            retained.append(material)
            assert base64.b64decode(material['identity']) == device._identity.get_private_key()
            assert base64.b64decode(material['wireguard_private']) == device._wireguard_key.private_bytes_raw()
            assert material['wireguard_public'] == device.wireguard_public_key
            assert material['profile'] == 'P1' and material['country'] == 'nl'
            assert len(material['normal_floors']) == 2
            assert all(set(floor) == {'payload', 'signature'} for floor in material['normal_floors'])
            return dict(state='CONNECTING', desired_connected=True, selected='')

    result = owner.connect_auto('nl', Driver(), profile='P1')
    assert result == dict(state='CONNECTING', desired_connected=True, selected='')
    assert retained == [{}] and inventory(path) == before


@pytest.mark.parametrize('failure', ['bad_signature', 'missing_marker', 'missing_key'])
def test_damaged_existing_state_cannot_start_auto_or_create_new_keys(existing, failure):
    owner, path, device = existing
    if failure == 'bad_signature':
        cache = json.loads((path / 'friends.configuration.json').read_bytes())
        cache['nl']['catalog']['signature'] = base64.b64encode(bytes(64)).decode()
        (path / 'friends.configuration.json').write_text(json.dumps(cache))
    elif failure == 'missing_marker':
        (path / 'friends.configuration.json.initialized').unlink()
    else:
        (path / 'wireguard.key').unlink()
    before = inventory(path)

    class Driver:
        def start_auto(self, material):
            pytest.fail('Invalid saved identity/configuration was handed to the service')

    with pytest.raises((ValueError, OSError)):
        owner.connect_auto('nl', Driver())
    assert inventory(path) == before


def test_backend_error_does_not_keep_handoff_material_or_mutate_state(existing):
    owner, path, device = existing
    before, retained = inventory(path), []

    class Driver:
        def start_auto(self, material):
            retained.append(material)
            raise RuntimeError('Synthetic unavailable service')

    with pytest.raises(RuntimeError):
        owner.connect_auto('ru', Driver())
    assert retained == [{}] and inventory(path) == before


def test_new_computer_cannot_inherit_another_device_identity(tmp_path):
    owner = FriendsOwner(tmp_path / 'missing', tmp_path / 'missing-anchor')
    with pytest.raises((ValueError, OSError)):
        owner.connect_auto('nl', object())
    assert not (tmp_path / 'missing').exists()
