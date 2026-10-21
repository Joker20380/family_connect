"""Bounded journal preservation for observed close intervals; never restarts services."""

import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess

from preserve import WORK

REMOTE = r'''
import datetime,hashlib,json,subprocess,sys
unit='family-connect-restricted-bootstrap.service'
def run(args):return subprocess.check_output(args,text=True,timeout=15).strip()
fields=run(['systemctl','show',unit,'-p','MainPID','-p','InvocationID','-p','NRestarts','-p','ExecMainStartTimestamp','-p','ActiveEnterTimestamp','-p','ActiveState'])
values=dict(line.split('=',1) for line in fields.splitlines())
pid=values['MainPID'];assert pid.isdigit() and pid!='0'
values['loaded_sha256']=run(['sha256sum','/proc/'+pid+'/exe']).split()[0]
values['utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
print(json.dumps(values),flush=True)
command=['journalctl','--file=/var/log/journal/*/system.journal','--no-pager','--all','-o','json','--since','2026-10-19 15:28:00 UTC','--until','2026-10-19 16:17:00 UTC','-n','600','-u',unit]
process=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
try:
 output,error=process.communicate(timeout=25)
 assert len(output)<=8*1024*1024,'bounded journal cap exceeded'
 sys.stdout.buffer.write(output)
 sys.stderr.buffer.write(error)
 sys.exit(process.returncode)
except BaseException:
 process.kill();process.communicate();raise
'''


def main():
    os.umask(0o077)
    output = WORK / 'NL-episodes.jsonl'
    with output.open('xb') as stdout, (WORK / 'NL-episodes.stderr').open('xb') as stderr:
        response = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
                                   '-o', 'ConnectTimeout=8', 'root@186.246.45.246', 'python3 -B -'],
                                  input=REMOTE.encode(), stdout=stdout, stderr=stderr, timeout=50)
    print(json.dumps(dict(exit=response.returncode, bytes=output.stat().st_size,
                          sha256=hashlib.sha256(output.read_bytes()).hexdigest())))
    response.check_returncode()


if __name__ == '__main__':
    main()
