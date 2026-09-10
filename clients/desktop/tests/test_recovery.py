from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).parents[1]))
import backend

@pytest.fixture
def policy():
    clock=[0.0];p=backend.RecoveryPolicy(lambda:clock[0]);p.arm('vpn')
    return p,clock

def test_two_failures_and_scoped_intent(policy):
    p,t=policy
    assert not p.due('vpn') and not p.due('other')
    t[0]=15;assert p.due('vpn')
    assert not p.observe(False)
    t[0]=30;assert p.observe(False)
    assert p.attempts==1

def test_transient_failure_does_not_switch(policy):
    p,_=policy
    assert not p.observe(False)
    assert not p.observe(True)
    assert not p.observe(False)

def test_attempt_budget_and_backoff(policy):
    p,t=policy
    p.observe(False)
    for index,delay in enumerate((15,30,60),1):
        assert p.observe(False);assert p.attempts==index
        p.recovered(False);assert p.next_check==t[0]+delay
        if index<3:
            assert not p.due('vpn');t[0]+=delay;assert p.due('vpn')
    assert p.exhausted and not p.due('vpn') and not p.observe(False)

def test_brief_success_does_not_erase_retry_budget(policy):
    p,t=policy;p.observe(False);p.observe(False);p.recovered(True)
    p.observe(True);t[0]=30;p.observe(True)
    assert p.attempts==1
    t[0]=60;p.observe(True);assert p.attempts==0

def test_stop_and_manual_retry(policy):
    p,t=policy;p.observe(False);p.stop();t[0]=100
    assert not p.due(None) and not p.due('vpn') and not p.observe(False)
    p.arm('new');assert p.attempts==0 and not p.exhausted

def test_second_independent_service_can_confirm_tunnel(monkeypatch):
    calls=[]
    def fake(*args,**kwargs):
        calls.append(args)
        if '1.1.1.1' in args[-1]:raise backend.BackendError('unavailable')
        return '185.251.89.19'
    monkeypatch.setattr(backend,'run',fake)
    backend.probe_interface('awg0','185.251.89.19')
    assert len(calls)==2
    assert all(c[c.index('--interface')+1]=='awg0' for c in calls)
    assert all(c[1]=='--disable' for c in calls)

def test_wrong_egress_and_timeouts_fail_closed(monkeypatch):
    monkeypatch.setattr(backend,'run',lambda *a,**k:'192.0.2.3')
    with pytest.raises(backend.BackendError):backend.probe_interface('awg0','185.251.89.19')
    def timeout(*args,**kwargs):raise backend.subprocess.TimeoutExpired('curl',5)
    monkeypatch.setattr(backend,'run',timeout)
    with pytest.raises(backend.BackendError):backend.probe_interface('awg0','185.251.89.19')

def test_recovery_disconnects_then_reconnects_paired_primary(monkeypatch):
    driver=backend.Linux();events=[]
    monkeypatch.setattr(driver,'_awg_records',lambda:{'awg':{'primary':'wg'}})
    monkeypatch.setattr(driver,'_nm_active',lambda x:False)
    monkeypatch.setattr(driver,'disconnect',lambda x:events.append(('down',x)))
    monkeypatch.setattr(driver,'connect',lambda x:events.append(('up',x)))
    monkeypatch.setattr(driver,'healthy',lambda x:True)
    driver.recover('awg')
    assert events==[('down','wg'),('up','wg')]

def test_auth_cancel_has_distinct_error(monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setattr(backend.subprocess,'run',lambda *a,**kw:SimpleNamespace(returncode=126,stdout=''))
    with pytest.raises(backend.AuthorizationError):backend.Linux()._awg('up','fcawg12345678')

def test_paired_awg_alias_tracks_recovered_wg(monkeypatch):
    driver=backend.Linux()
    monkeypatch.setattr(driver,'_awg_records',lambda:{'fcawg12345678':dict(primary='wg',endpoint='185.251.89.19')})
    monkeypatch.setattr(driver,'_nm_active',lambda ident:ident=='wg')
    monkeypatch.setattr(driver,'_probe',lambda *args:None)
    assert driver.active('fcawg12345678') and driver.healthy('fcawg12345678')
