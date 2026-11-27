import base64
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
from types import SimpleNamespace

import pytest

from control.friends import geoip
from control_plane.apps.console import technical_metadata_collector as collector

NOW = 1794700000
PUBLIC = base64.b64encode(b'synthetic-public-key'.ljust(32, b'!')).decode()


def row(source='nl-amsterdam-1'):
    return dict(device='b' * 32, consent='enabled', consent_epoch=1, sequence=1, received_at=NOW,
        observations=dict(session=dict(received_at=NOW, expires_at=NOW + 604800, age_at_receive_ms=0,
            values=dict(gateway=source, transport='AWG', state='CONNECTED'))), geoip=None)


@pytest.fixture
def registry(tmp_path):
    registry = tmp_path / 'registry.db'
    with sqlite3.connect(registry) as connection:
        connection.execute('CREATE TABLE devices(device TEXT, wg TEXT, revoked INTEGER)')
        connection.execute('INSERT INTO devices VALUES (?,?,0)', ('b' * 32, PUBLIC))
    return registry


@pytest.fixture
def peer_source(tmp_path):
    root = tmp_path / 'awg'
    root.mkdir()
    (root / 'paid-transport.pyz').write_bytes(b'controlled-runtime')
    (root / 'transport-state.json').write_text(json.dumps(dict(schema=1, node='nl-amsterdam-1',
        records={'b' * 32: dict(decision=dict(public_key=PUBLIC))})))
    return root, hashlib.sha256(b'controlled-runtime').hexdigest()


def peer_command(command, **options):
    assert command[-1] in ('endpoints', 'latest-handshakes')
    assert options == dict(capture_output=True, check=True, timeout=4)
    value = '1.1.1.1:51820' if command[-1] == 'endpoints' else str(NOW - 10)
    return SimpleNamespace(stdout=(PUBLIC + '\t' + value + '\n').encode())


@pytest.mark.parametrize('source', collector.NL_SOURCES)
def test_both_nl_targets_require_canonical_binding(registry, source):
    result = collector.geoip_targets([row(source)], registry, NOW)
    assert result == [dict(device='b' * 32, public=PUBLIC, source=source, consent_epoch=1, sequence=1)]
    with sqlite3.connect(registry) as connection:
        connection.execute('UPDATE devices SET revoked=1')
    assert collector.geoip_targets([row(source)], registry, NOW) == []


@pytest.mark.parametrize('change', ['revoked', 'tcp', 'mesh', 'ru', 'disconnected', 'stale', 'future', 'expired', 'old_sample'])
def test_ineligible_devices_are_not_requested(registry, change):
    entry = row()
    session = entry['observations']['session']
    if change == 'revoked': entry['consent'] = 'revoked'
    if change == 'tcp': session['values']['transport'] = 'TCP'
    if change == 'mesh': session['values']['transport'] = 'MESH'
    if change == 'ru': session['values']['gateway'] = 'gateway-ru'
    if change == 'disconnected': session['values']['state'] = 'DISCONNECTED'
    if change == 'stale': session['received_at'] = NOW - 181
    if change == 'future': session['received_at'] = NOW + 1
    if change == 'expired': session['expires_at'] = NOW
    if change == 'old_sample': session['age_at_receive_ms'] = 181000
    assert collector.geoip_targets([entry], registry, NOW) == []


def test_sampler_only_returns_requested_authenticated_peer(registry, peer_source):
    targets = collector.geoip_targets([row()], registry, NOW)
    result = collector.sample_awg_peers('nl-amsterdam-1', targets, peer_source[1], peer_source[0], peer_command, NOW)
    assert result['status'] == 'ok'
    assert result['peers'] == [dict(target=targets[0], endpoint='1.1.1.1:51820', handshake=NOW - 10)]
    assert collector.sample_awg_peers('nl-amsterdam-2', targets, peer_source[1], peer_source[0], peer_command, NOW)['status'] == 'unavailable'
    assert collector.sample_awg_peers('nl-amsterdam-1', targets, '0' * 64, peer_source[0], peer_command, NOW)['status'] == 'unavailable'


