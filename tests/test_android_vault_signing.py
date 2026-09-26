import argparse
from datetime import datetime,timedelta,timezone
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile
import zipfile

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes,serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID
from scripts import sign_android_vault as signing


@pytest.fixture
def bundle():
    key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    name=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'PUBLIC TEST ONLY')])
    now=datetime.now(timezone.utc)
    cert=x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key()).serial_number(1).not_valid_before(now-timedelta(days=1)).not_valid_after(now+timedelta(days=1)).sign(key,hashes.SHA256())
    password=b'PUBLIC TEST ONLY password'
    store=pkcs12.serialize_key_and_certificates(b'test',key,cert,None,serialization.BestAvailableEncryption(password))
    files={'signing/store':store,'signing/password':password+b'\n'}
    inventory={'files':[dict(path=k,size=len(v),sha256=hashlib.sha256(v).hexdigest()) for k,v in files.items()]}
    files['PRIVATE-INVENTORY.json']=json.dumps(inventory).encode()
    out=io.BytesIO()
    with tarfile.open(fileobj=out,mode='w:gz') as archive:
        for name,data in files.items():
            item=tarfile.TarInfo(name);item.size=len(data);archive.addfile(item,io.BytesIO(data))
    return out.getvalue(),store,password,cert.fingerprint(hashes.SHA256()).hex()


def test_verified_pkcs12_and_pin(bundle):
    raw,store,password,pin=bundle
    assert signing.credentials(raw,'signing/store','signing/password',pin)==(store,password)
    with pytest.raises(ValueError):signing.credentials(raw,'signing/store','signing/password','0'*64)
    with pytest.raises(ValueError):signing.members(raw,['../store','signing/password'])
    with pytest.raises(ValueError):signing.members(raw,['signing/store','signing/store'])


def test_modified_member_refused(bundle):
    raw,*_=bundle
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as a:
        files={m.name:a.extractfile(m).read() for m in a}
    files['signing/password']=b'changed'
    out=io.BytesIO()
    with tarfile.open(fileobj=out,mode='w:gz') as a:
        for name,data in files.items():
            m=tarfile.TarInfo(name);m.size=len(data);a.addfile(m,io.BytesIO(data))
    with pytest.raises(ValueError,match='inventory'):signing.members(out.getvalue(),['signing/store','signing/password'])


def test_real_kdbx_to_apksigner(bundle,tmp_path,monkeypatch):
    java=os.environ.get('FC_TEST_JAVA');jar=os.environ.get('FC_TEST_APKSIGNER_JAR');template=os.environ.get('FC_TEST_APK')
    if not all([java,jar,template]) or not Path('/usr/bin/keepassxc-cli').exists():
        pytest.skip('explicit Android SDK and public APK fixture required')
    raw,_,password,pin=bundle
    vault=tmp_path/'test.kdbx';master=b'PUBLIC TEST vault password'
    def cli(*args,fds=()):
        r=subprocess.run(['/usr/bin/keepassxc-cli',*args],input=master+b'\n'+master+b'\n',capture_output=True,pass_fds=fds)
        assert r.returncode==0
    cli('db-create','-p','-t','100',str(vault));vault.chmod(0o600)
    cli('add','-q',str(vault),'test')
    fd=os.memfd_create('test-archive',os.MFD_CLOEXEC)
    try:
        os.write(fd,raw);cli('attachment-import','-q',str(vault),'test','recovery.tar.gz',f'/proc/self/fd/{fd}',fds=(fd,))
    finally:os.close(fd)
    apk=tmp_path/'fixture.apk';output=tmp_path/'signed.apk'
    # Public binary Android manifest only; executable payload is synthetic.
    with zipfile.ZipFile(template) as source,zipfile.ZipFile(apk,'w') as dest:
        dest.writestr('AndroidManifest.xml',source.read('AndroidManifest.xml'))
        dest.writestr('assets/test.txt',b'PUBLIC TEST ONLY')
    actual=subprocess.run
    def run(command,**kw):
        assert master.decode() not in ' '.join(command) and password.decode() not in ' '.join(command)
        if command[0]=='/usr/bin/zenity':return subprocess.CompletedProcess(command,0,master+b'\n')
        return actual(command,**kw)
    monkeypatch.setattr(signing.subprocess,'run',run)
    args=argparse.Namespace(vault=vault,vault_entry='test',vault_password_dialog=True,apk=apk,
        apk_sha256=hashlib.sha256(apk.read_bytes()).hexdigest(),output=output,java=java,apksigner_jar=jar,certificate_sha256=pin)
    store,pw=signing.credentials(signing.vault_archive(args),'signing/store','signing/password',pin)
    digest=signing.sign(store,pw,args)
    assert digest==hashlib.sha256(output.read_bytes()).hexdigest()
    assert set(p.name for p in tmp_path.iterdir())=={'test.kdbx','fixture.apk','signed.apk'}
    with pytest.raises(FileExistsError):signing.sign(store,pw,args)
    args.apk_sha256='0'*64
    with pytest.raises(ValueError,match='hash'):signing.sign(store,pw,args)


@pytest.mark.parametrize('kind',['symlink','duplicate'])
def test_unsafe_archive_members_refused(bundle,kind):
    raw,*_=bundle
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as a:
        files={m.name:a.extractfile(m).read() for m in a}
    out=io.BytesIO()
    with tarfile.open(fileobj=out,mode='w:gz') as a:
        for name,data in files.items():
            m=tarfile.TarInfo(name);m.size=len(data)
            if name=='signing/store' and kind=='symlink':m.type=tarfile.SYMTYPE;m.linkname='/outside'
            a.addfile(m,io.BytesIO(data))
            if name=='signing/store' and kind=='duplicate':a.addfile(m,io.BytesIO(data))
    with pytest.raises(ValueError):signing.members(out.getvalue(),['signing/store','signing/password'])
