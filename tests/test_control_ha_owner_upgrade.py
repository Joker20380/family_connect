import copy
import io
import json
import tarfile
from types import SimpleNamespace

import pytest

from scripts import control_ha_owner_upgrade as upgrade
from tests.test_control_ha_owner_admission_preflight import container
from tests.fixtures.owner_upgrade.native import LABEL, Stand


def installed(role):
    item = container(f'fc-control-plane-0-{role}-1', gate=None)
    item['Image'] = upgrade.ROLES[role]
    item['Config'].update(User=upgrade.USERS[role], Entrypoint=None, WorkingDir='/app/control_plane',
                          Cmd=['sh', '-ec', upgrade.CONSOLE if role == 'console' else
                               upgrade.PUBLISHER.format(origin='https://example.invalid')])
    return item


@pytest.mark.parametrize('role', upgrade.ROLES)
def test_exact_effective_workload_is_redacted_without_authorization(role):
    result = upgrade.workload(installed(role), role)
    assert 'private-secret' not in json.dumps(result)
    assert result['image'] == upgrade.ROLES[role] and not result['gate_configured']


@pytest.mark.parametrize('role', upgrade.ROLES)
@pytest.mark.parametrize('change', ['image', 'user', 'entrypoint', 'workdir', 'gate', 'rootfs', 'shell',
                                  'seed', 'suffix', 'substitution', 'redirect', 'environment'])
def test_unreviewed_workload_refuses(role, change):
    item = installed(role)
    config = item['Config']
    if change == 'image':
        item['Image'] = 'sha256:' + '9' * 64
    elif change in ('user', 'entrypoint', 'workdir'):
        config[{'user': 'User', 'entrypoint': 'Entrypoint', 'workdir': 'WorkingDir'}[change]] = 'other'
    elif change == 'gate':
        config['Env'].append(upgrade.source.preflight.GATE + '=/run/other')
    elif change == 'rootfs':
        item['HostConfig']['ReadonlyRootfs'] = False
    elif change == 'shell':
        config['Cmd'][0] = 'bash'
    else:
        config['Cmd'][2] += {'seed': ' && python manage.py seed_demo', 'suffix': '; true',
                             'substitution': ' $(id)', 'redirect': ' >/other',
                             'environment': ' SECRET=other'}[change]
    with pytest.raises(ValueError):
        upgrade.workload(item, role)


@pytest.mark.parametrize('origin', ['http://example.invalid', 'https://secret@example.invalid',
                                  'https://example.invalid/a', 'https://example.invalid?token=secret',
                                  'https://example.invalid:443', 'https://$(id)'])
def test_origin_cannot_be_credentials_path_or_shell(origin):
    item = installed('system_publisher')
    item['Config']['Cmd'][2] = upgrade.PUBLISHER.format(origin=origin)
    with pytest.raises(ValueError):
        upgrade.workload(item, 'system_publisher')


def test_installed_origin_variable_is_supported_but_other_expansions_refuse():
    item = installed('system_publisher')
    item['Config']['Cmd'][2] = upgrade.PUBLISHER.format(origin='$FC_SYSTEM_PUBLISHER_ORIGIN')
    upgrade.workload(item, 'system_publisher')
    item['Config']['Cmd'][2] = upgrade.PUBLISHER.format(origin='$OTHER')
    with pytest.raises(ValueError, match='PUBLISHER_ORIGIN'):
        upgrade.workload(item, 'system_publisher')


@pytest.mark.parametrize('role', upgrade.ROLES)
def test_context_is_closed_deterministic_source_only(role):
    first, records = upgrade.context(role)
    assert first == upgrade.context(role)[0]
    with tarfile.open(fileobj=io.BytesIO(first)) as archive:
        assert set(archive.getnames()) == {'Dockerfile', *('app/' + name for name in upgrade.source.SOURCES)}
        assert all(member.isfile() and member.mode == 0o644 and member.uid == member.gid == 0 and
                   member.mtime == 0 for member in archive.getmembers())
        assert archive.extractfile('Dockerfile').read() == (
            f'FROM {upgrade.ROLES[role]}\nCOPY --chown=0:0 app/ /app/\n').encode()
        for name, record in records.items():
            assert upgrade.source.source_record(archive.extractfile('app/' + name).read()) == record


def test_missing_symlink_and_oversized_sources_refuse(tmp_path):
    with pytest.raises(ValueError, match='SOURCE_PATH'):
        upgrade.context('console', tmp_path)
    candidate = tmp_path / upgrade.source.SOURCES[0]
    candidate.parent.mkdir()
    candidate.symlink_to(upgrade.source.ROOT / upgrade.source.SOURCES[0])
    with pytest.raises(ValueError, match='SOURCE_PATH'):
        upgrade.context('console', tmp_path)
    candidate.unlink()
    candidate.write_bytes(b'x' * (upgrade.source.FILE_LIMIT + 1))
    with pytest.raises(ValueError, match='SOURCE_BOUNDS'):
        upgrade.context('console', tmp_path)


