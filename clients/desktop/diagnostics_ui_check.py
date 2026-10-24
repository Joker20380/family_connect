"""Rendered GTK support/export checks with an isolated synthetic service, no VPN."""
import json
import os
from pathlib import Path
import sys
import time

os.environ.setdefault('GDK_BACKEND', 'x11')
from app import App, Adw, Gtk, Gdk, Gio
from mesh_ui_check import Driver, capture, done, pump, state
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.diagnostic106_vectors import baseline
from provisioning.support import SupportConsent, SupportSnapshot, SupportUpload


class SupportOwner:
    def refresh_support_id(self, version, code):
        assert version == 'linux-0.2.11' and code == 2011
        return 'FC-3Y3W-EBZE'


def wait_for(predicate):
    deadline = time.monotonic() + 5
    while not predicate() and time.monotonic() < deadline:
        pump(.05)
    assert predicate()


def main(destination, scale):
    destination.mkdir(parents=True, exist_ok=False)
    if hasattr(Gtk, 'disable_portals'):
        Gtk.disable_portals()
    Adw.init()
    assert 'X11' in type(Gdk.Display.get_default()).__name__
    Gtk.Settings.get_default().set_property('gtk-enable-animations', False)
    Gtk.Settings.get_default().set_property('gtk-xft-dpi', round(96 * scale / int(os.environ.get('GDK_SCALE', '1')) * 1024))
    app = App(smoke=True)
    driver = Driver()
    app.friends_owner = SupportOwner()
    consent_path = destination/'consent'
    consent_path.mkdir(mode=0o700)
    sent = []
    def send(report, *, cancelled):
        assert not cancelled()
        sent.append(json.loads(SupportSnapshot.encode(report)))
    app.support_upload = SupportUpload(SupportConsent(consent_path, 'a'*32), send, app.online_snapshot, 2011)
    app.complete('initialized', done((driver, driver.profiles(), False)), app.revision, None)
    app.friends_owner_class = SupportOwner
    app.configure_transports()
    app.protocol.set_selected(2)
    app.mesh_profile.set_selected(1)
    driver.current = state('RESTORING')
    reference = baseline()
    driver.current['native']['native']['packet']['diagnostic'] = reference['session']
    driver.current['native']['native']['startup'] = reference['startup']
    app.accept_mesh_state(driver.current)
    app.present()
    app.select_page('settings')
    pump(.3)
    try:
        app.support_refresh.emit('clicked')
        pump(.3)
        assert app.support_id == 'FC-3Y3W-EBZE' and app.support_copy.get_sensitive()
        app.support_copy.emit('clicked')
        clipboard = []
        app.window.get_clipboard().read_text_async(None, lambda owner, result: clipboard.append(owner.read_text_finish(result)))
        pump(.2)
        assert clipboard == ['FC-3Y3W-EBZE']
        for language in ('ru', 'en'):
            app.ru = language == 'ru'
            app.paint()
            pump(.2)
            assert app.detail_text == ('Support ID скопирован' if app.ru else 'Support ID copied')
            app.support_refresh.grab_focus()
            adjustment = app.scroll.get_vadjustment()
            adjustment.set_value(adjustment.get_upper())
            pump(.2)
            assert app.support_refresh.has_focus()
            assert app.window.child_focus(Gtk.DirectionType.TAB_FORWARD)
            capture(app, destination / (language + '-settings.png'))
            app.diagnostic_button.emit('clicked')
            pump(.1)
            assert app.confirmation is not None
            capture(app, destination / (language + '-privacy.png'))
            assert app.key_pressed(None, Gdk.KEY_Escape, 0, 0)
            assert app.confirmation is None
            assert not app.support_online.get_active() and not sent
            app.support_online.emit('state-set', True)
            pump(.1)
            assert app.confirmation is not None and not app.support_online.get_active()
            capture(app, destination/(language+'-online-consent.png'))
            assert app.key_pressed(None, Gdk.KEY_Escape, 0, 0)
            assert not (consent_path/SupportConsent.NAME).exists() and not sent
        app.support_online.emit('state-set', True)
        app.confirmation.get_last_child().emit('clicked')
        wait_for(lambda: not app.support_consent_busy and app.support_upload.status()['state'] == 'STORED')
        app.paint_support_upload()
        assert app.support_online.get_active() and len(sent) == 1
        assert sent[0]['platform'] == 'linux' and sent[0]['metrics']['speed_profile'] == 'P1'
        assert (consent_path/SupportConsent.NAME).stat().st_mode & 0o777 == 0o600
        assert SupportConsent(consent_path, 'a'*32).enabled()
        capture(app, destination/'en-online-enabled.png')
        app.window.set_default_size(390, 600)
        pump(.3)
        app.support_online.grab_focus()
        pump(.2)
        assert app.support_online.has_focus()
        measured, bounds = app.support_online.compute_bounds(app.scroll)
        assert measured and bounds.get_y() >= 0 and bounds.get_y()+bounds.get_height() <= app.scroll.get_height()+1
        monitor = app.window.get_display().get_monitor_at_surface(app.window.get_surface()).get_geometry()
        assert app.window.get_height() <= monitor.height and app.window.get_width() <= monitor.width
        geometry = dict(window=[app.window.get_width(),app.window.get_height()], monitor=[monitor.width,monitor.height],
                        scale_factor=app.window.get_scale_factor(), font_dpi=Gtk.Settings.get_default().get_property('gtk-xft-dpi')/1024,
                        display_type=type(Gdk.Display.get_default()).__name__)
        capture(app, destination/'en-online-compact-focus.png')
        app.support_online.emit('state-set', False)
        wait_for(lambda: not app.support_consent_busy)
        assert not app.support_online.get_active() and not (consent_path/SupportConsent.NAME).exists()
        assert len(sent) == 1 and app.support_upload.status()['state'] == 'OFF'
        app.diagnostic_button.emit('clicked')
        app.confirmation.get_last_child().emit('clicked')
        pump(.3)
        assert app.file_chooser.get_action() == Gtk.FileChooserAction.SAVE
        target = destination / 'diagnostics.json'
        target.write_text('{}')
        app.file_chooser.set_file(Gio.File.new_for_path(str(target.resolve())))
        app.file_chooser.set_current_name(target.name)
        wait_for(lambda: app.file_chooser.get_file() is not None and app.file_chooser.get_file().get_path() == str(target.resolve()))
        assert app.file_chooser.get_file().get_path() == str(target.resolve())
        app.file_chooser.emit('response', Gtk.ResponseType.ACCEPT)
        wait_for(lambda: not app.diagnostic_busy and app.file_chooser is None)
        assert not app.diagnostic_busy and app.file_chooser is None
        report = json.loads(target.read_bytes())['ring']
        assert report['device_support_id'] == 'FC-3Y3W-EBZE'
        assert report['state'] == 'RESTORING' and report['actual_transport'] == 'none'
        assert report['selected_profile'] == 'P1'
        assert report['restricted_session']['reliable_limits']['local_write_completion'] is True
        assert report['restricted_session']['lifecycle']['trace'][0]['delivery']['flow']['send_next'] == 3
        assert report['restricted_session']['mux_lifecycle']['first_unknown']['stream']['send_done'] == list(range(1000, 1009))
        assert report['restricted_startup']['observation']['error_category'] == 'IO_DEADLINE'
        assert target.stat().st_mode & 0o777 == 0o600
        assert 'JSON saved' in app.detail_text
        assert not driver.starts and not driver.stops
        (destination / 'result.json').write_text(json.dumps(dict(scale=scale, status='PASS',
            export_bytes=target.stat().st_size, service='SYNTHETIC', installed=False, geometry=geometry,
            scope='GTK/Xvfb; 125/150 percent use font DPI, not compositor fractional scaling',
            checks=['RU', 'EN', 'keyboard focus', 'clipboard', 'privacy cancel', 'GTK native save chooser (portal disabled in fixture)', 'valid JSON', 'native flow/Mux/startup preserved', 'private file', 'online consent cancel/enable/revoke (synthetic sender)', 'VPN unchanged']), indent=2) + '\n')
    finally:
        app.active = False
        app.mesh_state = None
        app.close(True)
        pump(.1)


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), float(sys.argv[2]))
