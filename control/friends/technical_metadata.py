"""Separately consented, latest-only observations; never an access authority."""
from contextlib import closing, contextmanager
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import stat
import threading
import time

from .access import Rejected
from .diagnostics import unique
from .referrals import RateLimited

MAX_REPORT = 6144
MAX_DEVICES = 5000
RETENTION = 7 * 86400
MIN_INTERVAL = 60
MAX_INTEGER = 2**53 - 1
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


def require(condition):
    if not condition:
        raise ValueError('Technical metadata contract')


def integer(value, minimum=0):
    return type(value) is int and minimum <= value <= MAX_INTEGER


def validate(raw):
    require(isinstance(raw, str) and len(raw.encode('utf-8')) <= MAX_REPORT)
    report = json.loads(raw, object_pairs_hook=unique, parse_constant=lambda value: require(False))
    require(type(report) is dict and set(report) == {
        'schema', 'report_id', 'consent_epoch', 'sequence', 'operation', 'observations'})
    require(type(report['schema']) is int and report['schema'] == 1)
    require(integer(report['consent_epoch'], 1) and integer(report['sequence'], 1))
    require(report['report_id'] == f"{report['consent_epoch']:016x}{report['sequence']:016x}")
    require(report['operation'] in ('sample', 'revoke'))
    observations = report['observations']
    require(type(observations) is dict)
    require(set(observations) == (set(SOURCES) if report['operation'] == 'sample' else set()))
    validate_observations(observations)
    return report


def validate_observations(observations, complete=False):
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
        require(type(values) is dict and set(values) == set(FIELDS[group]))
        for name, specification in FIELDS[group].items():
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
        yield database


def project(observations, received):
    result = {}
    for group, observation in observations.items():
        age_ms = observation['age_ms']
        wall_age = received * 1000 - observation['sampled_at_ms']
        clock = 'consistent' if abs(wall_age - age_ms) <= 300000 else 'clock_skew'
        if clock == 'consistent':
            age_ms = max(age_ms, wall_age, 0)
        remaining = RETENTION - (age_ms + 999) // 1000
        if remaining <= 0:
            continue
        result[group] = dict(observation, received_at=received, age_at_receive_ms=age_ms,
                             clock_status=clock, expires_at=received + remaining)
    return result


def expire(database, now):
    for device, raw in database.execute("SELECT device,payload FROM device_metadata WHERE payload!='{}'").fetchall():
        observations = json.loads(raw)
        retained = {name: value for name, value in observations.items() if value['expires_at'] > now}
        if retained != observations:
            database.execute('UPDATE device_metadata SET payload=? WHERE device=?',
                             (json.dumps(retained, separators=(',', ':')), device))


def request(access, path, value):
    if type(value) is not dict or set(value) != {'proof', 'report'}:
        raise Rejected()
    report = validate(value['report'])
    digest = hashlib.sha256(value['report'].encode('utf-8')).hexdigest()
    device = access.complete(value['proof'], 'technical-metadata-v1:' + digest)['device']
    now = int(access.clock())
    with store(path) as database:
        expire(database, now)
        previous = database.execute('SELECT epoch,sequence,digest,enabled,received FROM device_metadata WHERE device=?',
                                    (device,)).fetchone()
        epoch, sequence = report['consent_epoch'], report['sequence']
        enabled = report['operation'] == 'sample'
        if previous:
            old_epoch, old_sequence, old_digest, old_enabled, old_received = previous
            if (epoch, sequence) == (old_epoch, old_sequence):
                if digest != old_digest:
                    raise Rejected()
                return receipt(report, old_received, old_enabled)
            if epoch < old_epoch or epoch == old_epoch and (sequence <= old_sequence or not old_enabled and enabled):
                raise Rejected()
            if enabled and now - old_received < MIN_INTERVAL:
                raise RateLimited()
        elif database.execute('SELECT count(*) FROM device_metadata').fetchone()[0] >= MAX_DEVICES:
            raise RateLimited()
        payload = project(report['observations'], now) if enabled else {}
        database.execute('INSERT OR REPLACE INTO device_metadata VALUES(?,?,?,?,?,?,?)',
                         (device, epoch, sequence, digest, int(enabled), now,
                          json.dumps(payload, ensure_ascii=False, separators=(',', ':'))))
    return receipt(report, now, enabled)


def receipt(report, received, enabled):
    return dict(schema=1, report_id=report['report_id'], received_at=received,
                consent='enabled' if enabled else 'revoked', retention_seconds=RETENTION)


def read_all(path, now):
    if not Path(path).exists():
        return []
    with closing(sqlite3.connect('file:' + str(Path(path).resolve()) + '?mode=ro', uri=True)) as database:
        rows = database.execute('SELECT device,epoch,sequence,enabled,received,payload FROM device_metadata').fetchall()
    return [dict(device=device, consent_epoch=epoch, sequence=sequence,
                 consent='enabled' if enabled else 'revoked', received_at=received,
                 observations={name: value for name, value in json.loads(raw).items() if value['expires_at'] > now})
            for device, epoch, sequence, enabled, received, raw in rows]


def prune(path, now):
    if Path(path).exists():
        with store(path) as database:
            expire(database, now)


def start_retention(path):
    stopped = threading.Event()
    def run():
        while not stopped.is_set():
            try:
                prune(path, int(time.time()))
            except (OSError, sqlite3.Error):
                pass
            stopped.wait(60)
    threading.Thread(target=run, name='technical-metadata-retention', daemon=True).start()
    return stopped
