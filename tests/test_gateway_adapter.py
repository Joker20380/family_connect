import json
from types import SimpleNamespace

import pytest

from control.product.gateway_adapter import DockerGateway
from device_identity.device import DeviceIdentity


@pytest.fixture
def adapter(tmp_path):
    state={'peers':{},'fail_set':False,'calls':[]}
    gateway={'public_key':DeviceIdentity.generate().wireguard_public_key,'port':51820}
    def run(args,**kwargs):
        assert kwargs['timeout']==3 and kwargs['capture_output']
        state['calls'].append(args)
        if args[1]=='inspect':return SimpleNamespace(stdout=json.dumps([{'Source':str(tmp_path),'Destination':'/keys'}]))
        cmd=args[3:]
        if cmd[0]=='cat':return SimpleNamespace(stdout='# family-connect-dynamic-peers-v1\n# family-connect-peer-sync-v1')
        if cmd[:3]==['wg','show','wg0']:
            if cmd[3]=='public-key':return SimpleNamespace(stdout=gateway['public_key'])
            if cmd[3]=='listen-port':return SimpleNamespace(stdout='51820')
            return SimpleNamespace(stdout='\n'.join(k+'\t'+','.join(v) for k,v in state['peers'].items()))
        if state['fail_set']:raise RuntimeError('wg unavailable')
        assert cmd[0]=='/usr/local/bin/family-connect-peer-sync'
        identity,key=cmd[1:]
        record=tmp_path/'peers'/f'product-{identity}.conf'
        if not record.exists():state['peers'].pop(key,None)
        else:state['peers'][key]=sorted(DockerGateway._parse(record.read_text())[1])
        return SimpleNamespace(stdout='')
    driver=DockerGateway(container='test-gateway',keys=tmp_path,run=run)
    device=DeviceIdentity.generate()
    return driver,state,device,gateway


def apply(fixture,present=True):
    driver,_,device,gateway=fixture
    driver.apply(device.reference,device.wireguard_public_key,['10.77.0.4/32'],present=present,gateway=gateway)


def test_idempotent_install_remove_and_preserve_unmanaged(adapter):
    driver,state,device,_=adapter
    other=DeviceIdentity.generate().wireguard_public_key
    state['peers'][other]=['10.77.0.3/32']
    apply(adapter);apply(adapter)
    file=driver.keys/'peers'/f'product-{device.reference}.conf'
    assert file.stat().st_mode&0o777==0o600
    apply(adapter,False);apply(adapter,False)
    assert not file.exists() and state['peers']=={other:['10.77.0.3/32']}


def test_install_failure_persists_for_retry(adapter):
    driver,state,device,_=adapter;state['fail_set']=True
    with pytest.raises(RuntimeError):apply(adapter)
    assert (driver.keys/'peers'/f'product-{device.reference}.conf').exists()
    state['fail_set']=False;apply(adapter)
    assert device.wireguard_public_key in state['peers']


def test_remove_failure_does_not_resurrect_after_restart(adapter):
    driver,state,device,_=adapter;apply(adapter);state['fail_set']=True
    with pytest.raises(RuntimeError):apply(adapter,False)
    assert not list((driver.keys/'peers').glob('*.conf'))
    assert device.wireguard_public_key in state['peers']
    state['fail_set']=False;apply(adapter,False)
    assert not state['peers']


@pytest.mark.parametrize('kind',['live_key','live_address','saved_address','static','symlink'])
def test_unmanaged_peers_and_unsafe_records_are_not_adopted(adapter,kind):
    driver,state,device,_=adapter
    other=DeviceIdentity.generate().wireguard_public_key
    if kind=='live_key':state['peers'][device.wireguard_public_key]=['10.77.0.4/32']
    elif kind=='live_address':state['peers'][other]=['10.77.0.0/24']
    elif kind=='static':
        file=driver.keys/'android.pub';file.write_text(device.wireguard_public_key);file.chmod(0o600)
    else:
        folder=driver.keys/'peers';folder.mkdir(mode=0o700)
        file=folder/'legacy.conf'
        if kind=='symlink':file.symlink_to('/etc/passwd')
        else:file.write_text(f'[Peer]\nPublicKey = {other}\nAllowedIPs = 10.77.0.4/32\n');file.chmod(0o600)
    with pytest.raises((ValueError,OSError)):apply(adapter)
    assert not any('/usr/local/bin/family-connect-peer-sync' in call[3:4] for call in state['calls'])


def test_gateway_identity_mismatch_does_not_mutate(adapter):
    driver,state,device,gateway=adapter
    with pytest.raises(ValueError):
        driver.apply(device.reference,device.wireguard_public_key,['10.77.0.4/32'],present=True,
                     gateway={**gateway,'public_key':DeviceIdentity.generate().wireguard_public_key})
    assert not any('/usr/local/bin/family-connect-peer-sync' in call[3:4] for call in state['calls'])


def test_revocation_removes_owned_key_even_after_live_route_drift(adapter):
    _,state,device,_=adapter
    apply(adapter)
    state['peers'][device.wireguard_public_key]=['10.77.0.9/32']
    apply(adapter,False)
    assert device.wireguard_public_key not in state['peers']
