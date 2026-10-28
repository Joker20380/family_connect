import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile

import pytest

from control.friends.restricted_maintenance import strict
from scripts import package_restricted_maintenance as package


@pytest.fixture
def source(tmp_path):
    repository = tmp_path / 'source'
    repository.mkdir()
    subprocess.run(['git', 'init', '-q', str(repository)], check=True)
    for name in package.SOURCES:
        path = repository / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((package.ROOT / name).read_bytes())
    subprocess.run(['git', 'add', '.'], cwd=repository, check=True)
    subprocess.run(['git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                    'commit', '-qm', 'synthetic source fixture'], cwd=repository, check=True)
    return repository


def fixture_permit():
    return dict(schema=1, operation_id='restricted_maintenance_' + 'c' * 32, action='reconcile_current_floor',
        expected_profile_sha256='a' * 64, expected_directory_sha256='b' * 64,
        expected_embedded_crl_sha256='c' * 64, expected_embedded_crl_number=27211,
        expected_minimum_crl=27088, request_sha256='d' * 64, target_crl_sha256='c' * 64,
        target_crl_number=27211, target_minimum_crl=27211, not_before=1800000000, not_after=1800000300)


@pytest.mark.parametrize('bound', [False, True])
def test_deterministic_committed_package_and_complete_hashes(source, tmp_path, bound):
    permit = fixture_permit() if bound else None
    (source / 'control/friends/restricted_maintenance.py').write_text('dirty_work_must_not_ship = True\n')
    first, second = tmp_path / 'first.pyz', tmp_path / 'second.pyz'
    receipt = package.build(first, 'HEAD', repository=source, permit=permit)
    assert package.build(second, 'HEAD', repository=source, permit=permit) == receipt
    assert first.read_bytes() == second.read_bytes()
    with zipfile.ZipFile(first) as archive:
        manifest_raw = archive.read('source-manifest.json')
        manifest = strict(manifest_raw, 32768, 'INVALID_REQUEST')
        assert manifest['binding'] == ('single_operation' if bound else 'unbound')
        assert manifest['operation_permit'] == permit
        assert manifest['production_configuration'] == 'absent'
        assert json.loads(archive.read('operation-permit.json')) == permit
        assert receipt['manifest_sha256'] == hashlib.sha256(manifest_raw).hexdigest()
        assert set(archive.namelist()) == set(manifest['files']) | {'source-manifest.json'}
        for name, expected in manifest['files'].items():
            raw = archive.read(name)
            assert hashlib.sha256(raw).hexdigest() == expected
            assert not re.search(rb'FC-[A-Z0-9]{4}-[A-Z0-9]{4}|-----BEGIN [A-Z ]*PRIVATE KEY|dirty_work_must_not_ship', raw)
            assert not re.search(rb'\b(?:\d{1,3}\.){3}\d{1,3}\b|/opt/apps/|/home/|/private/', raw)
            assert not any(name.endswith(suffix) for suffix in ('.db', '.env', '.pem', '.key'))
            assert archive.getinfo(name).date_time == (1980, 1, 1, 0, 0, 0)
            assert archive.getinfo(name).external_attr >> 16 == (0o40755 if name.endswith('/') else 0o100644)
            if name.endswith('.py'):
                ast.parse(raw)
        assert {'LICENSE', 'THIRD_PARTY_NOTICES.md'} <= set(manifest['files'])
        original = subprocess.check_output(['git', 'show', 'HEAD:control/friends/restricted.py'], cwd=source)
        assert archive.read('control/friends/restricted.py') == original
    for flag in ('--help', '--manifest'):
        result = subprocess.run([sys.executable, '-I', '-B', str(first), flag], capture_output=True, check=True)
        assert not result.stderr and json.loads(result.stdout)['binding'] == manifest['binding']
    probe = ('import sys;sys.path.insert(0,sys.argv[1]);from control.friends import restricted_maintenance as module;'
             'assert module.__file__.startswith(sys.argv[1]+"/");assert module.MAX_TEST_LIFETIME==14400')
    subprocess.run([sys.executable, '-I', '-B', '-c', probe, str(first)], capture_output=True, check=True)
    for action in ('apply_exact_crl', 'reconcile_current_floor', 'status', '--profile', '--config', '--command'):
        result = subprocess.run([sys.executable, '-I', '-B', str(first), action], input=b'{}', capture_output=True)
        assert result.returncode == 2 and not result.stderr
        assert json.loads(result.stdout)['result'] == 'INVALID_REQUEST'
    if not bound:
        result = subprocess.run([sys.executable, '-I', '-B', str(first)], input=b'{}', capture_output=True)
        assert result.returncode == 2 and not result.stderr
        assert json.loads(result.stdout)['result'] == 'INVALID_PERMIT'
    with pytest.raises(FileExistsError):
        package.build(first, 'HEAD', repository=source, permit=permit)


def test_invalid_bound_permit_rejected_before_output(source, tmp_path):
    permit = fixture_permit()
    permit['not_after'] += 1
    with pytest.raises(ValueError):
        package.build(tmp_path / 'invalid.pyz', 'HEAD', repository=source, permit=permit)
    assert not (tmp_path / 'invalid.pyz').exists()
