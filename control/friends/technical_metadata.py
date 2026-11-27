"""Versioned latest-only observations; processing mode is not inferred consent."""
from contextlib import closing, contextmanager, nullcontext
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import stat
import time

from .access import Rejected
from .diagnostics import unique
from .referrals import RateLimited

MAX_REPORT = 6144
MAX_DEVICES = 5000
RETENTION = 7 * 86400
MIN_INTERVAL = 60
MAX_INTEGER = 2**53 - 1
REPOSITORY_PURPOSE = 'family-connect/ha-metadata-synthetic/v1/db-only'
SOURCES = {
    'profile': {'android_build_package'},
    'network': {'tunnel_socket', 'vpn_transport_capabilities', 'android_default_network', 'unavailable'},
    'mobile': {'android_telephony_public'},
    'session': {'connection_service'},
    'diagnostic': {'connection_terminal'},
}
REASONS = {'none', 'permission_not_granted', 'api_not_supported', 'no_sim',
           'no_registered_network', 'not_cellular', 'ambiguous_subscription',
           'not_observed', 'network_unavailable', 'underlay_not_exposed',
           'service_unavailable', 'stale', 'clock_skew'}
FIELDS = {
    'profile': {'manufacturer': 80, 'model': 100, 'android_version': 40,
                'api_level': int, 'app_version': 64, 'version_code': int},
    'network': {'kind': {'WIFI', 'CELLULAR', 'ETHERNET', 'OFFLINE', 'UNKNOWN'},
                'scope': {'session_underlay', 'default_network', 'unknown'}},
    'mobile': {'sim_operator': 100, 'registered_operator': 100,
               'radio': {'2G', '3G', 'LTE_4G', '5G', 'UNKNOWN'},
               'sim_reason': REASONS, 'registered_reason': REASONS, 'radio_reason': REASONS},
    'session': {'preference': {'AUTO', 'AWG', 'TCP', 'MESH', 'UNKNOWN'},
                'attempt': {'AWG', 'TCP', 'MESH', 'NONE', 'UNKNOWN'},
                'transport': {'AWG', 'TCP', 'MESH', 'NONE', 'UNKNOWN'},
                'gateway': {'gateway-ru', 'nl-amsterdam-1', 'nl-amsterdam-2', 'UNKNOWN'},
                'state': {'DISCONNECTED', 'CONNECTING', 'CONNECTED', 'RESTORING',
                          'FAILED', 'STOPPING', 'UNKNOWN'}},
    'diagnostic': {'error': {'NONE', 'CANCELLED', 'AUTH', 'READINESS', 'NETWORK',
                            'TIMEOUT', 'TRANSPORT', 'PERMISSION', 'UNKNOWN'},
                   'error_at_ms': int, 'readiness': {'READY', 'NOT_READY', 'UNKNOWN'}},
}


BASIC_MODE = 'automatic_basic'
BASIC_POLICY = 'basic-2026-11-v1'
BASIC_FIELDS = {
    'profile': {'os': {'Android'}, 'os_version': 40, 'app_version': 64},
    'network': FIELDS['network'],
    'mobile': {name: FIELDS['mobile'][name] for name in
               ('sim_operator', 'registered_operator', 'sim_reason', 'registered_reason')},
    'session': {name: FIELDS['session'][name] for name in ('transport', 'gateway', 'state')},
    'diagnostic': {name: FIELDS['diagnostic'][name] for name in ('error', 'error_at_ms')},
}


def require(condition):
    if not condition:
        raise ValueError('Technical metadata contract')


def integer(value, minimum=0):
    return type(value) is int and minimum <= value <= MAX_INTEGER


