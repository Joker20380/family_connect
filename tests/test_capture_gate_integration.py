import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import threading
import time
from types import SimpleNamespace

import pytest

from control.capture_gate import GateError, initialize
from control.friends import chat_sync, diagnostics, technical_metadata
from control.product.gateway_adapter import DockerGateway
from test_friends_http_runtime import runtime, running, request
from test_peer_worker import worker
from test_gateway_adapter import adapter, apply

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def gate(tmp_path):
    return initialize(tmp_path / 'capture')


def test_packaged_http_refuses_before_proof_or_database_write_and_recovers(runtime, gate):
    runtime['command'] += ['--capture-gate', str(gate.directory)]
    device = runtime['canary']
    body = dict(public_identity=device.public_identity, wireguard_public_key=device.wireguard_public_key,
                purpose='status', invitation='')
    with running(runtime):
        with runtime['access'].db() as database:
            before = list(database.execute('SELECT * FROM challenges'))
        with gate.drain(.5):
            status, raw = request(runtime['backend'], '/friends/challenge', body=body)
            assert status == 503 and json.loads(raw)['error'] == 'capture-busy'
            with runtime['access'].db() as database:
                assert list(database.execute('SELECT * FROM challenges')) == before
        assert request(runtime['backend'], '/friends/challenge', body=body)[0] == 200


def test_packaged_http_invalid_gate_exits_instead_of_silently_disabling(runtime, tmp_path):
    result = subprocess.run(runtime['command'] + ['--capture-gate', str(tmp_path / 'missing')],
        cwd=runtime['temporary'], env=runtime['environment'], capture_output=True, timeout=5)
    assert result.returncode != 0
    assert not (tmp_path / 'missing').exists()


def test_http_wrapper_holds_gate_for_whole_admitted_request_and_keeps_external_ambiguity(gate, monkeypatch):
    spec = importlib.util.spec_from_file_location('capture_http_test', ROOT / 'deploy/friends/access-api.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, 'capture_gate', gate)
    replies = []
    def body():
        assert len(list((gate.directory / 'pending').iterdir())) == 1
        try:
            with module.external_operation():
                raise subprocess.TimeoutExpired('private-command', 1)
        except subprocess.TimeoutExpired:
            replies.append((503, 'handled'))
    handler = SimpleNamespace(admitted_post=body, reply=lambda *args: replies.append(args),
                              connection=SimpleNamespace(settimeout=lambda timeout: None),
                              path='/friends/challenge')
    module.Handler.do_POST(handler)
    assert replies == [(503, 'handled')]
    with pytest.raises(GateError, match='UNSETTLED_OPERATION'):
        with gate.drain(.1):
            pytest.fail('lost external command')


@pytest.mark.parametrize('path,status,available', [('/invalid', 404, True), ('/friends/challenge', 429, False)])
def test_http_rejects_invalid_or_overload_before_gate(gate, monkeypatch, path, status, available):
    spec = importlib.util.spec_from_file_location('capture_http_limit', ROOT / 'deploy/friends/access-api.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, 'capture_gate', gate)
    monkeypatch.setattr(module, 'slots', threading.BoundedSemaphore(1 if available else 0))
    replies = []
    handler = SimpleNamespace(admitted_post=lambda: pytest.fail('request admitted'), path=path,
                              connection=SimpleNamespace(settimeout=lambda timeout: None),
                              reply=lambda *args: replies.append(args))
    with gate.drain(.2):
        module.Handler.do_POST(handler)
    assert len(replies) == 1 and replies[0][0] == status
    assert not list((gate.directory / 'pending').iterdir())


@pytest.mark.parametrize('module', [diagnostics, technical_metadata])
def test_retention_obeys_gate_without_killing_thread(module, gate, monkeypatch, tmp_path):
    calls, threads = [], []
    original = threading.Thread
    def launch(*args, **kwargs):
        instance = original(*args, **kwargs)
        threads.append(instance)
        return instance
    monkeypatch.setattr(module.threading, 'Thread', launch)
    monkeypatch.setattr(module, 'prune', lambda *args: calls.append(args))
    with gate.drain(.2):
        stopped = module.start_retention(tmp_path / 'store', capture_gate=gate)
        time.sleep(.02)
        stopped.set()
        threads[-1].join(1)
        assert not calls and not threads[-1].is_alive()
    stopped = module.start_retention(tmp_path / 'store', capture_gate=gate)
    deadline = time.monotonic() + 1
    while not calls:
        assert time.monotonic() < deadline
        time.sleep(.005)
    stopped.set()
    threads[-1].join(1)
    assert len(calls) == 1 and not threads[-1].is_alive()


def test_product_cli_busy_does_not_create_database_then_migrates(gate, tmp_path):
    database = tmp_path / 'product.db'
    command = [sys.executable, '-m', 'control.product.admin', '--database', str(database),
               '--capture-gate', str(gate.directory), 'migrate']
    with gate.drain(.5):
        result = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=5)
        assert result.returncode == 75 and json.loads(result.stdout)['result'] == 'CAPTURE_BUSY'
        assert not database.exists()
    result = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=5)
    assert result.returncode == 0, result.stderr
    assert database.exists() and not list((gate.directory / 'pending').iterdir())


