import os
import time
from pathlib import Path

import pytest

pytest.importorskip('gi')
pytestmark = pytest.mark.skipif(not os.environ.get('DISPLAY'), reason='Real GTK display required')

import app as module


def pump():
    deadline = time.monotonic() + .15
    while time.monotonic() < deadline:
        while module.GLib.MainContext.default().iteration(False):
            pass
        time.sleep(.005)


@pytest.mark.parametrize('ru', [True, False])
def test_real_picker_preserves_default_and_passes_exact_selected_gateway(monkeypatch, ru):
    module.Adw.init()
    application = module.App(smoke=True)
    connections = []
    class Owner:
        def connect(self, target, driver, *, transport):
            connections.append((target, transport))
    class Driver:
        def profiles(self):
            return []
    try:
        application.ru = ru
        application.driver = Driver()
        application.active = False
        application.friends_registered = True
        application.friends_owner_class = lambda *_: Owner()
        callbacks = []
        monkeypatch.setattr(application, 'submit', lambda callback, *args, **kwargs: callbacks.append(callback))
        application.present()
        pump()
        assert application.route_target() == 'nl'
        assert application.country.get_model().get_n_items() == 4
        for index, target in enumerate(module.GATEWAY_TARGETS[2:], 2):
            application.country.set_selected(index)
            application.route_changed()
            pump()
            assert application.route_target() == target
            assert application.country_label(target) == ('Амстердам ' if ru else 'Amsterdam ') + str(index - 1)
            assert application.route_options['gateway_id'] == target and application.route_options['country'] == 'nl'
            assert application.load_key() is None
            application.toggle_vpn()
            callbacks.pop()()
            assert connections[-1] == (target, 'awg')
        render = os.environ.get('FC_SELECTION_RENDER_DIR')
        if render:
            from gi.repository import Gsk
            paintable = module.Gtk.WidgetPaintable.new(application.window.get_content())
            snapshot = module.Gtk.Snapshot()
            paintable.snapshot(snapshot, application.window.get_width(), application.window.get_height())
            renderer = Gsk.Renderer.new_for_surface(application.window.get_surface())
            try:
                destination = Path(render) / ('selection-' + ('ru' if ru else 'en') + '-' + os.environ.get('GDK_SCALE', '1') + '.png')
                assert renderer.render_texture(snapshot.to_node(), None).save_to_png(str(destination))
            finally:
                renderer.unrealize()
        monkeypatch.setattr(application, 'transport_id', lambda: 'auto')
        application.toggle_vpn()
        assert not callbacks and len(connections) == 2
        assert 'AWG' in application.detail_text
        application.country.set_selected(0)
        application.route_changed()
        assert application.route_options['gateway_id'] is None
    finally:
        application.busy = False
        application.close(True)
        pump()
