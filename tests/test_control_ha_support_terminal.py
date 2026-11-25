import hashlib
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import threading

import pytest

from scripts import control_ha_support_exit as bridge
from scripts import control_ha_support_replace as replace
from scripts import control_ha_support_witness as witness


@pytest.fixture
def terminal(tmp_path):
    root = tmp_path / 'controller'
    root.mkdir(mode=0o700)
    participant = tmp_path / 'participant'
    drain = participant / 'drain'
    drain.mkdir(parents=True)
    plan = dict(schema=1, root=str(root), unit='fc-ha-support-replace-test-' + 'a' * 32 + '.service',
                user=True, dropin=str(tmp_path / 'never-installed'), participant=str(participant))
    replace.admission.write(root / 'plan.json', plan)
    replace.admission.write(drain / 'error.json', dict(reason='WORKERS_REMAIN', irreversible=True,
                                                      capture_permitted=False))
    return replace.Replacement(root)


@pytest.mark.parametrize('action', ['run', 'recover', 'rollback', 'old_exit'])
def test_irreversible_error_latches_original_evidence_before_any_runtime_action(terminal, monkeypatch, action):
    def forbidden(*args, **kwargs):
        pytest.fail('terminal failure must not touch service or install candidate')
    monkeypatch.setattr(terminal, 'validate', forbidden)
    monkeypatch.setattr(terminal.manager, 'call', forbidden)
    result = terminal.run(recover=True) if action == 'recover' else getattr(terminal, action)()
    assert result == (False if action == 'old_exit' else 'MANUAL_RECONCILIATION_REQUIRED')
    retained = replace.admission.read(terminal.root / 'terminal-failure.json')
    receipt = json.loads(retained)
    assert receipt['reason'] == 'WORKERS_REMAIN'
    assert receipt['evidence']['error.json'] == hashlib.sha256(
        replace.admission.read(terminal.drain / 'error.json')).hexdigest()
    assert all(receipt[name] is False for name in ('witness_permitted', 'opening_permitted', 'capture_permitted'))
    assert not terminal.dropin.exists()
    assert not terminal.has('rollback-intent')
    assert not terminal.has('accepted')
    (terminal.drain / 'error.json').unlink()
    assert terminal.run() == 'MANUAL_RECONCILIATION_REQUIRED'
    assert replace.admission.read(terminal.root / 'terminal-failure.json') == retained


def test_terminal_failure_cannot_issue_witness(terminal):
    with pytest.raises(ValueError, match='TERMINAL_RECONCILIATION_REQUIRED'):
        witness.sample(terminal.root, {})
    assert not terminal.has('handoff-reserved')


def test_terminal_cli_returns_non_restartable_status_and_original_cause(terminal):
    result = subprocess.run([sys.executable, '-m', 'scripts.control_ha_support_replace',
                             '--run', str(terminal.root)], capture_output=True, text=True, timeout=5)
    assert result.returncode == 78
    receipt = json.loads(result.stdout)
    assert receipt['result'] == 'MANUAL_RECONCILIATION_REQUIRED'
    assert receipt['reason'] == 'WORKERS_REMAIN'
    assert receipt['evidence']
    assert 'RestartPreventExitStatus=78' in replace.supervisor_unit(terminal.plan, sys.executable)


def test_reversible_error_is_not_latched_as_terminal(terminal):
    (terminal.drain / 'error.json').unlink()
    replace.admission.write(terminal.drain / 'error.json', dict(reason='COMMIT_EXPIRED', irreversible=False,
                                                              capture_permitted=False))
    assert not terminal.terminal_failure()
    assert terminal.old_exit_outcome() == 'WAITING_OLD_EXIT'
    assert not terminal.has('terminal-failure')


def test_census_is_bounded_and_does_not_export_thread_names_or_payloads(monkeypatch):
    worker = threading.current_thread()
    previous = worker.name
    worker.name = 'secret-message-key'
    try:
        result = bridge.census('before-exit', [('main', worker)] * 129, 'socket-parent-synced')
    finally:
        worker.name = previous
    assert not result['complete']
    assert result['errors'] == ['TRUNCATED']
    assert len(result['known_owners']) == 128
    assert 'secret-message-key' not in json.dumps(result)


def test_census_marks_read_failure_incomplete(monkeypatch):
    def unavailable():
        raise RuntimeError('must not export exception text')
    monkeypatch.setattr(threading, 'enumerate', unavailable)
    result = bridge.census('before-exit', [], 'socket-parent-synced')
    assert not result['complete']
    assert result['errors'] == ['SAMPLE_UNAVAILABLE']
    assert 'exception text' not in json.dumps(result)


@pytest.mark.parametrize('mode', ['kernel', 'persistence'])
def test_native_retirement_waits_for_owned_tail_missing_from_python_enumeration(mode):
    reader, writer = os.pipe()
    release_reader, release_writer = os.pipe()
    fixture = Path(__file__).parent / 'fixtures/support_native_tail.py'
    process = subprocess.Popen([sys.executable, '-I', '-B', str(fixture), str(writer), str(release_reader), mode],
                               pass_fds=(writer, release_reader), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    os.close(writer)
    os.close(release_reader)
    try:
        with os.fdopen(reader, 'rb', buffering=0) as stream:
            assert select.select([stream], [], [], 5)[0]
            snapshot = json.loads(stream.readline())
            assert snapshot['native_without_python']
            assert not select.select([stream], [], [], 0)[0]
            assert process.poll() is None
            os.write(release_writer, b'x')
            assert select.select([stream], [], [], 5)[0]
            assert stream.readline() == b'REAPED\n'
        stdout, stderr = process.communicate(timeout=5)
        assert process.returncode == 0, stderr.decode()
    finally:
        os.close(release_writer)
        if process.poll() is None:
            process.kill()
        process.wait(5)