def test_worker_forwards_gate_to_child_before_reconcile(monkeypatch, tmp_path):
    commands = []
    monkeypatch.setattr(sys, 'argv', ['worker', '--database', 'database', '--gateways', 'gateways',
                                     '--capture-gate', str(tmp_path)])
    monkeypatch.setattr(worker.signal, 'signal', lambda *args: None)
    monkeypatch.setattr(worker, 'run_loop', lambda command, stop: commands.append(command))
    worker.main()
    assert commands == [[sys.executable, '-m', 'control.product.admin', '--database', 'database',
                         '--capture-gate', str(tmp_path), 'reconcile-peers', '--gateways', 'gateways']]


def test_docker_timeout_caught_by_reconciler_still_refuses_drain(gate, tmp_path):
    def run(*args, **kwargs):
        raise subprocess.TimeoutExpired('private-command', 3)
    adapter = DockerGateway(container='family-connect-test', keys=tmp_path, run=run)
    with gate.operation():
        with pytest.raises(subprocess.TimeoutExpired):
            adapter._command('not-executed')
    with pytest.raises(GateError, match='UNSETTLED_OPERATION'):
        with gate.drain(.1):
            pytest.fail('timed-out Docker command lost')


def test_docker_success_with_failed_readback_keeps_uncertainty(gate, adapter, monkeypatch):
    driver, state, device, gateway = adapter
    original = driver._command
    def command(*args):
        if args == ('wg', 'show', 'wg0', 'allowed-ips') and state['peers']:
            return ''
        return original(*args)
    monkeypatch.setattr(driver, '_command', command)
    with gate.operation():
        with pytest.raises(RuntimeError, match='verification failed'):
            apply(adapter)
    assert device.wireguard_public_key in state['peers']
    with pytest.raises(GateError, match='UNSETTLED_OPERATION'):
        with gate.drain(.1):
            pytest.fail('unverified external work lost')


def test_chat_timeout_retains_uncertainty_without_dispatch(gate, tmp_path, monkeypatch):
    monkeypatch.setattr(chat_sync, 'ROOT', tmp_path)
    def synchronize(registry):
        raise subprocess.TimeoutExpired('private-ssh', 10)
    monkeypatch.setattr(chat_sync, '_synchronize', synchronize)
    with gate.operation():
        with pytest.raises(subprocess.TimeoutExpired):
            chat_sync.synchronize(None)
    with pytest.raises(GateError, match='UNSETTLED_OPERATION'):
        with gate.drain(.1):
            pytest.fail('timed-out SSH command lost')
