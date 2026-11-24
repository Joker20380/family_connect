import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('mesh_lifetime_build', ROOT / 'tests/fixtures/mesh_lifetime/build.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def test_overlay_intercepts_common_current_boundary_not_only_cached_entry():
    source = (ROOT / 'carrier/wholedevice/session.go').read_text()
    overlay = builder.session_overlay(source)
    common = overlay.split('func openDirectoryWithTransport(', 1)[1].split('\n}', 1)[0]
    assert 'return l021Open(ctx, raw)' in common
    for entry in ('func openDirectory(', 'func openProvisioned('):
        body = overlay.split(entry, 1)[1].split('\n}', 1)[0]
        assert 'return openDirectoryWithTransport(' in body
    assert 'func unusedProductionDirectoryWithTransport(' in overlay
    assert overlay.count('return l021Open(ctx, raw)') == 1
    for caller in ('carrier/restrictedchat/owner.go', 'carrier/desktopmesh/session.go'):
        assert 'wholedevice.OpenProvisioned(' in (ROOT / caller).read_text()


@pytest.mark.parametrize('source', ['', 'func openDirectoryWithTransport(',
                                   (ROOT / 'carrier/wholedevice/session.go').read_text() * 2])
def test_overlay_fails_closed_if_boundary_moves_or_duplicates(source):
    with pytest.raises(ValueError, match='single common'):
        builder.session_overlay(source)
