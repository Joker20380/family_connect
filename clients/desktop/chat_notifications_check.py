"""Real GTK/session-D-Bus integration; isolated daemon, synthetic identities only."""
import json
import ctypes
import ctypes.util
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace

from gi.repository import Gio, GLib

from app import App, Adw, Gtk, Gdk
from chat_notifications import Notifications, NAME, PATH
from chat_ui_check import MemoryKeyring, settled, click
from mesh_ui_check import capture, pump, Driver, done
from device_identity.friends import load_friends_identity
from messenger.local import LocalChat
from provisioning.chat_owner import ChatOwner


XML = '''<node><interface name="org.freedesktop.Notifications">
<method name="Notify"><arg type="s" direction="in"/><arg type="u" direction="in"/>
<arg type="s" direction="in"/><arg type="s" direction="in"/><arg type="s" direction="in"/>
<arg type="as" direction="in"/><arg type="a{sv}" direction="in"/><arg type="i" direction="in"/>
<arg type="u" direction="out"/></method>
<method name="CloseNotification"><arg type="u" direction="in"/></method>
<signal name="ActionInvoked"><arg type="u"/><arg type="s"/></signal>
<signal name="NotificationClosed"><arg type="u"/><arg type="u"/></signal>
</interface></node>'''


def wait(predicate):
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        pump(.02)
        if predicate():
            return
    raise AssertionError('bounded notification wait expired')


def key(keysym):
    x11 = ctypes.CDLL(ctypes.util.find_library('X11'))
    xtest = ctypes.CDLL(ctypes.util.find_library('Xtst'))
    x11.XOpenDisplay.argtypes, x11.XOpenDisplay.restype = [ctypes.c_char_p], ctypes.c_void_p
    x11.XKeysymToKeycode.argtypes, x11.XKeysymToKeycode.restype = [ctypes.c_void_p, ctypes.c_ulong], ctypes.c_uint
    x11.XFlush.argtypes = x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
    xtest.XTestFakeKeyEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_int, ctypes.c_ulong]
    display = x11.XOpenDisplay(os.environ['DISPLAY'].encode())
    assert display
    try:
        code = x11.XKeysymToKeycode(display, keysym)
        xtest.XTestFakeKeyEvent(display, code, 1, 0)
        xtest.XTestFakeKeyEvent(display, code, 0, 0)
        x11.XFlush(display)
        pump(.1)
    finally:
        x11.XCloseDisplay(display)


class Daemon:
    def __init__(self):
        self.connection = Gio.DBusConnection.new_for_address_sync(os.environ['DBUS_SESSION_BUS_ADDRESS'],
            Gio.DBusConnectionFlags.AUTHENTICATION_CLIENT | Gio.DBusConnectionFlags.MESSAGE_BUS_CONNECTION, None, None)
        self.registration = self.connection.register_object(PATH, Gio.DBusNodeInfo.new_for_xml(XML).interfaces[0], self.method, None, None)
        self.posts, self.closed, self.waiting = [], [], []
        self.delay = self.deny = False
        self.next_id = 1
        self.name('RequestName', GLib.Variant('(su)', (NAME, 0)))

    def name(self, operation, arguments):
        return self.connection.call_sync('org.freedesktop.DBus', '/org/freedesktop/DBus', 'org.freedesktop.DBus',
            operation, arguments, None, Gio.DBusCallFlags.NONE, 3000, None)

    def method(self, connection, sender, path, interface, method, parameters, invocation):
        values = parameters.unpack()
        if method == 'CloseNotification':
            self.closed.append(values[0])
            invocation.return_value(GLib.Variant('()', ()))
            return
        if self.deny:
            invocation.return_dbus_error('org.freedesktop.DBus.Error.AccessDenied', 'Synthetic denial')
            return
        ident = values[1] or self.next_id
        self.next_id += 1
        self.posts.append((ident, values))
        if self.delay:
            self.waiting.append((invocation, ident))
        else:
            invocation.return_value(GLib.Variant('(u)', (ident,)))

    def reply(self):
        pending, self.waiting = self.waiting, []
        for invocation, ident in pending:
            invocation.return_value(GLib.Variant('(u)', (ident,)))

    def action(self, ident, action='default'):
        self.connection.emit_signal(None, PATH, NAME, 'ActionInvoked', GLib.Variant('(us)', (ident, action)))

    def close(self):
        self.reply()
        self.name('ReleaseName', GLib.Variant('(s)', (NAME,)))
        self.connection.unregister_object(self.registration)
        self.connection.close_sync(None)


