import copy
import hashlib
import json
import os
import stat
import subprocess
import sys

import pytest

from scripts import control_ha_owner_activation_plan as plan
from tests.test_control_ha_owner_upgrade import installed, images
from tests.test_control_ha_owner_admission_preflight import top


@pytest.fixture
def inputs():
    value = dict(observed_at_ns=123456789, containers={}, processes={}, images={}, candidates={})
    for index, role in enumerate(plan.upgrade.ROLES):
        item = installed(role)
        item['Config']['Image'] = 'private-original-tag'
        item['Config']['Healthcheck'] = {'Test': ['CMD', 'private-health-probe']}
        item['HostConfig'].update(Binds=['/private/token:/run/token:ro'], NetworkMode='private-network',
                                 PortBindings={'8000/tcp': [{'HostIp': '127.0.0.1', 'HostPort': '12345'}]},
                                 SecurityOpt=['no-new-privileges'], CapDrop=['ALL'], RestartPolicy={'Name': 'unless-stopped'},
                                 Memory=256000000, LogConfig={'Type': 'json-file'}, Tmpfs={'/tmp': 'rw'})
        item['Mounts'].append(dict(Type='bind', Source='/private/token', Destination='/run/token', RW=False))
        item['NetworkSettings'] = {'Networks': {'private-network': {'Aliases': ['private-alias'], 'IPAddress': '192.0.2.2'}}}
        baseline, candidate = images()
        baseline['Id'] = item['Image']
        candidate['Id'] = 'sha256:' + str(index + 7) * 64
        value['images'].update({baseline['Id']: baseline, candidate['Id']: candidate})
        value['containers'][role] = item
        value['processes'][role] = top(plan.GATES[role]['uid'])
        value['candidates'][role] = candidate['Id']
    return value


def test_exact_delta_preserves_private_configuration_and_input(inputs, monkeypatch):
    original = copy.deepcopy(inputs)
    def forbidden(*args, **kwargs):
        pytest.fail('offline proposal attempted live dispatch')
    monkeypatch.setattr(plan.upgrade, 'docker', forbidden)
    monkeypatch.setattr(plan.observer, 'read', forbidden)
    candidate = plan.proposal(inputs)
    assert candidate == plan.proposal(inputs) and inputs == original
    for role, item in candidate['roles'].items():
        before, after = item['current'], copy.deepcopy(item['proposed'])
        gate = plan.GATES[role]
        assert after['Image'] == after['Config']['Image'] == inputs['candidates'][role]
        assert after['Config']['Env'].pop() == plan.observer.GATE + '=' + plan.DESTINATION
        assert after['HostConfig']['Binds'].pop() == gate['source'] + ':' + plan.DESTINATION + ':rw,rprivate'
        assert after['Mounts'].pop()['Source'] == gate['source']
        after['Image'], after['Config']['Image'] = before['Image'], before['Config']['Image']
        assert after == before
        assert item['rollback_config_sha256'] == plan.observer.digest(before)
    receipt = plan.validate(candidate, inputs)
    assert all(receipt[field] is False for field in ('executable', 'independent_approval', 'runtime_qualified',
                                                   'capture_permitted', 'deployed'))
    for secret in ('private-secret', 'private-token', '/private/token', 'private-network', 'private-alias',
                   'private-health-probe', '192.0.2.2', '12345'):
        assert secret not in json.dumps(receipt)


@pytest.mark.parametrize('path,value', [
    (('Config', 'Cmd'), ['sh', '-c', 'seed']), (('Config', 'Env'), ['PASSWORD=changed']),
    (('Config', 'User'), 'root'), (('Config', 'Entrypoint'), ['other']),
    (('Config', 'Healthcheck'), {'Test': ['NONE']}), (('Config', 'WorkingDir'), '/tmp'),
    (('Config', 'Labels'), {'other': 'project'}), (('Config', 'Volumes'), {'/product': {}}),
    (('HostConfig', 'Binds'), []), (('HostConfig', 'ReadonlyRootfs'), False),
    (('HostConfig', 'NetworkMode'), 'host'), (('HostConfig', 'PortBindings'), {}),
    (('HostConfig', 'SecurityOpt'), []), (('HostConfig', 'CapDrop'), []),
    (('HostConfig', 'Memory'), 0), (('HostConfig', 'RestartPolicy'), {'Name': 'no'}),
    (('HostConfig', 'LogConfig'), {'Type': 'none'}), (('HostConfig', 'Tmpfs'), {}),
    (('Mounts',), []), (('NetworkSettings',), {}),
])
def test_any_unapproved_config_edit_refuses(inputs, path, value):
    candidate = plan.proposal(inputs)
    target = candidate['roles']['console']['proposed']
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = value
    with pytest.raises(ValueError, match='UNREVIEWED_CONFIG_DELTA'):
        plan.validate(candidate, inputs)


