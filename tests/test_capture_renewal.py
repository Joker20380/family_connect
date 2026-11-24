import hashlib
import json
import subprocess
import sys
import tarfile
from types import SimpleNamespace
import zipfile

import pytest

from control.capture_gate import Busy, Gate, GateError
from test_capture_gate import gate, pending, child, line, GUARD
from test_package_credential_renewal import source, package
from test_renewal_profile_routes import route, transport, Rejected


def test_direct_node_dispatch_is_gated_and_caught_failure_remains(gate, monkeypatch):
    import node
    calls = []
    def dispatch(native, request):
        calls.append(request)
        assert len(pending(gate)) == 1
        raise Rejected('SYNTHETIC_NATIVE_FAILURE')
    monkeypatch.setattr(node, '_dispatch', dispatch)
    with gate.drain(.2):
        with pytest.raises(Busy):
            node.dispatch(None, {}, capture_gate=gate)
    assert not calls and not pending(gate)
    with gate.operation():
        with pytest.raises(Rejected, match='SYNTHETIC_NATIVE_FAILURE'):
            node.dispatch(None, {})
    assert calls == [{}] and len(pending(gate)) == 1
    with pytest.raises(Rejected, match='CAPTURE_GATE_REQUIRED'):
        node.dispatch(None, {}, capture_gate=Gate())


@pytest.fixture
def capsule(source, tmp_path):
    archive = tmp_path / 'renewal.tar.gz'
    package.build(archive, 'HEAD', repository=source, api_ref='HEAD')
    root = tmp_path / 'capsule'
    root.mkdir(mode=0o700)
    with tarfile.open(archive) as bundle:
        bundle.extractall(root, filter='data')
    return root


def command(capsule, gate, entry='renewal', arguments=('--help',)):
    manifest_hash = hashlib.sha256((capsule / 'source-manifest.json').read_bytes()).hexdigest()
    return [sys.executable, '-I', '-B', str(capsule / 'renewal/capture_entry.py'),
            '--manifest-sha256', manifest_hash, '--capture-gate', str(gate.directory),
            '--entry', entry, '--', *arguments]


def replace_source(capsule, name, content):
    path = capsule / ('renewal/' + name)
    path.write_text(content)
    manifest_path = capsule / 'source-manifest.json'
    manifest = json.loads(manifest_path.read_bytes())
    digest = package.digest(path.read_bytes())
    manifest['source_files'][name] = digest
    manifest['source_sha256'] = package.digest(package.encode(manifest['source_files']))
    manifest['files']['renewal/' + name] = digest
    manifest_path.write_bytes(package.encode(manifest))


@pytest.mark.parametrize('entry', ['renewal', 'scheduled', 'node'])
def test_closed_native_entry_help_and_busy_before_config_or_stdin(capsule, gate, tmp_path, entry):
    invocation = command(capsule, gate, entry)
    result = subprocess.run(invocation, cwd=tmp_path, capture_output=True, timeout=10)
    assert result.returncode == 0, result.stdout + result.stderr
    assert b'--config' in result.stdout and not pending(gate)
    with gate.drain(.2):
        result = subprocess.run(command(capsule, gate, entry, arguments=()),
                                cwd=tmp_path, capture_output=True, timeout=5)
    assert result.returncode == 75 and json.loads(result.stdout)['cause'] == 'CAPTURE_BUSY'
    assert not pending(gate)
    with zipfile.ZipFile(capsule / 'api.pyz') as archive:
        assert archive.read('control/capture_gate.py') == (package.ROOT / 'control/capture_gate.py').read_bytes()


@pytest.mark.parametrize('defect', ['source', 'api', 'manifest', 'unsafe_mode', 'symlink', 'nonisolated',
                                 'online_absent', 'bytecode', 'extra_source'])
def test_pinned_capsule_refuses_before_admission(capsule, gate, tmp_path, defect):
    invocation = command(capsule, gate)
    if defect in ('source', 'api', 'manifest'):
        relative = {'source': 'renewal/production_transport.py', 'api': 'api.pyz',
                    'manifest': 'source-manifest.json'}[defect]
        with (capsule / relative).open('ab') as target:
            target.write(b'\nchanged\n')
    elif defect == 'unsafe_mode':
        (capsule / 'renewal/node.py').chmod(0o666)
    elif defect == 'symlink':
        original = capsule / 'renewal/node.py'
        moved = tmp_path / 'node.py'
        original.rename(moved)
        original.symlink_to(moved)
    elif defect == 'nonisolated':
        invocation.remove('-I')
    elif defect == 'bytecode':
        (capsule / 'renewal/__pycache__').mkdir()
    elif defect == 'extra_source':
        (capsule / 'renewal/control.py').write_text('raise RuntimeError("untracked")\n')
    else:
        invocation = command(capsule, gate, 'online')
    result = subprocess.run(invocation, cwd=tmp_path, capture_output=True, timeout=5)
    assert result.returncode == 1, result.stderr
    assert json.loads(result.stdout)['cause'] == 'CAPTURE_KIT_REFUSED'
    assert not pending(gate)


def test_missing_gate_refuses_without_initialization(capsule, gate, tmp_path):
    invocation = command(capsule, gate)
    missing = tmp_path / 'missing-gate'
    invocation[invocation.index('--capture-gate') + 1] = str(missing)
    result = subprocess.run(invocation, cwd=tmp_path, capture_output=True, timeout=5)
    assert result.returncode == 1 and not missing.exists() and not pending(gate)


