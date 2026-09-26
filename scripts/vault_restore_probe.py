"""Private, network-isolated container probe; stdin is sensitive, stdout is counts only.

Operator runner must use network=none, read-only root, tmpfs /restore and a separate
mailbox state tmpfs. Never pipe decrypted input through logged shell commands.
"""
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import resource
import socket
import subprocess
import sys
import tarfile
import time

from scripts.server_secret_snapshot import LIMIT, verify


def restore(raw, root):
    """Materialize a verified snapshot in a fresh private staging directory."""
    report = verify(raw)
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:gz') as archive:
        manifest = json.load(archive.extractfile('PRIVATE-INVENTORY.json'))
        if manifest.get('scope', 'application') not in {'application', 'infrastructure'}:
            raise ValueError('unknown scope')
        prefix = root if manifest.get('scope') == 'infrastructure' else root/'opt/apps/family_connect'
        for record in manifest['files']:
            path = prefix/record['path']
            # root is an operator-owned isolated tmpfs, never a live service root.
            if any(p.is_symlink() for p in [path, *path.parents]):
                raise ValueError('unsafe staging path')
            path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            with path.open('xb') as stream:
                stream.write(archive.extractfile(record['path']).read())
            path.chmod(0o600)
        for link in manifest.get('symlinks', []):
            path = prefix/link['path']; target = prefix/link['target']
            if any(p.is_symlink() for p in [path, *path.parents]) or not target.is_file():
                raise ValueError('unsafe staging link')
            path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            path.symlink_to(os.path.relpath(target, path.parent))
    return report


def probe(root):
    from control.friends.access import Access
    from control.friends.chat import ChatAccess
    from control.friends.referrals import Referrals
    import RNS
    ru = root/'ru/opt/apps/family_connect'
    nl = root/'nl/opt/apps/family_connect/mailbox-pilot'
    access = Access(ru/'friends-access/access.db')
    members = ChatAccess(access).desired_members()
    referrals = Referrals(access, (ru/'friends-access/referral.key').read_bytes())
    with access.db() as db:
        for token, sponsor in db.execute('SELECT token,sponsor FROM referral_links'):
            expected = hashlib.sha256(referrals.digest('referral-v1:'+sponsor).encode()).hexdigest()
            if token != expected: raise ValueError('referral key mismatch')
    settings = json.loads((nl/'settings.json').read_bytes())
    identity = RNS.Identity.from_bytes((nl/'node.identity').read_bytes())
    if identity.get_public_key().hex() != settings['public_key']:
        raise ValueError('mailbox identity mismatch')
    from messenger.membership import Membership
    # Historical leases must not be extended or used to grant restored access.
    lease = json.loads((nl/'members.json').read_bytes())
    if lease['expires_at'] <= time.time() and Membership(nl/'members.json',lambda p,n:p.read_bytes()).keys():
        raise ValueError('expired membership accepted')
    from messenger.server import preflight
    preflight(nl/'settings.json')
    from messenger.relay import Spool
    spool = Spool(nl/'state/spool'); spool.close()
    process = subprocess.Popen([sys.executable,'-B','-m','messenger.server','--settings',str(nl/'settings.json')],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        deadline = time.monotonic()+15
        while time.monotonic()<deadline:
            if process.poll() is not None: raise ValueError('mailbox startup failed')
            try:
                with socket.create_connection(('127.0.0.1',4243),timeout=.2): break
            except OSError: time.sleep(.1)
        else: raise TimeoutError('mailbox listener deadline')
        process.terminate()
        if process.wait(timeout=10) != 0: raise ValueError('mailbox shutdown failed')
    finally:
        if process.poll() is None: process.kill(); process.wait()
    return dict(access_open=True, referral_key_matches=True, mailbox_identity_matches=True,
                mailbox_preflight=True, spool_open=True, mailbox_start_stop=True,
                restored_authorized_chat_members=len(members))


def main():
    resource.setrlimit(resource.RLIMIT_CORE,(0,0)); os.umask(0o077)
    root=Path('/restore')
    if not root.is_mount() or set(p.name for p in Path('/sys/class/net').iterdir()) != {'lo'}:
        raise ValueError('isolated runtime required')
    payload=sys.stdin.buffer.read(6*LIMIT+1)
    if len(payload)>6*LIMIT:raise ValueError('input limit')
    archives=json.loads(payload)
    if set(archives)!={'ru-application','nl-application','ru-infrastructure','nl-infrastructure'}:
        raise ValueError('four scopes required')
    reports=[]
    for name,encoded in archives.items():
        raw=base64.b64decode(encoded,validate=True)
        report=verify(raw)
        if report['role']!=name.split('-')[0]:raise ValueError('role mismatch')
        reports.append(restore(raw,root/report['role']))
    result=probe(root)
    result.update(files=sum(r['files'] for r in reports),databases=sum(r['databases_verified'] for r in reports))
    print(json.dumps(result))


if __name__=='__main__':
    try: main()
    except Exception as error:
        import traceback
        print(json.dumps(dict(failure=type(error).__name__,
            frames=[dict(function=f.name,line=f.lineno) for f in traceback.extract_tb(error.__traceback__)])),file=sys.stderr)
        sys.exit(1)
