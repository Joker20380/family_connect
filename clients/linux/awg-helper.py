#!/usr/bin/python3 -I
"""Root-installed AWG pilot helper. No caller-supplied commands, hooks or paths."""
import fcntl
import ipaddress
import json
import os
from pathlib import Path
import re
import secrets
import stat
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from profile_config import parse, validate, AWG_FIELDS, MAX_PROFILE

ROOT = Path('/etc/family-connect/awg')
BIN = '/usr/local/lib/family-connect-awg'
ENV = {'PATH': BIN+':/usr/sbin:/usr/bin:/sbin:/bin', 'LANG':'C', 'HOME':'/root',
       'WG_QUICK_USERSPACE_IMPLEMENTATION':BIN+'/amneziawg-go'}

def command(*args, timeout=30):
    p = subprocess.run(args, capture_output=True, text=True, env=ENV, timeout=timeout)
    if p.returncode: raise RuntimeError('AWG operation failed: '+Path(args[0]).name+'; exit='+str(p.returncode))
    return p.stdout.strip()

def read(path, *, private=False):
    fd=os.open(path, os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        info=os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid!=0 or info.st_nlink!=1 or
            stat.S_IMODE(info.st_mode)!=(0o600 if private else 0o644)):
            raise ValueError('Unsafe AWG state')
        raw=os.read(fd,MAX_PROFILE+1)
        if len(raw)>MAX_PROFILE: raise ValueError('Oversized AWG state')
        return raw.decode()
    finally: os.close(fd)

def write(path, text, mode):
    temporary=path.with_name('.'+secrets.token_hex(16))
    fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,mode)
    try:
        with os.fdopen(fd,'w') as out:
            out.write(text);out.flush();os.fsync(out.fileno())
        os.replace(temporary,path)
        directory=os.open(ROOT,os.O_RDONLY|os.O_DIRECTORY)
        try: os.fsync(directory)
        finally: os.close(directory)
    finally: temporary.unlink(missing_ok=True)

def healthy(ident, expected):
    # Bind the probe to this interface; a working normal route cannot produce success.
    raw=command('curl','--noproxy','*','--interface',ident,'--fail','--silent',
        '--connect-timeout','4','--max-time','8','--max-filesize','4096',
        'https://1.1.1.1/cdn-cgi/trace',timeout=10)
    values=dict(line.split('=',1) for line in raw.splitlines() if '=' in line)
    if values.get('ip')!=expected: raise RuntimeError('AWG egress check failed')
    stamps=command(BIN+'/awg','show',ident,'latest-handshakes')
    if not any(0<=time.time()-int(line.split()[1])<180 for line in stamps.splitlines()):
        raise RuntimeError('AWG handshake unavailable')

def main():
    if os.geteuid()!=0: raise ValueError('Administrator required')
    uid=int(os.environ.get('PKEXEC_UID',os.environ.get('SUDO_UID','0')))
    if len(sys.argv)<2: raise ValueError('Missing operation')
    info=ROOT.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid!=0 or stat.S_IMODE(info.st_mode)!=0o755:
        raise ValueError('Unsafe AWG directory')
    lock=os.open('/run/family-connect-awg.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    try:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        action=sys.argv[1]
        if action=='import' and len(sys.argv)==2:
            raw=sys.stdin.buffer.read(MAX_PROFILE+1).decode('utf-8-sig')
            text=validate(raw,allow_awg=True);fields=parse(text,allow_awg=True)
            if not set(fields['Interface'])&AWG_FIELDS: raise ValueError('AWG profile required')
            ident='fcawg'+secrets.token_hex(4)
            endpoint=fields['Peer']['Endpoint'].rsplit(':',1)[0].strip('[]')
            if ipaddress.ip_address(endpoint).version!=4: raise ValueError('Pilot IPv4 gateway required')
            write(ROOT/(ident+'.conf'),text,0o600)
            write(ROOT/(ident+'.json'),json.dumps(dict(id=ident,owner=uid,endpoint=endpoint,primary=None)),0o644)
            print(ident);return
        if len(sys.argv) not in (3,4) or not re.fullmatch(r'fcawg[0-9a-f]{8}',sys.argv[2]):
            raise ValueError('Invalid AWG identifier')
        ident=sys.argv[2];config=ROOT/(ident+'.conf');metadata=ROOT/(ident+'.json')
        meta=json.loads(read(metadata))
        if uid!=0 and meta['owner']!=uid: raise ValueError('AWG profile belongs to another user')
        if action=='pair' and len(sys.argv)==4:
            primary=str(__import__('uuid').UUID(sys.argv[3]))
            for other in ROOT.glob('*.json'):
                record=json.loads(read(other))
                if other!=metadata and record.get('primary')==primary: raise ValueError('Already paired')
            meta['primary']=primary;write(metadata,json.dumps(meta),0o644);return
        if len(sys.argv)!=3 or action not in ('up','down'): raise ValueError('Invalid operation')
        validate(read(config,private=True),allow_awg=True)
        active=Path('/sys/class/net',ident).exists()
        if action=='down':
            if active: command(BIN+'/awg-quick','down',str(config))
            return
        for other in ROOT.glob('*.json'):
            if other.stem!=ident and Path('/sys/class/net',other.stem).exists():
                raise ValueError('Another AWG tunnel is active')
        try:
            if not active: command(BIN+'/awg-quick','up',str(config))
            healthy(ident,meta['endpoint'])
        except Exception:
            if Path('/sys/class/net',ident).exists(): command(BIN+'/awg-quick','down',str(config))
            raise
    finally: os.close(lock)

if __name__=='__main__':
    try: main()
    except Exception as error:
        if isinstance(error,RuntimeError):print(str(error),file=sys.stderr)
        print('Family Connect AWG operation failed; check installation, profile and connectivity.',file=sys.stderr)
        sys.exit(1)
