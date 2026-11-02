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
def test_real_picker_has_two_nodes_with_distinct_metrics_and_exact_connection(monkeypatch, ru):
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
        assert application.route_target() == 'nl-amsterdam-1'
        assert application.country.get_model().get_n_items() == 3
        application.all_loads={target:dict(country=target,percent=percent,cpu=percent,rx=5,tx=2,capacity=5000,
            estimated=True,capacity_basis='operator-assumed-capacity',observed_at=time.time())
            for target,percent in zip(module.EXPLICIT_GATEWAYS,(23,7))}
        for target in module.EXPLICIT_GATEWAYS:
            index=module.GATEWAY_TARGETS.index(target)
            application.country.set_selected(index)
            application.route_changed()
            pump()
            assert application.route_target() == target
            assert application.country_label(target) == ('Амстердам ' if ru else 'Amsterdam ') + target[-1]
            assert application.route_options['gateway_id'] == target and application.route_options['country'] == 'nl'
            assert application.load_key() == 'gateway:'+target
            application.load_ident=application.load_key()
            application.load_sample=application.all_loads[target]
            application.refresh_country_labels();application.render_server_load()
            assert ('23%' if target.endswith('1') else '7%') in application.load_label.get_text()
            assert '5000' in application.load_label.get_tooltip_text()
            application.toggle_vpn()
            callbacks.pop()()
            assert connections[-1] == (target, 'awg')
        render = os.environ.get('FC_SELECTION_RENDER_DIR')
        if render:
            from gi.repository import Gsk
            paintable = module.Gtk.WidgetPaintable.new(application.window.get_content())
            deadline = time.monotonic() + 3
            node = None
            while node is None and time.monotonic() < deadline:
                pump()
                snapshot = module.Gtk.Snapshot()
                paintable.snapshot(snapshot, application.window.get_width(), application.window.get_height())
                node = snapshot.to_node()
            assert application.window.get_mapped() and node is not None
            renderer = Gsk.Renderer.new_for_surface(application.window.get_surface())
            try:
                destination = Path(render) / ('selection-' + ('ru' if ru else 'en') + '-' + os.environ.get('GDK_SCALE', '1') + '.png')
                assert renderer.render_texture(node, None).save_to_png(str(destination))
            finally:
                renderer.unrealize()
        monkeypatch.setattr(application, 'transport_id', lambda: 'auto')
        application.toggle_vpn()
        assert not callbacks and len(connections) == 2
        assert 'AWG' in application.detail_text
        application.configure_gateway_picker()
        application.route_changed()
        assert application.country.get_model().get_n_items()==2
        assert application.route_target()=='nl'
        assert application.load_key()=='country:nl'
        monkeypatch.setattr(application,'transport_id',lambda:'tcp')
        application.route_changed()
        assert application.country.get_model().get_n_items()==3
        assert application.route_target()=='nl-amsterdam-2'
        assert application.route_options['gateway_id']=='nl-amsterdam-2'
    finally:
        application.busy = False
        application.close(True)
        pump()
