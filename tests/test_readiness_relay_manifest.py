import json
from pathlib import Path
import sys

import pytest


SOURCE = Path(__file__).resolve().parents[1] / 'deploy/friends/restricted'
sys.path.insert(0, str(SOURCE))
from install_readiness_relay import digest, updated_preview_manifest


def fixture(tmp_path, monkeypatch):
    import install_readiness_relay
    (tmp_path / 'provisioning').mkdir()
    originals = {'reticulum.py': b'provider', 'runtime.py': b'runner'}
    monkeypatch.setattr(install_readiness_relay, 'EXPECTED', {key: digest(raw) for key, raw in originals.items()})
    for name, raw in originals.items():
        (tmp_path / 'provisioning' / name).write_bytes(raw)
    (tmp_path / 'unchanged.py').write_bytes(b'unchanged')
    files = {'provisioning/' + name: digest(raw) for name, raw in originals.items()}
    files['unchanged.py'] = digest(b'unchanged')
    manifest = dict(schema_version=1, preview=True, files=files,
                    bundle_id=digest(json.dumps(files, sort_keys=True).encode()))
    (tmp_path / 'manifest.json').write_text(json.dumps(manifest))
    for path in tmp_path.rglob('*'):
        if path.is_file():
            path.chmod(0o600)
    candidate = {'reticulum.py': b'new-provider', 'runtime.py': b'new-runner', 'readiness_relay.py': b'relay'}
    return manifest, candidate


def test_exact_launcher_manifest_updated_without_weakening_verifier(tmp_path, monkeypatch):
    original, candidate = fixture(tmp_path, monkeypatch)
    result = json.loads(updated_preview_manifest(tmp_path, candidate))
    assert result['files']['unchanged.py'] == original['files']['unchanged.py']
    for name, raw in candidate.items():
        assert result['files']['provisioning/' + name] == digest(raw)
    assert result['bundle_id'] == digest(json.dumps(result['files'], sort_keys=True).encode())
    for name, raw in candidate.items():
        (tmp_path / 'provisioning' / name).write_bytes(raw)
    assert json.loads(updated_preview_manifest(tmp_path, candidate)) == result


@pytest.mark.parametrize('mutation', ['unrelated', 'conflicting_candidate', 'manifest'])
def test_mixed_or_corrupt_source_rejected(tmp_path, monkeypatch, mutation):
    original, candidate = fixture(tmp_path, monkeypatch)
    target = {'unrelated': 'unchanged.py', 'conflicting_candidate': 'provisioning/runtime.py',
              'manifest': 'manifest.json'}[mutation]
    (tmp_path / target).write_text('{}' if mutation == 'manifest' else 'unexpected')
    with pytest.raises((ValueError, KeyError)):
        updated_preview_manifest(tmp_path, candidate)
