import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import zipfile

import pytest

from scripts import package_support_capture as package


@pytest.fixture
def synthetic(tmp_path):
    source, baseline = tmp_path / 'source', tmp_path / 'baseline'
    binding = package.contract(package.ROOT)
    before = {}
    after = {}
    for name in binding['baseline']:
        path = baseline / name
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = b'VALUE = "old"\n'
        path.write_bytes(raw)
        before[name] = package.digest(raw)
    for name in package.MODIFIED | package.ADDED:
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = b'VALUE = "new"\n'
        path.write_bytes(raw)
        after[name] = package.digest(raw)
    path = source / package.CONTRACT
    path.parent.mkdir(parents=True)
    path.write_bytes(package.encode(dict(schema=1, baseline=before, candidate=after)))
    return source, baseline, tmp_path / 'output'


def test_exact_closure_determinism_private_output_and_preserved_bytes(synthetic):
    source, baseline, output = synthetic
    (baseline / 'private.key').write_text('must never enter the archive')
    receipt = package.build(baseline, output, source)
    assert receipt == package.build(baseline, output.with_name('repeat'), source)
    assert receipt['modified'] == sorted(package.MODIFIED) and receipt['added'] == sorted(package.ADDED)
    assert receipt['removed'] == [] and receipt['preserved'] == 16
    assert stat.S_IMODE(output.stat().st_mode) == 0o700
    for name in ('baseline.pyz', 'candidate.pyz', 'receipt.json'):
        assert (output / name).read_bytes() == (output.with_name('repeat') / name).read_bytes()
        assert stat.S_IMODE((output / name).stat().st_mode) == 0o600
    with zipfile.ZipFile(output / 'baseline.pyz') as old, zipfile.ZipFile(output / 'candidate.pyz') as new:
        assert len(set(new.namelist())) == len(new.namelist())
        assert 'private.key' not in new.namelist()
        assert new.read('__main__.py') == package.ENTRYPOINT
        old_files = json.loads(old.read('source-manifest.json'))
        new_files = json.loads(new.read('source-manifest.json'))
        assert len(old_files) == 19 and len(new_files) == 23
        for name in old_files:
            if name not in package.MODIFIED:
                assert new.read(name) == old.read(name)
        assert new_files == receipt['files']


@pytest.mark.parametrize('scope', ['baseline', 'candidate'])
@pytest.mark.parametrize('change', ['bytes', 'missing', 'symlink', 'hardlink', 'fifo', 'oversized'])
def test_changed_or_unsafe_source_refuses_without_output(synthetic, scope, change):
    source, baseline, output = synthetic
    target = (baseline if scope == 'baseline' else source) / 'provisioning/support_worker.py'
    if change == 'bytes':
        target.write_bytes(b'CHANGED = True\n')
    elif change == 'oversized':
        target.write_bytes(b'x' * (package.LIMIT + 1))
    else:
        target.unlink()
        if change == 'symlink':
            target.symlink_to(source / package.CONTRACT)
        elif change == 'hardlink':
            os.link(source / package.CONTRACT, target)
        elif change == 'fifo':
            os.mkfifo(target)
    with pytest.raises((ValueError, OSError)):
        package.build(baseline, output, source)
    assert not output.exists()


def test_extra_installed_python_is_not_silently_excluded(synthetic):
    source, baseline, output = synthetic
    (baseline / 'extra.py').write_text('pass\n')
    with pytest.raises(ValueError, match='BASELINE_CLOSURE'):
        package.build(baseline, output, source)
    assert not output.exists()


@pytest.mark.parametrize('field,value', [
    ('schema', True), ('baseline', []), ('candidate', {}),
    ('candidate', {'../outside.py': 'a' * 64}),
    ('candidate', {'/outside.py': 'a' * 64}),
    ('candidate', {'outside.py': 'not-a-digest'}),
])
def test_invalid_contract_refuses(synthetic, field, value):
    source, baseline, output = synthetic
    location = source / package.CONTRACT
    binding = json.loads(location.read_bytes())
    binding[field] = value
    location.write_bytes(package.encode(binding))
    with pytest.raises(ValueError):
        package.build(baseline, output, source)
    assert not output.exists()


def test_syntax_failure_does_not_publish_output(synthetic):
    source, baseline, output = synthetic
    target = source / 'provisioning/support_capture.py'
    target.write_bytes(b'not valid python !\n')
    location = source / package.CONTRACT
    binding = json.loads(location.read_bytes())
    binding['candidate']['provisioning/support_capture.py'] = package.digest(target.read_bytes())
    location.write_bytes(package.encode(binding))
    with pytest.raises(SyntaxError):
        package.build(baseline, output, source)
    assert not output.exists()


@pytest.mark.parametrize('kind', ['existing', 'symlink'])
def test_output_is_never_overwritten(synthetic, kind):
    source, baseline, output = synthetic
    retained = output.with_name('retained')
    retained.mkdir()
    (retained / 'evidence').write_text('keep')
    if kind == 'existing':
        output.mkdir()
        (output / 'evidence').write_text('keep')
    else:
        output.symlink_to(retained, target_is_directory=True)
    with pytest.raises((ValueError, OSError)):
        package.build(baseline, output, source)
    assert (retained / 'evidence').read_text() == 'keep'
    assert (output / 'evidence').read_text() == 'keep'


def test_failed_sync_retains_partial_output_and_rejects_retry(synthetic, monkeypatch):
    source, baseline, output = synthetic

    def fail(descriptor):
        raise OSError('synthetic sync failure')

    with monkeypatch.context() as patch:
        patch.setattr(package.os, 'fsync', fail)
        with pytest.raises(OSError, match='sync failure'):
            package.build(baseline, output, source)
    assert output.is_dir() and (output / 'baseline.pyz').exists()
    with pytest.raises(FileExistsError):
        package.build(baseline, output, source)


def test_native_installed_shape_archive_imports_without_checkout(tmp_path):
    selected = os.environ.get('FC_TEST_SUPPORT_BASELINE')
    if selected is None:
        pytest.skip('requires retained installed source-only support baseline')
    output = tmp_path / 'candidate'
    receipt = package.build(Path(selected), output)
    for name in ('baseline.pyz', 'candidate.pyz'):
        result = subprocess.run([sys.executable, '-I', str(output / name), '--help'],
                                cwd=tmp_path, capture_output=True, text=True, timeout=10)
        assert result.returncode == 0, result.stderr
        assert ('--capture-gate' in result.stdout) == (name == 'candidate.pyz')
    code = '''
import json, sys, zipfile
sys.path.insert(0, sys.argv[1])
from provisioning import support_worker
with zipfile.ZipFile(sys.argv[1]) as package:
    names = json.loads(package.read('source-manifest.json'))
modules = {(name[:-12] if name.endswith('/__init__.py') else name[:-3]).replace('/', '.') for name in names}
required = {'provisioning.support_worker', 'provisioning.support_capture', 'provisioning.support_lifecycle', 'provisioning.support_runtime',
            'provisioning.subscription_notifications', 'messenger.routed', 'control.capture_gate'}
assert required <= sys.modules.keys()
for name, module in tuple(sys.modules.items()):
    if name in modules:
        assert module.__file__.startswith(sys.argv[1] + '/'), name
'''
    subprocess.run([sys.executable, '-I', '-c', code, str(output / 'candidate.pyz')],
                   cwd=tmp_path, capture_output=True, check=True, timeout=10)
    assert len(receipt['files']) == 23
