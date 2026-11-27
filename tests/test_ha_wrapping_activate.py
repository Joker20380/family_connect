from pathlib import Path
import subprocess

import pytest

from scripts import ha_wrapping_activate as activation
from scripts import ha_wrapping_key as wrapping


def test_current_entries_include_history_without_duplicate_identity():
    raw = b'<KeePassFile><Root><Group><Entry><UUID>one</UUID><History><Entry><UUID>one</UUID>' \
          b'</Entry></History></Entry><Group><Entry><UUID>two</UUID></Entry></Group></Group></Root></KeePassFile>'
    assert set(activation.entries(raw)) == {'one', 'two'}


def test_native_selective_existing_key_and_changed_working_entries(tmp_path, monkeypatch):
    assert Path('/usr/bin/keepassxc-cli').is_file(), 'native dependency required, not a skip'
    password = b'public disposable selective-copy test'
    working = tmp_path / wrapping.DATABASE
    actual = subprocess.run
    result = actual(['/usr/bin/keepassxc-cli', 'db-create', '-p', '-t', '100', str(working)],
        input=password + b'\n' + password + b'\n', capture_output=True, timeout=30)
    assert result.returncode == 0
    working.chmod(0o600)

    def run(command, **options):
        assert password.decode() not in ' '.join(command)
        if command[0] == '/usr/bin/zenity':
            return subprocess.CompletedProcess(command, 0, password + b'\n')
        if command[0] == '/usr/bin/pgrep':
            return subprocess.CompletedProcess(command, 1)
        return actual(command, **options)

    monkeypatch.setattr(activation.subprocess, 'run', run)
    wrapping.prepare(working, tmp_path / 'candidate')
    candidate = tmp_path / 'candidate' / wrapping.DATABASE
    existing_key = wrapping.load(candidate)
    latest = actual(['/usr/bin/keepassxc-cli', 'add', '-q', str(working), 'new-working-entry'],
        input=password + b'\n', capture_output=True, timeout=30)
    assert latest.returncode == 0
    encrypted_before = working.read_bytes()
    monkeypatch.setattr(wrapping.secrets, 'token_bytes', lambda size: pytest.fail('new key generated'))
    receipt = activation.activate(candidate, working, tmp_path / 'activation')
    assert receipt['other_entries_unchanged'] and not receipt['whole_vault_replaced']
    assert not receipt['new_key_generated']
    assert (tmp_path / 'activation/working-before.kdbx').read_bytes() == encrypted_before
    assert wrapping.load(working) == existing_key
    active = working.read_bytes()
    with pytest.raises(ValueError, match='HA_ACTIVATION_REFUSED'):
        activation.activate(candidate, working, tmp_path / 'duplicate')
    assert working.read_bytes() == active
    assert (tmp_path / 'duplicate/failed.json').is_file()


def test_open_gui_refuses_before_vault_write(tmp_path, monkeypatch):
    def run(command, **options):
        return subprocess.CompletedProcess(command, 0)
    monkeypatch.setattr(activation.subprocess, 'run', run)
    with pytest.raises(ValueError, match='HA_GUI_MUST_BE_CLOSED'):
        activation.activate(tmp_path / 'candidate/Family-Connect.kdbx', tmp_path / 'Family-Connect.kdbx',
                            tmp_path / 'journal')
    assert not (tmp_path / 'journal').exists()
