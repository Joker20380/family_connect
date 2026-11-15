"""Local DB-IP enrichment. Addresses are ephemeral, never returned or persisted."""
from contextlib import ExitStack, closing
import hashlib
import ipaddress
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import time

MAX_AGE = 45 * 86400
MAX_DATABASE = 256 * 1024 * 1024
GATEWAY_ADDRESSES = frozenset(('185.251.89.19', '186.246.45.246', '185.10.158.212', '185.10.158.196'))
FIELDS = {'status', 'reason', 'source', 'origin', 'sampled_at', 'received_at', 'expires_at',
          'country', 'region', 'city', 'asn', 'organization', 'retail_isp', 'database'}


def unknown(reason, now, origin='unknown'):
    return dict(status='unavailable', reason=reason, source='db_ip_lite', origin=origin,
                sampled_at=now, received_at=now, expires_at=now + 7 * 86400,
                country=None, region=None, city=None, asn=None, organization=None,
                retail_isp=None, database=None)


def text(value):
    if not isinstance(value, str) or not value.strip() or len(value) > 160 or not all(char.isprintable() for char in value):
        return None
    return value


def peer_address(endpoint):
    if not isinstance(endpoint, str) or len(endpoint) > 128:
        return None
    try:
        host, port = endpoint.rsplit(':', 1)
        if not port.isdigit() or not 1 <= int(port) <= 65535:
            return None
        if host.startswith('[') and host.endswith(']'):
            host = host[1:-1]
        if '%' in host:
            return None
        return str(ipaddress.ip_address(host))
    except ValueError:
        return None


class Database:
    def __init__(self, root, now=None):
        self.root, self.now = Path(root), int(time.time()) if now is None else now
        self.stack = ExitStack()
        self.readers = {}
        self.version = None
        self.error = 'database_missing'
        try:
            manifest = self.root / 'current.json'
            if manifest.is_symlink() or manifest.stat().st_size > 8192:
                raise ValueError('Manifest bound')
            value = json.loads(manifest.read_text())
            if set(value) != {'schema', 'version', 'directory', 'databases'} or value['schema'] != 1:
                raise ValueError('Manifest schema')
            if not re.fullmatch(r'\d{4}-\d{2}', value['version']) or not re.fullmatch(r'set-[0-9a-f]{32}', value['directory']):
                raise ValueError('Manifest path')
            if set(value['databases']) != {'city', 'asn'}:
                raise ValueError('Database pair required')
            import maxminddb
            for kind, description in value['databases'].items():
                path = self.root / value['directory'] / (kind + '.mmdb')
                if path.parent.is_symlink() or path.is_symlink() or not 0 < path.stat().st_size <= MAX_DATABASE:
                    raise ValueError('Database size')
                with path.open('rb') as handle:
                    if hashlib.file_digest(handle, 'sha256').hexdigest() != description['sha256']:
                        raise ValueError('Database checksum')
                reader = self.stack.enter_context(maxminddb.open_database(str(path)))
                metadata = reader.metadata()
                if kind not in metadata.database_type.lower() or metadata.node_count <= 0 or metadata.ip_version not in (4, 6):
                    raise ValueError('Database structure')
                if metadata.build_epoch != description['build_epoch'] or metadata.build_epoch > self.now + 86400:
                    raise ValueError('Database epoch')
                self.readers[kind] = reader
            self.version = dict(version=value['version'], city_sha256=value['databases']['city']['sha256'],
                                asn_sha256=value['databases']['asn']['sha256'])
            self.error = 'database_stale' if any(self.now - item['build_epoch'] > MAX_AGE for item in value['databases'].values()) else None
        except FileNotFoundError:
            self.error = 'database_missing'
        except ImportError:
            self.error = 'reader_unavailable'
        except Exception:
            self.error = 'database_invalid'

    def close(self):
        self.stack.close()

    def lookup(self, address, *, origin, sampled_at):
        result = unknown('origin_unverified', self.now, origin)
        if origin not in ('authenticated_awg_peer', 'authenticated_direct_service'):
            return result
        try:
            address = ipaddress.ip_address(address)
            if not address.is_global:
                result['reason'] = 'non_public_address'
                return result
            if str(address) in GATEWAY_ADDRESSES:
                result.update(reason='known_vpn_exit', origin='vpn_exit')
                return result
            if not self.now - 180 <= sampled_at <= self.now:
                result['reason'] = 'peer_observation_stale'
                return result
            result.update(sampled_at=sampled_at, expires_at=sampled_at + 7 * 86400, database=self.version)
            if self.error:
                result['reason'] = self.error
                return result
            city, asn = self.readers['city'].get(str(address)) or {}, self.readers['asn'].get(str(address)) or {}
            country = text(city.get('country', {}).get('iso_code'))
            if country and not re.fullmatch('[A-Z]{2}', country):
                country = None
            subdivisions = city.get('subdivisions') or []
            number = asn.get('autonomous_system_number')
            result.update(country=country, city=text(city.get('city', {}).get('names', {}).get('en')),
                          region=text(subdivisions[0].get('names', {}).get('en')) if subdivisions else None,
                          asn=number if type(number) is int and 0 < number <= 4294967295 else None,
                          organization=text(asn.get('autonomous_system_organization')))
            result.update(status='available' if result['city'] and result['asn'] else 'partial',
                          reason='none' if result['city'] and result['asn'] else 'no_asn' if result['city'] else 'no_city' if country else 'lookup_miss')
        except Exception:
            result = unknown('lookup_failed', self.now, origin)
        return result


def enrich_ru_peers(rows, registry, database_root, *, command=subprocess.run, now=None):
    now = int(time.time()) if now is None else now
    eligible = [row for row in rows if row['consent'] == 'enabled' and
                row.get('observations', {}).get('session', {}).get('values', {}).get('gateway') == 'gateway-ru' and
                row['observations']['session']['values'].get('transport') == 'AWG' and
                row['observations']['session']['values'].get('state') == 'CONNECTED' and
                now - row['observations']['session']['received_at'] <= 180]
    for row in rows:
        row['geoip'] = None if row['consent'] == 'revoked' else unknown('no_suitable_direct_observation', now)
    if not eligible:
        return rows
    try:
        with closing(sqlite3.connect('file:' + str(Path(registry).resolve()) + '?mode=ro', uri=True)) as registry_db:
            bindings = dict(registry_db.execute('SELECT device,wg FROM devices WHERE revoked=0'))
        observed = {}
        for field in ('endpoints', 'latest-handshakes'):
            reply = command(['/opt/apps/family_connect/friends-awg/awg', 'show', 'fcopen31', field],
                            capture_output=True, check=True, timeout=4)
            if len(reply.stdout) > 2_000_000:
                raise ValueError('Peer bound')
            values = {}
            for line in reply.stdout.decode().splitlines():
                public, value = line.split()
                if public in values:
                    raise ValueError('Duplicate peer')
                values[public] = value
            observed[field] = values
        with closing(Database(database_root, now)) as database:
            for row in eligible:
                public = bindings.get(row['device'])
                endpoint = observed['endpoints'].get(public)
                handshake = int(observed['latest-handshakes'].get(public, 0))
                address = peer_address(endpoint)
                if public and address and now - 180 <= handshake <= now:
                    row['geoip'] = database.lookup(address, origin='authenticated_awg_peer', sampled_at=handshake)
    except (OSError, ValueError, sqlite3.Error, subprocess.SubprocessError):
        for row in eligible:
            row['geoip'] = unknown('peer_source_unavailable', now)
    return rows
