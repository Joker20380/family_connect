import copy
import io
import json
from types import SimpleNamespace
from pathlib import Path

import pytest

from tests.fixtures.owner_upgrade import cross_mount as stand


def reports(uid=10001):
    writer = dict(uid=uid, gid=uid, groups=[], maps={'uid': 'a' * 64, 'gid': 'b' * 64},
        source_sha256='c' * 64, namespaces={name: [5, index + 1] for index, name in enumerate(stand.NAMESPACES)},
        pins={name: [8, index + 1] for index, name in enumerate(('.', 'admission.lock', 'operations.lock', 'pending'))},
        files={'.': [uid, uid, 0o700], 'admission.lock': [uid, uid, 0o600],
               'operations.lock': [uid, uid, 0o600], 'pending': [uid, uid, 0o700]}, pending=0)
    guardian = copy.deepcopy(writer)
    writer['groups'] = [uid]
    guardian['namespaces']['mnt'][1] += 100
    guardian['namespaces']['pid'][1] += 100
    return writer, guardian


@pytest.mark.parametrize('uid', [10001, 1000])
def test_exact_cross_mount_identity(uid):
    writer, guardian = reports(uid)
    original = copy.deepcopy((writer, guardian))
    assert stand.match(writer, guardian, uid) is None
    assert (writer, guardian) == original


@pytest.mark.parametrize('side', [0, 1])
@pytest.mark.parametrize('field', ['uid', 'gid', 'groups', 'maps', 'source_sha256', 'pins', 'pending', 'files'])
def test_unbound_identity_refuses(side, field):
    pair = reports()
    item = pair[side]
    if field in ('uid', 'gid', 'pending'):
        item[field] += 1
    elif field == 'groups':
        item[field].append(1000)
    elif field == 'maps':
        item[field]['uid'] = 'd' * 64
    elif field == 'source_sha256':
        item[field] = 'd' * 64
    elif field == 'pins':
        item[field]['admission.lock'][1] += 100
    else:
        item[field]['operations.lock'][2] = 0o660
    with pytest.raises(RuntimeError, match='CROSS_MOUNT_REFUSED'):
        stand.match(*pair, 10001)


@pytest.mark.parametrize('namespace', stand.NAMESPACES)
def test_unqualified_namespace_relationship_refuses(namespace):
    writer, guardian = reports()
    if namespace in ('user', 'time'):
        writer['namespaces'][namespace][1] += 1
    else:
        writer['namespaces'][namespace] = guardian['namespaces'][namespace]
    with pytest.raises(RuntimeError, match='CROSS_MOUNT_REFUSED'):
        stand.match(writer, guardian, 10001)


def test_aliased_files_refuse_even_when_both_reports_match():
    writer, guardian = reports()
    for item in (writer, guardian):
        item['pins']['operations.lock'] = item['pins']['admission.lock']
    with pytest.raises(RuntimeError, match='CROSS_MOUNT_REFUSED'):
        stand.match(writer, guardian, 10001)


@pytest.mark.parametrize('content', [b'', b'{}', b'{}' + b' ' * 16384 + b'\n'])
def test_truncated_or_missing_response_refuses(monkeypatch, content):
    stream = io.BytesIO(content)
    monkeypatch.setattr(stand.select, 'select', lambda *args: ([stream], [], []))
    with pytest.raises(RuntimeError, match='CROSS_MOUNT_REFUSED'):
        stand.receive(SimpleNamespace(stdout=stream))


def test_response_deadline_is_bounded(monkeypatch):
    monkeypatch.setattr(stand.select, 'select', lambda *args: ([], [], []))
    with pytest.raises(RuntimeError, match='CROSS_MOUNT_REFUSED'):
        stand.receive(SimpleNamespace(stdout=io.BytesIO()), timeout=0.001)


def test_complete_response(monkeypatch):
    stream = io.BytesIO(json.dumps({'status': 'BUSY'}).encode() + b'\n')
    monkeypatch.setattr(stand.select, 'select', lambda *args: ([stream], [], []))
    assert stand.receive(SimpleNamespace(stdout=stream)) == {'status': 'BUSY'}


def test_existing_directory_refuses_before_docker(tmp_path, monkeypatch):
    monkeypatch.setattr(stand, 'docker', lambda *args, **kwargs: pytest.fail('unexpected Docker dispatch'))
    with pytest.raises(RuntimeError, match='CROSS_MOUNT_REFUSED'):
        stand.host(tmp_path)


def test_symlink_parent_refuses_before_docker(tmp_path, monkeypatch):
    alias = tmp_path / 'alias'
    alias.symlink_to(tmp_path, target_is_directory=True)
    monkeypatch.setattr(stand, 'docker', lambda *args, **kwargs: pytest.fail('unexpected Docker dispatch'))
    with pytest.raises(RuntimeError, match='CROSS_MOUNT_REFUSED'):
        stand.host(alias / 'new')


def container():
    return dict(Id='f' * 64, Image=stand.IMAGES['console'], Config={
        'Labels': {'family-connect.cross-mount': 'fixture'}, 'User': '10001:10001'},
        State={'Running': True, 'Pid': 100}, HostConfig={
            'ReadonlyRootfs': True, 'NetworkMode': 'none', 'PidsLimit': 48, 'Memory': 192 * 1024 * 1024,
            'CapDrop': ['ALL'], 'SecurityOpt': ['no-new-privileges'], 'CapAdd': None, 'UsernsMode': ''},
        Mounts=[dict(Type='bind', Propagation='rprivate', Destination='/stand', Source='/private/source', RW=False),
                dict(Type='bind', Propagation='rprivate', Destination=stand.DESTINATION,
                     Source='/private/console/gate', RW=True)])


def test_actual_mount_readback():
    receipt = stand.container_binding(container(), 'console', 'fixture', Path('/private/source'), Path('/private'))
    assert receipt['image'] == stand.IMAGES['console']
    assert '/private' not in json.dumps(receipt)


@pytest.mark.parametrize('field', ['label', 'running', 'user', 'image', 'network', 'rootfs', 'capability',
                                  'source', 'destination', 'mode', 'propagation', 'alias', 'extra', 'tmpfs'])
def test_unexpected_container_configuration_refuses(field):
    item = container()
    if field == 'label':
        item['Config']['Labels']['family-connect.cross-mount'] = 'other'
    elif field == 'running':
        item['State']['Running'] = False
    elif field == 'user':
        item['Config']['User'] = '0:0'
    elif field == 'image':
        item['Image'] = 'sha256:' + '0' * 64
    elif field == 'network':
        item['HostConfig']['NetworkMode'] = 'host'
    elif field == 'rootfs':
        item['HostConfig']['ReadonlyRootfs'] = False
    elif field == 'capability':
        item['HostConfig']['CapAdd'] = ['DAC_OVERRIDE']
    elif field in ('source', 'destination', 'mode', 'propagation'):
        key = {'source': 'Source', 'destination': 'Destination', 'mode': 'RW', 'propagation': 'Propagation'}[field]
        item['Mounts'][1][key] = False if field == 'mode' else '/unexpected'
    elif field in ('alias', 'extra'):
        item['Mounts'].append(copy.deepcopy(item['Mounts'][0]))
        if field == 'extra':
            item['Mounts'][-1]['Destination'] = '/extra'
    else:
        item['Mounts'][1]['Type'] = 'tmpfs'
    with pytest.raises(RuntimeError, match='CROSS_MOUNT_REFUSED'):
        stand.container_binding(item, 'console', 'fixture', Path('/private/source'), Path('/private'))
