import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from test_activated_maintenance import MAINTENANCE, Rejected
import production_transport as transport
import renewal_health
import scheduled_evaluate


@pytest.fixture
def route(tmp_path):
    key, hosts = tmp_path / 'synthetic-key', tmp_path / 'synthetic-hosts'
    for path in (key, hosts):
        path.write_bytes(b'synthetic transport fixture')
        path.chmod(0o600)
    return dict(key=str(key), known_hosts=str(hosts), target='synthetic_reader@gateway.invalid')


@pytest.mark.parametrize('forced', [True, False])
def test_renewal_fixed_route_and_exact_rpc_binding(route, monkeypatch, forced):
    seen = []
    if not forced:
        route['command'] = ['/synthetic/python', '-E', '-s', '-B', '/synthetic/node.py', '--config', '/synthetic/fixed.json']
    def run(command, **kwargs):
        seen.append((command, kwargs))
        message = json.loads(kwargs['input'])
        request = message['request'] if forced else message
        response = dict(schema=1, role='NL', operation_id=request['operation_id'], action=request['action'],
                        source_sha256=request['expected_source_sha256'], result='PASS', payload={'result': 'SYNTHETIC'})
        kwargs['stdout'].write(transport.canonical(response))
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(transport.subprocess, 'run', run)
    monkeypatch.setenv('SSH_ORIGINAL_COMMAND', 'override-target')
    node = transport.SshNode('NL', 'a' * 64, **({'forced': route} if forced else {'route': route}))
    assert node.call('inspect', 'synthetic-operation-123') == {'result': 'SYNTHETIC'}
    command, kwargs = seen[0]
    assert command[-2] == route['target'] and command[:3] == ['/usr/bin/ssh', '-F', '/dev/null']
    assert 'IdentitiesOnly=yes' in command and 'StrictHostKeyChecking=yes' in command
    assert kwargs['env'] == {'PATH': '/usr/bin:/bin', 'LANG': 'C'}
    if forced:
        assert command[-1] == 'restricted-sync'
        assert set(json.loads(kwargs['input'])) == {'schema', 'operation', 'request'}
    else:
        assert command[-1] == '/synthetic/python -E -s -B /synthetic/node.py --config /synthetic/fixed.json'
    route['target'] = 'other@gateway.invalid'
    assert node.route['target'] == 'synthetic_reader@gateway.invalid'


@pytest.mark.parametrize('defect', ['missing', 'extra', 'target_option', 'target_shell', 'relative_key', 'symlink', 'command'])
def test_renewal_route_rejects_unpinned_or_unsafe_inputs(route, defect):
    if defect == 'missing':
        del route['target']
    elif defect == 'extra':
        route['action'] = 'reconcile_current_floor'
    elif defect == 'target_option':
        route['target'] = '-oProxyCommand=bad'
    elif defect == 'target_shell':
        route['target'] = 'synthetic@gateway.invalid;false'
    elif defect == 'relative_key':
        route['key'] = 'relative'
    elif defect == 'symlink':
        path = Path(route['key'])
        path.rename(path.with_suffix('.before'))
        path.symlink_to(path.with_suffix('.before'))
    elif defect == 'command':
        route['command'] = ['sh', '-c', 'unexpected']
    with pytest.raises(Rejected, match='SSH_CONFIG'):
        transport.SshNode('NL', 'a' * 64, forced=route)


def test_renewal_requires_fixed_transport_no_historical_default():
    with pytest.raises(Rejected, match='SSH_CONFIG'):
        transport.SshNode('NL', 'a' * 64)


@pytest.mark.parametrize('role', ['RU', 'NL'])
def test_fixed_systemd_units_preserve_quiesce_and_resume_semantics(tmp_path, monkeypatch, role):
    units = ['synthetic-api.service', 'synthetic-old.timer', 'synthetic-old.service',
             'synthetic-directory.timer', 'synthetic-directory.service'] if role == 'RU' else ['synthetic-gateway.service']
    states = {unit: 'active' for unit in units}
    calls = []
    def run(command, **kwargs):
        action, unit = command[1:3]
        assert unit in units
        if action == 'show':
            active = states[unit]
            return SimpleNamespace(returncode=0, stdout=(f'ActiveState={active}\nSubState=running\nMainPID={1 if active == "active" else 0}\n').encode())
        assert action in ('stop', 'start')
        calls.append((action, unit))
        states[unit] = 'inactive' if action == 'stop' else 'active'
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(transport.subprocess, 'run', run)
    root = tmp_path / 'state'
    root.mkdir(mode=0o700)
    barrier = transport.SystemdBarrier(role, root, units=units)
    barrier.quiesce()
    assert barrier.stopped() and calls == [('stop', unit) for unit in units]
    barrier.resume(commit_decided=True, equality_verified=True)
    expected = [units[0], units[3]] if role == 'RU' else units
    assert calls[len(units):] == [('start', unit) for unit in expected]
    barrier.resume(commit_decided=True, equality_verified=True)
    assert calls[len(units):] == [('start', unit) for unit in expected]
    with pytest.raises(Rejected, match='SYSTEMD_ACTION_FORBIDDEN'):
        barrier.invoke('restart', units[0])
    with pytest.raises(Rejected, match='UNIT_NOT_ALLOWLISTED'):
        barrier.state('unrelated.service')


@pytest.mark.parametrize('units', [None, [], ['bad.timer'], ['bad.service', 'extra.service'], ['-bad.service']])
def test_fixed_unit_schema_is_not_an_unrestricted_service_api(tmp_path, units):
    with pytest.raises(Rejected, match='UNIT_CONFIG'):
        transport.SystemdBarrier('NL', tmp_path, units=units)


def test_scheduled_snapshot_uses_fixed_target_and_readonly_envelope(route, monkeypatch):
    seen = []
    def run(command, **kwargs):
        seen.append((command, json.loads(kwargs['input'])))
        kwargs['stdout'].write(transport.canonical(dict(schema=1, profile={}, directory='synthetic')))
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(scheduled_evaluate.subprocess, 'run', run)
    scheduled_evaluate.read_gateway(Path(route['key']), Path(route['known_hosts']), route['target'])
    command, payload = seen[0]
    assert command[-2:] == [route['target'], 'restricted-sync']
    assert payload == dict(schema=1, operation='READ_ONLY_SECURITY_SNAPSHOT')


def test_health_monitor_uses_fixed_unit_and_systemd_escape(monkeypatch):
    seen = []
    def run(command, **kwargs):
        seen.append(command)
        raw = b'ActiveState=active\nLastTriggerUSecMonotonic=0\n' if command[0].endswith('systemctl') else b't 12345\n'
        return SimpleNamespace(returncode=0, stdout=raw)
    monkeypatch.setattr(renewal_health.subprocess, 'run', run)
    value = renewal_health.read('synthetic-renewal_a.timer', ('ActiveState', 'LastTriggerUSecMonotonic'))
    assert value == dict(ActiveState='active', LastTriggerUSecMonotonic='12345')
    assert seen[1][4] == '/org/freedesktop/systemd1/unit/synthetic_2drenewal_5fa_2etimer'
    with pytest.raises(Rejected, match='HEALTH_UNIT'):
        renewal_health.read('bad;command.timer', ('ActiveState',))


def test_renewal_generic_sources_do_not_embed_operational_routes():
    import re
    for path in MAINTENANCE.glob('*.py'):
        raw = path.read_bytes()
        assert not re.search(rb'\b(?:\d{1,3}\.){3}\d{1,3}\b|/opt/apps/[a-z]|[a-z_][a-z0-9_-]+@[a-z0-9][a-z0-9.-]+', raw), path.name
