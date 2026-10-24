"""Real GTK detach, private D-Bus and user-systemd support restart; no production access."""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

os.environ.setdefault('GDK_BACKEND', 'x11')
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import httpx
from gi.repository import Gio, GLib
from app import App, Gtk, Adw, Gdk
from control.friends.access import Access
from control.friends import diagnostics, support_ids
from messenger.local import LocalError
from provisioning.chat_client import ChatClient
from provisioning.chat_rpc import BUS_NAME
from provisioning.friends_owner import FriendsOwner
from provisioning.support import SupportConsent
from provisioning.support_client import SupportClient
from scripts.diagnostic106_vectors import baseline
from mesh_ui_check import Driver, capture, done, pump


def wait(predicate, seconds=12):
    deadline = time.monotonic()+seconds
    while time.monotonic() < deadline:
        pump(.03)
        if predicate():return
    raise AssertionError('Support owner observation deadline')


def main(root):
    root.mkdir(mode=0o700, parents=True, exist_ok=False)
    parent_unit = os.environ['FC_TEST_PARENT_UNIT']
    assert parent_unit.startswith('fc-parity-support-service-') and parent_unit.endswith('.service')
    unit = 'fc-support-fixture-'+str(os.getpid())
    connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    def owner_pid():
        try:
            return connection.call_sync('org.freedesktop.DBus','/org/freedesktop/DBus','org.freedesktop.DBus',
                'GetConnectionUnixProcessID',GLib.Variant('(s)',(BUS_NAME,)),GLib.VariantType.new('(u)'),
                Gio.DBusCallFlags.NONE,1000,None).unpack()[0]
        except GLib.Error:return None
    assert owner_pid() is None, 'Fixture must use a private session bus'
    def ctl(*args):
        return subprocess.run(['systemctl','--user',*args],capture_output=True,text=True,timeout=15)
    access = Access(root/'registry.db');access.initialize()
    def enroll(request):
        value=json.loads(request.content)
        if request.url.path=='/friends/challenge':return httpx.Response(200,json=access.challenge(**value))
        if request.url.path=='/friends/activate':return httpx.Response(200,json=dict(device=access.complete(value,'activate')['device'],status='active'))
        raise AssertionError('Only isolated enrollment is permitted')
    friends=FriendsOwner(root/'device',root/'anchor',http_factory=lambda:
        httpx.Client(base_url='https://test.invalid',transport=httpx.MockTransport(enroll)))
    friends.activate(access.invite())
    with access.db() as database:
        support_ids.create(database)
        support_id=support_ids.registered(database,friends._device().reference)
    key_hashes={name:hashlib.sha256((friends.path/name).read_bytes()).hexdigest() for name in ('reticulum.key','wireguard.key','friends.initialized')}
    sample=dict(state='CONNECTING',network_class='WIFI',restricted_readiness='READY',vpn_capture_open=False,restricted_session=baseline()['session'])
    (root/'sample.json').write_text(json.dumps(sample))
    def reports():
        path=root/'stored.jsonl'
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
    def proxy():return SupportClient(client=ChatClient(starter=lambda:None))
    app=None;unit_started=False;monitor=None
    try:
        environment=['--setenv='+name+'='+os.environ[name] for name in ('DBUS_SESSION_BUS_ADDRESS','HOME','XDG_CONFIG_HOME',
            'XDG_DATA_HOME','XDG_STATE_HOME','XDG_CACHE_HOME','PYTHONPATH','XDG_RUNTIME_DIR') if name in os.environ]
        command=['systemd-run','--user','--collect','--quiet','--unit='+unit,'--property=Type=exec',
            '--property=Restart=on-failure','--property=RestartSec=1s','--property=StartLimitIntervalSec=240s',
            '--property=StartLimitBurst=3','--property=RuntimeMaxSec=210s','--property=TimeoutStopSec=15s',
            '--property=KillMode=control-group','--property=CPUQuota=25%','--property=MemoryMax=256M',
            '--property=TasksMax=128','--property=UMask=0077','--property=BindsTo='+parent_unit,
            '--property=After='+parent_unit]+environment+[sys.executable,str(Path(__file__).parent/'tests/support_service_peer.py'),str(root)]
        unit_started=True;subprocess.run(command,check=True,capture_output=True,timeout=15)
        wait(lambda:owner_pid() is not None)
        first_pid=owner_pid()
        if hasattr(Gtk,'disable_portals'):Gtk.disable_portals()
        Adw.init();assert 'X11' in type(Gdk.Display.get_default()).__name__
        Gtk.Settings.get_default().set_property('gtk-enable-animations',False)
        def window():
            result=App(smoke=True);driver=Driver()
            result.complete('initialized',done((driver,driver.profiles(),False)),result.revision,None)
            result.support_upload=proxy();result.ru=True;result.present();result.select_page('settings')
            result.support_upload.tick()
            wait(lambda:result.support_upload.status()['available'])
            result.paint_support_upload()
            return result
        app=window()
        assert not app.support_online.get_active() and not reports()
        app.support_online.emit('state-set',True)
        assert app.confirmation is not None and not reports()
        app.confirmation.get_last_child().emit('clicked')
        wait(lambda:not app.support_consent_busy and app.support_upload.status()['enabled'])
        wait(lambda:len(reports())==1)
        first_report=reports()[0]
        consent=(friends.path/SupportConsent.NAME).read_bytes()
        revision=app.support_upload.status()['revision']
        capture(app,root/'ru-service-online-enabled.png')
        app.close(True);wait(lambda:app.closed);app=None
        assert owner_pid()==first_pid
        sample.update(state='CONNECTED',vpn_capture_open=True)
        (root/'sample.json').write_text(json.dumps(sample))
        wait(lambda:len(reports())>=2,seconds=78)
        latest=diagnostics.read(root/'snapshots.db',support_id,int(time.time()))['report']
        assert latest['metrics']['state']=='CONNECTED' and latest['metrics']['speed_profile']=='P1'
        assert reports()[1]['at']-first_report['at']>=60
        assert reports()[1]['pid']==first_pid
        os.kill(first_pid,signal.SIGKILL)
        wait(lambda:owner_pid() not in (None,first_pid),seconds=15)
        second_pid=owner_pid()
        monitor=ChatClient(starter=lambda:None)
        status=monitor.request('support_status',{})
        assert status['enabled'] and status['revision']!=revision
        assert (friends.path/SupportConsent.NAME).read_bytes()==consent
        try:
            monitor.request('support_consent',dict(enabled=False,revision=revision))
            raise AssertionError('Old service control revision accepted')
        except LocalError as failure:assert str(failure)=='support_conflict'
        monitor.close();monitor=None
        app=window();assert app.support_online.get_active()
        capture(app,root/'ru-reopened-same-consent.png')
        app.support_online.emit('state-set',False)
        wait(lambda:not app.support_consent_busy and not app.support_upload.status()['enabled'])
        assert not (friends.path/SupportConsent.NAME).exists()
        stored_count=len(reports())
        capture(app,root/'ru-service-consent-withdrawn.png')
        app.close(True);wait(lambda:app.closed);app=None
        wait(lambda:owner_pid() is None,seconds=78)
        assert len(reports())==stored_count and ctl('show',unit,'-p','MainPID','--value').stdout.strip()=='0'
        assert all(hashlib.sha256((friends.path/name).read_bytes()).hexdigest()==expected for name,expected in key_hashes.items())
        assert not (root/'chat').exists()
        (root/'result.json').write_text(json.dumps(dict(status='PASS',actual_gtk=True,actual_private_dbus=True,
            actual_user_systemd=True,supervisor='Type=exec on private bus; production Type=dbus NOT_RUN',
            gtk_closed_upload=True,completion_cadence_seconds=reports()[1]['at']-reports()[0]['at'],
            reports_stored=stored_count,restart_preserved_identity_and_consent=True,stale_revision_rejected=True,
            revoked_without_chat_keyring=True,revoked_idle_exit=True,host_installation='NOT_RUN',
            vpn='SYNTHETIC',api='real local handlers via HTTP MockTransport; no external network',
            production_identity_and_policy_changed=False),indent=2)+'\n')
    finally:
        if app is not None and not app.closed:app.close(True);wait(lambda:app.closed)
        if monitor is not None:monitor.close()
        if unit_started:ctl('stop',unit)
        (root/'unit-after-stop.txt').write_text(ctl('show',unit,'-p','ActiveState','-p','MainPID').stdout)


if __name__=='__main__':
    main(Path(sys.argv[1]).resolve())
