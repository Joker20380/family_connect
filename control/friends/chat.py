"""One immutable chat identity per activated device. No node admission side effects."""
import base64
import hashlib
import secrets
import sqlite3

import RNS
from device_identity.device import verify_transport_key_proof
from messenger.admission import message
from .access import Rejected, CHALLENGE_TTL


class ChatAccess:
    def __init__(self, access): self.access = access

    def initialize(self):
        # Explicit additive migration, never executed on a request or module import.
        with self.access.db() as db:
            db.execute('CREATE TABLE IF NOT EXISTS chat_bindings (device TEXT PRIMARY KEY, public TEXT UNIQUE NOT NULL)')
            db.execute('''CREATE TABLE IF NOT EXISTS chat_challenges (
                nonce TEXT PRIMARY KEY, device TEXT NOT NULL, public TEXT NOT NULL,
                expires INTEGER NOT NULL, used INTEGER NOT NULL DEFAULT 0)''')
            db.execute('CREATE TABLE IF NOT EXISTS chat_sequence (id INTEGER PRIMARY KEY CHECK(id=1), value INTEGER NOT NULL)')
            db.execute('INSERT OR IGNORE INTO chat_sequence VALUES (1,0)')

    @staticmethod
    def active(db, device, public_identity=None, wireguard_public_key=None):
        row = db.execute('SELECT * FROM devices WHERE device=?', (device,)).fetchone()
        grant = db.execute('SELECT revoked FROM invites WHERE device=?', (device,)).fetchone()
        if row is None or row['revoked'] or grant is None or grant['revoked']:
            raise Rejected()
        if public_identity is not None and (row['public'] != public_identity or row['wg'] != wireguard_public_key):
            raise Rejected()
        return row

    def challenge(self, public_identity, wireguard_public_key, chat_public):
        device = self.access.binding(public_identity, wireguard_public_key)
        nonce = base64.b64encode(secrets.token_bytes(32)).decode()
        message(chat_public, device, nonce)  # Canonical bounded fields.
        now = int(self.access.clock())
        with self.access.db() as db:
            self.active(db, device, public_identity, wireguard_public_key)
            binding = db.execute('SELECT public FROM chat_bindings WHERE device=?', (device,)).fetchone()
            if binding is not None and binding['public'] != chat_public: raise Rejected()
            db.execute('DELETE FROM chat_challenges WHERE expires<=?', (now,))
            if db.execute('SELECT COUNT(*) FROM chat_challenges WHERE device=? AND used=0', (device,)).fetchone()[0] >= 8:
                raise Rejected()
            db.execute('INSERT INTO chat_challenges VALUES (?,?,?,?,0)',
                       (hashlib.sha256(nonce.encode()).hexdigest(), device, chat_public, now+CHALLENGE_TTL))
        return dict(challenge=nonce, expires_at=now+CHALLENGE_TTL, audience='family-connect/enrollment/v1',
                    device=device, chat_public=chat_public)

    def register(self, proof, chat_public, chat_signature):
        device = verify_transport_key_proof(proof, expected_challenge=proof['challenge'])
        payload = message(chat_public, device, proof['challenge'])
        if type(chat_signature) is not str or len(chat_signature) != 128: raise Rejected()
        signature = bytes.fromhex(chat_signature)
        if signature.hex() != chat_signature: raise Rejected()
        identity = RNS.Identity(create_keys=False)
        identity.load_public_key(bytes.fromhex(chat_public))
        if not identity.validate(signature, payload): raise Rejected()
        nonce = hashlib.sha256(proof['challenge'].encode()).hexdigest()
        now = int(self.access.clock())
        with self.access.db() as db:
            self.active(db, device, proof['public_identity'], proof['wireguard_public_key'])
            row = db.execute('SELECT * FROM chat_challenges WHERE nonce=?', (nonce,)).fetchone()
            if row is None or row['used'] or row['expires'] <= now or row['device'] != device or row['public'] != chat_public:
                raise Rejected()
            prior = db.execute('SELECT public FROM chat_bindings WHERE device=?', (device,)).fetchone()
            if prior is not None and prior['public'] != chat_public: raise Rejected()
            try:
                if prior is None: db.execute('INSERT INTO chat_bindings VALUES (?,?)', (device, chat_public))
            except sqlite3.IntegrityError: raise Rejected() from None
            db.execute('UPDATE chat_challenges SET used=1 WHERE nonce=?', (nonce,))
        # Registration is NOT proof that an operator has synchronized the node.
        return dict(device=device, chat_public=chat_public, status='pending-node')

    def desired_members(self):
        """Operator-only snapshot. Never expose membership via the public API."""
        with self.access.db() as db:
            return [row[0] for row in db.execute('''SELECT c.public FROM chat_bindings c
                JOIN devices d ON d.device=c.device JOIN invites i ON i.device=c.device
                WHERE d.revoked=0 AND i.revoked=0 ORDER BY c.device''')]

    def snapshot(self):
        with self.access.db() as db:
            keys=[row[0] for row in db.execute('''SELECT c.public FROM chat_bindings c
                JOIN devices d ON d.device=c.device JOIN invites i ON i.device=c.device
                WHERE d.revoked=0 AND i.revoked=0 ORDER BY c.device''')]
            if len(keys)>550:raise Rejected()
            db.execute('UPDATE chat_sequence SET value=value+1 WHERE id=1')
            sequence=db.execute('SELECT value FROM chat_sequence WHERE id=1').fetchone()[0]
            return dict(sequence=sequence,expires_at=int(self.access.clock())+100,public_keys=keys)