def validate(raw):
    require(isinstance(raw, str) and len(raw.encode('utf-8')) <= MAX_REPORT)
    report = json.loads(raw, object_pairs_hook=unique, parse_constant=lambda value: require(False))
    require(type(report) is dict and type(report.get('schema')) is int and report['schema'] in (1, 2))
    basic = report['schema'] == 2
    require(set(report) == {'schema', 'report_id', 'consent_epoch', 'sequence', 'operation', 'observations'} |
            ({'processing_mode', 'policy_version'} if basic else set()))
    require(not basic or report['processing_mode'] == BASIC_MODE and report['policy_version'] == BASIC_POLICY)
    require(integer(report['consent_epoch'], 1) and integer(report['sequence'], 1))
    require(report['report_id'] == f"{report['consent_epoch']:016x}{report['sequence']:016x}")
    require(report['operation'] in ('sample', 'revoke'))
    observations = report['observations']
    require(type(observations) is dict)
    require(set(observations) == (set(SOURCES) if report['operation'] == 'sample' else set()))
    validate_observations(observations, basic=basic)
    return report


def validate_observations(observations, complete=False, *, basic=False):
    require(type(observations) is dict and set(observations) <= set(SOURCES))
    require(not complete or set(observations) == set(SOURCES))
    for group, observation in observations.items():
        require(type(observation) is dict and set(observation) == {
            'sampled_at_ms', 'age_ms', 'source', 'status', 'reason', 'values'})
        require(integer(observation['sampled_at_ms']) and integer(observation['age_ms']))
        require(isinstance(observation['source'], str) and observation['source'] in SOURCES[group])
        require(observation['status'] in ('available', 'partial', 'unknown', 'unavailable', 'stale'))
        require(isinstance(observation['reason'], str) and observation['reason'] in REASONS)
        values = observation['values']
        selected = (BASIC_FIELDS if basic else FIELDS)[group]
        require(type(values) is dict and set(values) == set(selected))
        for name, specification in selected.items():
            value = values[name]
            if value is None:
                require(observation['status'] != 'available')
            elif specification is int:
                require(integer(value))
            elif type(specification) is int:
                require(isinstance(value, str) and 0 < len(value) <= specification
                        and all(character.isprintable() for character in value))
            else:
                require(isinstance(value, str) and value in specification)
        if group == 'network':
            require(values['scope'] != 'session_underlay' or observation['source'] in {
                'tunnel_socket', 'vpn_transport_capabilities'})
        if group == 'session':
            require(values['state'] in ('CONNECTED', 'RESTORING') or
                    values['transport'] in ('NONE', 'UNKNOWN', None))
        if group == 'mobile':
            for name, reason in (('sim_operator', 'sim_reason'), ('registered_operator', 'registered_reason'),
                                ('radio', 'radio_reason')):
                if basic and name == 'radio':
                    continue
                require(values[reason] is not None)
                require(values[name] not in (None, 'UNKNOWN') or values[reason] != 'none')


@contextmanager
def store(path):
    path = Path(path)
    descriptor = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        info = os.fstat(descriptor)
        require(stat.S_ISREG(info.st_mode) and info.st_mode & 0o077 == 0 and info.st_nlink == 1)
    finally:
        os.close(descriptor)
    with closing(sqlite3.connect(path, timeout=3)) as database, database:
        database.execute('PRAGMA secure_delete=ON')
        database.execute('''CREATE TABLE IF NOT EXISTS device_metadata(
            device TEXT PRIMARY KEY, epoch INTEGER NOT NULL, sequence INTEGER NOT NULL,
            digest TEXT NOT NULL, enabled INTEGER NOT NULL, received INTEGER NOT NULL,
            payload TEXT NOT NULL)''')
        database.execute('BEGIN IMMEDIATE')
        columns = {row[1] for row in database.execute('PRAGMA table_info(device_metadata)')}
        if 'processing_mode' not in columns:
            database.execute("ALTER TABLE device_metadata ADD COLUMN processing_mode TEXT NOT NULL DEFAULT 'consented_extended'")
        if 'policy_version' not in columns:
            database.execute("ALTER TABLE device_metadata ADD COLUMN policy_version TEXT NOT NULL DEFAULT 'legacy-v1'")
        yield database


