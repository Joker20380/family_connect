"""Private control-plane acknowledgements; transport-neutral safe product payload v1."""
import base64
import hashlib
import json
import re
import secrets
import sqlite3

from device_identity.device import verify_transport_key_proof
from provisioning.friends_catalog import fields, require
from .access import Rejected, CHALLENGE_TTL

CODES = frozenset(('READY', 'NATIVE_VALIDATION_FAILED', 'BOOTSTRAP_VALIDATION_FAILED',
                   'ATOMIC_IMPORT_FAILED', 'PERSISTENCE_FAILED', 'EXPIRED_ON_IMPORT',
                   'ORCHESTRATOR_NOT_USABLE', 'INTERNAL_ERROR', 'STALE_STATE',
                   'AUTHORIZATION_REJECTED', 'FETCH_FAILED', 'MISSING'))
FIELDS = ('version type correlation_id challenge_id fetch_id result provisioning bootstrap '
          'orchestrator_usable revision minimum_crl expires_at observed_at phase app_version version_code failure_reason')


def request_id(value):
    require(type(value) is str and re.fullmatch('[a-f0-9]{32}', value))
    return value


def validate(value):
    fields(value, FIELDS)
    require(type(value['version']) is int and value['version'] == 1 and value['type'] == 'READINESS_IMPORT_RESULT')
    for name in ('correlation_id', 'challenge_id', 'fetch_id'):
        request_id(value[name])
    require(value['correlation_id'] == value['challenge_id'] != value['fetch_id'])
    require(type(value['result']) is str and value['result'] in CODES)
    ready = value['result'] == 'READY'
    require(type(value['orchestrator_usable']) is bool and value['orchestrator_usable'] == ready)
    require(value['provisioning'] == value['bootstrap'] == ('PRESENT_VALID' if ready else 'NOT_READY'))
    require(value['failure_reason'] == ('NONE' if ready else value['result']))
    for name in ('revision', 'minimum_crl', 'expires_at', 'observed_at', 'version_code'):
        require(type(value[name]) is int and (1 if ready or name in ('observed_at', 'version_code') else 0) <= value[name] < 2**53)
    require(type(value['app_version']) is str and re.fullmatch('[A-Za-z0-9._-]{1,64}', value['app_version']))
    require(value['phase'] in ('import', 'restart'))
    require(not ready or value['expires_at'] > value['observed_at'])
    raw = json.dumps(value, sort_keys=True, separators=(',', ':')).encode()
    require(len(raw) <= 2048)
    return raw


def migrate(database):
    database.execute('CREATE TABLE IF NOT EXISTS restricted_readiness_results ('
                     'correlation TEXT PRIMARY KEY, nonce TEXT UNIQUE NOT NULL, device TEXT NOT NULL, '
                     'challenge_at INTEGER NOT NULL, fetch_id TEXT, fetch_at INTEGER, '
                     'revision INTEGER, minimum_crl INTEGER, expires INTEGER, ack TEXT, ack_at INTEGER)')


def challenge(database, correlation, nonce, device, now):
    request_id(correlation)
    database.execute('DELETE FROM restricted_readiness_results WHERE challenge_at<?', (now - 86400,))
    database.execute('DELETE FROM restricted_readiness_results WHERE device=? AND correlation NOT IN '
                     '(SELECT correlation FROM restricted_readiness_results WHERE device=? ORDER BY challenge_at DESC LIMIT 15)', (device, device))
    database.execute('INSERT INTO restricted_readiness_results(correlation,nonce,device,challenge_at) VALUES (?,?,?,?)', (correlation, nonce, device, now))


def fetched(database, nonce, fetch_id, response, now):
    request_id(fetch_id)
    row = database.execute('SELECT correlation FROM restricted_readiness_results WHERE nonce=?', (nonce,)).fetchone()
    if row is not None:
        require(row['correlation'] != fetch_id)
        database.execute('UPDATE restricted_readiness_results SET fetch_id=?,fetch_at=?,revision=?,minimum_crl=?,expires=? WHERE nonce=?',
                         (fetch_id, now, response['revision'], response['minimum_crl'], response['expires_at'], nonce))


