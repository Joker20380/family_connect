"""Linux operator APK signer: PKCS12/password from KeePassXC, pinned certificate.

No release publishing or installation. Use --check-only for production-key checks
without signing. Release acceptance requirements still apply before actual signing.
"""
import argparse
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import resource
import subprocess
import tarfile

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.serialization import pkcs12
from scripts.signing_key import LIMIT, vault_archive


def members(raw, wanted):
    if len(set(wanted)) != 2:
        raise ValueError('distinct members required')
    for name in wanted:
        path=PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts or str(path)!=name:
            raise ValueError('invalid member')
    found={}; total=0; seen=set()
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r|gz') as archive:
        for item in archive:
            total+=item.size
            if total>LIMIT or item.size<0 or len(seen)>=1024 or item.name in seen:
                raise ValueError('archive bounds or duplicate')
            seen.add(item.name)
            if item.name in {*wanted,'PRIVATE-INVENTORY.json'}:
                if not item.isfile():raise ValueError('regular member required')
                found[item.name]=archive.extractfile(item).read()
    inventory=json.loads(found.pop('PRIVATE-INVENTORY.json'))
    for name in wanted:
        data=found[name];records=[r for r in inventory['files'] if r['path']==name]
        if len(records)!=1 or records[0]['size']!=len(data) or records[0]['sha256']!=hashlib.sha256(data).hexdigest():
            raise ValueError('inventory mismatch')
    return [found[name] for name in wanted]


def credentials(raw, keystore_member, password_member, certificate_sha256):
    if not re.fullmatch('[0-9a-f]{64}',certificate_sha256):raise ValueError('certificate pin required')
    store,password=members(raw,[keystore_member,password_member])
    password=password.removesuffix(b'\n')
    if not password or len(password)>4096 or any(c in password for c in (b'\n',b'\r',b'\x00')):
        raise ValueError('invalid password format')
    key,cert,_=pkcs12.load_key_and_certificates(store,password)
    if key is None or cert is None or cert.fingerprint(hashes.SHA256()).hex()!=certificate_sha256:
        raise ValueError('certificate mismatch')
    public=lambda value:value.public_bytes(serialization.Encoding.DER,serialization.PublicFormat.SubjectPublicKeyInfo)
    if public(key.public_key())!=public(cert.public_key()):raise ValueError('key mismatch')
    return store,password


def sign(store,password,args):
    """Keep secret inputs and unverified output in memfd; never overwrite an APK."""
    with contextlib.ExitStack() as stack:
        def memory(data=b''):
            fd=os.memfd_create('fc-apk-signing',os.MFD_CLOEXEC);stack.callback(os.close,fd)
            with os.fdopen(os.dup(fd),'wb') as f:f.write(data)
            os.lseek(fd,0,0);return fd
        ks=memory(store);pw=memory(password+b'\n');output=memory()
        source=os.open(args.apk,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK);stack.callback(os.close,source)
        import stat
        info=os.fstat(source)
        if not stat.S_ISREG(info.st_mode) or not 0<info.st_size<=256*1024*1024:raise ValueError('APK bounds')
        # Snapshot the public input to avoid signing a file changed during review.
        with os.fdopen(os.dup(source),'rb') as f:data=f.read(256*1024*1024+1)
        if len(data)!=info.st_size or hashlib.sha256(data).hexdigest()!=args.apk_sha256:
            raise ValueError('APK hash mismatch')
        apk=memory(data)
        path=lambda fd:f'/proc/self/fd/{fd}'
        tool=[str(args.java),'-XX:-UsePerfData','-XX:+DisableAttachMechanism','-jar',str(args.apksigner_jar)]
        result=subprocess.run([*tool,'sign','--ks',path(ks),'--ks-type','PKCS12',
            '--ks-pass','file:'+path(pw),'--v4-signing-enabled','false','--out',path(output),path(apk)],
            pass_fds=(ks,pw,output,apk),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=120)
        if result.returncode:raise ValueError('APK signing failed')
        result=subprocess.run([*tool,'verify','--verbose','--print-certs',path(output)],pass_fds=(output,),capture_output=True,timeout=120)
        fingerprints=re.findall(rb'Signer #\d+ certificate SHA-256 digest: ([0-9a-f]{64})',result.stdout)
        if result.returncode or fingerprints!=[args.certificate_sha256.encode()]:raise ValueError('signed APK verification failed')
        if not 0<os.fstat(output).st_size<=256*1024*1024:raise ValueError('output bounds')
        os.lseek(output,0,0)
        with os.fdopen(os.dup(output),'rb') as f:data=f.read()
        fd=os.open(args.output,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
        return hashlib.sha256(data).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vault',type=Path,required=True)
    parser.add_argument('--vault-entry',required=True)
    parser.add_argument('--vault-password-dialog',action='store_true')
    parser.add_argument('--keystore-member',required=True)
    parser.add_argument('--password-member',required=True)
    parser.add_argument('--certificate-sha256',required=True)
    parser.add_argument('--check-only',action='store_true')
    parser.add_argument('--apk',type=Path);parser.add_argument('--apk-sha256')
    parser.add_argument('--output',type=Path)
    parser.add_argument('--java',type=Path);parser.add_argument('--apksigner-jar',type=Path)
    args=parser.parse_args()
    resource.setrlimit(resource.RLIMIT_CORE,(0,0));os.umask(0o077)
    try:
        if not args.check_only and (not all([args.apk,args.apk_sha256,args.output,args.java,args.apksigner_jar]) or args.output.exists()):
            raise ValueError('signing arguments or existing output')
        store,password=credentials(vault_archive(args),args.keystore_member,args.password_member,args.certificate_sha256)
        if args.check_only:print('Vault PKCS12 and certificate verified; no APK signed.')
        else:print('Signed APK verified; SHA256='+sign(store,password,args))
    except Exception:
        raise SystemExit('Android vault operation failed; private diagnostics suppressed') from None


if __name__=='__main__':main()
