from contextlib import ExitStack
import json
import importlib.util
import os
from pathlib import Path
import subprocess
import sys

import pytest

from control import capture_profile, capture_receiver as receiver
from scripts.build_profile_snapshot_launcher import expected_argv, render_argv
from test_capture_gate import gate, pending
from test_capture_receivers import digest, environment, invocation, launcher, write_binding


def profile_binding(tmp_path, gate, body, *, read_only=False):
    binding = write_binding(tmp_path, gate, body, kind='profile-launcher')
    entry = tmp_path / 'snapshot-launcher'
    archive = tmp_path / 'native.pyz'
    entry.write_bytes(render_argv(expected_argv(sys.executable, str(archive)), read_only=read_only))
    values = json.loads(binding.read_bytes())
    values['entry_sha256'] = digest(entry.read_bytes())
    binding.write_text(json.dumps(values))
    return binding, entry, archive


@pytest.mark.parametrize('read_only', [False, True])
def test_native_wrapper_preserves_runtime_guards_environment_and_directory(launcher, gate, tmp_path, read_only):
    body = ('import json,os,sys\n'
            'print(json.dumps(dict(cwd=os.getcwd(),uid=os.getuid(),executable=sys.executable,\n'
            'isolated=sys.flags.isolated,bytecode=sys.dont_write_bytecode,\n'
            'path=os.environ["PATH"],lang=os.environ["LANG"],command=os.environ["SSH_ORIGINAL_COMMAND"],\n'
            'sentinel="FC_CAPTURE_TEST_SENTINEL" in os.environ,request=json.load(sys.stdin))))\n')
    binding, entry, archive = profile_binding(tmp_path, gate, body, read_only=read_only)
    request = b'{"schema":1,"operation":"READ_ONLY_SECURITY_SNAPSHOT"}'
    result = subprocess.run(invocation(launcher, binding), input=request,
        env=environment('profile-launcher') | {'FC_CAPTURE_TEST_SENTINEL': 'synthetic'},
        cwd=tmp_path, capture_output=True, timeout=5)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == dict(cwd='/', uid=os.getuid(), executable=sys.executable,
        isolated=1, bytecode=True, path='/usr/bin:/bin', lang='C', command='restricted-sync',
        sentinel=False, request=json.loads(request))
    assert not pending(gate)


@pytest.mark.parametrize('payload', [b'{}', b'{"schema":true,"operation":"READ_ONLY_SECURITY_SNAPSHOT"}',
    b'{"schema":1,"schema":1,"operation":"READ_ONLY_SECURITY_SNAPSHOT"}',
    b'{"schema":1,"operation":"WRITE"}', b'x' * 20001])
def test_read_only_native_guard_is_not_bypassed(launcher, gate, tmp_path, payload):
    binding, entry, archive = profile_binding(tmp_path, gate, 'print("UNSAFE_EXECUTION")', read_only=True)
    result = subprocess.run(invocation(launcher, binding), input=payload,
        env=environment('profile-launcher'), capture_output=True, timeout=5)
    assert result.returncode == 1 and not result.stdout
    assert result.stderr == b'CAPTURE_RECEIVER_REFUSED\n' and len(pending(gate)) == 1


@pytest.mark.parametrize('fault', ['changed-body', 'duplicate-command', 'missing-readonly', 'bool-as-integer',
    'wrong-runtime', 'wrong-flags', 'wrong-archive', 'missing-archive', 'extra-archive', 'oversized'])
def test_binding_refuses_noncanonical_wrapper_or_mismatched_chain(launcher, gate, tmp_path, fault):
    binding, entry, archive = profile_binding(tmp_path, gate, 'print("UNSAFE_EXECUTION")')
    values = json.loads(binding.read_bytes())
    raw = entry.read_bytes()
    if fault == 'changed-body':
        raw += b'print("UNSAFE_EXECUTION")\n'
    elif fault == 'duplicate-command':
        raw += b'COMMAND="other"\n'
    elif fault == 'missing-readonly':
        raw = raw.replace(b'READ_ONLY = False\n', b'')
    elif fault == 'bool-as-integer':
        raw = raw.replace(b'READ_ONLY = False', b'READ_ONLY = 0')
    elif fault == 'wrong-runtime':
        raw = render_argv(expected_argv('/not-the-runtime/python3.14', str(archive)), read_only=False)
    elif fault == 'wrong-flags':
        raw = raw.replace(b' -I -B ', b' -B ')
    elif fault == 'wrong-archive':
        raw = render_argv(expected_argv(sys.executable, str(tmp_path / 'other.pyz')), read_only=False)
    elif fault == 'missing-archive':
        values['libraries'] = []
    elif fault == 'extra-archive':
        extra = tmp_path / 'extra.pyz'
        extra.write_bytes(archive.read_bytes())
        extra.chmod(0o600)
        values['libraries'].append(dict(path=str(extra), sha256=digest(extra.read_bytes())))
    else:
        raw = b' ' * 16385
    entry.write_bytes(raw)
    values['entry_sha256'] = digest(raw)
    binding.write_text(json.dumps(values))
    result = subprocess.run(invocation(launcher, binding), input=b'{}',
        env=environment('profile-launcher'), capture_output=True, timeout=5)
    assert result.returncode == 1 and not result.stdout
    assert result.stderr == b'CAPTURE_RECEIVER_REFUSED\n' and not pending(gate)


def test_sealed_wrapper_and_snapshot_survive_path_replacement(gate, tmp_path, monkeypatch, capfd):
    binding, entry, archive = profile_binding(tmp_path, gate, 'print("PINNED_SNAPSHOT")')
    monkeypatch.setenv('SSH_ORIGINAL_COMMAND', 'restricted-sync')
    with ExitStack() as stack:
        admitted, call = receiver.load(stack, binding, digest(binding.read_bytes()))
        entry.write_text('raise RuntimeError("replacement")')
        archive.write_bytes(b'not an archive')
        receiver.run(admitted, call)
    assert capfd.readouterr().out == 'PINNED_SNAPSHOT\n' and not pending(gate)


@pytest.mark.parametrize('raw', [b'', b'COMMAND = __import__("os")\nREAD_ONLY=False',
                              b'COMMAND = 123\nREAD_ONLY=False', b'not python('])
def test_wrapper_parser_never_executes_input(raw):
    with pytest.raises((ValueError, SyntaxError)):
        capture_profile.command(raw, [], sys.executable)


def test_native_stand_refuses_host_before_reading_inventory(monkeypatch):
    monkeypatch.setattr(sys, 'path', list(sys.path))
    filename = Path(__file__).parent / 'fixtures/capture_profile/native.py'
    specification = importlib.util.spec_from_file_location('profile_native_fixture', filename)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    monkeypatch.setattr(module.os, 'geteuid', lambda: 1000)
    with pytest.raises(AssertionError):
        module.main()
