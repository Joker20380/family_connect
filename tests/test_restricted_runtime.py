import base64
import ast
import configparser
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import socket
import subprocess
import sys
import time
import zipfile

from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat
import pytest

from control.friends import restricted_sync
from scripts.package_restricted_runtime import ARCHIVE, CONTRACT, ROOT, build, smoke
from test_friends_restricted import configured


PREFIX = '/opt/apps/family_connect'
REQUIRED = json.loads((ROOT / CONTRACT / 'runtime-files.json').read_text())


@pytest.fixture
def bundle(tmp_path):
    output = tmp_path / 'opt/apps/family_connect/friends-access'
    build(output)
    return output


def environment(material=None):
    result = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    result.pop('PYTHONPATH', None)
    result.pop('PYTHONHOME', None)
    if material is not None:
        result['FC_FRIENDS_RESTRICTED_DIR'] = str(material)
    return result


def unit_command(bundle):
    unit = configparser.ConfigParser(interpolation=None, strict=False)
    unit.read(bundle / 'family-connect-restricted-sync.service')
    command = shlex.split(unit['Service']['ExecStart'])
    assert command[:4] == [PREFIX + '/friends-access/venv/bin/python', '-I',
                           PREFIX + '/friends-access/' + ARCHIVE, 'sync']
    assert unit['Service']['WorkingDirectory'] == PREFIX + '/friends-access/app'
    command = [item.replace(PREFIX, str(bundle.parent)) for item in command]
    command[0] = sys.executable
    return command


def material_fixture(bundle, now=None):
    material = bundle.parent / 'friends-restricted'
    material.mkdir(mode=0o700)
    service, _, _ = configured(bundle, int(time.time()) if now is None else now)
    with service.access.db() as database:
        database.execute('CREATE TABLE restricted_crl_sequence (singleton INTEGER PRIMARY KEY, sequence INTEGER NOT NULL)')
        database.execute('INSERT INTO restricted_crl_sequence VALUES (1,1)')
    values = {'issuer.json': json.dumps(service.manifest).encode(),
              'issuer.key': service.signing_key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()),
              'anchor.pub': base64.b64encode(service.anchor),
              'admission.json': b'{"devices":[]}', 'revocations.pem': service.crl_source(),
              'sync.key': b'offline-test-placeholder', 'known_hosts': b'offline-test-placeholder'}
    for name, raw in values.items():
        path = material / name
        path.write_bytes(raw)
        path.chmod(0o600)
    return material, service


def snapshot(root):
    return {str(path.relative_to(root)): (hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_mtime_ns)
            for path in root.rglob('*') if path.is_file()}


def test_old_runtime_layout_reproduces_missing_clients(tmp_path):
    app = tmp_path / 'friends-access/app'
    app.mkdir(parents=True)
    for folder in ('control/friends', 'device_identity', 'provisioning'):
        for source in (ROOT / folder).glob('*.py'):
            target = app / source.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
    clean = environment()
    clean.pop('PYTHONPATH', None)
    result = subprocess.run([sys.executable, '-m', 'control.friends.restricted_sync', '--help'],
                            cwd=app, env=clean, capture_output=True, timeout=30)
    assert result.returncode != 0
    assert b"ModuleNotFoundError: No module named 'clients'" in result.stderr


def test_final_artifact_isolated_imports_and_exact_sources(bundle, tmp_path):
    smoke(bundle, sys.executable)
    with zipfile.ZipFile(bundle / ARCHIVE) as archive:
        sources = {name for name in archive.namelist() if name.endswith('.py')}
        assert sources == set(REQUIRED) | {'__main__.py'}
        for name in REQUIRED:
            assert archive.read(name) == (ROOT / name).read_bytes() == (bundle / 'app' / name).read_bytes()
        assert {name for name in sources if name.startswith('clients/')} == {'clients/desktop/profile_config.py'}
    probe = ('import runpy,sys,json;sys.argv=[sys.argv[1],"--help"]\n'
             'try:runpy.run_path(sys.argv[0],run_name="__main__")\n'
             'except SystemExit as result:assert result.code==0\n'
             'names=["control.friends.restricted_sync","control.friends.restricted_admin",'
             '"provisioning.friends_catalog","clients.desktop.profile_config","device_identity.device"]\n'
             'print(json.dumps({name:sys.modules[name].__file__ for name in names}))')
    result = subprocess.run([sys.executable, '-I', '-c', probe, str(bundle / ARCHIVE)],
                            cwd=tmp_path, env=environment(), capture_output=True, text=True, timeout=30, check=True)
    modules = json.loads(result.stdout.splitlines()[-1])
    assert all(path.startswith(str(bundle / ARCHIVE) + '/') for path in modules.values())
    assert not any(name in modules for name in ('clients.desktop.app', 'clients.desktop.backend'))


@pytest.mark.parametrize('missing', REQUIRED)
def test_manifest_rejects_missing_source(tmp_path, missing):
    source = tmp_path / 'source'
    for name in [*REQUIRED, str(CONTRACT / 'runtime-files.json')]:
        target = source / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    (source / missing).unlink()
    with pytest.raises(ValueError, match='Missing or unsafe runtime source: ' + missing):
        build(tmp_path / 'incomplete', source)
    assert not (tmp_path / 'incomplete').exists()


