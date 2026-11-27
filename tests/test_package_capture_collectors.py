import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

import pytest

from control.capture_gate import initialize
from scripts import package_capture_collectors as package


@pytest.fixture(params=['inventory', 'probe'])
def baseline(tmp_path, request):
    role = request.param
    root = tmp_path / role
    for name in set(package.ROLES[role]) | set(package.COMMON) | set(package.DEPENDENCIES[role]):
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(package.ROOT / name, target)
    return root, role


def pins_for(root, role):
    return {name: package.digest(raw) for name, raw in package.snapshot(root, role).items()}


def test_previous_reviewed_helper_is_preserved_for_exact_rollback(baseline, tmp_path):
    root, role = baseline
    name = 'control_plane/fc_control_plane/capture.py'
    previous = (package.ROOT / 'tests/fixtures/owner_upgrade/capture_before_orm.py').read_bytes()
    assert package.digest(previous) in package.ADMISSION_HISTORY[name]
    (root / name).write_bytes(previous)
    output = tmp_path / 'updated.zip'
    receipt = package.build(root, role, pins_for(root, role), output)
    assert receipt['restore_on_rollback'][name] == package.digest(previous)
    with zipfile.ZipFile(output) as archive:
        assert archive.read('rollback/' + name) == previous
        assert package.digest(archive.read(name)) == package.ADMISSION[name]


def test_legacy_manual_metadata_keeps_original_dispatch_contract(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(package.ROOT / 'control_plane'))
    monkeypatch.delenv('FC_CONTROL_CAPTURE_GATE', raising=False)
    monkeypatch.delenv('FC_PSEUDONYM_ALIASES', raising=False)
    root = tmp_path / 'baseline'
    for name in set(package.ROLES['inventory']) | set(package.COMMON) | set(package.DEPENDENCIES['inventory']):
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(package.ROOT / name, target)
    name = 'control_plane/collect_technical_metadata.py'
    previous = (package.ROOT / 'tests/fixtures/owner_upgrade/technical_metadata_legacy.py').read_bytes()
    assert package.digest(previous) == package.ENTRIES[name][2]
    (root / name).write_bytes(previous)
    receipt = package.build(root, 'inventory', pins_for(root, 'inventory'), tmp_path / 'legacy.zip')
    with zipfile.ZipFile(tmp_path / 'legacy.zip') as archive:
        candidate = archive.read(name)
        assert archive.read('rollback/' + name) == previous
    assert receipt['after'][name] == package.digest(candidate) == package.ENTRIES[name][3]
    runtime = tmp_path / 'runtime'
    local = runtime / '.local'
    local.mkdir(parents=True)
    values = [('technical-metadata-source.json', json.dumps(dict(python='/isolated/python',
        archive='/isolated/source.pyz', archive_sha256='a' * 64)).encode()), ('inventory-hmac.key', b'x' * 32)]
    for filename, raw in values:
        target = local / filename
        target.write_bytes(raw)
        target.chmod(0o600)
    script = runtime / 'apps/console/technical_metadata_collector.py'
    script.parent.mkdir(parents=True)
    script.write_text('')
    results = []
    for raw in (previous, candidate):
        calls = []
        def run(command, **options):
            calls.append((command, options))
            return subprocess.CompletedProcess(command, 0, stdout=b'{"source":"gateway-ru","devices":[]}')
        namespace = dict(__name__='isolated_legacy', __file__=str(package.ROOT / name))
        exec(compile(raw, name, 'exec'), namespace)
        results.append((namespace['collect'](base=runtime, run=run), calls))
    assert len(results[0][1]) == 1 and results[0] == results[1]


def test_candidate_is_reproducible_closed_and_preserves_baseline(baseline, tmp_path):
    root, role = baseline
    private = root / 'control_plane/.local/private.key'
    private.parent.mkdir()
    private.write_text('synthetic excluded state')
    before = pins_for(root, role)
    output = tmp_path / 'candidate.zip'
    receipt = package.build(root, role, before, output)
    repeat = package.build(root, role, before, tmp_path / 'repeat.zip')
    assert receipt == repeat
    assert not receipt['installed'] and not receipt['capture_permitted'] and not receipt['runtime_qualified']
    assert set(receipt['changed']) == set(package.ADMISSION)
    assert receipt['restore_on_rollback'] == {} and set(receipt['remove_on_rollback']) == set(package.ADMISSION)
    assert output.stat().st_mode & 0o777 == 0o600
    assert pins_for(root, role) == before and private.read_text() == 'synthetic excluded state'
    with zipfile.ZipFile(output) as archive:
        assert set(archive.namelist()) == set(receipt['after']) | {'manifest.json'}
        assert all(name.endswith('.py') or name == 'manifest.json' for name in archive.namelist())
        assert json.loads(archive.read('manifest.json')) == {key: value for key, value in receipt.items() if key != 'sha256'}
        for name, digest in before.items():
            if digest is not None:
                assert package.digest(archive.read(name)) == digest
    with pytest.raises(FileExistsError):
        package.build(root, role, before, output)
    assert package.digest(output.read_bytes()) == receipt['sha256']


