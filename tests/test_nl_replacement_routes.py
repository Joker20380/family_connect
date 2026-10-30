import base64
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from control.friends import chat_sync

ROOT = Path(__file__).parents[1]


def load(name, spelling):
    spec = importlib.util.spec_from_file_location(name, ROOT / spelling)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def api(tmp_path, monkeypatch):
    module = load('replacement_http', 'deploy/friends/access-api.py')
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    return module


def catalog(host):
    payload = dict(schema=2, sequence=4, access='invite-test', gateways=[
        dict(country='ru', tcp=dict(server='185.251.89.19')),
        dict(country='nl', tcp=dict(server=host)),
    ])
    return dict(payload=base64.b64encode(json.dumps(payload).encode()).decode(), signature='fixture')


@pytest.mark.parametrize('host', ['186.246.45.246', '185.10.158.212'])
def test_registration_route_and_response_use_same_catalog(api, host):
    envelope = catalog(host)
    (api.ROOT / 'catalog.json').write_text(json.dumps(envelope))
    assert api.configuration_catalog('nl') == (envelope, host)
    assert api.configuration_catalog('ru') == (envelope, '185.251.89.19')


@pytest.mark.parametrize('host', ['127.0.0.1', '0.0.0.0', '224.0.0.1', '::1', '-oProxyCommand=bad', '185.10.158.212\n'])
def test_registration_rejects_invalid_host(api, host):
    (api.ROOT / 'catalog.json').write_text(json.dumps(catalog(host)))
    with pytest.raises(ValueError):
        api.configuration_catalog('nl')


def test_registration_rejects_duplicate_gateway(api):
    envelope = catalog('185.10.158.212')
    value = json.loads(base64.b64decode(envelope['payload']))
    value['gateways'].append(value['gateways'][-1])
    envelope['payload'] = base64.b64encode(json.dumps(value).encode()).decode()
    (api.ROOT / 'catalog.json').write_text(json.dumps(envelope))
    with pytest.raises(ValueError):
        api.configuration_catalog('nl')


def test_chat_sync_uses_configured_host_and_keeps_pinning(tmp_path, monkeypatch):
    node = dict(host='185.10.158.212', port=4243, public_key='fixture-public')
    snapshot = dict(sequence=5, expires_at=1000, public_keys=[])
    (tmp_path / 'chat-node.json').write_text(json.dumps(node))
    monkeypatch.setattr(chat_sync, 'ROOT', tmp_path)
    observed = []

    def run(command, **kwargs):
        observed.append(command)
        assert json.loads(kwargs['input']) == snapshot
        return SimpleNamespace(returncode=0, stdout=json.dumps(dict(sequence=5, expires_at=1000, **node)).encode())

    monkeypatch.setattr(chat_sync.subprocess, 'run', run)
    assert chat_sync._synchronize(SimpleNamespace(snapshot=lambda: snapshot)) == (snapshot, dict(sequence=5, expires_at=1000, **node))
    assert observed[0][-2:] == ['root@185.10.158.212', 'chat-sync']
    assert 'StrictHostKeyChecking=yes' in observed[0]


def test_mailbox_acknowledges_bootstrap_without_changing_identity():
    module = load('replacement_mailbox', 'pilot/messenger/accept_membership.py')
    settings = dict(public_key='fixture-public')
    bootstrap = dict(server='185.10.158.212', port=4243, **settings)
    value = dict(sequence=5, expires_at=1000)
    assert module.acknowledgement(value, settings, bootstrap) == dict(value, host=bootstrap['server'], port=4243, **settings)
    with pytest.raises(ValueError):
        module.acknowledgement(value, settings, dict(bootstrap, public_key='different'))


def test_monitor_uses_configured_host_and_checks_freshness(monkeypatch):
    module = load('replacement_monitor', 'deploy/server-load/monitor.py')
    observed = []
    monkeypatch.setattr(module.time, 'time', lambda: 1000)

    def run(command, **kwargs):
        observed.append(command)
        return SimpleNamespace(stdout=json.dumps(dict(country='nl', observed_at=999)))

    monkeypatch.setattr(module.subprocess, 'run', run)
    assert module.remote(dict(key='/fixture/key', known_hosts='/fixture/known', remote_host='185.10.158.212'))['country'] == 'nl'
    assert observed[0][-2:] == ['root@185.10.158.212', 'load']
    assert 'StrictHostKeyChecking=yes' in observed[0]
