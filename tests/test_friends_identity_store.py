import os
from concurrent.futures import ThreadPoolExecutor

import pytest

from device_identity.device import load_or_create
from device_identity.friends import load_friends_identity


def test_resume_does_not_create_directory_or_lock(tmp_path):
    path = tmp_path / 'device'
    with pytest.raises(FileNotFoundError):
        load_friends_identity(path, create=False)
    assert not path.exists()
    path.mkdir(mode=0o700)
    with pytest.raises(FileNotFoundError):
        load_friends_identity(path, create=False)
    assert list(path.iterdir()) == []


def test_create_resume_and_concurrent_owners_keep_same_keys(tmp_path):
    path = tmp_path / 'device'
    first = load_friends_identity(path, create=True)
    original = {p.name: p.read_bytes() for p in path.iterdir()}
    with ThreadPoolExecutor(max_workers=8) as pool:
        devices = list(pool.map(lambda _: load_friends_identity(path, create=True), range(16)))
    devices.append(load_friends_identity(path, create=False))
    assert {d.reference for d in devices} == {first.reference}
    assert {d.wireguard_public_key for d in devices} == {first.wireguard_public_key}
    assert original == {p.name: p.read_bytes() for p in path.iterdir()}


def test_explicit_adoption_keeps_paired_identity_and_wg_key(tmp_path):
    path = tmp_path / 'device'
    legacy = load_or_create(path)
    original = {name: (path / name).read_bytes() for name in ('reticulum.key', 'wireguard.key')}
    with pytest.raises(ValueError, match='not enrolled'):
        load_friends_identity(path, create=False)
    assert not (path / 'friends.initialized').exists()
    adopted = load_friends_identity(path, create=True)
    assert adopted.reference == legacy.reference
    assert adopted.wireguard_public_key == legacy.wireguard_public_key
    assert original == {name: (path / name).read_bytes() for name in original}


@pytest.mark.parametrize('missing', ['reticulum.key', 'wireguard.key', 'both'])
def test_missing_registered_keys_are_never_recreated(tmp_path, missing):
    path = tmp_path / 'device'
    load_friends_identity(path, create=True)
    for name in ('reticulum.key', 'wireguard.key') if missing == 'both' else (missing,):
        (path / name).unlink()
    snapshot = {p.name: p.read_bytes() for p in path.iterdir()}
    for create in (False, True):
        with pytest.raises(ValueError, match='recovery'):
            load_friends_identity(path, create=create)
    with pytest.raises(ValueError, match='missing enrolled'):
        load_or_create(path)
    assert snapshot == {p.name: p.read_bytes() for p in path.iterdir()}


@pytest.mark.parametrize('unsafe', ['corrupt', 'permissions', 'symlink', 'hardlink'])
def test_unsafe_marker_rejected(tmp_path, unsafe):
    path = tmp_path / 'device'
    load_friends_identity(path, create=True)
    marker = path / 'friends.initialized'
    if unsafe == 'corrupt':
        marker.write_bytes(b'x' * len(marker.read_bytes()))
    elif unsafe == 'permissions':
        marker.chmod(0o644)
    elif unsafe == 'symlink':
        other = tmp_path / 'other';marker.rename(other);marker.symlink_to(other)
    else:
        os.link(marker, tmp_path / 'other')
    for create in (False, True):
        with pytest.raises((ValueError, OSError)):
            load_friends_identity(path, create=create)


def test_interrupted_creation_refuses_to_replace_identity(tmp_path, monkeypatch):
    import device_identity.friends as module
    real = module._create_key
    def fail_after_marker(directory, name, raw):
        if name == 'reticulum.key':
            raise OSError('simulated interrupted write')
        real(directory, name, raw)
    path = tmp_path / 'device'
    with monkeypatch.context() as patch:
        patch.setattr(module, '_create_key', fail_after_marker)
        with pytest.raises(OSError):
            load_friends_identity(path, create=True)
    with pytest.raises(ValueError, match='recovery'):
        load_friends_identity(path, create=True)
    assert (path / 'friends.initialized').exists()
    assert not (path / 'reticulum.key').exists()
