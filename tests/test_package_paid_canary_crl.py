import ast
import hashlib
import json
import re
import subprocess
import sys
import zipfile

import pytest

from control.friends.paid_canary_crl import strict
from scripts import package_paid_canary_crl as package


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
                    'commit', '-qm', 'fixture'], cwd=repository, check=True)
    return repository


def test_deterministic_unbound_committed_package(source, tmp_path):
    (source / 'control/friends/paid_canary_crl.py').write_text('dirty_source_must_not_ship = True\n')
    first, second = tmp_path / 'first.pyz', tmp_path / 'second.pyz'
    receipt = package.build(first, 'HEAD', repository=source)
    assert package.build(second, 'HEAD', repository=source) == receipt
    assert first.read_bytes() == second.read_bytes()
    with zipfile.ZipFile(first) as archive:
        manifest_raw = archive.read('source-manifest.json')
        manifest = strict(manifest_raw, 32768)
        assert manifest['binding'] == 'unbound' and manifest['operation_permit'] is None
        assert manifest['production_configuration'] == 'absent'
        original = subprocess.check_output(['git', 'show', 'HEAD:' + package.PARSER_SOURCE], cwd=source)
        projected, provenance = package.parser_projection(original)
        assert archive.read(package.PARSER_SOURCE) == projected
        assert manifest['source_projections'] == {package.PARSER_SOURCE: provenance}
        original_functions = {node.name: ast.dump(node) for node in ast.parse(original).body if isinstance(node, ast.FunctionDef)}
        projected_functions = {node.name: ast.dump(node) for node in ast.parse(projected).body if isinstance(node, ast.FunctionDef)}
        assert projected_functions == {name: original_functions[name] for name in package.PARSER_DEFINITIONS}
        assert archive.read('operation-permit.json') == b'null'
        assert receipt['manifest_sha256'] == hashlib.sha256(manifest_raw).hexdigest()
        assert set(archive.namelist()) == set(manifest['files']) | {'source-manifest.json'}
        for name, expected in manifest['files'].items():
            raw = archive.read(name)
            assert hashlib.sha256(raw).hexdigest() == expected
            assert not re.search(rb'FC-[A-Z0-9]{4}-[A-Z0-9]{4}|-----BEGIN [A-Z ]*PRIVATE KEY|dirty_source_must_not_ship', raw)
            assert not re.search(rb'\b(?:\d{1,3}\.){3}\d{1,3}\b|/opt/apps/|/etc/family', raw)
            assert not any(name.endswith(suffix) for suffix in ('.db', '.env', '.pem', '.key'))
            assert archive.getinfo(name).date_time == (1980, 1, 1, 0, 0, 0)
            if name.endswith('.py'):
                ast.parse(raw)
        assert 'LICENSE' in manifest['files']
        assert 'THIRD_PARTY_NOTICES.md' in manifest['files']
    probe = ('import sys; sys.path.insert(0,sys.argv[1]); '
             'from control.friends import paid_canary_crl; '
             'assert paid_canary_crl.__file__.startswith(sys.argv[1]+"/"); '
             'assert paid_canary_crl.main(["--manifest"]) == 0')
    subprocess.run([sys.executable, '-I', '-c', probe, str(first)], cwd=tmp_path, capture_output=True, check=True)
    for flag in ('--help', '--manifest'):
        result = subprocess.run([sys.executable, str(first), flag], cwd=tmp_path, capture_output=True, check=True)
        assert not result.stderr and b'unbound' in result.stdout.lower()
    for action in ('generate', 'deliver', 'commit', 'lookup'):
        result = subprocess.run([sys.executable, str(first), action], cwd=tmp_path, capture_output=True)
        assert result.returncode == 2 and not result.stderr
        assert json.loads(result.stdout)['result'] == 'INVALID_PERMIT'
    with pytest.raises(FileExistsError):
        package.build(first, 'HEAD', repository=source)


def test_bound_envelope_not_supported(source, tmp_path):
    with pytest.raises(TypeError):
        package.build(tmp_path / 'bound.pyz', 'HEAD', envelope={}, repository=source)


def test_missing_committed_member_rejected(source, tmp_path):
    subprocess.run(['git', 'rm', '-q', 'LICENSE'], cwd=source, check=True)
    subprocess.run(['git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                    'commit', '-qm', 'missing fixture member'], cwd=source, check=True)
    with pytest.raises(ValueError, match='Missing committed regular source'):
        package.build(tmp_path / 'missing.pyz', 'HEAD', repository=source)
    (source / 'LICENSE').write_bytes((package.ROOT / 'LICENSE').read_bytes())
    helper = source / 'control/friends/paid_canary_crl.py'
    helper.write_text(helper.read_text() + '\nFORBIDDEN_ENDPOINT = ' + repr('.'.join(('192', '0', '2', '1'))) + '\n')
    subprocess.run(['git', 'add', '.'], cwd=source, check=True)
    subprocess.run(['git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                    'commit', '-qm', 'forbidden endpoint fixture'], cwd=source, check=True)
    with pytest.raises(ValueError, match='Operational data forbidden'):
        package.build(tmp_path / 'forbidden.pyz', 'HEAD', repository=source)
    assert not (tmp_path / 'forbidden.pyz').exists()
