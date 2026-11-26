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


def installed_binding(gate, monkeypatch):
    application = Path(owner_capture.__file__).resolve().parents[1]
    binding = gate.directory.parent / 'installed-binding.json'
    binding.write_text(json.dumps(dict(schema=1, application=str(application), gate=str(gate.directory),
                                     pins=gate.pins), sort_keys=True, separators=(',', ':')) + '\n')
    binding.chmod(0o600)
    monkeypatch.setattr(owner_capture, 'INSTALLED_APP', application)
    monkeypatch.setattr(owner_capture, 'INSTALLED_BINDING', binding)
    monkeypatch.setattr(owner_capture, 'INSTALLED_GATE', gate.directory)
    monkeypatch.delenv('FC_OWNER_CAPTURE_GATE')
    return binding


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
    installed_binding(gate, monkeypatch)
    with gate.drain(.1):
        with pytest.raises(Busy):
            support_bindings.collect('127.0.0.1', key, hosts, output)
    monkeypatch.setenv('FC_OWNER_CAPTURE_GATE', '/tmp/unrelated-gate')
    with pytest.raises(GateError, match='OWNER_CAPTURE_CONFIGURATION_CHANGED'):
        support_bindings.collect('127.0.0.1', key, hosts, output)
    assert not calls and output.read_bytes() == b'original-projection'


@pytest.mark.parametrize('entrypoint', ['direct', 'bindings', 'notifications'])
@pytest.mark.parametrize('damage', ['missing', 'replaced', 'symlink', 'permissions', 'missing-lock',
                                   'missing-binding', 'invalid-binding', 'binding-permissions', 'binding-pins'])
def test_installed_gate_damage_refuses_without_environment_before_io(setup, monkeypatch, entrypoint, damage):
    gate, key, hosts, output, calls = setup
    binding = installed_binding(gate, monkeypatch)
    original = gate.directory
    saved = original.with_name('saved-gate')
    if damage in ('missing', 'replaced', 'symlink'):
        original.rename(saved)
        if damage == 'replaced':
            initialize(original)
        elif damage == 'symlink':
            original.symlink_to(saved, target_is_directory=True)
    elif damage == 'permissions':
        original.chmod(0o755)
    elif damage == 'missing-lock':
        (original / 'admission.lock').rename(original / 'saved-admission.lock')
    elif damage == 'missing-binding':
        binding.rename(binding.with_suffix('.saved'))
    elif damage == 'invalid-binding':
        binding.write_text('{}')
    elif damage == 'binding-permissions':
        binding.chmod(0o644)
    else:
        document = json.loads(binding.read_bytes())
        document['pins']['.'][1] += 1
        binding.write_text(json.dumps(document, sort_keys=True, separators=(',', ':')) + '\n')
    owner_capture.gate_for.cache_clear()
    monkeypatch.setattr(subscription_collector, 'command', lambda path: pytest.fail('IPC before admission'))
    monkeypatch.setattr(support_bindings.os, 'replace', lambda *args: pytest.fail('write before admission'))
    if entrypoint == 'direct':
        with pytest.raises(GateError):
            support_bindings.collect('127.0.0.1', key, hosts, output)
    else:
        arguments = ['collector', '--host', '127.0.0.1', '--key', str(key),
                     '--known-hosts', str(hosts), '--output', str(output)]
        if entrypoint == 'notifications':
            arguments.extend(['--socket', '/synthetic/unreachable'])
        monkeypatch.setattr(sys, 'argv', arguments)
        with pytest.raises(SystemExit) as refused:
            (subscription_collector if entrypoint == 'notifications' else support_bindings).main()
        assert refused.value.code == 78
    assert not calls and output.read_bytes() == b'original-projection'
    assert not list((saved if saved.exists() else original).joinpath('pending').iterdir())
    if damage == 'replaced':
        assert not list(original.joinpath('pending').iterdir())


def test_installed_binding_rechecks_cached_gate_before_nested_io(setup, monkeypatch):
    gate, key, hosts, output, calls = setup
    installed_binding(gate, monkeypatch)
    with owner_capture.operation():
        original_pending = pending(gate)
        gate.directory.rename(gate.directory.with_name('saved-gate'))
        initialize(gate.directory)
        with pytest.raises(GateError):
            support_bindings.collect('127.0.0.1', key, hosts, output)
        assert not calls and output.read_bytes() == b'original-projection'
        assert not pending(gate)
        assert original_pending


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
