import json
import os
import subprocess
import sys

import pytest

from control.friends import transport_gateway as module
from test_transport_enforcement import engine, envelope, registry


@pytest.mark.parametrize('scenario,phase,boundary,remaining,duration,replaced', [
    ('before', 'persist_file', 'before', -0.1, None, False),
    ('query', 'persist_file', 'after', 0.05, 0.1, False),
    ('file', 'persist_file', 'after', 8, 8.1, False),
    ('replace', 'persist_replace', 'after', 7.99, 8.1, True),
    ('directory', 'persist_directory', 'after', 7.99, 8.1, True),
])
def test_individual_calls_distinguish_total_deadline(tmp_path, monkeypatch, scenario,
        phase, boundary, remaining, duration, replaced):
    clock = [10.0]
    monkeypatch.setattr(module.time, 'monotonic', lambda: clock[0])
    original_sync, original_replace = os.fsync, os.replace
    sync_calls = []

    def sync(descriptor):
        sync_calls.append(descriptor)
        original_sync(descriptor)
        clock[0] += (8.1 if scenario == 'file' and len(sync_calls) == 1
            or scenario == 'directory' and len(sync_calls) == 2 else .1 if scenario == 'query' else .01)

    def replace(source, target):
        original_replace(source, target)
        if scenario == 'replace':
            clock[0] += 8.1

    monkeypatch.setattr(module.os, 'fsync', sync)
    monkeypatch.setattr(module.os, 'replace', replace)
    operation = module.Operation()
    token = module.CURRENT_OPERATION.set(operation)
    try:
        if scenario == 'before':
            clock[0] += 8.1
        if scenario == 'query':
            with operation.stage('engine_query'), module.measured_call('tcp-query'):
                clock[0] += 7.95
        with pytest.raises(TimeoutError) as caught:
            module.write(tmp_path/'transport-attempt.json', dict(secret='not in diagnostics'))
    finally:
        module.CURRENT_OPERATION.reset(token)
    record = module.failure_record(caught.value, 'watch')
    assert record['phase'] == phase and record['boundary'] == boundary
    assert record['elapsed'] > 8 and record['budget'] == 8
    call = record['calls'][-1]
    assert call['remaining'] == pytest.approx(remaining)
    if duration is None:
        assert call['duration'] is None
    else:
        assert call['duration'] == pytest.approx(duration)
    assert call['completed'] == (scenario != 'before')
    assert call['replace_completed'] is replaced
    assert call['role'] == 'attempt_result'
    assert (tmp_path/'transport-attempt.json').exists() is replaced
    assert len(sync_calls) == (0 if scenario == 'before' else 2 if scenario == 'directory' else 1)
    assert 'secret' not in json.dumps(record) and str(tmp_path) not in json.dumps(record)
    if scenario == 'query':
        assert record['calls'][0]['kind'] == 'tcp-query'
        assert record['calls'][0]['duration'] == pytest.approx(7.95)


def test_converged_readback_keeps_both_durable_writes(engine, registry):
    gateway = engine[0]
    gateway.accept(envelope(registry))
    gateway.apply()
    gateway.apply()
    assert gateway.metrics['stage_counts']['readback'] == 1
    calls = gateway.metrics['calls']
    assert [(call['role'], call['kind']) for call in calls] == [
        (role, kind) for role in ('decision_state', 'attempt_result')
        for kind in ('file_fsync', 'replace', 'directory_fsync')]
    assert all(call['completed'] for call in calls)
    assert gateway.metrics['stage_counts']['persist_file'] == 2
    assert gateway.load()['records']
    assert json.loads((gateway.root/'transport-attempt.json').read_text())['result'] == 'applied'


def test_command_details_do_not_disclose_arguments_and_preserve_primary_failure(tmp_path, capsys):
    operation = module.Operation()
    token = module.CURRENT_OPERATION.set(operation)
    try:
        with pytest.raises(subprocess.CalledProcessError) as caught:
            with operation.stage('engine_query'):
                module.execute([sys.executable, '-c', 'import sys;print("secret-profile");sys.exit(7)'])
    finally:
        module.CURRENT_OPERATION.reset(token)
    module.report_failure(caught.value, 'watch', tmp_path)
    first = (tmp_path/'transport-failure.json').read_bytes()
    module.report_failure(ValueError('ENGINE_START_TIMEOUT'), 'watch', tmp_path)
    assert (tmp_path/'transport-failure.json').read_bytes() == first
    record = json.loads(first)
    assert record['phase'] == 'engine_query' and record['boundary'] == 'body'
    assert record['returncode'] == 7 and record['calls'][0]['duration'] >= 0
    assert not record['calls'][0]['completed']
    assert 'secret-profile' not in capsys.readouterr().err


def test_diagnostic_history_bounded_and_resource_read_optional(monkeypatch):
    monkeypatch.setattr(module, 'process_usage', lambda: None)
    operation = module.Operation()
    for count in range(40):
        with operation.call('file_fsync', role='unknown'):
            pass
    assert len(operation.calls) == 24 and operation.calls_dropped == 16
    assert all(call['completed'] and 'self_cpu_seconds' not in call for call in operation.calls)
