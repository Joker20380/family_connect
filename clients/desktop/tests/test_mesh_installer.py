import hashlib
import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

SOURCE = Path(__file__).resolve().parents[2] / 'linux/install-mesh-bundle.py'
SPEC = importlib.util.spec_from_file_location('mesh_installer_checks', SOURCE)
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)


def bundle(path):
    payload = {name: ('synthetic public ' + name).encode() for name in set(installer.FILES) |
               {'compat/awg-helper.py', 'compat/tcp-helper.py', 'install.py', 'README.txt', 'licenses/example/LICENSE'}}
    for name, raw in payload.items():
        target = path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    manifest = dict(schema=1, architecture='amd64', source_digest='a' * 64, signing='unsigned-private-component',
                    sha256={name: hashlib.sha256(raw).hexdigest() for name, raw in payload.items()})
    (path / 'manifest.json').write_text(json.dumps(manifest))
    return payload, manifest


def test_bounded_component_inventory_and_checksum(tmp_path):
    payload, manifest = bundle(tmp_path)
    assert installer.verify(tmp_path) == (manifest, payload)
    (tmp_path / 'lib/helper').write_bytes(b'modified')
    with pytest.raises(ValueError, match='checksum'):
        installer.verify(tmp_path)


@pytest.mark.parametrize('name', ['../outside', '/etc/shadow', 'licenses/../../outside', 'licenses/./alias', 'lib/exec'])
def test_component_rejects_unlisted_and_traversal_targets(name):
    with pytest.raises(ValueError):
        installer.target(name)


def test_component_never_follows_source_symlinks(tmp_path):
    bundle(tmp_path)
    path = tmp_path / 'lib/helper'
    path.rename(tmp_path / 'original')
    path.symlink_to(tmp_path / 'original')
    with pytest.raises(ValueError, match='symlink'):
        installer.verify(tmp_path)


