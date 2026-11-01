"""Local one-time synthetic enrollment. No public endpoint or transport issuance."""

import base64
import os
from pathlib import Path
import secrets
import sqlite3
import time

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from .contracts import canonical, digest, exact, fail, load, typed

BINDING = dict(instance_id='id', logical_gateway='id', bundle_id='id', provider='id', region='id',
               ipv4='ipv4?', roles='roles')


def binding_check(binding):
    exact(binding, BINDING)
    if not all(typed(binding[key], kind) for key, kind in BINDING.items()) or not binding['roles']:
        fail('enrollment_binding')


def generate_node_key(path):
    path = Path(path)
    if any(parent.is_symlink() for parent in [path] + list(path.parents)):
        fail('node_key_path')
    key = Ed25519PrivateKey.generate()
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'wb') as output:
        output.write(key.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption()))
        output.flush()
        os.fsync(output.fileno())
    return key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex()


def proof_payload(binding, challenge, public_key):
    return canonical(dict(schema=1, purpose='synthetic-instance-enrollment', binding=binding,
                          challenge=challenge, public_key=public_key))


def verify_receipt(receipt, authority, binding):
    binding_check(binding)
    exact(receipt, ('body','signature'))
    body=receipt['body']
    exact(body, ('schema','scope','binding','public_key','enrolled_at','transport_issuance'))
    if (type(body['schema']) is not int or body['schema']!=1 or body['scope']!='synthetic'
            or body['binding']!=binding or not typed(body['public_key'],'hash')
            or type(body['enrolled_at']) is not int or not 0<=body['enrolled_at']<=time.time()+60
            or body['transport_issuance'] is not False):
        fail('instance_receipt_binding')
    try:
        authority.verify(base64.b64decode(receipt['signature'],validate=True),canonical(body))
    except (ValueError,InvalidSignature):
        fail('instance_receipt_signature')
    return digest(bytes.fromhex(body['public_key']))


class EnrollmentStore:
    def __init__(self, path, authority, clock=time.time):
        self.path = Path(path)
        if self.path.is_symlink() or self.path.exists() and self.path.stat().st_nlink != 1:
            fail('enrollment_store_path')
        if not self.path.exists():
            os.close(os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600))
        if self.path.stat().st_mode & 0o077:
            fail('enrollment_store_permissions')
        self.authority = authority
        self.clock = clock
        with self.connect() as database:
            database.executescript('''
                CREATE TABLE IF NOT EXISTS tokens (
                    hash TEXT PRIMARY KEY, binding TEXT NOT NULL, challenge TEXT NOT NULL,
                    expires INTEGER NOT NULL, state TEXT NOT NULL CHECK(state IN ('NEW','USED','CANCELLED')));
                CREATE TABLE IF NOT EXISTS identities (
                    instance TEXT PRIMARY KEY, public_key TEXT UNIQUE NOT NULL, receipt TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS audit (sequence INTEGER PRIMARY KEY, event TEXT NOT NULL,
                    token_hash TEXT NOT NULL, occurred INTEGER NOT NULL);
                CREATE TRIGGER IF NOT EXISTS audit_no_update BEFORE UPDATE ON audit BEGIN SELECT RAISE(ABORT,'immutable'); END;
                CREATE TRIGGER IF NOT EXISTS audit_no_delete BEFORE DELETE ON audit BEGIN SELECT RAISE(ABORT,'immutable'); END;
            ''')

    def connect(self):
        return sqlite3.connect(self.path, timeout=5)

    def issue(self, binding, lifetime=600):
        binding_check(binding)
        if type(lifetime) is not int or not 1 <= lifetime <= 600:
            fail('enrollment_lifetime')
        raw = secrets.token_urlsafe(32)
        token_hash = digest(raw.encode())
        challenge = secrets.token_hex(32)
        expires = int(self.clock()) + lifetime
        with self.connect() as database:
            database.execute('INSERT INTO tokens VALUES (?,?,?,?,?)', (token_hash, canonical(binding).decode(), challenge, expires, 'NEW'))
            database.execute('INSERT INTO audit(event,token_hash,occurred) VALUES (?,?,?)', ('ISSUED',token_hash,int(self.clock())))
        return raw, dict(challenge=challenge, expires_at=expires, scope='synthetic')

    def cancel(self, raw):
        token_hash = digest(raw.encode())
        with self.connect() as database:
            database.execute('BEGIN IMMEDIATE')
            changed = database.execute("UPDATE tokens SET state='CANCELLED' WHERE hash=? AND state='NEW'", (token_hash,)).rowcount
            if changed != 1:
                fail('enrollment_not_cancellable')
            database.execute('INSERT INTO audit(event,token_hash,occurred) VALUES (?,?,?)', ('CANCELLED',token_hash,int(self.clock())))

    def enroll(self, raw, binding, public_key, signature):
        binding_check(binding)
        if not typed(public_key, 'hash'):
            fail('enrollment_public_key')
        token_hash = digest(raw.encode())
        with self.connect() as database:
            database.execute('BEGIN IMMEDIATE')
            row = database.execute('SELECT binding,challenge,expires,state FROM tokens WHERE hash=?', (token_hash,)).fetchone()
            if not row or row[3] != 'NEW' or int(self.clock()) >= row[2]:
                fail('enrollment_expired_used_or_cancelled')
            if canonical(binding).decode() != row[0]:
                fail('enrollment_binding_mismatch')
            try:
                Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key)).verify(signature, proof_payload(binding,row[1],public_key))
            except (ValueError, InvalidSignature):
                fail('enrollment_possession')
            if database.execute('SELECT 1 FROM identities WHERE instance=? OR public_key=?', (binding['instance_id'],public_key)).fetchone():
                fail('enrollment_identity_exists')
            body = dict(schema=1, scope='synthetic', binding=binding, public_key=public_key,
                        enrolled_at=int(self.clock()), transport_issuance=False)
            receipt = dict(body=body, signature=base64.b64encode(self.authority.sign(canonical(body))).decode())
            database.execute('INSERT INTO identities VALUES (?,?,?)', (binding['instance_id'], public_key, canonical(receipt).decode()))
            database.execute("UPDATE tokens SET state='USED' WHERE hash=?", (token_hash,))
            database.execute('INSERT INTO audit(event,token_hash,occurred) VALUES (?,?,?)', ('ENROLLED',token_hash,int(self.clock())))
        return receipt
