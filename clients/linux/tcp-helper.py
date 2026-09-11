#!/usr/bin/python3 -I
"""Strict root broker and systemd-supervised TUN runtime for the Linux TCP pilot."""
import fcntl
import json
import os
from pathlib import Path
import re
import secrets
import signal
import stat
import subprocess
import sys
import time
import uuid
import ipaddress

sys.path.insert(0,str(Path(__file__).resolve().parent))
from profile_config import parse_tcp, tcp_config, MAX_PROFILE
from backend import probe_interface

ROOT=Path('/etc/family-connect/tcp')
BIN=Path('/usr/local/lib/family-connect-tcp')
RUN=Path('/run/family-connect-tcp')
ENV={'PATH':'/usr/sbin:/usr/bin:/sbin:/bin','LANG':'C','HOME':'/root'}
TABLE='64630'
PRIORITY='10630'
ROUTE_PRIORITIES={10627,10628,10629,10630}

def routing_rules(endpoint):
    endpoint=str(ipaddress.IPv4Address(endpoint))+'/32'
    # Preserve kernel-generated gateway packets even when they lack SO_MARK.
    # If main has no gateway route, prohibit fall-through into our own tunnel.
    return [('-4',('priority','10627','to',endpoint,'lookup','main')),
            ('-4',('priority','10628','to',endpoint,'prohibit'))]+[
        (family,rule) for family in ('-4','-6') for rule in (
            ('priority','10629','lookup','main','suppress_prefixlength','0'),
            ('priority',PRIORITY,'not','fwmark',TABLE,'lookup',TABLE))]

def check_routing_available():
    for family in ('-4','-6'):
        rules=json.loads(command('ip','-j',family,'rule','show').stdout)
        if any(r.get('priority') in ROUTE_PRIORITIES for r in rules):
            raise ValueError('TCP route priority occupied')
        routes=json.loads(command('ip','-j',family,'route','show','table','all').stdout)
        if any(str(r.get('table'))==TABLE for r in routes):
            raise ValueError('TCP route table occupied')

def install_routes(ident,endpoint):
    for family in ('-4','-6'):
        command('ip',family,'route','add','default','dev',ident,'table',TABLE)
    for family,rule in routing_rules(endpoint):command('ip',family,'rule','add',*rule)

def remove_routes(ident,endpoint=None):
    # Legacy markers own only the original two rules.
    rules=routing_rules(endpoint) if endpoint else [
        (family,('priority',PRIORITY,'not','fwmark',TABLE,'lookup',TABLE)) for family in ('-4','-6')]
    for family,rule in reversed(rules):command('ip',family,'rule','del',*rule,check=False)
    for family in ('-4','-6'):
        command('ip',family,'route','del','default','dev',ident,'table',TABLE,check=False)
    # Retain the ownership marker if cleanup failed, allowing another cleanup attempt.
    owned=ROUTE_PRIORITIES if endpoint else {int(PRIORITY)}
    for family in ('-4','-6'):
        if any(r.get('priority') in owned for r in json.loads(command('ip','-j',family,'rule','show').stdout)):
            raise RuntimeError('TCP rules remain; cleanup must be retried')
        routes=json.loads(command('ip','-j',family,'route','show','table','all').stdout)
        if any(str(r.get('table'))==TABLE and r.get('dev')==ident and r.get('dst')=='default' for r in routes):
            raise RuntimeError('TCP route remains; cleanup must be retried')

def command(*args,check=True):
    p=subprocess.run(args,capture_output=True,text=True,env=ENV,timeout=30)
    if check and p.returncode:raise RuntimeError('TCP system operation failed: '+Path(args[0]).name+'; exit='+str(p.returncode))
    return p

def read(path,private=False):
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        s=os.fstat(fd)
        if not stat.S_ISREG(s.st_mode) or s.st_uid!=0 or s.st_nlink!=1 or stat.S_IMODE(s.st_mode)!=(0o600 if private else 0o644):
            raise ValueError('Unsafe TCP state')
        raw=os.read(fd,MAX_PROFILE+1)
        if len(raw)>MAX_PROFILE:raise ValueError('Oversized TCP state')
        return raw.decode()
    finally:os.close(fd)

def write(path,data,mode):
    temporary=path.with_name('.'+secrets.token_hex(16))
    fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,mode)
    try:
        with os.fdopen(fd,'w') as out:
            out.write(data);out.flush();os.fsync(out.fileno())
        os.replace(temporary,path)
    finally:temporary.unlink(missing_ok=True)

def cleanup(ident):
    marker=RUN/'active'
    if not marker.exists():return
    raw=read(marker,True)
    if raw==ident:owner={'id':ident,'endpoint':None} # Installed v1 helper compatibility.
    else:
        owner=json.loads(raw)
        if set(owner)!={'id','endpoint'}:raise ValueError('Invalid TCP ownership marker')
        owner['endpoint']=str(ipaddress.IPv4Address(owner['endpoint']))
    if owner['id']!=ident:return
    remove_routes(ident,owner['endpoint'])
    command('resolvectl','revert',ident,check=False)
    (RUN/(ident+'.json')).unlink(missing_ok=True)
    marker.unlink()

