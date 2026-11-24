from contextlib import ExitStack
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import zipfile

import pytest

from control import capture_receiver as receiver
from control.capture_gate import Busy, GateError
from scripts.package_capture_receivers import build
from test_capture_gate import gate, pending, line


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def write_binding(root, gate, body, *, kind='awg-register', libraries=()):
    entry = root / 'native.py'
    if kind == 'profile-snapshot':
        entry = root / 'native.pyz'
        with zipfile.ZipFile(entry, 'w') as bundle:
            bundle.writestr('__main__.py', body)
    else:
        entry.write_text(body)
    entry.chmod(0o600)
    value = dict(schema=1, kind=kind, capture_gate=str(gate.directory), entry_path=str(entry),
                 entry_sha256=digest(entry.read_bytes()), libraries=list(libraries))
    path = root / 'binding.json'
    path.write_text(json.dumps(value))
    path.chmod(0o600)
    return path


def invocation(launcher, binding):
    return [sys.executable, '-I', '-B', str(launcher), '--binding', str(binding),
            '--binding-sha256', digest(binding.read_bytes())]


def environment(kind='awg-register'):
    result = {name: value for name, value in os.environ.items()
              if not name.startswith(('SSH_', 'PYTHON'))}
    result['SSH_ORIGINAL_COMMAND'] = receiver.ENTRIES[kind][0]
    return result


@pytest.fixture
def launcher(tmp_path):
    path = tmp_path / 'receiver.pyz'
    report = build(path)
    assert report['deployed'] is False and report['capture_permitted'] is False
    return path


def test_closed_deterministic_archive(launcher, tmp_path):
    other = tmp_path / 'other.pyz'
    build(other)
    assert launcher.read_bytes() == other.read_bytes()
    with zipfile.ZipFile(launcher) as bundle:
        assert set(bundle.namelist()) == {'control/', 'control/capture_gate.py',
                                         'control/capture_receiver.py', '__main__.py'}
    with pytest.raises(FileExistsError):
        build(launcher)


@pytest.mark.parametrize('kind', receiver.ENTRIES)
def test_fixed_native_arguments_and_busy_before_import_or_input(launcher, gate, tmp_path, kind):
    expected = list(receiver.ENTRIES[kind][2])
    body = ('import sys\nfrom pathlib import Path\n'
            f'assert sys.argv[1:] == {expected!r}\n'
            f'assert len(list(Path({str(gate.directory / "pending")!r}).iterdir())) == 1\n'
            'print("ACK:" + sys.stdin.readline().strip())\n')
    binding = write_binding(tmp_path, gate, body, kind=kind)
    with gate.drain(.2):
        result = subprocess.run(invocation(launcher, binding), input=b'not consumed', env=environment(kind),
                                capture_output=True, timeout=5)
    assert result.returncode == 75 and result.stdout == b'' and result.stderr == b'CAPTURE_BUSY\n'
    assert not pending(gate)
    result = subprocess.run(invocation(launcher, binding), input=b'synthetic\n', env=environment(kind),
                            capture_output=True, timeout=5)
    assert result.returncode == 0 and result.stdout == b'ACK:synthetic\n', result.stderr
    assert not pending(gate)


@pytest.mark.parametrize('kind', receiver.ENTRIES)
def test_ssh_original_command_is_exact_not_shell_parsed(launcher, gate, tmp_path, kind):
    binding = write_binding(tmp_path, gate, 'raise RuntimeError("must not run")', kind=kind)
    for command in ('', receiver.ENTRIES[kind][0] + ' extra', 'register; true'):
        env = environment(kind) | {'SSH_ORIGINAL_COMMAND': command}
        result = subprocess.run(invocation(launcher, binding), env=env, capture_output=True, timeout=5)
        assert result.returncode == 1 and result.stdout == b'' and not pending(gate)


def test_only_awg_has_local_dispatch_without_ssh(launcher, gate, tmp_path):
    env = environment()
    del env['SSH_ORIGINAL_COMMAND']
    binding = write_binding(tmp_path, gate, 'print("LOCAL")')
    result = subprocess.run(invocation(launcher, binding), env=env, capture_output=True, timeout=5)
    assert result.returncode == 0 and result.stdout == b'LOCAL\n'
    result = subprocess.run(invocation(launcher, binding), env=env | {'SSH_CONNECTION': 'synthetic'},
                            capture_output=True, timeout=5)
    assert result.returncode == 1 and not pending(gate)
    binding = write_binding(tmp_path, gate, 'print("must not run")', kind='mailbox-membership')
    result = subprocess.run(invocation(launcher, binding), env=env, capture_output=True, timeout=5)
    assert result.returncode == 1 and result.stdout == b'' and not pending(gate)


@pytest.mark.parametrize('fault', ['binding-pin', 'entry-pin', 'binding-mode', 'entry-mode', 'hardlink',
                                  'symlink', 'missing-gate', 'extra-field', 'duplicate-field', 'library'])
