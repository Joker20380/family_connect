"""One immutable chat identity per activated device. No node admission side effects."""
import base64
import hashlib
import secrets

import RNS
from device_identity.device import verify_transport_key_proof
from messenger.admission import message
from .access import Rejected, CHALLENGE_TTL, SQLiteEnrollment


class ChatTransaction:
    def __init__(self, enrollment):
        self.enrollment = enrollment
        self.database = enrollment.database
        self.placeholder = enrollment.placeholder

    def binding(self, device):
        return self.database.execute('SELECT public,support_sender FROM chat_bindings WHERE device=' +
                                     self.placeholder, (device,)).fetchone()

    def public_binding(self, public):
        return self.database.execute('SELECT device FROM chat_bindings WHERE public=' + self.placeholder,
                                     (public,)).fetchone()

    def service(self, public):
        return self.database.execute('SELECT enabled FROM chat_service_senders WHERE public=' + self.placeholder,
                                     (public,)).fetchone()

    def add_service(self, public):
        self.database.execute('INSERT INTO chat_service_senders(public,enabled) VALUES (' +
                              self.placeholder + ',1) ON CONFLICT DO NOTHING', (public,))

    def revoke_service(self, public):
        self.database.execute('UPDATE chat_service_senders SET enabled=0 WHERE public=' + self.placeholder, (public,))

    def prune_challenges(self, now):
        self.database.execute('DELETE FROM chat_challenges WHERE expires<=' + self.placeholder, (now,))

    def pending_challenges(self, device):
        return self.database.execute('SELECT COUNT(*) AS total FROM chat_challenges WHERE device=' +
            self.placeholder + ' AND used=0', (device,)).fetchone()['total']

    def add_challenge(self, nonce, device, public, expires):
        self.database.execute('INSERT INTO chat_challenges(nonce,device,public,expires,used) VALUES (' +
                              ','.join([self.placeholder] * 4) + ',0)', (nonce, device, public, expires))

    def challenge(self, nonce):
        return self.database.execute('SELECT * FROM chat_challenges WHERE nonce=' + self.placeholder, (nonce,)).fetchone()

    def bind(self, device, public):
        inserted = self.database.execute('INSERT INTO chat_bindings(device,public) VALUES (' +
            ','.join([self.placeholder] * 2) + ') ON CONFLICT DO NOTHING', (device, public)).rowcount
        if inserted != 1:
            raise Rejected()

    def consume_challenge(self, nonce):
        self.database.execute('UPDATE chat_challenges SET used=1 WHERE nonce=' + self.placeholder, (nonce,))

    def enroll_support(self, device, public):
        self.database.execute('UPDATE chat_bindings SET support_sender=' + self.placeholder +
                              ' WHERE device=' + self.placeholder, (public, device))

    def members(self):
        devices = [row['public'] for row in self.database.execute('SELECT c.public FROM chat_bindings c '
            'JOIN devices d ON d.device=c.device JOIN invites i ON i.device=c.device '
            'WHERE d.revoked=0 AND i.revoked=0 ORDER BY c.device')]
        services = [row['public'] for row in self.database.execute(
            'SELECT public FROM chat_service_senders WHERE enabled=1 ORDER BY public')]
        return list(dict.fromkeys(devices + services))

    def sequence(self):
        return self.database.execute('SELECT value FROM chat_sequence WHERE id=1').fetchone()['value']

    def advance_sequence(self):
        self.database.execute('UPDATE chat_sequence SET value=value+1 WHERE id=1')
        return self.sequence()

    def support_bindings(self):
        return self.database.execute('SELECT d.device,c.public,c.support_sender,d.revoked,'
            'EXISTS(SELECT 1 FROM invites i WHERE i.device=d.device AND i.revoked=0) AS active '
            'FROM devices d LEFT JOIN chat_bindings c ON c.device=d.device ORDER BY d.device').fetchall()


