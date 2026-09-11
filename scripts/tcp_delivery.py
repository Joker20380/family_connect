"""Authenticated Linux TCP delivery. Run only from an already trusted checkout."""
import argparse,base64,gzip,hashlib,io,json,os,re,stat,subprocess,sys,tarfile,tempfile,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'clients/desktop'))
import updates as storage
DOMAIN=b'family-connect/tcp-component/v1\x00'
CATALOG_URL='https://raw.githubusercontent.com/Joker20380/family_connect/main/updates/tcp-pilot.json'
NAMES={'bin/xray','lib/helper','lib/backend.py','lib/profile_config.py','lib/LICENSE','systemd/family-connect-tcp@.service','install.py','README.txt','manifest.json'}
MAX_SIZE=128*1024*1024

def artifact_url(version):
    storage.version(version)
    return f'https://github.com/Joker20380/family_connect/releases/download/tcp-v{version}/FamilyConnect-TCP-amd64-{version}.tar.gz'

def verify(raw,public,now):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    if len(raw)>65536:raise ValueError('catalog too large')
    outer=json.loads(raw,object_pairs_hook=storage.unique)
    if type(outer) is not dict or set(outer)!={'payload','signature'}:raise ValueError('invalid envelope')
    payload=base64.b64decode(outer['payload'],validate=True)
    Ed25519PublicKey.from_public_bytes(public).verify(base64.b64decode(outer['signature'],validate=True),DOMAIN+payload)
    d=json.loads(payload,object_pairs_hook=storage.unique)
    if type(d) is not dict or set(d)!={'schema','component','architecture','version','sequence','issued_at','expires_at','artifact'}:raise ValueError('invalid component catalog')
    if d['component']!='tcp' or d['architecture']!='amd64':raise ValueError('wrong component or architecture')
    if any(type(d[k]) is not int for k in ('schema','sequence','issued_at','expires_at')) or d['schema']!=1 or not 1<=d['sequence']<2**63 or not 1<=d['issued_at']<=now<d['expires_at'] or not 0<d['expires_at']-d['issued_at']<=90*86400:raise ValueError('invalid component lease')
    a=d['artifact']
    if type(a) is not dict or set(a)!={'url','size','sha256'} or a['url']!=artifact_url(d['version']) or type(a['size']) is not int or not 1<=a['size']<=MAX_SIZE or type(a['sha256']) is not str or not re.fullmatch('[0-9a-f]{64}',a['sha256']):raise ValueError('invalid component artifact')
    return d,hashlib.sha256(payload).hexdigest()

