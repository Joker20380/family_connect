"""Ubuntu GTK/Xvfb UX evidence; only synthetic in-memory conversations."""
import json
from pathlib import Path
import sys
from types import SimpleNamespace

from app import Adw, Gtk
from mesh_ui_check import capture, pump
from messenger_window import MessengerWindow

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
    window = MessengerWindow(owner_factory=lambda: fixture)
    window.present_chat()
    pane = window.pane
    settle(pane)
    pane.conversation(fixture.cards[0])
    settle(pane)
    pump(.3)
    sizes = {}
    def shot(name):
        pump(.3)
        sizes[name] = [window.get_width(), window.get_height()]
        assert pane.composer_box.get_mapped() if pane.screen == 'conversation' else True
        capture_native(window, destination / (name + '.png'))
    shot('wide-conversation')
    pane.emoji_button.popup()
    pump(.8)
    assert pane.emoji.get_mapped()
    capture_native(window, destination / 'emoji-chooser.png', pane.emoji)
    pane.emoji.popdown()
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
    closed = []
    pane.request_close(lambda: closed.append(True))
    while not closed:
        pump(.03)
    window.dispose_window()
    from chat_ui import ChatPane
    before = Adw.ApplicationWindow(default_width=420, default_height=680, title='Before · synthetic')
    old = ChatPane(owner_factory=ChatFixture)
    scroll = Gtk.ScrolledWindow()
    scroll.set_child(old)
    before.set_content(scroll)
    before.present()
    old.activate(True, True)
    settle(old)
    old.conversation(old.owner.cards[0])
    settle(old)
    capture(SimpleNamespace(window=before), destination / 'before.png')
    closed.clear()
    old.request_close(lambda: closed.append(True))
    while not closed:
        pump(.03)
    before.destroy()
    (destination / 'result.json').write_text(json.dumps(dict(scale=scale, rendering='real GTK/X11/Xvfb widget snapshots; native popover at observed widget coordinates',
        synthetic=True, sizes=sizes, screenshots=sorted(path.name for path in destination.glob('*.png'))), indent=2) + '\n')


if __name__ == '__main__':
    main(Path(sys.argv[1]), float(sys.argv[2]))
