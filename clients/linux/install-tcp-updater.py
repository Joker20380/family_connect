#!/usr/bin/python3 -I
"""One-time bootstrap from a trusted checkout; never run an unverified download as root."""
import fcntl,json,os,stat,sys,tempfile
from pathlib import Path
ROOT=Path('/usr/local/lib/family-connect-tcp-updater')
SOURCE=Path(__file__).resolve().parents[2]
FILES={'broker':'clients/linux/tcp-update-broker.py','tcp_delivery.py':'scripts/tcp_delivery.py','updates.py':'clients/desktop/updates.py','update.pub':'clients/desktop/update.pub'}
def directory(path):
    if path!=path.parent:directory(path.parent)
    if path.exists() or path.is_symlink():
        s=path.lstat()
        if not stat.S_ISDIR(s.st_mode) or s.st_uid!=0 or s.st_mode&0o022:raise ValueError('Unsafe bootstrap destination')
    else:directory(path.parent);path.mkdir(mode=0o755)
def atomic(path,raw,mode):
    fd,name=tempfile.mkstemp(dir=path.parent,prefix='.bootstrap-')
    try:
        with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
        os.chmod(name,mode);os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)
def main():
    if os.geteuid()!=0 or len(sys.argv)!=1:raise ValueError('Run trusted bootstrap as root without arguments')
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    import base64
    payload={name:(SOURCE/path).read_bytes() for name,path in FILES.items()}
    Ed25519PublicKey.from_public_bytes(base64.b64decode(payload['update.pub'].strip(),validate=True))
    fd=os.open('/run/family-connect-tcp-updater.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    try:
        s=os.fstat(fd)
        if s.st_uid!=0 or not stat.S_ISREG(s.st_mode) or s.st_nlink!=1 or stat.S_IMODE(s.st_mode)!=0o600:raise ValueError('Unsafe bootstrap lock')
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        directory(ROOT);old={}
        for name in FILES:
            p=ROOT/name
            if p.exists() or p.is_symlink():
                s=p.lstat()
                if not stat.S_ISREG(s.st_mode) or s.st_uid!=0 or s.st_nlink!=1:raise ValueError('Unsafe installed updater')
                old[name]=(p.read_bytes(),stat.S_IMODE(s.st_mode))
        if 'update.pub' in old and old['update.pub'][0]!=payload['update.pub']:raise ValueError('Anchor rotation requires separate procedure')
        backup_root=Path('/var/backups/family-connect');directory(backup_root)
        backup=Path(tempfile.mkdtemp(prefix='tcp-updater-',dir=backup_root))
        for name,(raw,mode) in old.items():atomic(backup/name,raw,0o600)
        atomic(backup/'restore.json',json.dumps({'previous_modes':{n:m for n,(_,m) in old.items()},'new_files':[n for n in FILES if n not in old]}).encode(),0o600)
        print(json.dumps({'backup':str(backup)}),flush=True)
        changed=[]
        try:
            for name,raw in payload.items():atomic(ROOT/name,raw,0o755 if name=='broker' else 0o644);changed.append(name)
        except Exception:
            for name in reversed(changed):
                if name in old:atomic(ROOT/name,*old[name])
                else:(ROOT/name).unlink()
            raise
    finally:os.close(fd)
if __name__=='__main__':main()
