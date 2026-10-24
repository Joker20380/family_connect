"""One non-root user-session owner for delivery, encrypted history and notices."""
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
if (ROOT / 'vendor').is_dir():
    sys.path.insert(0, str(ROOT / 'vendor'))

from gi.repository import Gio, GLib

from chat_notifications import Notifications
from messenger.local import LocalError
from provisioning.chat_owner import ChatOwner
from provisioning.chat_rpc import BUS_NAME, OBJECT_PATH, SUPPORT, parse_request, encode_response, invoke
from provisioning.chat_client import entry_command, session_environment
from provisioning.friends_owner import FriendsOwner


XML = '<node><interface name="' + BUS_NAME + '"><method name="Request"><arg type="s" direction="in"/><arg type="s" direction="out"/></method></interface></node>'
LEASE_SECONDS = 15


def open_window(peer):
    if type(peer) is not str or not re.fullmatch('(?:[a-f0-9]{32}|service)', peer):
        raise LocalError('invalid_input')
    command = entry_command()
    if command[-1].endswith('/chat_daemon.py'):
        command[-1] = str(Path(__file__).with_name('app.py'))
    subprocess.Popen(['systemd-run', '--user', '--collect', '--quiet',
        '--unit=family-connect-window-' + uuid.uuid4().hex, '--property=Type=exec'] + session_environment() +
        command + ['familyconnect://chat/' + peer], stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)