class Delivery(storage.Updater):
    def __init__(self,*,directory,anchor=None):
        super().__init__('0.0.0',directory=directory,anchor=anchor)

    def floor(self,d,digest,now):
        path=self.directory/'state.json'
        if path.exists() or path.is_symlink():
            info=path.lstat()
            if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1 or info.st_uid!=os.getuid() or stat.S_IMODE(info.st_mode)!=0o600:raise ValueError('unsafe component floor')
            old=json.loads(path.read_text(),object_pairs_hook=storage.unique)
            if (set(old)!={'sequence','digest','last_now','version','artifact_sha256'} or type(old['sequence']) is not int or type(old['last_now']) is not int or now<old['last_now'] or d['sequence']<old['sequence'] or storage.version(d['version'])<storage.version(old['version']) or (d['sequence']==old['sequence'] and digest!=old['digest']) or (d['version']==old['version'] and d['artifact']['sha256']!=old['artifact_sha256'])):
                raise ValueError('component rollback or conflicting catalog')
        storage.atomic(path,json.dumps(dict(sequence=d['sequence'],digest=digest,last_now=now,version=d['version'],artifact_sha256=d['artifact']['sha256'])).encode())

    def fetch(self,raw,*,now=None):
        clock=(lambda: int(time.time())) if now is None else (lambda: now)
        now=clock()
        d,digest=verify(raw,self.anchor,now)
        with self.locked():
            self.floor(d,digest,now)
            a=d['artifact'];target=self.directory/(a['sha256']+'.tar.gz')
            fd,name=tempfile.mkstemp(prefix='.download-',dir=self.directory)
            try:
                h=hashlib.sha256();size=0;deadline=time.monotonic()+600
                with os.fdopen(fd,'wb') as out,storage.open_url(a['url']) as response:
                    while chunk:=response.read(65536):
                        size+=len(chunk)
                        if size>a['size'] or time.monotonic()>deadline:raise ValueError('component download limit')
                        h.update(chunk);out.write(chunk)
                    out.flush();os.fsync(out.fileno())
                if size!=a['size'] or h.hexdigest()!=a['sha256']:raise ValueError('component digest mismatch')
                verify(raw,self.anchor,clock())
                os.replace(name,target)
                storage.atomic(self.directory/'catalog.json',raw)
                return target
            finally:
                if os.path.exists(name):os.unlink(name)

    def install(self,raw,archive):
        if os.geteuid()!=0:raise ValueError('administrator required')
        if os.uname().machine!='x86_64':raise ValueError('amd64 required')
        now=int(time.time());d,digest=verify(raw,self.anchor,now)
        with self.locked():
            self.floor(d,digest,now)
            # Read the untrusted input exactly once. Extract only this authenticated snapshot.
            with open(archive,'rb') as stream:blob=stream.read(d['artifact']['size']+1)
            if len(blob)!=d['artifact']['size'] or hashlib.sha256(blob).hexdigest()!=d['artifact']['sha256']:raise ValueError('component changed')
            with tempfile.TemporaryDirectory(prefix='install-',dir=self.directory) as folder:
                root=Path(folder)
                extract(blob,root)
                verify(raw,self.anchor,int(time.time()))
                subprocess.run(['/usr/bin/python3','-I',str(root/'install.py')],check=True,timeout=180,env={'PATH':'/usr/sbin:/usr/bin:/sbin:/bin','HOME':'/root','LANG':'C'})
                storage.atomic(self.directory/'installed.json',json.dumps(d).encode())

def extract(blob,root):
    prefix='FamilyConnect-TCP-amd64/'
    # Bound decompression including metadata before tarfile parses PAX/long-name entries.
    with gzip.GzipFile(fileobj=io.BytesIO(blob)) as compressed:
        unpacked=compressed.read(MAX_SIZE+65537)
    if len(unpacked)>MAX_SIZE+65536:raise ValueError('expanded component too large')
    with tarfile.open(fileobj=io.BytesIO(unpacked),mode='r:') as archive:
        members=[];total=0
        for member in archive:
            total+=member.size
            if len(members)>=len(NAMES) or not member.isfile() or member.name not in {prefix+n for n in NAMES} or not 0<=member.size<=MAX_SIZE or total>MAX_SIZE:raise ValueError('invalid component archive')
            members.append(member)
        if len(members)!=len(NAMES) or {m.name for m in members}!={prefix+n for n in NAMES}:raise ValueError('invalid component files')
        for member in members:
            target=root/member.name.removeprefix(prefix);target.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
            storage.atomic(target,archive.extractfile(member).read(member.size+1))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['fetch','install']);p.add_argument('--catalog',type=Path);p.add_argument('--archive',type=Path);a=p.parse_args()
    if a.action=='install':
        if not a.catalog or not a.archive:p.error('install requires --catalog and --archive')
        directory=Path('/var/lib/family-connect-tcp-updates')
    else:directory=Path.home()/'.local/state/family-connect-tcp-updates'
    if a.catalog:
        with a.catalog.open('rb') as stream:raw=stream.read(65537)
    else:
        with storage.open_url(CATALOG_URL) as response:raw=response.read(65537)
    service=Delivery(directory=directory)
    if a.action=='fetch':print(service.fetch(raw))
    else:service.install(raw,a.archive)

if __name__=='__main__':main()
