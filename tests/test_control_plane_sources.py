from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

from control_plane import collect_inventory
from control_plane.apps.console import collector, server_inventory


NOW = datetime(2026, 11, 3, tzinfo=timezone.utc)


def observation(source='nl-amsterdam-1', seconds=0, services=None, scope='production'):
    return SimpleNamespace(source=source, scope=scope, observed_at=NOW - timedelta(seconds=seconds),
        server=SimpleNamespace(services=services if services is not None else {
            name: 'active' for name in collector.ORDINARY_SERVICES}))


def test_inventory_uses_exact_nodes_and_keeps_old_country_as_history():
    assert collect_inventory.HOSTS == {'gateway-ru': '185.251.89.19',
        'nl-amsterdam-1': '185.10.158.212', 'nl-amsterdam-2': '185.10.158.196'}
    assert collector.SOURCES['gateway-nl']['host'] is None
    with pytest.raises(ValueError):
        collect_inventory.ssh_command('gateway-nl')
    with pytest.raises(ValueError):
        collector.collect('gateway-nl', b's' * 32)


@pytest.mark.parametrize('source', ['nl-amsterdam-1', 'nl-amsterdam-2'])
def test_node_collection_never_reads_registry_or_requires_identity_key(source, tmp_path, monkeypatch):
    path = tmp_path / 'do-not-read.db'
    path.write_bytes(b'private registry sentinel')
    def forbidden(*args):
        pytest.fail('Node collector must not read user registry')
    monkeypatch.setattr(collector, 'registry_rows', forbidden)
    monkeypatch.setattr(collector.subprocess, 'run', lambda *args, **kwargs: SimpleNamespace(
        stdout='LoadState=loaded\nActiveState=active\n'))
    result = collector.collect(source, path=path)
    assert result['source'] == source
    assert result['devices'] == [] and result['registry_status'] == 'not_collected'
    assert path.read_bytes() == b'private registry sentinel'


def test_ssh_requires_strict_pins_and_optional_existing_pin_file(tmp_path):
    pins = tmp_path / 'known_hosts'
    pins.write_text('approved public test host pin')
    command = collect_inventory.ssh_command('nl-amsterdam-2', pins)
    assert 'StrictHostKeyChecking=yes' in command and 'BatchMode=yes' in command
    assert 'UserKnownHostsFile=' + str(pins) in command
    assert command[-2:] == ['root@185.10.158.196', 'python3 -B -']
    with pytest.raises(ValueError):
        collect_inventory.ssh_command('nl-amsterdam-2', tmp_path / 'missing')
    alias = tmp_path / 'alias'
    alias.symlink_to(pins)
    with pytest.raises(ValueError):
        collect_inventory.ssh_command('nl-amsterdam-2', alias)


def test_node_cli_does_not_create_or_send_hmac_key(tmp_path, monkeypatch, capsys):
    source = Path(collector.__file__).read_text()
    standalone = tmp_path / 'apps/console/collector.py'
    standalone.parent.mkdir(parents=True)
    standalone.write_text(source)
    for module in ('transport_collector.py', 'metrics_collector.py'):
        (standalone.parent/module).write_text((Path(collector.__file__).parent/module).read_text())
    monkeypatch.setattr(collect_inventory, 'BASE', tmp_path)
    monkeypatch.setattr(sys, 'argv', ['collect_inventory.py', 'nl-amsterdam-2'])
    def run(command, **options):
        assert command[-2:] == ['root@185.10.158.196', 'python3 -B -']
        assert b"collect('nl-amsterdam-2', None)" in options['input']
        assert b'bytes.fromhex(' not in options['input']
        return SimpleNamespace(returncode=0, stdout=json.dumps(dict(
            source='nl-amsterdam-2', scope='production')).encode())
    monkeypatch.setattr(collect_inventory.subprocess, 'run', run)
    collect_inventory.main()
    destination = Path(capsys.readouterr().out.strip())
    assert destination.parent == tmp_path / '.local'
    assert destination.stat().st_mode & 0o777 == 0o600
    assert not (tmp_path / '.local/inventory-hmac.key').exists()


@pytest.mark.parametrize(('seconds', 'expected'), [(0, 'observed_active'), (300, 'observed_active'),
    (301, 'stale'), (-15, 'observed_active'), (-16, 'clock_skew')])
def test_observation_freshness_is_not_availability(seconds, expected):
    assert server_inventory.observation_state('nl-amsterdam-1', observation(seconds=seconds), NOW) == expected


@pytest.mark.parametrize(('status', 'expected'), [('failed', 'degraded'), ('inactive', 'degraded'),
    ('not_found', 'degraded'), ('deactivating', 'degraded'), ('activating', 'degraded'),
    ('unknown', 'unknown'), ('unexpected', 'unknown')])
def test_required_service_failure_and_unknown_are_not_green(status, expected):
    item = observation()
    item.server.services[collector.ORDINARY_SERVICES[0]] = status
    assert server_inventory.observation_state(item.source, item, NOW) == expected


def test_missing_or_wrong_node_never_uses_legacy_or_other_node():
    item = observation()
    assert server_inventory.observation_state(item.source, None, NOW) == 'no_data'
    assert server_inventory.observation_state('nl-amsterdam-2', item, NOW) == 'unknown'
    assert server_inventory.observation_state(item.source, observation(scope='synthetic'), NOW) == 'unknown'
    assert server_inventory.observation_state(item.source, observation(services={}), NOW) == 'unknown'
    cards = server_inventory.server_cards([item, observation('gateway-nl')], NOW)
    assert [(card['source'], card['state']) for card in cards] == [('gateway-ru', 'no_data'),
        ('nl-amsterdam-1', 'observed_active'), ('nl-amsterdam-2', 'no_data'), ('gateway-nl', 'retired')]
    selected = server_inventory.server_cards([item], NOW, 'nl-amsterdam-2')
    assert len(selected) == 1 and selected[0]['snapshot'] is None
