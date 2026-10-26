"""Real GTK and encrypted local-owner checks; synthetic identities, no remote calls."""
import json
import os
from pathlib import Path
import sys
import threading
import time
from types import SimpleNamespace

from app import App, Adw, Gtk, Gdk
from mesh_ui_check import capture, pump, Driver, done
from device_identity.friends import load_friends_identity
from messenger.local import LocalChat
from provisioning.chat_owner import ChatOwner


class MemoryKeyring:
    def __init__(self):
        self.keys = {}

    def key(self, device, *, create):
        if device not in self.keys:
            assert create
            self.keys[device] = os.urandom(32)
        return self.keys[device]


def settled(pane):
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        pump(.05)
        if not pane.busy:
            pump(.1)
            return
    raise AssertionError('chat owner did not finish')


def click(pane, text):
    if text == pane.t('chat_add') and hasattr(pane, 'add_button'):
        pane.add_button.emit('clicked')
        settled(pane)
        return
    if text == pane.t('chat_create') and hasattr(pane, 'status_action'):
        pane.status_action.emit('clicked')
        settled(pane)
        return
    if text == pane.t('chat_rename') and hasattr(pane, 'split'):
        pane.header_menu.emit('clicked')
        settled(pane)
        return
    if text in (pane.t('chat_profile'), pane.t('chat_background')) and hasattr(pane, 'options'):
        pane.options.popup()
        widget = pane.options.get_popover().get_child().get_first_child()
        while widget is not None:
            if widget.get_label() == text:
                widget.emit('clicked')
                settled(pane)
                return
            widget = widget.get_next_sibling()
    widget = pane.content.get_first_child()
    while widget is not None:
        if isinstance(widget, Gtk.Button) and widget.get_label() == text:
            assert widget.get_sensitive()
            widget.emit('clicked')
            settled(pane)
            return
        widget = widget.get_next_sibling()
    raise AssertionError('missing control: ' + text)


