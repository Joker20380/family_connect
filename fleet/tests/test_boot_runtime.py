import hashlib
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from fleet.contracts import canonical
from fleet.private_files import write_private
from fleet.runtime import boot_prepare, expiry_guard


@pytest.fixture
def installation(tmp_path):
    root=tmp_path/'root'
    bundle='gw-'+'a'*32
    instance='fleet-rehearsal-boot'
    path='/etc/family-connect/rehearsal/'+bundle+'/metadata.json'
    config=root/path.lstrip('/')
    state=root/'var/lib/family-connect-rehearsal'/instance
    for directory in (config.parent,state,root/'etc/sysctl.d',root/'opt/family-connect'):
        directory.mkdir(parents=True,mode=0o755)
    firewall=b'table inet family_connect_rehearsal {\n}\n'
    metadata=dict(bundle_id=bundle,instance_id=instance,material_expires_at=3000,
                  runtime_lifetime_seconds=900,files={'firewall.nft':hashlib.sha256(firewall).hexdigest()})
    raw=canonical(metadata)
    write_private(config,raw,mode=0o644)
    write_private(config.parent/'validated.json',canonical(dict(bundle_id=bundle,metadata_sha256=hashlib.sha256(raw).hexdigest())))
    write_private(config.parent/'firewall.nft',firewall)
    write_private(state/('network-'+bundle+'.json'),canonical(dict(sha256=hashlib.sha256(firewall).hexdigest())))
    write_private(root/'etc/sysctl.d/90-family-connect-rehearsal.conf',b'net.ipv4.ip_forward = 1\n',mode=0o644)
    (root/'opt/family-connect/current').symlink_to('releases/'+bundle)
    executor=SimpleNamespace(table=None,calls=[],forwarding=b'1\n',error=None)
    def run(argv,**kwargs):
        executor.calls.append((argv,kwargs.get('input')))
        if argv[0]=='sysctl':
            return SimpleNamespace(returncode=0,stdout=executor.forwarding,stderr=b'')
        if argv[:3]==['nft','-s','list']:
            if executor.error:
                return SimpleNamespace(returncode=2,stdout=b'',stderr=b'permission denied')
            return SimpleNamespace(returncode=0 if executor.table else 1,stdout=executor.table or b'',stderr=b'No such file or directory')
        if argv==['nft','-f','-']:
            executor.table=kwargs['input']
        else:
            assert argv==['nft','-c','-f','-']
        return SimpleNamespace(returncode=0,stdout=b'',stderr=b'')
    return root,path,config,metadata,executor,run


def test_boot_restores_only_owned_table_and_is_idempotent(installation):
    root,path,config,metadata,executor,run=installation
    boot_prepare.prepare(path,root=root,runner=run,now=lambda:1000)
    assert executor.table==(config.parent/'firewall.nft').read_bytes()
    assert sum(argv==['nft','-f','-'] for argv,unused in executor.calls)==1
    boot_prepare.prepare(path,root=root,runner=run,now=lambda:1000)
    assert sum(argv==['nft','-f','-'] for argv,unused in executor.calls)==1
    assert not any('flush' in argv or 'delete' in argv for argv,unused in executor.calls)


@pytest.mark.parametrize('attack',['table-drift','observe-error','forwarding','expired','metadata','firewall','symlink','hardlink','pointer'])
def test_boot_rejects_drift_without_network_mutation(installation,attack):
    root,path,config,metadata,executor,run=installation
    now=1000
    if attack=='table-drift':executor.table=b'unexpected table'
    elif attack=='observe-error':executor.error=True
    elif attack=='forwarding':executor.forwarding=b'0\n'
    elif attack=='expired':now=3001
    elif attack=='metadata':config.write_bytes(canonical(dict(metadata,instance_id='fleet-rehearsal-other')))
    elif attack=='firewall':(config.parent/'firewall.nft').write_bytes(b'flush ruleset')
    elif attack=='symlink':
        config.unlink();config.symlink_to('/not-read')
    elif attack=='hardlink':os.link(config,config.parent/'extra')
    elif attack=='pointer':
        current=root/'opt/family-connect/current';current.unlink();current.symlink_to('releases/gw-'+'b'*32)
    with pytest.raises((ValueError,FileNotFoundError)):
        boot_prepare.prepare(path,root=root,runner=run,now=lambda:now)
    assert not any(argv==['nft','-f','-'] for argv,unused in executor.calls)


@pytest.mark.parametrize('lifetime,deadline,allowed',[(900,3000,True),(900,2020,False),(None,3000,False),(14400,20000,False),(299,3000,False)])
def test_start_guard_reserves_launch_time_and_bounds_every_restart(monkeypatch,lifetime,deadline,allowed):
    monkeypatch.setattr(expiry_guard.sys,'argv',['expiry_guard.py','/etc/family-connect/rehearsal/gw-'+'a'*32+'/metadata.json'])
    monkeypatch.setattr(expiry_guard.time,'time',lambda:1000)
    monkeypatch.setattr(Path,'read_bytes',lambda self:canonical(dict(material_expires_at=deadline,runtime_lifetime_seconds=lifetime)))
    if allowed:
        expiry_guard.main()
        assert 1000+2+lifetime<deadline
    else:
        with pytest.raises(SystemExit):expiry_guard.main()
