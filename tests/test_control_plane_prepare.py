import importlib.util
import json
import os
from pathlib import Path
import stat

import pytest


@pytest.mark.parametrize('mask', [0o022, 0o077])
def test_source_context_readable_without_exposing_private_configuration(tmp_path, monkeypatch, mask):
    path = Path(__file__).resolve().parents[1] / 'control_plane/prepare_local.py'
    spec = importlib.util.spec_from_file_location('prepare_local', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    base = tmp_path / 'control_plane'
    base.mkdir()
    source = base / 'apps' / 'demo.py'
    source.parent.mkdir()
    source.write_text('value = 1\n')
    source.chmod(0o600)
    (base / 'Dockerfile').write_text('FROM scratch\n')
    monkeypatch.setattr(module, 'BASE', base)
    monkeypatch.setattr(module, 'REPOSITORY', tmp_path)
    monkeypatch.setattr(module, 'source_paths', lambda: [source])
    previous = os.umask(mask)
    try:
        module.prepare()
        original_env = (base / '.env').read_bytes()
        module.prepare()
    finally:
        os.umask(previous)
    assert (base / '.env').read_bytes() == original_env
    assert stat.S_IMODE((base / '.env').stat().st_mode) == 0o600
    assert stat.S_IMODE((base / '.local').stat().st_mode) == 0o700
    assert stat.S_IMODE(source.stat().st_mode) == 0o600
    context = base / '.local/build-context'
    for staged in [context, *context.rglob('*')]:
        assert stat.S_IMODE(staged.stat().st_mode) == (0o755 if staged.is_dir() else 0o644)
    manifest = json.loads((context / 'source-manifest.json').read_text())
    assert set(manifest) == {'Dockerfile', 'control_plane/apps/demo.py'}
    assert not (context / '.env').exists()
