#!/usr/bin/python3 -I
"""Root-owned, fixed-operation TCP updater. No caller paths, URLs or code accepted."""
import fcntl,os,stat,sys
from pathlib import Path
ROOT=Path('/usr/local/lib/family-connect-tcp-updater')
FILES=('broker','tcp_delivery.py','updates.py','update.pub')
def trusted(root=ROOT):
    for path in (root,*root.parents):
        s=path.lstat()
        if not stat.S_ISDIR(s.st_mode) or s.st_uid!=0 or s.st_mode&0o022:raise ValueError('Unsafe updater directory')
    for name in FILES:
        s=(root/name).lstat()
        if not stat.S_ISREG(s.st_mode) or s.st_uid!=0 or s.st_nlink!=1 or s.st_mode&0o022:raise ValueError('Unsafe updater file')
def main():
    if os.geteuid()!=0 or sys.argv[1:]!=['install']:raise ValueError('Administrator and fixed install operation required')
    trusted()
    fd=os.open('/run/family-connect-tcp-updater.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    try:
        s=os.fstat(fd)
        if s.st_uid!=0 or not stat.S_ISREG(s.st_mode) or s.st_nlink!=1 or stat.S_IMODE(s.st_mode)!=0o600:raise ValueError('Unsafe updater lock')
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        os.environ.clear();os.environ.update(PATH='/usr/sbin:/usr/bin:/sbin:/bin',HOME='/root',LANG='C')
        sys.path.insert(0,str(ROOT))
        from tcp_delivery import Delivery,CATALOG_URL,storage
        service=Delivery(directory='/var/lib/family-connect-tcp-updates')
        with storage.open_url(CATALOG_URL) as response:raw=response.read(65537)
        archive=service.fetch(raw)
        service.install(raw,archive)
    finally:os.close(fd)
if __name__=='__main__':
    try:main()
    except Exception:
        print('TCP installation failed; check authorization, connectivity and inactive TCP state.',file=sys.stderr)
        raise SystemExit(1)
