import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import zipfile

import pytest

from scripts import package_credential_renewal as package


@pytest.fixture
def source(tmp_path):
    root = tmp_path / 'source'
    root.mkdir()
    subprocess.run(['git', 'init', '-q', str(root)], check=True)
    for name in package.SOURCES:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((package.ROOT / name).read_bytes())
    subprocess.run(['git', 'add', '.'], cwd=root, check=True)
    subprocess.run(['git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                    'commit', '-qm', 'synthetic renewal source'], cwd=root, check=True)
    return root


def test_renewal_package_pins_every_source_and_shared_profile_module(source, tmp_path):
    (source / package.DIRECTORY / 'production_transport.py').write_text('dirty_work_must_not_ship\n')
    first, second = tmp_path / 'first.tar.gz', tmp_path / 'second.tar.gz'
    initial = package.build(first, 'HEAD', repository=source)
    assert package.build(second, 'HEAD', repository=source) == initial
    assert first.read_bytes() == second.read_bytes()
    extracted = tmp_path / 'extracted'
    extracted.mkdir(mode=0o700)
    with tarfile.open(first, 'r:gz') as archive:
        manifest = json.load(archive.extractfile('source-manifest.json'))
        assert manifest['production_configuration'] == 'absent' and manifest['operation_permit'] is None
        assert manifest['source_commit'] == subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source).decode().strip()
        assert len(manifest['source_files']) == 13
        assert manifest['source_sha256'] == package.digest(package.encode(manifest['source_files']))
        assert set(archive.getnames()) == set(manifest['files']) | {'source-manifest.json'}
        for member in archive.getmembers():
            assert member.isfile() and member.uid == member.gid == member.mtime == 0
            assert member.uname == member.gname == ''
            raw = archive.extractfile(member).read()
            if member.name != 'source-manifest.json':
                assert hashlib.sha256(raw).hexdigest() == manifest['files'][member.name]
            if member.name.startswith('renewal/'):
                assert hashlib.sha256(raw).hexdigest() == manifest['source_files'][Path(member.name).name]
                assert not re.search(rb'\b(?:\d{1,3}\.){3}\d{1,3}\b|/opt/apps/[a-z]|dirty_work_must_not_ship|-----BEGIN [A-Z ]*PRIVATE KEY', raw)
        archive.extractall(extracted, filter='data')
    with zipfile.ZipFile(extracted / 'api.pyz') as archive:
        api_manifest = json.loads(archive.read('source-manifest.json'))
        assert api_manifest['source_commit'] == manifest['source_commit']
        assert archive.read('control/friends/profile_store.py') == (package.ROOT / 'control/friends/profile_store.py').read_bytes()
        assert package.digest((extracted / 'api.pyz').read_bytes()) == manifest['api_sha256']
        assert {'LICENSE', 'THIRD_PARTY_NOTICES.md'} <= set(api_manifest['files'])
    for module in ('node.py', 'runtime_controller.py', 'renewal_cli.py', 'scheduled_evaluate.py'):
        result = subprocess.run([sys.executable, '-E', '-s', '-B', str(extracted / 'renewal' / module), '--help'],
                                capture_output=True, check=True)
        assert result.stdout and not result.stderr
    probe = ('import sys;sys.path.insert(0,sys.argv[1]);sys.path.insert(0,sys.argv[2]);'
             'import node,renewal_health;from control.friends import profile_store;'
             'assert profile_store.__file__.startswith(sys.argv[2]+"/");assert len(node.NODE_MODULES)==7')
    subprocess.run([sys.executable, '-I', '-B', '-c', probe, str(extracted / 'renewal'), str(extracted / 'api.pyz')],
                   capture_output=True, check=True)
    with pytest.raises(FileExistsError):
        package.build(first, 'HEAD', repository=source)


def test_renewal_missing_source_member_rejected(source, tmp_path):
    subprocess.run(['git', 'rm', '-q', package.DIRECTORY + '/node.py'], cwd=source, check=True)
    subprocess.run(['git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                    'commit', '-qm', 'incomplete fixture'], cwd=source, check=True)
    with pytest.raises(ValueError, match='Missing committed renewal source'):
        package.build(tmp_path / 'missing.tar.gz', 'HEAD', repository=source)
