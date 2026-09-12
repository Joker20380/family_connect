import json
import shutil
import subprocess
import sys
import tarfile

import pytest

from scripts.package_control import ROOT, FILES, DESKTOP, package


def test_extracted_preview(tmp_path):
    artifact = package(ROOT, tmp_path / 'out')
    unpacked = tmp_path / 'unpacked'
    with tarfile.open(artifact) as archive:
        assert all(item.isfile() for item in archive.getmembers())
        assert {item.name for item in archive.getmembers()} == {
            'FamilyConnect-Control-preview/' + name for name in (*FILES, 'manifest.json')}
        archive.extractall(unpacked, filter='data')
    root = unpacked / 'FamilyConnect-Control-preview'
    launcher = root / 'scripts/run_control_preview.py'
    def run(*args):
        return subprocess.run([sys.executable, str(launcher), *args], cwd=tmp_path,
            capture_output=True, text=True, timeout=20)
    verified = run('verify')
    assert verified.returncode == 0
    assert verified.stdout.strip() == json.loads((root / 'manifest.json').read_text())['bundle_id']
    assert run('control', '--help').returncode == 0
    # Initialize real private identity/journal using the shipped public anchor,
    # outside the source checkout, without starting RNS or changing host VPN.
    initialized = run('control', 'init-client', '--identity', str(tmp_path / 'identity'),
        '--state', str(tmp_path / 'journal'), '--anchor', str(root / 'clients/desktop/update.pub'))
    assert initialized.returncode == 0, initialized.stderr
    assert (tmp_path / 'journal/cache.json').is_file()
    # Reuse the real two-process RNS fixture against extracted modules only.
    (root / 'tests').mkdir()
    for name in ('test_control_channel.py', 'reticulum_control_peer.py'):
        shutil.copyfile(ROOT / 'tests' / name, root / 'tests' / name)
    (root / 'clients/desktop/tests').mkdir()
    for name in ('conftest.py', 'test_operations.py'):
        shutil.copyfile(ROOT / 'clients/desktop/tests' / name, root / 'clients/desktop/tests' / name)
    lifecycle = subprocess.run([sys.executable, '-m', 'pytest', '-q',
        'tests/test_control_channel.py', 'clients/desktop/tests/test_operations.py'],
        cwd=root, capture_output=True, text=True, timeout=90)
    assert lifecycle.returncode == 0, lifecycle.stdout + lifecycle.stderr
    (root / 'clients/desktop/backend.py').write_text('raise RuntimeError("must not execute")')
    assert run('control', '--help').returncode != 0


def test_package_allowlist_and_no_overwrite(tmp_path):
    package(ROOT, tmp_path)
    with pytest.raises(FileExistsError):
        package(ROOT, tmp_path)
    assert len(DESKTOP) == 6
    assert not any('sign_control' in name or name.endswith('.key') for name in FILES)


def test_preview_dependency_pins_reuse_existing_locks():
    accepted = set((ROOT / 'control/requirements.lock').read_text().splitlines()) | set(
        (ROOT / 'device_identity/requirements.lock').read_text().splitlines())
    pins = (ROOT / 'provisioning/requirements.lock').read_text().splitlines()
    assert all(line in accepted for line in pins if line and not line.startswith('#'))
