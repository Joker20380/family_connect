from pathlib import Path
import subprocess
import base64
import gzip
import json
import os
import sys

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
    actual(['/usr/bin/keepassxc-cli', 'add', '-q', str(working), 'existing-attachment'],
           input=password + b'\n', capture_output=True, check=True, timeout=30)
    attachment = tmp_path / 'public-test-attachment'
    attachment.write_bytes(b'public disposable existing attachment')
    actual(['/usr/bin/keepassxc-cli', 'attachment-import', '-q', str(working), 'existing-attachment',
            'original', str(attachment)], input=password + b'\n', capture_output=True, check=True, timeout=30)

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
    activation.record(tmp_path / 'activation', 'failed.json', dict(cause='SIMULATED_RESPONSE_LOSS'))
    result = activation.reconcile(candidate, working, tmp_path / 'activation')
    assert result['reconciliation_read_only'] and result['prior_failure_retained']
    assert working.read_bytes() == active
    with pytest.raises(ValueError, match='HA_ACTIVATION_REFUSED'):
        activation.activate(candidate, working, tmp_path / 'duplicate')
    assert working.read_bytes() == active
    assert (tmp_path / 'duplicate/failed.json').is_file()


def test_binary_reference_reordering_preserves_bytes_not_numeric_indices():
    def xml(index, content):
        data = base64.b64encode(gzip.compress(content)).decode()
        return ('<KeePassFile><Meta><Binaries><Binary ID="' + index + '" Compressed="True">' + data +
            '</Binary></Binaries></Meta><Root><Group><Entry><UUID>one</UUID><Binary><Key>old</Key>'
            '<Value Ref="' + index + '"/></Binary></Entry></Group></Root></KeePassFile>').encode()
    assert activation.entries(xml('0', b'old attachment')) == activation.entries(xml('7', b'old attachment'))
    assert activation.entries(xml('0', b'old attachment')) != activation.entries(xml('0', b'changed'))


@pytest.mark.parametrize('failed_stage', ['PRESTATE_EXPORT', 'WORKING_EXPORT',
    'CANDIDATE_CONSUMER', 'WORKING_CONSUMER', 'PRESERVATION_COMPARE'])
def test_native_read_only_stage_receipts(tmp_path, monkeypatch, failed_stage):
    password = b'disposable stage test password'
    actual = subprocess.run
    working = tmp_path / wrapping.DATABASE
    result = actual(['/usr/bin/keepassxc-cli', 'db-create', '-p', '-t', '100', str(working)],
        input=password + b'\n' + password + b'\n', capture_output=True, timeout=30)
    assert result.returncode == 0
    working.chmod(0o600)

    def dialogs(command, **options):
        if command[0] == '/usr/bin/zenity':
            return subprocess.CompletedProcess(command, 0, password + b'\n')
        if command[0] == '/usr/bin/pgrep':
            return subprocess.CompletedProcess(command, 1)
        return actual(command, **options)

    monkeypatch.setattr(activation.subprocess, 'run', dialogs)
    wrapping.prepare(working, tmp_path / 'candidate')
    candidate = tmp_path / 'candidate' / wrapping.DATABASE
    journal = tmp_path / 'activation'
    activation.activate(candidate, working, journal)
    activation.record(journal, 'failed.json', dict(cause='ORIGINAL_RESPONSE_LOSS'))
    first = (journal / 'failed.json').read_bytes()
    if failed_stage == 'PRESERVATION_COMPARE':
        added = actual(['/usr/bin/keepassxc-cli', 'add', '-q', str(working), 'unexpected'],
            input=password + b'\n', capture_output=True, timeout=30)
        assert added.returncode == 0
    original = working.read_bytes()

    def refused(command, **options):
        if command[0] == '/usr/bin/keepassxc-cli':
            path = Path(os.readlink(command[3]))
            stage = ('PRESTATE_EXPORT' if path.name == 'working-before.kdbx' else 'WORKING_EXPORT')
            if command[1] == 'attachment-export':
                stage = 'CANDIDATE_CONSUMER' if path.parent.name == 'candidate' else 'WORKING_CONSUMER'
            if stage == failed_stage:
                options['input'] = b'intentionally incorrect disposable password\n'
        return dialogs(command, **options)

    monkeypatch.setattr(activation.subprocess, 'run', refused)
    with pytest.raises(activation.StageRefused) as raised:
        activation.reconcile(candidate, working, journal)
    assert raised.value.stage == failed_stage
    receipt, = journal.glob(f'reconcile-*-{failed_stage}.json')
    data = json.loads(receipt.read_bytes())
    assert data['stage'] == failed_stage and data['vault_write'] is False
    if failed_stage == 'PRESERVATION_COMPARE':
        assert data['category'] == 'PRESERVATION_CHANGED' and data['exit_status'] is None
    else:
        assert data['category'] == 'NATIVE_EXIT' and data['exit_status'] != 0
    assert (journal / 'failed.json').read_bytes() == first
    assert working.read_bytes() == original
    assert not (journal / 'reconciled.json').exists()
    postcheck, = journal.glob('reconcile-*-WORKING_POSTCHECK.json')
    assert json.loads(postcheck.read_bytes())['category'] == 'PASS'
    for receipt in journal.glob('reconcile-*.json'):
        assert password not in receipt.read_bytes() and b'<KeePassFile' not in receipt.read_bytes()


def test_open_gui_refuses_before_vault_write(tmp_path, monkeypatch):
    def run(command, **options):
        return subprocess.CompletedProcess(command, 0)
    monkeypatch.setattr(activation.subprocess, 'run', run)
    with pytest.raises(ValueError, match='HA_GUI_MUST_BE_CLOSED'):
        activation.activate(tmp_path / 'candidate/Family-Connect.kdbx', tmp_path / 'Family-Connect.kdbx',
                            tmp_path / 'journal')
    assert not (tmp_path / 'journal').exists()


def test_reconciliation_refusal_records_safe_code_without_overwriting_first_cause(tmp_path, monkeypatch, capsys):
    journal = tmp_path / 'journal'
    journal.mkdir(mode=0o700)
    activation.record(journal, 'failed.json', dict(cause='HA_OTHER_ENTRIES_CHANGED'))
    original = (journal / 'failed.json').read_bytes()
    def refused(*args):
        raise ValueError('HA_RECONCILE_NATIVE_READ_REFUSED')
    monkeypatch.setattr(activation, 'reconcile', refused)
    monkeypatch.setattr(sys, 'argv', ['activate', '--reconcile', '--candidate', '/candidate/Family-Connect.kdbx',
        '--working', '/working/Family-Connect.kdbx', '--journal', str(journal)])
    with pytest.raises(SystemExit) as error:
        activation.main()
    assert error.value.code == 1
    assert 'HA_RECONCILE_NATIVE_READ_REFUSED' in capsys.readouterr().err
    assert (journal / 'failed.json').read_bytes() == original
    attempt, = journal.glob('reconcile-refused-*.json')
    assert json.loads(attempt.read_bytes())['vault_write'] is False