@pytest.mark.parametrize('failure', ['duplicate', 'timeout', 'stale', 'future', 'missing', 'oversized'])
def test_sampler_failure_does_not_export_addresses(registry, peer_source, failure):
    targets = collector.geoip_targets([row()], registry, NOW)
    def run(command, **options):
        if failure == 'timeout':
            raise subprocess.TimeoutExpired(command, 4)
        result = peer_command(command, **options)
        if failure == 'duplicate': result.stdout *= 2
        if failure == 'oversized': result.stdout = b'x' * 2_000_001
        if failure == 'missing': result.stdout = b''
        if command[-1] == 'latest-handshakes' and failure in ('stale', 'future'):
            result.stdout = (PUBLIC + ' ' + str(NOW - 181 if failure == 'stale' else NOW + 1)).encode()
        return result
    result = collector.sample_awg_peers('nl-amsterdam-1', targets, peer_source[1], peer_source[0], run, NOW)
    assert result['peers'] == []
    assert '1.1.1.1' not in json.dumps(result)


class Database:
    def __init__(self, root, now):
        self.now = now

    def close(self):
        pass

    def lookup(self, address, *, origin, sampled_at):
        assert address == '1.1.1.1' and origin == 'authenticated_awg_peer'
        result = geoip.unknown('none', self.now, origin)
        result.update(status='available', city='Controlled city', country='AU', asn=13335,
                      sampled_at=sampled_at, expires_at=sampled_at + 604800)
        return result


@pytest.mark.parametrize('source', collector.NL_SOURCES)
def test_basic_nl_passes_asn_only_without_implicit_consent(registry, monkeypatch, source):
    class AsnOnly(Database):
        def lookup(self, address, *, origin, sampled_at, asn_only=False):
            assert asn_only
            result = geoip.unknown('none', self.now, origin)
            result.update(status='available', asn=13335, organization='Network only',
                          sampled_at=sampled_at, expires_at=sampled_at + 604800)
            return result
    monkeypatch.setattr(geoip, 'Database', AsnOnly)
    entry = row(source)
    entry.update(consent='not_requested', processing_mode='automatic_basic', policy_version='basic-2026-11-v1')
    target, = collector.geoip_targets([entry], registry, NOW)
    samples = {source: dict(source=source, observed_at=NOW, status='ok',
        peers=[dict(target=target, endpoint='1.1.1.1:51820', handshake=NOW - 10)])}
    result, = collector.enrich_nl_peers([entry], samples, geoip, registry, now=NOW)
    assert result['geoip']['asn'] == 13335 and result['geoip']['city'] is None
    assert result['consent'] == 'not_requested' and '1.1.1.1' not in json.dumps(result)


@pytest.mark.parametrize('source', collector.NL_SOURCES)
def test_enrichment_discards_ip_and_binds_exact_consent_sequence(registry, monkeypatch, source):
    monkeypatch.setattr(geoip, 'Database', Database)
    entry = row(source)
    target = collector.geoip_targets([entry], registry, NOW)[0]
    samples = {source: dict(source=source, observed_at=NOW, status='ok',
        peers=[dict(target=target, endpoint='1.1.1.1:51820', handshake=NOW - 10)])}
    result = collector.enrich_nl_peers([entry], samples, geoip, registry, now=NOW)
    assert result[0]['geoip']['city'] == 'Controlled city'
    assert not any(secret in json.dumps(result) for secret in ('1.1.1.1', PUBLIC, 'endpoint'))
    changed = row(source)
    changed['consent_epoch'] = 2
    result = collector.enrich_nl_peers([changed], samples, geoip, registry, now=NOW)
    assert result[0]['geoip']['city'] is None
    revoked = row(source)
    revoked['consent'] = 'revoked'
    assert collector.enrich_nl_peers([revoked], samples, geoip, registry, now=NOW)[0]['geoip'] is None


