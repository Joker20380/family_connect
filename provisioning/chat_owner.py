"""One Linux chat owner, bound to the existing computer identity and user vault."""
import fcntl
import json
import os
from pathlib import Path
import stat
import time

from messenger.local import LocalChat, LocalError, contact_card
from .chat_keyring import ChatKeyring, KeyringUnavailable
from .chat_transport import initialize, SystemMailbox, ExistingExitMailbox, ProtectedMailbox
from .chat_events import fetch_events, notification_batches
from .friends import FriendsClient, FriendsError


class ChatOwner:
    def __init__(self, directory, friends, *, keyring=None, runtime_factory=initialize,
                 mailbox_factory=SystemMailbox, events_fetcher=fetch_events, restricted_factory=None, direct_factory=None):
        if direct_factory is not None and restricted_factory is None:
            raise ValueError('Protected chat requires an explicit existing-exit boundary')
        self.directory = Path(directory)
        self.friends = friends
        self.keyring = keyring or ChatKeyring()
        self.runtime_factory, self.mailbox_factory = runtime_factory, mailbox_factory
        self.events_fetcher = events_fetcher
        self.local = self.carrier = self.runtime = self.device = None
        self.lock = None
        self.node = None
        self.registration_route = None
        self.next_enrollment = self.next_sync = 0
        self.delivery_error = None
        self.next_events = 0
        self.events_error = False
        self.restricted_factory, self.restricted = restricted_factory, None
        self.direct_factory, self.direct = direct_factory, None

    def open(self, *, create=False):
        if self.local is not None:
            return self.local.profile()
        try:
            self.device = self.friends._device(False)
        except (OSError, ValueError):
            raise LocalError('identity_unavailable') from None
        if not self.directory.exists() and not create:
            raise LocalError('not_created')
        try:
            self.directory.mkdir(mode=0o700, exist_ok=True)
            info = self.directory.lstat()
            if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
                raise LocalError('store_unavailable')
            self.lock = os.open(self.directory / '.owner', os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
            info = os.fstat(self.lock)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o600:
                raise LocalError('store_unavailable')
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            binding = self.directory / 'account.json'
            if create:
                if binding.exists() or (self.directory / 'store').exists():
                    raise LocalError('store_unavailable')
            else:
                descriptor = os.open(binding, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
                with os.fdopen(descriptor, 'rb') as source:
                    info = os.fstat(source.fileno())
                    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o600:
                        raise LocalError('store_unavailable')
                    raw = source.read(1025)
                if len(raw) > 1024:
                    raise LocalError('store_unavailable')
                value = json.loads(raw, object_pairs_hook=FriendsClient._object)
                if (type(value) is not dict or type(value.get('schema')) is not int or
                        value != {'schema': 1, 'device': self.device.reference}):
                    raise LocalError('identity_mismatch')
            key = self.keyring.key(self.device.reference, create=create)
            self.runtime = self.runtime_factory(self.directory / 'runtime')
            if create:
                descriptor = os.open(binding, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
                with os.fdopen(descriptor, 'w') as target:
                    json.dump({'schema': 1, 'device': self.device.reference}, target)
                    target.flush()
                    os.fsync(target.fileno())
            self.local = LocalChat(self.directory / 'store', key, create=create, platform='linux', version=2011)
            self.local._chat.durable_delivery = True
            if self.restricted_factory is not None:
                self.restricted = self.restricted_factory(self.device.reference)
            if self.direct_factory is not None:
                self.direct = self.direct_factory(self.device.reference)
            return self.local.profile()
        except Exception as failure:
            self.close()
            if isinstance(failure, KeyringUnavailable):
                raise LocalError('keyring_unavailable') from None
            if isinstance(failure, LocalError):
                raise
            raise LocalError('store_unavailable') from None

    def invoke(self, operation, **arguments):
        if self.local is None:
            raise LocalError('closed')
        signatures = {'profile': (), 'contacts': (), 'inbox': (), 'preview_contact': ('public',),
                      'inbox_summary': (), 'event_counts': (), 'service_events_page': ('offset', 'limit'),
                      'announcements_list': ('offset',), 'announcements_publish': ('notice',), 'announcements_edit': ('notice',),
                      'trust_contact': ('public', 'fingerprint'), 'rename_contact': ('address', 'name'),
                      'history': ('address', 'offset', 'limit'), 'queue': ('address', 'text'),
                      'edit_message': ('address', 'message_id', 'text'), 'mark_inbox': ('ids', 'flag'),
                      'queue_audio': ('address', 'audio'),
                      'queue_radio': ('address', 'audio', 'mode', 'confirmed'), 'audio': ('message_id',),
                      'service_events': (), 'mark_events': ('ids', 'flag'),
                      'delivery_settings': (), 'background_delivery': ('enabled',),
                      'notification_settings': ('enabled',), 'notification_snapshot': (),
                      'notification_posted': ('peer', 'receipts'),
                      'visible_read': ('peer', 'receipts'),
                      'voice_settings': (), 'voice_mode': ('mode',), 'voice_confirm': ('address',)}
        if operation not in signatures or set(arguments) != set(signatures[operation]):
            raise LocalError('invalid_input')
        if operation.startswith('announcements_'):
            from .chat_admin import AnnouncementClient
            try:
                with self.friends.http_factory() as http:
                    client = AnnouncementClient(http, self.device)
                    if operation == 'announcements_list':
                        return client.list(arguments['offset'])
                    result = (client.publish if operation == 'announcements_publish' else client.edit)(arguments['notice'])
                self.next_events = 0
                return result
            except FriendsError as failure:
                code = str(failure)
                raise LocalError('notice_denied' if code == 'access_rejected' else code if code in ('notice_conflict', 'invalid_input') else 'notice_unavailable') from None
            except Exception:
                raise LocalError('notice_unavailable') from None
        if operation == 'preview_contact':
            return contact_card(arguments['public'])
        if operation == 'inbox_summary':
            return [{key: item[key] for key in ('id', 'peer', 'read', 'notified')} for item in self.local.inbox()]
        if operation == 'event_counts':
            events = self.local.service_events()
            return dict(total=len(events), unread=sum(not event['read'] for event in events))
        if operation == 'service_events_page':
            offset, limit = arguments['offset'], arguments['limit']
            if type(offset) is not int or not 0 <= offset <= 2000 or type(limit) is not int or not 1 <= limit <= 50:
                raise LocalError('invalid_input')
            events = list(reversed(self.local.service_events()))
            return dict(events=events[offset:offset+limit], total=len(events),
                        next_offset=offset+limit if offset+limit < len(events) else None)
        if operation == 'delivery_settings':
            return self.delivery_settings()
        if operation in ('background_delivery', 'notification_settings'):
            if type(arguments['enabled']) is not bool:
                raise LocalError('invalid_input')
            return self.delivery_settings('background' if operation == 'background_delivery' else 'notifications', arguments['enabled'])
        if operation == 'notification_snapshot':
            with self.local._lock:
                result = notification_batches(self.local._store.inbox(), self.local.service_events())
                result['settings'] = self.delivery_settings()
                return result
        if operation == 'notification_posted':
            return self.notification_posted(**arguments)
        if operation == 'visible_read':
            return self.notification_posted(**arguments, flag='read')
        if operation.startswith('voice_'):
            if any(value is None for value in arguments.values()):
                raise LocalError('invalid_input')
            return self.voice_settings(**arguments)
        return getattr(self.local, operation)(**arguments)

    def delivery_settings(self, setting=None, enabled=None):
        store = self.local._store
        with store._lock, store._db:
            value = store._get('desktop-delivery-v1')
            if value is None:
                value = {'background': True, 'notifications': True}
            if (type(value) is not dict or set(value) != {'background', 'notifications'} or
                    any(type(item) is not bool for item in value.values())):
                raise LocalError('store_unavailable')
            if setting is not None:
                value[setting] = enabled
                store._put('desktop-delivery-v1', value)
            return value

    def notification_posted(self, peer, receipts, flag='notified'):
        if (type(peer) is not str or (peer != 'service' and (len(peer) != 32 or
                any(char not in '0123456789abcdef' for char in peer))) or type(receipts) is not list or
                len(receipts) > 1000 or any(type(item) is not dict or set(item) != {'id', 'revision'} or
                    type(item['id']) is not str or len(item['id']) > 160 or
                    type(item['revision']) is not int for item in receipts)):
            raise LocalError('invalid_input')
        with self.local._lock, self.local._store._lock, self.local._store._db:
            messages = self.local.service_events() if peer == 'service' else self.local._store.inbox()
            wanted = {(item['id'], item['revision']) for item in receipts}
            ids = [item['id'] for item in messages if (item['id'], item.get('revision', 1 if peer == 'service' else 0)) in wanted and
                   (peer == 'service' or item['peer'] == peer)]
            return (self.local.mark_events if peer == 'service' else self.local.mark_inbox)(ids, flag)

    def voice_settings(self, *, mode=None, address=None):
        store = self.local._store
        with store._lock, store._db:
            value = store._get('desktop-voice-v1') or {'mode': 16, 'confirmed': []}
            if (type(value) is not dict or set(value) != {'mode', 'confirmed'} or
                    type(value['mode']) is not int or value['mode'] not in (16, 7, 8, 9) or
                    type(value['confirmed']) is not list or len(value['confirmed']) > 1000 or
                    any(type(peer) is not str or len(peer) != 32 or
                        any(char not in '0123456789abcdef' for char in peer) for peer in value['confirmed'])):
                raise LocalError('store_unavailable')
            if mode is not None:
                if type(mode) is not int or mode not in (16, 7, 8, 9):
                    raise LocalError('invalid_input')
                value['mode'] = mode
            if address is not None:
                if type(address) is not str or address not in store.contacts():
                    raise LocalError('unverified_contact')
                if address not in value['confirmed']:
                    if len(value['confirmed']) >= 1000:
                        raise LocalError('invalid_input')
                    value['confirmed'].append(address)
            if mode is not None or address is not None:
                store._put('desktop-voice-v1', value)
            return value

    def tick(self, *, online, visible, background=False):
        if type(online) is not bool or type(visible) is not bool or type(background) is not bool:
            raise LocalError('invalid_input')
        if self.local is None:
            return {'attached': False}
        now = time.monotonic()
        enabled = visible or (background and self.delivery_settings()['background'])
        if online and enabled and (self.node is None or self.node['expires_at'] <= time.time() + 20) and now >= self.next_enrollment:
            self.next_enrollment = now + 60
            try:
                with self.friends.http_factory() as http:
                    if self.restricted is not None:
                        from .chat_bridge import ChatHTTP
                        if self.direct is not None:
                            from .chat_direct import DirectHTTP
                            http = DirectHTTP(self.direct)
                        http = ChatHTTP(http, self.restricted)
                    result = FriendsClient(http, self.device).register_chat(self.local)
                if result['status'] != 'active' or 'node' not in result:
                    raise LocalError('delivery_unavailable')
                node = result['node']
                registration_route = None
                if self.direct is not None:
                    registration_route = http.route
                    if registration_route not in ('DIRECT', 'EXISTING_EXIT'):
                        raise LocalError('delivery_unavailable')
                    self.direct.bind(result if registration_route == 'DIRECT' else None)
                unchanged = (self.carrier is not None and self.node is not None and
                             self.registration_route == registration_route and
                             all(self.node[field] == node[field] for field in ('host', 'port', 'public_key')))
                if unchanged:
                    self.carrier.expires = node['expires_at']
                else:
                    if self.carrier is not None:
                        self.local.detach_carrier()
                        self.carrier.close()
                        self.carrier = None
                    self.node = None
                    if self.direct is not None and self.mailbox_factory is SystemMailbox:
                        self.carrier = self.local.attach_carrier(lambda chat: ProtectedMailbox(chat, node, self.runtime, self.direct, self.restricted, registration_route=registration_route))
                    elif self.restricted is not None and self.mailbox_factory is SystemMailbox:
                        self.carrier = self.local.attach_carrier(lambda chat: ExistingExitMailbox(chat, node, self.runtime, self.restricted))
                    else:
                        self.carrier = self.local.attach_carrier(lambda chat: self.mailbox_factory(chat, node, self.runtime))
                self.node = node
                self.registration_route = registration_route
                self.delivery_error = None
            except (FriendsError, LocalError, OSError, ValueError) as failure:
                self.delivery_error = 'delivery_unavailable'
                if not isinstance(failure, FriendsError) or str(failure) != 'service_unavailable':
                    self.node = None
        if self.carrier is not None:
            allowed = online and enabled and self.node is not None and time.time() < self.node['expires_at']
            self.local.delivery_update(online=allowed, foreground=enabled)
            current = self.local.delivery_state()
            if allowed and not current.get('running') and not current.get('pending') and now >= self.next_sync:
                self.next_sync = now + (60 if current.get('error') else 15)
                self.local.request_sync()
        if online and enabled and now >= self.next_events:
            self.next_events = now + 30
            try:
                events = self.events_fetcher(self.friends.http_factory)
                with self.local._lock:
                    self.local._store.service_events(events)
                self.events_error = False
            except Exception:
                self.events_error = True
        state = self.local.delivery_state()
        state['registration_error'] = self.delivery_error
        state['events_unavailable'] = self.events_error
        state['route'] = None if self.carrier is None else self.carrier.route
        return state

    def close(self):
        if self.direct is not None:
            self.direct.close()
            self.direct = None
        if self.restricted is not None:
            self.restricted.close()
            self.restricted = None
        if self.local is not None:
            self.local.close()
            self.local = None
        if self.carrier is not None:
            self.carrier.close()
            self.carrier = None
        self.node = None
        self.registration_route = None
        self.next_enrollment = 0
        if self.lock is not None:
            os.close(self.lock)
            self.lock = None