def serve(ident,profile):
    # systemd serializes this singleton service; never start a second route owner.
    runtime_lock=os.open('/run/family-connect-tcp-runtime.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    fcntl.flock(runtime_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    check_routing_available()
    RUN.mkdir(mode=0o700,exist_ok=True)
    if (RUN/'active').exists():raise ValueError('TCP cleanup required')
    write(RUN/'active',json.dumps({'id':ident,'endpoint':profile['server']}),0o600)
    config=RUN/(ident+'.json')
    write(config,json.dumps(tcp_config(profile,ident)),0o600)
    process=None
    def stop(*_):raise InterruptedError('Stopping')
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    try:
        process=subprocess.Popen([str(BIN/'xray'),'run','-config',str(config)],
            stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,env=ENV)
        for _ in range(100):
            if process.poll() is not None:raise RuntimeError('TCP engine exited')
            if Path('/sys/class/net',ident).exists():break
            time.sleep(.05)
        else:raise RuntimeError('TCP interface unavailable')
        command('ip','address','add','10.79.0.2/32','dev',ident)
        command('ip','-6','address','add','fd79:92::2/128','dev',ident,'nodad')
        command('sysctl','-q','-w','net.ipv4.conf.'+ident+'.rp_filter=2')
        install_routes(ident,profile['server'])
        command('resolvectl','dns',ident,'1.1.1.1','9.9.9.9')
        command('resolvectl','domain',ident,'~.')
        command('resolvectl','default-route',ident,'yes')
        if process.wait()!=0:raise RuntimeError('TCP engine exited')
    except InterruptedError:pass
    finally:
        signal.signal(signal.SIGTERM,signal.SIG_IGN)
        try:cleanup(ident)
        finally:
            if process and process.poll() is None:
                process.terminate()
                try:process.wait(timeout=5)
                except subprocess.TimeoutExpired:process.kill();process.wait()

def main():
    if os.geteuid()!=0:raise ValueError('Administrator required')
    s=ROOT.lstat()
    if not stat.S_ISDIR(s.st_mode) or s.st_uid!=0 or stat.S_IMODE(s.st_mode)!=0o755:
        raise ValueError('Unsafe TCP directory')
    uid=int(os.environ.get('PKEXEC_UID',os.environ.get('SUDO_UID','0')))
    args=sys.argv[1:]
    if not args:raise ValueError('Missing operation')
    action=args[0]
    # Runtime operations are systemd-only, never reachable through a user broker call.
    if action in ('serve','cleanup') and uid!=0:raise ValueError('Service operation required')
    lock=None
    if action not in ('serve','cleanup'):
        lock=os.open('/run/family-connect-tcp.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    try:
        if args==['import']:
            p=parse_tcp(sys.stdin.buffer.read(MAX_PROFILE+1).decode('utf-8-sig'))
            ident='fctcp'+secrets.token_hex(4)
            write(ROOT/(ident+'.conf'),json.dumps(p),0o600)
            write(ROOT/(ident+'.json'),json.dumps(dict(id=ident,owner=uid,endpoint=p['server'],primary=None)),0o644)
            print(ident);return
        if len(args)<2 or not re.fullmatch(r'fctcp[0-9a-f]{8}',args[1]):raise ValueError('Invalid TCP identity')
        ident=args[1];path=ROOT/(ident+'.json');meta=json.loads(read(path))
        if uid and meta['owner']!=uid:raise ValueError('TCP profile belongs to another user')
        if action=='pair' and len(args)==3:
            primary=str(uuid.UUID(args[2]))
            for other in ROOT.glob('*.json'):
                if other!=path and json.loads(read(other)).get('primary')==primary:raise ValueError('Already paired')
            meta['primary']=primary;write(path,json.dumps(meta),0o644);return
        if len(args)!=2 or action not in ('up','down','serve','cleanup'):raise ValueError('Invalid TCP operation')
        unit='family-connect-tcp@'+ident+'.service'
        if action=='cleanup':cleanup(ident);return
        if action=='down':command('systemctl','stop',unit);return
        profile=parse_tcp(read(ROOT/(ident+'.conf'),True))
        if action=='serve':serve(ident,profile);return
        for other in ROOT.glob('*.json'):
            if other.stem!=ident and command('systemctl','is-active','--quiet','family-connect-tcp@'+other.stem+'.service',check=False).returncode==0:
                raise ValueError('Another TCP tunnel is active')
        try:
            command('systemctl','start',unit)
            for _ in range(100):
                if Path('/sys/class/net',ident).exists():break
                time.sleep(.05)
            probe_interface(ident,profile['server'])
        except Exception:
            command('systemctl','stop',unit)
            raise
    finally:
        if lock is not None:os.close(lock)

if __name__=='__main__':
    try:main()
    except Exception as error:
        if isinstance(error,RuntimeError):print(str(error),file=sys.stderr)
        print('TCP operation failed; check installation, profile and connectivity.',file=sys.stderr)
        sys.exit(1)
