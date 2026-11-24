import copy
import json
from types import SimpleNamespace

import pytest

from scripts import control_ha_owner_admission_preflight as preflight


def container(name, uid=10001, gate='/run/capture', mounts=None):
    return dict(Name='/' + name, Id=('1' if name == preflight.NAMES[0] else '2') * 64,
                Image='sha256:' + '3' * 64, RestartCount=0,
                State=dict(Running=True, Paused=False, Restarting=False, Pid=123, StartedAt='2026-11-24T00:00:00Z'),
                Config=dict(User=str(uid), Entrypoint=['/private/entry'], Cmd=['--secret=command-value'],
                            Env=['PASSWORD=private-secret'] + ([] if gate is None else [preflight.GATE + '=' + gate]),
                            Labels={'com.docker.compose.project': 'fc-control-plane-0',
                                    'com.docker.compose.service': name[len('fc-control-plane-0-'):-2]}),
                HostConfig=dict(ReadonlyRootfs=True, UsernsMode=''),
                Mounts=mounts if mounts is not None else [dict(Type='bind', Source='/private/host-capture',
                                                             Destination='/run/capture', RW=True)])


def top(uid=10001):
    return dict(Titles=['UID', 'GID', 'PID', 'PPID'], Processes=[[str(uid), str(uid), '123', '1']])


@pytest.fixture
def installed(monkeypatch):
    items = {name: container(name) for name in preflight.NAMES}
    samples = {name: top() for name in preflight.NAMES}
    calls = []

    def read(endpoint):
        calls.append(endpoint)
        for name, item in items.items():
            if endpoint == '/containers/' + name + '/json':
                return copy.deepcopy(item)
            if endpoint == '/containers/' + item['Id'] + '/' + preflight.TOP:
                return copy.deepcopy(samples[name])
        pytest.fail('Unexpected Docker endpoint')

    monkeypatch.setattr(preflight, 'read', read)
    return items, samples, calls


def test_same_bindings_never_authorize_capture(installed):
    result = preflight.collect()
    assert result['binding_observations_equal'] is True
    for field in ('capture_permitted', 'all_writers_qualified', 'services_changed', 'commands_executed_in_containers'):
        assert result[field] is False
    assert 'GATE_INODES_NOT_ATTESTED' in result['unresolved']
    assert len(installed[2]) == 6
    for sensitive in ('private-secret', 'command-value', '/private/entry', '/private/host-capture', '/run/capture'):
        assert sensitive not in json.dumps(result)


def test_runtime_identity_not_configured_username(installed):
    items, samples, calls = installed
    items[preflight.NAMES[1]]['Config']['User'] = 'console'
    samples[preflight.NAMES[1]] = top(1000)
    result = preflight.collect()
    assert 'DIFFERENT_HOST_PROCESS_IDENTITIES' in result['unresolved']
    assert result['containers'][1]['processes']['host_uid_gid'] == [(1000, 1000)]


def test_missing_gate_does_not_treat_application_mount_as_gate(installed):
    items, samples, calls = installed
    items[preflight.NAMES[0]]['Config']['Env'] = ['PASSWORD=private-secret']
    result = preflight.collect()
    assert 'GATE_NOT_CONFIGURED' in result['unresolved']
    assert 'WRITABLE_NON_TMPFS_GATE_MOUNT_NOT_OBSERVED' in result['unresolved']
    assert result['containers'][0]['binding']['gate_mount'] is None


@pytest.mark.parametrize('gate', ['', 'relative', '/a/../b', '//gate', '/a//b', '/gate/'])
def test_invalid_gate_refuses(gate):
    with pytest.raises(ValueError):
        preflight.binding(container(preflight.NAMES[0], gate=gate), preflight.NAMES[0])


@pytest.mark.parametrize('field', ['FC_CONTROL_CAPTURE_GATE', 'PASSWORD'])
def test_duplicate_environment_refuses(field):
    item = container(preflight.NAMES[0])
    item['Config']['Env'].append(field + '=other')
    with pytest.raises(ValueError, match='DUPLICATE_FIELD'):
        preflight.binding(item, preflight.NAMES[0])


@pytest.mark.parametrize('mutation', ['name', 'project', 'service', 'id', 'image', 'paused', 'stopped', 'restarting'])
def test_wrong_or_inactive_container_refuses(mutation):
    item = container(preflight.NAMES[0])
    if mutation in ('name', 'id', 'image'):
        item[{'name': 'Name', 'id': 'Id', 'image': 'Image'}[mutation]] = 'other'
    elif mutation in ('project', 'service'):
        item['Config']['Labels']['com.docker.compose.' + mutation] = 'other'
    else:
        item['State'][{'paused': 'Paused', 'stopped': 'Running', 'restarting': 'Restarting'}[mutation]] = mutation != 'stopped'
    with pytest.raises(ValueError):
        preflight.binding(item, preflight.NAMES[0])


