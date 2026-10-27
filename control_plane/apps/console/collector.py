"""Standalone, read-only collector; run over authenticated SSH stdin, never deploy."""
from datetime import datetime, timezone
import hashlib
import hmac
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess

REGISTRY = Path('/opt/apps/family_connect/friends-access/access.db')
SERVICES = ('family-connect-friends-http-candidate.service', 'family-connect-friends-awg.service',
    'family-connect-friends-tcp.service', 'family-connect-server-load.service',
    'family-connect-restricted-bootstrap.service', 'family-connect-reticulum.service',
    'family-connect-mailbox.service', 'wg-quick@fcams.service')


def instant(epoch):
    return datetime.fromtimestamp(epoch, timezone.utc).isoformat() if epoch is not None else None


def registry_rows(path, key):
    database = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True, timeout=5)
    database.row_factory = sqlite3.Row
    try:
        database.execute('PRAGMA query_only=ON')
        database.execute('BEGIN')
        rows = database.execute('''SELECT d.device,d.revoked,s.version_code,s.last_seen,
            EXISTS(SELECT 1 FROM invites i WHERE i.device=d.device AND i.revoked=0) AS activated,
            EXISTS(SELECT 1 FROM invites i WHERE i.device=d.device AND i.revoked!=0) AS invite_revoked
            FROM devices d LEFT JOIN device_support s ON s.device=d.device ORDER BY d.device LIMIT 10001''').fetchall()
        if len(rows) > 10000:
            raise ValueError('INVENTORY_LIMIT')
        has_ack = database.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='restricted_readiness_results'").fetchone()
        result = []
        for row in rows:
            version, seen = row['version_code'], row['last_seen']
            source = 'support' if version is not None else 'unknown'
            if has_ack:
                ack = database.execute('SELECT ack,ack_at FROM restricted_readiness_results WHERE device=? AND ack IS NOT NULL ORDER BY ack_at DESC LIMIT 1', (row['device'],)).fetchone()
                if ack and ack['ack_at'] is not None and ack['ack_at'] >= (seen or 0):
                    payload = json.loads(ack['ack'])
                    if type(payload.get('version_code')) is int:
                        version, seen, source = payload['version_code'], ack['ack_at'], 'readiness_ack'
            result.append(dict(pseudonym=hmac.new(key, row['device'].encode(), hashlib.sha256).hexdigest(),
                activated=bool(row['activated']) and not bool(row['revoked']),
                revoked=bool(row['revoked'] or row['invite_revoked']), version_code=version,
                version_source=source, last_seen=instant(seen)))
        return result
    finally:
        database.rollback()
        database.close()


def collect(source, key, path=REGISTRY):
    if source not in ('gateway-ru', 'gateway-nl') or len(key) != 32:
        raise ValueError('INVALID_COLLECTOR_INPUT')
    data = dict(schema=1, scope='production', source=source,
        observed_at=datetime.now(timezone.utc).isoformat(), registry_status='unavailable', devices=[])
    if path.is_file() and not path.is_symlink():
        try:
            data['devices'] = registry_rows(path, key)
            data['registry_status'] = 'ok'
        except (sqlite3.Error, ValueError, OverflowError):
            pass
    server = dict(load_1m=None, memory_used_percent=None, disk_used_percent=None, uptime_seconds=None, services={})
    try:
        server['load_1m'] = round(os.getloadavg()[0], 3)
        memory = {name: int(value.split()[0]) for name, value in
            (line.split(':', 1) for line in Path('/proc/meminfo').read_text().splitlines())}
        server['memory_used_percent'] = round(100 * (1 - memory['MemAvailable'] / memory['MemTotal']), 2)
        disk = shutil.disk_usage('/opt/apps/family_connect')
        server['disk_used_percent'] = round(100 * disk.used / disk.total, 2)
        server['uptime_seconds'] = int(float(Path('/proc/uptime').read_text().split()[0]))
    except (OSError, KeyError, ValueError):
        pass
    for service in SERVICES:
        try:
            output = subprocess.run(['systemctl', 'show', service, '--property=LoadState,ActiveState'],
                capture_output=True, text=True, timeout=3).stdout
            properties = dict(line.split('=', 1) for line in output.splitlines() if '=' in line)
            status = 'not_found' if properties.get('LoadState') == 'not-found' else properties.get('ActiveState', 'unknown')
        except (OSError, subprocess.TimeoutExpired):
            status = 'unknown'
        server['services'][service] = status if status in ('active', 'inactive', 'failed', 'activating', 'deactivating', 'not_found') else 'unknown'
    data['server'] = server
    return data
