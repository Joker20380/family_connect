import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).parents[1]))
import backend
from profile_config import parse_tcp,tcp_config

# Public, synthetic fixture; never a live credential.
PROFILE=dict(type='vless-reality-v1',server='192.0.2.1',port=443,
    id='00000000-0000-4000-8000-000000000001',public_key='AQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQE',
    server_name='www.example.com',short_id='0123456789abcdef')

@pytest.mark.parametrize('key,value',[
    ('port',True),('port',0),('port',65536),('port','443'),('server','example.com'),
    ('server','127.0.0.1;id'),('server_name','example.com/path'),('server_name','$(id).com'),
    ('public_key','a'*42),('public_key','A'*42+'B'),('short_id','abc'),('id','not-a-uuid'),
    ('type','vless'),('post_up','id'),('log',{'access':'/etc/passwd'})])
def test_tcp_rejects_unsafe_profile(key,value):
    with pytest.raises(ValueError):parse_tcp(json.dumps({**PROFILE,key:value}))

def test_duplicate_keys_rejected():
    with pytest.raises(ValueError):parse_tcp(json.dumps(PROFILE)[:-1]+',"port":443}')

def test_generated_config_cannot_bypass_tunnel():
    config=tcp_config(PROFILE,'fctcp12345678')
    assert len(config['outbounds'])==1
    assert config['outbounds'][0]['protocol']=='vless'
    assert config['outbounds'][0]['streamSettings']['sockopt']['mark']==64630
    assert 'autoSystemRoutingTable' not in config['inbounds'][0]['settings']
    with pytest.raises(ValueError):tcp_config(PROFILE,'../../unsafe')

@pytest.fixture
def chain(monkeypatch):
    driver=backend.LinuxTCP();events=[];live=set()
    monkeypatch.setattr(driver,'_awg_records',lambda:{'fcawg12345678':dict(primary='wg-id',endpoint='192.0.2.1')})
    monkeypatch.setattr(driver,'_tcp_records',lambda:{'fctcp12345678':dict(primary='wg-id',endpoint='192.0.2.1')})
    monkeypatch.setattr(driver,'_live',lambda item:item[0] in live)
    monkeypatch.setattr(driver,'_nm_active',lambda _: 'wg' in live)
    def operation(kind,action):
        events.append((kind,action))
        if action=='up':live.add(kind)
        else:live.discard(kind)
    monkeypatch.setattr(backend,'run',lambda *args,**kw:operation('wg',args[2]))
    monkeypatch.setattr(driver,'_awg',lambda action,ident:operation('awg',action))
    monkeypatch.setattr(driver,'_tcp',lambda action,ident:operation('tcp',action))
    def check(item):
        if item[0]!='tcp':raise backend.BackendError('blocked')
    monkeypatch.setattr(driver,'_check',check)
    return driver,events,live

def test_both_udp_blocked_reach_tcp_after_cleanup(chain):
    driver,events,live=chain
    driver.connect('wg-id')
    assert events==[('wg','up'),('wg','down'),('awg','up'),('awg','down'),('tcp','up')]
    assert live=={'tcp'} and driver.healthy('wg-id')
    driver.disconnect('fcawg12345678')
    assert not live

def test_established_awg_failure_tries_tcp_first(chain):
    driver,events,live=chain;live.add('awg')
    driver.recover('wg-id')
    assert events==[('awg','down'),('tcp','up')]

def test_cancelled_authorization_never_tries_next_transport(chain,monkeypatch):
    driver,events,live=chain
    def denied(*args):raise backend.AuthorizationError('cancelled')
    monkeypatch.setattr(driver,'_awg',denied)
    with pytest.raises(backend.AuthorizationError):driver.connect('wg-id')
    assert events==[('wg','up'),('wg','down')]

def test_failed_cleanup_never_starts_next_transport(chain,monkeypatch):
    driver,events,live=chain
    def failed(*args):raise backend.BackendError('cleanup failed')
    monkeypatch.setattr(driver,'_stop',failed)
    with pytest.raises(backend.BackendError):driver.connect('wg-id')
    assert events==[('wg','up')]

def test_explicit_tcp_skips_udp(chain):
    driver,events,live=chain;driver.connect('fctcp12345678')
    assert events==[('tcp','up')]

def test_explicit_tcp_replaces_healthy_wg(chain,monkeypatch):
    driver,events,live=chain;live.add('wg')
    monkeypatch.setattr(driver,'_check',lambda _:None)
    driver.connect('fctcp12345678')
    assert events==[('wg','down'),('tcp','up')]


def test_wg_health_uses_paired_awg_endpoint_when_tcp_gateway_differs(chain,monkeypatch):
    driver,_,_=chain
    monkeypatch.setattr(driver,'_tcp_records',lambda:{'fctcp12345678':dict(primary='wg-id',endpoint='198.51.100.2')})
    assert driver._chain('wg-id')==[
        ('wg','wg-id','192.0.2.1'),('awg','fcawg12345678','192.0.2.1'),
        ('tcp','fctcp12345678','198.51.100.2')]


def test_no_tcp_profiles_preserves_wg_awg_backend(monkeypatch):
    driver=backend.LinuxTCP();calls=[]
    monkeypatch.setattr(driver,'_tcp_records',lambda:{})
    monkeypatch.setattr(driver,'_awg_records',lambda:{})
    monkeypatch.setattr(backend.Linux,'connect',lambda self,ident:calls.append(ident))
    driver.connect('wg-id')
    assert calls==['wg-id']

@pytest.mark.parametrize('systemctl_body',['echo active-tcp.service','exit 1'])
def test_installer_refuses_active_or_unreadable_service_state(tmp_path,systemctl_body):
    import os,stat,subprocess
    device=Path('/dev/net/tun')
    if not device.exists() or not stat.S_ISCHR(device.stat().st_mode):
        pytest.skip('Host has no TUN device for installer preflight')
    commands=tmp_path/'bin';commands.mkdir();marker=tmp_path/'mutated'
    for name,body in {'id':'echo 0','systemctl':systemctl_body,'resolvectl':'exit 0',
                      'curl':'exit 0','install':'touch "$INSTALL_MARKER"; exit 99'}.items():
        f=commands/name;f.write_text('#!/bin/sh\n'+body+'\n');f.chmod(0o755)
    script=Path(__file__).resolve().parents[2]/'linux/install-tcp.sh'
    result=subprocess.run(['sh',str(script),str(tmp_path),str(tmp_path)],capture_output=True,
        env={**os.environ,'PATH':str(commands)+':'+os.environ['PATH'],'INSTALL_MARKER':str(marker)})
    assert result.returncode!=0 and not marker.exists()
