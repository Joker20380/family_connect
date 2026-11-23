"""Read-only consistency evidence, never an admission or recovery payload."""
import base64
import hashlib
import hmac
import json
from pathlib import Path
import re
import sqlite3
import time

from . import paid_beta, transport_policy

PURPOSE = 'family-connect/control-ha-shadow/v1'
MAX_BYTES = 131072
MAX_ROWS = 100000
MAX_TABLES = 128


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(key, purpose, value):
    if type(key) is not bytes or len(key) != 32:
        raise ValueError('SHADOW_KEY_REQUIRED')
    return hmac.new(key, PURPOSE.encode() + b'\0' + purpose.encode() + b'\0' + encode(value),
                    hashlib.sha256).hexdigest()


def cell(value):
    return {'blob': base64.b64encode(value).decode()} if isinstance(value, bytes) else value


def capture(registry, key, *, observed_at=None, budget=10):
    observed = int(time.time()) if observed_at is None else observed_at
    if type(observed) is not int or observed < 0 or not 0 < budget <= 30:
        raise ValueError('INVALID_SHADOW_WINDOW')
    source = Path(registry)
    if any(parent.is_symlink() for parent in (source, *source.parents)):
        raise ValueError('SHADOW_SYMLINK_FORBIDDEN')
    deadline = time.monotonic() + budget

    def bounded():
        if time.monotonic() >= deadline:
            raise ValueError('SHADOW_CAPTURE_DEADLINE')

    with paid_beta.connection(source) as database:
        database.execute('PRAGMA busy_timeout=1000')
        database.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, MAX_BYTES)
        database.set_progress_handler(lambda: int(time.monotonic() >= deadline), 1000)
        paid_beta.require(paid_beta.schema_present(database), 'PAID_SCHEMA_REQUIRED')
        schema = [tuple(row) for row in database.execute(
            'SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name')]
        names = [row[1] for row in schema if row[0] == 'table']
        if len(names) > MAX_TABLES:
            raise ValueError('SHADOW_TABLE_LIMIT')
        tables, total = {}, 0
        for name in names:
            bounded()
            if not re.fullmatch('[a-zA-Z_][a-zA-Z0-9_]{0,127}', name):
                raise ValueError('SHADOW_TABLE_NAME')
            hashes = []
            for row in database.execute('SELECT * FROM "' + name + '"'):
                bounded()
                total += 1
                if total > MAX_ROWS:
                    raise ValueError('SHADOW_ROW_LIMIT')
                values = [cell(value) for value in row]
                if len(encode(values)) > MAX_BYTES:
                    raise ValueError('SHADOW_ROW_SIZE')
                hashes.append(digest(key, 'row/' + name, values))
            tables[name] = dict(rows=len(hashes), hmac=digest(key, 'table/' + name, sorted(hashes)))
        decisions = {}
        for node in transport_policy.NODES:
            bounded()
            envelope = transport_policy.read_snapshot(database, node, observed)
            transport_policy.validate(envelope, node, observed)
            decisions[node] = dict(rows=len(envelope['decisions']), hmac=digest(key, 'decision/' + node, envelope))
        bounded()
        payload = dict(schema=1, purpose=PURPOSE, mode='shadow-only', observed_at=observed,
                       expires_at=observed + transport_policy.LEASE_SECONDS,
                       schema_hmac=digest(key, 'schema', schema), tables=tables, decisions=decisions)
    result = dict(payload=payload, mac=digest(key, 'manifest', payload))
    if len(encode(result)) > MAX_BYTES:
        raise ValueError('SHADOW_MANIFEST_SIZE')
    return result


def validate(manifest, key, *, now=None):
    observed = int(time.time()) if now is None else now
    if type(manifest) is not dict or set(manifest) != {'payload', 'mac'}:
        raise ValueError('INVALID_SHADOW_MANIFEST')
    payload = manifest['payload']
    if (type(payload) is not dict or set(payload) != {
            'schema', 'purpose', 'mode', 'observed_at', 'expires_at', 'schema_hmac', 'tables', 'decisions'}
            or type(manifest['mac']) is not str
            or not hmac.compare_digest(manifest['mac'], digest(key, 'manifest', payload))
            or type(payload['schema']) is not int or payload['schema'] != 1
            or payload['purpose'] != PURPOSE or payload['mode'] != 'shadow-only'
            or type(payload['observed_at']) is not int or type(payload['expires_at']) is not int
            or not observed - transport_policy.LEASE_SECONDS < payload['observed_at'] <= observed + 5
            or payload['expires_at'] != payload['observed_at'] + transport_policy.LEASE_SECONDS
            or not re.fullmatch('[0-9a-f]{64}', str(payload['schema_hmac']))):
        raise ValueError('INVALID_SHADOW_MANIFEST')
    if (type(payload['tables']) is not dict or not 1 <= len(payload['tables']) <= MAX_TABLES
            or type(payload['decisions']) is not dict
            or set(payload['decisions']) != set(transport_policy.NODES)):
        raise ValueError('INVALID_SHADOW_PROJECTIONS')
    for name, summary in list(payload['tables'].items()) + list(payload['decisions'].items()):
        if (not re.fullmatch('[a-zA-Z_][a-zA-Z0-9_-]{0,127}', name)
                or type(summary) is not dict or set(summary) != {'rows', 'hmac'}
                or type(summary['rows']) is not int or not 0 <= summary['rows'] <= MAX_ROWS
                or type(summary['hmac']) is not str or not re.fullmatch('[0-9a-f]{64}', summary['hmac'])):
            raise ValueError('INVALID_SHADOW_PROJECTIONS')
    if len(encode(manifest)) > MAX_BYTES:
        raise ValueError('SHADOW_MANIFEST_SIZE')
    return payload


def compare(left, right, key, *, now=None):
    first, second = validate(left, key, now=now), validate(right, key, now=now)
    if first['observed_at'] != second['observed_at']:
        raise ValueError('SAME_OBSERVATION_REQUIRED')
    return dict(schema=1, mode='shadow-only', matches=first == second,
                authority='NOT_IMPLEMENTED', production_writes=0)
