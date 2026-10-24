import base64
from contextlib import contextmanager
import copy
import importlib.util
import json
import os
from pathlib import Path
import socket
import sys
import threading
import time
import tempfile

import pytest

import backend
from test_mesh_presentation import snapshot as mesh_snapshot

LINUX = Path(__file__).resolve().parents[2]/'linux'
sys.path.insert(0,str(LINUX))
import auto_ipc
import mesh_ipc
import auto_service


def material():
    def encoded(size):
        return base64.b64encode(bytes([7])*size).decode()
    return dict(identity=encoded(64),wireguard_private=encoded(32),wireguard_public=encoded(32),anchor=encoded(32),
                country='nl',profile='P1',normal_floors=[])


def state(name='DISCONNECTED', generation='', desired=False):
    return dict(schema=1,id=1,ok=True,state=name,generation=generation,desired_connected=desired,
                requested_profile='P1' if generation else '',reason='',controller=None,selected='')


@pytest.fixture
def driver(tmp_path,monkeypatch):
    monkeypatch.setattr(backend,'operation_directory',lambda:tmp_path/'operations')
    monkeypatch.setattr(backend,'AUTO_RUN',tmp_path/'ipc')
    monkeypatch.setattr(backend,'auto_component_present',lambda:True)
    monkeypatch.setattr(backend.LinuxTCP,'profiles',lambda self:[])
    monkeypatch.setattr(backend.LinuxTCP,'active',lambda self,ident:False)
    monkeypatch.setattr(backend.LinuxMesh,'mesh_status',lambda self:dict(state='DISCONNECTED',desired_connected=False))
    calls=[]
    class Client:
        protocol=auto_ipc
        value=state()
        fail_start=False
        fail_stop=False
        catalog=None
        def call(self,action,**kwargs):
            calls.append(action)
            if action=='start':
                assert backend._auto_receipt()==dict(schema=1,generation='',desired=True)
                self.protocol.selection(kwargs['selection'])
                if self.fail_start:
                    raise backend.BackendError('Synthetic unknown save')
                type(self).value=state('CONNECTING','a'*32,True)
            elif action=='stop':
                assert kwargs['generation']==self.value['generation']
                if self.fail_stop:
                    raise backend.BackendError('Synthetic IPC unavailable')
                type(self).value=state('DISCONNECTED',kwargs['generation'],False)
            elif action=='catalog':return copy.deepcopy(self.catalog)
            return copy.deepcopy(self.value)
    monkeypatch.setattr(backend,'AutoServiceClient',Client)
    def setup(self,action,generation=None):
        calls.append(('helper',action,generation))
        if action=='down':
            assert generation==Client.value['generation']
            Client.value=state('DISCONNECTED',generation,False)
    monkeypatch.setattr(backend.LinuxAuto,'_auto_setup',setup)
    return backend.LinuxAuto(),Client,calls,tmp_path


def test_start_uses_same_computer_material_and_durable_pending_receipt(driver):
    instance,client,calls,_=driver
    value=material()
    result=instance.start_auto(value)
    assert value=={} and result['generation']=='a'*32 and result['state']=='CONNECTING'
    assert calls==[('helper','up',None),'status','start']
    assert backend._auto_receipt()==dict(schema=1,generation='a'*32,desired=True)


def test_unknown_start_is_not_replayed_or_reported_disconnected(driver):
    instance,client,calls,_=driver
    client.fail_start=True
    value=material()
    with pytest.raises(backend.BackendError):instance.start_auto(value)
    assert value=={}
    assert instance.auto_status()['state']=='FAILED' and instance.auto_status()['desired_connected']
    assert calls.count('start')==1


def test_stop_uses_generation_fenced_ipc_without_another_admin_prompt(driver):
    instance,client,calls,_=driver
    instance.start_auto(material())
    result=instance.stop_auto('a'*32)
    assert result['state']=='DISCONNECTED' and not result['desired_connected']
    assert ('helper','down','a'*32) not in calls
    assert backend._auto_receipt()==dict(schema=1,generation='a'*32,desired=False)