def project(observations, received, *, basic=False):
    result = {}
    for group, observation in observations.items():
        age_ms = observation['age_ms']
        wall_age = received * 1000 - observation['sampled_at_ms']
        clock = 'consistent' if abs(wall_age - age_ms) <= 300000 else 'clock_skew'
        if basic:
            require(wall_age >= -300000)
        if clock == 'consistent' or basic:
            age_ms = max(age_ms, wall_age, 0)
        remaining = RETENTION - (age_ms + 999) // 1000
        if remaining <= 0:
            continue
        result[group] = dict(observation, received_at=received, age_at_receive_ms=age_ms,
                             clock_status=clock, expires_at=received + remaining)
    return result


class MetadataTransaction:
    def __init__(self, database, placeholder='?'):
        self.database, self.placeholder = database, placeholder

    def fetch(self, query, parameters=()):
        cursor = self.database.execute(query, parameters)
        fields = [description[0] for description in cursor.description]
        return [dict(row) if hasattr(row, 'keys') else dict(zip(fields, row)) for row in cursor.fetchall()]

    def require_schema(self):
        if self.fetch('SELECT version,purpose FROM ha_metadata_schema') != [dict(version=1, purpose=REPOSITORY_PURPOSE)]:
            raise RuntimeError('Metadata rehearsal schema mismatch')

    def prepare_write(self):
        self.database.execute('PRAGMA secure_delete=ON')

    def previous(self, device):
        rows = self.fetch('SELECT * FROM device_metadata WHERE device=' + self.placeholder, (device,))
        return rows[0] if rows else None

    def count(self):
        return self.fetch('SELECT COUNT(*) AS total FROM device_metadata')[0]['total']

    def supports_basic(self):
        return self.placeholder == '?' and {'processing_mode', 'policy_version'} <= {
            row['name'] for row in self.fetch('PRAGMA table_info(device_metadata)')}

    def rows(self):
        return self.fetch('SELECT * FROM device_metadata ORDER BY device')

    def save(self, device, epoch, sequence, digest, enabled, now, payload):
        self.database.execute('INSERT INTO device_metadata(device,epoch,sequence,digest,enabled,received,payload) VALUES (' +
            ','.join([self.placeholder] * 7) + ') ON CONFLICT(device) DO UPDATE SET epoch=excluded.epoch, '
            'sequence=excluded.sequence,digest=excluded.digest,enabled=excluded.enabled,received=excluded.received,payload=excluded.payload',
            (device, epoch, sequence, digest, int(enabled), now, json.dumps(payload, ensure_ascii=False, separators=(',', ':'))))

    def expire(self, now):
        for row in self.fetch("SELECT device,payload FROM device_metadata WHERE payload!='{}'"):
            observations = json.loads(row['payload'])
            retained = {name: value for name, value in observations.items() if value['expires_at'] > now}
            if retained != observations:
                self.database.execute('UPDATE device_metadata SET payload=' + self.placeholder + ' WHERE device=' + self.placeholder,
                    (json.dumps(retained, ensure_ascii=False, separators=(',', ':')), row['device']))


def expire(database, now):
    MetadataTransaction(database).expire(now)


def validated_request(value):
    if type(value) is not dict or set(value) != {'proof', 'report'}:
        raise Rejected()
    return validate(value['report']), hashlib.sha256(value['report'].encode('utf-8')).hexdigest()


def record(transaction, device, report, digest, now):
    basic = report['schema'] == 2
    require(not basic or transaction.supports_basic())
    transaction.prepare_write()
    transaction.expire(now)
    previous = transaction.previous(device)
    epoch, sequence = report['consent_epoch'], report['sequence']
    enabled = report['operation'] == 'sample'
    if previous:
        if (epoch, sequence) == (previous['epoch'], previous['sequence']):
            if digest != previous['digest']:
                raise Rejected()
            return receipt(report, previous['received'], previous['enabled'])
        if enabled and not basic and previous.get('processing_mode') == BASIC_MODE:
            raise Rejected()
        if epoch < previous['epoch'] or epoch == previous['epoch'] and (
                sequence <= previous['sequence'] or not previous['enabled'] and enabled):
            raise Rejected()
        if enabled and now - previous['received'] < MIN_INTERVAL:
            raise RateLimited()
    elif transaction.count() >= MAX_DEVICES:
        raise RateLimited()
    payload = project(report['observations'], now, basic=basic) if enabled else {}
    transaction.save(device, epoch, sequence, digest, enabled, now, payload)
    if transaction.supports_basic():
        keep_basic = basic or not enabled and previous and previous.get('processing_mode') == BASIC_MODE
        transaction.database.execute('UPDATE device_metadata SET processing_mode=?,policy_version=? WHERE device=?',
            (BASIC_MODE if keep_basic else 'consented_extended', BASIC_POLICY if keep_basic else 'legacy-v1', device))
    return receipt(report, now, enabled)


