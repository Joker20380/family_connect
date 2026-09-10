"""Signed, transport-independent update catalog and opt-in Linux installer."""
import base64
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import stat
import tarfile
import time
import urllib.request

CATALOG_URL='https://raw.githubusercontent.com/Joker20380/family_connect/main/updates/pilot.json'
DOMAIN=b'family-connect/app-update/v1\x00'
FILES={'app.py','backend.py','profile_config.py','updates.py','update.pub','install-linux.sh'}


def unique(pairs):
    result={}
    for key,value in pairs:
        if key in result:raise ValueError('duplicate update field')
        result[key]=value
    return result


def version(value):
    if type(value) is not str or not re.fullmatch(r'(0|[1-9][0-9]{0,5})\.(0|[1-9][0-9]{0,5})\.(0|[1-9][0-9]{0,5})',value):
        raise ValueError('invalid version')
    return tuple(map(int,value.split('.')))


def verify(raw, public, now):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    if len(raw)>65536:raise ValueError('catalog too large')
    outer=json.loads(raw,object_pairs_hook=unique)
    if type(outer) is not dict or set(outer)!={'payload','signature'}:raise ValueError('invalid catalog')
    payload=base64.b64decode(outer['payload'],validate=True)
    signature=base64.b64decode(outer['signature'],validate=True)
    Ed25519PublicKey.from_public_bytes(public).verify(signature,DOMAIN+payload)
    data=json.loads(payload,object_pairs_hook=unique)
    if (type(data) is not dict or set(data)!={'schema','sequence','version','issued_at','expires_at','artifacts'} or
        any(type(data[k]) is not int for k in ('schema','sequence','issued_at','expires_at')) or
        data['schema']!=1 or data['issued_at']<1 or not 1<=data['sequence']<2**63 or
        not data['issued_at']<=now<data['expires_at'] or
        not 0<data['expires_at']-data['issued_at']<=90*86400):raise ValueError('invalid update lease')
    version(data['version'])
    if type(data['artifacts']) is not dict or set(data['artifacts'])!={'linux','windows'}:raise ValueError('invalid platforms')
    for platform,artifact in data['artifacts'].items():
        name=(f'FamilyConnect-Linux-{data["version"]}.tar.gz' if platform=='linux' else f'FamilyConnect-Setup-{data["version"]}-pilot-unsigned.exe')
        expected=f'https://github.com/Joker20380/family_connect/releases/download/v{data["version"]}/{name}'
        if (type(artifact) is not dict or set(artifact)!={'url','sha256','size'} or artifact['url']!=expected or
            type(artifact['sha256']) is not str or not re.fullmatch('[0-9a-f]{64}',artifact['sha256']) or
            type(artifact['size']) is not int or not 1<=artifact['size']<=512*1024*1024):raise ValueError('invalid update artifact')
    return data,hashlib.sha256(payload).hexdigest()


class HTTPSRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        if not newurl.startswith('https://'):raise ValueError('insecure update redirect')
        return super().redirect_request(req,fp,code,msg,headers,newurl)


def open_url(url):
    return urllib.request.build_opener(HTTPSRedirect()).open(url,timeout=30)


def private_directory(path):
    path.mkdir(mode=0o700,parents=True,exist_ok=True)
    info=path.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid!=os.getuid() or stat.S_IMODE(info.st_mode)!=0o700:
        raise ValueError('unsafe update storage')


