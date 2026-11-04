import json
import os
from pathlib import Path
import subprocess

import pytest

from scripts import mesh_cleanup_gateway_source as source

HEAD_LOSS = (b'func headLossPair(test *testing.T, ctx context.Context, head uint64, fault string) (*headLossEndpoint, *headLossEndpoint) {\n'
             b'\ttest.Helper()\n'
             b'\tsession, err := New(sessiontrace.With(ctx, trace), Config{RoomURL: "local-test"})\n}\n')


@pytest.fixture
def accepted(tmp_path, monkeypatch):
    directory = tmp_path / 'accepted'
    (directory / 'carrier').mkdir(parents=True)
    (directory / 'carrier/engine.go').write_bytes(b'package engine\n')
    (directory / 'carrier/policy.go').write_bytes(b'package policy\n')
    (directory / 'carrier/telemost').mkdir()
    (directory / 'carrier/telemost/head_loss_test.go').write_bytes(HEAD_LOSS)
    raw = json.dumps({'files': {name: source.digest(content)
                              for name, content in source.inventory(directory).items()}}).encode()
    (directory / 'source-manifest.json').write_bytes(raw)
    monkeypatch.setattr(source, 'MANIFEST_SHA256', source.digest(raw))
    return directory


@pytest.fixture
def patch(monkeypatch):
    raw = b'--- a/engine.go\n+++ b/engine.go\n@@ -1 +1 @@\n-package engine\n+package corrected\n'
    monkeypatch.setattr(source, 'PATCH_SHA256', source.digest(raw))
    monkeypatch.setattr(source, 'CHANGED', frozenset(('engine.go',)))
    return raw


@pytest.mark.parametrize('change', ['extra', 'modified', 'missing', 'symlink', 'hardlink', 'fifo', 'manifest'])
def test_predecessor_inventory_is_exact(accepted, change):
    assert len(source.accepted(accepted)) == 3
    member = accepted / 'carrier/engine.go'
    if change == 'extra':
        (accepted / 'extra.key').write_text('synthetic')
    elif change == 'manifest':
        (accepted / 'source-manifest.json').write_text('{}')
    else:
        member.unlink()
        if change == 'modified':
            member.write_text('changed')
        elif change == 'symlink':
            member.symlink_to(accepted / 'carrier/policy.go')
        elif change == 'hardlink':
            os.link(accepted / 'carrier/policy.go', member)
        elif change == 'fifo':
            os.mkfifo(member)
    with pytest.raises(ValueError):
        source.accepted(accepted)


def test_root_alias_rejected(accepted, tmp_path):
    alias = tmp_path / 'alias'
    alias.symlink_to(accepted, target_is_directory=True)
    with pytest.raises(ValueError):
        source.accepted(alias)


@pytest.mark.parametrize('baseline,manifest', [('other', None), ('primary', None), ('secondary', Path('other.json'))])
def test_predecessor_selection_cannot_fall_back(accepted, baseline, manifest):
    with pytest.raises(ValueError):
        source.accepted(accepted, baseline, manifest)


def test_primary_uses_its_own_pinned_inventory(accepted, monkeypatch):
    calls = []

    def primary(directory, manifest):
        calls.append((directory, manifest))
        return {'policy.go': b'primary policy'}

    monkeypatch.setattr(source.predecessor, 'accepted', primary)
    manifest = accepted / 'primary.json'
    assert source.accepted(accepted, 'primary', manifest) == {'carrier/policy.go': b'primary policy'}
    assert calls == [(accepted, manifest)]


def test_projection_preserves_all_other_sources(accepted, patch, monkeypatch):
    monkeypatch.setenv('GIT_DIR', '/invalid')
    original = source.accepted(accepted)
    result = source.project(original, patch)
    assert result['carrier/engine.go'] == b'package corrected\n'
    assert result['carrier/policy.go'] == original['carrier/policy.go']
    assert source.accepted(accepted) == original


def test_patch_pin_and_changed_scope_are_required(accepted, patch, monkeypatch):
    with pytest.raises(ValueError, match='patch mismatch'):
        source.project(source.accepted(accepted), patch + b'\n')
    monkeypatch.setattr(source, 'CHANGED', frozenset(('policy.go',)))
    with pytest.raises(ValueError, match='boundary'):
        source.project(source.accepted(accepted), patch)


def test_reviewed_patch_and_imported_tests_are_narrow():
    raw = (Path(__file__).resolve().parents[1] / source.PATCH).read_bytes()
    assert source.digest(raw) == source.PATCH_SHA256
    assert {line[6:].decode() for line in raw.splitlines() if line.startswith(b'+++ b/')} == source.CHANGED
    assert all(name.endswith('_test.go') for name in source.TESTS)
    assert not any(name.startswith(('roombroker/', 'cmd/')) for name in source.CHANGED)


def test_head_loss_overlay_preserves_predecessor_framing_assertions():
    marker = b'\nconst existingFrameTimeout = 123\n'
    patched = source.head_loss_constructor(HEAD_LOSS + marker)
    assert patched.endswith(marker) and b'constructor := New' in patched
    assert b'reorderGapTimeout' not in patched
    with pytest.raises(ValueError, match='constructor mismatch'):
        source.head_loss_constructor(patched)


def test_materialization_is_committed_private_and_exclusive(accepted, patch, monkeypatch, tmp_path):
    calls = []
    revision = 'a' * 40
    monkeypatch.setattr(subprocess, 'check_output', lambda *arguments, **keywords: revision.encode())

    def committed(repository, ref, name):
        calls.append((ref, name))
        return patch if name == source.PATCH else b'package fixture\n'

    monkeypatch.setattr(source, 'committed', committed)
    output = tmp_path / 'output'
    receipt = source.materialize(accepted, output, 'HEAD')
    assert calls == [(revision, source.PATCH)] + [(source.LIFECYCLE_SOURCE, 'carrier/' + name) for name in source.TESTS]
    assert receipt['operation_permit'] is None and receipt['production_configuration'] == 'absent'
    assert (output / 'carrier/policy.go').read_bytes() == b'package policy\n'
    assert (output / 'carrier/telemost/head_loss_test.go').read_bytes() == source.head_loss_constructor(HEAD_LOSS)
    assert output.stat().st_mode & 0o777 == 0o700
    assert all(path.stat().st_mode & 0o777 == 0o600 for path in output.rglob('*') if path.is_file())
    with pytest.raises(FileExistsError):
        source.materialize(accepted, output, 'HEAD')


def test_invalid_inventory_creates_no_output(accepted, patch, monkeypatch, tmp_path):
    monkeypatch.setattr(subprocess, 'check_output', lambda *arguments, **keywords: b'a' * 40)
    (accepted / 'carrier/extra').write_text('synthetic')
    output = tmp_path / 'output'
    with pytest.raises(ValueError, match='inventory'):
        source.materialize(accepted, output, 'HEAD')
    assert not output.exists()