def test_stale_stop_cannot_stop_new_session_or_request_helper_fallback(driver):
    instance,client,calls,_=driver
    instance.start_auto(material())
    with pytest.raises(backend.StaleConnection):instance.stop_auto('b'*32)
    assert 'stop' not in calls and not any(isinstance(call,tuple) and call[1]=='down' for call in calls)
    assert backend._auto_receipt()['desired']


def test_lost_service_stop_uses_only_exact_generation_helper_fallback(driver):
    instance,client,calls,_=driver
    instance.start_auto(material())
    client.fail_stop=True
    assert instance.stop_auto('a'*32)['state']=='DISCONNECTED'
    assert ('helper','down','a'*32) in calls


def test_root_catalog_read_is_authorized_and_cannot_refresh_during_active_auto(driver):
    instance,client,calls,_=driver
    assert instance.normal_catalog() is None
    assert calls==[('helper','up',None),'status','catalog']
    instance.start_auto(material())
    calls.clear()
    with pytest.raises(backend.BackendError,match='Disconnect Auto'):instance.normal_catalog()
    assert 'catalog' not in calls


def test_old_installation_without_auto_keeps_existing_normal_workflow(driver,monkeypatch):
    instance,client,calls,_=driver
    monkeypatch.setattr(backend,'auto_component_present',lambda:False)
    assert instance.normal_catalog() is None and calls==[]
    backend._auto_receipt(dict(schema=1,generation='a'*32,desired=True))
    with pytest.raises(backend.BackendError):instance.normal_catalog()


@pytest.mark.parametrize('failure',['signature-shape','country','extra'])
def test_bad_material_never_reaches_privileged_setup(driver,failure):
    instance,client,calls,_=driver
    value=material()
    if failure=='signature-shape':value['identity']='invalid'
    elif failure=='country':value['country']='invalid'
    else:value['command']='arbitrary'
    with pytest.raises(ValueError):instance.start_auto(value)
    assert value=={} and calls==[]


@pytest.mark.parametrize('kind',['mesh','normal'])
def test_existing_vpn_is_not_silently_stopped_to_start_auto(driver,monkeypatch,kind):
    instance,client,calls,_=driver
    if kind=='mesh':monkeypatch.setattr(backend.LinuxMesh,'mesh_status',lambda self:dict(desired_connected=True))
    else:
        monkeypatch.setattr(backend.LinuxTCP,'profiles',lambda self:[('fctcp12345678','existing')])
        monkeypatch.setattr(backend.LinuxTCP,'active',lambda self,ident:True)
    with pytest.raises(backend.BackendError):instance.start_auto(material())
    assert calls==[]


@pytest.mark.parametrize('action,ident,data', [('import',None,'secret'),('down','fcauto0',None),('up','a'*32,None),
    ('up','fcauto0','payload'),('down','a'*31,None),('down','../service',None)])
def test_authorization_session_rejects_unbounded_auto_operations(action,ident,data):
    with pytest.raises(ValueError):backend._session_request(dict(kind='auto',action=action,ident=ident,data=data))


def test_authorization_session_maps_only_fixed_helper_verbs():
    helper=backend._SESSION_HELPERS['mesh']
    assert backend._session_request(dict(kind='auto',action='up',ident='fcauto0',data=None))==([helper,'auto-up','fcauto0'],None)
    assert backend._session_request(dict(kind='auto',action='down',ident='a'*32,data=None))==([helper,'auto-down','a'*32],None)


def test_auto_receipt_survives_restart_without_private_material(driver):
    instance,client,calls,folder=driver
    instance.start_auto(material())
    restarted=backend.LinuxAuto()
    assert restarted.auto_status()['generation']=='a'*32
    path=folder/'operations/auto-session.json'
    assert path.stat().st_mode&0o777==0o600
    assert set(json.loads(path.read_text()))=={'schema','generation','desired'}


