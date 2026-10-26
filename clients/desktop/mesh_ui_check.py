"""Real GTK rendering/interactions with synthetic service states, never host networking."""
import argparse
from concurrent.futures import Future
import json
from pathlib import Path
import threading

from app import App, Adw, Gtk, Gdk
from layout_check import pump


def done(value):
    future = Future()
    future.set_result(value)
    return future


def state(name, desired=True):
    return dict(state=name,desired_connected=desired,native=dict(native=dict(
        selected_profile='P1',tun_ready=name=='CONNECTED',packet=dict(diagnostic=dict(
            reliable_limits=dict(effective_send=16,local_receive=32),mux_profile='LEGACY64',mux_window=65536)))))


class Driver:
    def __init__(self):
        self.current = state('DISCONNECTED',False)
        self.starts = []
        self.stops = []
        self.start_gate = threading.Event()
        self.start_gate.set()
        self.started = threading.Event()
        self.lose_reply = False

    def mesh_available(self): return True
    def mesh_status(self): return self.current
    def profiles(self): return [('fcmesh0','Family Connect · MESH')]
    def active(self,ident): return self.current['state']=='CONNECTED'
    def start_mesh(self,profile):
        self.starts.append(profile)
        self.started.set()
        assert self.start_gate.wait(5)
        self.current=state('CONNECTING')
        if self.lose_reply:raise RuntimeError('Synthetic lost start reply')
    def disconnect(self,ident):
        self.stops.append(ident)
        self.current=state('DISCONNECTED',False)


class Owner:
    def __init__(self,*args): pass
    def connect_mesh(self,driver,profile): driver.start_mesh(profile)


def capture(app, path):
    from gi.repository import Gsk
    content=app.window.get_content()
    paintable=Gtk.WidgetPaintable.new(content)
    node=None
    for attempt in range(20):
        snapshot=Gtk.Snapshot()
        snapshot.scale(content.get_scale_factor(),content.get_scale_factor())
        paintable.snapshot(snapshot,content.get_width(),content.get_height())
        node=snapshot.to_node()
        if node is not None:break
        pump(.05)
    assert node is not None
    renderer=Gsk.Renderer.new_for_surface(app.window.get_surface())
    try:
        assert renderer.render_texture(node,None).save_to_png(str(path))
    finally:
        renderer.unrealize()


