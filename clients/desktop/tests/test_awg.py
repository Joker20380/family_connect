import importlib.util
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).parents[1]))
import backend
from profile_config import validate

PROFILE='''[Interface]
PrivateKey = AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=
Address = 10.78.0.2/32, fd78:92::2/128
DNS = 1.1.1.1
MTU = 1280
Jc = 4
Jmin = 40
Jmax = 100
S1 = 32
S2 = 64
S3 = 16
S4 = 8
H1 = 1000-1100
H2 = 2000-2100
H3 = 3000-3100
H4 = 4000-4100
I1 = <b 0xc000><r 24><t>
[Peer]
PublicKey = AQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQE=
Endpoint = 185.251.89.19:51821
AllowedIPs = 0.0.0.0/0, ::/0
PersistentKeepalive = 25
'''

def test_awg_roundtrip_and_legacy_rejection():
    assert validate(validate(PROFILE,allow_awg=True),allow_awg=True)==validate(PROFILE,allow_awg=True)
    with pytest.raises(ValueError):validate(PROFILE)

@pytest.mark.parametrize('old,new',[
    ('Jc = 4','Jc = 65535'),('Jmin = 40','Jmin = 101'),
    ('S3 = 16\n',''),('H2 = 2000-2100','H2 = 1050-2100'),
    ('H1 = 1000-1100','H1 = 4294967296'),('H1 = 1000-1100','H1 = 1'),
    ('I1 = <b 0xc000><r 24><t>','I1 = <r 1281>'),
    ('I1 = <b 0xc000><r 24><t>','I1 = <b 0xabc>'),
    ('I1 = <b 0xc000><r 24><t>','I1 = $(touch /tmp/unsafe)'),
    ('DNS = 1.1.1.1','DNS = 1.1.1.1\nPostUp = echo unsafe'),
    ('Jc = 4','Jc = 4\nSaveConfig = true'),
])
def test_rejects_unsafe_awg(old,new):
    with pytest.raises(ValueError):validate(PROFILE.replace(old,new),allow_awg=True)

@pytest.fixture
def linux(monkeypatch):
    driver=backend.Linux();events=[]
    monkeypatch.setattr(driver,'_awg_records',lambda:{'fcawg12345678':dict(primary='wg-id',endpoint='185.251.89.19')})
    monkeypatch.setattr(driver,'_nm_active',lambda _:True)
    monkeypatch.setattr(driver,'_awg',lambda action,ident:events.append(('awg',action,ident)))
    monkeypatch.setattr(backend,'run',lambda *args,**kw:events.append(args) or '')
    monkeypatch.setattr(backend.time,'sleep',lambda _:None)
    return driver,events

def test_working_wg_does_not_switch(linux,monkeypatch):
    driver,events=linux
    monkeypatch.setattr(driver,'_probe',lambda *args:None)
    driver.connect('wg-id')
    assert events==[('nmcli','connection','up','uuid','wg-id')]

def test_failed_wg_probes_switch_only_after_down(linux,monkeypatch):
    driver,events=linux;probes=[]
    def failed(*args):
        probes.append(args);raise backend.BackendError('failed')
    monkeypatch.setattr(driver,'_probe',failed)
    driver.connect('wg-id')
    assert len(probes)==2
    assert events==[('nmcli','connection','up','uuid','wg-id'),
        ('nmcli','connection','down','uuid','wg-id'),('awg','up','fcawg12345678')]

def test_failed_down_never_starts_second_tunnel(linux,monkeypatch):
    driver,events=linux
    def failed(*args,**kwargs):raise backend.BackendError('failed')
    monkeypatch.setattr(driver,'_probe',failed)
    monkeypatch.setattr(backend,'run',failed)
    with pytest.raises(backend.BackendError):driver.connect('wg-id')
    assert not events

def test_unpaired_wg_retains_original_behavior(linux,monkeypatch):
    driver,events=linux
    monkeypatch.setattr(driver,'_awg_records',lambda:{})
    driver.connect('wg-id')
    assert events==[('nmcli','connection','up','uuid','wg-id')]

def test_manual_awg_failure_restores_previously_active_wg(linux,monkeypatch):
    driver,events=linux
    def fail(*args):raise backend.BackendError('failed')
    monkeypatch.setattr(driver,'_awg',fail)
    with pytest.raises(backend.BackendError):driver.connect('fcawg12345678')
    assert events==[('nmcli','connection','down','uuid','wg-id'),
                    ('nmcli','connection','up','uuid','wg-id')]

def test_probe_cannot_use_default_route(linux,monkeypatch):
    driver,_=linux;calls=[]
    def fake(*args,**kwargs):
        calls.append(args)
        return 'wg-test' if args[0]=='nmcli' else 'ip=185.251.89.19\n'
    monkeypatch.setattr(backend,'run',fake)
    driver._probe('wg-id','185.251.89.19')
    assert calls[1][calls[1].index('--interface')+1]=='wg-test'
    with pytest.raises(backend.BackendError):driver._probe('wg-id','192.0.2.1')
