"""Single encrypted support identity owner; only addressed text/history over local IPC."""
import argparse
import ipaddress
import json
import os
from pathlib import Path
import re
import signal
import socketserver
import stat
import threading
import time

from messenger import codec
from messenger.chat import Chat
from messenger.delivery import DeliveryController
from messenger.mailbox import MailboxError
from messenger.store import Store
from provisioning.subscription_notifications import Notifications
from provisioning.chat_transport import SystemMailbox, initialize


class SupportError(ValueError):
    pass


def unique(pairs):
    result = {}
    for name, value in pairs:
        if name in result:
            raise SupportError('invalid_request')
        result[name] = value
    return result


def canonical(value, length):
    return type(value) is str and re.fullmatch('[0-9a-f]{' + str(length) + '}', value) is not None


class SupportChat(Chat):
    def contacts(self):
        return self.authority.contacts()


class SupportStore(Store):
    def pending_outbox(self):
        pending = super().pending_outbox()
        allowed = self.authority.contacts()
        with self._lock:
            return [ident for ident in pending
                    if bytes.fromhex(self._get('message:' + ident)['peer']) in allowed
                    and self.authority.notifications.allow(ident)]


class SupportOwner:
    def __init__(self, store, sender_public):
        self.store = store
        self.chat = SupportChat(store, create_identity=False, durable_delivery=True, platform='linux')
        if self.chat.public.hex() != sender_public:
            raise SupportError('sender_mismatch')
        self.chat.authority = self
        store.authority = self
        self.notifications = Notifications(self)

    def update(self, snapshot):
        fields = {'schema', 'sequence', 'expires_at', 'sender_public', 'node', 'devices'}
        if (type(snapshot) is not dict or set(snapshot) != fields or type(snapshot['schema']) is not int or snapshot['schema'] != 1
                or type(snapshot['sequence']) is not int or not 1 <= snapshot['sequence'] <= 2**53 - 1
                or type(snapshot['expires_at']) is not int or not time.time() < snapshot['expires_at'] <= time.time() + 120
                or snapshot['sender_public'] != self.chat.public.hex()
                or type(snapshot['devices']) is not list or len(snapshot['devices']) > 550
                or type(snapshot['node']) is not dict):
            raise SupportError('invalid_binding_snapshot')
        node = snapshot['node']
        if (type(node) is not dict or set(node) != {'host', 'port', 'public_key', 'expires_at'}
                or node['expires_at'] != snapshot['expires_at']
                or type(node['port']) is not int or not 1 <= node['port'] <= 65535
                or not canonical(node['public_key'], 128)
                or type(node['host']) is not str or str(ipaddress.IPv4Address(node['host'])) != node['host']):
            raise SupportError('invalid_binding_snapshot')
        devices, addresses, identities = {}, set(), set()
        for item in snapshot['devices']:
            if (type(item) is not dict or set(item) != {'pseudonym', 'device', 'public', 'state'}
                    or not canonical(item['pseudonym'], 64) or not canonical(item['device'], 32)
                    or item['state'] not in ('verified', 'revoked', 'unregistered', 'support_not_enrolled')
                    or item['public'] is not None and not canonical(item['public'], 128)
                    or item['state'] == 'verified' and item['public'] is None
                    or item['pseudonym'] in devices or item['device'] in identities):
                raise SupportError('invalid_binding_snapshot')
            identities.add(item['device'])
            if item['public'] is not None:
                address = codec.address(bytes.fromhex(item['public'])).hex()
                if address in addresses:
                    raise SupportError('ambiguous_binding')
                addresses.add(address)
            devices[item['pseudonym']] = dict(item)
        with self.store._lock, self.store._db:
            prior = self.store._get('support-bindings')
            if snapshot == prior:
                return
            if prior is not None and (snapshot['sequence'] < prior['sequence'] or
                    snapshot['sequence'] == prior['sequence'] and snapshot != prior):
                raise SupportError('stale_binding_snapshot')
            pinned = self.store._get('support-threads') or {}
            for pseudonym, item in devices.items():
                original = pinned.get(pseudonym)
                if original is not None:
                    if original['device'] != item['device'] or original['public'] != item['public']:
                        original['blocked'] = 'identity_changed'
                    elif item['state'] == 'revoked':
                        original['blocked'] = 'revoked'
                elif item['state'] == 'verified' and item['public'] != self.chat.public.hex():
                    pinned[pseudonym] = dict(item, blocked=None)
            self.store._put('support-bindings', snapshot)
            self.store._put('support-threads', pinned)

    def binding(self, pseudonym):
        if not canonical(pseudonym, 64):
            raise SupportError('invalid_recipient')
        with self.store._lock:
            snapshot = self.store._get('support-bindings')
            thread = (self.store._get('support-threads') or {}).get(pseudonym)
            state = 'unconfirmed'
            if snapshot is not None:
                item = next((item for item in snapshot['devices'] if item['pseudonym'] == pseudonym), None)
                state = item['state'] if item is not None else 'unconfirmed'
                if time.time() >= snapshot['expires_at']:
                    state = 'binding_expired'
            if thread is not None and thread['blocked']:
                state = thread['blocked']
            return dict(pseudonym=pseudonym, state=state if thread is not None or state != 'verified' else 'unconfirmed',
                        device=thread['device'] if thread else None,
                        address=codec.address(bytes.fromhex(thread['public'])).hex() if thread else None,
                        public=thread['public'] if thread else None)

    def contacts(self):
        with self.store._lock:
            result = {}
            for pseudonym in self.store._get('support-threads') or {}:
                binding = self.binding(pseudonym)
                if binding['state'] == 'verified':
                    result[bytes.fromhex(binding['address'])] = bytes.fromhex(binding['public'])
            return result

    def send(self, pseudonym, address, request_id, actor, text):
        if (type(request_id) is not str or re.fullmatch('[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}', request_id) is None
                or type(actor) is not str or re.fullmatch('[1-9][0-9]{0,18}', actor) is None
                or type(text) is not str or not text.strip() or not 1 <= len(text.encode('utf-8')) <= codec.MAX_TEXT):
            raise SupportError('invalid_message')
        with self.store._lock, self.store._db:
            return self.enqueue(pseudonym, address, request_id, actor, text)

    def enqueue(self, pseudonym, address, request_id, source, text, *, expires_at=None):
        binding = self.binding(pseudonym)
        request = dict(pseudonym=pseudonym, address=address, text=text)
        request['actor' if type(source) is str else 'source'] = source
        if expires_at is not None:
            request['expires_at'] = expires_at
        previous = self.store._get('support-request:' + request_id)
        if previous is not None:
            if previous['request'] != request:
                raise SupportError('request_conflict')
            return dict(id=previous['id'], accepted=True)
        if binding['state'] != 'verified':
            raise SupportError(binding['state'])
        if binding['address'] != address:
            raise SupportError('recipient_mismatch')
        public = bytes.fromhex(binding['public'])
        raw = codec.pack(self.chat.identity, public, text)
        message = codec.unpack(raw, recipient=public, contacts={self.chat.address: self.chat.public})
        message.update(peer=address, require_stored=True,
                       expires_at=time.time() + 7 * 86400 if expires_at is None else expires_at)
        try:
            self.store._add(message, raw, outgoing=True)
        except ValueError:
            raise SupportError('history_full') from None
        self.store._put('support-request:' + request_id, dict(request=request, id=message['id']))
        return dict(id=message['id'], accepted=True)

    def history(self, pseudonym):
        binding = self.binding(pseudonym)
        messages = []
        for message in self.store.visible_messages():
            if message['peer'] == binding['address']:
                messages.append({key: message[key] for key in ('id', 'text', 'outgoing', 'status', 'timestamp')})
        return dict(binding=binding, messages=messages, sender=self.chat.address.hex(),
                    notifications=self.notifications.status(pseudonym))

    def inbox(self):
        with self.store._lock:
            counts = {}
            for message in self.store.visible_messages():
                if not message['outgoing']:
                    counts[message['peer']] = counts.get(message['peer'], 0) + 1
            result = []
            for pseudonym in self.store._get('support-threads') or {}:
                count = counts.get(self.binding(pseudonym)['address'], 0)
                if count:
                    result.append(dict(pseudonym=pseudonym, incoming=count))
            return result

    def invoke(self, request):
        if type(request) is not dict or set(request) != {'operation', 'arguments'} or type(request['arguments']) is not dict:
            raise SupportError('invalid_request')
        operation, arguments = request['operation'], request['arguments']
        fields = {'history': {'pseudonym'}, 'inbox': set(), 'notification_cursor': set(),
                  'send': {'pseudonym', 'address', 'request_id', 'actor', 'text'}}
        if operation not in fields or set(arguments) != fields[operation]:
            raise SupportError('invalid_request')
        return getattr(self, operation)(**arguments)

    def notification_cursor(self):
        return self.notifications.cursor()


