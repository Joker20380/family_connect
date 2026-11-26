import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from scripts import control_ha_support_entry as entry


def context(tmp_path):
    tmp_path.chmod(0o700)
    return dict(phase='authority', diagnostics=tmp_path, archive=tmp_path / 'candidate.pyz',
                authority=tmp_path / 'authority.json')


@pytest.mark.parametrize('reason', sorted(entry.REASONS))
def test_refusal_is_bounded_private_and_bound_to_this_process(tmp_path, reason):
    receipt = entry.refusal(context(tmp_path), ValueError(reason))
    files = list(tmp_path.iterdir())
    assert len(files) == 1 and files[0].stat().st_mode & 0o777 == 0o600
    assert files[0].stat().st_size <= 2048
    assert json.loads(files[0].read_bytes()) == receipt
    assert receipt['binding'] == entry.binding()
    assert receipt['reason'] == reason and receipt['phase'] == 'authority'
    assert receipt['admission_permitted'] is False and receipt['capture_permitted'] is False
    assert receipt['authority_path_sha256'] == hashlib.sha256(os.fsencode(tmp_path / 'authority.json')).hexdigest()
    assert str(tmp_path) not in files[0].read_text()


@pytest.mark.parametrize('phase,expected', [('authority', 'STARTUP_INPUT_ERROR'),
                                         ('candidate', 'CANDIDATE_EXCEPTION'),
                                         ('arguments', 'STARTUP_INPUT_ERROR')])
def test_arbitrary_exception_text_is_not_retained(tmp_path, phase, expected):
    receipt = entry.refusal(dict(context(tmp_path), phase=phase), ValueError('PRIVATE_MESSAGE_OR_KEY'))
    assert receipt['reason'] == expected
    assert 'PRIVATE_MESSAGE_OR_KEY' not in next(tmp_path.iterdir()).read_text()


def test_candidate_exit_is_not_reported_as_stale_authority(tmp_path):
    receipt = entry.refusal(dict(context(tmp_path), phase='candidate'), SystemExit(78))
    assert receipt['phase'] == 'candidate' and receipt['reason'] == 'CANDIDATE_EXIT'


@pytest.mark.parametrize('failure', ['full', 'symlink', 'permissions', 'fsync', 'binding', 'duplicate'])
def test_diagnostic_failure_never_admits_or_overwrites(tmp_path, monkeypatch, failure):
    values = context(tmp_path)
    original = None
    if failure == 'full':
        for number in range(128):
            (tmp_path / str(number)).touch()
    elif failure == 'symlink':
        link = tmp_path / 'link'
        link.symlink_to(tmp_path, target_is_directory=True)
        values['diagnostics'] = link
    elif failure == 'permissions':
        tmp_path.chmod(0o755)
    elif failure == 'fsync':
        monkeypatch.setattr(entry.os, 'fsync', lambda *args: (_ for _ in ()).throw(OSError('private')))
    elif failure == 'binding':
        monkeypatch.setattr(entry, 'binding', lambda: (_ for _ in ()).throw(OSError('private')))
    else:
        entry.refusal(values, ValueError('START_AUTHORITY_FILE'))
        original = next(tmp_path.iterdir()).read_bytes()
    receipt = entry.refusal(values, ValueError('START_AUTHORITY_CHANGED'))
    assert receipt['admission_permitted'] is False and receipt['reason'] == 'START_AUTHORITY_CHANGED'
    if failure == 'duplicate':
        assert next(tmp_path.iterdir()).read_bytes() == original
    if failure == 'full':
        assert len(list(tmp_path.iterdir())) == 128


def test_actual_stale_boot_entry_refuses_without_executing_candidate(tmp_path):
    diagnostics = tmp_path / 'diagnostics'
    diagnostics.mkdir(mode=0o700)
    archive = tmp_path / 'candidate.py'
    archive.write_text('raise RuntimeError("candidate must not execute")')
    authority = tmp_path / 'authority.json'
    authority.write_text(json.dumps(dict(schema=1, binding=dict(entry.binding(), boot='old-boot'),
                                        archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest())))
    authority.chmod(0o600)
    result = subprocess.run([sys.executable, '-I', '-B', str(Path(entry.__file__).resolve()),
                             '--refusal-directory', str(diagnostics), str(archive), str(authority), str(os.getuid())],
                            capture_output=True, timeout=10)
    assert result.returncode == 78 and result.stdout == b''
    receipt = json.loads(result.stderr)
    assert receipt['reason'] == 'START_AUTHORITY_CHANGED' and receipt['phase'] == 'authority'
    assert receipt == json.loads(next(diagnostics.iterdir()).read_bytes())
    assert receipt['binding']['pid'] != os.getpid()


def test_valid_authority_still_requires_exact_live_binding(tmp_path):
    archive = tmp_path / 'candidate.py'
    archive.write_bytes(b'')
    authority = tmp_path / 'authority.json'
    current = entry.binding()
    value = dict(schema=1, binding=current, archive_sha256=hashlib.sha256(b'').hexdigest())
    authority.write_text(json.dumps(value))
    authority.chmod(0o600)
    entry.admitted(authority, os.getuid(), archive)
    for field in ('pid', 'start', 'boot', 'command', 'cgroup'):
        authority.write_text(json.dumps(dict(value, binding=dict(current, **{field: 'stale'}))))
        with pytest.raises(ValueError, match='START_AUTHORITY_CHANGED'):
            entry.admitted(authority, os.getuid(), archive)