def chat_transaction(database):
    return database if isinstance(database, ChatTransaction) else SQLiteEnrollment(database).chat()


class ChatAccess:
    def __init__(self, access): self.access = access

    def initialize(self):
        # Explicit additive migration, never executed on a request or module import.
        with self.access.db() as db:
            db.execute('CREATE TABLE IF NOT EXISTS chat_bindings (device TEXT PRIMARY KEY, public TEXT UNIQUE NOT NULL)')
            if 'support_sender' not in {row[1] for row in db.execute('PRAGMA table_info(chat_bindings)')}:
                db.execute('ALTER TABLE chat_bindings ADD COLUMN support_sender TEXT')
            db.execute('''CREATE TABLE IF NOT EXISTS chat_challenges (
                nonce TEXT PRIMARY KEY, device TEXT NOT NULL, public TEXT NOT NULL,
                expires INTEGER NOT NULL, used INTEGER NOT NULL DEFAULT 0)''')
            db.execute('CREATE TABLE IF NOT EXISTS chat_sequence (id INTEGER PRIMARY KEY CHECK(id=1), value INTEGER NOT NULL)')
            db.execute('INSERT OR IGNORE INTO chat_sequence VALUES (1,0)')
            db.execute('''CREATE TABLE IF NOT EXISTS chat_service_senders (
                public TEXT PRIMARY KEY, enabled INTEGER NOT NULL CHECK(enabled IN (0,1)))''')

    @staticmethod
    def active(db, device, public_identity=None, wireguard_public_key=None):
        enrollment = chat_transaction(db).enrollment
        row = enrollment.device(device)
        grant = enrollment.device_invitation(device)
        if row is None or row['revoked'] or grant is None or grant['revoked']:
            raise Rejected()
        if public_identity is not None and (row['public'] != public_identity or row['wg'] != wireguard_public_key):
            raise Rejected()
        return row

    def challenge(self, public_identity, wireguard_public_key, chat_public):
        device = self.access.binding(public_identity, wireguard_public_key)
        nonce = base64.b64encode(secrets.token_bytes(32)).decode()
        message(chat_public, device, nonce)  # Canonical bounded fields.
        with self.access.enrollment() as enrollment:
            db = enrollment.chat()
            now = int(self.access.clock())
            self.active(db, device, public_identity, wireguard_public_key)
            binding = db.binding(device)
            if binding is not None and binding['public'] != chat_public: raise Rejected()
            db.prune_challenges(now)
            if db.pending_challenges(device) >= 8:
                raise Rejected()
            db.add_challenge(hashlib.sha256(nonce.encode()).hexdigest(), device, chat_public, now+CHALLENGE_TTL)
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
        with self.access.enrollment() as enrollment:
            db = enrollment.chat()
            now = int(self.access.clock())
            self.active(db, device, proof['public_identity'], proof['wireguard_public_key'])
            if db.service(chat_public):
                raise Rejected()
            row = db.challenge(nonce)
            if row is None or row['used'] or row['expires'] <= now or row['device'] != device or row['public'] != chat_public:
                raise Rejected()
            prior = db.binding(device)
            if prior is not None and prior['public'] != chat_public: raise Rejected()
            if prior is None: db.bind(device, chat_public)
            db.consume_challenge(nonce)
        # Registration is NOT proof that an operator has synchronized the node.
        return dict(device=device, chat_public=chat_public, status='pending-node')

    def desired_members(self):
        """Operator-only snapshot. Never expose membership via the public API."""
        with self.access.read_enrollment() as enrollment:
            return self.members(enrollment.chat())

    @staticmethod
    def members(db):
        return chat_transaction(db).members()

    def snapshot(self):
        with self.access.enrollment() as enrollment:
            db = enrollment.chat()
            keys=self.members(db)
            if len(keys)>550:raise Rejected()
            sequence=db.advance_sequence()
            return dict(sequence=sequence,expires_at=int(self.access.clock())+100,public_keys=keys)
