"""Persisted invited TCP users remain readable after a service restart."""
import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace


def test_tcp_registration_preserves_service_read_access(tmp_path, monkeypatch):
    source = Path(__file__).parents[1] / 'deploy/friends/awg-gateway.py'
    spec = importlib.util.spec_from_file_location('friends_gateway', source)
    gateway = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gateway)
    monkeypatch.setattr(gateway, 'ROOT', tmp_path / 'friends-awg')
    tcp = tmp_path / 'friends-tcp'
    tcp.mkdir()
    config = tcp / 'server.json'
    config.write_text(json.dumps({'inbounds': [{'tag': 'friends', 'port': 8446,
                                              'settings': {'clients': []}}]}))
    config.chmod(0o640)
    device = 'a' * 32
    ident = '11111111-1111-4111-8111-111111111111'
    monkeypatch.setattr(gateway, 'command', lambda *args: 0)
    monkeypatch.setattr(gateway.subprocess, 'run', lambda *args, **kwargs:
                        SimpleNamespace(returncode=0, stdout=ident + device + '@family.test'))
    prior = os.umask(0o077)
    try:
        gateway.tcp_user(device, ident)
        gateway.tcp_user(device, ident)
    finally:
        os.umask(prior)
    assert config.stat().st_mode & 0o777 == 0o640
    users = json.loads(config.read_text())['inbounds'][0]['settings']['clients']
    assert len(users) == 1 and users[0]['id'] == ident
    assert not (tcp / 'user-request.json').exists()
