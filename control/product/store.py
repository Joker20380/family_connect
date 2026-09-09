"""Transactional single-host enrollment. Contains public keys, never VPN secrets.

The database path must be inside a private local operator-owned directory. This
is intentionally separate from signed laboratory catalogs and their lifecycle.
"""
import base64
import hashlib
import secrets
import os
import stat
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

from device_identity.device import verify_transport_key_proof


class EnrollmentRejected(ValueError):
    """Fixed outward-facing error; do not attach request content."""


class ProductStore:
    def __init__(self, path, *, clock=time.time):
        self.path = str(path)
        self.clock = clock

    @contextmanager
    def _transaction(self):
        self._check_storage()
        db = sqlite3.connect(Path(self.path).absolute().as_uri() + '?mode=rw',
                             uri=True, timeout=5, isolation_level=None)
        db.row_factory = sqlite3.Row
        try:
            db.execute('PRAGMA foreign_keys = ON')
            db.execute('BEGIN IMMEDIATE')
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def _check_storage(self):
        path = Path(self.path)
        parent = path.parent.lstat()
        if (not stat.S_ISDIR(parent.st_mode) or parent.st_uid != os.getuid()
                or stat.S_IMODE(parent.st_mode) != 0o700):
            raise RuntimeError('product database requires a private local directory')
        info = path.lstat()
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                or stat.S_IMODE(info.st_mode) != 0o600 or info.st_nlink != 1):
            raise RuntimeError('unsafe product database file')

    def migrate(self):
        # Called explicitly at installation, never for every incoming request.
        path = Path(self.path)
        parent = path.parent.lstat()
        if (not stat.S_ISDIR(parent.st_mode) or parent.st_uid != os.getuid()
                or stat.S_IMODE(parent.st_mode) != 0o700):
            raise RuntimeError('product database requires a private local directory')
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        except FileExistsError:
            pass
        else:
            os.close(fd)
        script = (Path(__file__).resolve().parents[1] / 'migrations/001_product.sql').read_text()
        with self._transaction() as db:
            version = db.execute('PRAGMA user_version').fetchone()[0]
            if version == 1:
                return
            if version != 0:
                raise RuntimeError('unsupported product database version')
            # Avoid executescript(), which implicitly commits an open transaction.
            for statement in script.split(';'):
                if statement.strip():
                    db.execute(statement)

    def check_ready(self):
        with self._transaction() as db:
            if db.execute('PRAGMA user_version').fetchone()[0] != 1:
                raise RuntimeError('product database migration required')

    @staticmethod
    def _audit(db, event, subject, now):
        db.execute('INSERT INTO product_audit(event, subject_id, created_at) VALUES (?, ?, ?)',
                   (event, subject, now))

    @staticmethod
    def _hash(value):
        return hashlib.sha256(value.encode('ascii')).hexdigest()

    @staticmethod
    def _public(value, size):
        if type(value) is not str or len(value) > 128:
            raise EnrollmentRejected('registration rejected')
        try:
            raw = base64.b64decode(value, validate=True)
        except ValueError:
            raise EnrollmentRejected('registration rejected') from None
        if len(raw) != size or base64.b64encode(raw).decode() != value or raw == bytes(size):
            raise EnrollmentRejected('registration rejected')
        return value

    @staticmethod
    def _token(value):
        if type(value) is not str or len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
            raise EnrollmentRejected('registration rejected')
        return value

    def create_entitlement(self, *, expires_at, device_limit=5):
        """Trusted operator operation; not exposed by the enrollment HTTP API."""
        now = int(self.clock())
        if (type(expires_at) is not int or expires_at <= now or
                type(device_limit) is not int or not 1 <= device_limit <= 100):
            raise ValueError('invalid entitlement parameters')
        family, entitlement = secrets.token_hex(16), secrets.token_hex(16)
        with self._transaction() as db:
            db.execute('INSERT INTO families VALUES (?, ?)', (family, now))
            db.execute('INSERT INTO entitlements(id,family_id,expires_at,device_limit) VALUES (?,?,?,?)',
                       (entitlement, family, expires_at, device_limit))
            self._audit(db, 'entitlement_created', entitlement, now)
        return dict(family_id=family, entitlement_id=entitlement)

    @staticmethod
    def _entitlement(db, entitlement_id, now):
        row = db.execute('SELECT * FROM entitlements WHERE id=?', (entitlement_id,)).fetchone()
        if row is None or row['revoked_at'] is not None or row['expires_at'] <= now:
            raise EnrollmentRejected('registration rejected')
        return row

    def create_invitation(self, entitlement_id, *, expires_at, max_uses=1):
        now = int(self.clock())
        if (type(expires_at) is not int or expires_at <= now or expires_at > now + 7 * 86400
                or type(max_uses) is not int or not 1 <= max_uses <= 100):
            raise ValueError('invalid invitation parameters')
        token, invitation = secrets.token_hex(32), secrets.token_hex(16)
        with self._transaction() as db:
            entitlement = self._entitlement(db, entitlement_id, now)
            if expires_at > entitlement['expires_at']:
                raise ValueError('invitation exceeds entitlement validity')
            db.execute('INSERT INTO invitations(id,token_hash,entitlement_id,created_at,expires_at,max_uses) '
                       'VALUES (?,?,?,?,?,?)',
                       (invitation, self._hash(token), entitlement_id, now, expires_at, max_uses))
            self._audit(db, 'invitation_created', invitation, now)
        # Return the bearer invitation only once. Never store/log it in plaintext.
        return dict(invitation_id=invitation, invitation_token=token, expires_at=expires_at)

    def challenge(self, *, invitation_token, public_identity, wireguard_public_key):
        token = self._token(invitation_token)
        self._public(public_identity, 64)
        self._public(wireguard_public_key, 32)
        nonce = base64.b64encode(secrets.token_bytes(32)).decode()
        with self._transaction() as db:
            now = int(self.clock())
            invitation = db.execute('SELECT * FROM invitations WHERE token_hash=?',
                                    (self._hash(token),)).fetchone()
            entitlement = self._valid_invitation(db, invitation, now)
            # Bounded live challenges per invitation. Expired rows do not hold capacity.
            count = db.execute('SELECT count(*) FROM challenges WHERE invitation_id=? '
                               'AND expires_at>? AND consumed_at IS NULL',
                               (invitation['id'], now)).fetchone()[0]
            if count >= 16:
                raise EnrollmentRejected('registration rejected')
            expiry = min(now + 120, invitation['expires_at'], entitlement['expires_at'])
            db.execute('INSERT INTO challenges(nonce_hash,invitation_id,public_identity,wireguard_public_key,'
                       'created_at,expires_at) VALUES (?,?,?,?,?,?)',
                       (self._hash(nonce), invitation['id'], public_identity, wireguard_public_key, now, expiry))
        return dict(challenge=nonce, expires_at=expiry, audience='family-connect/enrollment/v1')

    def _valid_invitation(self, db, invitation, now):
        if (invitation is None or invitation['revoked_at'] is not None or
                invitation['expires_at'] <= now or invitation['uses'] >= invitation['max_uses']):
            raise EnrollmentRejected('registration rejected')
        return self._entitlement(db, invitation['entitlement_id'], now)

    def enroll(self, proof):
        # Verify before obtaining the write lock; unknown/malformed proofs cannot
        # use the database lock while doing signature work.
        try:
            nonce = self._public(proof['challenge'], 32)
            identity = verify_transport_key_proof(proof, expected_challenge=nonce)
        except (ValueError, KeyError, TypeError):
            raise EnrollmentRejected('registration rejected') from None
        try:
            with self._transaction() as db:
                now = int(self.clock())
                challenge = db.execute('SELECT * FROM challenges WHERE nonce_hash=?',
                                       (self._hash(nonce),)).fetchone()
                if (challenge is None or challenge['consumed_at'] is not None or
                        challenge['expires_at'] <= now or
                        challenge['public_identity'] != proof['public_identity'] or
                        challenge['wireguard_public_key'] != proof['wireguard_public_key']):
                    raise EnrollmentRejected('registration rejected')
                invitation = db.execute('SELECT * FROM invitations WHERE id=?',
                                        (challenge['invitation_id'],)).fetchone()
                entitlement = self._valid_invitation(db, invitation, now)
                occupied = db.execute('SELECT count(*) FROM device_entitlements m JOIN devices d '
                                      'ON d.identity=m.device_identity WHERE m.entitlement_id=? '
                                      'AND d.revoked_at IS NULL', (entitlement['id'],)).fetchone()[0]
                if occupied >= entitlement['device_limit']:
                    raise EnrollmentRejected('registration rejected')
                # Unique constraints also prevent re-enrolling revoked identities,
                # moving devices to another family, and sharing a WG public key.
                db.execute('INSERT INTO devices(identity,public_identity,created_at) VALUES (?,?,?)',
                           (identity, proof['public_identity'], now))
                db.execute('INSERT INTO device_entitlements VALUES (?,?,?)',
                           (identity, entitlement['id'], now))
                db.execute('INSERT INTO transport_keys(id,device_identity,transport,public_key,registered_at) '
                           'VALUES (?,?,?,?,?)',
                           (secrets.token_hex(16), identity, 'wireguard', proof['wireguard_public_key'], now))
                db.execute('UPDATE challenges SET consumed_at=? WHERE nonce_hash=?', (now, self._hash(nonce)))
                db.execute('UPDATE invitations SET uses=uses+1 WHERE id=?', (invitation['id'],))
                self._audit(db, 'device_enrolled', identity, now)
                return dict(device_identity=identity, entitlement_id=entitlement['id'],
                            entitlement_revision=entitlement['revision'], status='enrolled')
        except sqlite3.IntegrityError:
            raise EnrollmentRejected('registration rejected') from None

    def authorization(self, identity):
        """Internal lookup for the future provisioning issuer; not HTTP authentication."""
        with self._transaction() as db:
            now = int(self.clock())
            row = db.execute('SELECT d.revoked_at,m.entitlement_id,k.public_key,k.revoked_at AS key_revoked '
                             'FROM devices d JOIN device_entitlements m ON d.identity=m.device_identity '
                             'JOIN transport_keys k ON d.identity=k.device_identity '
                             'WHERE d.identity=?', (identity,)).fetchone()
            if row is None or row['revoked_at'] is not None or row['key_revoked'] is not None:
                raise EnrollmentRejected('registration rejected')
            entitlement = self._entitlement(db, row['entitlement_id'], now)
            return dict(device_identity=identity, entitlement_id=entitlement['id'],
                        entitlement_revision=entitlement['revision'], expires_at=entitlement['expires_at'],
                        wireguard_public_key=row['public_key'])

    def revoke_device(self, identity):
        with self._transaction() as db:
            now = int(self.clock())
            changed = db.execute('UPDATE devices SET revoked_at=? WHERE identity=? AND revoked_at IS NULL',
                                 (now, identity)).rowcount
            db.execute('UPDATE transport_keys SET revoked_at=? WHERE device_identity=? AND revoked_at IS NULL',
                       (now, identity))
            if changed:
                self._audit(db, 'device_revoked', identity, now)

    def revoke_entitlement(self, entitlement_id):
        with self._transaction() as db:
            now = int(self.clock())
            changed = db.execute('UPDATE entitlements SET revoked_at=?,revision=revision+1 '
                                 'WHERE id=? AND revoked_at IS NULL', (now, entitlement_id)).rowcount
            if changed:
                self._audit(db, 'entitlement_revoked', entitlement_id, now)

    def revoke_invitation(self, invitation_id):
        with self._transaction() as db:
            now = int(self.clock())
            changed = db.execute('UPDATE invitations SET revoked_at=? WHERE id=? AND revoked_at IS NULL',
                                 (now, invitation_id)).rowcount
            if changed:
                self._audit(db, 'invitation_revoked', invitation_id, now)

    def prune_challenges(self):
        """Maintenance: no plaintext nonce retained, replay stays rejected after deletion."""
        with self._transaction() as db:
            return db.execute('DELETE FROM challenges WHERE expires_at<=?', (int(self.clock()),)).rowcount
