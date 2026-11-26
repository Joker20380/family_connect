import hashlib
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from control.capture_gate import GateError, initialize
from scripts import control_ha_capture_guard as guard


@pytest.fixture
def gate(tmp_path):
    return initialize(tmp_path / 'gate')


def invoke(gate):
    result = subprocess.run([sys.executable, '-m', 'scripts.control_ha_capture_guard',
        '--gate', str(gate.directory), '--drain-seconds', '.1'], input='', capture_output=True,
        text=True, timeout=3, cwd=Path(__file__).resolve().parents[1])
    assert result.returncode == 1
    assert not result.stderr
    return json.loads(result.stdout)


def test_uncertain_operation_has_exact_retained_marker_evidence(gate):
    with gate.operation() as operation:
        operation.uncertain()
    marker, = (gate.directory / 'pending').iterdir()
    before = marker.read_bytes()
    receipt = invoke(gate)
    assert receipt['reason'] == 'UNSETTLED_OPERATION'
    evidence = receipt['evidence']
    assert evidence['scope'] == 'AFTER_REFUSAL_NON_ATOMIC'
    assert evidence['complete'] is True and evidence['settlement_proven'] is False
    assert evidence['capture_permitted'] is False and receipt['capture_permitted'] is False
    assert evidence['marker_contents_read'] is False
    entry, = evidence['pending_entries']
    assert entry['name_sha256'] == hashlib.sha256(os.fsencode(marker.name)).hexdigest()
    assert entry['inode'] == marker.stat().st_ino and entry['size'] == len(before)
    raw = json.dumps(evidence, sort_keys=True, separators=(',', ':')).encode()
    assert receipt['evidence_sha256'] == hashlib.sha256(raw).hexdigest()
    assert marker.read_bytes() == before
    assert marker.name not in json.dumps(receipt)
    with gate.operation():
        pass
    assert marker.exists()


def test_live_writer_timeout_is_distinct_and_does_not_clear_marker(gate):
    with gate.operation():
        receipt = invoke(gate)
        assert receipt['reason'] == 'DRAIN_TIMEOUT'
        assert len(receipt['evidence']['pending_entries']) == 1
        assert len(list((gate.directory / 'pending').iterdir())) == 1
    with gate.drain(.1):
        pass


def test_competing_controller_does_not_release_first_boundary(gate):
    with gate.drain(.1):
        receipt = invoke(gate)
        assert receipt['reason'] == 'CAPTURE_ALREADY_PENDING'
        assert receipt['evidence']['pending_entries'] == []
        assert receipt['capture_permitted'] is False
        with pytest.raises(GateError, match='CAPTURE_ADMISSION_CLOSED'):
            with gate.operation():
                pytest.fail('competing refusal opened admission')


@pytest.mark.parametrize('kind', ['file', 'symlink', 'directory', 'fifo'])
def test_unknown_entries_are_not_read_followed_or_removed(gate, tmp_path, kind):
    target = tmp_path / 'private-target'
    target.write_text('private-payload')
    entry = gate.directory / 'pending/private-operation'
    if kind == 'file':
        entry.write_text('private-payload')
    elif kind == 'symlink':
        entry.symlink_to(target)
    elif kind == 'directory':
        entry.mkdir()
    else:
        os.mkfifo(entry)
    receipt = invoke(gate)
    assert receipt['reason'] == 'UNSETTLED_OPERATION'
    record, = receipt['evidence']['pending_entries']
    assert record['kind'] == stat.S_IFMT(entry.lstat().st_mode)
    assert 'private-' not in json.dumps(receipt)
    assert entry.lstat() and target.read_text() == 'private-payload'


def test_bounded_inventory_is_never_described_as_complete(gate, monkeypatch):
    monkeypatch.setattr(guard, 'MAX_PENDING', 2)
    for name in ('one', 'two', 'three'):
        (gate.directory / 'pending' / name).touch()
    evidence = guard.refusal_evidence(gate)
    assert len(evidence['pending_entries']) == 2 and evidence['complete'] is False
    assert len(list((gate.directory / 'pending').iterdir())) == 3


def test_replaced_gate_cannot_be_used_as_refusal_evidence(gate):
    directory = gate.directory / 'pending'
    directory.rename(gate.directory / 'retained')
    directory.mkdir(mode=0o700)
    receipt = guard.refusal(GateError('GATE_REPLACED'), gate)
    assert receipt['reason'] == 'GATE_REPLACED'
    assert receipt['evidence']['status'] == 'UNAVAILABLE'
    assert receipt['evidence']['complete'] is False


def test_unexpected_error_does_not_leak_message_or_paths():
    receipt = guard.refusal(OSError('private-key-path'), None)
    assert receipt['reason'] == 'GATE_IO_REFUSED'
    assert receipt['evidence']['status'] == 'GATE_NOT_OPENED'
    assert 'private-key-path' not in json.dumps(receipt)


def test_missing_gate_reports_io_class_without_private_path(tmp_path):
    result = subprocess.run([sys.executable, '-m', 'scripts.control_ha_capture_guard',
        '--gate', str(tmp_path / 'private-missing')], input='', capture_output=True,
        text=True, timeout=3, cwd=Path(__file__).resolve().parents[1])
    assert result.returncode == 1 and not result.stderr
    receipt = json.loads(result.stdout)
    assert receipt['reason'] == 'GATE_IO_REFUSED' and receipt['error_type'] == 'FileNotFoundError'
    assert receipt['errno'] == 2 and 'private-missing' not in result.stdout


def test_evidence_failure_does_not_mask_original_refusal(gate, monkeypatch):
    def unavailable(*args):
        raise PermissionError('private-path')
    monkeypatch.setattr(guard.os, 'scandir', unavailable)
    receipt = guard.refusal(GateError('UNSETTLED_OPERATION'), gate)
    assert receipt['reason'] == 'UNSETTLED_OPERATION'
    assert receipt['evidence']['status'] == 'UNAVAILABLE'
    assert 'private-path' not in json.dumps(receipt)
