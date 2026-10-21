"""Opt-in, identity-bound support snapshots. No remote commands or raw logs."""
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
from contextlib import closing
import threading
import time

from .access import Rejected
from .referrals import RateLimited
from .support_ids import registered

MAX_REPORT = 4096
RETENTION = 7 * 86400
MAX_DEVICES = 5000
COUNTERS = frozenset(('protocol_errors', 'retransmissions', 'retry_bytes', 'sent_bytes',
                      'received_bytes', 'recovery_timeouts', 'mux_window', 'effective_send_window',
                      'receive_window', 'peer_receive_window', 'send_window', 'observed_at_ms',
                      'open_replay', 'unknown_stream', 'open_state', 'data_state', 'credit_state',
                      'fin_state', 'close_state', 'frame_kind', 'dns_replay', 'dns_role', 'dns_unmatched'))
ENUMS = {
    'state': {'DISCONNECTED', 'CONNECTING', 'CONNECTED', 'RESTORING', 'FAILED', 'STOPPING', 'UNKNOWN'},
    'network': {'WIFI', 'CELLULAR', 'ETHERNET', 'VPN', 'NONE', 'UNKNOWN'},
    'readiness': {'READY', 'NOT_READY', 'UNKNOWN'},
    'speed_profile': {'P0', 'P1', 'P2', 'UNKNOWN'},
    'mux_profile': {'LEGACY64', 'CREDIT128', 'UNKNOWN'},
    'terminal_reason': {'NONE', 'CANCELLED', 'REMOTE_RESET', 'RELIABLE_EXHAUSTED', 'IO_CLOSED',
                        'MUX_PROTOCOL', 'RELIABLE_PROTOCOL', 'FAMILY_REJECTED', 'DEADLINE',
                        'NETWORK_TIMEOUT', 'UNKNOWN'},
}


def unique(pairs):
    result = {}
    for name, value in pairs:
        if name in result:
            raise ValueError('Duplicate field')
        result[name] = value
    return result


def validate(raw):
    if not isinstance(raw, str) or len(raw.encode('utf-8')) > MAX_REPORT:
        raise ValueError('Report bound')
    report = json.loads(raw, object_pairs_hook=unique)
    required = {'schema', 'report_id', 'platform', 'version_code', 'sampled_at_ms', 'consent', 'metrics'}
    if not isinstance(report, dict) or set(report) != required or type(report['schema']) is not int or report['schema'] != 1 or report['consent'] is not True:
        raise ValueError('Report contract')
    if not isinstance(report['report_id'], str) or not re.fullmatch('[0-9a-f]{32}', report['report_id']):
        raise ValueError('Report ID')
    if report['platform'] not in ('android', 'linux', 'windows'):
        raise ValueError('Platform')
    for key in ('version_code', 'sampled_at_ms'):
        if type(report[key]) is not int or not 0 <= report[key] <= 2**53-1:
            raise ValueError('Integer bound')
    metrics = report['metrics']
    if not isinstance(metrics, dict) or not set(metrics) <= COUNTERS | ENUMS.keys() | {'session_tag', 'vpn_capture_open'}:
        raise ValueError('Unknown metric')
    for key, value in metrics.items():
        if key in COUNTERS:
            valid = type(value) is int and 0 <= value <= 2**53-1
        elif key in ENUMS:
            valid = isinstance(value, str) and value in ENUMS[key]
        elif key == 'session_tag':
            valid = isinstance(value, str) and re.fullmatch('[0-9a-f]{32}|[0-9a-f]{64}', value)
        else:
            valid = type(value) is bool
        if not valid:
            raise ValueError('Metric contract')
    return report


def request(access, path, value):
    if not isinstance(value, dict) or set(value) != {'proof', 'report'}:
        raise Rejected()
    report = validate(value['report'])
    purpose = 'diagnostics:' + hashlib.sha256(value['report'].encode('utf-8')).hexdigest()
    device = access.complete(value['proof'], purpose)['device']
    with access.db() as database:
        support = registered(database, device)
    now = int(access.clock())
    path = Path(path)
    descriptor = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    os.close(descriptor)
    with closing(sqlite3.connect(path, timeout=3)) as database, database:
        database.execute('PRAGMA secure_delete=ON')
        database.execute('CREATE TABLE IF NOT EXISTS snapshots(device TEXT PRIMARY KEY, support TEXT NOT NULL, received INTEGER NOT NULL, report TEXT NOT NULL)')
        database.execute('BEGIN IMMEDIATE')
        database.execute('DELETE FROM snapshots WHERE received<?', (now - RETENTION,))
        previous = database.execute('SELECT received,report FROM snapshots WHERE device=?', (device,)).fetchone()
        if previous and json.loads(previous[1])['report_id'] == report['report_id']:
            if json.loads(previous[1]) != report:
                raise Rejected()
            return {'schema': 1, 'report_id': report['report_id'], 'stored_at': previous[0]}
        if previous and now - previous[0] < 60:
            raise RateLimited()
        if not previous and database.execute('SELECT count(*) FROM snapshots').fetchone()[0] >= MAX_DEVICES:
            raise RateLimited()
        database.execute('INSERT OR REPLACE INTO snapshots VALUES(?,?,?,?)',
                         (device, support, now, json.dumps(report, separators=(',', ':'))))
    return {'schema': 1, 'report_id': report['report_id'], 'stored_at': now}


def read(path, support, now):
    from .support_ids import normalize
    with closing(sqlite3.connect('file:' + str(Path(path).resolve()) + '?mode=ro', uri=True)) as database:
        row = database.execute('SELECT received,report FROM snapshots WHERE support=? AND received>=?',
                               (normalize(support), now - RETENTION)).fetchone()
    return None if row is None else {'stored_at': row[0], 'report': json.loads(row[1])}


def prune(path, now):
    if not Path(path).exists():
        return
    with closing(sqlite3.connect(path, timeout=3)) as database, database:
        database.execute('PRAGMA secure_delete=ON')
        if database.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='snapshots'").fetchone():
            database.execute('DELETE FROM snapshots WHERE received<?', (now - RETENTION,))


def start_retention(path):
    stopped = threading.Event()
    def run():
        while not stopped.is_set():
            try:
                prune(path, int(time.time()))
            except (OSError, sqlite3.Error):
                pass
            stopped.wait(60)
    worker = threading.Thread(target=run, name='support-retention', daemon=True)
    worker.start()
    return stopped
