"""Ubuntu GTK/Xvfb UX evidence; only synthetic in-memory conversations."""
import json
from pathlib import Path
import sys
from types import SimpleNamespace

from app import Adw, App, Gtk
from mesh_ui_check import capture, pump

sys.path.insert(0, str(Path(__file__).parent / 'tests'))
from messenger_fixture import ChatFixture
from test_messenger_ux import settle


def capture_native(window, path, popup=None):
    from gi.repository import Graphene
    content = window.get_content()
    snapshot = Gtk.Snapshot()
    Gtk.WidgetPaintable.new(content).snapshot(snapshot, content.get_width(), content.get_height())
    if popup is not None:
        assert popup.get_mapped() and popup.get_surface().get_mapped()
        success, bounds = popup.compute_bounds(content)
        assert success
        snapshot.save()
        snapshot.translate(Graphene.Point().init(bounds.get_x(), bounds.get_y()))
        Gtk.WidgetPaintable.new(popup).snapshot(snapshot, popup.get_width(), popup.get_height())
        snapshot.restore()
    node = snapshot.to_node()
    assert node is not None
    assert window.get_renderer().render_texture(node, None).save_to_png(str(path))


def main(destination, scale):
    destination.mkdir(parents=True, exist_ok=False)
    Adw.init()
    Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.FORCE_DARK)
    Gtk.Settings.get_default().set_property('gtk-enable-animations', False)
    Gtk.Settings.get_default().set_property('gtk-xft-dpi', round(96 * scale * 1024))
    fixture = ChatFixture()
    fixture.messages[0]['text'] = 'Привет! :) *LOL* @}->-- *DANCE*\nОбычный текст и Unicode 🙂'
    app = App(smoke=True)
    app.ru = True
    app.paint()
    window = app.window
    pane = app.chat_pane
    pane.owner_factory = lambda: fixture
    app.present()
    pump(.4)
    capture_native(window, destination / 'status.png')
    app.select_page('messenger')
    window.set_default_size(900, 800)
    pane.activate(True, True)
    settle(pane)
    pane.conversation(fixture.cards[0])
    settle(pane)
    pump(.3)
    sizes = {}
    def shot(name):
        pump(.3)
        assert len([item for item in Gtk.Window.get_toplevels() if item.get_visible()]) == 1
        assert app.window is window
        sizes[name] = [window.get_width(), window.get_height()]
        assert pane.composer_box.get_mapped() if pane.screen == 'conversation' else True
        capture_native(window, destination / (name + '.png'))
    shot('wide-conversation')
    pane.emoji_button.popup()
    pump(.8)
    assert pane.smileys.get_mapped()
    capture_native(window, destination / 'icq-picker.png', pane.smileys)
    pane.smileys.popdown()
    window.set_default_size(360, 680)
    pump(.5)
    assert pane.split.get_folded()
    shot('narrow-conversation')
    pane.contacts()
    settle(pane)
    shot('narrow-contacts')
    window.set_default_size(900, 680)
    fixture.cards = []
    fixture.invoke_original = fixture.invoke
    fixture.invoke = lambda operation, **arguments: [] if operation == 'inbox_summary' else fixture.invoke_original(operation, **arguments)
    pane.contacts()
    settle(pane)
    shot('empty')
    pane.opened = False
    pane.open_error = 'identity_unavailable'
    pane.welcome()
    shot('onboarding')
    app.close(True)
    while not app.closed:
        pump(.03)
    (destination / 'result.json').write_text(json.dumps(dict(scale=scale, rendering='real GTK/X11/Xvfb widget snapshots; native popover at observed widget coordinates',
        synthetic=True, one_toplevel=True, same_window=True, sizes=sizes, screenshots=sorted(path.name for path in destination.glob('*.png'))), indent=2) + '\n')


if __name__ == '__main__':
    main(Path(sys.argv[1]), float(sys.argv[2]))