class SupportMailbox:
    def __init__(self, owner, snapshot_path, runtime, *, snapshot_uid=None):
        self.owner, self.snapshot_path, self.runtime = owner, snapshot_path, runtime
        self.snapshot_uid = os.getuid() if snapshot_uid is None else snapshot_uid

    def refresh(self):
        descriptor = os.open(self.snapshot_path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(descriptor, 'rb') as stream:
            info = os.fstat(stream.fileno())
            if (not stat.S_ISREG(info.st_mode) or info.st_uid != self.snapshot_uid
                    or info.st_mode & 0o027 or info.st_nlink != 1 or info.st_size > 512 * 1024):
                raise SupportError('binding_unavailable')
            snapshot = json.loads(stream.read(512 * 1024 + 1), object_pairs_hook=unique)
        self.owner.update(snapshot)
        return snapshot

    def exchange(self, *, timeout=12, cancel=None):
        try:
            snapshot = self.refresh()
            mailbox = SystemMailbox(self.owner.chat, snapshot['node'], self.runtime)
        except (OSError, ValueError, KeyError):
            raise MailboxError('access_denied') from None
        try:
            return mailbox.exchange(timeout=timeout, cancel=cancel)
        finally:
            mailbox.close()


class SupportServer(socketserver.UnixStreamServer):
    def __init__(self, path, owner, mailbox, delivery):
        self.owner, self.mailbox, self.delivery = owner, mailbox, delivery
        if path.exists() or path.is_symlink():
            info = path.lstat()
            if not stat.S_ISSOCK(info.st_mode) or info.st_uid != os.getuid():
                raise SupportError('unsafe_socket')
            path.unlink()
        super().__init__(str(path), SupportHandler)
        os.chmod(path, 0o660)


class SupportHandler(socketserver.StreamRequestHandler):
    def handle(self):
        self.connection.settimeout(5)
        try:
            raw = self.rfile.readline(16385)
            if len(raw) > 16384 or not raw.endswith(b'\n'):
                raise SupportError('invalid_request')
            request = json.loads(raw, object_pairs_hook=unique)
            try:
                self.server.mailbox.refresh()
            except (OSError, ValueError, KeyError):
                if request.get('operation') == 'send':
                    raise SupportError('binding_unavailable') from None
            result = self.server.owner.invoke(request)
            if request['operation'] == 'send':
                self.server.delivery.request_sync()
            response = dict(ok=True, result=result)
        except SupportError as failure:
            response = dict(ok=False, error=str(failure))
        except Exception:
            response = dict(ok=False, error='support_unavailable')
        try:
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode() + b'\n')
        except OSError:
            pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('store', 'key', 'sender-public', 'snapshot', 'runtime', 'socket'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--snapshot-uid', type=int, default=0)
    parser.add_argument('--subscription-feed', type=Path)
    args = parser.parse_args()
    key_path = Path(args.key)
    info = key_path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_mode & 0o077 or info.st_size != 32:
        parser.error('Private external 32-byte store key required')
    store = SupportStore(args.store, key_path.read_bytes(), create=False)
    owner = SupportOwner(store, args.sender_public)
    mailbox = SupportMailbox(owner, Path(args.snapshot), initialize(args.runtime), snapshot_uid=args.snapshot_uid)
    delivery = DeliveryController(mailbox, timeout=30)
    stopped = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stopped.set())
    signal.signal(signal.SIGINT, lambda *_: stopped.set())
    try:
        with SupportServer(Path(args.socket), owner, mailbox, delivery) as server:
            server.timeout = 1
            delivery.update(online=True, foreground=True)
            next_sync = time.monotonic() + 60
            while not stopped.is_set():
                server.handle_request()
                if time.monotonic() >= next_sync:
                    if args.subscription_feed:
                        owner.notifications.refresh(args.subscription_feed, uid=args.snapshot_uid)
                    delivery.request_sync()
                    next_sync = time.monotonic() + 60
    finally:
        if delivery.close(timeout=31):
            store.close()
            Path(args.socket).unlink(missing_ok=True)


if __name__ == '__main__':
    main()
