import importlib.util
import json
import os
from pathlib import Path
import stat
from types import SimpleNamespace

import pytest

import backend
from test_mesh_service import materials


def test_linux_selects_mesh_capable_owner_without_starting_service():
    if not os.sys.platform.startswith('linux'):
        pytest.skip('Linux backend selection')
    assert isinstance(backend.backend(), backend.LinuxMesh)


def test_missing_component_never_enabled(tmp_path, monkeypatch):
    monkeypatch.setattr(backend, 'MESH_ROOT', tmp_path / 'not-installed')
    assert not backend.mesh_component_available()
    with pytest.raises(backend.BackendError, match='Install the verified'):
        backend.MeshServiceClient()


def test_unprivileged_or_symlink_system_component_rejected(tmp_path):
    target = tmp_path / 'component'
    target.write_bytes(b'public')
    target.chmod(0o666)
    with pytest.raises(backend.BackendError):
        backend._mesh_trusted(target)
    alias = tmp_path / 'alias'
    alias.symlink_to(target)
    with pytest.raises(backend.BackendError):
        backend._mesh_trusted(alias)


def test_lost_service_with_active_guard_is_not_disconnected(tmp_path, monkeypatch):
    monkeypatch.setattr(backend, 'MESH_RUN', tmp_path)
    driver = backend.LinuxMesh()
    assert driver.mesh_status()['state'] == 'DISCONNECTED'
    (tmp_path / 'active.json').write_bytes(b'synthetic ownership journal')
    state = driver.mesh_status()
    assert state['state'] == 'FAILED' and state['desired_connected']
    with pytest.raises(backend.BackendError, match='Disconnect MESH'):
        driver.connect('fctcp12345678')


@pytest.fixture
def component(tmp_path, monkeypatch):
    import mesh_ipc
    monkeypatch.setattr(backend, 'MESH_RUN', tmp_path)
    operations = []
    class Client:
        protocol = mesh_ipc
        def call(self, action, material=None):
            operations.append(action)
            if action == 'start':
                assert set(material) == {'identity', 'anchor', 'wireguard_public', 'profile'}
                return dict(state='CONNECTING', desired_connected=True)
            if action == 'stop':
                return dict(state='DISCONNECTED', desired_connected=False)
            return dict(state='CONNECTED', desired_connected=True)
    monkeypatch.setattr(backend, 'MeshServiceClient', Client)
    monkeypatch.setattr(backend.LinuxTCP, 'profiles', lambda self: [])
    monkeypatch.setattr(backend.LinuxTCP, 'active', lambda self, ident: False)
    def setup(self, action):
        operations.append('authorize-' + action)
        (tmp_path / (str(os.getuid()) + '.sock')).touch()
    monkeypatch.setattr(backend.LinuxMesh, '_mesh_setup', setup)
    return operations


def test_start_only_requests_connection_and_erases_callers_material(component):
    value = materials()
    result = backend.LinuxMesh().start_mesh(value)
    assert value == {}
    assert result['state'] == 'CONNECTING' and result['desired_connected']
    assert component == ['authorize-up', 'start']


def test_no_implicit_other_vpn_disconnect(component, monkeypatch):
    monkeypatch.setattr(backend.LinuxTCP, 'profiles', lambda self: [('fctcp12345678', 'existing')])
    monkeypatch.setattr(backend.LinuxTCP, 'active', lambda self, ident: True)
    value = materials()
    with pytest.raises(backend.BackendError, match='Disconnect the existing'):
        backend.LinuxMesh().start_mesh(value)
    assert not component and value == {}


def test_invalid_materials_never_prompt_or_start(component):
    value = materials()
    value['profile'] = 'P2'
    with pytest.raises(ValueError):
        backend.LinuxMesh().start_mesh(value)
    assert not component and value == {}


def test_explicit_disconnect_requests_cleanup_before_service_stop(component, tmp_path):
    (tmp_path / (str(os.getuid()) + '.sock')).touch()
    backend.LinuxMesh().disconnect('fcmesh0')
    assert component == ['status', 'stop', 'authorize-down']


def test_disconnect_still_revokes_service_when_private_socket_is_lost(component, tmp_path, monkeypatch):
    (tmp_path / (str(os.getuid()) + '.sock')).touch()
    monkeypatch.setattr(backend.LinuxMesh, 'mesh_status', lambda self: (_ for _ in ()).throw(backend.BackendError('lost')))
    backend.LinuxMesh().disconnect('fcmesh0')
    assert component == ['authorize-down']


def test_mesh_has_no_unowned_gui_reconnect_loop(component):
    driver = backend.LinuxMesh()
    assert not driver.allows_automatic_recovery('fcmesh0')
    with pytest.raises(backend.BackendError, match='activated account'):
        driver.connect('fcmesh0')
    with pytest.raises(backend.BackendError, match='existing system service'):
        driver.recover('fcmesh0')
    assert not component


def test_service_client_rejects_unprivileged_peer_before_private_send(tmp_path, monkeypatch):
    import mesh_ipc
    import socket
    import struct
    monkeypatch.setattr(backend, '_mesh_protocol', lambda: mesh_ipc)
    monkeypatch.setattr(backend, 'MESH_RUN', tmp_path)
    endpoint = tmp_path / (str(os.getuid()) + '.sock')
    endpoint.touch()
    original = Path.lstat
    def info(path):
        if path == endpoint:
            return SimpleNamespace(st_mode=stat.S_IFSOCK | 0o600, st_uid=os.getuid())
        return original(path)
    monkeypatch.setattr(Path, 'lstat', info)
    monkeypatch.setattr(backend, '_mesh_trusted', lambda *args, **kwargs: SimpleNamespace(st_mode=stat.S_IFDIR | 0o711))
    class Socket:
        def settimeout(self, value): pass
        def connect(self, path): pass
        def getsockopt(self, *args): return struct.pack('3i', 123, 1000, 1000)
        def close(self): pass
        def fileno(self): raise AssertionError('Private material reached unprivileged peer')
    monkeypatch.setattr(socket, 'socket', lambda *args: Socket())
    with pytest.raises(backend.BackendError, match='not privileged'):
        backend.MeshServiceClient().call('start', materials())
