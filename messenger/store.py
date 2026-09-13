"""Private, encrypted SQLite history/outbox. Key supplied by the application.

Linux prototype: one owner process, thread-safe callbacks. AES-GCM protects every
row including identity and message status; record IDs/count/size remain visible.
Key storage, backup/rollback protection and mobile keystore integration are not
implemented here. Do not store the encryption key alongside the database.
"""
import fcntl
import json
import os
from pathlib import Path
import sqlite3
import stat
import threading
import uuid

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class Store:
    def __init__(self, directory, key):
        if type(key) is not bytes or len(key) != 32:
            raise ValueError('A 32-byte external storage key is required')
        root = Path(directory)
        root.mkdir(mode=0o700, parents=False, exist_ok=True)
        info = root.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
            raise ValueError('Unsafe chat directory')
        self._lock = threading.RLock()
        self._cipher = AESGCM(key)
        self._owner = None
        self._db = None
        try:
            self._owner = self._open(root / '.lock')
            fcntl.flock(self._owner, fcntl.LOCK_EX | fcntl.LOCK_NB)
            fresh = not (root / 'history.sqlite').exists()
            fd = self._open(root / 'history.sqlite')
            os.close(fd)
            self._db = sqlite3.connect(root / 'history.sqlite', check_same_thread=False)
            self._db.execute('PRAGMA journal_mode=DELETE')
            self._db.execute('PRAGMA synchronous=FULL')
            self._db.execute('PRAGMA temp_store=MEMORY')
            if fresh:
                with self._db:
                    self._db.execute('CREATE TABLE records (id TEXT PRIMARY KEY, sealed BLOB NOT NULL)')
                    self._put('meta', {'format': 1})
            if self._get('meta') != {'format': 1}:
                raise ValueError('Invalid chat store')
            # Each opening gets a new callback epoch. Old in-flight messages can
            # be retried using identical signed bytes, so receiver dedupe survives.
            self.epoch = uuid.uuid4().hex
        except BaseException:
            self.close()
            raise

    @staticmethod
    def _open(path):
        fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o600 or info.st_nlink != 1:
            os.close(fd)
            raise ValueError('Unsafe chat file')
        return fd

    def _put(self, ident, value):
        nonce = os.urandom(12)
        raw = json.dumps(value, separators=(',', ':'), ensure_ascii=False).encode()
        sealed = nonce + self._cipher.encrypt(nonce, raw, b'fc-chat-v1:' + ident.encode())
        self._db.execute('INSERT OR REPLACE INTO records VALUES (?,?)', (ident, sealed))

    def _get(self, ident):
        row = self._db.execute('SELECT sealed FROM records WHERE id=?', (ident,)).fetchone()
        if row is None:
            return None
        sealed = row[0]
        return json.loads(self._cipher.decrypt(sealed[:12], sealed[12:], b'fc-chat-v1:' + ident.encode()))

    def chat_identity(self):
        import RNS
        with self._lock, self._db:
            saved = self._get('identity')
            if saved is None:
                result = RNS.Identity()
                self._put('identity', result.get_private_key().hex())
                return result
            result = RNS.Identity.from_bytes(bytes.fromhex(saved))
            if result is None:
                raise ValueError('Invalid chat identity')
            return result

    def add(self, message, raw, *, outgoing):
        # Only callers that verified/created the signed message may insert it.
        if type(raw) is not bytes or not 96 < len(raw) <= 4608:
            raise ValueError('Invalid packed message')
        ident = 'message:' + message['id']
        with self._lock, self._db:
            if self._get(ident) is not None:
                return False
            if self._db.execute("SELECT count(*) FROM records WHERE id LIKE 'message:%'").fetchone()[0] >= 1000:
                raise ValueError('Pilot history quota reached')
            self._put(ident, dict(message, packed=raw.hex(), outgoing=outgoing,
                                 status='queued' if outgoing else 'received', attempt=None))
            return True

    def contacts(self):
        with self._lock:
            return self._get('contacts') or {}

    def save_contact(self, address, public):
        with self._lock, self._db:
            contacts = self._get('contacts') or {}
            if address not in contacts and len(contacts) >= 100:
                raise ValueError('Pilot contact quota reached')
            contacts[address] = public
            self._put('contacts', contacts)

    def messages(self):
        with self._lock:
            return [self._get(row[0]) for row in self._db.execute(
                "SELECT id FROM records WHERE id LIKE 'message:%' ORDER BY rowid").fetchall()]

    def begin_attempt(self, message_id):
        with self._lock, self._db:
            ident = 'message:' + message_id
            message = self._get(ident)
            if message is None or not message['outgoing'] or message['status'] == 'delivered':
                raise ValueError('Message is not pending')
            if message['status'] == 'sending' and message['attempt'].startswith(self.epoch + ':'):
                raise ValueError('Message is already in flight')
            token = self.epoch + ':' + uuid.uuid4().hex
            message.update(status='sending', attempt=token)
            self._put(ident, message)
            return token, bytes.fromhex(message['packed'])

    def relay_blob(self, message_id, create):
        """Persist one encrypted envelope so a lost ingress ACK can be retried."""
        with self._lock, self._db:
            ident='message:'+message_id
            message=self._get(ident)
            if message is None or not message['outgoing']:
                raise ValueError('Outgoing message required')
            if 'relay_blob' not in message:
                blob=create()
                if type(blob) is not bytes or not 112<=len(blob)<=4864:
                    raise ValueError('Invalid relay ciphertext')
                message['relay_blob']=blob.hex()
                self._put(ident,message)
            return bytes.fromhex(message['relay_blob'])

    def finish_attempt(self, message_id, token, *, delivered, relayed=False):
        if delivered and relayed:
            raise ValueError('Relay acceptance is not recipient delivery')
        with self._lock, self._db:
            ident = 'message:' + message_id
            message = self._get(ident)
            if (message is None or message['status'] != 'sending' or message['attempt'] != token
                    or not token.startswith(self.epoch + ':')):
                return False
            message.update(status='delivered' if delivered else 'relayed' if relayed else 'queued', attempt=None)
            self._put(ident, message)
            return True

    def close(self):
        with self._lock:
            if self._db is not None:
                self._db.close()
                self._db = None
            if self._owner is not None:
                os.close(self._owner)
                self._owner = None
