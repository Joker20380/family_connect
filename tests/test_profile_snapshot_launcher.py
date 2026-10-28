import base64
import hashlib
import json
import os
from pathlib import Path
import platform
import pwd
import shlex
import shutil
import struct
import subprocess
import sys
from types import SimpleNamespace
import zipfile

import pytest

from scripts import build_profile_snapshot_launcher as launcher


@pytest.fixture
def fixture(tmp_path):
    executable = tmp_path / 'python3.14'
    shutil.copyfile(Path(sys.executable).resolve(), executable)
    executable.chmod(0o755)
    package = tmp_path / 'snapshot.pyz'
    with zipfile.ZipFile(package, 'w') as archive:
        archive.writestr('__main__.py', 'import json,sys; print(json.dumps(dict(argv=sys.argv,request=json.load(sys.stdin))))\n')
    package.chmod(0o644)
    account = launcher.Account.lookup(pwd.getpwuid(os.geteuid()).pw_name)
    config = dict(python_executable=str(executable), snapshot_package=str(package),
                  snapshot_sha256=hashlib.sha256(package.read_bytes()).hexdigest())
    calls = []
    def run(argv, **kwargs):
        calls.append((argv, kwargs))
        value = dict(executable=str(executable), version=[3, 14, 4], implementation='CPython', executable_access=True)
        return SimpleNamespace(returncode=0, stdout=json.dumps(value).encode(), stderr=b'')
    return SimpleNamespace(executable=executable, package=package, account=account, config=config,
                           calls=calls, run=run, root=tmp_path)


def build(fixture, **kwargs):
    return launcher.build(fixture.config, fixture.account, run=fixture.run, **kwargs)


def test_absolute_executable_actual_runtime_and_private_stat_pins():
    executable = str(Path(sys.executable).resolve())
    account = launcher.Account.lookup(pwd.getpwuid(os.geteuid()).pw_name)
    assert sys.version_info[:2] == (3, 14), 'Run with the accepted Python 3.14 test environment'
    result = launcher.inspect_executable(executable, account)
    assert result['runtime']['version'][:2] == [3, 14]
    assert result['runtime']['executable_access'] is True
    assert result['pin']['metadata'] == launcher.metadata(Path(executable).stat())
    assert launcher.inspect_executable(executable, account, expected_pin=result['pin']) == result


@pytest.mark.parametrize('value', [None, 314, [], {}, 'Python 3.14.4', '3.14.4', platform.python_version(),
    'Python 3.14.4\n', 'python --version', 'python3.14', './python3.14',
    '/synthetic/python 3.14', '/synthetic/python3.14\n', '/synthetic/python3.14 -I',
    '/usr/bin/env', '/usr/bin/env python3.14', '/synthetic/python3.14\x00',
    '/synthetic/python3.14;id', '/synthetic/$(python3.14)', '/synthetic/../python3.14'])
def test_reject_invalid_executable_before_invocation(fixture, value):
    fixture.config['python_executable'] = value
    with pytest.raises(launcher.LauncherError, match=launcher.INVALID):
        build(fixture)
    assert not fixture.calls


@pytest.mark.parametrize('mode', [0o644, 0o775, 0o757, 0o777, 0o4755])
def test_non_executable_or_group_world_writable_rejected(fixture, mode):
    fixture.executable.chmod(mode)
    with pytest.raises(launcher.LauncherError, match=launcher.INVALID):
        build(fixture)
    assert not fixture.calls


def test_shell_wrapper_rejected(fixture):
    fixture.executable.write_bytes(b'#!/bin/sh\nexec python3 "$@"\n')
    with pytest.raises(launcher.LauncherError, match=launcher.INVALID):
        build(fixture)


def test_directory_rejected(fixture):
    fixture.executable.unlink()
    fixture.executable.mkdir()
    with pytest.raises(launcher.LauncherError, match=launcher.INVALID):
        build(fixture)


def test_symlink_must_be_resolved_before_build(fixture):
    alias = fixture.root / 'python'
    alias.symlink_to(fixture.executable)
    fixture.config['python_executable'] = str(alias)
    with pytest.raises(launcher.LauncherError, match=launcher.INVALID):
        build(fixture)


def test_account_execute_access_required(fixture):
    fixture.executable.chmod(0o700)
    fixture.account = launcher.Account(123456, 123456, (123456,))
    with pytest.raises(launcher.LauncherError, match=launcher.INVALID):
        build(fixture)


@pytest.mark.parametrize('version', [[3, 13, 9], [2, 7, 18], [3, 15, 0], [True, 14, 4]])
def test_runtime_version_mismatch(fixture, version):
    original = fixture.run
    def wrong(argv, **kwargs):
        result = original(argv, **kwargs)
        value = json.loads(result.stdout)
        value['version'] = version
        result.stdout = json.dumps(value).encode()
        return result
    fixture.run = wrong
    with pytest.raises(launcher.LauncherError, match=launcher.VERSION):
        build(fixture)


def test_diagnostic_version_never_changes_argv(fixture):
    first, pins = build(fixture)
    fixture.config['python_version'] = 'Python 0.0.0; never executable'
    second, repeated = build(fixture)
    assert first == second and pins == repeated
    del fixture.config['python_executable']
    with pytest.raises(launcher.LauncherError, match=launcher.INVALID):
        build(fixture)


def test_extra_arguments_cannot_be_supplied(fixture):
    fixture.config['arguments'] = ['-c', 'arbitrary']
    with pytest.raises(launcher.LauncherError, match=launcher.INVALID):
        build(fixture)
    assert not fixture.calls


