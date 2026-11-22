import json
from copy import deepcopy

import pytest

from scripts import package_metadata_panel_overlay as overlay


def test_geoip_delta_is_three_files_no_migration_or_command_change(tmp_path, monkeypatch):
    baseline = tmp_path / 'baseline'
    pins = {}
    for name in overlay.GEOIP_REPLACED:
        target = baseline / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b'accepted metadata baseline')
        pins[name] = overlay.digest(target.read_bytes())
    monkeypatch.setattr(overlay, 'GEOIP_REPLACED', pins)
    output = tmp_path / 'output'
    receipt = overlay.prepare_geoip_delta(baseline, overlay.GEOIP_IMAGE, output)
    assert len(receipt['installed']) == 3
    assert {str(item.relative_to(output)) for item in output.rglob('*') if item.is_file()} == set(pins) | {'Dockerfile'}
    assert 'CMD' not in (output / 'Dockerfile').read_text()
    assert 'RUN' not in (output / 'Dockerfile').read_text()
    assert all((output / name).stat().st_mode & 0o777 == 0o644 for name in pins)
    with pytest.raises(ValueError, match='image'):
        overlay.prepare_geoip_delta(baseline, 'unqualified', tmp_path / 'bad')
    (baseline / next(iter(pins))).write_bytes(b'changed')
    with pytest.raises(ValueError, match='preimage'):
        overlay.prepare_geoip_delta(baseline, overlay.GEOIP_IMAGE, tmp_path / 'changed')


@pytest.fixture
def baseline(tmp_path, monkeypatch):
    root = tmp_path / 'baseline'
    for group in ('REPLACED', 'PRESERVED'):
        pins = {}
        for name in getattr(overlay, group):
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b'accepted generation2 bytes\n')
            pins[name] = overlay.digest(target.read_bytes())
        monkeypatch.setattr(overlay, group, pins)
    return root


def test_only_metadata_files_and_query_free_command(baseline, tmp_path):
    output = tmp_path / 'context'
    receipt = overlay.prepare(baseline, overlay.IMAGE, output)
    assert set(receipt['installed']) == set(overlay.REPLACED) | set(overlay.ADDED)
    assert len(receipt['installed']) == 14
    assert not set(receipt['installed']) & set(overlay.PRESERVED)
    assert {str(path.relative_to(output)) for path in output.rglob('*') if path.is_file()} == set(receipt['installed']) | {'Dockerfile'}
    lines = (output / 'Dockerfile').read_text().splitlines()
    assert lines[0] == 'FROM ' + overlay.IMAGE
    assert lines[-2] == 'USER console'
    command = json.loads(lines[-1].removeprefix('CMD '))
    assert command[-2:] == ['--access-logformat', '%(m)s %(U)s %(s)s %(D)s']
    for name in receipt['installed']:
        assert (output / name).read_bytes() == (overlay.ROOT / name).read_bytes()
    with pytest.raises(FileExistsError):
        overlay.prepare(baseline, overlay.IMAGE, output)


@pytest.mark.parametrize('name', tuple(overlay.REPLACED) + tuple(overlay.PRESERVED))
def test_rejects_unknown_runtime_or_lost_alias_layer(baseline, tmp_path, name):
    (baseline / name).write_bytes(b'unexpected bytes')
    with pytest.raises(ValueError, match='preimage'):
        overlay.prepare(baseline, overlay.IMAGE, tmp_path / 'context')
    assert not (tmp_path / 'context').exists()


def test_rejects_pre_hmac_image_and_existing_metadata(baseline, tmp_path):
    with pytest.raises(ValueError, match='Unqualified'):
        overlay.prepare(baseline, 'sha256:' + '0' * 64, tmp_path / 'context')
    target = baseline / overlay.ADDED[0]
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b'existing metadata')
    with pytest.raises(ValueError, match='already present'):
        overlay.prepare(baseline, overlay.IMAGE, tmp_path / 'context')


def deployment():
    running = dict(Config=dict(Env=['PATH=/usr/bin', 'FC_PSEUDONYM_ALIASES=/run/fc-pseudonym-aliases.json'], User='console'),
                   HostConfig=dict(GroupAdd=['980']), Mounts=[
                       dict(Type='bind', Source='/private/aliases.json', Destination='/run/fc-pseudonym-aliases.json', RW=False),
                       dict(Type='volume', Name='production_data', Destination='/data', RW=True)])
    image = dict(Config=dict(Env=['PATH=/usr/bin'], User='console', Cmd=['gunicorn', '--access-logformat', overlay.LOG_FORMAT]))
    resolved = dict(services=dict(console=dict(environment={'FC_PSEUDONYM_ALIASES': '/run/fc-pseudonym-aliases.json'},
                    group_add=['980'], volumes=[
                        dict(type='bind', source='/private/aliases.json', target='/run/fc-pseudonym-aliases.json', read_only=True),
                        dict(type='volume', source='data', target='/data')])), volumes=dict(data=dict(name='production_data')))
    return running, image, resolved


def test_validate_loaded_configuration_not_just_reconstructed_compose():
    running, image, resolved = deployment()
    overlay.validate_deployment(running, image, resolved)
    missing_override = deepcopy(resolved)
    missing_override['services']['console']['environment'] = {}
    with pytest.raises(ValueError, match='environment'):
        overlay.validate_deployment(running, image, missing_override)
    missing_mount = deepcopy(resolved)
    missing_mount['services']['console']['volumes'] = resolved['services']['console']['volumes'][1:]
    with pytest.raises(ValueError, match='mounts'):
        overlay.validate_deployment(running, image, missing_mount)


@pytest.mark.parametrize('change', ('writable_alias', 'user', 'group', 'seed', 'query_log'))
def test_rejects_runtime_security_regressions(change):
    running, image, resolved = deployment()
    console = resolved['services']['console']
    if change == 'writable_alias':
        console['volumes'][0]['read_only'] = False
    elif change == 'user':
        console['user'] = 'root'
    elif change == 'group':
        console['group_add'] = []
    elif change == 'seed':
        console['command'] = ['sh', '-ec', 'python manage.py seed_demo; gunicorn --access-logformat "' + overlay.LOG_FORMAT + '"']
    elif change == 'query_log':
        console['command'] = ['gunicorn', '--access-logformat', '%(r)s']
    with pytest.raises(ValueError):
        overlay.validate_deployment(running, image, resolved)
