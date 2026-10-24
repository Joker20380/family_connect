import base64
from pathlib import Path

import pytest

from device_identity.friends import load_friends_identity
from provisioning.friends_owner import FriendsOwner


def test_existing_computer_identity_passes_only_to_private_driver(tmp_path):
    path = tmp_path / 'identity'
    path.parent.mkdir(exist_ok=True, mode=0o700)
    device = load_friends_identity(path, create=True)
    original = {name: (path / name).read_bytes() for name in ('reticulum.key', 'wireguard.key', 'friends.initialized')}
    anchor = tmp_path / 'anchor.pub'
    anchor.write_bytes(base64.b64encode(b'a' * 32))
    owner = FriendsOwner(path, anchor)
    assert owner.has_existing_identity()
    held = []
    class Driver:
        def start_mesh(self, material):
            held.append(material)
            assert base64.b64decode(material['identity']) == original['reticulum.key']
            assert material['wireguard_public'] == device.wireguard_public_key
            assert material['profile'] == 'P1'
            return dict(state='CONNECTING', desired_connected=True)
    result = owner.connect_mesh(Driver(), 'P1')
    assert result == dict(profile='fcmesh0', transport='mesh', requested_profile='P1', state='CONNECTING', desired_connected=True)
    assert held == [{}]
    assert original == {name: (path / name).read_bytes() for name in original}


def test_mesh_never_creates_or_clones_an_identity(tmp_path):
    anchor = tmp_path / 'anchor.pub'
    anchor.write_bytes(base64.b64encode(b'a' * 32))
    path = tmp_path / 'missing'
    owner = FriendsOwner(path, anchor)
    assert not owner.has_existing_identity()
    assert not path.exists()
    with pytest.raises((ValueError, OSError)):
        owner.connect_mesh(object())
    assert not path.exists()
    with pytest.raises(ValueError, match='Unsupported MESH profile'):
        owner.connect_mesh(object(), 'P2')
