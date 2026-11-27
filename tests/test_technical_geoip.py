from contextlib import closing
import gzip
import hashlib
import io
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
from types import SimpleNamespace

import pytest

from control.friends import geoip
from scripts import update_geoip as updater

NOW = 1794700000


class Reader:
    def __init__(self, path):
        self.kind = Path(path).stem

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        pass

    def metadata(self):
        return SimpleNamespace(database_type='DBIP-' + self.kind, node_count=1, ip_version=6, build_epoch=1793501546)

    def get(self, address):
        if self.kind == 'city':
            return dict(country=dict(iso_code='AU'), city=dict(names=dict(en='Controlled city')),
                        subdivisions=[dict(names=dict(en='Controlled region'))], location=dict(latitude=12, longitude=34))
        return dict(autonomous_system_number=13335, autonomous_system_organization='Controlled network')


@pytest.fixture
def database(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, 'maxminddb', SimpleNamespace(open_database=Reader))
    monkeypatch.setattr(updater.shutil, 'disk_usage', lambda root: SimpleNamespace(free=2**40))
    root = tmp_path / 'geoip'
    def fetch(kind, version, destination, opener):
        destination.write_bytes(b'controlled-reader-' + kind.encode())
    value = updater.update(root, '2026-11', fetch=fetch)
    return root, value, fetch


def test_local_pair_returns_only_needed_fields(database):
    with closing(geoip.Database(database[0], NOW)) as reader:
        result = reader.lookup('1.1.1.1', origin='authenticated_awg_peer', sampled_at=NOW - 30)
    assert result['status'] == 'available' and result['city'] == 'Controlled city'
    assert result['asn'] == 13335 and result['retail_isp'] is None
    assert result['sampled_at'] == NOW - 30 and result['received_at'] == NOW
    assert result['expires_at'] == NOW - 30 + 7 * 86400
    assert result['database']['version'] == '2026-11'
    assert set(result) == geoip.FIELDS
    assert not any(field in json.dumps(result) for field in ('1.1.1.1', 'latitude', 'longitude'))


def test_basic_asn_never_queries_city_database(database, monkeypatch):
    original = Reader.get
    def no_city(self, address):
        assert self.kind != 'city', 'basic must not query detailed geography'
        return original(self, address)
    monkeypatch.setattr(Reader, 'get', no_city)
    with closing(geoip.Database(database[0], NOW)) as reader:
        result = reader.lookup('1.1.1.1', origin='authenticated_awg_peer', sampled_at=NOW - 30, asn_only=True)
        assert reader.lookup('1.1.1.1', origin='relay', sampled_at=NOW, asn_only=True)['status'] == 'unavailable'
    assert result['asn'] == 13335 and result['status'] == 'available'
    assert all(result[name] is None for name in ('city', 'country', 'region', 'retail_isp'))
    assert result['expires_at'] == NOW - 30 + 7 * 86400


@pytest.mark.parametrize('address,origin,age,reason', [
    ('1.1.1.1', 'unknown', 0, 'origin_unverified'),
    ('1.1.1.1', 'relay', 0, 'origin_unverified'),
    ('185.251.89.19', 'authenticated_awg_peer', 0, 'known_vpn_exit'),
    ('127.0.0.1', 'authenticated_awg_peer', 0, 'non_public_address'),
    ('10.1.2.3', 'authenticated_awg_peer', 0, 'non_public_address'),
    ('1.1.1.1', 'authenticated_awg_peer', 181, 'peer_observation_stale'),
    ('1.1.1.1', 'authenticated_awg_peer', -1, 'peer_observation_stale'),
])
def test_untrusted_vpn_relay_local_and_old_addresses_never_geolocated(database, address, origin, age, reason):
    with closing(geoip.Database(database[0], NOW)) as reader:
        result = reader.lookup(address, origin=origin, sampled_at=NOW-age)
    assert result['reason'] == reason and result['city'] is None and result['asn'] is None


@pytest.mark.parametrize('endpoint,expected', [('1.1.1.1:51820', '1.1.1.1'),
    ('[2606:4700:4700::1111]:51820', '2606:4700:4700::1111'), ('(none)', None),
    ('[fe80::1%eth0]:123', None), ('1.1.1.1:65536', None), ('not-an-address:123', None)])
def test_peer_endpoint_public_api_parsing(endpoint, expected):
    assert geoip.peer_address(endpoint) == expected


