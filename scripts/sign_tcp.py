"""Offline TCP catalog signing, only after artifact CI and acceptance. Never use in CI."""
import argparse,base64,hashlib,json,os,stat,time
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from tcp_delivery import DOMAIN,artifact_url,verify

def sign(key,archive,version,sequence,now):
    raw=archive.read_bytes()
    data=dict(schema=1,component='tcp',architecture='amd64',version=version,sequence=sequence,
        issued_at=now,expires_at=now+90*86400,
        artifact=dict(url=artifact_url(version),size=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
    payload=json.dumps(data,sort_keys=True,separators=(',',':')).encode()
    envelope=json.dumps(dict(payload=base64.b64encode(payload).decode(),signature=base64.b64encode(key.sign(DOMAIN+payload)).decode())).encode()+b'\n'
    verify(envelope,key.public_key().public_bytes_raw(),now)
    return envelope

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('key','archive','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--version',required=True);p.add_argument('--sequence',type=int,required=True);a=p.parse_args()
    fd=os.open(a.key,os.O_RDONLY|os.O_NOFOLLOW)
    with os.fdopen(fd,'rb') as stream:
        info=os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1 or info.st_uid!=os.getuid() or stat.S_IMODE(info.st_mode)!=0o600:raise ValueError('unsafe signing key')
        key=Ed25519PrivateKey.from_private_bytes(stream.read(33))
    envelope=sign(key,a.archive,a.version,a.sequence,int(time.time()))
    with a.output.open('xb') as stream:stream.write(envelope);stream.flush();os.fsync(stream.fileno())

if __name__=='__main__':main()
