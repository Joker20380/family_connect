"""Private reference relay store. Only public identities and encrypted configs.

Operator publishes immutable offline-signed envelopes; relay cannot mint configs.
Own database, never migrates the existing product DB. ACKs are observations, not
configuration publication authority or evidence of independent infrastructure.
"""
import base64
from contextlib import contextmanager, closing
import hashlib
import os
import secrets
import sqlite3

from . import ack
from .auth import AUDIENCE, verify
from .cache import ProvisioningCache
from .envelope import MAX_ENVELOPE_BYTES, ProvisioningRejected, public_identity
from device_identity.device import _decode


class ControlRelay:
    def __init__(self, path, *, clock):
        self.files = ProvisioningCache(path, None)
        self.clock = clock

    def initialize(self):
        self.files.path.mkdir(mode=0o700)
        fd = os.open(self.files.path / 'relay.db', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.close(fd)
        with self._db() as db:
            db.executescript('''
                CREATE TABLE devices (device TEXT PRIMARY KEY, public TEXT NOT NULL, wg TEXT NOT NULL,
                    revoked INTEGER NOT NULL DEFAULT 0);
                CREATE TABLE configs (device TEXT NOT NULL, sequence INTEGER NOT NULL, digest TEXT NOT NULL,
                    envelope BLOB NOT NULL, PRIMARY KEY(device,sequence));
                CREATE TABLE challenges (nonce TEXT PRIMARY KEY, device TEXT NOT NULL, expires INTEGER NOT NULL);
                CREATE TABLE acks (id TEXT PRIMARY KEY, device TEXT NOT NULL, raw BLOB NOT NULL);
            ''')

    @contextmanager
    def _db(self):
        with self.files._locked() as directory:
            fd = os.open('relay.db', os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
            try:
                self.files._safe(fd)
            finally:
                os.close(fd)
            # Directory is private, owner/root are trusted as for existing cache.
            with closing(sqlite3.connect(self.files.path / 'relay.db')) as db, db:
                db.execute('PRAGMA synchronous=FULL')
                db.execute('BEGIN IMMEDIATE')
                yield db

    def publish(self, *, public, wg, sequence, envelope):
        _decode(wg, 32)
        key = _decode(public, 64)
        identity = public_identity(key).hash.hex()
        if type(sequence) is not int or not 1 <= sequence < 2**63 or type(envelope) is not bytes or len(envelope) > MAX_ENVELOPE_BYTES:
            raise ValueError('invalid publication')
        with self._db() as db:
            existing = db.execute('SELECT public,wg,revoked FROM devices WHERE device=?', (identity,)).fetchone()
            if existing is not None and existing != (public, wg, 0):
                raise ValueError('device binding or revoke mismatch')
            latest = db.execute('SELECT MAX(sequence) FROM configs WHERE device=?', (identity,)).fetchone()[0]
            if latest is not None and sequence <= latest:
                raise ValueError('nonmonotonic publication')
            db.execute('INSERT OR IGNORE INTO devices VALUES (?,?,?,0)', (identity, public, wg))
            db.execute('INSERT INTO configs VALUES (?,?,?,?)',
                (identity, sequence, hashlib.sha256(envelope).hexdigest(), envelope))

    @staticmethod
    def _authorized(db, identity):
        row = db.execute('SELECT public,wg FROM devices WHERE device=? AND revoked=0', (identity,)).fetchone()
        if row is None:
            raise ProvisioningRejected('control request rejected')
        return row

    def challenge(self, *, public_identity, wireguard_public_key):
        from .envelope import public_identity as decode_identity
        identity = decode_identity(_decode(public_identity, 64)).hash.hex()
        _decode(wireguard_public_key, 32)
        now = int(self.clock())
        with self._db() as db:
            if self._authorized(db, identity) != (public_identity, wireguard_public_key):
                raise ProvisioningRejected('control request rejected')
            db.execute('DELETE FROM challenges WHERE expires<=?', (now,))
            if db.execute('SELECT COUNT(*) FROM challenges WHERE device=?', (identity,)).fetchone()[0] >= 16:
                raise ProvisioningRejected('control request rejected')
            nonce = base64.b64encode(secrets.token_bytes(32)).decode()
            db.execute('INSERT INTO challenges VALUES (?,?,?)',
                (hashlib.sha256(nonce.encode()).hexdigest(), identity, now + 120))
            return dict(challenge=nonce, audience=AUDIENCE, expires_at=now + 120)

    def fetch(self, proof):
        identity = verify(proof)
        with self._db() as db:
            if self._authorized(db, identity) != (proof['public_identity'], proof['wireguard_public_key']):
                raise ProvisioningRejected('control request rejected')
            nonce = hashlib.sha256(proof['challenge'].encode()).hexdigest()
            row = db.execute('SELECT device,expires FROM challenges WHERE nonce=?', (nonce,)).fetchone()
            if row is None or row[0] != identity or row[1] <= self.clock():
                raise ProvisioningRejected('control request rejected')
            db.execute('DELETE FROM challenges WHERE nonce=?', (nonce,))
            return bytes(db.execute('SELECT envelope FROM configs WHERE device=? ORDER BY sequence DESC LIMIT 1',
                (identity,)).fetchone()[0])

    def acknowledge(self, raw):
        body = ack.verify(raw)
        with self._db() as db:
            public, _ = self._authorized(db, body['device'])
            if public != body['public_identity']:
                raise ProvisioningRejected('control ACK rejected')
            db.execute('INSERT OR IGNORE INTO acks VALUES (?,?,?)', (body['ack_id'], body['device'], raw))
        return True

    def revoke(self, identity):
        with self._db() as db:
            db.execute('UPDATE devices SET revoked=1 WHERE device=?', (identity,))


class TestAdapter:
    """Deterministic carrier exercising the same relay proofs and signed ACKs."""
    __test__ = False
    def __init__(self, relay, device):
        self.relay, self.device = relay, device
        self.available = True

    def receive(self):
        from .auth import prove
        if not self.available:
            raise OSError('test carrier unavailable')
        challenge = self.relay.challenge(public_identity=self.device.public_identity,
            wireguard_public_key=self.device.wireguard_public_key)
        return self.relay.fetch(prove(self.device, challenge['challenge']))

    def send_ack(self, raw):
        if not self.available:
            raise OSError('test carrier unavailable')
        return self.relay.acknowledge(raw)
