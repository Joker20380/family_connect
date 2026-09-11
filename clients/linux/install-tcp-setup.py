#!/usr/bin/python3 -I
"""Install an independently trusted setup archive using a private verified snapshot."""
import hashlib,json,os,re,runpy,sys,tempfile
from pathlib import Path
FILES={'clients/linux/install-tcp-updater.py','clients/linux/tcp-update-broker.py','scripts/tcp_delivery.py','clients/desktop/updates.py','clients/desktop/update.pub','install.py','README.txt'}
def verified(root):
    path=root/'manifest.json'
    if path.is_symlink() or not path.is_file() or path.stat().st_size>65536:raise ValueError('Invalid setup manifest')
    manifest=json.loads(path.read_bytes())
    if set(manifest)!={'format','version','architecture','sha256'} or type(manifest['format']) is not int or manifest['format']!=1 or manifest['architecture']!='amd64' or set(manifest['sha256'])!=FILES:raise ValueError('Invalid setup manifest')
    if not isinstance(manifest['version'],str) or not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+',manifest['version']):raise ValueError('Invalid setup version')
    payload={}
    for name in FILES:
        path=root/name
        for parent in path.relative_to(root).parents:
            if (root/parent).is_symlink():raise ValueError('Setup symlink')
        if path.is_symlink() or not path.is_file() or path.stat().st_size>2*1024*1024:raise ValueError('Invalid setup file')
        with path.open('rb') as stream:raw=stream.read(2*1024*1024+1)
        if hashlib.sha256(raw).hexdigest()!=manifest['sha256'][name]:raise ValueError('Setup checksum mismatch')
        payload[name]=raw
    return payload

def main():
    if os.geteuid()!=0 or len(sys.argv)!=1:raise ValueError('Run trusted setup as root without arguments')
    payload=verified(Path(__file__).resolve().parent)
    with tempfile.TemporaryDirectory(prefix='family-connect-setup-',dir='/run') as folder:
        root=Path(folder)
        for name,raw in payload.items():
            path=root/name;path.parent.mkdir(parents=True,exist_ok=True,mode=0o700);path.write_bytes(raw);path.chmod(0o600)
        runpy.run_path(str(root/'clients/linux/install-tcp-updater.py'),run_name='__main__')
if __name__=='__main__':main()
