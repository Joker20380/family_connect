import fcntl
import importlib.util
import json
import os
from pathlib import Path
import sys

import pytest

import backend

LINUX = Path(__file__).resolve().parents[2] / 'linux'
sys.path.insert(0, str(LINUX))
import system_runtime


@pytest.mark.parametrize('changes', [dict(action='down'), dict(action='serve'), dict(ident='1000'),
    dict(ident='family-connect-mesh@1000.service'), dict(data='endpoint'), dict(uid=1000), dict(kind='chat-direct')])
def test_chat_setup_cannot_expand_privilege(changes):
    request = dict(kind='chat', action='up', ident='fcchat0', data=None)
    request.update(changes)
    with pytest.raises(ValueError):
        backend._session_request(request)


def test_chat_setup_uses_only_existing_authorization_owner(monkeypatch):
    assert backend._session_request(dict(kind='chat', action='up', ident='fcchat0', data=None)) == (
        [backend._SESSION_HELPERS['mesh'], 'chat-up', 'fcchat0'], None)
    monkeypatch.setattr(backend, 'system_component_status', lambda: 'RUNTIME_CONTRACT_MISMATCH')
    monkeypatch.setattr(backend, 'authorization_operation', lambda: pytest.fail('No prompt for incompatible host'))
    with pytest.raises(backend.BackendError, match='RUNTIME_CONTRACT_MISMATCH'):
        backend.prepare_chat_services()


def test_root_setup_derives_uid_and_never_calls_vpn(monkeypatch):
    import pwd
    spec = importlib.util.spec_from_file_location('chat_setup_test', LINUX / 'mesh-helper.py')
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    monkeypatch.setattr(sys, 'argv', ['helper', 'chat-up', 'fcchat0'])
    monkeypatch.setattr(os, 'geteuid', lambda: 0)
    monkeypatch.setenv('PKEXEC_UID', '1234')
    monkeypatch.setattr(pwd, 'getpwuid', lambda uid: uid == 1234 or pytest.fail('Wrong UID'))
    monkeypatch.setattr(backend, 'system_component_status', lambda: 'READY')
    commands = []
    monkeypatch.setattr(helper, 'command', lambda *args: commands.append(args))
    helper.main()
    assert commands == [('systemctl', 'start', 'family-connect-chat-direct@1234.service'),
                        ('systemctl', 'start', 'family-connect-chat-mesh@1234.service')]


def test_runtime_paths_exclude_checkout_pythonpath_and_sites(tmp_path, monkeypatch):
    system_runtime.sysconfig.get_path('stdlib')
    (tmp_path / 'python-runtime.json').write_text(json.dumps(dict(python=list(sys.version_info[:2]))))
    monkeypatch.setattr(sys, 'path', ['checkout', 'user-site', 'dev-venv'])
    monkeypatch.setenv('PYTHONPATH', '/unsafe')
    system_runtime.configure(tmp_path)
    assert sys.path[:2] == [str(tmp_path), str(tmp_path / 'vendor')]
    assert not {'checkout', 'user-site', 'dev-venv', '/unsafe'} & set(sys.path)


@pytest.mark.skipif(os.geteuid() != 0, reason='Real root-owned flock, isolated test runner only')
def test_shared_start_gate_cannot_enter_install_transaction(tmp_path, monkeypatch):
    path = tmp_path / 'install.lock'
    monkeypatch.setattr(system_runtime, 'LOCK', str(path))
    descriptor = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError):
            system_runtime.shared_gate()
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        service = system_runtime.shared_gate()
        try:
            with pytest.raises(BlockingIOError):
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        finally:
            os.close(service)
    finally:
        os.close(descriptor)