def main(output, scale):
    from gi.repository import PangoCairo
    Adw.init()
    device_scale=2 if scale>=2 else 1
    font_dpi=96*scale/device_scale
    Gtk.Settings.get_default().set_property('gtk-xft-dpi',round(font_dpi*1024))
    Gtk.Settings.get_default().set_property('gtk-enable-animations',False)
    app=App(smoke=True)
    driver=Driver()
    app.friends_owner_class=Owner
    app.friends_registered=True
    app.complete('initialized',done((driver,driver.profiles(),False,driver.mesh_status())),app.revision,None)
    app.protocol.set_selected(2)
    app.mesh_profile.set_selected(1)
    app.present();pump(.3)
    assert app.window.get_scale_factor()==device_scale
    assert abs(PangoCairo.context_get_resolution(app.status.get_pango_context())-font_dpi)<.01
    cases=[]
    try:
        assert app.transport_id()=='mesh' and app.selected()=='fcmesh0'
        assert app.dashboard_map.region is None
        app.friends_registered=False;app.mesh_identity_available=True;app.paint();pump()
        assert app.toggle.get_sensitive()
        app.gauge.grab_focus();pump();assert app.gauge.has_focus()
        assert app.window.child_focus(Gtk.DirectionType.TAB_FORWARD)
        app.gauge.grab_focus();assert app.gauge.activate();pump(.4)
        app.friends_registered=True
        assert driver.starts==['P1'] and app.active is False and not app.busy
        assert app.toggle.get_sensitive() and app.mesh_view()['pending']
        assert not app.protocol.get_sensitive() and not app.mesh_profile.get_sensitive()
        assert 'Disconnect' in app.gauge.get_tooltip_text() or 'Отключить' in app.gauge.get_tooltip_text()
        old_revision=app.revision
        app.toggle_vpn();pump(.2)
        assert driver.stops==['fcmesh0'] and not app.active and not app.mesh_view()['owned']
        app.complete('mesh-poll',done(state('CONNECTED')),old_revision,'fcmesh0')
        assert not app.active and not app.mesh_view()['owned']
        driver.start_gate.clear();driver.started.clear()
        app.toggle_vpn()
        assert driver.started.wait(1)
        app.toggle_vpn()
        assert app.service_cancel_requested
        driver.start_gate.set();pump(.4)
        assert len(driver.stops)==2 and not app.mesh_view()['owned']
        driver.start_gate.clear();driver.started.clear();driver.lose_reply=True
        app.toggle_vpn();assert driver.started.wait(1);app.toggle_vpn()
        driver.start_gate.set();pump(.4);driver.lose_reply=False
        assert len(driver.stops)==3 and not app.mesh_view()['owned']
        app.accept_mesh_state(state('RESTORING'));app.paint();pump()
        assert app.toggle.get_sensitive() and not app.active and app.recovery.identity is None
        app.toggle_vpn();pump(.2)
        assert len(driver.stops)==4 and app.recovery.identity is None
        app.accept_mesh_state(state('FAILED'));app.active=None;app.paint();pump()
        assert app.toggle.get_sensitive()
        app.toggle_vpn();pump(.2)
        assert len(driver.stops)==5 and not app.mesh_view()['owned']
        driver.current=state('RESTORING')
        app.complete('initialized',done((driver,driver.profiles(),False,driver.current)),app.revision,None)
        pump()
        assert app.mesh_view()['owned'] and app.transport_id()=='mesh' and app.recovery.identity is None
        app.select_page('settings')
        assert app.key_pressed(None,Gdk.KEY_Escape,0,0) and app.page=='status'
        accepted=[];app.confirm('Test','Accept',lambda:accepted.append(True))
        assert app.key_pressed(None,Gdk.KEY_Escape,0,0) and app.confirmation is None and not accepted
        output.mkdir(parents=True,exist_ok=True)
        for ru in (False,True):
            app.ru=ru
            for name in ('DISCONNECTED','CONNECTING','CONNECTED','RESTORING','FAILED'):
                driver.current=state(name,name!='DISCONNECTED');app.accept_mesh_state(driver.current)
                app.select_page('status');app.paint();pump(.12)
                assert app.gauge.get_mapped() and all(button.get_mapped() for button in app.nav.values())
                language='ru' if ru else 'en'
                capture(app,output/f'{language}-{name.lower()}.png')
                cases.append(dict(language=language,state=name,width=app.window.get_width(),height=app.window.get_height()))
            driver.current=state('CONNECTED');app.accept_mesh_state(driver.current)
            for page in ('settings','route'):
                app.select_page(page);pump(.15)
                capture(app,output/f'{language}-{page}.png')
            assert 'RS16/32 · LEGACY64' in app.mesh_profile_details.get_text()
        app.select_page('status');app.window.set_default_size(780,800)
        app.set_detail(('Длинное сообщение об ошибке. Long error message. ')*12);pump(.3)
        assert app.body.get_width()<=560 and app.scroll.get_vadjustment().get_value()==0, (app.body.get_width(),app.scroll.get_vadjustment().get_value())
        assert app.detail.get_height()>=app.detail.get_layout().get_pixel_size()[1]
        capture(app,output/'wide-long-error.png')
        print(json.dumps(dict(result='PASS',scale=scale,device_scale=device_scale,font_dpi=font_dpi,
            scope='GTK synthetic service; fractional cases are font-DPI, not compositor fractional scaling',cases=cases)))
    finally:
        driver.start_gate.set()
        app.busy=False;app.close(True);pump()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--scale',type=float,default=1)
    arguments=parser.parse_args()
    main(arguments.output,arguments.scale)