@pytest.mark.parametrize('missing', [name for name in REQUIRED if not name.endswith('__init__.py')])
def test_missing_transitive_module_fails_despite_checkout_pythonpath(bundle, tmp_path, missing):
    broken = tmp_path / 'broken.pyz'
    with zipfile.ZipFile(bundle / ARCHIVE) as original, zipfile.ZipFile(broken, 'w') as output:
        for entry in original.infolist():
            if entry.filename != missing:
                output.writestr(entry, original.read(entry))
    result = subprocess.run([sys.executable, '-I', str(broken), '--help'], cwd=ROOT,
                            env=dict(environment(), PYTHONPATH=str(ROOT)), capture_output=True, timeout=30)
    assert result.returncode != 0
    assert b'ImportError' in result.stderr or b'ModuleNotFoundError' in result.stderr


def test_profile_dependency_stays_pure_stdlib():
    source = ast.parse((ROOT / 'clients/desktop/profile_config.py').read_text())
    imports = set()
    for node in ast.walk(source):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.add(node.module)
    assert imports == {'base64', 'ipaddress', 're', 'json', 'uuid'}


@pytest.mark.parametrize('working_directory', ['app', 'unrelated'])
def test_actual_unit_cli_pre_network_check_without_mutations(bundle, tmp_path, working_directory):
    material, _ = material_fixture(bundle)
    before = snapshot(bundle.parent)
    result = subprocess.run([*unit_command(bundle), '--check'],
                            cwd=bundle / 'app' if working_directory == 'app' else tmp_path,
                            env=environment(material), capture_output=True, timeout=30)
    assert result.returncode == 0 and result.stderr == b''
    assert result.stdout == b'Restricted runtime pre-network check passed\n'
    assert snapshot(bundle.parent) == before


@pytest.mark.parametrize('invalid', ['issuer.json', 'issuer.key', 'anchor.pub', 'admission.json', 'revocations.pem'])
def test_packaged_check_rejects_bad_authority_without_output_or_writes(bundle, invalid):
    material, _ = material_fixture(bundle)
    (material / invalid).write_bytes(b'private-test-marker-invalid')
    before = snapshot(bundle.parent)
    result = subprocess.run([*unit_command(bundle), '--check'], cwd=bundle.parent,
                            env=environment(material), capture_output=True, timeout=30)
    assert result.returncode == 1 and result.stdout == b''
    assert result.stderr == b'Restricted synchronization unavailable\n'
    assert snapshot(bundle.parent) == before


def test_check_cannot_publish_start_ssh_or_open_socket(bundle, monkeypatch):
    material, service = material_fixture(bundle)
    monkeypatch.setenv('FC_FRIENDS_RESTRICTED_DIR', str(material))
    def forbidden(*args, **kwargs):
        pytest.fail('Pre-network check invoked a mutation/network boundary')
    monkeypatch.setattr(restricted_sync, 'publish_crl', forbidden)
    monkeypatch.setattr(subprocess, 'run', forbidden)
    monkeypatch.setattr(socket, 'socket', forbidden)
    restricted_sync.check(service.access, '186.246.45.246', material / 'sync.key', material / 'known_hosts')


@pytest.mark.parametrize('invalid', ['expired-crl', 'sequence-mismatch', 'private-mode'])
def test_check_rejects_invalid_local_state_without_repair(bundle, invalid):
    material, service = material_fixture(bundle, int(time.time()) - 7200 if invalid == 'expired-crl' else None)
    if invalid == 'sequence-mismatch':
        with service.access.db() as database:
            database.execute('UPDATE restricted_crl_sequence SET sequence=2')
    if invalid == 'private-mode':
        (material / 'issuer.key').chmod(0o644)
    before = snapshot(bundle.parent)
    result = subprocess.run([*unit_command(bundle), '--check'], cwd=bundle.parent,
                            env=environment(material), capture_output=True, timeout=30)
    assert result.returncode == 1 and result.stdout == b''
    assert result.stderr == b'Restricted synchronization unavailable\n'
    assert snapshot(bundle.parent) == before


def test_gateway_forced_command_targets_same_isolated_artifact(bundle):
    wrapper = (bundle / 'restricted-sync-command').read_text()
    command = shlex.split(wrapper.split('exec ', 1)[1].replace('\\\n', ''))
    assert command[:4] == [PREFIX + '/friends-access/venv/bin/python', '-I',
                           PREFIX + '/friends-access/' + ARCHIVE, 'gateway']
    assert '[ "${SSH_ORIGINAL_COMMAND-}" = restricted-sync ] || exit 126' in wrapper
    assert '[ "$#" -eq 0 ] || exit 126' in wrapper
    for original_command, arguments in [('id', []), ('restricted-sync', ['unexpected'])]:
        result = subprocess.run(['/bin/sh', str(bundle / 'restricted-sync-command'), *arguments],
                                env=dict(environment(), SSH_ORIGINAL_COMMAND=original_command), capture_output=True, timeout=5)
        assert result.returncode == 126 and not result.stdout
    command = [item.replace(PREFIX, str(bundle.parent)) for item in command]
    command[0] = sys.executable
    result = subprocess.run([*command, '--help'], cwd=bundle.parent, env=environment(),
                            capture_output=True, timeout=30)
    assert result.returncode == 0 and not result.stderr