class ChatService:
    def __init__(self, owner, *, activate=open_window, notifier=Notifications, online=None, support=None):
        self.owner = owner
        self.support = support
        self.support_pending = False
        self.support_pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix='fc-support-control')
        self.notifier = notifier(activate)
        self.online = online or (lambda: Gio.NetworkMonitor.get_default().get_network_available())
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix='fc-chat-commands')
        self.network = ThreadPoolExecutor(max_workers=1, thread_name_prefix='fc-chat-network')
        self.loop = GLib.MainLoop()
        self.clients = {}
        self.pending = 0
        self.network_busy = self.notice_busy = self.stopping = False
        self.posting = set()
        self.next_resume = 0
        self.idle_since = time.monotonic()
        self.state = {'attached': False}
        self.connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        self.registration = self.connection.register_object(OBJECT_PATH, Gio.DBusNodeInfo.new_for_xml(XML).interfaces[0], self.request, None, None)
        reply = self.connection.call_sync('org.freedesktop.DBus', '/org/freedesktop/DBus', 'org.freedesktop.DBus',
            'RequestName', GLib.Variant('(su)', (BUS_NAME, 4)), GLib.VariantType.new('(u)'),
            Gio.DBusCallFlags.NONE, 3000, None).unpack()[0]
        if reply != 1:
            raise LocalError('busy')
        self.subscription = self.connection.signal_subscribe('org.freedesktop.DBus', 'org.freedesktop.DBus',
            'NameOwnerChanged', '/org/freedesktop/DBus', None, Gio.DBusSignalFlags.NONE, self.name_changed)
        self.connection.connect('closed', lambda *_: self.stop())
        self.timer = GLib.timeout_add_seconds(6, self.poll)

    def name_changed(self, connection, sender, path, interface, signal_name, parameters):
        name, old, new = parameters.unpack()
        if not new:
            self.clients.pop(name, None)

    def submit(self, work, callback):
        if self.pending >= 8 or self.stopping:
            return False
        self.pending += 1
        future = self.pool.submit(work)
        def done(result):
            self.pending -= 1
            callback(result)
            return False
        future.add_done_callback(lambda result: GLib.idle_add(done, result))
        return True

    def request(self, connection, sender, path, interface, method, parameters, invocation):
        try:
            if self.stopping:
                raise LocalError('busy')
            uid = connection.call_sync('org.freedesktop.DBus', '/org/freedesktop/DBus', 'org.freedesktop.DBus',
                'GetConnectionUnixUser', GLib.Variant('(s)', (sender,)), GLib.VariantType.new('(u)'),
                Gio.DBusCallFlags.NONE, 3000, None).unpack()[0]
            if uid != os.getuid() or method != 'Request':
                raise LocalError('invalid_input')
            request = parse_request(parameters.unpack()[0])
            operation, arguments = request['operation'], request['arguments']
            if operation in SUPPORT:
                self.support_request(sender, operation, arguments, invocation)
                return
            if self.pending >= 8:
                raise LocalError('busy')
            if operation == 'heartbeat':
                if (set(arguments) != {'visible', 'peer'} or type(arguments['visible']) is not bool or
                        arguments['peer'] is not None and (type(arguments['peer']) is not str or
                        not re.fullmatch('(?:[a-f0-9]{32}|service)', arguments['peer']))):
                    raise LocalError('invalid_input')
                if sender not in self.clients and len(self.clients) >= 4:
                    raise LocalError('busy')
                self.clients[sender] = (time.monotonic() + LEASE_SECONDS, arguments['visible'], arguments['peer'])
                if arguments['visible'] and arguments['peer']:
                    self.notifier.withdraw(arguments['peer'])
                invocation.return_value(GLib.Variant('(s)', (encode_response(self.state),)))
                return
            if operation in ('detach', 'status'):
                if arguments:
                    raise LocalError('invalid_input')
                if operation == 'detach':
                    self.clients.pop(sender, None)
                invocation.return_value(GLib.Variant('(s)', (encode_response(self.state),)))
                return
            if operation == 'open':
                if set(arguments) != {'create'} or type(arguments['create']) is not bool:
                    raise LocalError('invalid_input')
                if sender not in self.clients and len(self.clients) >= 4:
                    raise LocalError('busy')
                self.clients[sender] = (time.monotonic() + LEASE_SECONDS, False, None)
            def work():
                if operation == 'open':
                    return self.owner.open(**arguments)
                if self.owner.local is None:
                    self.owner.open(create=False)
                return invoke(self.owner, request)
            def reply(result):
                try:
                    raw = encode_response(result.result())
                except Exception as failure:
                    raw = encode_response(error=str(failure) if isinstance(failure, LocalError) else 'store_unavailable')
                invocation.return_value(GLib.Variant('(s)', (raw,)))
            if not self.submit(work, reply):
                raise LocalError('busy')
        except Exception as failure:
            invocation.return_value(GLib.Variant('(s)', (encode_response(error=str(failure) if isinstance(failure, LocalError) else 'invalid_input'),)))

    def support_request(self, sender, operation, arguments, invocation):
        if (operation == 'support_status' and arguments or operation == 'support_consent' and
                (set(arguments) != {'enabled', 'revision'} or type(arguments['enabled']) is not bool or
                 type(arguments['revision']) is not str or not re.fullmatch('[a-f0-9]{32}', arguments['revision']))):
            raise LocalError('invalid_input')
        if self.support is None:
            raise LocalError('support_unavailable')
        if sender not in self.clients and len(self.clients) >= 4:
            raise LocalError('busy')
        self.clients[sender] = (time.monotonic()+LEASE_SECONDS, False, None)
        if operation == 'support_status':
            invocation.return_value(GLib.Variant('(s)', (encode_response(self.support.status()),)))
            return
        if self.support_pending:
            raise LocalError('busy')
        self.support_pending = True
        future = self.support_pool.submit(self.support.change, arguments['enabled'], arguments['revision'])
        def done(result):
            self.support_pending = False
            try:raw = encode_response(result.result())
            except Exception as failure:
                raw = encode_response(error=str(failure) if isinstance(failure, LocalError) else 'support_unavailable')
            invocation.return_value(GLib.Variant('(s)', (raw,)))
            return False
        future.add_done_callback(lambda result: GLib.idle_add(done, result))

    def support_wanted(self):
        return self.support is not None and self.support.status()['enabled']

    def poll(self):
        if self.stopping:
            return False
        if self.support is not None:
            self.support.poll()
        now = time.monotonic()
        self.clients = {name: lease for name, lease in self.clients.items() if lease[0] > now}
        if self.owner.local is None:
            if self.clients or self.support_wanted():
                self.idle_since = now
            elif now - self.idle_since >= 60 and not self.pending:
                return self.stop()
            if now >= self.next_resume:
                self.next_resume = now + 60
                def resumed(result):
                    try:
                        result.result()
                    except Exception:
                        pass
                self.submit(lambda: self.owner.open(create=False), resumed)
            return True
        if not self.network_busy:
            self.network_busy = True
            future = self.network.submit(self.owner.tick, online=bool(self.online()),
                visible=any(lease[1] for lease in self.clients.values()), background=True)
            def completed(result):
                self.network_busy = False
                try:
                    state = result.result()
                    self.state = {key: state.get(key) for key in ('attached', 'running', 'pending', 'error',
                        'registration_error', 'route', 'events_unavailable')}
                except Exception:
                    self.state = {'attached': False, 'registration_error': 'delivery_unavailable'}
                return False
            future.add_done_callback(lambda result: GLib.idle_add(completed, result))
        if not self.notice_busy:
            self.notice_busy = True
            if not self.submit(lambda: self.owner.invoke('notification_snapshot'), self.notices):
                self.notice_busy = False
        return True

    def notices(self, result):
        self.notice_busy = False
        if self.stopping:
            return
        try:
            snapshot = result.result()
        except Exception:
            return
        visible = {lease[2] for lease in self.clients.values() if lease[0] > time.monotonic() and lease[1]}
        enabled = snapshot['settings']['notifications']
        self.notifier.retain(set(snapshot['peers']) - visible if enabled else set())
        if enabled:
            for batch in snapshot['batches']:
                peer = batch['peer']
                if peer in visible or peer in self.posting:
                    continue
                self.posting.add(peer)
                self.notifier.notify(peer, batch['unread'], self.russian(),
                    lambda accepted, batch=batch: self.posted(batch, accepted))
        if self.clients or snapshot['settings']['background'] or self.support_wanted():
            self.idle_since = time.monotonic()
        elif time.monotonic() - self.idle_since >= 30:
            self.stop()

    @staticmethod
    def russian():
        try:
            root = Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home() / '.config')))
            descriptor = os.open(root / 'family-connect/ui-language', os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
            with os.fdopen(descriptor, 'rb') as source:
                if not stat.S_ISREG(os.fstat(source.fileno()).st_mode):
                    raise OSError('language file unavailable')
                return source.read(4).decode('ascii').strip() == 'ru'
        except (OSError, UnicodeError):
            return os.environ.get('LANG', '').lower().startswith('ru')

    def posted(self, batch, accepted):
        peer = batch['peer']
        if not accepted or self.stopping:
            self.posting.discard(peer)
            return
        def complete(result):
            self.posting.discard(peer)
            try:
                result.result()
            except Exception:
                pass
        if not self.submit(lambda: self.owner.invoke('notification_posted', peer=peer, receipts=batch['receipts']), complete):
            self.posting.discard(peer)

    def stop(self):
        self.stopping = True
        if self.support is not None:
            self.support.close()
        self.loop.quit()
        return False

    def run(self):
        self.poll()
        try:
            self.loop.run()
        finally:
            self.stopping = True
            if self.support is not None:
                self.support.close()
            GLib.source_remove(self.timer)
            self.notifier.close()
            self.connection.unregister_object(self.registration)
            self.connection.signal_unsubscribe(self.subscription)
            self.network.shutdown(wait=True, cancel_futures=True)
            self.pool.shutdown(wait=True, cancel_futures=True)
            self.support_pool.shutdown(wait=True, cancel_futures=True)
            self.owner.close()


def main():
    if sys.argv[1:] != ['--chat-service'] or os.getuid() == 0:
        return 2
    root = Path.home() / '.local/share/family-connect'
    from provisioning.chat_bridge import ChatBridge
    from provisioning.chat_direct import DirectBridge
    owner = ChatOwner(root / 'chat', FriendsOwner(root / 'friends-identity', Path(__file__).with_name('update.pub')),
                      restricted_factory=ChatBridge, direct_factory=DirectBridge)
    try:
        from support_daemon import SupportCollector, SupportSession, version_info
        try:
            version, code = version_info(ROOT)
            support = SupportSession(owner.friends, SupportCollector(version), code)
        except (OSError, ValueError):
            support = None
        service = ChatService(owner, support=support)
        for signum in (signal.SIGTERM, signal.SIGINT):
            GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signum, service.stop)
        service.run()
        return 0
    except Exception:
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
