import json
import subprocess
import sys

import pytest

from control.friends import transport_gateway as module
from test_transport_enforcement import engine, envelope, registry


def test_first_failure_precedes_cleanup_and_survives_secondary_failure(engine, registry, capsys):
    gateway = engine[0]
    gateway.accept(envelope(registry))
    original = module.execute
    def query(arguments):
        if 'inbounduser' in arguments:
            raise subprocess.CalledProcessError(7, arguments, stderr=b'private-identity-proof')
        return b''
    gateway.run = query
    with pytest.raises(subprocess.CalledProcessError) as caught:
        gateway.apply()
    before = gateway.path.read_bytes()
    def cleanup():
        first = json.loads((gateway.root/'transport-failure.json').read_text())
        assert first['command_family'] == 'tcp-query'
        raise RuntimeError('cleanup-private-identity')
    gateway.stop_all = cleanup
    gateway.fail_closed(caught.value, 'watch')
    first = (gateway.root/'transport-failure.json').read_bytes()
    gateway.fail_closed(ValueError('ENGINE_START_TIMEOUT'), 'watch')
    assert (gateway.root/'transport-failure.json').read_bytes() == first
    assert gateway.path.read_bytes() == before
    record = json.loads(first)
    assert record['reason'] == 'COMMAND_FAILED' and record['returncode'] == 7
    assert record['phase'] == 'engine_query' and record['elapsed'] >= 0
    assert record['pid'] > 0 and record['budget'] == 8
    assert json.loads((gateway.root/'transport-attempt.json').read_text())['result'] == 'error'
    assert (gateway.root/'transport-failure.json').stat().st_mode & 0o777 == 0o600
    assert 'private-identity' not in capsys.readouterr().err
    assert module.execute is original


def test_persistence_deadline_identifies_phase_without_claiming_native_failure(tmp_path, monkeypatch):
    clock = [10.0]
    monkeypatch.setattr(module.time, 'monotonic', lambda: clock[0])
    operation = module.Operation()
    monkeypatch.setattr(module.os, 'fsync', lambda descriptor: clock.__setitem__(0, 19.0))
    token = module.CURRENT_OPERATION.set(operation)
    try:
        with pytest.raises(TimeoutError) as caught:
            module.write(tmp_path/'state.json', dict(secret='not logged'))
    finally:
        module.CURRENT_OPERATION.reset(token)
    record = module.failure_record(caught.value, 'register')
    assert record['phase'] == 'persist_file'
    assert record['reason'] == 'TRANSPORT_OPERATION_DEADLINE'
    assert record['elapsed'] == 9
    assert 'command_family' not in record
    assert not (tmp_path/'state.json').exists()


def test_executor_timeout_retains_safe_family_not_arguments_or_output(tmp_path, capsys):
    token = module.CURRENT_OPERATION.set(module.Operation(.1))
    try:
        with pytest.raises(subprocess.TimeoutExpired) as caught:
            module.execute([sys.executable, '-c', 'import time;print("private-proof");time.sleep(5)'])
    finally:
        module.CURRENT_OPERATION.reset(token)
    module.report_failure(caught.value, 'register', tmp_path)
    record = json.loads((tmp_path/'transport-failure.json').read_text())
    assert record['reason'] == 'COMMAND_TIMEOUT' and record['timeout'] is True
    assert record['command_family'] == 'other' and record['returncode'] is None
    assert 'private-proof' not in capsys.readouterr().err


def test_arbitrary_exception_and_invocation_are_not_logged(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv('INVOCATION_ID', 'private-invocation')
    module.report_failure(ValueError('private-binding-and-request-json'), 'untrusted-mode', tmp_path)
    record = json.loads((tmp_path/'transport-failure.json').read_text())
    assert record['reason'] == 'INVALID_INPUT_OR_STATE'
    assert record['mode'] == 'unknown' and record['invocation_id'] is None
    assert 'private-' not in capsys.readouterr().err


def test_failed_diagnostic_channels_do_not_prevent_protective_stop(engine, monkeypatch):
    gateway = engine[0]
    calls = []
    def unavailable(*arguments, **keywords):
        raise OSError('diagnostic storage unavailable')
    monkeypatch.setattr('builtins.print', unavailable)
    monkeypatch.setattr(module.os, 'open', unavailable)
    gateway.stop_all = lambda: calls.append('stop')
    gateway.fail_closed(ValueError('ENGINE_READBACK_MISMATCH'), 'watch')
    assert calls == ['stop']
