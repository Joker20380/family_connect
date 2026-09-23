"""Operator-only lease publication over a pinned, forced-command SSH identity."""
import json
import fcntl
from pathlib import Path
import subprocess

ROOT=Path('/opt/apps/family_connect/friends-access')


def synchronize(registry):
    with (ROOT/'chat-sync.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        return _synchronize(registry)


def _synchronize(registry):
    snapshot=registry.snapshot()
    node=json.loads((ROOT/'chat-node.json').read_bytes())
    command=['/usr/bin/ssh','-i',str(ROOT/'chat-sync-key'),'-o','IdentitiesOnly=yes',
             '-o','BatchMode=yes','-o','ConnectTimeout=5','-o','StrictHostKeyChecking=yes',
             '-o','UserKnownHostsFile='+str(ROOT/'chat-known-hosts'),
             'root@186.246.45.246','chat-sync']
    result=subprocess.run(command,input=json.dumps(snapshot).encode(),capture_output=True,timeout=10)
    if result.returncode or len(result.stdout)>2048:raise RuntimeError('Node synchronization unavailable')
    reply=json.loads(result.stdout)
    expected=dict(sequence=snapshot['sequence'],expires_at=snapshot['expires_at'],**node)
    if reply!=expected:raise ValueError('Node acknowledgement mismatch')
    return snapshot,reply
