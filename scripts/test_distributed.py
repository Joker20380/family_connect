"""Run from the operator laptop; SSH credentials stay on that laptop."""
import json
import shlex
import subprocess
import time
from pathlib import Path

PRIMARY='root@185.251.89.19'
REMOTE='appuser@186.246.51.201'
PC=['docker','compose','-f','/opt/apps/family_connect-data/compose.data.yaml',
    '-f','/opt/apps/family_connect-data/compose.distributed.yaml']
RC=['docker','compose','-f','/opt/apps/family_connect-relay/compose.site-remote.yaml']
OUT=Path('artifacts/distributed')
SIZE=8*1024*1024


def command(host, args, check=True, timeout=45):
    return subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10',host,shlex.join(args)],
                          capture_output=True,text=True,check=check,timeout=timeout)


def primary(*args, **kw): return command(PRIMARY,[*PC,*args],**kw)
def remote(*args, **kw): return command(REMOTE,[*RC,*args],**kw)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    process=None
    try:
        remote('up','-d','router','relay','routes',timeout=90)
        primary('rm','-s','-f','client-wg','client',timeout=60)
        primary('up','-d','--no-build','client','client-wg',timeout=90)
        for attempt in range(12):
            trace=primary('exec','-T','client-wg','curl','-4','-fsS','--max-time','5',
                'https://www.cloudflare.com/cdn-cgi/trace',check=False)
            if trace.returncode==0: break
            time.sleep(1)
        else: raise RuntimeError('no VPN connectivity')
        values=dict(line.split('=',1) for line in trace.stdout.splitlines() if '=' in line)
        if values.get('ip')!='185.251.89.19': raise RuntimeError('wrong egress')
        logs=primary('logs','--no-color','client').stdout
        if logs.count('packet tunnel ready; inner_quic_connections=1')!=1 or 'authenticated relay path changed' in logs:
            raise RuntimeError('unexpected initial path/session')
        transfers=remote('exec','-T','router','wg','show','fcsite0','transfer').stdout.split()
        before=sum(map(int,transfers[1:]))
        print('HTTPS transfer starts through remote relay',flush=True)
        with (OUT/'download.json').open('w') as out, (OUT/'download.stderr').open('w') as err:
            args=[*PC,'exec','-T','client-wg','curl','-4','-fsS','--max-time','150','--limit-rate','256k',
                '--output','/tmp/fc-distributed.bin','--write-out','%{json}',
                f'https://speed.cloudflare.com/__down?bytes={SIZE}']
            process=subprocess.Popen(['ssh',PRIMARY,shlex.join(args)],stdout=out,stderr=err)
            for _ in range(30):
                if process.poll() is not None: raise RuntimeError('transfer ended before fault')
                stat=primary('exec','-T','client-wg','stat','-c','%s','/tmp/fc-distributed.bin',check=False)
                partial=int(stat.stdout.strip() or 0)
                if partial>=256*1024: break
                time.sleep(0.5)
            if not 0<partial<SIZE: raise RuntimeError('missing partial transfer')
            transfers=remote('exec','-T','router','wg','show','fcsite0','transfer').stdout.split()
            delta=sum(map(int,transfers[1:]))-before
            if delta<partial: raise RuntimeError('download did not traverse remote site')
            if 'authenticated relay path changed' in primary('logs','--no-color','client').stdout:
                raise RuntimeError('path changed before injected fault')
            print('Stopping both remote relay and site router',flush=True)
            remote('stop','-t','1','relay','router',timeout=45)
            if process.wait(timeout=160)!=0: raise RuntimeError('download failed after remote-site loss')
        result=json.loads((OUT/'download.json').read_text())
        logs=primary('logs','--no-color','client').stdout
        switches=logs.count('authenticated relay path changed')
        if result['http_code']!=200 or result['size_download']!=SIZE or result['num_connects']!=1:
            raise RuntimeError('unexpected HTTPS result')
        if switches<1 or logs.count('packet tunnel ready; inner_quic_connections=1')!=1:
            raise RuntimeError('missing switch or tunnel recreated')
        digest=primary('exec','-T','client-wg','sha256sum','/tmp/fc-distributed.bin').stdout.split()[0]
        (OUT/'client.log').write_text(logs)
        report={'gateway_ip':values['ip'],'gateway_country':values.get('loc'),
            'remote_host':'186.246.51.201','bytes':SIZE,'bytes_before_remote_stop':partial,
            'remote_site_transfer_delta':delta,'seconds':result['time_total'],
            'https_connections':1,'inner_quic_connections':1,'relay_switches':switches,
            'sha256_observed':digest,'fault':'stop remote relay AND site-router containers',
            'underlay':'operator WireGuard site link over public IPv4',
            'scope':'two VPS; client namespace and gateway on primary VPS'}
        (OUT/'result.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report,indent=2),flush=True)
    finally:
        if process is not None and process.poll() is None:
            process.terminate(); process.wait(timeout=10)
        primary('rm','-s','-f','client-wg','client',timeout=60)
        remote('up','-d','router','relay','routes',timeout=90)


if __name__=='__main__': main()
