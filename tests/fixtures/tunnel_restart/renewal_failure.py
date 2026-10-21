"""Preserve the current renewal failure without replaying the operation."""

import json
import os
import subprocess

from preserve import WORK

REMOTE = r'''
import datetime,json,subprocess
from pathlib import Path
root=Path('/opt/apps/family_connect/friends-restricted')
records={}
for name in ['renewal-state/owner.json','renewal-coordinator/transaction.json']:
 path=root/name
 records[name]=json.loads(path.read_bytes()) if path.exists() else None
response=subprocess.run(['journalctl','--file=/var/log/journal/*/system.journal','--no-pager','--all','-o','json','--since','2026-10-19 17:01:45 UTC','--until','2026-10-19 17:06:00 UTC','-n','45','-u','family-connect-credential-renewal.service'],capture_output=True,timeout=20)
assert len(response.stdout)<2*1024*1024
print(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),records=records,exit=response.returncode,rows=[json.loads(line) for line in response.stdout.splitlines()])))
'''


if __name__ == '__main__':
    os.umask(0o077)
    for role, host in [('NL', '186.246.45.246'), ('RU', '185.251.89.19')]:
        with (WORK / (role + '-renewal-failure.json')).open('xb') as stdout, (WORK / (role + '-renewal-failure.stderr')).open('xb') as stderr:
            response = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=8', 'root@' + host,
                'python3 -B -'], input=REMOTE.encode(), stdout=stdout, stderr=stderr, timeout=35)
        print(json.dumps(dict(role=role,exit=response.returncode)))
