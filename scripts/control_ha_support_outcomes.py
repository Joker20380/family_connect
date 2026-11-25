"""Read-only support/relay outcome census; never a writer fence or settlement permit."""
from collections import Counter
from contextlib import closing
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import stat
import time


LIMIT = 32 * 1024 * 1024
STATUSES = frozenset(('queued', 'sending', 'relayed', 'delivered', 'recipient_stored', 'received', 'expired'))
SCHEMAS = {
    'records': [('id', 'TEXT', 0, 1), ('sealed', 'BLOB', 1, 0)],
    'messages': [('id', 'BLOB', 0, 1), ('sender', 'BLOB', 1, 0), ('recipient', 'BLOB', 1, 0),
                 ('received', 'REAL', 1, 0), ('body', 'BLOB', 1, 0)],
}


def require(value, reason):
    if not value:
        raise ValueError(reason)


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def hexadecimal(value, length):
    return type(value) is str and re.fullmatch('[0-9a-f]{' + str(length) + '}', value) is not None


def read_rows(path, table, uid):
    require(table in SCHEMAS, 'TABLE_SCOPE')
    path = Path(path).absolute()
    require(not any(item.is_symlink() for item in (path, *path.parents)), 'DATABASE_SYMLINK')
    information = path.stat()
    require(stat.S_ISREG(information.st_mode) and information.st_nlink == 1 and
            information.st_uid == uid and stat.S_IMODE(information.st_mode) == 0o600 and
            512 <= information.st_size <= LIMIT, 'DATABASE_SHAPE')
    require(not any(Path(str(path) + suffix).exists() or Path(str(path) + suffix).is_symlink()
                    for suffix in ('-wal', '-shm', '-journal')), 'DATABASE_SIDECAR')
    with path.open('rb') as stream:
        header = stream.read(100)
    require(header[:16] == b'SQLite format 3\x00' and header[18:20] == b'\x01\x01', 'ROLLBACK_JOURNAL_REQUIRED')
    started = time.monotonic()
    with closing(sqlite3.connect(path.as_uri() + '?mode=ro', uri=True, timeout=0, isolation_level=None)) as connection:
        connection.setconfig(sqlite3.SQLITE_DBCONFIG_NO_CKPT_ON_CLOSE, True)
        connection.execute('PRAGMA trusted_schema=OFF')
        connection.execute('PRAGMA query_only=ON')
        connection.execute('PRAGMA temp_store=MEMORY')
        connection.set_progress_handler(lambda: time.monotonic() - started >= .25, 1000)
        connection.execute('BEGIN')
        try:
            require(connection.execute('PRAGMA journal_mode').fetchone() == ('delete',), 'ROLLBACK_JOURNAL_REQUIRED')
            require(connection.execute('SELECT name FROM sqlite_master WHERE type="table" ORDER BY name').fetchall()
                    == [(table,)], 'DATABASE_TABLES')
            columns = connection.execute('PRAGMA table_info(' + table + ')').fetchall()
            require([(row[1], row[2], row[3], row[5]) for row in columns] == SCHEMAS[table], 'DATABASE_SCHEMA')
            body = 'sealed' if table == 'records' else 'body'
            count, size = connection.execute('SELECT count(*),coalesce(sum(length(' + body + ')),0) FROM ' + table).fetchone()
            require(count <= 10000 and size <= LIMIT, 'DATABASE_BOUNDS')
            rows = connection.execute('SELECT * FROM ' + table + ' ORDER BY id').fetchall()
            require((path.stat().st_dev, path.stat().st_ino) == (information.st_dev, information.st_ino), 'DATABASE_REPLACED')
        finally:
            connection.rollback()
    require(time.monotonic() - started < .25, 'READ_DEADLINE')
    return rows