def test_component_requires_its_own_marker_and_matching_native_digest(tmp_path,monkeypatch):
    monkeypatch.setattr(backend,'MESH_ROOT',tmp_path)
    monkeypatch.setattr(backend,'AUTO_UNIT',tmp_path/'family-connect-auto@.service')
    monkeypatch.setattr(backend,'mesh_component_available',lambda:True)
    monkeypatch.setattr(backend,'_mesh_trusted',lambda path,directory=False:path.lstat())
    for name in backend.AUTO_FILES:(tmp_path/name).write_text('')
    backend.AUTO_UNIT.write_text('')
    (tmp_path/'capabilities.json').write_text(json.dumps(dict(source_digest='a'*64)))
    marker=dict(schema=1,service_protocol=1,catalog_protocol=1,source_digest='a'*64)
    (tmp_path/'auto-capabilities.json').write_text(json.dumps(marker))
    assert backend.auto_component_available()
    marker['source_digest']='b'*64
    (tmp_path/'auto-capabilities.json').write_text(json.dumps(marker))
    assert not backend.auto_component_available()
    (tmp_path/'auto-capabilities.json').unlink()
    assert backend.auto_component_present() and not backend.auto_component_available()


@pytest.mark.parametrize('action',['status','catalog'])
def test_real_unix_client_frames_and_isolated_protocol_loading(short_socket_path,monkeypatch,action):
    tmp_path=short_socket_path
    monkeypatch.setattr(backend,'MESH_ROOT',LINUX)
    monkeypatch.setattr(backend,'AUTO_RUN',tmp_path)
    monkeypatch.setattr(backend,'auto_component_available',lambda:True)
    monkeypatch.setattr(backend,'_mesh_trusted',lambda path,directory=False:path.lstat())
    tmp_path.chmod(0o711)
    before={name for name in sys.modules if name.startswith('family_connect_auto_protocol_')}
    client=backend.AutoServiceClient()
    assert {name for name in sys.modules if name.startswith('family_connect_auto_protocol_')}==before
    monkeypatch.setattr(client.protocol.ipc,'peer_uid',lambda connection:0)
    listener=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
    endpoint=tmp_path/(str(os.getuid())+'.sock')
    listener.bind(str(endpoint));endpoint.chmod(0o600);listener.listen(1);listener.settimeout(3)
    errors=[]
    def serve():
        try:
            connection,_=listener.accept()
            with connection:
                request=mesh_ipc.receive(connection.fileno(),32768,time.monotonic()+3)
                assert request==dict(schema=1,id=1,action=action)
                response=dict(schema=1,id=1,ok=True,catalog=None) if action=='catalog' else {key:value for key,value in state().items() if key!='selected'}
                mesh_ipc.send(connection.fileno(),response,mesh_ipc.MAX_REPLY,time.monotonic()+3)
        except Exception as error:errors.append(error)
    thread=threading.Thread(target=serve);thread.start()
    try:
        result=client.call(action)
        assert result is None if action=='catalog' else result['state']=='DISCONNECTED'
    finally:
        listener.close();thread.join(timeout=4)
    assert not thread.is_alive() and errors==[]


@pytest.fixture
def short_socket_path():
    with tempfile.TemporaryDirectory(prefix='fc-auto-',dir='/tmp') as directory:
        yield Path(directory)


@pytest.mark.parametrize('stale',[False,True])
def test_privileged_helper_holds_start_gate_and_checks_generation_before_stop(tmp_path,monkeypatch,stale):
    spec=importlib.util.spec_from_file_location('auto_helper_test',LINUX/'mesh-helper.py')
    helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    events=[]
    @contextmanager
    def gate():
        events.append('lock');yield;events.append('unlock')
    class Intent:
        def __init__(self,path,uid):assert uid==1000
        def read(self):return dict(generation=('b' if stale else 'a')*32)
        def revoke(self):events.append('revoke')
    import auto_intent
    monkeypatch.setattr(auto_intent,'AutoIntent',Intent)
    monkeypatch.setattr(auto_service,'command_gate',gate)
    monkeypatch.setattr(auto_service,'manage_unit',lambda action,uid:events.append((action,uid)))
    monkeypatch.setattr(os,'geteuid',lambda:0)
    monkeypatch.setenv('PKEXEC_UID','1000')
    monkeypatch.setattr(sys,'argv',['helper','auto-down','a'*32])
    if stale:
        with pytest.raises(ValueError,match='Stale'):helper.main()
        assert 'revoke' not in events and ('stop',1000) not in events
    else:
        helper.main()
        assert events==['lock','revoke',('stop',1000),'unlock']


