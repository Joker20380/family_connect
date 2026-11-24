"""Operator-only lease publication over a pinned, forced-command SSH identity."""
import json
import fcntl
import ipaddress
from pathlib import Path
import subprocess
from control.capture_gate import external_operation

ROOT=Path('/opt/apps/family_connect/friends-access')


def synchronize(registry):
    require_local_registry(registry)
    with (ROOT/'chat-sync.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        with external_operation():
            return _synchronize(registry)


def _synchronize(registry):
    require_local_registry(registry)
    snapshot=registry.snapshot()
    node=json.loads((ROOT/'chat-node.json').read_bytes())
    host=str(ipaddress.IPv4Address(node['host']))
    if host!=node['host']:raise ValueError('Invalid mailbox address')
    command=['/usr/bin/ssh','-i',str(ROOT/'chat-sync-key'),'-o','IdentitiesOnly=yes',
             '-o','BatchMode=yes','-o','ConnectTimeout=5','-o','StrictHostKeyChecking=yes',
             '-o','UserKnownHostsFile='+str(ROOT/'chat-known-hosts'),
             'root@'+host,'chat-sync']
    result=subprocess.run(command,input=json.dumps(snapshot).encode(),capture_output=True,timeout=10)
    if result.returncode or len(result.stdout)>2048:raise RuntimeError('Node synchronization unavailable')
    reply=json.loads(result.stdout)
    expected=dict(sequence=snapshot['sequence'],expires_at=snapshot['expires_at'],**node)
    if reply!=expected:raise ValueError('Node acknowledgement mismatch')
    return snapshot,reply


def require_local_registry(registry):
    if registry is not None and registry.access.enrollment_repository is not None:
        raise NotImplementedError('PostgreSQL mailbox publication requires fenced authority')