def protocol():
    daemon = Daemon()
    opened, receipts = [], []
    publisher = Notifications(opened.append)
    wait(lambda: publisher.proxy is not None and publisher.proxy.get_name_owner())
    peer = 'a' * 32
    publisher.notify(peer, 2, True, receipts.append)
    wait(lambda: receipts == [True])
    ident = publisher.items[peer]
    daemon.action(ident, 'arbitrary-command')
    pump(.1)
    assert opened == []
    daemon.action(ident)
    wait(lambda: opened == [peer])
    daemon.delay = True
    publisher.notify(peer, 3, False, receipts.append)
    wait(lambda: len(daemon.waiting) == 1)
    publisher.withdraw(peer)
    daemon.reply()
    wait(lambda: receipts == [True, False] and ident in daemon.closed)
    daemon.delay = False
    daemon.deny = True
    publisher.notify(peer, 3, False, receipts.append)
    wait(lambda: receipts == [True, False, False])
    daemon.deny = False
    daemon.delay = True
    publisher.notify(peer, 4, False, receipts.append)
    wait(lambda: len(daemon.waiting) == 1)
    old_id = daemon.waiting[0][1]
    daemon.name('ReleaseName', GLib.Variant('(s)', (NAME,)))
    wait(lambda: publisher.proxy.get_name_owner() is None)
    replacement = Daemon()
    wait(lambda: publisher.proxy.get_name_owner() == replacement.connection.get_unique_name())
    daemon.reply()
    wait(lambda: len(receipts) == 4 and old_id in daemon.closed)
    assert receipts[-1] is False and replacement.closed == []
    publisher.notify(peer, 1, False, receipts.append)
    wait(lambda: receipts[-1] is True)
    publisher.close()
    wait(lambda: bool(replacement.closed))
    daemon.close()
    replacement.close()
    absent = Notifications(opened.append)
    wait(lambda: absent.proxy is not None)
    missing = []
    absent.notify(peer, 1, False, missing.append)
    assert missing == [False]
    absent.close()


