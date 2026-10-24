import datetime
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time

os.umask(0o077)
root = Path('/mnt/data/PycharmProjects/family_connect/state-client-build/owner-disconnections-20261022')
since, until, label = sys.argv[1:]
duration = datetime.datetime.fromisoformat(until) - datetime.datetime.fromisoformat(since)
assert 0 < duration.total_seconds() <= 600
assert label.replace('-', '').isalnum()
destination = root / ('raw-gateway-' + label)
destination.mkdir(exist_ok=False)
records = []


def save(name, command):
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    monotonic = time.monotonic_ns()
    try:
        result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=8',
                                 'root@186.246.45.246', command], capture_output=True, timeout=60)
    except subprocess.TimeoutExpired as error:
        result = subprocess.CompletedProcess(command, 124, error.stdout or b'', (error.stderr or b'') + b'\nCOLLECTION_TIMEOUT\n')
    for suffix, data in [('', result.stdout), ('.stderr', result.stderr)]:
        path = destination / (name + suffix)
        path.write_bytes(data)
        path.chmod(0o400)
        records.append(dict(file=path.name, started_utc=started, completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                            start_monotonic_ns=monotonic, end_monotonic_ns=time.monotonic_ns(), returncode=result.returncode,
                            sha256=hashlib.sha256(data).hexdigest(), bytes=len(data)))


journal_code = '''import glob,subprocess,sys
paths=glob.glob('/var/log/journal/*/system.journal');assert len(paths)==1
sys.stdout.buffer.write(subprocess.check_output(['journalctl','--file='+paths[0],'--utc','--no-pager','--all','-u','family-connect-restricted-bootstrap.service','--since',sys.argv[1]+' UTC','--until',sys.argv[2]+' UTC','-o','json'],timeout=45))
'''
save('journal.jsonl', shlex.join(['python3', '-B', '-c', journal_code, since, until]))
code = '''import json,subprocess,hashlib,time
from pathlib import Path
state=dict(line.split('=',1) for line in subprocess.check_output(['systemctl','show','family-connect-restricted-bootstrap.service','-p','MainPID,InvocationID,ActiveState,NRestarts,ExecMainStartTimestamp,ExecMainExitTimestamp,ExecMainStatus,Result'],text=True).splitlines())
root=Path('/opt/apps/family_connect/friends-restricted')
flags={name:(root/'diag67'/name).read_text().strip() if (root/'diag67'/name).exists() else None for name in ('speed-profile','speed-target','rtp-pacing','mux-profile','mux-counters')}
print(json.dumps(dict(epoch=time.time(),monotonic=time.monotonic(),state=state,binary_sha256=hashlib.sha256((Path('/proc')/state['MainPID']/'exe').read_bytes()).hexdigest() if state['MainPID']!='0' else None,profile_sha256=hashlib.sha256((root/'gateway.json').read_bytes()).hexdigest(),operator=flags)))
'''
save('runtime.json', 'python3 -B -c ' + shlex.quote(code))
manifest = destination / 'acquisition-manifest.json'
manifest.write_text(json.dumps(dict(since_utc=since, until_utc=until, records=records), indent=2) + '\n')
manifest.chmod(0o400)
print(destination)
print('MANIFEST_SHA256', hashlib.sha256(manifest.read_bytes()).hexdigest())
print('RETURN_CODES', [record['returncode'] for record in records])
