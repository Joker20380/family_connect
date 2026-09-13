"""Bounded real Amsterdam tunnel checks in an isolated Linux network namespace.

Root only. WG UDP socket is born in the original network namespace; all test
traffic/DNS is in the new namespace. No host default route or resolver changes.
Private configuration stays in --state, never printed or sent to the gateway.
"""
import argparse,json,os,pwd,re,subprocess,time
from pathlib import Path

NS='fc-ams-check';IFACE='fcamschk';HOST='186.246.45.246'

def call(args,*,check=True,timeout=25):
    return subprocess.run(args,text=True,capture_output=True,check=check,timeout=timeout)
def run(*args):return call(list(args)).stdout.strip()
def inside(*args,check=True,timeout=25):return call(['ip','netns','exec',NS,*args],check=check,timeout=timeout)
def snapshot():return {name:run(*args) for name,args in {
    'rules4':['ip','-4','rule','show'],'rules6':['ip','-6','rule','show'],
    'default4':['ip','-4','route','show','default'],'default6':['ip','-6','route','show','default']}.items()}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--state',type=Path,required=True);a=parser.parse_args()
    assert os.geteuid()==0
    state=a.state.resolve();owner=(state/'client.key').stat().st_uid;user=pwd.getpwuid(owner).pw_name
    wg=str(state/'wg');assert (state/'client-uapi.conf').is_file()
    assert call(['ip','link','show',IFACE],check=False).returncode!=0
    assert NS not in [line.split()[0] for line in run('ip','netns','list').splitlines()]
    dns_dir=Path('/etc/netns')/NS;assert not dns_dir.exists()
    baseline=snapshot();resolver=Path('/etc/resolv.conf').read_bytes()
    result=dict(host=HOST,namespace=NS,started_at=int(time.time()),tests=[],passed=False)
    stage='setup';created=False
    def https(label):
        r=inside('curl','-4','--interface',IFACE,'--fail','--silent','--show-error','--connect-timeout','5','--max-time','15','https://www.cloudflare.com/cdn-cgi/trace')
        values=dict(line.split('=',1) for line in r.stdout.splitlines() if '=' in line)
        assert values.get('ip')==HOST,'unexpected egress'
        result['tests'].append(dict(test=label,egress=values['ip'],country=values.get('loc'),passed=True))
    def connect():
        run('ip','link','add',IFACE,'type','wireguard')
        run(wg,'setconf',IFACE,str(state/'client-uapi.conf'))
        run('ip','link','set',IFACE,'netns',NS)
        inside('ip','link','set','lo','up');inside('ip','address','add','10.79.0.2/32','dev',IFACE)
        inside('ip','-6','address','add','fd79:92::2/128','dev',IFACE)
        inside('ip','link','set',IFACE,'mtu','1280','up')
        inside('ip','route','add','default','dev',IFACE);inside('ip','-6','route','add','default','dev',IFACE)
    try:
        run('ip','netns','add',NS);created=True;dns_dir.mkdir(parents=True);(dns_dir/'resolv.conf').write_text('nameserver 1.1.1.1\n')
        connect()
        stage='gateway_ping';ping=inside('ping','-n','-c','3','-W','3','10.79.0.1')
        result['tests'].append(dict(test=stage,summary=ping.stdout.splitlines()[-2:],passed=True))
        stage='dns';dns=inside('dig','@1.1.1.1','example.com','A','+time=3','+tries=1')
        assert 'status: NOERROR' in dns.stdout and 'ANSWER: 0' not in dns.stdout
        result['tests'].append(dict(test=stage,passed=True))
        stage='https';https(stage)
        stage='second_https';ip=inside('curl','-4','--interface',IFACE,'--fail','--silent','--show-error','--connect-timeout','5','--max-time','15','https://api.ipify.org').stdout.strip();assert ip==HOST
        result['tests'].append(dict(test=stage,egress=ip,passed=True))
        stage='bounded_download';speed=inside('curl','-4','--interface',IFACE,'--fail','--silent','--show-error','--connect-timeout','5','--max-time','20','--output','/dev/null','--write-out','%{http_code} %{size_download} %{speed_download} %{time_total}','https://speed.cloudflare.com/__down?bytes=1048576')
        code,size,bps,elapsed=speed.stdout.split();assert code=='200' and int(size)==1048576
        result['tests'].append(dict(test=stage,bytes=int(size),bytes_per_second=float(bps),seconds=float(elapsed),passed=True))
        stage='private_network_block';blocked=inside('curl','-4','--interface',IFACE,'--silent','--connect-timeout','2','--max-time','3','http://10.0.0.1',check=False)
        assert blocked.returncode!=0;result['tests'].append(dict(test=stage,passed=True))
        stage='ipv6_block';blocked=inside('ping','-6','-n','-c','1','-W','2','2606:4700:4700::1111',check=False)
        assert blocked.returncode!=0;result['tests'].append(dict(test=stage,passed=True))
        stage='server_restart'
        call(['runuser','-u',user,'--','/tmp/fc-amsterdam-ssh','systemctl restart wg-quick@fcams.service && systemctl is-active wg-quick@fcams.service'],timeout=30)
        result['server_restart_command_succeeded']=True
        stage='post_restart_readiness';start=time.monotonic()
        while time.monotonic()-start<35:
            ready=inside('ping','-n','-c','1','-W','1','10.79.0.1',check=False,timeout=3)
            if ready.returncode==0:break
            time.sleep(.5)
        else:raise TimeoutError('WireGuard did not recover within 35s')
        result['post_restart_readiness_seconds']=round(time.monotonic()-start,3)
        stage='https_after_server_restart'
        # Application HTTP budgets stay unchanged after bounded tunnel readiness.
        for attempt in range(3):
            try:https('https_after_server_restart');break
            except (subprocess.CalledProcessError,AssertionError):
                if attempt==2:raise
                time.sleep(1)
        stage='client_reconnect';inside('ip','link','del',IFACE);connect()
        start=time.monotonic()
        while time.monotonic()-start<35:
            ready=inside('ping','-n','-c','1','-W','1','10.79.0.1',check=False,timeout=3)
            if ready.returncode==0:break
            time.sleep(.5)
        else:raise TimeoutError('Client reconnect did not become ready within 35s')
        result['client_reconnect_readiness_seconds']=round(time.monotonic()-start,3)
        stage='https_after_client_reconnect';https(stage)
        handshakes=inside(wg,'show',IFACE,'latest-handshakes').stdout.splitlines();assert len(handshakes)==1 and int(handshakes[0].split()[1])>0
        result['recent_handshake']=int(handshakes[0].split()[1]);result['passed']=True
    except Exception as e:
        result['error']=dict(stage=stage,type=type(e).__name__)
        if isinstance(e,subprocess.CalledProcessError) and stage!='setup':
            result['error']['exit_code']=e.returncode
            result['error']['detail']=re.sub(r'[A-Za-z0-9+/=_-]{40,}','[redacted]',e.stderr or '')[-500:]
    finally:
        if created:call(['ip','netns','del',NS],check=False)
        call(['ip','link','del',IFACE],check=False)
        if dns_dir.exists():
            (dns_dir/'resolv.conf').unlink(missing_ok=True);dns_dir.rmdir()
        result['host_routes_rules_unchanged']=snapshot()==baseline
        result['host_resolver_unchanged']=Path('/etc/resolv.conf').read_bytes()==resolver
        result['namespace_removed']=NS not in [line.split()[0] for line in run('ip','netns','list').splitlines()]
        result['interface_removed']=call(['ip','link','show',IFACE],check=False).returncode!=0
        result['finished_at']=int(time.time())
        result['passed'] &= all(result[k] for k in ('host_routes_rules_unchanged','host_resolver_unchanged','namespace_removed','interface_removed'))
        path=state/'result.json';path.write_text(json.dumps(result,indent=2)+'\n');os.chown(path,owner,-1)
        print(json.dumps(result))
    return 0 if result['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
