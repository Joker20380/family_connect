"""Content-free notifications, acknowledged by the user's session daemon."""
import re

from gi.repository import Gio, GLib
from chat_strings import STRINGS


NAME = 'org.freedesktop.Notifications'
PATH = '/org/freedesktop/Notifications'


class Notifications:
    def __init__(self, activate):
        self.activate = activate
        self.proxy = None
        self.closed = False
        self.items = {}
        self.pending = {}
        self.cancelled = set()
        self.cancellable = Gio.Cancellable()
        Gio.DBusProxy.new_for_bus(Gio.BusType.SESSION,
            Gio.DBusProxyFlags.DO_NOT_LOAD_PROPERTIES | Gio.DBusProxyFlags.DO_NOT_AUTO_START,
            None, NAME, PATH, NAME, self.cancellable, self.ready)

    def ready(self, source, result):
        try:
            proxy = Gio.DBusProxy.new_for_bus_finish(result)
        except GLib.Error:
            return
        if self.closed:
            return
        self.proxy = proxy
        proxy.connect('g-signal', self.signal)
        proxy.connect('notify::g-name-owner', self.owner_changed)

    def owner_changed(self, *_):
        self.items.clear()
        self.cancelled.update(self.pending)

    def signal(self, proxy, sender, name, parameters):
        if self.closed or sender != proxy.get_name_owner():
            return
        values = parameters.unpack()
        if len(values) != 2 or type(values[0]) is not int:
            return
        peer = next((peer for peer, item in self.items.items() if item == values[0]), None)
        if peer is None:
            return
        if name == 'ActionInvoked' and len(values) == 2 and values[1] == 'default':
            self.activate(peer)
        elif name == 'NotificationClosed':
            self.items.pop(peer, None)

    def notify(self, peer, unread, ru, callback):
        owner = self.proxy.get_name_owner() if self.proxy else None
        if (self.closed or not owner or peer in self.pending or len(self.pending) >= 8 or
                type(peer) is not str or not re.fullmatch(r'(?:[0-9a-f]{32}|service)', peer) or
                type(unread) is not int or unread < 1):
            callback(False)
            return
        self.pending[peer] = owner
        self.cancelled.discard(peer)
        body = STRINGS['service_events' if peer == 'service' else 'chat_new_message'][0 if ru else 1]
        if unread > 1:
            body += ' · ' + str(unread)
        values = ('Family Connect', self.items.get(peer, 0), 'com.familyconnect.Client',
                  'Family Connect', body, ['default', 'Открыть' if ru else 'Open'],
                  {'category': GLib.Variant('s', 'im.received'), 'desktop-entry': GLib.Variant('s', 'com.familyconnect.Client')}, -1)
        def finished(connection, result):
            self.pending.pop(peer, None)
            try:
                ident = connection.call_finish(result).unpack()[0]
                accepted = bool(ident) and not self.closed and peer not in self.cancelled and self.proxy.get_name_owner() == owner
            except GLib.Error:
                self.cancelled.discard(peer)
                callback(False)
                return
            self.cancelled.discard(peer)
            if accepted:
                if peer not in self.items and len(self.items) >= 64:
                    self.withdraw(next(iter(self.items)))
                self.items[peer] = ident
            elif ident:
                self.close_id(owner, ident)
            callback(accepted)
        self.proxy.get_connection().call(owner, PATH, NAME, 'Notify', GLib.Variant('(susssasa{sv}i)', values),
            GLib.VariantType.new('(u)'), Gio.DBusCallFlags.NO_AUTO_START, 3000, None, finished)

    def close_id(self, owner, ident):
        def finished(connection, result):
            try:
                connection.call_finish(result)
            except GLib.Error:
                pass
        self.proxy.get_connection().call(owner, PATH, NAME, 'CloseNotification', GLib.Variant('(u)', (ident,)),
            None, Gio.DBusCallFlags.NO_AUTO_START, 3000, None, finished)

    def withdraw(self, peer):
        if peer in self.pending:
            self.cancelled.add(peer)
        ident = self.items.pop(peer, None)
        if ident and self.proxy and self.proxy.get_name_owner():
            self.close_id(self.proxy.get_name_owner(), ident)

    def retain(self, peers):
        for peer in set(self.items) | set(self.pending):
            if peer not in peers:
                self.withdraw(peer)

    def close(self):
        self.closed = True
        self.retain(set())
        self.cancellable.cancel()
