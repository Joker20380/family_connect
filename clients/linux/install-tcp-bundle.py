#!/usr/bin/python3 -I
"""Install a local, trusted TCP bundle; verify bytes and preserve rollback files."""
import fcntl,hashlib,json,os,shutil,stat,subprocess,tempfile
from pathlib import Path
FILES={'bin/xray':'/usr/local/lib/family-connect-tcp/xray',
       'lib/helper':'/usr/local/lib/family-connect-tcp/helper',
       'lib/backend.py':'/usr/local/lib/family-connect-tcp/backend.py',
       'lib/profile_config.py':'/usr/local/lib/family-connect-tcp/profile_config.py',
       'lib/LICENSE':'/usr/local/lib/family-connect-tcp/LICENSE',
       'systemd/family-connect-tcp@.service':'/etc/systemd/system/family-connect-tcp@.service'}

def verify(root):
    manifest=json.loads((root/'manifest.json').read_text())
    if manifest.get('format')!=1 or manifest.get('architecture')!='amd64':raise ValueError('Unsupported bundle')
    hashes=manifest['sha256']
    if set(hashes)!=set(FILES)|{'install.py','README.txt'}:raise ValueError('Unexpected bundle manifest')
    payload={}
    for name,digest in hashes.items():
        path=root/name
        if path.is_symlink() or not path.is_file():raise ValueError('Invalid bundle file')
        data=path.read_bytes()
        if hashlib.sha256(data).hexdigest()!=digest:raise ValueError('Bundle checksum mismatch')
        payload[name]=data
    return payload

def command(*args):
    return subprocess.run(args,check=True,capture_output=True,text=True,timeout=30)

def directory(path):
    path=Path(path)
    if path.exists() or path.is_symlink():
        info=path.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid!=0 or info.st_mode&0o022:raise ValueError('Unsafe destination directory')
    else:
        directory(path.parent);path.mkdir(mode=0o755)

def atomic(path,data,mode):
    fd,name=tempfile.mkstemp(prefix='.tcp-install-',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as out:out.write(data);out.flush();os.fsync(out.fileno())
        os.chmod(name,mode);os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)

def main():
    if os.geteuid()!=0:raise ValueError('Run the trusted installer as root')
    if os.uname().machine!='x86_64':raise ValueError('This bundle requires x86_64')
    payload=verify(Path(__file__).resolve().parent)
    for program in ('ip','curl','resolvectl','systemctl','pkexec','sysctl'):
        if not shutil.which(program):raise ValueError('Missing dependency: '+program)
    if not stat.S_ISCHR(Path('/dev/net/tun').stat().st_mode):raise ValueError('TUN device required')
    fd=os.open('/run/family-connect-tcp.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    try:
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if Path('/run/family-connect-tcp/active').exists():raise ValueError('Finish TCP cleanup first')
        active=command('systemctl','list-units','family-connect-tcp@*.service','--state=active,activating,deactivating','--no-legend','--plain').stdout
        if active.strip():raise ValueError('Stop TCP services before installation')
        old={}
        for name,target in FILES.items():
            path=Path(target);directory(path.parent)
            if path.exists() or path.is_symlink():
                info=path.lstat()
                if not stat.S_ISREG(info.st_mode) or info.st_uid!=0 or info.st_nlink!=1:raise ValueError('Unsafe installed file')
                old[name]=(path.read_bytes(),stat.S_IMODE(info.st_mode))
        directory('/etc/family-connect/tcp');directory('/var/backups/family-connect')
        backup=Path(tempfile.mkdtemp(prefix='tcp-bundle-',dir='/var/backups/family-connect'))
        records={}
        for i,(name,(data,mode)) in enumerate(old.items()):
            saved=backup/str(i);saved.write_bytes(data);saved.chmod(0o600)
            records[name]={'backup':str(i),'destination':FILES[name],'mode':mode,'sha256':hashlib.sha256(data).hexdigest()}
        (backup/'restore.json').write_text(json.dumps({'previous':records,'new_files':[FILES[n] for n in FILES if n not in old]},indent=2));(backup/'restore.json').chmod(0o600)
        print(json.dumps({'backup':str(backup),'installing':True}),flush=True)
        changed=[]
        try:
            for name,target in FILES.items():
                atomic(Path(target),payload[name],0o755 if name in ('bin/xray','lib/helper') else 0o644);changed.append(name)
            command('systemctl','daemon-reload')
        except Exception:
            for name in reversed(changed):
                if name in old:atomic(Path(FILES[name]),*old[name])
                else:Path(FILES[name]).unlink()
            command('systemctl','daemon-reload')
            raise
        print(json.dumps({'installed':True,'backup':str(backup),'service_started':False}))
    finally:os.close(fd)

if __name__=='__main__':
    try:main()
    except Exception as error:
        detail=str(error) if isinstance(error,ValueError) else type(error).__name__
        print('TCP installation failed: '+detail)
        raise SystemExit(1)
