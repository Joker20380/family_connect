"""Forced SSH command on the authorized mailbox host; root-owned input only."""
import json
import fcntl
import ipaddress
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path('/opt/apps/family_connect/mailbox-pilot')
sys.path.insert(0, str(ROOT/'app'))
from messenger.membership import validate


def acknowledgement(value,settings,bootstrap):
    host=str(ipaddress.IPv4Address(bootstrap['server']))
    port=bootstrap['port']
    if (host!=bootstrap['server'] or type(port) is not int or not 1<=port<=65535
            or bootstrap['public_key']!=settings['public_key']):
        raise ValueError('Invalid mailbox bootstrap')
    return dict(sequence=value['sequence'],expires_at=value['expires_at'],
                host=host,port=port,public_key=settings['public_key'])


def main():
    if os.getuid()!=0 or os.environ.get('SSH_ORIGINAL_COMMAND')!='chat-sync':
        raise ValueError('Restricted mailbox command')
    lock=os.open(ROOT/'.members.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    fcntl.flock(lock,fcntl.LOCK_EX) # Held until this one-shot process exits.
    raw=sys.stdin.buffer.read(131073)
    if len(raw)>131072: raise ValueError('Snapshot too large')
    value=validate(json.loads(raw))
    target=ROOT/'members.json'
    if target.exists() and value['sequence']<=json.loads(target.read_bytes())['sequence']:
        raise ValueError('Stale snapshot')
    subprocess.run(['systemctl','is-active','--quiet','family-connect-mailbox'],check=True)
    settings=json.loads((ROOT/'settings.json').read_bytes())
    reply=acknowledgement(value,settings,json.loads((ROOT/'bootstrap.json').read_bytes()))
    import grp
    fd,path=tempfile.mkstemp(prefix='.members-',dir=ROOT)
    try:
        os.fchmod(fd,0o640);os.fchown(fd,0,grp.getgrnam('fc-mailbox').gr_gid)
        with os.fdopen(fd,'wb') as output:
            output.write(raw);output.flush();os.fsync(output.fileno())
        os.replace(path,target)
        directory=os.open(ROOT,os.O_RDONLY|os.O_DIRECTORY)
        try:os.fsync(directory)
        finally:os.close(directory)
    finally:
        if os.path.exists(path):os.unlink(path)
    print(json.dumps(reply))


if __name__=='__main__':
    try:main()
    except Exception:sys.exit(1) # No member list or private paths in remote stderr.