def atomic(path,raw):
    temporary=path.with_name('.'+path.name+'-'+secrets.token_hex(8))
    fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    try:
        with os.fdopen(fd,'wb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
        os.replace(temporary,path)
        directory=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
        try:os.fsync(directory)
        finally:os.close(directory)
    finally:
        if temporary.exists():temporary.unlink()


class Updater:
    def __init__(self,current_version,*,directory=None,anchor=None):
        self.current=current_version
        self.directory=Path(directory or Path.home()/'.local/state/family-connect-updates')
        self.anchor=anchor or base64.b64decode(Path(__file__).with_name('update.pub').read_text().strip(),validate=True)

    @contextmanager
    def locked(self):
        private_directory(self.directory)
        fd=os.open(self.directory/'lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
        try:
            info=os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1 or info.st_uid!=os.getuid() or stat.S_IMODE(info.st_mode)!=0o600:raise ValueError('unsafe update lock')
            fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            yield
        finally:os.close(fd)

    def accept(self,raw,*,now=None):
        now=int(time.time()) if now is None else now
        data,digest=verify(raw,self.anchor,now)
        with self.locked():
            state_path=self.directory/'state.json'
            if state_path.exists() or state_path.is_symlink():
                info=state_path.lstat()
                if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1 or stat.S_IMODE(info.st_mode)!=0o600 or info.st_uid!=os.getuid():raise ValueError('unsafe update floor')
                state=json.loads(state_path.read_text(),object_pairs_hook=unique)
                if (type(state) is not dict or set(state)!={'sequence','digest','last_now'} or
                    type(state['sequence']) is not int or type(state['last_now']) is not int or
                    state['sequence']<1 or now<state['last_now'] or
                    data['sequence']<state['sequence'] or
                    (data['sequence']==state['sequence'] and digest!=state['digest'])):raise ValueError('update rollback')
            atomic(state_path,json.dumps(dict(sequence=data['sequence'],digest=digest,last_now=now)).encode())
        return data if version(data['version'])>version(self.current) else None

    def check(self):
        with open_url(CATALOG_URL) as response:raw=response.read(65537)
        return self.accept(raw)

    def download(self,data):
        if not data['issued_at']<=int(time.time())<data['expires_at']:raise ValueError('expired update')
        artifact=data['artifacts']['linux'];private_directory(self.directory)
        target=self.directory/(artifact['sha256']+'.tar.gz')
        temporary=self.directory/('.download-'+secrets.token_hex(8))
        digest=hashlib.sha256();size=0;deadline=time.monotonic()+600
        try:
            fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
            with os.fdopen(fd,'wb') as output,open_url(artifact['url']) as response:
                while chunk:=response.read(65536):
                    if time.monotonic()>deadline:raise TimeoutError('update download timeout')
                    size+=len(chunk)
                    if size>artifact['size']:raise ValueError('oversized download')
                    digest.update(chunk);output.write(chunk)
                output.flush();os.fsync(output.fileno())
            if size!=artifact['size'] or digest.hexdigest()!=artifact['sha256']:raise ValueError('update digest mismatch')
            os.replace(temporary,target)
            return target
        finally:
            if temporary.exists():temporary.unlink()

    def install(self,data,archive,*,application_root=None):
        artifact=data['artifacts']['linux']
        # Recheck both expiry and bytes immediately before installing.
        if not data['issued_at']<=int(time.time())<data['expires_at']:raise ValueError('expired update')
        with open(archive,'rb') as stream:
            if hashlib.file_digest(stream,'sha256').hexdigest()!=artifact['sha256']:raise ValueError('update changed')
        root=Path(application_root or Path.home()/'.local/share/family-connect')
        if root.is_symlink():raise ValueError('unsafe application root')
        root.mkdir(parents=True,exist_ok=True)
        releases=root/'releases';private_directory(releases)
        target=releases/(data['version']+'-'+artifact['sha256'][:12]+'-'+secrets.token_hex(6))
        with self.locked():
            if not target.exists():
                staging=releases/('.new-'+secrets.token_hex(8));staging.mkdir(mode=0o700)
                with tarfile.open(archive,'r:gz') as bundle:
                    members=bundle.getmembers();prefix=f'FamilyConnect-Linux-{data["version"]}/'
                    if (len(members)!=len(FILES) or {m.name for m in members}!={prefix+n for n in FILES} or
                        any(not m.isfile() or m.size>1024*1024 for m in members)):raise ValueError('invalid application archive')
                    for member in members:
                        raw=bundle.extractfile(member).read(1024*1024+1)
                        atomic(staging/Path(member.name).name,raw)
                import subprocess,sys
                subprocess.run([sys.executable,str(staging/'app.py'),'--smoke'],check=True,capture_output=True,timeout=15)
                os.replace(staging,target)
            if target.is_symlink():raise ValueError('unsafe installed version')
            link=root/('.current-'+secrets.token_hex(8));link.symlink_to(target.relative_to(root))
            if (root/'current').is_symlink():
                previous=root/('.previous-'+secrets.token_hex(8));previous.symlink_to(os.readlink(root/'current'));os.replace(previous,root/'previous')
            os.replace(link,root/'current')
            directory=os.open(root,os.O_RDONLY|os.O_DIRECTORY)
            try:os.fsync(directory)
            finally:os.close(directory)
        return root/'current/app.py'
