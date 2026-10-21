"""Read only exact fatal receipts and narrow earlier episode journals."""

import hashlib
import json
import os
import subprocess

from preserve import WORK

REMOTE = r'''
import json,os,subprocess
from pathlib import Path
unit='family-connect-restricted-bootstrap.service'
pid=subprocess.check_output(['systemctl','show',unit,'--value','-p','MainPID'],text=True).strip()
environment=dict(item.split(b'=',1) for item in Path('/proc/'+pid+'/environ').read_bytes().split(b'\0') if b'=' in item)
directory=Path(os.fsdecode(environment[b'FC_FATAL_RECEIPT_DIR']))
result={}
for invocation in ['560d88eec8024976b59b802f98d78971','3d5e86bab80643dc849c1a9e617be26b','85f5b21190674ed4bc75fb660789734f']:
 path=directory/('application-'+invocation+'.json')
 result[invocation]=json.loads(path.read_bytes()) if path.exists() else None
print(json.dumps(result),flush=True)
for start,end in [('15:54:30','15:55:25'),('16:00:10','16:01:05')]:
 command=['journalctl','--file=/var/log/journal/*/system.journal','--no-pager','--all','-o','json','--since','2026-10-19 '+start+' UTC','--until','2026-10-19 '+end+' UTC','-n','120','-u',unit]
 response=subprocess.run(command,capture_output=True,timeout=20)
 assert len(response.stdout)<3*1024*1024
 print(json.dumps(dict(interval=[start,end],exit=response.returncode,rows=[json.loads(line) for line in response.stdout.splitlines()],stderr=response.stderr.decode())),flush=True)
'''

RU = r'''
import json,subprocess
command=['journalctl','--file=/var/log/journal/*/system.journal','--no-pager','--all','-o','json','--since','2026-10-19 15:28:00 UTC','--until','2026-10-19 16:17:00 UTC','-n','100','-u','family-connect-credential-renewal.service']
response=subprocess.run(command,capture_output=True,timeout=20)
print(json.dumps(dict(exit=response.returncode,rows=[json.loads(line) for line in response.stdout.splitlines()],stderr=response.stderr.decode())))
'''


def main():
    os.umask(0o077)
    for role, host, script in [('NL', '186.246.45.246', REMOTE), ('RU', '185.251.89.19', RU)]:
        output = WORK / (role + '-management.jsonl')
        with output.open('xb') as stdout, (WORK / (role + '-management.stderr')).open('xb') as stderr:
            response = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=8',
                                       'root@' + host, 'python3 -B -'], input=script.encode(),
                                      stdout=stdout, stderr=stderr, timeout=55)
        print(json.dumps(dict(role=role, exit=response.returncode, bytes=output.stat().st_size,
                              sha256=hashlib.sha256(output.read_bytes()).hexdigest())))
        response.check_returncode()


if __name__ == '__main__':
    main()