def images():
    baseline = dict(Id=upgrade.ROLES['console'], Config={'User': 'console', 'Cmd': ['gunicorn']},
                    RootFS={'Type': 'layers', 'Layers': ['base', 'application']}, Os='linux', Architecture='amd64')
    candidate = copy.deepcopy(baseline)
    candidate['Id'] = 'sha256:' + '7' * 64
    candidate['RootFS']['Layers'].append('source-only')
    return baseline, candidate


def test_overlay_preserves_original_config_and_layers():
    upgrade.verify(*images())


@pytest.mark.parametrize('change', ['same', 'base', 'config', 'architecture', 'os', 'variant', 'layers', 'extra', 'type'])
def test_overlay_drift_refuses(change):
    baseline, candidate = images()
    if change == 'same':
        candidate['Id'] = baseline['Id']
    elif change == 'base':
        baseline['Id'] = 'sha256:' + '8' * 64
    elif change == 'config':
        candidate['Config']['User'] = 'root'
    elif change in ('architecture', 'os', 'variant'):
        candidate[change.capitalize() if change != 'os' else 'Os'] = 'other'
    elif change == 'layers':
        candidate['RootFS']['Layers'][0] = 'other'
    elif change == 'extra':
        candidate['RootFS']['Layers'].append('another')
    else:
        candidate['RootFS']['Type'] = 'other'
    with pytest.raises(ValueError):
        upgrade.verify(baseline, candidate)


def test_build_never_creates_or_replaces_a_container(monkeypatch):
    baseline, candidate = images()
    monkeypatch.setattr(upgrade, 'image', lambda image_id: baseline if image_id == baseline['Id'] else candidate)
    calls = []

    def docker(*arguments, **kwargs):
        calls.append((arguments, kwargs))
        return candidate['Id'].encode()

    monkeypatch.setattr(upgrade, 'docker', docker)
    result = upgrade.build('console')
    assert [arguments for arguments, kwargs in calls] == [('build', '--pull=false', '--network=none', '--quiet', '-')]
    assert result['rollback_image'] == baseline['Id']
    assert not result['independent_approval'] and not result['deployed']


def fake_stand(*, other_owner=False):
    calls = []

    def docker(*arguments):
        calls.append(arguments)
        if arguments[:2] == ('volume', 'inspect'):
            return json.dumps([{'Labels': {LABEL: 'other' if other_owner else 'token'}}]).encode()
        if arguments[0] == 'create':
            return b'owned-container'
        return b''

    lab = SimpleNamespace(name='fixture', volume='fixture-data', token='token', docker=docker,
                          container='owned-postgres', password='fixture-password', secret='fixture-secret')
    return Stand(lab, {}, {}), calls


def test_fixture_volume_cannot_alias_postgres_or_be_reused():
    stand, calls = fake_stand()
    name = stand.create_volume('data')
    assert name == 'fixture-upgrade-data' and name != stand.lab.volume
    with pytest.raises(ValueError, match='VOLUME_COLLISION'):
        stand.create_volume('data')
    assert len(calls) == 2


def test_existing_volume_with_other_owner_is_never_mounted_or_removed():
    stand, calls = fake_stand(other_owner=True)
    with pytest.raises(ValueError, match='VOLUME_OWNERSHIP'):
        stand.create_volume('data')
    assert not stand.volumes
    assert [call[:2] for call in calls] == [('volume', 'create'), ('volume', 'inspect')]


@pytest.mark.parametrize('role', upgrade.ROLES)
@pytest.mark.parametrize('enabled', [True, False])
def test_fixture_only_uses_disposable_volumes_namespace_and_secrets(monkeypatch, role, enabled):
    stand, calls = fake_stand()
    stand.data = 'owned-data'
    stand.gates = {role: 'owned-gate'}
    monkeypatch.setattr(stand, 'owned', lambda container: None)
    stand.create(role, upgrade.ROLES[role], ['python', 'manage.py', 'check'], enabled=enabled)
    arguments = calls[0]
    assert arguments[arguments.index('--network') + 1] == 'container:owned-postgres'
    assert arguments[arguments.index('--user') + 1] == upgrade.USERS[role]
    assert '--read-only' in arguments and '--no-healthcheck' in arguments
    mounts = [arguments[index + 1] for index, value in enumerate(arguments) if value == '--mount']
    assert all(value.startswith('type=volume,source=owned-') for value in mounts)
    assert not any('type=bind' in value or '/var/run/docker.sock' in value for value in arguments)
    assert ('FC_CONTROL_CAPTURE_GATE=/run/fc-admission/gate' in arguments) == enabled
    assert 'FC_SYSTEM_PUBLISHER_ORIGIN=https://example.invalid' in arguments
    assert 'FC_SUPPORT_SOCKET=' in arguments
