"""Install reviewed helper update; test loss of an established WG session."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import argparse


def arguments():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--binaries',type=Path,required=True)
    parser.add_argument('--identity',required=True)
    parser.add_argument('--result',type=Path,required=True)
    return parser.parse_args()

def main():
    assert os.geteuid()==0
    args=arguments()
    import re
    assert re.fullmatch(r'fcawg[0-9a-f]{8}',args.identity)
    assert not args.result.exists(), 'Use a fresh result path'
    source=args.source.resolve()
    sys.path.insert(0,str(source/'clients/desktop'))
    import backend
    ident=args.identity
    installed=json.loads((Path('/etc/family-connect/awg')/(ident+'.json')).read_text())
    primary=installed['primary']
    assert primary, 'The AWG profile must be paired with an existing WG UUID' 
    class RootTest(backend.Linux):
        def _awg_records(self):return {ident:json.loads((self.awg_root/(ident+'.json')).read_text())}
        def _awg(self,action,ident=None,data=None):return backend.run(self.awg_helper,action,ident,timeout=60)
    driver=RootTest()
    assert not driver.active(primary), 'Existing user VPN active; leave it untouched'
    backup='/usr/local/lib/family-connect-awg-before-recovery-'+str(int(time.time()))
    shutil.copytree('/usr/local/lib/family-connect-awg',backup)
    backend.run('sh',str(source/'clients/linux/install-awg.sh'),str(source),str(args.binaries.resolve()))
    table='fc_recovery_accept_'+str(os.getpid());created=False
    result=dict(helper_backup=backup)
    try:
        driver.connect(primary)
        assert driver._nm_active(primary) and driver.healthy(primary)
        print('Established WG is healthy. Blocking only its endpoint for the recovery test.',flush=True)
        policy=backend.RecoveryPolicy();policy.arm(primary)
        backend.run('nft','add','table','inet',table);created=True
        backend.run('nft','add','chain','inet',table,'output','{ type filter hook output priority 0; policy accept; }')
        backend.run('nft','add','rule','inet',table,'output','ip','daddr','185.251.89.19','udp','dport','51820','drop')
        start=time.monotonic();checks=0
        while time.monotonic()-start<100:
            if not policy.due(primary):time.sleep(.2);continue
            healthy=driver.healthy(primary);checks+=1
            if policy.observe(healthy):
                driver.recover(primary);policy.recovered(True);break
        else:raise RuntimeError('Recovery deadline exceeded')
        assert checks==2 and Path('/sys/class/net',ident).exists() and not driver._nm_active(primary)
        result.update(established_wg_recovered=True,failed_health_cycles=checks,
                      recovery_seconds=round(time.monotonic()-start,2))
        # Health monitoring actually runs as the unprivileged desktop user.
        code="import sys;sys.path.insert(0,"+repr(str(source/'clients/desktop'))+");from backend import Linux;assert Linux().healthy("+repr(primary)+")"
        import pwd
        owner=pwd.getpwuid(installed['owner']).pw_name
        backend.run('runuser','-u',owner,'--','python3','-c',code)
        result['unprivileged_health_probe']=True
        driver.disconnect(primary);policy.stop()
        assert not driver.active(primary) and not policy.due(primary)
        result['explicit_disconnect_stops_recovery']=True
        result['passed']=True
    finally:
        try:driver.disconnect(primary)
        finally:
            if created:backend.run('nft','delete','table','inet',table)
        result['test_firewall_and_tunnels_removed']=not driver.active(primary)
        path=args.result
        fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o644)
        with os.fdopen(fd,'w') as f:json.dump(result,f,indent=2)
    print(json.dumps(result),flush=True)

if __name__=='__main__':main()
