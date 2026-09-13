"""Root installer for the separately authorized Amsterdam closed pilot only.

Run on Amsterdam after placing the public, hashed source bundle in /tmp.
Input JSON contains ONLY synthetic pilot public keys. Refuses existing installs.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import pwd
import socket
import subprocess
import tarfile
import uuid

BASE=Path('/opt/apps/family_connect/mailbox-pilot')
SERVICE='family-connect-mailbox.service'


def run(*args,**kwargs):return subprocess.run(args,check=True,**kwargs)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--bundle',required=True);parser.add_argument('--sha256',required=True)
    args=parser.parse_args()
    if os.getuid()!=0:raise ValueError('Root installer required')
    interfaces=json.loads(subprocess.check_output(['ip','-j','-4','address','show']))
    if not any(a.get('local')=='186.246.45.246' for i in interfaces for a in i.get('addr_info',[])):
        raise ValueError('Installer is restricted to the authorized Amsterdam address')
    if BASE.exists() or Path('/etc/systemd/system',SERVICE).exists():raise ValueError('Existing pilot preserved; refusing overwrite')
    public=json.load(__import__('sys').stdin)
    if set(public)!={'allowed_public'} or len(public['allowed_public'])!=2:raise ValueError('Two diagnostic identities required')
    allowed=public['allowed_public']
    if len(set(allowed))!=2 or any(len(bytes.fromhex(key))!=64 for key in allowed):raise ValueError('Invalid public identities')
    with socket.socket() as check:check.bind(('0.0.0.0',4243))
    try:pwd.getpwnam('fc-mailbox');raise ValueError('Unexpected existing service user')
    except KeyError:pass
    bundle=Path(args.bundle)
    if hashlib.sha256(bundle.read_bytes()).hexdigest()!=args.sha256:raise ValueError('Public bundle hash mismatch')
    expected={'messenger/'+name for name in ('__init__.py','codec.py','relay.py','server.py','store.py','chat.py','mailbox.py','requirements.lock')}
    expected|={'provisioning/requirements.lock','pilot/messenger/family-connect-mailbox.service'}
    with tarfile.open(bundle) as archive:
        entries=archive.getmembers()
        if {x.name for x in entries}!=expected or len(entries)!=len(expected) or any(not x.isfile() or x.size>100000 for x in entries):
            raise ValueError('Unexpected bundle contents')
        BASE.mkdir(mode=0o755)
        app=BASE/'app';app.mkdir(mode=0o755)
        for member in entries:
            target=app/member.name;target.parent.mkdir(mode=0o755,parents=True,exist_ok=True)
            target.write_bytes(archive.extractfile(member).read());target.chmod(0o644)
    run('/usr/bin/python3','-m','venv',str(BASE/'venv'))
    python=str(BASE/'venv/bin/python')
    run(python,'-m','pip','install','--disable-pip-version-check','-r',str(app/'provisioning/requirements.lock'))
    run(python,'-m','pip','install','--disable-pip-version-check','--no-deps','--require-hashes','-r',str(app/'messenger/requirements.lock'))
    run('useradd','--system','--user-group','--home-dir','/nonexistent','--shell','/usr/sbin/nologin','fc-mailbox')
    account=pwd.getpwnam('fc-mailbox')
    identity_script='''import os,json,RNS
from pathlib import Path
root=Path('/opt/apps/family_connect/mailbox-pilot')
os.umask(0o077)
i=RNS.Identity()
with (root/'node.identity').open('xb') as f:f.write(i.get_private_key())
(root/'bootstrap.json').write_text(json.dumps(dict(server='186.246.45.246',port=4243,public_key=i.get_public_key().hex(),destination=RNS.Destination.hash(i,'lxmf','propagation').hex()),indent=2)+'\\n')
'''
    run(python,'-c',identity_script)
    os.chown(BASE/'node.identity',0,account.pw_gid);(BASE/'node.identity').chmod(0o640)
    (BASE/'bootstrap.json').chmod(0o644)
    bootstrap=json.loads((BASE/'bootstrap.json').read_text())
    marker=uuid.uuid4().hex
    (BASE/'settings.json').write_text(json.dumps(dict(volume_id=marker,public_key=bootstrap['public_key'],allowed_public=allowed),indent=2)+'\n')
    (BASE/'settings.json').chmod(0o644)
    state=BASE/'state';state.mkdir(mode=0o000)
    check=run_check=[python,'-B','-m','messenger.server','--settings',str(BASE/'settings.json'),'--check']
    before=subprocess.run(check,cwd=app,capture_output=True)
    if before.returncode==0 or b'not mounted' not in before.stderr:raise ValueError('Unmounted-state refusal was not verified')
    image=BASE/'state.ext4'
    with image.open('xb') as f:f.truncate(64*1024*1024)
    image.chmod(0o600)
    run('mkfs.ext4','-q','-F','-m','0',str(image))
    mount_name=subprocess.check_output(['systemd-escape','--path','--suffix=mount',str(state)],text=True).strip()
    mount=Path('/etc/systemd/system')/mount_name
    if mount.exists():raise ValueError('Existing mount unit preserved')
    mount.write_text(f'[Unit]\nDescription=Family Connect mailbox bounded state volume\n\n[Mount]\nWhat={image}\nWhere={state}\nType=ext4\nOptions=loop,nodev,nosuid,noexec\n\n[Install]\nWantedBy=multi-user.target\n')
    service=(app/'pilot/messenger/family-connect-mailbox.service').read_text().replace('RequiresMountsFor=',f'BindsTo={mount_name}\nRequiresMountsFor=')
    Path('/etc/systemd/system',SERVICE).write_text(service)
    run('systemd-analyze','verify',str(mount),'/etc/systemd/system/'+SERVICE)
    run('systemctl','daemon-reload')
    run('systemctl','enable','--now',mount_name)
    os.chown(state,account.pw_uid,account.pw_gid);state.chmod(0o700)
    (state/'.volume-id').write_text(marker+'\n');(state/'.volume-id').chmod(0o444)
    for directory in ('rns','tmp'):
        path=state/directory;path.mkdir(mode=0o700);os.chown(path,account.pw_uid,account.pw_gid)
    (state/'rns/config').write_text('[reticulum]\nshare_instance = No\nenable_transport = No\n[logging]\nloglevel = 0\n[interfaces]\n[[closed-mailbox]]\nenabled = Yes\ntype = TCPServerInterface\nlisten_ip = 0.0.0.0\nlisten_port = 4243\n')
    (state/'rns/config').chmod(0o644)
    run('runuser','-u','fc-mailbox','--',*run_check,cwd=app)
    run('systemctl','enable','--now',SERVICE)
    run('systemctl','is-active',SERVICE)
    receipt=dict(bootstrap=bootstrap,volume_bytes=image.stat().st_size,mount_unit=mount_name,
                 unmounted_refused=True,allowed_count=len(allowed),bundle_sha256=args.sha256)
    (BASE/'install-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt))


if __name__=='__main__':main()
