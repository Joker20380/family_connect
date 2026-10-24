"""Display-backed Auto interactions; synthetic service, no installed identity or network."""
import argparse
from pathlib import Path
import json
import threading

from app import App, Adw, Gtk, Gdk, STATE_LABELS
from layout_check import pump, settled_size
from mesh_ui_check import capture, done, state as mesh_state


def state(name='DISCONNECTED', selected='restricted'):
    return dict(state=name, desired_connected=name not in ('DISCONNECTED','DISCONNECTING'), generation='a'*32,
        requested_profile='P1', reason='', selected=selected,
        controller=dict(policy=dict(selected=selected,events=[],events_dropped=0),
            platform=dict(attempt=1,interface='fcmesh0'),mesh=dict(native=mesh_state(name)['native'])))


def inject(app,driver,value):
    app.revision+=1;driver.current=value;app.accept_auto_state(value);app.paint();pump()


class Driver:
    def __init__(self):
        self.current=state()
        self.starts=[];self.stops=[];self.resolved=0;self.enabled=True
        self.start_gate=threading.Event();self.start_gate.set()
        self.started=threading.Event();self.lose_reply=False;self.denied=False
    def mesh_available(self):return True
    def auto_available(self):return self.enabled
    def mesh_status(self):return mesh_state('DISCONNECTED',False)
    def profiles(self):return [('fcmesh0','Family Connect · MESH')]
    def active(self,ident):return False
    def auto_status(self):return self.current
    def resolve_auto_status(self):
        self.resolved+=1
        return self.current
    def start_auto(self,country,profile):
        self.starts.append((country,profile));self.started.set()
        assert self.start_gate.wait(5)
        if self.denied:raise RuntimeError('Synthetic authorization denied before start')
        self.current=state('CONNECTING')
        if self.lose_reply:raise RuntimeError('Synthetic lost reply')
    def stop_auto(self,generation):
        assert generation==self.current['generation']
        self.stops.append(generation);self.current=state()
        return self.current
    def check_auto_ip(self):return 'IP: 192.0.2.1 · NL'


class Owner:
    def __init__(self,*args):pass
    def connect_auto(self,country,driver,profile):driver.start_auto(country,profile)