def request(access, path, value):
    if access.path is None:
        raise NotImplementedError('Legacy metadata requires SQLite; canonical import and fencing are pending')
    with closing(sqlite3.connect(Path(access.path).resolve().as_uri() + '?mode=ro', uri=True)) as database:
        if database.execute("SELECT 1 FROM sqlite_master WHERE name='ha_metadata_schema'").fetchone():
            raise NotImplementedError('Legacy metadata cannot split a canonical rehearsal transaction')
    report, digest = validated_request(value)
    device = access.complete(value['proof'], 'technical-metadata-v1:' + digest)['device']
    with store(path) as database:
        return record(MetadataTransaction(database), device, report, digest, int(access.clock()))


def request_repository(access, value):
    report, digest = validated_request(value)
    if report['schema'] == 2:
        raise NotImplementedError('Basic metadata canonical repository migration is not installed')
    with access.enrollment() as enrollment:
        transaction = enrollment.metadata()
        transaction.require_schema()
        device = access.complete(value['proof'], 'technical-metadata-v1:' + digest, transaction=enrollment)['device']
        invitation = enrollment.device_invitation(device)
        if invitation is None or invitation['revoked']:
            raise Rejected()
        return record(transaction, device, report, digest, int(access.clock()))


def receipt(report, received, enabled):
    if report['schema'] == 2:
        return dict(schema=2, report_id=report['report_id'], received_at=received,
                    processing_mode=BASIC_MODE, policy_version=BASIC_POLICY,
                    consent='not_requested' if enabled else 'revoked', retention_seconds=RETENTION)
    return dict(schema=1, report_id=report['report_id'], received_at=received,
                consent='enabled' if enabled else 'revoked', retention_seconds=RETENTION)


def view(rows, now):
    return [dict(device=row['device'], consent_epoch=row['epoch'], sequence=row['sequence'],
                 consent=('not_requested' if row.get('processing_mode') == BASIC_MODE else 'enabled') if row['enabled'] else 'revoked',
                 **(dict(processing_mode=BASIC_MODE, policy_version=BASIC_POLICY) if row.get('processing_mode') == BASIC_MODE else {}),
                 received_at=row['received'],
                 observations={name: value for name, value in json.loads(row['payload']).items() if value['expires_at'] > now})
            for row in rows]


def read_all(path, now):
    if not Path(path).exists():
        return []
    with closing(sqlite3.connect('file:' + str(Path(path).resolve()) + '?mode=ro', uri=True)) as database:
        return view(MetadataTransaction(database).rows(), now)


def read_repository(access):
    with access.read_enrollment() as enrollment:
        transaction = enrollment.metadata()
        transaction.require_schema()
        return view(transaction.rows(), int(access.clock()))


def prune_repository(access):
    with access.enrollment() as enrollment:
        transaction = enrollment.metadata()
        transaction.require_schema()
        transaction.prepare_write()
        transaction.expire(int(access.clock()))


def prune(path, now):
    if Path(path).exists():
        with store(path) as database:
            expire(database, now)


def start_retention(path, *, capture_gate=None):
    from control.friends.http_lifecycle import Retention
    stopped = Retention()
    def run():
        while not stopped.is_set():
            try:
                with capture_gate.operation() if capture_gate is not None else nullcontext():
                    prune(path, int(time.time()))
            except (OSError, sqlite3.Error):
                pass
            stopped.wait(60)
    return stopped.start(run, name='technical-metadata-retention')