def test_exact_argv_round_trip_and_no_shell_invocation(fixture):
    raw, pins = build(fixture)
    expected = [str(fixture.executable), '-I', '-B', str(fixture.package)]
    assert pins['argv'] == expected
    assert shlex.split(shlex.join(expected)) == expected
    launcher.validate_launcher(raw, expected, read_only=False)
    assert b'os.execv(arguments[0], arguments)' in raw and b'subprocess' not in raw
    assert b'sh -c' not in raw and b'/bin/sh' not in raw
    for argv, kwargs in fixture.calls:
        assert argv[:4] == [str(fixture.executable), '-I', '-B', '-c']
        assert 'shell' not in kwargs and kwargs['preexec_fn'] == fixture.account.enter
    with pytest.raises(launcher.LauncherError, match=launcher.INVALID):
        launcher.render_argv(['/bin/sh', '-I', '-B', str(fixture.package)], read_only=True)


def test_exact_snapshot_package_and_launcher_tamper_rejected(fixture):
    raw, pins = build(fixture)
    other = str(fixture.root / 'other.pyz')
    with pytest.raises(launcher.LauncherError, match=launcher.ARGV):
        launcher.validate_launcher(raw.replace(str(fixture.package).encode(), other.encode()), pins['argv'], read_only=False)
    with pytest.raises(launcher.LauncherError, match=launcher.ARGV):
        launcher.validate_launcher(raw.replace(b'len(sys.argv) != 1', b'False'), pins['argv'], read_only=False)
    fixture.package.write_bytes(b'changed package')
    with pytest.raises(launcher.LauncherError, match=launcher.ARGV):
        build(fixture)


def test_pin_change_rejected_before_runtime_probe(fixture):
    _, pins = build(fixture)
    fixture.executable.chmod(0o744)
    fixture.calls.clear()
    with pytest.raises(launcher.LauncherError, match=launcher.INVALID):
        build(fixture, expected_executable_pin=pins['executable']['pin'])
    assert not fixture.calls


def public_key():
    raw = struct.pack('>I', 11) + b'ssh-ed25519' + struct.pack('>I', 32) + bytes(range(32))
    return 'ssh-ed25519 ' + base64.b64encode(raw).decode()


def test_authorized_key_round_trip_and_restrictions(fixture):
    path = str(fixture.root / 'launcher')
    raw = launcher.authorized_key_line(path, public_key())
    launcher.validate_authorized_key_line(raw, path, public_key())
    for option in launcher.OPTIONS:
        assert option.encode() in raw
    with pytest.raises(launcher.LauncherError, match=launcher.ARGV):
        launcher.validate_authorized_key_line(raw.replace(b'no-pty,', b''), path, public_key())
    with pytest.raises(launcher.LauncherError, match=launcher.ARGV):
        launcher.authorized_key_line(path, public_key() + '\n' + public_key())
    with pytest.raises(launcher.LauncherError, match=launcher.ARGV):
        launcher.authorized_key_line(path + ';id', public_key())


def invoke(fixture, payload, *, original=launcher.ORIGINAL_COMMAND, arguments=()):
    raw, _ = build(fixture, read_only=True)
    path = fixture.root / 'launcher'
    path.write_bytes(raw)
    path.chmod(0o700)
    return subprocess.run([str(path), *arguments], input=payload, capture_output=True,
                          env={'SSH_ORIGINAL_COMMAND': original}, timeout=10)


def test_actual_readonly_launcher_executes_exact_package(fixture):
    request = b'{"schema":1,"operation":"READ_ONLY_SECURITY_SNAPSHOT"}'
    before = fixture.package.read_bytes()
    result = invoke(fixture, request)
    assert result.returncode == 0 and not result.stderr
    value = json.loads(result.stdout)
    assert value == dict(argv=[str(fixture.package)], request=json.loads(request))
    assert fixture.package.read_bytes() == before


@pytest.mark.parametrize('payload', [b'{}', b'{"schema":true,"operation":"READ_ONLY_SECURITY_SNAPSHOT"}',
    b'{"schema":1,"schema":1,"operation":"READ_ONLY_SECURITY_SNAPSHOT"}',
    b'{"schema":1,"operation":"CREDENTIAL_RENEWAL_RPC","request":{}}',
    b'{"schema":1,"operation":"apply_exact_crl"}', b'x' * 20001])
def test_temporary_rehearsal_route_rejects_mutating_payload(fixture, payload):
    result = invoke(fixture, payload)
    assert result.returncode == 126 and not result.stdout and not result.stderr


@pytest.mark.parametrize('original', ['', 'id', 'restricted-sync extra', 'restricted-sync;id'])
def test_original_command_restriction_preserved(fixture, original):
    result = invoke(fixture, b'{}', original=original)
    assert result.returncode == 126 and not result.stdout and not result.stderr


def test_launcher_extra_argv_rejected(fixture):
    result = invoke(fixture, b'{}', arguments=('--configuration', 'override'))
    assert result.returncode == 126 and not result.stdout and not result.stderr


def test_actual_failure_regression_version_is_not_a_command(fixture):
    with pytest.raises(FileNotFoundError):
        subprocess.run(['3.14.4', '-I', '-B', str(fixture.package)], check=True, env={'PATH': str(fixture.root)})
    fixture.config['python_executable'] = '3.14.4'
    with pytest.raises(launcher.LauncherError, match=launcher.INVALID):
        build(fixture)
    assert not fixture.calls
