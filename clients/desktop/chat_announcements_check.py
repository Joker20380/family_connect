"""Real GTK/private D-Bus/subprocess owner with synthetic proof/role API, no sockets."""
import json
from pathlib import Path
import subprocess
import sys
import uuid

from gi.repository import Gio, GLib
from app import App, Adw, Gtk
from chat_notifications_check import wait, key
from chat_ui_check import settled, click
from mesh_ui_check import capture, pump, Driver, done
from messenger.tests.announcement_server import AnnouncementServer
from provisioning.chat_client import ChatClient
from provisioning.chat_rpc import BUS_NAME
from provisioning.friends_owner import FriendsOwner


def main(root, scale):
    root.mkdir(mode=0o700, parents=True, exist_ok=False)
    errors = []
    def failed(kind, value, traceback):
        errors.append(kind.__name__)
        sys.__excepthook__(kind, value, traceback)
    sys.excepthook = failed
    server = AnnouncementServer(root / 'server')
    friends = FriendsOwner(root / 'identity', root / 'anchor', http_factory=server.http)
    friends.activate(server.access.invite())
    device = friends._device(False)
    original = {name: (friends.path / name).read_bytes() for name in ('reticulum.key', 'wireguard.key', 'friends.initialized')}
    diagnostics = (root / 'service.log').open('w')
    worker = subprocess.Popen([sys.executable, str(Path(__file__).parent / 'tests/announcement_peer.py'), str(root)],
                              stdout=diagnostics, stderr=diagnostics)
    connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    def owner_pid():
        try:
            return connection.call_sync('org.freedesktop.DBus', '/org/freedesktop/DBus', 'org.freedesktop.DBus',
                'GetConnectionUnixProcessID', GLib.Variant('(s)', (BUS_NAME,)), GLib.VariantType.new('(u)'),
                Gio.DBusCallFlags.NONE, 1000, None).unpack()[0]
        except GLib.Error:
            return None
    app = None
    try:
        wait(lambda: owner_pid() == worker.pid)
        Adw.init()
        settings = Gtk.Settings.get_default()
        settings.set_property('gtk-enable-animations', False)
        settings.set_property('gtk-xft-dpi', int(96 * 1024 * (scale if scale != 2 else 1)))
        app = App(smoke=True)
        driver = Driver()
        app.complete('initialized', done((driver, driver.profiles(), False)), app.revision, None)
        pane = app.chat_pane
        pane.owner_factory = lambda: ChatClient(starter=lambda: None)
        app.chat_smoke = False
        app.ru = True
        app.present()
        app.select_page('messenger')
        settled(pane)
        click(pane, pane.t('chat_create'))
        assert pane.owner.owns_notifications
        pane.service_events()
        settled(pane)
        assert pane.header_menu.get_visible()
        pane.header_menu.grab_focus()
        key(0xff0d)
        wait(lambda: pane.screen == 'notice-admin' and not pane.busy)
        assert pane.notice.get_text() == pane.t('notice_denied')
        capture(app, root / 'ru-member-denied.png')
        server.store.grant_device(server.access, device.reference, 'Synthetic operator')
        pane.announcements.listing()
        settled(pane)
        assert pane.notice.get_text() == pane.t('notice_admin_active')
        capture(app, root / 'ru-admin-empty.png')
        click(pane, pane.t('notice_new'))
        admin = pane.announcements
        click(pane, pane.t('notice_preview'))
        assert pane.notice.get_text() == pane.t('notice_required')
        admin.title_input.set_text('😀' * 81)
        assert len(admin.title.encode('utf-16-le')) // 2 == 160
        admin.buffer.set_text('😀' * 2001)
        assert len(admin.body.encode('utf-16-le')) // 2 == 4000
        admin.title_input.set_text('Синтетическое объявление')
        admin.buffer.set_text('Публичный текст для теста.\nНичего не опубликовано в рабочем сервисе.')
        title = admin.title
        capture(app, root / 'ru-compose.png')
        click(pane, pane.t('notice_preview'))
        ident = admin.prepared['id']
        assert server.store.feed()['events'] == []
        assert admin.prepared['platforms'] == ['android', 'windows', 'linux'] and admin.prepared['days'] == 30
        capture(app, root / 'ru-preview.png')
        key(0xff1b)
        wait(lambda: pane.screen == 'notice-compose')
        assert admin.title == title
        click(pane, pane.t('notice_preview'))
        assert admin.prepared['id'] == ident
        (server.root / 'lose-reply').touch()
        click(pane, pane.t('notice_publish'))
        assert pane.screen == 'notice-preview' and pane.notice.get_text() == pane.t('notice_unavailable')
        assert len(server.store.feed()['events']) == 1
        capture(app, root / 'ru-unconfirmed-publish.png')
        click(pane, pane.t('notice_publish'))
        assert pane.screen == 'notice-admin' and len(server.store.feed()['events']) == 1
        capture(app, root / 'ru-published-list.png')
        click(pane, title)
        original_notice = server.store.current_event(ident)
        admin.title_input.set_text('Исправленное объявление')
        admin.buffer.set_text('Исправленный публичный текст')
        capture(app, root / 'ru-edit.png')
        click(pane, pane.t('notice_preview'))
        server.store.edit_device(device.reference, dict(id=ident, revision=1, request_id=uuid.uuid4().hex,
            title='Concurrent fixture edit', body='Another authorized revision'))
        click(pane, pane.t('notice_save_edit'))
        assert pane.notice.get_text() == pane.t('notice_conflict')
        capture(app, root / 'ru-revision-conflict.png')
        admin.listing()
        settled(pane)
        click(pane, 'Concurrent fixture edit')
        admin.title_input.set_text('Final synthetic edit')
        click(pane, pane.t('notice_preview'))
        click(pane, pane.t('notice_save_edit'))
        current = server.store.current_event(ident)
        assert current['revision'] == 3
        assert all(current[field] == original_notice[field] for field in ('author', 'created', 'expires', 'platforms', 'kind'))
        app.ru = False
        app.paint()
        pane.activate(True, False)
        settled(pane)
        capture(app, root / 'en-published-list.png')
        click(pane, 'Final synthetic edit')
        click(pane, pane.t('notice_preview'))
        capture(app, root / 'en-edit-preview.png')
        server.store.revoke_device(device.reference)
        click(pane, pane.t('notice_save_edit'))
        assert pane.notice.get_text() == pane.t('notice_denied')
        assert server.store.current_event(ident)['revision'] == 3
        capture(app, root / 'en-revoked-preview.png')
        server.store.grant_device(server.access, device.reference, 'Synthetic operator')
        (server.root / 'hold-list').touch()
        admin.listing()
        app.select_page('status')
        pump(.2)
        (server.root / 'hold-list').unlink()
        wait(lambda: not pane.busy)
        assert app.page == 'status'
        assert pane.content.get_first_child() is None
        assert all((friends.path / name).read_bytes() == value for name, value in original.items())
        assert not errors, errors
        (root / 'result.json').write_text(json.dumps(dict(result='PASS', scale=scale,
            device_scale=app.window.get_scale_factor(), font_dpi=96*(scale if scale != 2 else 1),
            actual_gtk=True, actual_session_dbus=True, separate_owner_pid=True,
            actual_server_proof_and_role_code=True, transport='in-process MockTransport inside child; no sockets',
            memory_vault='fixture only; real Secret Service covered separately',
            permission_denial=True, explicit_preview_no_write=True, stable_operation_id_retry=True,
            stale_revision_conflict=True, unchanged_audience_expiry=True, late_revocation_denied=True,
            unicode_limits=True, keyboard_enter_escape=True, stale_callback_fenced=True,
            existing_identity_unchanged=True, live_publication=False, operator_grants='synthetic isolated registry only',
            installed=False, android_visual_comparison='NOT_RUN'), indent=2)+'\n')
    finally:
        if app is not None and not app.closed:
            app.close(True)
            wait(lambda: app.closed)
        worker.terminate()
        try:
            worker.wait(timeout=10)
        except subprocess.TimeoutExpired:
            worker.kill()
            worker.wait(timeout=5)
        diagnostics.close()
        server.close()


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), float(sys.argv[2]))