@pytest.mark.parametrize('change', ['source', 'clock', 'stale', 'sequence', 'public', 'duplicate', 'unavailable'])
def test_wrong_node_key_sequence_or_time_cannot_supply_location(registry, monkeypatch, change):
    monkeypatch.setattr(geoip, 'Database', Database)
    target = collector.geoip_targets([row()], registry, NOW)[0]
    sample = dict(source='nl-amsterdam-1', observed_at=NOW, status='ok',
        peers=[dict(target=target, endpoint='1.1.1.1:51820', handshake=NOW - 10)])
    if change == 'source': sample['source'] = 'nl-amsterdam-2'
    if change == 'clock': sample['observed_at'] = NOW + 1
    if change == 'stale': sample['peers'][0]['handshake'] = NOW - 181
    if change == 'sequence': target['sequence'] += 1
    if change == 'public': target['public'] = 'unrelated'
    if change == 'duplicate': sample['peers'] *= 2
    if change == 'unavailable': sample['status'] = 'unavailable'
    result = collector.enrich_nl_peers([row()], {'nl-amsterdam-1': sample}, geoip, registry, now=NOW)
    assert result[0]['geoip']['city'] is None


@pytest.mark.parametrize('outcome', ['available', 'nl_timeout', 'refresh_timeout', 'refresh_revoked', 'no_targets'])
def test_orchestrator_rechecks_canonical_then_seals_only_sanitized_export(tmp_path, monkeypatch, outcome):
    root = Path(__file__).resolve().parents[1]
    monkeypatch.syspath_prepend(str(root / 'control_plane'))
    from collect_technical_metadata import collect
    local = tmp_path / '.local'
    local.mkdir(mode=0o700)
    key = b'synthetic-hmac-test-key-32-bytes'
    assert len(key) == 32
    config = dict(python='/isolated/python', archive='/isolated/runtime.pyz', archive_sha256='a' * 64)
    for name, value in [('technical-metadata-source.json', json.dumps(config).encode()),
                        ('transport-source.json', json.dumps(dict(archive_sha256='c' * 64)).encode()),
                        ('inventory-hmac.key', key)]:
        (local / name).write_bytes(value)
        (local / name).chmod(0o600)
    code = tmp_path / 'apps/console'
    code.mkdir(parents=True)
    (code / 'technical_metadata_collector.py').write_text('')
    entry = row()
    target = dict(device=entry['device'], public=PUBLIC, source='nl-amsterdam-1', consent_epoch=1, sequence=1)
    data = dict(schema=1, source='gateway-ru', status='ok', observed_at=NOW, devices=[entry])
    calls = []
    def run(command, **options):
        calls.append(command)
        assert key not in options['input']
        assert 0 < options['timeout'] <= 45
        if len(calls) == 1:
            assert b'include_targets=True' in options['input']
            output = dict(data, _targets=[] if outcome == 'no_targets' else [target])
        elif len(calls) == 2:
            assert command[-2] == 'root@185.10.158.212'
            assert options['timeout'] <= 15
            if outcome == 'nl_timeout':
                raise subprocess.TimeoutExpired(command, options['timeout'])
            output = dict(source='nl-amsterdam-1', status='ok', observed_at=NOW,
                peers=[dict(target=target, endpoint='1.1.1.1:51820', handshake=NOW - 10)])
        else:
            assert len(calls) == 3 and b'peer_observations=' in options['input']
            assert (b'1.1.1.1' in options['input']) == (outcome != 'nl_timeout')
            if outcome == 'refresh_timeout':
                raise subprocess.TimeoutExpired(command, options['timeout'])
            output = data
            if outcome == 'refresh_revoked':
                output = json.loads(json.dumps(data))
                output['devices'][0].update(consent='revoked', consent_epoch=2, sequence=2, observations={}, geoip=None)
        return SimpleNamespace(stdout=json.dumps(output).encode())
    before = set(local.iterdir())
    result = collect(base=tmp_path, run=run)
    assert len(calls) == (1 if outcome == 'no_targets' else 3) and set(local.iterdir()) == before
    assert not any(value.encode() in result for value in (entry['device'], PUBLIC, '1.1.1.1', '_targets'))
    assert len(json.loads(result)['devices'][0]['pseudonym']) == 64
    assert (json.loads(result)['devices'][0]['consent'] == 'revoked') == (outcome == 'refresh_revoked')
