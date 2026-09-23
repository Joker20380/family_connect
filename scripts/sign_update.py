"""Offline Ed25519 release signing. Never put the private key in CI or Git."""
import argparse
import base64
import hashlib
import json
import os
import re
from pathlib import Path
import time
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

DOMAIN=b'family-connect/app-update/v1\x00'
WINDOWS_DOMAIN=b'family-connect/app-update/v2\x00'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--key',type=Path,required=True)
    parser.add_argument('--initialize',action='store_true');parser.add_argument('--version')
    parser.add_argument('--sequence',type=int);parser.add_argument('--artifacts',type=Path)
    parser.add_argument('--output',type=Path);parser.add_argument('--platform',choices=['both','windows'],default='both');args=parser.parse_args()
    if args.initialize:
        args.key.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
        key=Ed25519PrivateKey.generate()
        fd=os.open(args.key,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        with os.fdopen(fd,'wb') as stream:stream.write(key.private_bytes_raw());stream.flush();os.fsync(stream.fileno())
        print(base64.b64encode(key.public_key().public_bytes_raw()).decode());return
    if not args.version or not re.fullmatch(r'(0|[1-9][0-9]{0,5})\.(0|[1-9][0-9]{0,5})\.(0|[1-9][0-9]{0,5})',args.version) or args.sequence is None or not 1<=args.sequence<2**63:
        raise ValueError('invalid version or sequence')
    info=args.key.lstat()
    import stat
    if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1 or stat.S_IMODE(info.st_mode)!=0o600:raise ValueError('unsafe signing key')
    key=Ed25519PrivateKey.from_private_bytes(args.key.read_bytes())
    artifacts={}
    for platform,name in [('linux',f'FamilyConnect-Linux-{args.version}.tar.gz'),('windows',f'FamilyConnect-Setup-{args.version}-pilot-unsigned.exe')]:
        if args.platform=='windows' and platform!='windows':continue
        path=args.artifacts/name
        with path.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
        tag=('windows-v' if args.platform=='windows' else 'v')+args.version
        size=path.stat().st_size
        if not 1<=size<=512*1024*1024:raise ValueError('invalid artifact size')
        artifacts[platform]=dict(url=f'https://github.com/Joker20380/family_connect/releases/download/{tag}/{name}',sha256=digest,size=size)
    now=int(time.time())
    data=dict(schema=1,sequence=args.sequence,version=args.version,issued_at=now,expires_at=now+90*86400,artifacts=artifacts)
    domain=DOMAIN
    if args.platform=='windows':
        data=dict(schema=2,platform='windows',sequence=args.sequence,version=args.version,issued_at=now,expires_at=now+90*86400,artifact=artifacts['windows']);domain=WINDOWS_DOMAIN
    payload=json.dumps(data,sort_keys=True,separators=(',',':')).encode()
    outer=dict(payload=base64.b64encode(payload).decode(),signature=base64.b64encode(key.sign(domain+payload)).decode())
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(outer,separators=(',',':'))+'\n')


if __name__=='__main__':main()