def test_missing_corrupt_stale_and_city_miss_continue(database, monkeypatch):
    root, manifest, fetch = database
    with closing(geoip.Database(root / 'missing', NOW)) as reader:
        assert reader.lookup('1.1.1.1', origin='authenticated_awg_peer', sampled_at=NOW)['reason'] == 'database_missing'
    with closing(geoip.Database(root, NOW + 60*86400)) as reader:
        assert reader.error == 'database_stale'
    monkeypatch.setattr(Reader, 'get', lambda self, address: {})
    with closing(geoip.Database(root, NOW)) as reader:
        assert reader.lookup('1.1.1.1', origin='authenticated_awg_peer', sampled_at=NOW)['reason'] == 'lookup_miss'
    path = root / manifest['directory'] / 'city.mmdb'
    path.chmod(0o600); path.write_bytes(b'corrupt')
    with closing(geoip.Database(root, NOW)) as reader:
        assert reader.error == 'database_invalid'


def test_peer_bound_to_canonical_device_key_not_matching_ip(database, tmp_path):
    registry = tmp_path / 'access.db'
    with sqlite3.connect(registry) as connection:
        connection.execute('CREATE TABLE devices(device TEXT, wg TEXT, revoked INTEGER)')
        connection.executemany('INSERT INTO devices VALUES (?,?,?)', [('owned', 'owned-key', 0), ('other', 'other-key', 0)])
    def entry(device):
        return dict(device=device, consent='enabled', observations=dict(session=dict(received_at=NOW,
            values=dict(gateway='gateway-ru', transport='AWG', state='CONNECTED'))))
    def run(command, **kwargs):
        assert command[-1] in ('endpoints', 'latest-handshakes')
        assert kwargs == dict(capture_output=True, check=True, timeout=4)
        value = '1.1.1.1:51820' if command[-1] == 'endpoints' else str(NOW-10)
        return subprocess.CompletedProcess(command, 0, stdout=('owned-key\t' + value + '\n').encode())
    rows = geoip.enrich_ru_peers([entry('owned'), entry('other'), dict(device='off', consent='revoked')],
        registry, database[0], command=run, now=NOW)
    assert rows[0]['geoip']['status'] == 'available'
    assert rows[1]['geoip']['reason'] == 'no_suitable_direct_observation'
    assert rows[2]['geoip'] is None
    assert '1.1.1.1' not in json.dumps(rows)
    with sqlite3.connect(registry) as connection:
        connection.execute('UPDATE devices SET revoked=1')
    assert geoip.enrich_ru_peers([entry('owned')], registry, database[0], command=run, now=NOW)[0]['geoip']['city'] is None


def test_updater_pair_failure_preserves_previous_and_bounds_sets(database):
    root, first, fetch = database
    def fail(kind, version, destination, opener):
        if kind == 'asn':
            raise OSError('controlled unavailable')
        fetch(kind, version, destination, opener)
    with pytest.raises(OSError):
        updater.update(root, '2026-11', fetch=fail)
    assert json.loads((root/'current.json').read_text()) == first
    assert not list(root.glob('.pending-*'))
    assert json.loads((root/'update-status.json').read_text())['status'] == 'failed'
    second = updater.update(root, '2026-11', fetch=fetch)
    third = updater.update(root, '2026-11', fetch=fetch)
    assert {path.name for path in root.glob('set-*')} == {second['directory'], third['directory']}
    assert json.loads((root/'previous.json').read_text()) == second


def test_updater_checks_disk_before_fetch(database, monkeypatch):
    root, manifest, fetch = database
    monkeypatch.setattr(updater.shutil, 'disk_usage', lambda root: SimpleNamespace(free=100))
    with pytest.raises(ValueError, match='space'):
        updater.update(root, '2026-11', fetch=lambda *args: pytest.fail('must not download'))
    assert json.loads((root/'current.json').read_text()) == manifest


def test_download_bounded_decompression_and_redirect(tmp_path, monkeypatch):
    class Response(io.BytesIO):
        url = 'https://download.db-ip.com/free/controlled.gz'
    opener = SimpleNamespace(open=lambda request, timeout: Response(gzip.compress(b'large'*20)))
    monkeypatch.setattr(updater, 'MAX_EXPANDED', 20)
    with pytest.raises(ValueError, match='Expanded'):
        updater.download('city', '2026-11', tmp_path/'city.mmdb', opener)
    with pytest.raises(ValueError, match='origin'):
        updater.OfficialRedirect().redirect_request(None, None, 302, '', {}, 'https://attacker.invalid/file')
