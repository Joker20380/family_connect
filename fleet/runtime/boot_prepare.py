"""Restore only the verified rehearsal table after a disposable node boot."""

import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import time


def read_owned(path, root, mode, limit=65536):
    owner=0 if root==Path('/') else os.geteuid()
    if not path.is_relative_to(root):
        raise ValueError('boot_path')
    for parent in (path,*path.parents):
        info=parent.lstat()
        if stat.S_ISLNK(info.st_mode) or info.st_uid!=owner or info.st_mode & 0o022:
            raise ValueError('boot_owner')
        if parent==root:
            break
    info=path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1 or stat.S_IMODE(info.st_mode)!=mode or info.st_size>limit:
        raise ValueError('boot_file')
    descriptor=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
    with os.fdopen(descriptor,'rb') as source:
        actual=os.fstat(source.fileno())
        if (actual.st_dev,actual.st_ino,actual.st_nlink)!=(info.st_dev,info.st_ino,1):
            raise ValueError('boot_file_changed')
        return source.read(limit+1)


def prepare(metadata_path, *, root=Path('/'), runner=subprocess.run, now=time.time):
    match=re.fullmatch(r'/etc/family-connect/rehearsal/(gw-[0-9a-f]{32})/metadata.json',str(metadata_path))
    if not match:
        raise ValueError('boot_configuration_path')
    bundle=match.group(1)
    config=root/str(metadata_path).lstrip('/')
    raw=read_owned(config,root,0o644)
    metadata=json.loads(raw)
    validated=json.loads(read_owned(config.parent/'validated.json',root,0o600))
    if validated!={'bundle_id':bundle,'metadata_sha256':hashlib.sha256(raw).hexdigest()} or metadata['bundle_id']!=bundle:
        raise ValueError('boot_configuration_binding')
    if not now()<metadata['material_expires_at'] or not re.fullmatch(r'fleet-rehearsal-[a-z0-9-]+',metadata['instance_id']):
        raise ValueError('boot_expiry_or_identity')
    current=root/'opt/family-connect/current'
    if not current.is_symlink() or os.readlink(current)!='releases/'+bundle:
        raise ValueError('boot_pointer')
    firewall=read_owned(config.parent/'firewall.nft',root,0o600)
    if hashlib.sha256(firewall).hexdigest()!=metadata['files']['firewall.nft']:
        raise ValueError('boot_firewall_binding')
    state=root/'var/lib/family-connect-rehearsal'/metadata['instance_id']
    applied=json.loads(read_owned(state/('network-'+bundle+'.json'),root,0o600))['sha256']
    if read_owned(root/'etc/sysctl.d/90-family-connect-rehearsal.conf',root,0o644)!=b'net.ipv4.ip_forward = 1\n':
        raise ValueError('boot_sysctl_binding')
    def command(argv,content=None):
        return runner(argv,input=content,capture_output=True,timeout=15)
    forwarding=command(['sysctl','-n','net.ipv4.ip_forward'])
    if forwarding.returncode or forwarding.stdout.strip()!=b'1':
        raise ValueError('boot_forwarding')
    query=['nft','-s','list','table','inet','family_connect_rehearsal']
    before=command(query)
    if before.returncode:
        if before.returncode!=1 or b'No such file or directory' not in before.stderr:
            raise ValueError('boot_firewall_observation')
        for argv in (['nft','-c','-f','-'],['nft','-f','-']):
            if command(argv,firewall).returncode:
                raise ValueError('boot_firewall_restore')
        before=command(query)
    if before.returncode or hashlib.sha256(before.stdout).hexdigest()!=applied:
        raise ValueError('boot_firewall_drift')


def main():
    try:
        if os.geteuid()!=0 or len(sys.argv)!=2:
            raise ValueError('boot_root_boundary')
        prepare(sys.argv[1])
    except Exception:
        raise SystemExit(1) from None


if __name__=='__main__':
    main()
