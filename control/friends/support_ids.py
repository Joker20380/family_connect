"""Non-secret registration aliases; never credentials or an enrollment path."""
import json
import re
import secrets
import sqlite3

from .access import Rejected

ALPHABET = '23456789ABCDEFGHJKMNPQRSTVWXYZ'
PATTERN = r'FC-[23456789ABCDEFGHJKMNPQRSTVWXYZ]{4}-[23456789ABCDEFGHJKMNPQRSTVWXYZ]{4}'
VERSION = r'[A-Za-z0-9._-]{1,64}'


def normalize(value):
    if not isinstance(value, str) or not re.fullmatch(PATTERN, value.strip().upper()):
        raise ValueError('Invalid Support ID')
    return value.strip().upper()


def create(database):
    database.execute('CREATE TABLE IF NOT EXISTS device_support ('
                     'device TEXT PRIMARY KEY REFERENCES devices(device), support_id TEXT UNIQUE NOT NULL, '
                     'platform TEXT, app_version TEXT, version_code INTEGER, last_seen INTEGER, observation_source TEXT)')
    database.execute('CREATE TABLE IF NOT EXISTS field_support_audit ('
                     'id INTEGER PRIMARY KEY, timestamp INTEGER NOT NULL, support_id TEXT NOT NULL, '
                     'previous_state INTEGER NOT NULL, new_state INTEGER NOT NULL, outcome TEXT NOT NULL)')


def registered(database, device):
    if not database.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='device_support'").fetchone():
        return None
    row = database.execute('SELECT support_id FROM device_support WHERE device=?', (device,)).fetchone()
    if row is not None:
        return row['support_id']
    if not database.execute('SELECT 1 FROM devices WHERE device=?', (device,)).fetchone():
        raise Rejected()
    for attempt in range(32):
        random = ''.join(secrets.choice(ALPHABET) for index in range(8))
        support = 'FC-' + random[:4] + '-' + random[4:]
        try:
            database.execute('INSERT INTO device_support(device,support_id) VALUES (?,?)', (device, support))
            return support
        except sqlite3.IntegrityError:
            continue
    raise RuntimeError('Support ID allocation unavailable')


def receipt(database, device):
    if not database.execute("SELECT 1 FROM sqlite_master WHERE name='restricted_readiness_results'").fetchone():
        return None
    row = database.execute('SELECT ack,ack_at,expires FROM restricted_readiness_results '
                           'WHERE device=? AND ack IS NOT NULL ORDER BY ack_at DESC LIMIT 1', (device,)).fetchone()
    if row is None:
        return None
    try:
        value = json.loads(row['ack'])
        if (not isinstance(value.get('app_version'), str) or not re.fullmatch(VERSION, value['app_version'])
                or type(value.get('version_code')) is not int or not 1 <= value['version_code'] <= 2147483647):
            return None
        return dict(version=value['app_version'], code=value['version_code'], seen=row['ack_at'],
                    expires=row['expires'], ready=value.get('result') == 'READY')
    except (ValueError, TypeError):
        return None


def backfill(access):
    with access.db() as database:
        create(database)
        for row in database.execute('SELECT device FROM devices').fetchall():
            device = row['device']
            registered(database, device)
            observed = receipt(database, device)
            if observed is not None:
                database.execute('UPDATE device_support SET app_version=?,version_code=?,last_seen=?,observation_source=? '
                                 'WHERE device=? AND (last_seen IS NULL OR last_seen<?)',
                                 (observed['version'], observed['code'], observed['seen'], 'readiness_ack', device, observed['seen']))
    return inventory(access)


def inventory(access):
    with access.db() as database:
        row = database.execute('SELECT count(*) AS total,sum(d.revoked=0) AS non_revoked,sum(d.revoked!=0) AS revoked,'
                               'count(s.support_id) AS support_ids,count(s.platform) AS platform_known,'
                               'count(s.app_version) AS version_known FROM devices d LEFT JOIN device_support s ON s.device=d.device').fetchone()
        result = {key: value or 0 for key, value in dict(row).items()}
        result.update(platform_unknown=result['total'] - result['platform_known'], version_unknown=result['total'] - result['version_known'])
        return result


def request(access, value):
    if type(value) is not dict or set(value) != {'proof', 'platform', 'app_version', 'version_code'}:
        raise Rejected()
    if (type(value['proof']) is not dict or not isinstance(value['proof'].get('challenge'), str)
            or value['platform'] not in ('android', 'windows', 'linux') or type(value['app_version']) is not str
            or not re.fullmatch(VERSION, value['app_version']) or type(value['version_code']) is not int
            or not 1 <= value['version_code'] <= 2147483647):
        raise Rejected()
    record = access.complete(value['proof'], 'support')
    with access.db() as database:
        row = database.execute('SELECT d.revoked,i.revoked AS invite_revoked FROM devices d JOIN invites i '
                               'ON i.device=d.device WHERE d.device=?', (record['device'],)).fetchone()
        if row is None or row['revoked'] or row['invite_revoked']:
            raise Rejected()
        assigned = database.execute('SELECT support_id FROM device_support WHERE device=?', (record['device'],)).fetchone()
        if assigned is None:
            raise RuntimeError('Support inventory mismatch')
        support = assigned['support_id']
        database.execute('UPDATE device_support SET platform=?,app_version=?,version_code=?,last_seen=?,observation_source=? WHERE device=?',
                         (value['platform'], value['app_version'], value['version_code'], int(access.clock()), 'support_request', record['device']))
        return dict(schema=1, device_support_id=support)


def lookup(access, support, admitted):
    support = normalize(support)
    with access.db() as database:
        row = database.execute('SELECT s.*,d.revoked,i.revoked AS invite_revoked FROM device_support s '
                               'JOIN devices d ON d.device=s.device LEFT JOIN invites i ON i.device=s.device WHERE s.support_id=?', (support,)).fetchone()
        if row is None:
            raise ValueError('Support ID not found')
        grant = None
        if database.execute("SELECT 1 FROM sqlite_master WHERE name='restricted_grants'").fetchone():
            grant = database.execute('SELECT revoked,expires FROM restricted_grants WHERE device=?', (row['device'],)).fetchone()
        now = int(access.clock())
        observed = receipt(database, row['device'])
        readiness = 'UNKNOWN' if observed is None else 'EXPIRED' if not observed['expires'] or observed['expires'] <= now else 'READY' if observed['ready'] else 'NOT_READY'
        family = 'NOT_PROVISIONED' if grant is None else 'REVOKED' if grant['revoked'] else 'EXPIRED' if grant['expires'] is not None and grant['expires'] <= now else 'ACTIVE'
        revoked = bool(row['revoked'] or row['invite_revoked'])
        return dict(device_support_id=support, label=None, app_version=row['app_version'], version_code=row['version_code'],
                    platform=row['platform'], last_seen=row['last_seen'], observation_source=row['observation_source'],
                    active=not revoked and row['invite_revoked'] is not None, revoked=revoked,
                    family_state=family, restricted_readiness=readiness, field_admission=row['device'] in admitted)