def main(output,scale):
    from gi.repository import PangoCairo
    Adw.init()
    device_scale=2 if scale>=2 else 1
    font_dpi=96*scale/device_scale
    Gtk.Settings.get_default().set_property('gtk-xft-dpi',round(font_dpi*1024))
    Gtk.Settings.get_default().set_property('gtk-enable-animations',False)
    app=App(smoke=True);driver=Driver();app.friends_owner_class=Owner
    app.route_options={'transport':'auto'};app.mesh_identity_available=True
    app.complete('initialized',done((driver,driver.profiles(),False,driver.mesh_status(),driver.auto_status())),app.revision,None)
    app.mesh_profile.set_selected(1);app.present();pump(.3)
    try:
        assert app.window.get_scale_factor()==device_scale
        assert abs(PangoCairo.context_get_resolution(app.status.get_pango_context())-font_dpi)<.01
        assert app.transport_id()=='auto' and app.selected()=='fcauto0'
        assert app.toggle.get_sensitive() and not app.friends_registered
        app.gauge.grab_focus();pump();assert app.gauge.has_focus()
        assert app.window.child_focus(Gtk.DirectionType.TAB_FORWARD)
        app.gauge.grab_focus();assert app.gauge.activate();pump(.4)
        assert driver.starts==[('nl','P1')] and app.managed_view()['pending'] and not app.active
        assert not app.protocol.get_sensitive() and not app.country.get_sensitive()
        assert app.toggle.get_sensitive() and app.recovery.identity is None
        revision=app.revision;app.toggle_vpn();pump(.3)
        assert len(driver.stops)==1 and not app.managed_view()['owned']
        app.complete('auto-poll',done(state('CONNECTED')),revision,'fcauto0')
        assert not app.active and not app.managed_view()['owned']
        for lose_reply in (False,True):
            driver.start_gate.clear();driver.started.clear();driver.lose_reply=lose_reply
            app.toggle_vpn();assert driver.started.wait(1);app.toggle_vpn()
            assert app.service_cancel_requested
            driver.start_gate.set();pump(.4)
            assert not app.busy and not app.managed_view()['owned']
        assert len(driver.stops)==3 and driver.resolved==0
        driver.lose_reply=False
        driver.start_gate.clear();driver.started.clear();driver.denied=True
        app.toggle_vpn();assert driver.started.wait(1);app.toggle_vpn()
        driver.start_gate.set();pump(.4);driver.denied=False
        assert len(driver.stops)==3 and driver.resolved==0 and not app.managed_view()['owned']
        for name in ('RESTORING','FAILED'):
            inject(app,driver,state(name))
            assert app.toggle.get_sensitive() and app.recovery.identity is None
            app.toggle_vpn();pump(.3)
            assert not app.managed_view()['owned']
        driver.current=state('RESTORING')
        app.complete('initialized',done((driver,driver.profiles(),False,driver.mesh_status(),driver.current)),app.revision,None)
        assert app.transport_id()=='auto' and app.managed_view()['owned']
        app.on_close();pump()
        assert app.confirmation is not None and not app.closed
        assert app.key_pressed(None,Gdk.KEY_Escape,0,0) and app.confirmation is None
        output.mkdir(parents=True,exist_ok=True)
        cases=[]
        for ru in (False,True):
            app.ru=ru
            for name in ('DISCONNECTED','CONNECTING','CONNECTED','RESTORING','DISCONNECTING','FAILED'):
                inject(app,driver,state(name))
                app.select_page('status');app.paint();settled_size(app.window);pump(.15)
                expected='STOPPING' if name=='DISCONNECTING' else name
                assert app.status.get_text()==STATE_LABELS[expected][0 if ru else 1]
                assert app.gauge.connected==(name=='CONNECTED') and app.active==(name=='CONNECTED')
                if name!='CONNECTED':assert not app.detail_text.startswith('IP: ')
                assert app.gauge.get_mapped() and all(button.get_mapped() for button in app.nav.values())
                capture(app,output/f'{"ru" if ru else "en"}-{name.lower()}.png')
                cases.append(dict(language='ru' if ru else 'en',state=name,width=app.window.get_width(),height=app.window.get_height()))
            for selected,label in (('awg','AWG 3.1'),('tcp','TCP REALITY'),('restricted','MESH')):
                inject(app,driver,state('CONNECTED',selected))
                assert 'Auto → '+label in app.selectors.state.get_text()
                assert (app.dashboard_map.region is None)==(selected=='restricted')
                assert app.selectors.mesh_route.get_visible()==(selected=='restricted')
                assert ('RS16/32 · LEGACY64' in app.mesh_profile_details.get_text())==(selected=='restricted')
                assert app.diagnostics.current['selected_transport']=='auto'
                assert app.diagnostics.current['actual_transport']==selected
                if selected=='restricted':
                    app.check_ip();pump(.2);assert app.detail_text=='IP: 192.0.2.1 · NL'
            for page in ('settings','route'):
                app.select_page(page);settled_size(app.window);pump(.15)
                capture(app,output/f'{"ru" if ru else "en"}-{page}.png')
        app.select_page('status');app.window.set_default_size(780,800)
        app.set_detail(('Длинная ошибка. Long error message. ')*12);pump(.3)
        assert app.body.get_width()<=560 and app.scroll.get_vadjustment().get_value()==0
        assert app.detail.get_height()>=app.detail.get_layout().get_pixel_size()[1]
        capture(app,output/'wide-long-error.png')
        app.accept_auto_state(state());driver.enabled=False;app.configure_transports()
        assert not any(key=='auto' for key,_ in app.transports)
        print(json.dumps(dict(result='PASS',scale=scale,device_scale=device_scale,font_dpi=font_dpi,cases=cases,
            scope='Actual GTK; synthetic Auto service; fractional scales are font-DPI, not compositor scaling')))
    finally:
        driver.start_gate.set();app.busy=False;app.close(True);pump()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--scale',type=float,default=1)
    arguments=parser.parse_args();main(arguments.output,arguments.scale)