def test_component_rejects_incomplete_manifest(tmp_path):
    _, manifest = bundle(tmp_path)
    del manifest['sha256']['compat/tcp-helper.py']
    (tmp_path / 'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match='Incomplete'):
        installer.verify(tmp_path)


@pytest.fixture
def filesystem(tmp_path, monkeypatch):
    root = tmp_path / 'system/mesh'
    root.mkdir(parents=True)
    backups = tmp_path / 'backups'
    capability = root / 'capabilities.json'
    monkeypatch.setattr(installer, 'ROOT', root)
    monkeypatch.setattr(installer, 'BACKUPS', backups)
    monkeypatch.setattr(installer, 'CAPABILITY', capability)
    monkeypatch.setattr(installer, 'AUTO_CAPABILITY', root / 'auto-capabilities.json')
    monkeypatch.setattr(installer, 'directory', lambda path: path.mkdir(parents=True, exist_ok=True))
    def trusted(path, directory=False):
        assert path.is_relative_to(tmp_path) and not path.is_symlink()
        return path.lstat()
    monkeypatch.setattr(installer, 'trusted', trusted)
    def target(name):
        if name.startswith('compat/'):
            kind = name.split('/')[1].split('-')[0]
            return tmp_path / 'system' / kind / 'helper', 0o755
        return root / name.replace('/', '_'), 0o644
    monkeypatch.setattr(installer, 'target', target)
    operations = []
    def command(*args):
        operations.append(args)
        if args == ('systemctl', '--version'):
            return SimpleNamespace(stdout='systemd 255\n')
        assert not capability.exists()
        if args[0] == '/usr/bin/python3':
            assert args == ('/usr/bin/python3', '-I', '-S', str(root / 'rns/fc-rns.pyz'), '--version')
            return SimpleNamespace(stdout=json.dumps(dict(rns_protocol=1, rns='1.5.1', pyserial='3.5', crypto_provider='internal')))
        if args[-1] == '--version':
            return SimpleNamespace(stdout=json.dumps(dict(source_manifest='a' * 64, core_reference='android106-native105',
                bridge_protocol=1, materials_protocol=1, auto_policy_protocol=1, normal_configuration_protocol=1,
                chat_ipc_protocol=1, private_chat_endpoint='inherited-unix-stream',
                os='linux', arch='amd64', profiles=['P0', 'P1'])))
        assert args == ('systemctl', 'daemon-reload')
        return SimpleNamespace(stdout='')
    monkeypatch.setattr(installer, 'command', command)
    return root, operations


def test_install_updates_existing_helpers_but_not_user_identity(filesystem, tmp_path):
    root, operations = filesystem
    source = tmp_path / 'bundle'
    payload, _ = bundle(source)
    awg = tmp_path / 'system/awg'
    awg.mkdir()
    (awg / 'helper').write_bytes(b'old helper')
    identity = tmp_path / 'user/identity'
    identity.parent.mkdir()
    identity.write_bytes(b'synthetic private state never read by installer')
    backup = installer.apply(payload, 'a' * 64)
    assert (awg / 'helper').read_bytes() == payload['compat/awg-helper.py']
    assert (awg / 'backend.py').read_bytes() == payload['lib/backend.py']
    assert (awg / 'awg_lifecycle.py').read_bytes() == payload['lib/awg_lifecycle.py']
    assert not (tmp_path / 'system/tcp').exists()
    assert identity.read_bytes() == b'synthetic private state never read by installer'
    assert json.loads((root / 'capabilities.json').read_bytes())['materials_protocol'] == 1
    assert len(operations) == 4 and operations[3] == ('systemctl', 'daemon-reload')
    assert json.loads((root / 'capabilities.json').read_bytes())['intent_protocol'] == 1
    assert json.loads((root / 'auto-capabilities.json').read_bytes()) == dict(schema=1,service_protocol=1,catalog_protocol=1,source_digest='a'*64)
    record = json.loads((backup / 'restore.json').read_bytes())
    assert len(record['previous']) == 1
    assert (backup / record['previous'][0]['file']).read_bytes() == b'old helper'


def test_partial_install_restores_only_own_previous_files(filesystem, tmp_path, monkeypatch):
    root, operations = filesystem
    payload, _ = bundle(tmp_path / 'bundle')
    helper = root / 'lib_helper'
    helper.write_bytes(b'previous helper')
    untouched = root / 'unrelated'
    untouched.write_bytes(b'preserve')
    original = installer.atomic
    failed = False
    def atomic(path, raw, mode):
        nonlocal failed
        if path == root / 'lib_backend.py' and not failed:
            failed = True
            raise OSError('synthetic disk failure')
        original(path, raw, mode)
    monkeypatch.setattr(installer, 'atomic', atomic)
    with pytest.raises(OSError):
        installer.apply(payload, 'a' * 64)
    assert helper.read_bytes() == b'previous helper'
    assert not (root / 'auto-capabilities.json').exists()
    assert untouched.read_bytes() == b'preserve'
    assert not (root / 'capabilities.json').exists()
    assert not (root / 'bin_fc-mesh').exists()
    assert operations == [('systemctl', '--version'), ('systemctl', 'daemon-reload')]


def test_rns_runtime_mismatch_rolls_back_before_advertising_capability(filesystem, tmp_path, monkeypatch):
    root, operations = filesystem
    payload, _ = bundle(tmp_path / 'bundle')
    previous = root / 'rns_fc-rns.pyz'
    previous.write_bytes(b'previous verified runtime')
    original = installer.command
    def command(*args):
        if args[0] == '/usr/bin/python3':
            return SimpleNamespace(stdout='{}')
        return original(*args)
    monkeypatch.setattr(installer, 'command', command)
    with pytest.raises(ValueError, match='RNS runtime'):
        installer.apply(payload, 'a' * 64)
    assert previous.read_bytes() == b'previous verified runtime'
    assert not (root / 'capabilities.json').exists()
    assert not (root / 'bin_fc-mesh').exists()
    assert operations[-1] == ('systemctl', 'daemon-reload')


def test_unsupported_service_manager_rejected_before_any_install(filesystem, tmp_path, monkeypatch):
    root, _ = filesystem
    payload, _ = bundle(tmp_path / 'bundle')
    monkeypatch.setattr(installer, 'command', lambda *args: SimpleNamespace(stdout='systemd 249\n'))
    with pytest.raises(ValueError, match='systemd254'):
        installer.apply(payload, 'a' * 64)
    assert not list(root.iterdir())


@pytest.mark.parametrize('name', ['guard.json', 'normal.json', 'awg'])
@pytest.mark.parametrize('broken_link', [False, True])
def test_install_refuses_pending_auto_ownership_even_when_no_tun_exists(tmp_path, monkeypatch, name, broken_link):
    monkeypatch.setattr(installer, 'LOCKS', ())
    monkeypatch.setattr(installer, 'Path', lambda path: tmp_path / str(path).lstrip('/'))
    path = tmp_path / ('run/family-connect-awg/active.json' if name == 'awg' else 'run/family-connect-auto/'+name)
    path.parent.mkdir(parents=True)
    if broken_link:
        path.symlink_to(path.parent / 'missing')
    else:
        path.write_text('synthetic pending Auto ownership')
    monkeypatch.setattr(installer, 'command', lambda *args: pytest.fail('No service operation before ownership cleanup'))
    with pytest.raises(ValueError, match='Finish VPN cleanup'):
        installer.acquire()
    assert path.is_symlink() if broken_link else path.read_text() == 'synthetic pending Auto ownership'
