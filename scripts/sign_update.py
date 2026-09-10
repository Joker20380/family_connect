"""Offline Ed25519 release signing. Never put the private key in CI or Git."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import time
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

DOMAIN=b'family-connect/app-update/v1\x00'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--key',type=Path,required=True)
    parser.add_argument('--initialize',action='store_true');parser.add_argument('--version')
    parser.add_argument('--sequence',type=int);parser.add_argument('--artifacts',type=Path)
    parser.add_argument('--output',type=Path);args=parser.parse_args()
    if args.initialize:
        args.key.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
        key=Ed25519PrivateKey.generate()
        fd=os.open(args.key,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        with os.fdopen(fd,'wb') as stream:stream.write(key.private_bytes_raw());stream.flush();os.fsync(stream.fileno())
        print(base64.b64encode(key.public_key().public_bytes_raw()).decode());return
    info=args.key.lstat()
    import stat
    if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1 or stat.S_IMODE(info.st_mode)!=0o600:raise ValueError('unsafe signing key')
    key=Ed25519PrivateKey.from_private_bytes(args.key.read_bytes())
    artifacts={}
    for platform,name in [('linux',f'FamilyConnect-Linux-{args.version}.tar.gz'),('windows',f'FamilyConnect-Setup-{args.version}-pilot-unsigned.exe')]:
        path=args.artifacts/name
        with path.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
        artifacts[platform]=dict(url=f'https://github.com/Joker20380/family_connect/releases/download/v{args.version}/{name}',sha256=digest,size=path.stat().st_size)
    now=int(time.time())
    payload=json.dumps(dict(schema=1,sequence=args.sequence,version=args.version,issued_at=now,
        expires_at=now+90*86400,artifacts=artifacts),sort_keys=True,separators=(',',':')).encode()
    outer=dict(payload=base64.b64encode(payload).decode(),signature=base64.b64encode(key.sign(DOMAIN+payload)).decode())
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(outer,separators=(',',':'))+'\n')


if __name__=='__main__':main()