@pytest.mark.parametrize('change', ['approval', 'rollback', 'uid', 'binding', 'added-role', 'new-field', 'wrong-input'])
def test_plan_envelope_and_observation_are_bound(inputs, change):
    candidate = plan.proposal(inputs)
    if change == 'approval':
        candidate['independent_approval'] = True
    elif change == 'rollback':
        candidate['roles']['console']['current']['Config']['Env'] = []
    elif change == 'uid':
        candidate['roles']['console']['gate']['uid'] = 0
    elif change == 'binding':
        candidate['roles']['console']['observed']['id'] = 'f' * 64
    elif change == 'added-role':
        candidate['roles']['other'] = {}
    elif change == 'new-field':
        candidate['apply'] = True
    else:
        inputs['observed_at_ns'] += 1
    with pytest.raises(ValueError, match='UNREVIEWED_CONFIG_DELTA'):
        plan.validate(candidate, inputs)


@pytest.mark.parametrize('change', ['missing-role', 'extra-image', 'duplicate-image', 'image-id', 'image-config',
                                   'layers', 'identity', 'gate-present', 'stopped', 'startup', 'unknown-field'])
def test_baseline_identity_and_overlay_must_match(inputs, change):
    role = 'console'
    item = inputs['containers'][role]
    image = inputs['images'][inputs['candidates'][role]]
    if change == 'missing-role':
        del inputs['containers'][role]
    elif change == 'extra-image':
        inputs['images']['other'] = {}
    elif change == 'duplicate-image':
        inputs['candidates'][role] = inputs['candidates']['system_publisher']
    elif change == 'image-id':
        image['Id'] = 'sha256:' + 'f' * 64
    elif change == 'image-config':
        image['Config']['User'] = 'root'
    elif change == 'layers':
        image['RootFS']['Layers'][0] = 'other'
    elif change == 'identity':
        inputs['processes'][role] = top(0)
    elif change == 'gate-present':
        item['Config']['Env'].append(plan.observer.GATE + '=/run/old')
    elif change == 'stopped':
        item['State']['Running'] = False
    elif change == 'startup':
        item['Config']['Cmd'][2] += ' && other-command'
    else:
        inputs['secret-extra'] = 'private-secret'
    with pytest.raises(ValueError):
        plan.proposal(inputs)


@pytest.mark.parametrize('change', ['parent', 'child', 'source', 'other-source', 'bind', 'structured', 'tmpfs', 'inherit'])
def test_gate_cannot_shadow_or_reuse_product_mounts(inputs, change):
    item = inputs['containers']['console']
    if change in ('parent', 'child'):
        item['Mounts'][0]['Destination'] = '/run' if change == 'parent' else plan.DESTINATION + '/child'
    elif change in ('source', 'other-source'):
        role = 'console' if change == 'source' else 'system_publisher'
        item['Mounts'][0]['Source'] = plan.GATES[role]['source'] + '/child'
    elif change == 'bind':
        item['HostConfig']['Binds'].append('/private/bind:' + plan.DESTINATION + ':ro')
    elif change == 'structured':
        item['HostConfig']['Mounts'] = [dict(Type='bind', Source='/private/structured', Target=plan.DESTINATION)]
    elif change == 'tmpfs':
        item['HostConfig']['Tmpfs'][plan.DESTINATION] = 'rw'
    else:
        item['HostConfig']['VolumesFrom'] = ['other-container']
    with pytest.raises(ValueError):
        plan.proposal(inputs)


def private_input(tmp_path, inputs):
    tmp_path.chmod(0o700)
    path = tmp_path / 'input.json'
    raw = json.dumps(inputs).encode()
    path.write_bytes(raw)
    path.chmod(0o600)
    return path, hashlib.sha256(raw).hexdigest()


