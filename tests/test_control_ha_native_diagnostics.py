from pathlib import Path
import subprocess

import pytest

from scripts import control_ha_maintenance_fixture as fixture


@pytest.mark.parametrize('timeout', [False, True])
def test_native_failure_retains_original_stderr_without_issuer_stdout(tmp_path, monkeypatch, timeout):
    diagnostic = tmp_path / 'diagnostics'
    monkeypatch.setenv('FC_NATIVE_DIAGNOSTICS_DIR', str(diagnostic))
    def run(arguments, **kwargs):
        if 'inspect' in arguments:
            return subprocess.CompletedProcess(arguments, 1, b'', b'')
        if timeout:
            raise subprocess.TimeoutExpired(arguments, 45, output=b'private fixture output',
                                            stderr=b'original native failure')
        return subprocess.CompletedProcess(arguments, 125, b'private fixture output', b'original native failure')
    monkeypatch.setattr(fixture.subprocess, 'run', run)
    with pytest.raises(ValueError, match='NATIVE_ROOT_FIXTURE_(FAILED|TIMEOUT)') as error:
        fixture.capture_container({'synthetic': b'not exported'}, tmp_path)
    path = Path(str(error.value).split(': ', 1)[1])
    assert path.parent == diagnostic
    assert b'original native failure' in path.read_bytes()
    assert b'private fixture output' not in path.read_bytes()
    assert b'not exported' not in path.read_bytes()
    assert path.stat().st_mode & 0o777 == 0o600


def test_truncated_native_diagnostic_is_explicit(tmp_path, monkeypatch):
    monkeypatch.setenv('FC_NATIVE_DIAGNOSTICS_DIR', str(tmp_path))
    path = Path(fixture.retain_failure(b'x' * 1048577, 'exit-1'))
    assert path.read_bytes().endswith(b'DIAGNOSTIC_INCOMPLETE: STDERR_TRUNCATED\n')


def test_ci_uploads_native_diagnostics_on_full_suite_failure():
    root = Path(__file__).resolve().parents[1]
    for name in ('test.yml', 'control.yml'):
        source = (root / '.github/workflows' / name).read_text()
        assert '${{ runner.temp }}/native-fixtures/' in source
    assert 'FC_NATIVE_DIAGNOSTICS_DIR=' in (root / 'scripts/ci_full_suite.sh').read_text()