def main(destination, scale):
    failures = []
    def failed(kind, value, traceback):
        failures.append(kind.__name__)
        sys.__excepthook__(kind, value, traceback)
    sys.excepthook = failed
    destination.mkdir(parents=True, exist_ok=False)
    Adw.init()
    Gtk.Settings.get_default().set_property('gtk-enable-animations', False)
    Gtk.Settings.get_default().set_property('gtk-xft-dpi', round(96 * scale / int(os.environ.get('GDK_SCALE', '1')) * 1024))
    app = App(smoke=True)
    driver = Driver()
    app.complete('initialized', done((driver, driver.profiles(), False)), app.revision, None)
    assert app.window.get_display().__gtype__.name == 'GdkX11Display'
    device = load_friends_identity(destination / 'synthetic-device', create=True)
    def offline():
        raise OSError('synthetic offline test')
    friends = SimpleNamespace(_device=lambda create: device, http_factory=offline)
    vault = MemoryKeyring()
    pane = app.chat_pane
    pane.owner_factory = lambda: ChatOwner(destination / 'chat', friends, keyring=vault)
    app.present()
    app.select_page('messenger')
    pane.activate(True, True)
    settled(pane)
    assert pane.screen == 'welcome' and not pane.opened
    capture(app, destination / 'ru-welcome.png')
    click(pane, pane.t('chat_create'))
    assert pane.opened and pane.screen == 'contacts'
    alice_profile = pane.owner.invoke('profile')
    bob = LocalChat(destination / 'bob', os.urandom(32), create=True, platform='android', version=118)
    card = bob.profile()
    try:
        for ru in (True, False):
            language = 'ru' if ru else 'en'
            app.ru = ru
            app.paint()
            pane.activate(True, ru)
            pane.contacts()
            settled(pane)
            capture(app, destination / (language + '-contacts.png'))
            click(pane, pane.t('chat_profile'))
            click(pane, pane.t('chat_copy_key'))
            copied = []
            pane.get_clipboard().read_text_async(None, lambda owner, result: copied.append(owner.read_text_finish(result)))
            pump(.2)
            assert copied == [alice_profile['public']]
            capture(app, destination / (language + '-profile.png'))
            pane.contacts()
            settled(pane)
            click(pane, pane.t('chat_add'))
            pane.public_input.set_text(card['public'])
            pane.public_input.emit('activate')
            settled(pane)
            assert pane.screen == 'verify' and not pane.save_contact.get_sensitive()
            capture(app, destination / (language + '-verify.png'))
            pane.messages_scroll.get_vadjustment().set_value(pane.messages_scroll.get_vadjustment().get_upper())
            pump(.2)
            capture(app, destination / (language + '-verify-actions.png'))
            pane.verified.set_active(True)
            pane.save_contact.emit('clicked')
            settled(pane)
            assert pane.screen == 'conversation'
            pane.compose.set_text('Привет / Hello ' + language + ' 👩🏽‍💻🙂🇧🇪 е\u0301')
            pane.compose.emit('activate')
            settled(pane)
            assert pane.compose.get_text() == ''
            pane.compose.grab_focus()
            focus = app.window.get_focus()
            assert focus == pane.compose or focus.is_ancestor(pane.compose)
            assert app.window.child_focus(Gtk.DirectionType.TAB_FORWARD)
            pump(.2)
            capture(app, destination / (language + '-conversation.png'))
            pane.compose.set_text('draft preserved')
            assert pane.key_pressed(None, Gdk.KEY_Escape, 0, 0)
            settled(pane)
            pane.conversation(card)
            settled(pane)
            assert pane.compose.get_text() == 'draft preserved'
        entered, released = threading.Event(), threading.Event()
        original = pane.owner.invoke
        def delayed_history(operation, **arguments):
            if operation == 'history':
                entered.set()
                assert released.wait(3)
            return original(operation, **arguments)
        pane.owner.invoke = delayed_history
        pane.last_snapshot = None
        pane.refresh()
        deadline = time.monotonic() + 5
        while not entered.is_set() and time.monotonic() < deadline:
            pump(.02)
        assert entered.is_set()
        pane.contacts()
        released.set()
        settled(pane)
        pane.owner.invoke = original
        assert pane.screen == 'contacts' and pane.peer is None
        pane.conversation(card)
        settled(pane)
        history = pane.owner.invoke('history', address=card['address'], offset=0, limit=50)
        assert [item['text'] for item in history['messages']] == ['Привет / Hello ' + language + ' 👩🏽‍💻🙂🇧🇪 е\u0301' for language in ('ru', 'en')]
        assert all(item['status'] == 'queued' for item in history['messages'])
        click(pane, pane.t('chat_rename'))
        pane.content.get_first_child().set_text('Contact / Контакт')
        click(pane, 'Save')
        assert pane.peer['name'] == 'Contact / Контакт'
        row = pane.content.get_first_child()
        while row is not None and not hasattr(row, 'menu'):
            row = row.get_next_sibling()
        assert row is not None
        menu = row.menu
        assert isinstance(menu, Gtk.MenuButton)
        menu.popup()
        pump(.1)
        menu.get_popover().get_child().emit('clicked')
        assert pane.screen == 'edit'
        pane.content.get_first_child().set_text('Edited / Изменено')
        click(pane, 'Save')
        history = pane.owner.invoke('history', address=card['address'], offset=0, limit=50)
        assert history['messages'][0]['text'] == 'Edited / Изменено'
        assert history['messages'][0]['edited']
        while pane.network_busy:
            pump(.05)
        started, release = threading.Event(), threading.Event()
        original_tick = pane.owner.tick
        def pending_registration(**kwargs):
            started.set()
            assert release.wait(5)
            return {'attached': False}
        pane.owner.tick = pending_registration
        try:
            pane.network(True, True)
            assert started.wait(1)
            assert pane.content.get_sensitive() and not pane.busy
            pane.compose.set_text('Queued while registration waits')
            pane.compose.emit('activate')
            settled(pane)
            history = pane.owner.invoke('history', address=card['address'], offset=0, limit=50)
            assert history['messages'][-1]['text'] == 'Queued while registration waits'
            assert not release.is_set()
        finally:
            release.set()
            while pane.network_busy:
                pump(.05)
            pane.owner.tick = original_tick
        pane.activate(False, False)
        settled(pane)
        assert not pane.busy
        app.close(True)
        deadline = time.monotonic() + 5
        while not app.closed and time.monotonic() < deadline:
            pump(.05)
        assert app.closed and pane.owner.local is None
        reopened = ChatOwner(destination / 'chat', friends, keyring=vault)
        try:
            assert reopened.open() == alice_profile
            assert reopened.invoke('history', address=card['address'], offset=0, limit=50) == history
        finally:
            reopened.close()
        assert not failures, failures
        (destination / 'result.json').write_text(json.dumps(dict(result='PASS', scale=scale,
            actual_gtk=True, encrypted_owner=True, private_keyring='synthetic memory vault',
            contact_verification=True, queued_text_count=3, draft_resume=True, identity_history_resume=True,
            queue_during_pending_registration=True,
            rename=True, edit=True,
            remote_network=False, vpn_acceptance='NOT_RUN', device_scale=app.window.get_scale_factor(),
            display=app.window.get_display().__gtype__.name), indent=2) + '\n')
    finally:
        bob.close()
        if not app.closed:
            app.close(True)
            pump(1)


if __name__ == '__main__':
    main(Path(sys.argv[1]), float(sys.argv[2]))
