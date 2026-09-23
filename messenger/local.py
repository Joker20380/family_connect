"""Serialized local API for a native chat owner, without network or VPN effects.

The owner supplies its unwrapped storage key and explicitly chooses enrollment
or resume. Never retry a failed resume with create=True. Public methods return
UI data only; packed plaintext, private keys and retry tokens stay in the core.
Close the future carrier/worker before closing this owner.
"""
import hashlib
import base64
import threading

from . import codec
from .chat import Chat
from .store import Store


class LocalError(Exception):
    """Stable codes only: safe for native UI, never an underlying exception text."""


def _hex(value, size):
    if type(value) is not str or len(value) != size * 2:
        raise LocalError('invalid_input')
    try:
        raw = bytes.fromhex(value)
    except ValueError:
        raise LocalError('invalid_input') from None
    if len(raw) != size or raw.hex() != value:
        raise LocalError('invalid_input')
    return raw


def contact_card(public):
    """Preview only. Caller must arrange independent fingerprint verification."""
    raw = _hex(public, 64)
    try:
        address = codec.address(raw).hex()
    except Exception:
        raise LocalError('invalid_input') from None
    return dict(address=address, public=public,
                fingerprint=hashlib.sha256(raw).hexdigest())


class LocalChat:
    def __init__(self, directory, key=None, *, create, cipher=None):
        if type(create) is not bool:
            raise LocalError('invalid_input')
        self._lock = threading.RLock()
        self._store = self._chat = None
        self._delivery = None
        self._closing = False
        try:
            self._store = Store(directory, key, create=create, cipher=cipher)
            self._chat = Chat(self._store, create_identity=create)
            # Detect damaged encrypted records before exposing a usable account.
            self._store.contacts()
            self._store.messages()
            self._store.inbox()
        except Exception:
            self.close()
            raise LocalError('store_unavailable') from None

    def _require_open(self):
        if self._chat is None:
            raise LocalError('closed')
        if self._closing:
            raise LocalError('closing')

    def profile(self):
        with self._lock:
            self._require_open()
            return contact_card(self._chat.public.hex())

    def enrollment_proof(self, device, challenge):
        from .admission import message
        with self._lock:
            self._require_open()
            public = self._chat.public.hex()
            try:
                signature = self._chat.identity.sign(message(public, device, challenge)).hex()
                return dict(chat_public=public, chat_signature=signature)
            except Exception:
                raise LocalError('invalid_input') from None

    def trust_contact(self, public, fingerprint):
        # A pasted address alone is insufficient: retain the full verified key.
        card = contact_card(public)
        _hex(fingerprint, 32)
        if fingerprint != card['fingerprint']:
            raise LocalError('fingerprint_mismatch')
        with self._lock:
            self._require_open()
            if public == self._chat.public.hex():
                raise LocalError('own_contact')
            try:
                self._chat.trust_contact(bytes.fromhex(public))
            except Exception:
                raise LocalError('contact_not_saved') from None
            if self._delivery is not None:
                self._delivery.request_sync()
            return card

    def contacts(self):
        with self._lock:
            self._require_open()
            try:
                cards = [contact_card(public) for public in self._store.contacts().values()]
                names = self._store.contact_names()
                for card in cards:
                    if card['address'] in names: card['name'] = names[card['address']]
                return cards
            except Exception:
                raise LocalError('store_unavailable') from None

    def rename_contact(self, address, name):
        _hex(address, 16)
        if type(name) is not str or len(name) > 80 or any(ord(c) < 32 or c in '\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069' for c in name):
            raise LocalError('invalid_input')
        with self._lock:
            self._require_open()
            try: self._store.rename_contact(address, name.strip())
            except ValueError: raise LocalError('unverified_contact') from None
            return next(card for card in self.contacts() if card['address'] == address)

    def queue(self, address, text):
        recipient = _hex(address, 16)
        if type(text) is not str:
            raise LocalError('invalid_input')
        try:
            valid = 0 < len(text.encode('utf-8')) <= codec.MAX_TEXT
        except UnicodeEncodeError:
            valid = False
        if not valid:
            raise LocalError('invalid_input')
        with self._lock:
            self._require_open()
            try:
                if recipient not in self._chat.contacts():
                    raise LocalError('unverified_contact')
                ident = self._chat.queue(recipient, text)
                if self._delivery is not None:
                    self._delivery.request_sync()
                return ident
            except LocalError:
                raise
            except Exception:
                raise LocalError('message_not_saved') from None

    def edit_message(self, address, message_id, text):
        recipient=_hex(address,16);_hex(message_id,32)
        if type(text) is not str or not 0<len(text.encode('utf-8'))<=codec.MAX_TEXT:raise LocalError('invalid_input')
        with self._lock:
            self._require_open()
            original=next((m for m in self._store.visible_messages() if m['id']==message_id),None)
            if original is None or not original['outgoing'] or original['peer']!=address or original.get('kind')=='audio':raise LocalError('invalid_input')
            import LXMF
            fields={LXMF.FIELD_CUSTOM_DATA:dict(fc=1,type='edit',target=message_id,revision=original.get('revision',0)+1)}
            ident=self._chat.queue(recipient,text,fields=fields)
            if self._delivery is not None:self._delivery.request_sync()
            return ident

    def queue_audio(self, address, audio):
        recipient=_hex(address,16)
        if type(audio) is not str or len(audio)>175000:raise LocalError('invalid_input')
        try:raw=codec.finalize_recorded_opus(base64.b64decode(audio,validate=True))
        except (ValueError,TypeError):raise LocalError('invalid_input') from None
        with self._lock:
            self._require_open()
            if recipient not in self._chat.contacts():raise LocalError('unverified_contact')
            import LXMF
            ident=self._chat.queue(recipient,'',fields={LXMF.FIELD_AUDIO:[LXMF.AM_OPUS_OGG,raw]})
            if self._delivery is not None:self._delivery.request_sync()
            return ident

    def audio(self, message_id):
        _hex(message_id,32)
        with self._lock:
            self._require_open()
            message=next((m for m in self._store.messages() if m['id']==message_id and m.get('kind')=='audio'),None)
            if message is None:raise LocalError('invalid_input')
            return dict(audio=message['audio'],duration_ms=message['duration_ms'])

    def history(self, address, *, offset=0, limit=50):
        _hex(address, 16)
        if type(offset) is not int or not 0 <= offset <= 1000 or type(limit) is not int or not 1 <= limit <= 100:
            raise LocalError('invalid_input')
        with self._lock:
            self._require_open()
            try:
                messages = [m for m in self._store.visible_messages() if m['peer'] == address]
                result = []
                for message in messages[offset:offset + limit]:
                    item = {k: message[k] for k in ('id', 'peer', 'text', 'timestamp', 'outgoing', 'status')}
                    item.update({k:message[k] for k in ('kind','duration_ms','edited','revision') if k in message})
                    if item['status'] == 'sending' and not (message['attempt'] or '').startswith(self._store.epoch + ':'):
                        item['status'] = 'queued'
                    result.append(item)
                return dict(messages=result, total=len(messages),
                            next_offset=offset + len(result) if offset + len(result) < len(messages) else None)
            except Exception:
                raise LocalError('store_unavailable') from None

    def inbox(self):
        with self._lock:
            self._require_open()
            return [{k: m[k] for k in ('id', 'peer', 'text', 'timestamp', 'read', 'notified')}
                    for m in self._store.inbox()]

    def mark_inbox(self, ids, flag):
        with self._lock:
            self._require_open()
            try: self._store.inbox_mark(ids, flag)
            except ValueError: raise LocalError('invalid_input') from None
            return True

    def service_events(self):
        with self._lock:
            self._require_open()
            return self._store.service_events()

    def import_events(self, feed):
        from .service_events import validate_feed
        with self._lock:
            self._require_open()
            try: return self._store.service_events(validate_feed(feed, platform='android'))
            except ValueError: raise LocalError('invalid_input') from None

    def mark_events(self, ids, flag):
        with self._lock:
            self._require_open()
            try: self._store.service_mark(ids, flag)
            except ValueError: raise LocalError('invalid_input') from None
            return True

    def attach_delivery(self, source, node_public, **limits):
        """Native carrier supplies a trusted node and this identity's IN destination.

        No network opens until lifecycle update allows foreground/online work.
        This binding is not exposed as a caller-controlled JSON operation.
        """
        from .delivery import DeliveryController
        from .mailbox import Mailbox
        with self._lock:
            self._require_open()
            if self._delivery is not None:
                raise LocalError('delivery_already_attached')
            self._delivery = DeliveryController(Mailbox(self._chat, source, node_public), **limits)

    def delivery_update(self, *, online, foreground):
        with self._lock:
            self._require_open()
            if self._delivery is None:
                raise LocalError('delivery_unavailable')
            return self._delivery.update(online=online, foreground=foreground)

    def attach_carrier(self, factory, **limits):
        """Trusted platform code constructs/owns a mailbox for this private Chat."""
        from .delivery import DeliveryController
        with self._lock:
            self._require_open()
            if self._delivery is not None:
                raise LocalError('delivery_already_attached')
            carrier = factory(self._chat)
            try:
                self._delivery = DeliveryController(carrier, **limits)
            except BaseException:
                carrier.close()
                raise
            return carrier

    def request_sync(self):
        with self._lock:
            self._require_open()
            if self._delivery is None:
                raise LocalError('delivery_unavailable')
            return self._delivery.request_sync()

    def delivery_state(self):
        from dataclasses import asdict
        with self._lock:
            self._require_open()
            if self._delivery is None:
                return dict(attached=False)
            snapshot = self._delivery.snapshot()
            if snapshot['result'] is not None:
                snapshot['result'] = asdict(snapshot['result'])
            return dict(attached=True, **snapshot)

    def close(self, *, timeout=31):
        with self._lock:
            self._closing = True
            if self._delivery is not None and not self._delivery.close(timeout=timeout):
                # A live worker may still be committing records. Keep key/Store
                # owned, refuse new operations and let the caller retry close.
                raise LocalError('close_pending')
            if self._store is not None:
                self._store.close()
            self._store = self._chat = None
            self._delivery = None
