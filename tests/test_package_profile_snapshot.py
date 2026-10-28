import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile

import pytest

from scripts import package_profile_snapshot as package


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
                    'commit', '-qm', 'synthetic snapshot source'], cwd=root, check=True)
    return root


def test_snapshot_deterministic_committed_source_and_safe_import(source, tmp_path):
    (source / 'control/friends/profile_snapshot.py').write_text('dirty_work_must_not_ship\n')
    first, second = tmp_path / 'first.pyz', tmp_path / 'second.pyz'
    initial = package.build(first, 'HEAD', repository=source)
    repeated = package.build(second, 'HEAD', repository=source)
    assert first.read_bytes() == second.read_bytes() and initial == repeated
    with zipfile.ZipFile(first) as archive:
        manifest = json.loads(archive.read('source-manifest.json'))
        assert manifest['source_commit'] == subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source).decode().strip()
        assert manifest['entrypoint'] == 'control.friends.profile_snapshot'
        assert manifest['binding'] == 'unbound' and manifest['operation_permit'] is None
        assert manifest['production_configuration'] == 'absent'
        assert {'LICENSE', 'THIRD_PARTY_NOTICES.md', 'control/friends/profile_store.py'} <= set(manifest['files'])
        assert set(archive.namelist()) == set(manifest['files']) | {'source-manifest.json'}
        for name, expected in manifest['files'].items():
            raw = archive.read(name)
            assert hashlib.sha256(raw).hexdigest() == expected
            assert not re.search(rb'FC-[A-Z0-9]{4}-[A-Z0-9]{4}|-----BEGIN [A-Z ]*PRIVATE KEY|dirty_work_must_not_ship', raw)
            assert not re.search(rb'\b(?:\d{1,3}\.){3}\d{1,3}\b|/opt/apps/|/home/|/private/', raw)
            assert not any(name.endswith(suffix) for suffix in ('.db', '.env', '.pem', '.key'))
            assert archive.getinfo(name).date_time == (1980, 1, 1, 0, 0, 0)
            if name.endswith('.py'):
                ast.parse(raw)
    result = subprocess.run([sys.executable, '-I', '-B', str(first), '--help'], capture_output=True, check=True)
    assert b'Fixed canonical profile snapshot' in result.stdout and not result.stderr
    probe = ('import sys;sys.path.insert(0,sys.argv[1]);from control.friends import profile_snapshot as module;'
             'assert module.__file__.startswith(sys.argv[1]+"/");assert len(module.PROFILE_FIELDS)==7')
    subprocess.run([sys.executable, '-I', '-B', '-c', probe, str(first)], capture_output=True, check=True)
    for argument in ('--profile', '--config', 'reconcile_current_floor', 'apply_exact_crl'):
        result = subprocess.run([sys.executable, '-I', '-B', str(first), argument], input=b'{}', capture_output=True)
        assert result.returncode == 2 and not result.stdout
        assert result.stderr == b'Restricted snapshot route rejected\n'
    with pytest.raises(FileExistsError):
        package.build(first, 'HEAD', repository=source)


def test_snapshot_package_cannot_embed_write_permit(source, tmp_path):
    with pytest.raises(ValueError, match='cannot embed a write permit'):
        package.build_capsule(tmp_path / 'bad.pyz', 'HEAD', sources=package.SOURCES,
            entrypoint='control.friends.profile_snapshot', permit={'action': 'reconcile_current_floor'}, repository=source)
