"""Runs in an isolated operator SSH process, never in a Django request."""
import hashlib
import importlib
import base64
from contextlib import closing
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import time
import zipimport

NL_SOURCES = ('nl-amsterdam-1', 'nl-amsterdam-2')
REGISTRY = Path('/opt/apps/family_connect/friends-access/access.db')
GEOIP_ROOT = Path('/opt/apps/family_connect/geoip')


def geoip_targets(rows, registry=REGISTRY, now=None):
    now = int(time.time()) if now is None else now
    candidates = []
    for row in rows:
        session = row.get('observations', {}).get('session', {})
        values = session.get('values', {})
        if (row['consent'] in ('enabled', 'not_requested') and values.get('gateway') in NL_SOURCES and
                values.get('transport') == 'AWG' and values.get('state') == 'CONNECTED' and
                now - 180 <= session.get('received_at', 0) <= now and
                session.get('expires_at', 0) > now and
                now - session['received_at'] + session.get('age_at_receive_ms', 0) / 1000 <= 180):
            candidates.append(row)
    if not candidates:
        return []
    with closing(sqlite3.connect('file:' + str(registry.resolve()) + '?mode=ro', uri=True, timeout=2)) as connection:
        bindings = dict(connection.execute('SELECT device,wg FROM devices WHERE revoked=0'))
    targets = []
    for row in candidates:
        public = bindings.get(row['device'])
        if not isinstance(public, str) or not re.fullmatch(r'[A-Za-z0-9+/]{43}=', public):
            continue
        if len(base64.b64decode(public, validate=True)) != 32:
            continue
        targets.append(dict(device=row['device'], public=public, consent_epoch=row['consent_epoch'],
                            sequence=row['sequence'], source=row['observations']['session']['values']['gateway']))
    if len(targets) > 5000 or len({item['public'] for item in targets}) != len(targets):
        raise ValueError('Ambiguous peer binding')
    return targets


def sample_awg_peers(source, targets, expected_sha256, root=Path('/opt/apps/family_connect/friends-awg'),
                     command=subprocess.run, now=None):
    now = int(time.time()) if now is None else now
    result = dict(source=source, observed_at=now, status='unavailable', peers=[])
    try:
        if source not in NL_SOURCES or not targets or len(targets) > 5000:
            return result
        archive, state_path = root / 'paid-transport.pyz', root / 'transport-state.json'
        if (archive.is_symlink() or state_path.is_symlink() or archive.stat().st_size > 64 * 1024 * 1024 or
                state_path.stat().st_size > 8_000_000 or
                hashlib.sha256(archive.read_bytes()).hexdigest() != expected_sha256):
            return result
        state = json.loads(state_path.read_text())
        if state['schema'] != 1 or state['node'] != source:
            return result
        if len({item['public'] for item in targets}) != len(targets):
            return result
        for target in targets:
            if (target['source'] != source or not re.fullmatch('[0-9a-f]{32}', target['device']) or
                    state['records'].get(target['device'], {}).get('decision', {}).get('public_key') != target['public']):
                return result
        observed = {}
        for field in ('endpoints', 'latest-handshakes'):
            reply = command([str(root / 'awg'), 'show', 'fcopen31', field],
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
        for target in targets:
            endpoint = observed['endpoints'].get(target['public'])
            handshake = int(observed['latest-handshakes'].get(target['public'], 0))
            if endpoint and len(endpoint) <= 128 and now - 180 <= handshake <= now:
                result['peers'].append(dict(target=target, endpoint=endpoint, handshake=handshake))
        result['status'] = 'ok'
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        result.update(status='unavailable', peers=[])
    return result


def enrich_nl_peers(rows, samples, geo, registry=REGISTRY, database_root=GEOIP_ROOT, now=None):
    now = int(time.time()) if now is None else now
    targets = {item['device']: item for item in geoip_targets(rows, registry, now)}
    if not targets:
        return rows
    with closing(geo.Database(database_root, now)) as database:
        for row in rows:
            target = targets.get(row['device'])
            if target is None:
                continue
            row['geoip'] = geo.unknown('peer_source_unavailable', now)
            sample = samples.get(target['source'], {})
            if (type(sample) is not dict or sample.get('source') != target['source'] or sample.get('status') != 'ok' or
                    type(sample.get('observed_at')) is not int or not now - 180 <= sample['observed_at'] <= now or
                    type(sample.get('peers')) is not list or len(sample['peers']) > 5000 or
                    not all(type(peer) is dict for peer in sample['peers'])):
                continue
            matching = [peer for peer in sample['peers'] if peer.get('target') == target]
            row['geoip'] = geo.unknown('no_suitable_direct_observation', now)
            if len(matching) != 1:
                continue
            peer = matching[0]
            address = geo.peer_address(peer.get('endpoint'))
            handshake = peer.get('handshake')
            if type(handshake) is not int or not now - 180 <= handshake <= sample['observed_at']:
                row['geoip'] = geo.unknown('peer_observation_stale', now)
            elif address:
                options = dict(asn_only=True) if row.get('processing_mode') == 'automatic_basic' else {}
                row['geoip'] = database.lookup(address, origin='authenticated_awg_peer', sampled_at=handshake, **options)
    return rows


def collect_technical_metadata(config, include_targets=False, peer_observations=None):
    result = dict(schema=1, source='gateway-ru', observed_at=int(time.time()), status='unavailable', devices=[])
    try:
        archive = Path(config['archive']).resolve(strict=True)
        if hashlib.sha256(archive.read_bytes()).hexdigest() != config['archive_sha256']:
            return result
        name = 'control.friends.technical_metadata'
        if any(key == 'control' or key.startswith('control.') for key in sys.modules):
            return result
        sys.path.insert(0, str(archive))
        try:
            module = importlib.import_module(name)
            expected = str(archive / 'control/friends/technical_metadata.py')
            if (module.__file__ != expected or module.__spec__.origin != expected
                    or not isinstance(module.__spec__.loader, zipimport.zipimporter)
                    or Path(module.__spec__.loader.archive).resolve() != archive):
                return result
            result['devices'] = module.read_all(Path('/opt/apps/family_connect/friends-access/technical-metadata.sqlite'), result['observed_at'])
            geo = importlib.import_module('control.friends.geoip')
            if geo.__file__ != str(archive / 'control/friends/geoip.py'):
                raise ValueError('GeoIP module outside verified archive')
            result['devices'] = geo.enrich_ru_peers(result['devices'],
                REGISTRY, GEOIP_ROOT, now=result['observed_at'])
            if include_targets:
                try:
                    result['_targets'] = geoip_targets(result['devices'], now=result['observed_at'])
                except (OSError, ValueError, sqlite3.Error):
                    result['_targets'] = []
            if peer_observations is not None:
                try:
                    result['devices'] = enrich_nl_peers(result['devices'], peer_observations, geo, now=result['observed_at'])
                except (OSError, ValueError, sqlite3.Error):
                    pass
        finally:
            sys.path.pop(0)
        result['status'] = 'ok'
    except (OSError, ValueError, ImportError, KeyError, TypeError, sqlite3.Error):
        result.update(status='unavailable', devices=[])
        result.pop('_targets', None)
    return result
