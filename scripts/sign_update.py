"""Offline Ed25519 release signing. Never put the private key in CI or Git."""
import argparse
import base64
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
import time
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

if __package__:
    from . import signing_key
else:
    import signing_key

DOMAIN=b'family-connect/app-update/v1\x00'
WINDOWS_DOMAIN=b'family-connect/app-update/v2\x00'
ANDROID_DOMAIN=b'family-connect/android-update/v1\x00'
ANDROID_SIGNER='67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a'


def android_payload(args, now):
    code=int(args.version.rsplit('beta',1)[1])
    if not 1<=args.minimum_supported_code<=code or code>2147483647:
        raise ValueError('invalid Android policy')
    if args.mandatory_after and not now<=args.mandatory_after<now+90*86400:
        raise ValueError('invalid Android deadline')
    name=f'FamilyConnect-Test-{args.version}.apk';path=args.artifacts/name
    if not 1024<=path.stat().st_size<=150_000_000:raise ValueError('invalid APK size')
    if not args.apksigner or not args.aapt:raise ValueError('Android verification tools required')
    signer=subprocess.check_output([args.apksigner,'verify','--print-certs',str(path)],text=True)
    if re.findall(r'Signer #\d+ certificate SHA-256 digest: ([0-9a-f]+)',signer)!=[ANDROID_SIGNER]:raise ValueError('APK signer')
    badging=subprocess.check_output([args.aapt,'dump','badging',str(path)],text=True)
    expected=f"package: name='com.familyconnect.app.friends' versionCode='{code}' versionName='{args.version}'"
    if not badging.startswith(expected) or 'application-debuggable' in badging:raise ValueError('APK identity')
    return dict(schema=1,channel='android-field',sequence=args.sequence,package='com.familyconnect.app.friends',abi='arm64-v8a',
        version=args.version,version_code=code,url=f'https://185.251.89.19:8443/downloads/{name}',size=path.stat().st_size,
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),signer_fingerprint=ANDROID_SIGNER,
        minimum_supported_version=args.minimum_supported_code,mandatory_after=args.mandatory_after,
        release_notes='FIELD release with private local diagnostics; restricted access remains individually admitted.',issued_at=now,expires_at=now+90*86400)


def main():
    parser=argparse.ArgumentParser();signing_key.arguments(parser)
    parser.add_argument('--initialize',action='store_true');parser.add_argument('--version')
    parser.add_argument('--sequence',type=int);parser.add_argument('--artifacts',type=Path)
    parser.add_argument('--output',type=Path);parser.add_argument('--platform',choices=['both','windows','android'],default='both')
    parser.add_argument('--minimum-supported-code',type=int,default=1);parser.add_argument('--mandatory-after',type=int,default=0)
    parser.add_argument('--apksigner');parser.add_argument('--aapt');args=parser.parse_args()
    if args.initialize:
        if args.key is None: raise ValueError("initialization requires --key")
        args.key.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
        key=Ed25519PrivateKey.generate()
        fd=os.open(args.key,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        with os.fdopen(fd,'wb') as stream:stream.write(key.private_bytes_raw());stream.flush();os.fsync(stream.fileno())
        print(base64.b64encode(key.public_key().public_bytes_raw()).decode());return
    pattern=r'(0|[1-9][0-9]{0,5})\.(0|[1-9][0-9]{0,5})\.(0|[1-9][0-9]{0,5})'+(r'-beta[1-9][0-9]{0,8}' if args.platform=='android' else '')
    if not args.version or not re.fullmatch(pattern,args.version) or args.sequence is None or not 1<=args.sequence<(10**15 if args.platform=='android' else 2**63):
        raise ValueError('invalid version or sequence')
    key=signing_key.load(args)
    if args.platform=='android':
        data=android_payload(args,int(time.time()))
        payload=json.dumps(data,sort_keys=True,separators=(',',':')).encode()
        outer=dict(payload=base64.b64encode(payload).decode(),signature=base64.b64encode(key.sign(ANDROID_DOMAIN+payload)).decode())
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(outer,separators=(',',':'))+'\n');return
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
