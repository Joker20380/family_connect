import argparse
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from scripts import signing_key, sign_update


def archive(raw, *, digest=None, duplicate=False, link=False):
    out=io.BytesIO()
    with tarfile.open(fileobj=out,mode='w:gz') as tar:
        for _ in range(2 if duplicate else 1):
            entry=tarfile.TarInfo('keys/root');entry.size=len(raw)
            if link:entry.type=tarfile.SYMTYPE;entry.linkname='/private'
            tar.addfile(entry,io.BytesIO(raw))
        manifest=json.dumps({'files':[{'path':'keys/root','size':len(raw),'sha256':digest or hashlib.sha256(raw).hexdigest()}]}).encode()
        entry=tarfile.TarInfo('PRIVATE-INVENTORY.json');entry.size=len(manifest);tar.addfile(entry,io.BytesIO(manifest))
    return out.getvalue()


def args(**kw):
    values=dict(key=None,vault=Path('unused'),vault_entry='Signing/test',vault_member='keys/root',
                vault_public_key=None,vault_password_dialog=False)
    values.update(kw);return argparse.Namespace(**values)


def test_archive_refusals():
    raw=bytes(range(32))
    assert signing_key.archive_key(archive(raw),'keys/root')==raw
    for data,member in [(archive(raw),'../keys/root'),(archive(raw),'absent'),
                        (archive(raw,digest='0'*64),'keys/root'),
                        (archive(raw,duplicate=True),'keys/root'),
                        (archive(raw,link=True),'keys/root'),(archive(raw[:31]),'keys/root')]:
        with pytest.raises((ValueError, tarfile.TarError)):signing_key.archive_key(data,member)


def test_private_file_rejects_symlink_hardlink_and_permissions(tmp_path):
    p=tmp_path/'key';p.write_bytes(bytes(range(32)));p.chmod(0o600)
    key=signing_key.load(args(key=p,vault=None,vault_entry=None,vault_member=None))
    assert key.private_bytes_raw()==p.read_bytes()
    symlink=tmp_path/'symlink';symlink.symlink_to(p)
    with pytest.raises(OSError):signing_key.private_file(symlink)
    hard=tmp_path/'hard';os.link(p,hard)
    with pytest.raises(ValueError):signing_key.private_file(p)
    hard.unlink();p.chmod(0o644)
    with pytest.raises(ValueError):signing_key.private_file(p)


def test_vault_anchor_is_required_and_checked(tmp_path,monkeypatch):
    with pytest.raises(ValueError):signing_key.vault_bytes(args())
    raw=bytes(range(32));anchor=tmp_path/'anchor.pub'
    anchor.write_bytes(base64.b64encode(Ed25519PrivateKey.generate().public_key().public_bytes_raw()))
    monkeypatch.setattr(signing_key,'vault_bytes',lambda a:raw)
    with pytest.raises(ValueError,match='public anchor'):signing_key.load(args(vault_public_key=anchor))


@pytest.mark.skipif(not Path('/usr/bin/keepassxc-cli').exists() or not hasattr(os,'memfd_create'),reason='Linux KeePassXC integration')
@pytest.mark.parametrize('issuer', ['update', 'tcp', 'tcp-setup'])
def test_real_vault_signs_without_plaintext_key_file(tmp_path,monkeypatch,issuer):
    password=b'PUBLIC TEST ONLY - disposable vault'
    private=Ed25519PrivateKey.generate();vault=tmp_path/'test.kdbx';anchor=tmp_path/'anchor.pub'
    anchor.write_bytes(base64.b64encode(private.public_key().public_bytes_raw()))
    def cli(*a,fd=()):
        r=subprocess.run(['/usr/bin/keepassxc-cli',*a],input=password+b'\n'+password+b'\n',capture_output=True,pass_fds=fd)
        assert r.returncode==0
    cli('db-create','-p','-t','100',str(vault));vault.chmod(0o600)
    cli('add','-q',str(vault),'test')
    fd=os.memfd_create('public-test',os.MFD_CLOEXEC)
    try:
        os.write(fd,archive(private.private_bytes_raw()))
        cli('attachment-import','-q',str(vault),'test','recovery.tar.gz',f'/proc/self/fd/{fd}',fd=(fd,))
    finally:os.close(fd)
    # Local GUI password provider replaced in the test only; no CLI password option.
    actual_run=signing_key.subprocess.run
    def run(command,**kw):
        if command[0]=='/usr/bin/zenity':return subprocess.CompletedProcess(command,0,password+b'\n')
        assert password.decode() not in ' '.join(command)
        return actual_run(command,**kw)
    monkeypatch.setattr(signing_key.subprocess,'run',run)
    executable=tmp_path/'FamilyConnect-Setup-0.2.13-pilot-unsigned.exe';executable.write_bytes(b'PUBLIC TEST ARTIFACT')
    output=tmp_path/'update.json'
    options=['--vault',str(vault),'--vault-entry','test','--vault-member','keys/root',
             '--vault-public-key',str(anchor),'--vault-password-dialog']
    if issuer=='update':
        main=sign_update.main;domain=sign_update.WINDOWS_DOMAIN
        command=['sign_update',*options,'--platform','windows','--version','0.2.13',
                 '--sequence','99','--artifacts',str(tmp_path),'--output',str(output)]
    elif issuer=='tcp':
        from scripts import sign_tcp
        main=sign_tcp.main;domain=sign_tcp.DOMAIN
        command=['sign_tcp',*options,'--version','0.2.13','--sequence','99',
                 '--archive',str(executable),'--output',str(output)]
    else:
        from scripts import tcp_setup_signature
        main=tcp_setup_signature.main;domain=tcp_setup_signature.DOMAIN
        command=['tcp_setup_signature','sign',*options,'--version','0.2.13',
                 '--archive',str(executable),'--output',str(output)]
    monkeypatch.setattr('sys.argv',command)
    main()
    envelope=json.loads(output.read_text());payload=base64.b64decode(envelope['payload'])
    private.public_key().verify(base64.b64decode(envelope['signature']),domain+payload)
    if issuer=='tcp-setup':
        # The distributed verifier must not require the operator-only vault module.
        import shutil
        standalone=tmp_path/'standalone';standalone.mkdir()
        script=standalone/'tcp_setup_signature.py'
        shutil.copyfile(Path(tcp_setup_signature.__file__),script)
        import sys
        env={k:v for k,v in os.environ.items() if k!='PYTHONPATH'}
        result=actual_run([sys.executable,str(script),'verify','--archive',str(executable),
            '--signature',str(output),'--anchor',str(anchor),'--version','0.2.13'],
            cwd=standalone,env=env,capture_output=True)
        assert result.returncode==0
        script.unlink();standalone.rmdir()
    assert sorted(p.name for p in tmp_path.iterdir())==sorted(['test.kdbx','anchor.pub',executable.name,'update.json'])
    # Wrong master password is refused without creating an output or exposing CLI diagnostics.
    output.unlink()
    def wrong(command,**kw):
        if command[0]=='/usr/bin/zenity':return subprocess.CompletedProcess(command,0,b'wrong password\n')
        return actual_run(command,**kw)
    monkeypatch.setattr(signing_key.subprocess,'run',wrong)
    with pytest.raises(ValueError,match='private diagnostics suppressed'):main()
    assert not output.exists()
