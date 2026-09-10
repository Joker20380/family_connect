import base64
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import time

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

spec=importlib.util.spec_from_file_location('desktop_updates',Path(__file__).parents[1]/'updates.py')
u=importlib.util.module_from_spec(spec);spec.loader.exec_module(u)


def signed(key,data):
    payload=json.dumps(data,sort_keys=True,separators=(',',':')).encode()
    return json.dumps(dict(payload=base64.b64encode(payload).decode(),signature=base64.b64encode(key.sign(u.DOMAIN+payload)).decode())).encode()


@pytest.fixture
def setup(tmp_path):
    key=Ed25519PrivateKey.generate();now=int(time.time())
    data=dict(schema=1,sequence=2,version='0.2.2',issued_at=now-1,expires_at=now+1000,artifacts={})
    for platform,name in [('linux','FamilyConnect-Linux-0.2.2.tar.gz'),('windows','FamilyConnect-Setup-0.2.2-pilot-unsigned.exe')]:
        data['artifacts'][platform]=dict(url='https://github.com/Joker20380/family_connect/releases/download/v0.2.2/'+name,sha256='a'*64,size=1)
    updater=u.Updater('0.2.1',directory=tmp_path/'updates',anchor=key.public_key().public_bytes_raw())
    return updater,key,data,now


def test_signed_cross_platform_fixture():
    root=Path(__file__).parents[3]/'tests/fixtures'
    public=base64.b64decode((root/'update-v1.pub').read_text())
    data,_=u.verify((root/'update-v1.json').read_bytes(),public,1000)
    assert data['version']=='0.2.2'


@pytest.mark.parametrize('attack',['signature','expiry','future','schema','url','digest','size','fields','version'])
def test_reject_invalid_updates(setup,attack):
    updater,key,data,now=setup
    if attack=='signature':key=Ed25519PrivateKey.generate()
    elif attack=='expiry':data['expires_at']=now
    elif attack=='future':data['issued_at']=now+1
    elif attack=='schema':data['schema']=True
    elif attack=='url':data['artifacts']['linux']['url']='https://evil.example/app'
    elif attack=='digest':data['artifacts']['linux']['sha256']='x'*64
    elif attack=='size':data['artifacts']['linux']['size']=512*1024*1024+1
    elif attack=='fields':data['command']='anything'
    else:data['version']='0.2.2/../../evil'
    with pytest.raises(Exception):updater.accept(signed(key,data),now=now)
    assert not (updater.directory/'state.json').exists()


def test_floor_survives_restart_and_current_version_is_not_offered(setup):
    updater,key,data,now=setup
    assert updater.accept(signed(key,data),now=now)['version']=='0.2.2'
    assert updater.accept(signed(key,data),now=now)['version']=='0.2.2'
    restarted=u.Updater('0.2.2',directory=updater.directory,anchor=updater.anchor)
    assert restarted.accept(signed(key,data),now=now) is None
    data['sequence']=1
    with pytest.raises(ValueError):restarted.accept(signed(key,data),now=now)
    data['sequence']=2;data['expires_at']+=1
    with pytest.raises(ValueError):restarted.accept(signed(key,data),now=now)
    data['sequence']=3
    with pytest.raises(ValueError):restarted.accept(signed(key,data),now=now-1)


def bundle(data,*,evil=False):
    stream=io.BytesIO()
    with tarfile.open(fileobj=stream,mode='w:gz') as archive:
        for name in sorted(u.FILES):
            raw=b'# test application file\n'
            entry=tarfile.TarInfo('FamilyConnect-Linux-0.2.2/'+name);entry.size=len(raw)
            if evil and name=='app.py':entry.name='../escape.py'
            archive.addfile(entry,io.BytesIO(raw))
    raw=stream.getvalue();data['artifacts']['linux'].update(size=len(raw),sha256=hashlib.sha256(raw).hexdigest())
    return raw


def test_verified_download_and_atomic_install_preserve_previous(setup,tmp_path,monkeypatch):
    updater,key,data,now=setup;raw=bundle(data)
    monkeypatch.setattr(u,'open_url',lambda _:io.BytesIO(raw))
    plan=updater.accept(signed(key,data),now=now)
    archive=updater.download(plan)
    root=tmp_path/'app';(root/'releases').mkdir(parents=True,mode=0o700)
    old=root/'releases/old';old.mkdir();(old/'app.py').write_text('old')
    (root/'current').symlink_to('releases/old')
    path=updater.install(plan,archive,application_root=root)
    assert path.read_bytes()==b'# test application file\n'
    assert (root/'previous/app.py').read_text()=='old'


@pytest.mark.parametrize('attack',['digest','traversal','tamper'])
def test_failed_update_does_not_switch_application(setup,tmp_path,monkeypatch,attack):
    updater,key,data,now=setup;raw=bundle(data,evil=attack=='traversal')
    root=tmp_path/'app';root.mkdir();(root/'current').symlink_to('old')
    monkeypatch.setattr(u,'open_url',lambda _:io.BytesIO(raw+b'x' if attack=='digest' else raw))
    plan=updater.accept(signed(key,data),now=now)
    with pytest.raises(ValueError):
        archive=updater.download(plan)
        if attack=='tamper':archive.write_bytes(b'changed')
        updater.install(plan,archive,application_root=root)
    assert (root/'current').readlink()==Path('old')
    assert not (tmp_path/'escape.py').exists()
