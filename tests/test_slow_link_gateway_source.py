import hashlib
import json
import os
from pathlib import Path
import subprocess

import pytest

from scripts import slow_link_gateway_source as source


@pytest.fixture
def accepted(tmp_path, monkeypatch):
    directory = tmp_path / 'accepted'
    directory.mkdir()
    (directory / 'engine.go').write_bytes(b'package engine\n')
    (directory / 'policy.go').write_bytes(b'package policy\n')
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps({'files': {name: source.digest(raw)
                                             for name, raw in source.inventory(directory).items()}}))
    monkeypatch.setattr(source, 'MANIFEST_SHA256', source.digest(manifest.read_bytes()))
    return directory, manifest


def test_exact_inventory_is_required(accepted):
    directory, manifest = accepted
    assert source.accepted(directory, manifest)['policy.go'] == b'package policy\n'
    (directory / 'extra.key').write_text('synthetic')
    with pytest.raises(ValueError, match='source mismatch'):
        source.accepted(directory, manifest)


@pytest.mark.parametrize('change', ['modified', 'missing', 'symlink', 'hardlink', 'fifo'])
def test_changed_or_special_source_is_rejected(accepted, change):
    directory, manifest = accepted
    member = directory / 'engine.go'
    member.unlink()
    if change == 'modified':
        member.write_text('changed')
    elif change == 'symlink':
        member.symlink_to(directory / 'policy.go')
    elif change == 'hardlink':
        os.link(directory / 'policy.go', member)
    elif change == 'fifo':
        os.mkfifo(member)
    with pytest.raises(ValueError):
        source.accepted(directory, manifest)


def test_manifest_cannot_be_replaced_to_accept_changes(accepted):
    directory, manifest = accepted
    manifest.write_text('{}')
    with pytest.raises(ValueError, match='manifest mismatch'):
        source.accepted(directory, manifest)


def test_symlink_directory_rejected(accepted, tmp_path):
    directory, manifest = accepted
    alias = tmp_path / 'alias'
    alias.symlink_to(directory, target_is_directory=True)
    with pytest.raises(ValueError, match='real directory'):
        source.accepted(alias, manifest)


@pytest.mark.parametrize('name', ['../escape', '/absolute'])
def test_manifest_path_escape_rejected(accepted, monkeypatch, name):
    directory, manifest = accepted
    manifest.write_text(json.dumps({'files': {name: '0' * 64}}))
    monkeypatch.setattr(source, 'MANIFEST_SHA256', source.digest(manifest.read_bytes()))
    with pytest.raises(ValueError, match='inventory'):
        source.accepted(directory, manifest)


@pytest.fixture
def patch(monkeypatch):
    raw = b'--- a/engine.go\n+++ b/engine.go\n@@ -1 +1 @@\n-package engine\n+package corrected\n'
    monkeypatch.setattr(source, 'PATCH_SHA256', source.digest(raw))
    monkeypatch.setattr(source, 'CHANGED', frozenset(('engine.go',)))
    return raw


def test_projection_preserves_every_other_member(accepted, patch, monkeypatch):
    monkeypatch.setenv('GIT_DIR', '/does-not-exist')
    monkeypatch.setenv('GIT_WORK_TREE', '/does-not-exist')
    original = source.accepted(*accepted)
    projected = source.project(original, patch)
    assert projected == {'engine.go': b'package corrected\n', 'policy.go': b'package policy\n'}
    assert source.accepted(*accepted) == original


def test_modified_patch_rejected(accepted, patch):
    with pytest.raises(ValueError, match='patch mismatch'):
        source.project(source.accepted(*accepted), patch + b'\n')


def test_extra_change_rejected(accepted, patch, monkeypatch):
    patch += b'--- a/policy.go\n+++ b/policy.go\n@@ -1 +1 @@\n-package policy\n+package wrong\n'
    monkeypatch.setattr(source, 'PATCH_SHA256', source.digest(patch))
    with pytest.raises(ValueError, match='boundary'):
        source.project(source.accepted(*accepted), patch)


def test_mismatched_patch_context_rejected(accepted, patch):
    with pytest.raises(subprocess.CalledProcessError):
        source.project({'engine.go': b'package wrong\n'}, patch)


def test_committed_patch_and_test_scope():
    raw = (Path(__file__).resolve().parents[1] / source.PATCH).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == source.PATCH_SHA256
    assert {line[6:].decode() for line in raw.splitlines() if line.startswith(b'+++ b/')} == source.CHANGED
    assert all(name.endswith('_test.go') for name in source.TESTS)
    assert not any(name.startswith(('roombroker/', 'cmd/')) for name in source.CHANGED)


def test_materialization_uses_only_committed_inputs(accepted, patch, monkeypatch, tmp_path):
    calls = []
    revision = 'a' * 40
    monkeypatch.setattr(subprocess, 'check_output', lambda *arguments, **keywords: revision.encode())

    def committed(repository, ref, name):
        calls.append((ref, name))
        return patch if name == source.PATCH else b'fixture\n'

    monkeypatch.setattr(source, 'committed', committed)
    output = tmp_path / 'output'
    receipt = source.materialize(*accepted, output, 'HEAD')
    assert calls[0] == (revision, source.PATCH)
    assert all(ref == source.TRANSPORT_SOURCE for ref, _ in calls[1:])
    assert receipt['operation_permit'] is None and receipt['production_configuration'] == 'absent'
    assert (output / 'carrier/policy.go').read_bytes() == b'package policy\n'
    assert (output / 'source-manifest.json').stat().st_mode & 0o777 == 0o600
    assert output.stat().st_mode & 0o777 == 0o700
    with pytest.raises(FileExistsError):
        source.materialize(*accepted, output, 'HEAD')


def test_invalid_source_leaves_no_output(accepted, monkeypatch, tmp_path):
    monkeypatch.setattr(subprocess, 'check_output', lambda *arguments, **keywords: b'a' * 40)
    directory, manifest = accepted
    (directory / 'unexpected').write_text('synthetic')
    output = tmp_path / 'output'
    with pytest.raises(ValueError, match='source mismatch'):
        source.materialize(directory, manifest, output, 'HEAD')
    assert not output.exists()