@pytest.mark.parametrize('kind', ['bind', 'tmpfs'])
def test_deepest_mount_shadows_writable_parent(installed, kind):
    items, samples, calls = installed
    items[preflight.NAMES[0]]['Mounts'] = [dict(Type='bind', Source='/host', Destination='/run', RW=True),
        dict(Type=kind, Source='/host/readonly' if kind == 'bind' else '', Destination='/run/capture', RW=kind == 'tmpfs')]
    result = preflight.collect()
    assert 'WRITABLE_NON_TMPFS_GATE_MOUNT_NOT_OBSERVED' in result['unresolved']
    assert result['containers'][0]['binding']['gate_mount']['type'] == kind


def test_gate_mount_prefix_requires_path_boundary(installed):
    items, samples, calls = installed
    items[preflight.NAMES[0]]['Mounts'][0]['Destination'] = '/run/cap'
    assert preflight.collect()['containers'][0]['binding']['gate_mount'] is None


@pytest.mark.parametrize('mutation', ['empty', 'duplicate', 'main-missing', 'username', 'columns', 'too-many'])
def test_incomplete_process_observation_refuses(mutation):
    value = top()
    if mutation == 'empty':
        value['Processes'] = []
    elif mutation == 'duplicate':
        value['Processes'] *= 2
    elif mutation == 'main-missing':
        value['Processes'][0][2] = '456'
    elif mutation == 'username':
        value['Processes'][0][0] = 'console'
    elif mutation == 'columns':
        value['Titles'][0] = 'USER'
    else:
        value['Processes'] *= 129
    with pytest.raises(ValueError):
        preflight.processes(value, 123)


@pytest.mark.parametrize('field', ['Id', 'Image', 'Env', 'StartedAt', 'Mounts'])
def test_changed_binding_refuses_instead_of_empty_success(installed, monkeypatch, field):
    original = preflight.read
    count = 0

    def changing(endpoint):
        nonlocal count
        value = original(endpoint)
        count += 1
        if count == 5:
            if field in ('Id', 'Image'):
                value[field] = ('sha256:' if field == 'Image' else '') + '4' * 64
            elif field == 'Env':
                value['Config']['Env'].append('OTHER=changed')
            elif field == 'StartedAt':
                value['State']['StartedAt'] = '2026-11-24T01:00:00Z'
            else:
                value['Mounts'][0]['Source'] = '/changed'
        return value

    monkeypatch.setattr(preflight, 'read', changing)
    with pytest.raises(ValueError, match='BINDING_CHANGED'):
        preflight.collect()


@pytest.mark.parametrize('endpoint', ['/containers/other/json', '/containers/' + '1' * 64 + '/exec',
                                     '/images/json', '/containers/' + preflight.NAMES[0] + '/top'])
def test_endpoint_allowlist_precedes_connection(endpoint, monkeypatch):
    monkeypatch.setattr(preflight, 'DockerRead', lambda: pytest.fail('Connection opened'))
    with pytest.raises(ValueError, match='READ_SCOPE'):
        preflight.read(endpoint)


@pytest.mark.parametrize('raw,status,error', [(b'{"value":1}', 200, None), (b'{}', 403, 'DOCKER_READ_FAILED'),
    (b' ' * (preflight.LIMIT + 1), 200, 'READ_BOUNDS'), (b'{"a":1,"a":2}', 200, 'DUPLICATE_FIELD')])
def test_get_only_bounded_transport_closes(raw, status, error, monkeypatch):
    calls = []
    connection = SimpleNamespace(request=lambda method, endpoint: calls.append((method, endpoint)),
        getresponse=lambda: SimpleNamespace(status=status, read=lambda size: raw[:size]),
        close=lambda: calls.append('closed'))
    monkeypatch.setattr(preflight, 'DockerRead', lambda: connection)
    endpoint = '/containers/' + preflight.NAMES[0] + '/json'
    if error:
        with pytest.raises(ValueError, match=error):
            preflight.read(endpoint)
    else:
        assert preflight.read(endpoint) == {'value': 1}
    assert calls == [('GET', endpoint), 'closed']


def test_cli_failure_does_not_print_private_exception(monkeypatch, capsys):
    monkeypatch.setattr(preflight.resource, 'setrlimit', lambda *args: None)
    alarms = []
    monkeypatch.setattr(preflight.signal, 'alarm', alarms.append)
    monkeypatch.setattr(preflight, 'collect', lambda: (_ for _ in ()).throw(ValueError('private-secret')))
    with pytest.raises(SystemExit) as error:
        preflight.main()
    assert error.value.code == 1
    captured = capsys.readouterr()
    assert captured.out == ''
    assert captured.err == 'OWNER_ADMISSION_PREFLIGHT_REFUSED\n'
    assert alarms == [30, 0]