def automatic(selected='restricted', name='CONNECTED'):
    return dict(state(name,'a'*32,True),selected=selected,controller=dict(
        policy=dict(selected=selected,events=[],events_dropped=0),
        platform=dict(interface='fcmesh0',attempt=1),mesh=dict(native=mesh_snapshot()['native'],attempt=1)))


@pytest.mark.parametrize('selected,label',[('restricted','MESH'),('awg','AWG 3.1'),('tcp','TCP REALITY')])
def test_auto_profile_only_reports_actual_mesh_negotiation(selected,label):
    view=backend.auto_presentation(automatic(selected))
    assert view['transport']==label and view['selected_profile']==('P1' if selected=='restricted' else None)
    assert view['effective']==('RS32/32 · CREDIT128' if selected=='restricted' else None)
    for name in ('CONNECTING','RESTORING','DISCONNECTING','FAILED'):
        view=backend.auto_presentation(automatic(selected,name))
        assert view['owned'] and not view['connected'] and view['effective'] is None and view['transport'] is None
    assert backend.auto_presentation(automatic(name='DISCONNECTING'))['state']=='STOPPING'


@pytest.mark.parametrize('selected',['restricted','awg','tcp'])
def test_auto_diagnostics_distinguish_selection_from_actual_transport(selected):
    diagnostics=backend.DesktopDiagnostics('0.2.11')
    diagnostics.sample('CONNECTED','auto','P1',automatic(selected))
    assert diagnostics.current['selected_transport']=='auto'
    assert diagnostics.current['actual_transport']==selected and diagnostics.current['vpn_capture_open']
    diagnostics.sample('RESTORING','auto','P1',automatic(selected,'RESTORING'))
    assert diagnostics.current['actual_transport']=='none' and not diagnostics.current['vpn_capture_open']


@pytest.mark.parametrize('mutation',['none','attempt','generation','interface','state'])
def test_ip_check_binds_actual_tunnel_and_rejects_reconnect(driver,monkeypatch,mutation):
    instance,client,calls,_folder=driver
    client.value=automatic()
    backend.AUTO_RUN.mkdir()
    (backend.AUTO_RUN/(str(os.getuid())+'.sock')).touch()
    observed=[]
    def run(*args,**kwargs):
        observed.append(args)
        assert args[args.index('--interface')+1]=='if!fcmesh0'
        if mutation=='attempt':client.value['controller']['platform']['attempt']+=1
        elif mutation=='generation':client.value['generation']='b'*32
        elif mutation=='interface':client.value['controller']['platform']['interface']='fcawg12345678'
        elif mutation=='state':client.value['state']='RESTORING'
        return 'ip=192.0.2.1\nloc=NL\n'
    monkeypatch.setattr(backend,'run',run)
    if mutation=='none':assert instance.check_auto_ip()=='IP: 192.0.2.1 · NL'
    else:
        with pytest.raises(backend.BackendError,match='changed'):instance.check_auto_ip()
    assert len(observed)==1


def test_ip_check_never_uses_underlay_without_ready_auto(driver,monkeypatch):
    instance,client,_calls,_folder=driver
    monkeypatch.setattr(backend,'run',lambda *args,**kwargs:pytest.fail('Unexpected network check'))
    with pytest.raises(backend.BackendError,match='ready system tunnel'):instance.check_auto_ip()
