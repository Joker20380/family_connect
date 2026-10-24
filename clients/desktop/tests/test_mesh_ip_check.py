import pytest

import backend


def test_mesh_ip_check_is_fixed_bounded_and_tun_bound(monkeypatch):
    driver=backend.LinuxMesh()
    monkeypatch.setattr(driver,'mesh_status',lambda:dict(state='CONNECTED',attempt=1))
    def run(*args,timeout):
        assert args == ('/usr/bin/curl','--disable','--noproxy','*','--interface','if!fcmesh0',
                        '--fail','--silent','--connect-timeout','3','--max-time','8','--max-filesize',
                        '4096','https://1.1.1.1/cdn-cgi/trace')
        assert timeout==9
        return 'ip=203.0.113.7\nloc=NL\nprivate=not echoed'
    monkeypatch.setattr(backend,'run',run)
    assert driver.check_mesh_ip()=='IP: 203.0.113.7 · NL'


@pytest.mark.parametrize('state,attempt', [('DISCONNECTED',1),('RESTORING',1),('CONNECTED',2)])
def test_mesh_ip_check_rejects_session_change(monkeypatch,state,attempt):
    observations=iter([dict(state='CONNECTED',attempt=1),dict(state=state,attempt=attempt)])
    driver=backend.LinuxMesh()
    monkeypatch.setattr(driver,'mesh_status',lambda:next(observations))
    monkeypatch.setattr(backend,'run',lambda *args,**kwargs:'ip=203.0.113.7\nloc=NL')
    with pytest.raises(backend.BackendError,match='session changed'):driver.check_mesh_ip()


def test_mesh_ip_check_never_uses_underlay_when_interface_missing(monkeypatch):
    driver=backend.LinuxMesh();calls=[]
    monkeypatch.setattr(driver,'mesh_status',lambda:dict(state='CONNECTED',attempt=1))
    def fail(*args,**kwargs):
        calls.append(args)
        raise backend.BackendError('Interface missing')
    monkeypatch.setattr(backend,'run',fail)
    with pytest.raises(backend.BackendError,match='Interface missing'):driver.check_mesh_ip()
    assert len(calls)==1
