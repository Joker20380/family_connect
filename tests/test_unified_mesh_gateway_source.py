import json
import os
from pathlib import Path
import subprocess

import pytest

from scripts import unified_mesh_gateway_source as source


@pytest.fixture
def capsules(tmp_path, monkeypatch):
    roots = {}
    for role in source.MANIFESTS:
        root = tmp_path / role
        (root / 'carrier').mkdir(parents=True)
        (root / 'carrier/engine.go').write_bytes(b'package ' + role.encode() + b'\n')
        (root / 'carrier/policy.go').write_bytes(b'package canonical\n')
        raw = json.dumps({'files': {name: source.digest(content)
                                   for name, content in source.inventory(root).items()}}).encode()
        (root / 'source-manifest.json').write_bytes(raw)
        monkeypatch.setitem(source.MANIFESTS, role, source.digest(raw))
        roots[role] = root
    monkeypatch.setattr(source, 'PROMOTED', frozenset(('carrier/engine.go',)))
    return roots


@pytest.fixture
def patch(monkeypatch):
    raw = b'--- a/engine.go\n+++ b/engine.go\n@@ -1 +1 @@\n-package secondary\n+package corrected\n'
    monkeypatch.setattr(source, 'PATCH_SHA256', source.digest(raw))
    monkeypatch.setattr(source, 'CHANGED', frozenset(('carrier/engine.go',)))
    return raw


@pytest.mark.parametrize('role', ['primary', 'secondary'])
@pytest.mark.parametrize('change', ['extra', 'modified', 'missing', 'manifest', 'symlink', 'hardlink', 'fifo'])
def test_each_predecessor_is_pinned(capsules, role, change):
    root = capsules[role]
    assert len(source.accepted(root, role)) == 2
    member = root / 'carrier/engine.go'
    if change == 'extra':
        (root / 'unexpected.key').write_text('synthetic')
    elif change == 'manifest':
        (root / 'source-manifest.json').write_text('{}')
    else:
        member.unlink()
        if change == 'modified':
            member.write_text('changed')
        elif change == 'symlink':
            member.symlink_to(root / 'carrier/policy.go')
        elif change == 'hardlink':
            os.link(root / 'carrier/policy.go', member)
        elif change == 'fifo':
            os.mkfifo(member)
    with pytest.raises(ValueError):
        source.accepted(root, role)


def test_roles_and_root_alias_cannot_fall_back(capsules, tmp_path):
    with pytest.raises(ValueError):
        source.accepted(capsules['primary'], 'other')
    with pytest.raises(ValueError):
        source.accepted(capsules['primary'], 'secondary')
    alias = tmp_path / 'alias'
    alias.symlink_to(capsules['primary'], target_is_directory=True)
    with pytest.raises(ValueError):
        source.accepted(alias, 'primary')


def test_common_source_retains_canonical_policy(capsules):
    primary = source.accepted(capsules['primary'], 'primary')
    secondary = source.accepted(capsules['secondary'], 'secondary')
    result, differences = source.reconcile(primary, secondary)
    assert result == secondary and result is not secondary
    assert differences == ['carrier/engine.go']
    assert result['carrier/policy.go'] == primary['carrier/policy.go']


@pytest.mark.parametrize('change', ['policy', 'missing', 'extra', 'identical', 'lost-test'])
def test_unreviewed_drift_is_rejected(capsules, change):
    primary = source.accepted(capsules['primary'], 'primary')
    secondary = source.accepted(capsules['secondary'], 'secondary')
    if change == 'policy':
        secondary['carrier/policy.go'] = b'unsafe'
    elif change == 'missing':
        del secondary['carrier/policy.go']
    elif change == 'extra':
        secondary['private.key'] = b'synthetic'
    elif change == 'identical':
        secondary = dict(primary)
    else:
        primary['carrier/old_test.go'] = b'package old'
    with pytest.raises(ValueError):
        source.reconcile(primary, secondary)


def test_idle_projection_is_narrow(capsules, patch, monkeypatch):
    original = source.accepted(capsules['secondary'], 'secondary')
    monkeypatch.setenv('GIT_DIR', '/invalid')
    result = source.project(original, patch)
    assert result == {**original, 'carrier/engine.go': b'package corrected\n'}
    assert source.accepted(capsules['secondary'], 'secondary') == original
    with pytest.raises(ValueError):
        source.project(original, patch + b'\n')
    monkeypatch.setattr(source, 'CHANGED', frozenset(('carrier/policy.go',)))
    with pytest.raises(ValueError):
        source.project(original, patch)


def test_materialization_uses_committed_inputs_and_no_live_configuration(capsules, patch, tmp_path, monkeypatch):
    real_output = subprocess.check_output
    monkeypatch.setattr(source.subprocess, 'check_output', lambda *args, **kwargs: b'a' * 40 + b'\n')
    calls = []

    def committed(repository, ref, name):
        calls.append((ref, name))
        return patch if name == source.PATCH else b'package regression\n'

    monkeypatch.setattr(source, 'committed', committed)
    output = tmp_path / 'candidate'
    receipt = source.materialize(capsules['primary'], capsules['secondary'], output, 'HEAD')
    assert receipt['selected_base'] == 'secondary'
    assert receipt['production_configuration'] == 'absent' and receipt['operation_permit'] is None
    assert calls == [('a' * 40, source.PATCH)] + [(source.IDLE_SOURCE, name) for name in source.TESTS]
    assert receipt['files'] == {name: source.digest(raw) for name, raw in source.inventory(output).items()
                                if name != 'source-manifest.json'}
    assert (output / 'source-manifest.json').stat().st_mode & 0o777 == 0o600
    with pytest.raises(FileExistsError):
        source.materialize(capsules['primary'], capsules['secondary'], output, 'HEAD')
    with pytest.raises(ValueError):
        source.materialize(capsules['primary'], capsules['secondary'], capsules['primary'] / 'bad', 'HEAD')
    monkeypatch.setattr(source.subprocess, 'check_output', real_output)


def test_checked_in_projection_pin_and_scope():
    raw = (source.ROOT / source.PATCH).read_bytes()
    assert source.digest(raw) == source.PATCH_SHA256
    assert {line[6:].decode() for line in raw.splitlines() if line.startswith(b'+++ b/')} == {
        name.removeprefix('carrier/') for name in source.CHANGED}
    assert b'RELIABLE_IDLE_TIMEOUT' in raw
