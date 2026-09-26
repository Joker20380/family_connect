"""Opt-in Docker VPN/SSH acceptance; no published ports or host network changes."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import secrets
import subprocess
import time

IMAGE='family-connect-fleet-native:accept'
INNER='/app/pilot/fleet-native/accept.py'


def run(*args, data=None, ok=True):
    p=subprocess.run(args,input=data,capture_output=True,timeout=45)
    if ok and p.returncode:
        raise RuntimeError('native test command failed: '+' '.join(args[:4]))
    return p


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args()
    results=[]
    versions={}
    started=datetime.now(timezone.utc).isoformat()
    for mode in ('wg','awg2','awg31'):
        prefix='fc-fleet-native-'+secrets.token_hex(4)
        server,client=prefix+'-server',prefix+'-client'
        containers=[]
        run('docker','network','create','--internal',prefix)
        try:
            for name in (server,client):
                run('docker','run','-d','--name',name,'--network',prefix,
                    '--cap-add','NET_ADMIN','--device','/dev/net/tun',IMAGE)
                containers.append(name)
            run('docker','exec',server,'python',INNER,'setup',mode)
            address=json.loads(run('docker','inspect',server).stdout)[0]['NetworkSettings']['Networks'][prefix]['IPAddress']
            # Ephemeral test secrets remain in memory/container storage only.
            config=run('docker','exec',server,'cat','/run/fleet-test/client.conf').stdout.replace(b'SERVER',address.encode())
            run('docker','exec','-i',client,'python','-c',
                "import os,sys;f=os.open('/run/client.conf',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.write(f,sys.stdin.buffer.read());os.close(f)",data=config)
            cli='/usr/bin/wg' if mode=='wg' else '/opt/'+mode+'/awg'
            versions[mode]={'cli':run('docker','exec',server,cli,'--version').stdout.decode().strip()}
            if mode!='wg':
                versions[mode]['engine']=run('docker','exec',server,'/opt/'+mode+'/amneziawg-go','--version').stdout.decode().splitlines()[0]
            if mode=='wg':
                versions['kernel']=run('docker','exec',server,'uname','-r').stdout.decode().strip()
                versions['openssh']=run('docker','exec',server,'ssh','-V').stderr.decode().strip()
            if mode=='wg':run('docker','exec',client,'ip','link','add','fc0','type','wireguard')
            else:run('docker','exec',client,'/opt/'+mode+'/amneziawg-go','fc0')
            run('docker','exec',client,cli,'setconf','fc0','/run/client.conf')
            run('docker','exec',client,'ip','address','add','10.87.0.2/24','dev','fc0')
            run('docker','exec',client,'ip','link','set','fc0','up')
            for stage in ('admit','restart','remove','reuse'):
                result=json.loads(run('docker','exec',server,'python',INNER,stage).stdout)
                if stage in ('restart','reuse'):
                    # Request a fresh handshake explicitly. Automatic client
                    # recovery timing belongs to the separate stage 6 gate.
                    public=run('docker','exec',client,cli,'show','fc0','peers').stdout.decode().strip()
                    run('docker','exec',client,cli,'set','fc0','peer',public,'remove')
                    run('docker','exec',client,cli,'setconf','fc0','/run/client.conf')
                ping=run('docker','exec',client,'ping','-I','fc0','-c','2','-W','2','10.87.0.1',ok=False)
                assert (ping.returncode==0)==(stage!='remove'),(mode,stage,'traffic mismatch')
                if stage!='remove':
                    stamps=run('docker','exec',client,cli,'show','fc0','latest-handshakes').stdout.decode().split()
                    assert len(stamps)==2 and 0<=time.time()-int(stamps[1])<60
                results.append(dict(mode=mode,**result,traffic_verified=True))
                print(f'PASS {mode}: {stage}, native VPN traffic',flush=True)
        finally:
            failures=[]
            for name in reversed(containers):
                if run('docker','rm','-f',name,ok=False).returncode:failures.append(name)
            if run('docker','network','rm',prefix,ok=False).returncode:failures.append(prefix)
            if failures:raise RuntimeError('test resource cleanup failed: '+','.join(failures))
    image_id=run('docker','image','inspect','--format','{{.Id}}',IMAGE).stdout.decode().strip()
    root=Path(__file__).resolve().parents[1]
    sources=['scripts/test_fleet_native.py','pilot/fleet-native/accept.py','pilot/fleet-native/Dockerfile',
             'scripts/fleet_agent.py','control/fleet_gateway.py','control/fleet_wg.py','control/fleet_ssh.py','control/fleet_process.py']
    args.report.write_text(json.dumps(dict(started_utc=started,finished_utc=datetime.now(timezone.utc).isoformat(),
        image=image_id,versions=versions,results=results,cleanup=True,
        sha256={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in sources}),indent=2)+'\n')
    print('PASS: all isolated containers/networks removed; report saved',flush=True)


if __name__=='__main__':main()