def test_binding_refusal_does_not_enter_native(launcher, gate, tmp_path, fault):
    binding = write_binding(tmp_path, gate, 'print("must not run")')
    command = invocation(launcher, binding)
    entry = tmp_path / 'native.py'
    if fault == 'binding-pin':
        command[-1] = '0' * 64
    elif fault == 'entry-pin':
        entry.write_text('print("changed")')
    elif fault == 'binding-mode':
        binding.chmod(0o644)
    elif fault == 'entry-mode':
        entry.chmod(0o666)
    elif fault == 'hardlink':
        os.link(entry, tmp_path / 'other')
    elif fault == 'symlink':
        entry.rename(tmp_path / 'real')
        entry.symlink_to(tmp_path / 'real')
    else:
        value = json.loads(binding.read_bytes())
        if fault == 'missing-gate':
            value['capture_gate'] = str(tmp_path / 'absent')
        elif fault == 'extra-field':
            value['arguments'] = ['run']
        elif fault == 'library':
            value['libraries'] = [dict(path=str(entry), sha256=value['entry_sha256'])]
        binding.write_text(json.dumps(value))
        if fault == 'duplicate-field':
            binding.write_text(binding.read_text().replace('"schema": 1', '"schema": 1, "schema": 1'))
        command = invocation(launcher, binding)
    result = subprocess.run(command, env=environment(), capture_output=True, timeout=5)
    assert result.returncode == 1 and result.stdout == b''
    assert result.stderr == b'CAPTURE_RECEIVER_REFUSED\n' and not pending(gate)
    assert not (tmp_path / 'absent').exists()


@pytest.mark.parametrize('body', ['raise SystemExit(1)', 'raise SystemExit(75)',
                                  'import os, signal; os.kill(os.getpid(), signal.SIGKILL)'])
def test_native_failure_retains_marker_even_after_success(launcher, gate, tmp_path, body):
    binding = write_binding(tmp_path, gate, body)
    result = subprocess.run(invocation(launcher, binding), env=environment(), capture_output=True, timeout=5)
    assert result.returncode == 1 and len(pending(gate)) == 1
    retained = pending(gate)
    binding = write_binding(tmp_path, gate, 'print("OK")')
    result = subprocess.run(invocation(launcher, binding), env=environment(), capture_output=True, timeout=5)
    assert result.returncode == 0 and pending(gate) == retained
    with pytest.raises(GateError, match='UNSETTLED_OPERATION'):
        with gate.drain(.2):
            pytest.fail('failed receiver admitted capture')


def test_sealed_entry_and_library_are_used_after_originals_change(gate, tmp_path, monkeypatch, capfd):
    library = tmp_path / 'library.pyz'
    with zipfile.ZipFile(library, 'w') as bundle:
        bundle.writestr('capture_probe.py', 'VALUE = "PINNED"')
    library.chmod(0o600)
    binding = write_binding(tmp_path, gate, 'from capture_probe import VALUE\nprint(VALUE)\n',
                            libraries=[dict(path=str(library), sha256=digest(library.read_bytes()))])
    monkeypatch.setenv('SSH_ORIGINAL_COMMAND', 'register')
    with ExitStack() as stack:
        admitted, call = receiver.load(stack, binding, digest(binding.read_bytes()))
        (tmp_path / 'native.py').write_text('raise RuntimeError("changed")')
        library.write_bytes(b'changed')
        with pytest.raises(OSError):
            os.write(call[0], b'changed')
        receiver.run(admitted, call)
    assert capfd.readouterr().out == 'PINNED\n' and not pending(gate)


def test_ack_does_not_settle_before_native_process_exit(launcher, gate, tmp_path):
    binding = write_binding(tmp_path, gate, 'print("ACK", flush=True)\ninput()\n')
    process = subprocess.Popen(invocation(launcher, binding), env=environment(), stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        assert line(process).strip() == 'ACK'
        with pytest.raises(Busy, match='DRAIN_TIMEOUT'):
            with gate.drain(.1):
                pytest.fail('ACK preceded native completion')
        assert process.communicate(input='finish\n', timeout=5) == ('', '')
        assert process.returncode == 0 and not pending(gate)
    finally:
        if process.poll() is None:
            process.kill()
        process.communicate(timeout=5)


def test_broken_reply_pipe_keeps_pending(launcher, gate, tmp_path):
    binding = write_binding(tmp_path, gate, 'print("READY", flush=True)\ninput()\nprint("ACK", flush=True)\n')
    process = subprocess.Popen(invocation(launcher, binding), env=environment(), stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    try:
        assert line(process).strip() == 'READY'
        process.stdout.close()
        process.stdin.write('finish\n')
        process.stdin.flush()
        assert process.wait(timeout=5) == 1
        assert len(pending(gate)) == 1
    finally:
        if process.poll() is None:
            process.kill()
        process.wait(timeout=5)
        process.stdin.close()


def test_parent_death_does_not_imply_native_cancellation(launcher, gate, tmp_path):
    binding = write_binding(tmp_path, gate,
        'import os, sys\nprint("CHILD", os.getpid(), flush=True)\ninput()\nprint("NATIVE_FINISHED", flush=True)\n')
    process = subprocess.Popen(invocation(launcher, binding), env=environment(), stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
    try:
        assert line(process).startswith('CHILD ')
        with pytest.raises(Busy, match='DRAIN_TIMEOUT'):
            with gate.drain(.1):
                pytest.fail('in-flight native child admitted capture')
        process.kill()
        process.wait(timeout=5)
        assert len(pending(gate)) == 1
        process.stdin.write('finish\n')
        process.stdin.flush()
        assert line(process).strip() == 'NATIVE_FINISHED'
        with pytest.raises(GateError, match='UNSETTLED_OPERATION'):
            with gate.drain(.2):
                pytest.fail('late child success erased parent uncertainty')
    finally:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.communicate(timeout=5)
