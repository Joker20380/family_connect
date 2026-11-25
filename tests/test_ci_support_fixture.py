import hashlib
import json
from pathlib import Path

import pytest

from scripts import ci_support_fixture as fixture


def test_native_ci_reproduces_all_installed_pins_and_exact_candidate(tmp_path):
    environment = fixture.prepare(tmp_path / 'fixture')
    baseline = Path(environment['FC_TEST_SUPPORT_BASELINE'])
    expected = json.loads((fixture.ROOT / 'deploy/support-chat/support-capture-v1.json').read_text())['baseline']
    assert {path.relative_to(baseline).as_posix() for path in baseline.rglob('*') if path.is_file()} == set(expected)
    assert len(expected) == 19
    for name, digest in expected.items():
        assert hashlib.sha256((baseline / name).read_bytes()).hexdigest() == digest
    assert hashlib.sha256(Path(environment['FC_TEST_SUPPORT_ARCHIVE']).read_bytes()).hexdigest() == fixture.CANDIDATE_SHA256
    with pytest.raises(FileExistsError):
        fixture.prepare(tmp_path / 'fixture')


def test_wrong_historical_support_source_cannot_replace_pins(tmp_path, monkeypatch):
    monkeypatch.setattr(fixture.subprocess, 'check_output', lambda *args, **kwargs: b'wrong-source')
    with pytest.raises(ValueError, match='CI_BASELINE_PIN'):
        fixture.prepare(tmp_path / 'fixture')
    assert not (tmp_path / 'fixture/archive').exists()


def test_v2_preserves_v1_baseline_and_changes_only_reviewed_runtime():
    from scripts import package_support_capture as package
    original = json.loads((fixture.ROOT / 'deploy/support-chat/support-capture-v1.json').read_text())
    current = package.contract(fixture.ROOT)
    assert current['baseline'] == original['baseline']
    assert current['candidate'].keys() == original['candidate'].keys()
    changed = {name for name in current['candidate'] if current['candidate'][name] != original['candidate'][name]}
    assert changed == {'provisioning/support_runtime.py'}
    assert original['candidate']['provisioning/support_runtime.py'] == 'e24cba1a8bf913c0ba86d5269ff77bf1e5472d22fedf3fbf49750be2f16ba810'
    assert current['candidate']['provisioning/support_runtime.py'] == hashlib.sha256(
        (fixture.ROOT / 'provisioning/support_runtime.py').read_bytes()).hexdigest()


def test_native_ci_keeps_gil_systemd_and_zero_skip_gate():
    workflow = (fixture.ROOT / '.github/workflows/ha02-native.yml').read_text()
    assert 'ci_python314_context.sh' in workflow
    assert 'FC_TEST_SYSTEMD_SUPPORT_DRAIN: "1"' in workflow
    assert 'test_control_ha_support_terminal_native.py' in workflow
    assert 'test_control_ha_support_witness.py' in workflow
    assert "case.find('skipped') is None" in workflow
    assert 'sysctl' not in workflow and 'ptrace_scope' not in workflow