def local_snapshot(directory, key, sender_public, uid):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.asymmetric import ed25519, x25519
    require(type(key) is bytes and len(key) == 32 and hexadecimal(sender_public, 128), 'LOCAL_INPUT')
    rows = read_rows(Path(directory) / 'history.sqlite', 'records', uid)
    cipher = AESGCM(key)
    records = {}
    sealed_digest = hashlib.sha256()
    for name, sealed in rows:
        require(type(name) is str and len(name) <= 256 and type(sealed) is bytes and len(sealed) >= 28, 'RECORD_SHAPE')
        sealed_digest.update(encoded([name, len(sealed)]))
        sealed_digest.update(sealed)
        records[name] = json.loads(cipher.decrypt(sealed[:12], sealed[12:], b'fc-chat-v1:' + name.encode()))
    require(records.get('meta') == {'format': 1}, 'STORE_FORMAT')
    require(hexadecimal(records.get('identity'), 128), 'IDENTITY_SHAPE')
    private = bytes.fromhex(records['identity'])
    public = (x25519.X25519PrivateKey.from_private_bytes(private[:32]).public_key().public_bytes_raw() +
              ed25519.Ed25519PrivateKey.from_private_bytes(private[32:]).public_key().public_bytes_raw())
    require(public.hex() == sender_public, 'SENDER_IDENTITY')
    counts, messages, requests, retained_receipts = Counter(), {}, 0, 0
    envelopes = []
    for name, message in records.items():
        if not name.startswith('message:'):
            continue
        require(type(message) is dict and hexadecimal(message.get('id'), 64) and
                name == 'message:' + message['id'] and type(message.get('outgoing')) is bool and
                message.get('status') in STATUSES and hexadecimal(message.get('peer'), 32), 'MESSAGE_SHAPE')
        require(type(message.get('packed')) is str and 194 <= len(message['packed']) <= 263168 and
                re.fullmatch('[0-9a-f]+', message['packed']) is not None, 'PACKED_SHAPE')
        raw = bytes.fromhex(message['packed'])
        require(digest(raw[:32] + raw[96:]) == message['id'] and
                (raw[:16] if message['outgoing'] else raw[16:32]).hex() == message['peer'], 'MESSAGE_BINDING')
        messages[message['id']] = message
        counts[('outgoing:' if message['outgoing'] else 'incoming:') + message['status']] += 1
        retained_receipts += message.get('kind') == 'stored' and not message['outgoing']
        if message['outgoing']:
            envelope = dict(message_id=message['id'], status=message['status'], recipient=message['peer'],
                            kind='stored' if message.get('kind') == 'stored' else 'other',
                            active_attempt=message.get('attempt') is not None, blob_sha256=None, blob_bytes=0)
            if 'relay_blob' in message:
                require(type(message['relay_blob']) is str and 224 <= len(message['relay_blob']) <= 263680,
                        'RELAY_BLOB_SHAPE')
                require(re.fullmatch('[0-9a-f]+', message['relay_blob']) is not None, 'RELAY_BLOB_SHAPE')
                blob = bytes.fromhex(message['relay_blob'])
                require(blob[:16].hex() == message['peer'], 'RELAY_RECIPIENT')
                envelope.update(blob_sha256=digest(blob), blob_bytes=len(blob))
            envelopes.append(envelope)
    for name, request in records.items():
        if name.startswith('support-request:'):
            require(type(request) is dict and request.get('id') in messages and
                    messages[request['id']]['outgoing'], 'REQUEST_LINK')
            requests += 1
    identifiers = [item['blob_sha256'] for item in envelopes if item['blob_sha256'] is not None]
    require(len(set(identifiers)) == len(identifiers), 'DUPLICATE_ENVELOPE')
    return dict(schema=1, sealed_sha256=sealed_digest.hexdigest(), sender=digest(bytes.fromhex(sender_public))[:32],
                counts=dict(counts), records=len(rows), requests=requests, retained_incoming_acks=retained_receipts,
                outgoing=envelopes)


