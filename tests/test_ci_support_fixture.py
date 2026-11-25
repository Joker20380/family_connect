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


def test_native_ci_keeps_gil_systemd_and_zero_skip_gate():
    workflow = (fixture.ROOT / '.github/workflows/ha02-native.yml').read_text()
    assert 'ci_python314_context.sh' in workflow
    assert 'FC_TEST_SYSTEMD_SUPPORT_DRAIN: "1"' in workflow
    assert 'test_control_ha_support_terminal_native.py' in workflow
    assert 'test_control_ha_support_witness.py' in workflow
    assert "case.find('skipped') is None" in workflow
    assert 'sysctl' not in workflow and 'ptrace_scope' not in workflow
