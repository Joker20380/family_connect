from contextvars import copy_context
import json
from pathlib import Path
import select
import subprocess
import sys
from types import SimpleNamespace
import time

import pytest

from control.capture_gate import Busy, CURRENT, GateError, initialize
from provisioning import owner_capture, subscription_collector, support_bindings


@pytest.fixture
def setup(tmp_path, monkeypatch):
    gate = initialize(tmp_path / 'gate')
    monkeypatch.setenv('FC_OWNER_CAPTURE_GATE', str(gate.directory))
    key, hosts, output = [tmp_path / name for name in ('key', 'hosts', 'projection')]
    key.write_text('synthetic-not-a-key'); key.chmod(0o600)
    hosts.write_text('synthetic-not-a-host')
    output.write_bytes(b'original-projection')
    calls = []
    def response(command, **options):
        assert CURRENT.get() is not None
        calls.append(command)
        options['stdout'].write(json.dumps(dict(expires_at=int(time.time())+100)).encode())
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(support_bindings.subprocess, 'run', response)
    return gate, key, hosts, output, calls


def pending(gate):
    return {path.name: path.read_bytes() for path in (gate.directory / 'pending').iterdir()}


def test_manual_collect_refuses_before_dispatch_and_preserves_projection(setup):
    gate, key, hosts, output, calls = setup
    with gate.drain(.1):
        with pytest.raises(Busy, match='CAPTURE_ADMISSION_CLOSED'):
            support_bindings.collect('127.0.0.1', key, hosts, output)
    assert not calls and output.read_bytes() == b'original-projection' and not pending(gate)
    support_bindings.collect('127.0.0.1', key, hosts, output)
    assert len(calls) == 1 and json.loads(output.read_bytes())['expires_at'] > time.time()
    assert not pending(gate)


def test_notifications_refuses_before_cursor_or_ssh(setup, monkeypatch):
    gate, key, hosts, output, calls = setup
    monkeypatch.setattr('sys.argv', ['collector', '--host', '127.0.0.1', '--key', str(key),
        '--known-hosts', str(hosts), '--output', str(output), '--socket', '/synthetic/unreachable'])
    monkeypatch.setattr(subscription_collector, 'command', lambda path: pytest.fail('IPC before admission'))
    with gate.drain(.1):
        with pytest.raises(SystemExit) as refused:
            subscription_collector.main()
    assert refused.value.code == 75 and not calls and output.read_bytes() == b'original-projection'


def test_failed_dispatch_preserves_pending_and_original_projection(setup, monkeypatch):
    gate, key, hosts, output, calls = setup
    def failure(*arguments, **keywords):
        raise TimeoutError('synthetic response lost')
    monkeypatch.setattr(support_bindings.subprocess, 'run', failure)
    with pytest.raises(TimeoutError):
        support_bindings.collect('127.0.0.1', key, hosts, output)
    assert len(pending(gate)) == 1 and output.read_bytes() == b'original-projection'
    with pytest.raises(GateError, match='UNSETTLED_OPERATION'):
        with gate.drain(.1):
            pytest.fail('lost collector response settled')


def test_nested_collect_shares_gate_but_stale_copy_refuses(setup):
    gate, key, hosts, output, calls = setup
    with owner_capture.operation():
        copied = copy_context()
        support_bindings.collect('127.0.0.1', key, hosts, output)
        assert len(pending(gate)) == 1
    assert not pending(gate)
    with pytest.raises(GateError, match='OWNER_CAPTURE_STALE_CONTEXT'):
        copied.run(support_bindings.collect, '127.0.0.1', key, hosts, output)
    assert len(calls) == 1


def test_installed_gate_cannot_be_unset_or_redirected(setup, monkeypatch):
    gate, key, hosts, output, calls = setup
    monkeypatch.setattr(owner_capture, 'INSTALLED_GATE', gate.directory)
    monkeypatch.delenv('FC_OWNER_CAPTURE_GATE')
    with gate.drain(.1):
        with pytest.raises(Busy):
            support_bindings.collect('127.0.0.1', key, hosts, output)
    monkeypatch.setenv('FC_OWNER_CAPTURE_GATE', '/tmp/unrelated-gate')
    with pytest.raises(GateError, match='OWNER_CAPTURE_CONFIGURATION_CHANGED'):
        support_bindings.collect('127.0.0.1', key, hosts, output)
    assert not calls and output.read_bytes() == b'original-projection'


def test_busy_and_killed_collector_refuse_drain(tmp_path, monkeypatch):
    gate = initialize(tmp_path / 'gate')
    monkeypatch.setenv('FC_OWNER_CAPTURE_GATE', str(gate.directory))
    code = '''import os
from provisioning.owner_capture import operation
with operation():
    print('ADMITTED', flush=True)
    os.read(0, 1)
'''
    process = subprocess.Popen([sys.executable, '-c', code],
        cwd=Path(__file__).resolve().parents[1], stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        assert select.select([process.stdout], [], [], 10)[0]
        assert process.stdout.readline().strip() == 'ADMITTED'
        with pytest.raises(Busy, match='DRAIN_TIMEOUT'):
            with gate.drain(.05):
                pytest.fail('busy collector drained')
        retained = pending(gate)
        process.kill()
        process.communicate(timeout=5)
        assert pending(gate) == retained and len(retained) == 1
        with pytest.raises(GateError, match='UNSETTLED_OPERATION'):
            with gate.drain(.1):
                pytest.fail('killed collector settled')
    finally:
        if process.poll() is None:
            process.kill()
        process.communicate(timeout=5)
