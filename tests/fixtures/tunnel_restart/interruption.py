"""Reconcile unexpected external runtime change; never resumes or alters services."""

import json
import os
import subprocess

from preserve import WORK

REMOTE = r'''
import datetime,json,subprocess
from pathlib import Path
root=Path('/opt/apps/family_connect/friends-restricted')
paths=['gateway.json','directory.json','renewal/node.json','renewal/controller.json','renewal-state/owner.json','renewal-coordinator/transaction.json']
metadata={name:dict(exists=(root/name).exists(),modified=(root/name).stat().st_mtime if (root/name).exists() else None) for name in paths}
units=['family-connect-restricted-bootstrap.service','family-connect-credential-renewal.service','family-connect-credential-renewal.timer']
states={unit:subprocess.check_output(['systemctl','show',unit,'-p','ActiveState,SubState,MainPID,InvocationID,Result,ExecMainStartTimestamp,ExecMainExitTimestamp,UnitFileState'],text=True).strip() for unit in units}
command=['journalctl','--file=/var/log/journal/*/system.journal','--no-pager','--all','-o','json','--since','2026-10-19 17:01:30 UTC','--until','2026-10-19 17:04:00 UTC','-n','100']
for unit in units:command+=['-u',unit]
response=subprocess.run(command,capture_output=True,timeout=20)
assert len(response.stdout)<2*1024*1024
print(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),metadata=metadata,states=states,journal_exit=response.returncode,rows=[json.loads(line) for line in response.stdout.splitlines()])))
'''


if __name__ == '__main__':
    os.umask(0o077)
    for role, host in [('NL', '186.246.45.246'), ('RU', '185.251.89.19')]:
        with (WORK / (role + '-external-interruption.json')).open('xb') as stdout, (WORK / (role + '-external-interruption.stderr')).open('xb') as stderr:
            response = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=8', 'root@' + host,
                'python3 -B -'], input=REMOTE.encode(), stdout=stdout, stderr=stderr, timeout=35)
        print(json.dumps(dict(role=role,exit=response.returncode)))
