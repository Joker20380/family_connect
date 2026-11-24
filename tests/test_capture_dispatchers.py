import importlib.util
import json
import subprocess
import sys
from types import SimpleNamespace
import zipfile

import pytest

from control.capture_gate import GateError, initialize
from control.friends import paid_beta_admin, paid_beta, support, transport_reconcile, transport_membership
from scripts.package_capture_dispatchers import build, DISPATCHERS
from scripts.package_support_operator import build as build_operator
from test_capture_gate import ROOT, child, line, GUARD
from test_paid_beta import registry, snapshot, event, NOW
from test_transport_membership import configure


@pytest.fixture
def gate(tmp_path):
    return initialize(tmp_path / 'capture')


@pytest.fixture
def chat(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location('friends_chat_dispatch', ROOT / 'deploy/friends/chat-sync.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    return module


def pending(gate):
    return list((gate.directory / 'pending').iterdir())


@pytest.mark.parametrize('dispatcher', DISPATCHERS)
def test_packaged_dispatcher_is_closed_reproducible_and_busy_before_read(gate, tmp_path, dispatcher):
    archive = tmp_path / 'dispatcher.pyz'
    receipt = build(archive, dispatcher)
    duplicate = tmp_path / 'repeat.pyz'
    assert build(duplicate, dispatcher)['sha256'] == receipt['sha256']
    assert receipt['deployed'] is False and receipt['capture_permitted'] is False
    with pytest.raises(FileExistsError):
        build(archive, dispatcher)
    assert 'control/capture_gate.py' in receipt['files']
    command = [sys.executable, '-I', '-B', str(archive)]
    result = subprocess.run(command + ['--help'], cwd=tmp_path, capture_output=True, timeout=10)
    assert result.returncode == 0 and b'--capture-gate' in result.stdout
    arguments = ['--capture-gate', str(gate.directory)]
    if dispatcher == 'paid-reconcile':
        arguments += ['--registry', str(tmp_path / 'missing.db'), '--commands', str(tmp_path / 'missing.json')]
    with gate.drain(1):
        result = subprocess.run(command + arguments, cwd=tmp_path, capture_output=True, timeout=5)
        assert result.returncode == 75, result.stderr
    assert not pending(gate) and not (tmp_path / 'missing.db').exists()
    arguments[1] = str(tmp_path / 'missing-gate')
    result = subprocess.run(command + arguments, cwd=tmp_path, capture_output=True, timeout=5)
    assert result.returncode == 1
    assert not (tmp_path / 'missing-gate').exists()
    with zipfile.ZipFile(archive) as package:
        assert not any(name.endswith(('.db', '.key', '.sqlite')) for name in package.namelist())
    if dispatcher == 'chat-sync':
        program = ('import sys;sys.path.insert(0,sys.argv[1]);import friends_chat_sync;'
                   'assert "/opt/apps/family_connect/friends-access/app" not in sys.path')
        subprocess.run([sys.executable, '-I', '-B', '-c', program, str(archive)],
                       cwd=tmp_path, check=True, capture_output=True, timeout=5)


def test_chat_holds_gate_through_support_publication(chat, gate, tmp_path, monkeypatch):
    (tmp_path / 'chat-support.json').write_text('{}')
    calls = []
    def access(path):
        assert len(pending(gate)) == 1
        calls.append('access')
        return object()
    def publish(*args):
        assert len(pending(gate)) == 1
        calls.append('publish')
    monkeypatch.setattr(chat, 'Access', access)
    monkeypatch.setattr(chat, 'ChatAccess', lambda access: access)
    monkeypatch.setattr(chat, 'synchronize', lambda access: ({}, {}))
    monkeypatch.setattr(support, 'publish', publish)
    assert chat.main(['--capture-gate', str(gate.directory)]) == 0
    assert calls == ['access', 'publish'] and not pending(gate)


def test_chat_publication_error_retains_uncertainty(chat, gate, tmp_path, monkeypatch):
    (tmp_path / 'chat-support.json').write_text('{}')
    monkeypatch.setattr(chat, 'synchronize', lambda access: ({}, {}))
    def fail(*args):
        raise OSError('private details')
    monkeypatch.setattr(support, 'publish', fail)
    assert chat.main(['--capture-gate', str(gate.directory)]) == 1
    with pytest.raises(GateError, match='UNSETTLED_OPERATION'):
        with gate.drain(.1):
            pytest.fail('lost partial publication')


def test_paid_cli_busy_before_connection_then_unchanged_migration(gate, registry, capsys, monkeypatch):
    before = snapshot(registry[0])
    arguments = ['--db', str(registry[0].path), '--capture-gate', str(gate.directory), 'migrate']
    original = paid_beta.connection
    def connection(*args, **kwargs):
        assert len(pending(gate)) == 1
        return original(*args, **kwargs)
    with monkeypatch.context() as scoped:
        scoped.setattr(paid_beta, 'connection', connection)
        with gate.drain(.2):
            assert paid_beta_admin.main(arguments) == 75
        assert json.loads(capsys.readouterr().out)['reason'] == 'CAPTURE_BUSY'
        assert paid_beta_admin.main(arguments) == 0
    assert snapshot(registry[0]) == before and not pending(gate)


def test_policy_is_read_only_even_when_gate_unavailable(gate, tmp_path, capsys):
    with gate.drain(.2):
        assert paid_beta_admin.main(['--capture-gate', str(tmp_path / 'missing'), 'policy']) == 0
    assert json.loads(capsys.readouterr().out)['modules']
    assert not pending(gate) and not (tmp_path / 'missing').exists()


def test_packaged_paid_operator_includes_gate_and_refuses_before_database(gate, tmp_path):
    archive = tmp_path / 'paid.pyz'
    report = build_operator(archive, operator='paid-beta')
    assert 'control/capture_gate.py' in report['files']
    command = [sys.executable, '-I', '-B', str(archive), '--db', str(tmp_path / 'missing.db'),
               '--capture-gate', str(gate.directory), 'migrate']
    with gate.drain(1):
        result = subprocess.run(command, cwd=tmp_path, capture_output=True, timeout=5)
        assert result.returncode == 75 and json.loads(result.stdout)['reason'] == 'CAPTURE_BUSY'
    assert not (tmp_path / 'missing.db').exists()


@pytest.mark.parametrize('failure', ['timeout', 'wrong-node', 'duplicate', 'boolean', 'oversize', 'list'])
def test_caught_reconcile_error_preserves_uncertainty_and_registry(gate, registry, tmp_path, monkeypatch, capsys, failure):
    before = snapshot(registry[0])
    commands = tmp_path / 'commands.json'
    commands.write_text(json.dumps({node: [node] for node in transport_reconcile.NODES}))
    commands.chmod(0o600)
    calls = []
    def run(command, **kwargs):
        node = command[0]
        assert len(pending(gate)) == 1 and kwargs['timeout'] == 12 and kwargs['check'] is True
        calls.append(node)
        reply = json.dumps(dict(schema=1, node=node, result='applied')).encode()
        if node == transport_reconcile.NODES[1]:
            if failure == 'timeout':
                raise subprocess.TimeoutExpired('private command', 12)
            if failure == 'wrong-node':reply = reply.replace(node.encode(), b'wrong')
            elif failure == 'duplicate':reply = reply.replace(b'{', b'{"schema":1,', 1)
            elif failure == 'boolean':reply = reply.replace(b'"schema": 1', b'"schema": true')
            elif failure == 'oversize':reply += b' ' * 1024
            elif failure == 'list':reply = b'[]'
        return SimpleNamespace(stdout=reply)
    monkeypatch.setattr(transport_reconcile.subprocess, 'run', run)
    arguments = ['--registry', str(registry[0].path), '--commands', str(commands), '--capture-gate', str(gate.directory)]
    assert transport_reconcile.main(arguments) == 1
    assert json.loads(capsys.readouterr().out) == dict(zip(transport_reconcile.NODES, ['applied', 'unavailable', 'applied']))
    assert calls == list(transport_reconcile.NODES) and snapshot(registry[0]) == before
    with pytest.raises(GateError, match='UNSETTLED_OPERATION'):
        with gate.drain(.1):
            pytest.fail('caught external error lost')


@pytest.mark.parametrize('failure', ['lost-ack', 'bad-ack'])
def test_payment_rollback_keeps_external_preparation_uncertainty(gate, registry, monkeypatch, failure):
    configure(registry)
    before = snapshot(registry[0])
    calls = []
    def run(command, **kwargs):
        request = json.loads(kwargs['input'])
        calls.append(command[0])
        if len(calls) == 2:
            if failure == 'lost-ack':raise subprocess.TimeoutExpired('private command', 12)
            return SimpleNamespace(stdout=b'{}')
        return SimpleNamespace(stdout=json.dumps(dict(schema=1, node=command[0],
            result='prepared', token=request['token'])).encode())
    monkeypatch.setattr(transport_membership.subprocess, 'run', run)
    monkeypatch.setattr(paid_beta_admin.time, 'time', lambda: NOW)
    arguments = ['--db', str(registry[0].path), '--capture-gate', str(gate.directory), 'activate',
                 '--support-id', registry[2], '--event-id', 'event-00000001', '--reference', 'synthetic',
                 '--period-start', '2027-01-15T08:00:00Z', '--paid-until', '2027-01-15T09:00:00Z',
                 '--apk-sha256', paid_beta.PAID_ANDROID_APK_SHA256]
    assert paid_beta_admin.main(arguments) == 2
    assert len(calls) == 2 and snapshot(registry[0]) == before
    with pytest.raises(GateError, match='UNSETTLED_OPERATION'):
        with gate.drain(.1):
            pytest.fail('lost prepared node')


def test_caught_payment_error_and_successful_retry_never_erase_old_uncertainty(gate, registry, monkeypatch):
    configure(registry)
    before = snapshot(registry[0])
    failures = [True]
    def run(command, **kwargs):
        request = json.loads(kwargs['input'])
        if failures[0] and command[0] == transport_reconcile.NODES[1]:
            raise TimeoutError('private acknowledgement details')
        return SimpleNamespace(stdout=json.dumps(dict(schema=1, node=command[0],
            result='prepared', token=request['token'])).encode())
    monkeypatch.setattr(transport_membership.subprocess, 'run', run)
    with gate.operation():
        with pytest.raises(paid_beta.PaidBetaError, match='TRANSPORT_PREPARATION_REQUIRED'):
            event(registry)
    assert snapshot(registry[0]) == before
    markers = {path.name: path.read_bytes() for path in pending(gate)}
    assert len(markers) == 1
    failures[0] = False
    with gate.operation():
        event(registry)
    assert len(snapshot(registry[0])['paid_beta_events']) == 1
    assert {path.name: path.read_bytes() for path in pending(gate)} == markers
    with pytest.raises(GateError, match='UNSETTLED_OPERATION'):
        with gate.drain(.1):
            pytest.fail('retry cannot resolve external uncertainty by itself')


def test_reconcile_dispatch_is_drained_and_killed_dispatcher_retains_marker(gate, tmp_path):
    commands = tmp_path / 'commands.json'
    commands.write_text(json.dumps({node: [node] for node in transport_reconcile.NODES}))
    commands.chmod(0o600)
    program = '''
import sys,json
from types import SimpleNamespace
from control.friends import transport_reconcile as reconcile
reconcile.snapshot = lambda *args: {}
def run(command, **kwargs):
    print('DISPATCHED',flush=True)
    sys.stdin.readline()
    return SimpleNamespace(stdout=json.dumps(dict(schema=1,node=command[0],result='applied')).encode())
reconcile.subprocess.run = run
raise SystemExit(reconcile.main(sys.argv[1:]))
'''
    arguments = ['--registry', str(tmp_path / 'unused.db'), '--commands', str(commands),
                 '--capture-gate', str(gate.directory)]
    with child(['-c', program], *arguments) as dispatcher:
        assert line(dispatcher).strip() == 'DISPATCHED'
        with child(GUARD, '--gate', gate.directory, '--drain-seconds', .05) as guardian:
            assert json.loads(line(guardian))['status'] == 'REFUSED'
            assert guardian.wait(timeout=2) == 1
        assert dispatcher.poll() is None
        dispatcher.kill()
        dispatcher.wait(timeout=2)
    with pytest.raises(GateError, match='UNSETTLED_OPERATION'):
        with gate.drain(.1):
            pytest.fail('dead dispatcher is not settled external work')
    with gate.operation():
        pass


def test_reconcile_all_acknowledgements_release_gate(gate, tmp_path, monkeypatch, capsys):
    commands = tmp_path / 'commands.json'
    commands.write_text(json.dumps({node: [node] for node in transport_reconcile.NODES}))
    commands.chmod(0o600)
    monkeypatch.setattr(transport_reconcile, 'snapshot', lambda *args: {})
    def run(command, **kwargs):
        assert len(pending(gate)) == 1
        return SimpleNamespace(stdout=json.dumps(dict(schema=1, node=command[0], result='applied')).encode())
    monkeypatch.setattr(transport_reconcile.subprocess, 'run', run)
    assert transport_reconcile.main(['--registry', str(tmp_path / 'unused.db'),
        '--commands', str(commands), '--capture-gate', str(gate.directory)]) == 0
    assert json.loads(capsys.readouterr().out) == dict.fromkeys(transport_reconcile.NODES, 'applied')
    assert not pending(gate) and not (tmp_path / 'unused.db').exists()


def test_disabled_gate_and_external_context_do_not_import_fcntl(tmp_path):
    code = '''
import importlib.abc, sys
class RefuseFcntl(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if fullname == 'fcntl':
            raise ImportError('no POSIX module')
sys.meta_path.insert(0, RefuseFcntl())
from control.capture_gate import Gate, external_operation
from control.friends import paid_beta_admin, transport_membership
with Gate().operation(), external_operation():
    pass
assert 'fcntl' not in sys.modules
'''
    subprocess.run([sys.executable, '-B', '-c', code], cwd=ROOT,
                   capture_output=True, check=True, timeout=5)
