import base64
import fcntl
import json
import os
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'linux'))
import mesh_intent as intent


def materials():
    return dict(identity=base64.b64encode(b'x' * 64).decode(), anchor=base64.b64encode(b'a' * 32).decode(),
                wireguard_public=base64.b64encode(b'w' * 32).decode(), profile='P1')


class Manager:
    def __init__(self):
        self.descriptor = None
        self.fail = False

    def store(self, descriptor):
        assert self.descriptor is None
        self.descriptor = os.dup(descriptor)
        if self.fail:
            raise OSError('synthetic manager rejection')

    def remove(self):
        if self.descriptor is not None:
            os.close(self.descriptor)
            self.descriptor = None


@pytest.fixture
def owner(tmp_path):
    manager = Manager()
    current = intent.Intent(tmp_path / 'intent.json', 1000, manager, expected_owner=os.getuid())
    try:
        yield current, manager
    finally:
        current.close()
        manager.remove()


def test_private_material_survives_owner_restart_without_file_copy(owner):
    current, manager = owner
    current.begin(materials())
    raw = current.path.read_text()
    assert all(value not in raw for key, value in materials().items() if key != 'profile')
    assert set(json.loads(raw)) == {'schema', 'uid', 'generation', 'desired', 'recoveries'}
    assert current.path.stat().st_mode & 0o777 == 0o600
    assert fcntl.fcntl(manager.descriptor, fcntl.F_GET_SEALS) & intent.SEALS == intent.SEALS
    with pytest.raises(OSError):
        os.ftruncate(manager.descriptor, 1)
    current.close()
    restarted = intent.Intent(current.path, 1000, manager, expected_owner=os.getuid())
    try:
        assert restarted.recover(os.dup(manager.descriptor)) == materials()
        assert restarted.read()['recoveries'] == 1
    finally:
        restarted.close()


def test_explicit_revoke_prevents_recovery_even_before_manager_removes_fd(owner):
    current, manager = owner
    current.begin(materials())
    current.revoke()
    assert not current.desired()
    restored = intent.Intent(current.path, 1000, manager, expected_owner=os.getuid())
    try:
        assert restored.recover(os.dup(manager.descriptor)) is None
        assert manager.descriptor is None
    finally:
        restored.close()


def test_memory_revocation_wins_over_failed_disk_fence(owner, monkeypatch):
    current, manager = owner
    current.begin(materials())
    monkeypatch.setattr(intent, 'private_write', lambda *args: (_ for _ in ()).throw(OSError('synthetic')))
    with pytest.raises(OSError):
        current.revoke()
    assert current.desired()
    restored = intent.Intent(current.path, 1000, manager, expected_owner=os.getuid())
    try:
        assert restored.recover(os.dup(manager.descriptor)) is None
    finally:
        restored.close()


def test_manager_failure_never_commits_connected_intent(owner):
    current, manager = owner
    manager.fail = True
    with pytest.raises(OSError):
        current.begin(materials())
    assert not current.path.exists() and current.descriptor is None and manager.descriptor is None


@pytest.mark.parametrize('change', [{'uid': 1001}, {'generation': 'b' * 32}, {'desired': 1}, {'recoveries': -1}])
def test_wrong_owner_generation_and_invalid_fence_never_restore_keys(owner, change):
    current, manager = owner
    current.begin(materials())
    value = json.loads(current.path.read_text())
    value.update(change)
    current.path.write_text(json.dumps(value))
    restored = intent.Intent(current.path, 1000, manager, expected_owner=os.getuid())
    try:
        with pytest.raises(ValueError):
            restored.recover(os.dup(manager.descriptor))
    finally:
        restored.close()


def test_regular_disk_file_cannot_become_recovery_credential(owner, tmp_path):
    current, _ = owner
    disk = tmp_path / 'not-memory'
    disk.write_bytes(b'not a recovery object')
    descriptor = os.open(disk, os.O_RDWR)
    with pytest.raises(ValueError):
        current.recover(descriptor)


def test_duplicate_intent_fields_and_unsupported_profile_rejected(owner):
    current, _ = owner
    value = materials()
    value['profile'] = 'P2'
    with pytest.raises(ValueError):
        current.begin(value)
    assert not current.path.exists()
    current.path.write_bytes(b'{"schema":1,"schema":1}')
    current.path.chmod(0o600)
    with pytest.raises(ValueError):
        current.desired()
