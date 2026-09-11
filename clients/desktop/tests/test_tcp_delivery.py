import base64,hashlib,importlib.util,io,json,sys,tarfile,time
from pathlib import Path
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
import tcp_delivery as d
import sign_tcp

def envelope(key,data,domain=d.DOMAIN):
 raw=json.dumps(data).encode()
 return json.dumps(dict(payload=base64.b64encode(raw).decode(),signature=base64.b64encode(key.sign(domain+raw)).decode())).encode()

@pytest.fixture
def setup(tmp_path):
 key=Ed25519PrivateKey.generate();archive=tmp_path/'bundle';archive.write_bytes(b'payload')
 raw=sign_tcp.sign(key,archive,'1.0.0',2,int(time.time()))
 data,_=d.verify(raw,key.public_key().public_bytes_raw(),int(time.time()))
 service=d.Delivery(directory=tmp_path/'state',anchor=key.public_key().public_bytes_raw())
 return key,archive,raw,data,service

@pytest.mark.parametrize('attack',['key','domain','expired','future','bool','url','size','component','arch','extra'])
def test_reject_before_download(setup,monkeypatch,attack):
 key,archive,raw,data,service=setup
 if attack=='key':key=Ed25519PrivateKey.generate()
 elif attack=='expired':data['expires_at']=int(time.time())
 elif attack=='future':data['issued_at']=int(time.time())+100
 elif attack=='bool':data['sequence']=True
 elif attack=='url':data['artifact']['url']='https://evil.example/payload'
 elif attack=='size':data['artifact']['size']=d.MAX_SIZE+1
 elif attack=='component':data['component']='app'
 elif attack=='arch':data['architecture']='arm64'
 elif attack=='extra':data['command']='sh'
 raw=envelope(key,data,domain=d.storage.DOMAIN if attack=='domain' else d.DOMAIN)
 monkeypatch.setattr(d.storage,'open_url',lambda _:pytest.fail('network before authentication'))
 with pytest.raises(Exception):service.fetch(raw)
 assert not service.directory.exists()

def test_fetch_and_persistent_floors(setup,monkeypatch):
 key,archive,raw,data,service=setup
 monkeypatch.setattr(d.storage,'open_url',lambda _:io.BytesIO(b'payload'))
 target=service.fetch(raw);assert target.read_bytes()==b'payload' and target.stat().st_mode&0o777==0o600
 restarted=d.Delivery(directory=service.directory,anchor=service.anchor)
 assert restarted.fetch(raw)==target
 for change in ({'sequence':1},{'expires_at':data['expires_at']+1},{'sequence':3,'version':'0.9.0'}):
  changed={**data,**change}
  if 'version' in change:changed['artifact']={**data['artifact'],'url':d.artifact_url(changed['version'])}
  with pytest.raises(ValueError):restarted.fetch(envelope(key,changed))
 changed={**data,'sequence':3,'artifact':{**data['artifact'],'sha256':'a'*64}}
 with pytest.raises(ValueError):restarted.fetch(envelope(key,changed))
 with pytest.raises(ValueError):restarted.fetch(raw,now=data['issued_at']-1)

@pytest.mark.parametrize('payload',[b'bad',b'payloadextra'])
def test_download_tamper_not_staged(setup,monkeypatch,payload):
 key,archive,raw,data,service=setup
 monkeypatch.setattr(d.storage,'open_url',lambda _:io.BytesIO(payload))
 with pytest.raises(ValueError):service.fetch(raw)
 assert not list(service.directory.glob('*.tar.gz'))
 assert not list(service.directory.glob('.download-*'))

def tar(attack=None):
 out=io.BytesIO()
 with tarfile.open(fileobj=out,mode='w:gz') as f:
  for name in sorted(d.NAMES):
   m=tarfile.TarInfo('FamilyConnect-TCP-amd64/'+name);m.size=1
   if name=='install.py':
    if attack=='path':m.name='../install.py'
    if attack=='link':m.type=tarfile.SYMTYPE;m.linkname='/etc/passwd';m.size=0
    if attack=='duplicate':m.name='FamilyConnect-TCP-amd64/README.txt'
   f.addfile(m,io.BytesIO(b'x'))
 return out.getvalue()

@pytest.mark.parametrize('attack',['path','link','duplicate'])
def test_extract_rejects_archive_before_writes(tmp_path,attack):
 with pytest.raises(ValueError):d.extract(tar(attack),tmp_path)
 assert list(tmp_path.iterdir())==[]

def test_privileged_install_reverifies_before_execution(setup,monkeypatch):
 key,archive,raw,data,service=setup
 monkeypatch.setattr(d.os,'geteuid',lambda:0)
 monkeypatch.setattr(d.subprocess,'run',lambda *a,**kw:pytest.fail('executed unauthenticated installer'))
 archive.write_bytes(b'tampered')
 with pytest.raises(ValueError):service.install(raw,archive)
 with pytest.raises(Exception):service.install(envelope(Ed25519PrivateKey.generate(),data),archive)

def test_install_executes_private_verified_snapshot(setup,monkeypatch):
 key,archive,raw,data,service=setup;archive.write_bytes(tar())
 raw=sign_tcp.sign(key,archive,'1.0.0',2,int(time.time()))
 monkeypatch.setattr(d.os,'geteuid',lambda:0)
 def execute(args,**kw):
  path=Path(args[2]);assert path.read_bytes()==b'x'
  assert path.parent.stat().st_mode&0o777==0o700
  archive.write_bytes(b'changed after verification')
 monkeypatch.setattr(d.subprocess,'run',execute)
 service.install(raw,archive)
 assert (service.directory/'installed.json').exists()
 assert not list(service.directory.glob('install-*'))


def test_expanded_archive_limit(tmp_path,monkeypatch):
 import gzip
 monkeypatch.setattr(d,'MAX_SIZE',1024)
 with pytest.raises(ValueError,match='expanded component'):
  d.extract(gzip.compress(b'x'*70000),tmp_path)
 assert list(tmp_path.iterdir())==[]

def test_failed_installer_does_not_record_success(setup,monkeypatch):
 key,archive,raw,data,service=setup;archive.write_bytes(tar())
 raw=sign_tcp.sign(key,archive,'1.0.0',2,int(time.time()))
 monkeypatch.setattr(d.os,'geteuid',lambda:0)
 def fail(*args,**kwargs):raise d.subprocess.CalledProcessError(1,args[0])
 monkeypatch.setattr(d.subprocess,'run',fail)
 with pytest.raises(d.subprocess.CalledProcessError):service.install(raw,archive)
 assert not (service.directory/'installed.json').exists()
 assert not list(service.directory.glob('install-*'))