def main(destination, scale):
    failures = []
    def failed(kind, value, traceback):
        failures.append(kind.__name__)
        sys.__excepthook__(kind, value, traceback)
    sys.excepthook = failed
    destination.mkdir(parents=True, exist_ok=False)
    Adw.init()
    protocol()
    daemon = Daemon()
    Gtk.Settings.get_default().set_property('gtk-enable-animations', False)
    Gtk.Settings.get_default().set_property('gtk-xft-dpi', round(96 * scale / int(os.environ.get('GDK_SCALE', '1')) * 1024))
    app = App(smoke=True)
    driver = Driver()
    app.complete('initialized', done((driver, driver.profiles(), False)), app.revision, None)
    pane = app.chat_pane
    device = load_friends_identity(destination / 'synthetic-device', create=True)
    def offline():
        raise OSError('synthetic offline')
    friends = SimpleNamespace(_device=lambda create: device, http_factory=offline)
    pane.owner_factory = lambda: ChatOwner(destination / 'chat', friends, keyring=MemoryKeyring())
    app.chat_smoke = False
    app.ru = True
    app.present()
    app.select_page('messenger')
    pane.activate(True, True)
    settled(pane)
    click(pane, pane.t('chat_create'))
    alice = pane.owner.invoke('profile')
    bob = LocalChat(destination / 'bob', os.urandom(32), create=True, platform='android', version=118)
    try:
        card = bob.profile()
        pane.owner.invoke('trust_contact', public=card['public'], fingerprint=card['fingerprint'])
        bob.trust_contact(alice['public'], alice['fingerprint'])
        pane.owner.invoke('inbox')
        def receive(text):
            ident = bob.queue(alice['address'], text)
            raw = bob._store.begin_attempt(ident)[1]
            assert pane.owner.local._chat.receive(raw)
            return ident
        app.select_page('status')
        app.select_page('status')
        settled(pane)
        wait(lambda: pane.notifications.proxy is not None and pane.notifications.proxy.get_name_owner())
        daemon.delay = True
        message = receive('PRIVATE-TEXT-never-in-notifications')
        pane.refresh_notifications()
        wait(lambda: bool(daemon.waiting))
        assert not pane.owner.invoke('inbox')[0]['notified']
        assert not pane.owner.invoke('inbox')[0]['read']
        daemon.reply()
        wait(lambda: pane.owner.invoke('inbox')[0]['notified'])
        assert 'PRIVATE' not in str(daemon.posts)
        daemon.delay = False
        ident = pane.notifications.items[card['address']]
        daemon.action(ident)
        wait(lambda: pane.screen == 'conversation' and pane.peer['address'] == card['address'] and not pane.busy)
        wait(lambda: pane.owner.invoke('inbox')[0]['read'])
        capture(app, destination / 'notification-opened-conversation.png')
        before = len(daemon.posts)
        receive('Visible peer does not raise another popup')
        pane.last_snapshot = None
        pane.refresh()
        settled(pane)
        pane.refresh_notifications()
        wait(lambda: not pane.notices_busy)
        assert len(daemon.posts) == before
        assert all(item['read'] for item in pane.owner.invoke('inbox'))
        pane.notification_settings()
        settled(pane)
        toggle = pane.delivery_switches['background']
        toggle.grab_focus()
        key(Gdk.KEY_space)
        wait(lambda: not pane.busy and not pane.owner.invoke('delivery_settings')['background'])
        assert app.window.get_focus() is toggle
        key(Gdk.KEY_Return)
        wait(lambda: not pane.busy and pane.owner.invoke('delivery_settings')['background'])
        key(Gdk.KEY_Tab)
        assert app.window.get_focus() is pane.delivery_switches['notifications']
        capture(app, destination / 'ru-notification-settings.png')
        app.ru = False
        app.paint()
        pane.activate(True, False)
        pane.notification_settings()
        settled(pane)
        capture(app, destination / 'en-notification-settings.png')
        pane.owner.invoke('notification_settings', enabled=False)
        app.select_page('status')
        app.select_page('status')
        receive('Disabled notification stays pending')
        pane.refresh_notifications()
        wait(lambda: not pane.notices_busy)
        assert not pane.owner.invoke('inbox')[-1]['notified']
        assert len(daemon.posts) == before
        pane.owner.invoke('notification_settings', enabled=True)
        pane.refresh_notifications()
        wait(lambda: pane.owner.invoke('inbox')[-1]['notified'])
        app.select_page('messenger')
        settled(pane)
        pane.service_events()
        settled(pane)
        capture(app, destination / 'en-empty-service-notices.png')
        app.select_page('status')
        app.select_page('status')
        now = int(time.time())
        event = dict(id='b' * 32, kind='information', title='Плановые работы / Maintenance',
                     body='Public service notice. ' * 20, author='Operator', created=now-1, expires=now+1000,
                     platforms=['linux'], revision=1, updated=now-1, editor='Operator')
        pane.owner.local._store.service_events([event])
        pane.refresh_notifications()
        wait(lambda: 'service' in pane.notifications.items)
        daemon.action(pane.notifications.items['service'])
        wait(lambda: pane.screen == 'service' and not pane.busy)
        wait(lambda: pane.owner.invoke('service_events')[0]['read'])
        try:
            wait(lambda: app.window.get_height() > 500)
        except AssertionError:
            capture(app, destination / 'failed-service-layout.png')
            (destination / 'failed-service-layout.json').write_text(json.dumps(dict(
                window_width=app.window.get_width(), window_height=app.window.get_height(),
                default_size=list(app.window.get_default_size()),
                fitted_height=app.fitted_height, fit_pending=bool(app.fit_source),
                content_measure=list(app.window.get_content().measure(Gtk.Orientation.VERTICAL, app.window.get_width())),
                pane_measure=list(pane.measure(Gtk.Orientation.VERTICAL, app.window.get_width())),
                pane_mapped=pane.get_mapped(), page=app.page, screen=pane.screen), indent=2) + '\n')
            raise
        capture(app, destination / 'en-service-notices.png')
        app.ru = True
        app.paint()
        pane.activate(True, True)
        settled(pane)
        capture(app, destination / 'ru-service-notices.png')
        assert 'Public service notice' not in str(daemon.posts)
        pane.contacts()
        settled(pane)
        app.select_page('status')
        app.select_page('status')
        daemon.delay = True
        receive('Exit while daemon reply is delayed')
        pane.refresh_notifications()
        wait(lambda: bool(daemon.waiting))
        delayed_id = daemon.waiting[0][1]
        device_scale = app.window.get_scale_factor()
        app.close(True)
        daemon.reply()
        wait(lambda: app.closed and delayed_id in daemon.closed)
        assert pane.owner.local is None
        assert not failures, failures
        (destination / 'result.json').write_text(json.dumps(dict(result='PASS',
            protocol='real isolated session D-Bus with synthetic notification daemon',
            message_path='signed LXMF receive -> encrypted inbox -> notification ACK -> GTK action',
            no_private_preview=True, stale_reply_fenced=True, read_after_visible=True,
            hidden_tab_notifications=True, disabled_notifications_preserved=True,
            preference_keyboard='real XTest Space/Return/Tab',
            service_events=True, late_reply_close=True, device_scale=device_scale,
            font_scale=scale, remote_network=False, host_popup='NOT_RUN', closed_app_delivery='NOT_IMPLEMENTED'), indent=2) + '\n')
    finally:
        bob.close()
        if not app.closed:
            app.close(True)
            wait(lambda: app.closed)
        daemon.close()


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), float(sys.argv[2]))