def _attempt(service, database, payload, device, now):
    raw = validate(payload)
    row = database.execute('SELECT * FROM restricted_readiness_results WHERE correlation=? AND device=?', (payload['correlation_id'], device)).fetchone()
    grant = service._grant(database, device, now)
    trust, authority, crl, _, floor = service._trust(now)
    if (row is None or row['challenge_at'] < now - 86400 or not row['challenge_at'] <= payload['observed_at'] <= now + 5
            or grant['family'] != trust['family'] or grant['revision'] < trust['minimum_revision']):
        raise Rejected()
    if row['fetch_id'] is not None and payload['fetch_id'] != row['fetch_id']:
        raise Rejected()
    if payload['result'] == 'READY':
        if (row['fetch_at'] is None or row['revision'] != grant['revision']
                or payload['revision'] != row['revision'] or payload['minimum_crl'] != row['minimum_crl']
                or payload['expires_at'] != row['expires'] or payload['expires_at'] <= now
                or floor < payload['minimum_crl']):
            raise Rejected()
        serials = database.execute('SELECT serial FROM restricted_certificates WHERE device=? AND revision=?', (device, grant['revision']))
        if any(crl.get_revoked_certificate_by_serial_number(int(item['serial'])) is not None for item in serials):
            raise Rejected()
    if row['ack'] is not None:
        previous = json.loads(row['ack'])
        if payload['observed_at'] < previous['observed_at'] or (payload['observed_at'] == previous['observed_at'] and raw.decode() != row['ack']):
            raise Rejected()
    return row, raw


def ack_challenge(service, value):
    fields(value, 'public_identity wireguard_public_key receipt')
    device = service.access.binding(value['public_identity'], value['wireguard_public_key'])
    now = int(service.access.clock())
    with service.access.db() as database:
        row, raw = _attempt(service, database, value['receipt'], device, now)
        grant = service._grant(database, device, now)
        if grant['public'] != value['public_identity'] or grant['wg'] != value['wireguard_public_key']:
            raise Rejected()
        database.execute('DELETE FROM challenges WHERE expires<=?', (now,))
        require(database.execute('SELECT COUNT(*) FROM challenges WHERE device=? AND used=0', (device,)).fetchone()[0] < 8)
        nonce = base64.b64encode(secrets.token_bytes(32)).decode()
        expiry = now + CHALLENGE_TTL
        database.execute('INSERT INTO challenges VALUES (?,?,?,?,?,?,?,0)',
                         (hashlib.sha256(nonce.encode()).hexdigest(), device, grant['public'], grant['wg'],
                          'readiness-ack', hashlib.sha256(raw).hexdigest(), expiry))
    return dict(challenge=nonce, expires_at=expiry, audience='family-connect/enrollment/v1')


def acknowledge(service, value):
    fields(value, 'proof receipt')
    proof = value['proof']
    device = verify_transport_key_proof(proof, expected_challenge=proof['challenge'])
    nonce = hashlib.sha256(proof['challenge'].encode()).hexdigest()
    now = int(service.access.clock())
    with service.access.db() as database:
        row, raw = _attempt(service, database, value['receipt'], device, now)
        challenge_row = database.execute('SELECT * FROM challenges WHERE nonce=?', (nonce,)).fetchone()
        if (challenge_row is None or challenge_row['used'] or challenge_row['expires'] <= now
                or challenge_row['purpose'] != 'readiness-ack' or challenge_row['device'] != device
                or challenge_row['public'] != proof['public_identity'] or challenge_row['wg'] != proof['wireguard_public_key']
                or challenge_row['invite'] != hashlib.sha256(raw).hexdigest()):
            raise Rejected()
        database.execute('UPDATE challenges SET used=1 WHERE nonce=?', (nonce,))
        database.execute('UPDATE restricted_readiness_results SET ack=?,ack_at=? WHERE correlation=?', (raw.decode(), now, row['correlation']))
    return dict(version=1, correlation_id=value['receipt']['correlation_id'], status='ACK_RECEIVED')


def readback(service, correlation, expected_owner):
    request_id(correlation)
    now = int(service.access.clock())
    result = dict(version=1, correlation_id=correlation, status='UNKNOWN', receipt=None)
    database = sqlite3.connect(service.access.path.resolve().as_uri() + '?mode=ro', uri=True)
    database.row_factory = sqlite3.Row
    try:
        row = database.execute('SELECT * FROM restricted_readiness_results WHERE correlation=? AND device=?', (correlation, expected_owner)).fetchone()
        if row is None:
            return result
        result['status'] = 'ACK_PENDING'
        if row['ack'] is not None:
            payload = json.loads(row['ack'])
            try:
                _attempt(service, database, payload, expected_owner, now)
            except (ValueError, Rejected):
                return result
            result.update(status='ACK_RECEIVED', receipt=payload, received_at=row['ack_at'])
    finally:
        database.close()
    return result
