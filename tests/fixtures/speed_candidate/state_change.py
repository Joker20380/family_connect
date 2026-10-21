"""Read-only receipts for the process change during the final P0b phase."""

import json
import os
import subprocess
import sys

from prepare import WORK


REMOTE = r'''
import datetime,json,subprocess
from pathlib import Path
root=Path('/opt/apps/family_connect/friends-restricted')
records={}
for name in ('renewal-state/owner.json','renewal-coordinator/transaction.json'):
 path=root/name
 if path.exists():
  assert path.stat().st_size<2*1024*1024
  records[name]=json.loads(path.read_bytes())
journals={}
for unit in ('family-connect-credential-renewal.service','family-connect-restricted-bootstrap.service'):
 response=subprocess.run(['journalctl','--file=/var/log/journal/*/system.journal','--no-pager','--all','-o','json','--since','2026-10-21 14:10:00 UTC','--until','2026-10-21 14:12:30 UTC','-n','200','-u',unit],capture_output=True,timeout=20)
 assert len(response.stdout)<8*1024*1024
 journals[unit]=dict(exit=response.returncode,rows=[json.loads(line) for line in response.stdout.splitlines()])
print(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),records=records,journals=journals,read_only=True)))
'''


def profile_delta():
    remote = r'''
import hashlib,json
from pathlib import Path
root=Path('/opt/apps/family_connect/friends-restricted')
config=json.loads((root/'renewal/node.json').read_bytes())
state=Path(config['state'])
operation='scheduled-1792591872-28bb9be0fa02eed7'
completed=json.loads((state/'completed.json').read_bytes())[operation]
assert completed['result']=='CLEANED'
paths=(state/'archive'/operation/'gateway.json.before',root/'gateway.json')
for path in paths:assert path.stat().st_size<1024*1024
raw=[path.read_bytes() for path in paths]
hashes=[hashlib.sha256(value).hexdigest() for value in raw]
assert hashes==['24c040c087ca68100af363cc3285be836ae05f0bbaa77984cc7c8ec0c02b274d','738e5f52d6e9676743272827fc8f41fdfcb4581d28619202d6537f62e63566e2']
before,after=map(json.loads,raw)
print(json.dumps(dict(operation_id=operation,archive_result=completed['result'],
 before_sha256=hashes[0],after_sha256=hashes[1],
 fields=[dict(name=name,before_present=name in before,after_present=name in after,unchanged=name in before and name in after and before[name]==after[name]) for name in sorted(set(before)|set(after))],
 read_only=True,profile_values_exported=False)))
'''
    target = WORK / 'p0b-profile-delta-archive.json'
    with target.open('xb') as output, target.with_suffix('.stderr').open('xb') as error:
        response = subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',
            '-o','ConnectTimeout=8','root@186.246.45.246','python3 -B -'],
            input=remote.encode(),stdout=output,stderr=error,timeout=35)
    print(json.dumps(dict(receipt=target.name,exit=response.returncode)))
    response.check_returncode()


def main():
    os.umask(0o077)
    if sys.argv[1:] == ['profile-delta']:
        profile_delta()
        return
    assert len(sys.argv) == 1
    for role, host in (('NL', '186.246.45.246'), ('RU', '185.251.89.19')):
        target = WORK / (role + '-p0b-state-change.json')
        with target.open('xb') as output, target.with_suffix('.stderr').open('xb') as error:
            response = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
                '-o', 'ConnectTimeout=8', 'root@' + host, 'python3 -B -'],
                input=REMOTE.encode(), stdout=output, stderr=error, timeout=55)
        print(json.dumps(dict(role=role, exit=response.returncode, receipt=target.name)))
        response.check_returncode()


if __name__ == '__main__':
    main()
