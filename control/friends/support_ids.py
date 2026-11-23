"""Non-secret registration aliases; never credentials or an enrollment path."""
import json
import re
import secrets
import sqlite3

from .access import Rejected, SQLiteEnrollment

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


def parse_receipt(row):
    if row is None:
        return None
    try:
        value = json.loads(row['ack'])
        if (type(value) is not dict or not isinstance(value.get('app_version'), str)
                or not re.fullmatch(VERSION, value['app_version'])
                or type(value.get('version_code')) is not int or not 1 <= value['version_code'] <= 2147483647
                or type(row['ack_at']) is not int or row['ack_at'] < 0):
            return None
        return dict(version=value['app_version'], code=value['version_code'], seen=row['ack_at'],
                    expires=row['expires'], ready=value.get('result') == 'READY')
    except (ValueError, TypeError):
        return None


class SupportTransaction:
    def __init__(self, enrollment):
        self.enrollment = enrollment
        self.database = enrollment.database
        self.placeholder = enrollment.placeholder

    def ensure_schema(self):
        create(self.database)

    def table_exists(self, table):
        return self.database.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None

    def receipt(self, device):
        if not self.table_exists('restricted_readiness_results'):
            return None
        row = self.database.execute('SELECT ack,ack_at,expires FROM restricted_readiness_results '
            f'WHERE device={self.placeholder} AND ack IS NOT NULL '
            'ORDER BY ack_at DESC NULLS LAST,correlation ASC LIMIT 1', (device,)).fetchone()
        return parse_receipt(row)

    def devices(self):
        return self.database.execute('SELECT device FROM devices ORDER BY device').fetchall()

    def support_id(self, device):
        row = self.database.execute(f'SELECT support_id FROM device_support WHERE device={self.placeholder}', (device,)).fetchone()
        if row is None:
            raise RuntimeError('Support inventory mismatch')
        return row['support_id']

    def active(self, device):
        row = self.enrollment.device(device)
        invitation = self.enrollment.device_invitation(device)
        if row is None or row['revoked'] or invitation is None or invitation['revoked']:
            raise Rejected()

    def observe_receipt(self, device, observed):
        self.database.execute(f'UPDATE device_support SET app_version={self.placeholder},version_code={self.placeholder},'
            f'last_seen={self.placeholder},observation_source={self.placeholder} '
            f'WHERE device={self.placeholder} AND (last_seen IS NULL OR last_seen<{self.placeholder})',
            (observed['version'], observed['code'], observed['seen'], 'readiness_ack', device, observed['seen']))

    def observe_request(self, device, value, now):
        self.database.execute(f'UPDATE device_support SET platform={self.placeholder},app_version={self.placeholder},'
            f'version_code={self.placeholder},last_seen={self.placeholder},observation_source={self.placeholder} '
            f'WHERE device={self.placeholder}',
            (value['platform'], value['app_version'], value['version_code'], now, 'support_request', device))

    def inventory(self):
        row = self.database.execute('SELECT count(*) AS total,'
            'sum(CASE WHEN d.revoked=0 THEN 1 ELSE 0 END) AS non_revoked,'
            'sum(CASE WHEN d.revoked!=0 THEN 1 ELSE 0 END) AS revoked,'
            'count(s.support_id) AS support_ids,count(s.platform) AS platform_known,'
            'count(s.app_version) AS version_known FROM devices d LEFT JOIN device_support s ON s.device=d.device').fetchone()
        result = {key: value or 0 for key, value in dict(row).items()}
        result.update(platform_unknown=result['total'] - result['platform_known'], version_unknown=result['total'] - result['version_known'])
        return result

    def lookup(self, support):
        return self.database.execute('SELECT s.*,d.revoked,i.revoked AS invite_revoked FROM device_support s '
            'JOIN devices d ON d.device=s.device LEFT JOIN invites i ON i.device=s.device '
            f'WHERE s.support_id={self.placeholder}', (support,)).fetchone()

    def grant(self, device):
        if not self.table_exists('restricted_grants'):
            return None
        return self.database.execute(f'SELECT revoked,expires FROM restricted_grants WHERE device={self.placeholder}', (device,)).fetchone()


def receipt(database, device):
    return SupportTransaction(SQLiteEnrollment(database)).receipt(device)


def backfill(access):
    with access.enrollment() as transaction:
        database = transaction.support()
        database.ensure_schema()
        for row in database.devices():
            device = row['device']
            transaction.registered(device)
            observed = database.receipt(device)
            if observed is not None:
                database.observe_receipt(device, observed)
        return database.inventory()


def inventory(access):
    with access.enrollment() as transaction:
        return transaction.support().inventory()


def request(access, value):
    if type(value) is not dict or set(value) != {'proof', 'platform', 'app_version', 'version_code'}:
        raise Rejected()
    if (type(value['proof']) is not dict or not isinstance(value['proof'].get('challenge'), str)
            or value['platform'] not in ('android', 'windows', 'linux') or type(value['app_version']) is not str
            or not re.fullmatch(VERSION, value['app_version']) or type(value['version_code']) is not int
            or not 1 <= value['version_code'] <= 2147483647):
        raise Rejected()
    with access.enrollment() as transaction:
        database = transaction.support()
        record = access.complete(value['proof'], 'support', transaction=transaction)
        database.active(record['device'])
        support = database.support_id(record['device'])
        database.observe_request(record['device'], value, int(access.clock()))
        return dict(schema=1, device_support_id=support)


def lookup(access, support, admitted, *, all_activated=False):
    if type(all_activated) is not bool:
        raise ValueError('Invalid admission mode')
    support = normalize(support)
    with access.enrollment() as transaction:
        database = transaction.support()
        row = database.lookup(support)
        if row is None:
            raise ValueError('Support ID not found')
        grant = database.grant(row['device'])
        now = int(access.clock())
        observed = database.receipt(row['device'])
        readiness = 'UNKNOWN' if observed is None else 'EXPIRED' if not observed['expires'] or observed['expires'] <= now else 'READY' if observed['ready'] else 'NOT_READY'
        family = 'NOT_PROVISIONED' if grant is None else 'REVOKED' if grant['revoked'] else 'EXPIRED' if grant['expires'] is not None and grant['expires'] <= now else 'ACTIVE'
        revoked = bool(row['revoked'] or row['invite_revoked'])
        active = not revoked and row['invite_revoked'] is not None
        admitted_device = row['device'] in admitted or '*' in admitted
        if all_activated:
            admitted_device = active and (grant is None or not grant['revoked'])
            family = 'ELIGIBLE' if admitted_device else 'REVOKED' if revoked or grant is not None and grant['revoked'] else 'INACTIVE'
        return dict(device_support_id=support, label=None, app_version=row['app_version'], version_code=row['version_code'],
                    platform=row['platform'], last_seen=row['last_seen'], observation_source=row['observation_source'],
                    active=active, revoked=revoked,
                    family_state=family, restricted_readiness=readiness, field_admission=admitted_device)
