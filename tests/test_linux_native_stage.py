import hashlib
import json
from pathlib import Path
import subprocess

import pytest

from scripts import stage_linux_native as staging
from scripts import package_mesh_component as packager


def git(root, *arguments):
    return subprocess.check_output(['git', '-C', str(root), *arguments]).decode().strip()


@pytest.fixture
def accepted(tmp_path, monkeypatch):
    repository = tmp_path / 'repository'
    repository.mkdir()
    git(repository, 'init', '-q')
    git(repository, 'config', 'user.name', 'Synthetic CI')
    git(repository, 'config', 'user.email', 'ci@example.invalid')
    files = {
        'carrier/native.go': 'package carrier\n',
        'scripts/build_desktop_mesh.py':
            'from pathlib import Path\nimport hashlib\n'
            'def sources(source):\n'
            '    path = Path(__file__).resolve().parents[1] / "carrier/native.go"\n'
            '    return {"carrier/native.go": hashlib.sha256(path.read_bytes()).hexdigest()}\n',
        'scripts/verify_desktop_reference.py': 'def verify(root):\n    return {"result": "PASS"}\n',
    }
    for name, contents in files.items():
        path = repository / name
        path.parent.mkdir(exist_ok=True)
        path.write_text(contents)
    closure = {name: hashlib.sha256(contents.encode()).hexdigest() for name, contents in files.items()}
    native = {'carrier/native.go': closure['carrier/native.go']}
    git(repository, 'add', '.')
    git(repository, 'commit', '-qm', 'Synthetic accepted native closure')
    policy = dict(commit=git(repository, 'rev-parse', 'HEAD'), paths=['carrier', 'scripts'],
                  closure_sha256=staging.inventory_digest(closure),
                  native_source_digest=staging.inventory_digest(native))
    monkeypatch.setattr(staging, 'reference', lambda: policy)
    (repository / 'carrier/late.go').write_text('package late\n')
    git(repository, 'add', '.')
    git(repository, 'commit', '-qm', 'Later native input must not leak into staging')
    destination = tmp_path / 'staged'
    receipt = staging.stage(destination, repository)
    return destination, repository, native, receipt


def test_complete_pinned_closure_excludes_later_inputs(accepted):
    destination, repository, native, receipt = accepted
    assert not (destination / 'carrier/late.go').exists()
    assert receipt['native_source_commit'] != git(repository, 'rev-parse', 'HEAD')
    assert staging.verify(destination) == native
    assert packager.accepted_native_sources(destination) == native
    assert not list(destination.rglob('__pycache__'))
    with pytest.raises(ValueError, match='fresh'):
        staging.stage(destination, repository)


@pytest.mark.parametrize('mutation', ['changed', 'extra', 'missing', 'builder', 'symlink'])
def test_packager_rejects_native_closure_drift(accepted, tmp_path, mutation):
    destination, _, native, _ = accepted
    if mutation == 'changed':
        (destination / 'carrier/native.go').write_text('package changed\n')
    elif mutation == 'extra':
        (destination / 'carrier/new.go').write_text('package extra\n')
    elif mutation == 'missing':
        (destination / 'carrier/native.go').unlink()
    elif mutation == 'builder':
        (destination / 'scripts/build_desktop_mesh.py').write_text('raise AssertionError("must not execute")\n')
    else:
        (destination / 'carrier/link.go').symlink_to('native.go')
    build = tmp_path / 'build'
    build.mkdir()
    (build / 'build.json').write_text(json.dumps(dict(build_tags=[], source_digest=staging.inventory_digest(native))))
    (build / 'source-inventory.json').write_text(json.dumps(native))
    with pytest.raises(ValueError, match='Native closure'):
        packager.assemble(build, tmp_path / 'rns', tmp_path / 'out', tmp_path / 'awg', tmp_path / 'tcp',
                          native_source=destination)


def test_system_reference_keeps_historical_native_digest():
    assert staging.reference()['native_source_digest'] == 'f0e48d7cd3bd68a02759a5ff29967492ab170e171942d502864f0e03a07c23fe'


def test_ci_uses_one_native_stage_and_current_package_sources():
    source = (Path(__file__).resolve().parents[1] / 'scripts/ci_linux_candidate.sh').read_text()
    assert 'cd "$work/native-source"\n  python -m scripts.build_desktop_mesh' in source
    assert '--native-source /native-source' in source
    assert 'src=$work/current,dst=/workspace,readonly' in source
    assert 'src=$work/native-source,dst=/native-source,readonly' in source
    assert '--os linux --test' in source
    assert 'scripts.verify_linux_candidate' in source