def test_reviewed_replacement_has_exact_rollback_bytes(baseline, tmp_path, monkeypatch):
    root, role = baseline
    name = package.ROLES[role][0]
    previous = b'previous_source = True\n'
    (root / name).write_bytes(previous)
    monkeypatch.setitem(package.ENTRIES, name, (package.digest(previous), package.ENTRIES[name][1]))
    receipt = package.build(root, role, pins_for(root, role), tmp_path / 'candidate.zip')
    assert receipt['restore_on_rollback'] == {name: package.digest(previous)}
    assert set(receipt['remove_on_rollback']) == set(package.ADMISSION)
    with zipfile.ZipFile(tmp_path / 'candidate.zip') as archive:
        assert archive.read('rollback/' + name) == previous
        assert package.digest(archive.read(name)) == package.ENTRIES[name][1]
    assert (root / name).read_bytes() == previous


@pytest.mark.parametrize('fault', ['missing-pin', 'extra-pin', 'wrong-pin', 'entry-change', 'namespace', 'admission-change'])
def test_unknown_bindings_refuse_without_artifact(baseline, tmp_path, fault):
    root, role = baseline
    before = pins_for(root, role)
    name = package.ROLES[role][0]
    if fault == 'missing-pin':
        before.pop(name)
    elif fault == 'extra-pin':
        before['../private.key'] = '1' * 64
    elif fault == 'wrong-pin':
        before[name] = '1' * 64
    else:
        target = root / (name if fault == 'entry-change' else
                         'control_plane/__init__.py' if fault == 'namespace' else 'control/capture_gate.py')
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('raise RuntimeError("never execute baseline")\n')
        before = pins_for(root, role)
    output = tmp_path / 'refused.zip'
    with pytest.raises(ValueError):
        package.build(root, role, before, output)
    assert not output.exists()


@pytest.mark.parametrize('fault', ['symlink', 'hardlink', 'fifo', 'oversize', 'writable'])
def test_unsafe_source_refuses_bounded_read(baseline, tmp_path, fault):
    root, role = baseline
    target = root / package.ROLES[role][0]
    original = target.read_bytes()
    target.unlink()
    if fault in ('symlink', 'hardlink'):
        other = tmp_path / 'other.py'
        other.write_bytes(original)
        if fault == 'symlink':
            target.symlink_to(other)
        else:
            os.link(other, target)
    elif fault == 'fifo':
        os.mkfifo(target)
    elif fault == 'oversize':
        target.write_bytes(b'x' * (package.LIMIT + 1))
    else:
        target.write_bytes(original)
        target.chmod(0o666)
    with pytest.raises((OSError, ValueError)):
        package.snapshot(root, role)


def test_changed_dependency_during_build_is_refused(baseline, tmp_path, monkeypatch):
    root, role = baseline
    before = pins_for(root, role)
    original = package.read_source
    changed = False
    def read(path, optional=False):
        nonlocal changed
        raw = original(path, optional)
        if path == package.ROOT / 'control/capture_gate.py' and not changed:
            changed = True
            (root / package.COMMON[0]).write_text('changed = True\n')
        return raw
    monkeypatch.setattr(package, 'read_source', read)
    output = tmp_path / 'refused.zip'
    with pytest.raises(ValueError, match='BASELINE_CHANGED'):
        package.build(root, role, before, output)
    assert not output.exists()


def test_candidate_source_pin_and_output_scope_are_mandatory(baseline, tmp_path):
    root, role = baseline
    before = pins_for(root, role)
    source = tmp_path / 'changed-source'
    target = source / 'control/capture_gate.py'
    target.parent.mkdir(parents=True)
    target.write_text('raise RuntimeError("not executed")\n')
    with pytest.raises(ValueError, match='CANDIDATE_PIN'):
        package.build(root, role, before, tmp_path / 'refused.zip', source)
    with pytest.raises(ValueError, match='OUTPUT_SCOPE'):
        package.build(root, role, before, root / 'forbidden.zip')
    assert not (tmp_path / 'refused.zip').exists() and not (root / 'forbidden.zip').exists()


def test_unpacked_actual_scripts_refuse_before_dispatch(baseline, tmp_path):
    root, role = baseline
    output = tmp_path / 'candidate.zip'
    package.build(root, role, pins_for(root, role), output)
    unpacked = tmp_path / 'unpacked'
    with zipfile.ZipFile(output) as archive:
        archive.extractall(unpacked)
    gate = initialize(tmp_path / 'gate')
    environment = {key: value for key, value in os.environ.items() if not key.startswith('PYTHON')}
    environment['FC_CONTROL_CAPTURE_GATE'] = str(gate.directory)
    with gate.drain(.1):
        for name in package.ROLES[role]:
            command = [sys.executable, '-B', str(unpacked / name)]
            if name.endswith('/collect_inventory.py'):
                command += ['gateway-ru']
            result = subprocess.run(command, cwd=tmp_path, env=environment, capture_output=True, timeout=5)
            assert result.returncode == 75 and result.stderr.strip() == b'CAPTURE_BUSY'
    assert not (unpacked / 'control_plane/.local').exists()
    assert not list((gate.directory / 'pending').iterdir())


def test_cli_rejects_duplicate_pins_without_private_details(tmp_path):
    pin_file = tmp_path / 'pins.json'
    pin_file.write_text('{"private":null,"private":null}')
    result = subprocess.run([sys.executable, str(package.ROOT / 'scripts/package_capture_collectors.py'),
        '--baseline', str(tmp_path / 'baseline'), '--role', 'probe', '--pins', str(pin_file),
        '--output', str(tmp_path / 'refused.zip')], capture_output=True, timeout=5)
    assert result.returncode == 1 and result.stderr.strip() == b'COLLECTOR_CANDIDATE_REFUSED'
    assert not result.stdout and not (tmp_path / 'refused.zip').exists()