@pytest.mark.parametrize('change', ['none', 'name', 'destination', 'missing'])
def test_named_volume_is_preserved_only_with_matching_resolved_mount(inputs, change):
    item = inputs['containers']['console']
    item['HostConfig']['Binds'].append('private-volume:/app/data:rw')
    mount = dict(Type='volume', Name='private-volume', Source='/var/lib/docker/volumes/private-volume/_data',
                 Destination='/app/data', RW=True)
    if change == 'name':
        mount['Name'] = 'other'
    elif change == 'destination':
        mount['Destination'] = '/app/other'
    if change != 'missing':
        item['Mounts'].append(mount)
    if change != 'none':
        with pytest.raises(ValueError, match='NAMED_VOLUME_BINDING'):
            plan.proposal(inputs)
    else:
        candidate = plan.proposal(inputs)
        assert candidate['roles']['console']['proposed']['Mounts'][:-1] == item['Mounts']
        assert candidate['roles']['console']['proposed']['HostConfig']['Binds'][:-1] == item['HostConfig']['Binds']


@pytest.mark.parametrize('change', ['mode', 'hardlink', 'symlink', 'parent', 'fifo', 'size', 'pin', 'duplicate'])
def test_unsafe_or_unpinned_input_refuses(tmp_path, inputs, change):
    path, digest = private_input(tmp_path, inputs)
    if change == 'mode':
        path.chmod(0o644)
    elif change == 'hardlink':
        os.link(path, tmp_path / 'another')
    elif change == 'symlink':
        link = tmp_path / 'link'
        link.symlink_to(path)
        path = link
    elif change == 'parent':
        tmp_path.chmod(0o755)
    elif change == 'fifo':
        path.unlink()
        os.mkfifo(path, 0o600)
    elif change == 'size':
        with path.open('wb') as stream:
            stream.truncate(plan.LIMIT + 1)
    elif change == 'pin':
        digest = '0' * 64
    else:
        path.write_bytes(b'{"value":1,"value":2}')
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ValueError):
        plan.read_private(path, digest)


def test_cli_is_offline_private_redacted_and_does_not_overwrite(tmp_path, inputs):
    path, digest = private_input(tmp_path, inputs)
    output = tmp_path / 'proposal.json'
    command = [sys.executable, '-m', 'scripts.control_ha_owner_activation_plan', '--input', str(path),
               '--input-sha256', digest, '--output', str(output)]
    result = subprocess.run(command, capture_output=True, timeout=5)
    assert result.returncode == 0 and not result.stderr
    assert b'private-secret' not in result.stdout and b'/private/token' not in result.stdout
    before = output.read_bytes()
    assert stat.S_IMODE(output.stat().st_mode) == 0o600
    assert json.loads(result.stdout) == plan.validate(json.loads(before), inputs)
    repeated = subprocess.run(command, capture_output=True, timeout=5)
    assert repeated.returncode == 1 and not repeated.stdout
    assert repeated.stderr == b'OWNER_ACTIVATION_PLAN_REFUSED\n' and output.read_bytes() == before
    assert path.read_bytes() == json.dumps(inputs).encode()


@pytest.mark.parametrize('change', ['none', 'command', 'proposal-pin', 'input-pin'])
def test_cli_verifies_exact_retained_plan_without_writing(tmp_path, inputs, change):
    path, digest = private_input(tmp_path, inputs)
    candidate = plan.proposal(inputs)
    if change == 'command':
        candidate['roles']['console']['proposed']['Config']['Cmd'] = ['private-secret-command']
    retained = tmp_path / 'retained.json'
    plan.write_private(retained, candidate)
    before = retained.read_bytes()
    proposal_pin = hashlib.sha256(before).hexdigest()
    command = [sys.executable, '-m', 'scripts.control_ha_owner_activation_plan', '--input', str(path),
               '--input-sha256', '0' * 64 if change == 'input-pin' else digest, '--verify', str(retained),
               '--proposal-sha256', '0' * 64 if change == 'proposal-pin' else proposal_pin]
    result = subprocess.run(command, capture_output=True, timeout=5)
    assert retained.read_bytes() == before and set(tmp_path.iterdir()) == {path, retained}
    if change == 'none':
        assert result.returncode == 0 and not result.stderr
        assert json.loads(result.stdout) == plan.validate(candidate, inputs)
    else:
        assert result.returncode == 1 and not result.stdout
        assert result.stderr == b'OWNER_ACTIVATION_PLAN_REFUSED\n'
