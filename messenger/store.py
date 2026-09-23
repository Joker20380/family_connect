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

class Store:
    def __init__(self, directory, key=None, *, create=None, cipher=None):
        # Native enrollment must distinguish a new account from damaged/missing
        # existing state. None retains the prototype's open-or-create API.
        if create is not None and type(create) is not bool:
            raise ValueError('Explicit store creation mode required')
        if cipher is None:
            if type(key) is not bytes or len(key) != 32:
                raise ValueError('A 32-byte external storage key is required')
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            cipher = AESGCM(key)
        elif key is not None or not all(callable(getattr(cipher, name, None)) for name in ('encrypt', 'decrypt')):
            raise ValueError('Exactly one storage cipher is required')
        root = Path(directory)
        if create is not False:
            root.mkdir(mode=0o700, parents=False, exist_ok=create is None)
        info = root.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
            raise ValueError('Unsafe chat directory')
        self._lock = threading.RLock()
        # Android supplies the same AES-GCM format through a Java callback;
        # its storage key never needs to enter Python or a serialized request.
        self._cipher = cipher
        self._owner = None
        self._db = None
        try:
            self._owner = self._open(root / '.lock', create=create is not False)
            fcntl.flock(self._owner, fcntl.LOCK_EX | fcntl.LOCK_NB)
            fresh = not (root / 'history.sqlite').exists()
            fd = self._open(root / 'history.sqlite', create=create is not False)
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
    def _open(path, *, create=True):
        flags = os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK
        fd = os.open(path, flags | (os.O_CREAT if create else 0), 0o600)
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o600 or info.st_nlink != 1:
            os.close(fd)
            raise ValueError('Unsafe chat file')
        return fd

    def _put(self, ident, value):
        nonce = os.urandom(12)
        raw = json.dumps(value, separators=(',', ':'), ensure_ascii=False).encode()
        sealed = nonce + self._cipher.encrypt(nonce, raw, b'fc-chat-v1:' + ident.encode())
        # Preserve insertion order when status changes; REPLACE moves the row.
        self._db.execute('INSERT INTO records VALUES (?,?) ON CONFLICT(id) '
                         'DO UPDATE SET sealed=excluded.sealed', (ident, sealed))

    def _get(self, ident):
        row = self._db.execute('SELECT sealed FROM records WHERE id=?', (ident,)).fetchone()
        if row is None:
            return None
        sealed = row[0]
        return json.loads(self._cipher.decrypt(sealed[:12], sealed[12:], b'fc-chat-v1:' + ident.encode()))

    def chat_identity(self, *, create=True):
        import RNS
        with self._lock, self._db:
            saved = self._get('identity')
            if saved is None:
                if not create:
                    raise ValueError('Chat identity unavailable')
                result = RNS.Identity()
                self._put('identity', result.get_private_key().hex())
                return result
            result = RNS.Identity.from_bytes(bytes.fromhex(saved))
            if result is None:
                raise ValueError('Invalid chat identity')
            return result

    def add(self, message, raw, *, outgoing):
        # Only callers that verified/created the signed message may insert it.
        if type(raw) is not bytes or not 96 < len(raw) <= 131584:
            raise ValueError('Invalid packed message')
        ident = 'message:' + message['id']
        with self._lock, self._db:
            if self._get(ident) is not None:
                return False
            if self._db.execute("SELECT count(*) FROM records WHERE id LIKE 'message:%'").fetchone()[0] >= 1000:
                raise ValueError('Pilot history quota reached')
            if not outgoing and message.get('kind')=='edit':
                original=next((m for m in self.visible_messages() if m['id']==message['target']),None)
                if original is not None and not original['outgoing'] and original['peer']==message['peer'] and message['revision']>original.get('revision',0):
                    state=self._get('inbox') or {};state[message['target']]={'read':False,'notified':False};self._put('inbox',state)
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

    def contact_names(self):
        with self._lock:
            return self._get('contact-names') or {}

    def rename_contact(self, address, name):
        with self._lock, self._db:
            if address not in self.contacts(): raise ValueError('Unknown contact')
            names = self.contact_names()
            if name: names[address] = name
            else: names.pop(address, None)
            self._put('contact-names', names)

    def messages(self):
        with self._lock:
            return [self._get(row[0]) for row in self._db.execute(
                "SELECT id FROM records WHERE id LIKE 'message:%' ORDER BY rowid").fetchall()]

    def visible_messages(self):
        messages=self.messages();visible=[dict(m) for m in messages if m.get('kind')!='edit'];known={m['id']:m for m in visible}
        for edit in messages:
            if edit.get('kind')!='edit':continue
            original=known.get(edit['target'])
            if original is None or original.get('kind')=='audio' or original['peer']!=edit['peer'] or original['outgoing']!=edit['outgoing']:continue
            if edit['revision']<=original.get('revision',0):continue
            original.update(text=edit['text'],revision=edit['revision'],edited=True)
            if original['outgoing']:original.update(status=edit['status'],attempt=edit['attempt'])
        return visible

    def inbox(self):
        """Encrypted read/delivery flags; migrate old history silently once."""
        with self._lock, self._db:
            messages = self.visible_messages()
            state = self._get('inbox')
            if state is None:
                state = {m['id']: {'read': True, 'notified': True} for m in messages if not m['outgoing']}
                self._put('inbox', state)
            return [dict(m, **state.get(m['id'], {'read': False, 'notified': False}))
                    for m in messages if not m['outgoing']]

    def inbox_mark(self, ids, flag):
        if flag not in ('read', 'notified') or type(ids) is not list or len(ids) > 1000 or any(type(i) is not str for i in ids):
            raise ValueError('Invalid inbox update')
        with self._lock, self._db:
            messages = self.inbox()
            state = self._get('inbox')
            wanted = set(ids)
            for message in messages:
                if message['id'] in wanted:
                    value = state.setdefault(message['id'], {'read': False, 'notified': False})
                    value[flag] = True
                    if flag == 'read': value['notified'] = True
            self._put('inbox', state)

    def service_events(self, incoming=None):
        with self._lock, self._db:
            events = self._get('service-events') or []
            if incoming is not None:
                known = {event['id']: event for event in events}
                for event in incoming:
                    if event['id'] in known:
                        original = {k: v for k, v in known[event['id']].items() if k not in ('read', 'notified')}
                        revision=event.get('revision',1);previous=original.get('revision',1)
                        if revision<previous: continue
                        if revision>previous:
                            if any(event[k]!=original[k] for k in ('created','expires','author','kind','platforms')): raise ValueError('Changed service identity')
                            known[event['id']].clear();known[event['id']].update(event,read=False,notified=False)
                        else:
                            left={k:v for k,v in original.items() if k not in ('revision','updated','editor')}
                            right={k:v for k,v in event.items() if k not in ('revision','updated','editor')}
                            if left!=right: raise ValueError('Changed service event')
                            if 'revision' in original and 'revision' in event and original!=event: raise ValueError('Changed service revision')
                            if 'revision' in event: known[event['id']].update(event)
                    else:
                        value = dict(event, read=False, notified=False)
                        events.append(value);known[event['id']] = value
                if len(events) > 1000: raise ValueError('Service history quota reached')
                self._put('service-events', events)
            return events

    def service_mark(self, ids, flag):
        if flag not in ('read', 'notified') or type(ids) is not list or len(ids) > 1000 or any(type(i) is not str for i in ids):
            raise ValueError('Invalid service update')
        with self._lock, self._db:
            events = self.service_events()
            for event in events:
                if event['id'] in ids:
                    event[flag] = True
                    if flag == 'read': event['notified'] = True
            self._put('service-events', events)

    def pending_outbox(self):
        """Stable IDs only; never automatically resend a relay-accepted message.

        A sending record from a previous owner epoch can retry its original bytes.
        A current-epoch attempt belongs to the existing in-flight worker.
        """
        with self._lock:
            return [message['id'] for message in self.messages()
                    if message['outgoing'] and (message['status'] == 'queued'
                    or (message['status'] == 'sending'
                        and not (message['attempt'] or '').startswith(self.epoch + ':')))]

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
                if type(blob) is not bytes or not 112<=len(blob)<=131840:
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