def request_for(snapshot, nonce):
    require(hexadecimal(nonce, 64), 'NONCE')
    return dict(schema=1, nonce=nonce, sender=snapshot['sender'], sealed_sha256=snapshot['sealed_sha256'],
                envelopes=[{name: item[name] for name in ('blob_sha256', 'blob_bytes', 'recipient')}
                           for item in snapshot['outgoing'] if item['blob_sha256'] is not None])


def remote_snapshot(path, request, uid):
    require(type(request) is dict and set(request) == {'schema', 'nonce', 'sender', 'sealed_sha256', 'envelopes'} and
            type(request['schema']) is int and request['schema'] == 1 and hexadecimal(request['nonce'], 64) and
            hexadecimal(request['sender'], 32) and hexadecimal(request['sealed_sha256'], 64) and
            type(request['envelopes']) is list and len(request['envelopes']) <= 10000, 'REMOTE_REQUEST')
    expected = {}
    for item in request['envelopes']:
        require(type(item) is dict and set(item) == {'blob_sha256', 'blob_bytes', 'recipient'} and
                hexadecimal(item['blob_sha256'], 64) and hexadecimal(item['recipient'], 32) and
                type(item['blob_bytes']) is int and 112 <= item['blob_bytes'] <= 131840 and
                item['blob_sha256'] not in expected, 'REMOTE_ENVELOPE')
        expected[item['blob_sha256']] = item
    present, unrelated = 0, 0
    rows = read_rows(path, 'messages', uid)
    for ident, sender, recipient, received, body in rows:
        require(type(ident) is bytes and len(ident) == 32 and type(sender) is bytes and len(sender) == 16 and
                type(recipient) is bytes and len(recipient) == 16 and type(body) is bytes and
                112 <= len(body) <= 131840 and digest(body) == ident.hex() and body[:16] == recipient, 'SPOOL_ROW_BINDING')
        if ident.hex() in expected:
            item = expected[ident.hex()]
            require(sender.hex() == request['sender'] and recipient.hex() == item['recipient'] and
                    len(body) == item['blob_bytes'], 'REMOTE_MATCH_BINDING')
            present += 1
        elif sender.hex() == request['sender']:
            unrelated += 1
    return dict(schema=1, request_sha256=digest(encoded(request)), matched_present=present,
                absent_unknown=len(expected)-present, sender_rows_not_in_request=unrelated,
                snapshot_only=True, writer_fenced=False)


def assess(before, after, request, remote):
    require(type(remote) is dict and set(remote) == {'schema', 'request_sha256', 'matched_present',
            'absent_unknown', 'sender_rows_not_in_request', 'snapshot_only', 'writer_fenced'} and
            type(remote['schema']) is int and remote['schema'] == 1 and remote['snapshot_only'] is True and
            remote['writer_fenced'] is False and remote['request_sha256'] == digest(encoded(request)), 'REMOTE_RECEIPT')
    require(request == request_for(before, request['nonce']), 'LOCAL_REQUEST_BINDING')
    require(all(type(remote[name]) is int and 0 <= remote[name] <= 10000 for name in
                ('matched_present', 'absent_unknown', 'sender_rows_not_in_request')) and
            remote['matched_present'] + remote['absent_unknown'] == len(request['envelopes']), 'REMOTE_COUNTS')
    unchanged = before == after
    return dict(result='OBSERVED_UNFENCED' if unchanged else 'LOCAL_CHANGED_DURING_OBSERVATION',
                local_status_counts=before['counts'], outgoing=len(before['outgoing']), support_requests=before['requests'],
                prepared_envelopes=len(request['envelopes']), matched_present=remote['matched_present'],
                absent_unknown=remote['absent_unknown'], sender_rows_not_in_request=remote['sender_rows_not_in_request'],
                retained_incoming_acks=before['retained_incoming_acks'], local_unchanged=unchanged,
                active_attempts=sum(item['active_attempt'] for item in before['outgoing']),
                writer_fenced=False, external_settlement_proven=False, activation_ready=False, capture_permitted=False)