@pytest.mark.parametrize('body,code,unsettled', [
    ('return None', 0, False), ('return 0', 0, False), ('raise SystemExit(0)', 0, False),
    ('return 75', 75, True), ('raise SystemExit(75)', 75, True),
    ('raise RuntimeError("private-fixture-value")', 1, True)])
def test_complete_native_lifetime_and_failure_retention(capsule, gate, tmp_path, body, code, unsettled):
    replace_source(capsule, 'renewal_cli.py',
                   'from control.capture_gate import CURRENT\n'
                   'def main():\n    assert CURRENT.get() is not None\n    ' + body + '\n')
    result = subprocess.run(command(capsule, gate), cwd=tmp_path, capture_output=True, timeout=5)
    assert result.returncode == code, result.stderr
    assert bool(pending(gate)) is unsettled
    assert b'private-fixture-value' not in result.stdout + result.stderr
    if unsettled:
        with pytest.raises(GateError, match='UNSETTLED_OPERATION'):
            with gate.drain(.2):
                pytest.fail('unsettled native result admitted capture')


def test_native_process_is_drained_and_death_keeps_uncertainty(capsule, gate, tmp_path):
    replace_source(capsule, 'renewal_cli.py',
                   'def main():\n    print("NATIVE_ADMITTED", flush=True)\n    input()\n')
    process = subprocess.Popen(command(capsule, gate), cwd=tmp_path, stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        assert line(process).strip() == 'NATIVE_ADMITTED'
        with child(GUARD, '--gate', str(gate.directory), '--drain-seconds', '.1') as guardian:
            assert json.loads(line(guardian))['status'] == 'REFUSED'
            assert guardian.wait(timeout=5) == 1
        assert process.poll() is None and len(pending(gate)) == 1
        process.kill()
        process.communicate(timeout=5)
        with pytest.raises(GateError, match='UNSETTLED_OPERATION'):
            with gate.drain(.2):
                pytest.fail('dead native writer admitted capture')
    finally:
        if process.poll() is None:
            process.kill()
        process.communicate(timeout=5)


@pytest.mark.parametrize('failure', ['timeout', 'invalid_json', 'wrong_binding', 'rejected', 'exit', 'readback'])
def test_caught_ssh_ambiguity_survives_retry(gate, route, monkeypatch, failure):
    remote = transport.SshNode('NL', 'a' * 64, forced=route)
    broken = True
    def run(command, **kwargs):
        if broken and failure == 'timeout':
            raise subprocess.TimeoutExpired(command, 120)
        request = json.loads(kwargs['input'])['request']
        response = dict(schema=1, role='NL', operation_id=request['operation_id'], action=request['action'],
                        source_sha256='a' * 64, result='PASS', payload={'completed': True})
        if broken and failure == 'wrong_binding':
            response['source_sha256'] = 'b' * 64
        if broken and failure == 'rejected':
            response.update(result='REJECTED', payload={'cause': 'SYNTHETIC_REJECTED'})
        if broken and failure == 'readback':
            raise OSError('private-fixture-value')
        kwargs['stdout'].write(b'?' if broken and failure == 'invalid_json' else transport.canonical(response))
        return SimpleNamespace(returncode=1 if broken and failure == 'exit' else 0)
    monkeypatch.setattr(transport.subprocess, 'run', run)
    with gate.operation():
        with pytest.raises((Rejected, OSError)):
            remote.call('online', 'synthetic-operation-123', dict(command='prepare'))
        broken = False
        assert remote.call('online', 'synthetic-operation-123', dict(command='prepare')) == {'completed': True}
    retained = {path.name: path.read_bytes() for path in pending(gate)}
    assert len(retained) == 1 and b'private-fixture-value' not in b''.join(retained.values())
    with gate.operation():
        assert remote.call('readback', 'synthetic-operation-123') == {'completed': True}
    assert {path.name: path.read_bytes() for path in pending(gate)} == retained


def test_successful_ssh_ack_clears_marker(gate, route, monkeypatch):
    remote = transport.SshNode('NL', 'a' * 64, forced=route)
    def run(command, **kwargs):
        request = json.loads(kwargs['input'])['request']
        response = dict(schema=1, role='NL', operation_id=request['operation_id'], action=request['action'],
                        source_sha256='a' * 64, result='PASS', payload=None)
        kwargs['stdout'].write(transport.canonical(response))
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(transport.subprocess, 'run', run)
    with gate.operation():
        assert remote.call('readback', 'synthetic-operation-123') is None
    assert not pending(gate)


def test_legacy_transport_does_not_require_or_initialize_gate(tmp_path):
    script = ('import sys;sys.path.insert(0,sys.argv[1]);import production_transport as transport;'
              'assert "control.capture_gate" not in sys.modules;'
              'remote=object.__new__(transport.SshNode);remote._call=lambda *args: "legacy";'
              'assert remote.call("inspect","synthetic-operation-123")=="legacy";'
              'assert "control.capture_gate" not in sys.modules')
    subprocess.run([sys.executable, '-I', '-B', '-c', script, str(package.ROOT / package.DIRECTORY)],
                   cwd=tmp_path, check=True, capture_output=True, timeout=5)
