"""Operator-only next-session profile, exact candidate only; never restarts gateway."""

import json
import re
import subprocess
import sys
from prepare import WORK, digest


def main():
    profile, target, label = sys.argv[1:]
    assert profile in ('P0', 'P1', 'P2') and re.fullmatch('[0-9a-f]{32}', target)
    assert re.fullmatch('[a-z0-9-]+', label)
    receipt = WORK / ('policy-' + label + '.json')
    assert not receipt.exists()
    build = json.loads((WORK / 'gateway-build.json').read_text())
    assert digest(WORK / 'gateway-speed') == build['sha256']
    config = dict(profile=profile, target=target, binary=build['sha256'])
    remote = r'''
import hashlib,json,os,stat,subprocess,time
from pathlib import Path
config=CONFIG
unit='family-connect-restricted-bootstrap.service'
state=dict(line.split('=',1) for line in subprocess.check_output(['systemctl','show',unit,'-p','MainPID,InvocationID,ActiveState'],text=True).splitlines())
assert state['ActiveState']=='active'
process=Path('/proc')/state['MainPID']
assert hashlib.sha256((process/'exe').read_bytes()).hexdigest()==config['binary']
directory=Path('/opt/apps/family_connect/friends-restricted/diag67')
info=directory.lstat();assert stat.S_ISDIR(info.st_mode) and stat.S_IMODE(info.st_mode)==0o700
uid=int(next(line for line in (process/'status').read_text().splitlines() if line.startswith('Uid:')).split()[2]);assert info.st_uid==uid
assert (directory/'rtp-pacing').read_text().strip()=='OFF'
assert (directory/'mux-profile').read_text().strip()=='LEGACY64'
before={name:(directory/name).read_text().strip() if (directory/name).exists() else None for name in ('speed-profile','speed-target')}
assert before['speed-target'] in (None,config['target']), 'different owner target; do not retarget an active experiment'
def put(name,value):
 raw=value.encode();assert 0<len(raw)<=32
 temporary=directory/(name+'.new-'+str(time.time_ns()))
 descriptor=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 try:
  os.fchown(descriptor,info.st_uid,info.st_gid);assert os.write(descriptor,raw)==len(raw);os.fsync(descriptor)
 finally:os.close(descriptor)
 os.replace(temporary,directory/name)
put('speed-target',config['target'])
put('speed-profile',config['profile'])
print(json.dumps(dict(state=state,binary_sha256=config['binary'],previous=before,profile=config['profile'],target=config['target'],new_sessions_only=True,restart=False,epoch=time.time())))
'''.replace('CONFIG', repr(config))
    compile(remote, '<next-session-policy>', 'exec')
    result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=8', 'root@186.246.45.246', 'python3 -B -'], input=remote, text=True, capture_output=True, timeout=30)
    if result.returncode:
        (WORK/('policy-'+label+'-failure.json')).write_text(json.dumps(dict(exit=result.returncode,stdout=result.stdout,stderr=result.stderr,outcome='READBACK_REQUIRED'),indent=2))
    result.check_returncode()
    record = json.loads(result.stdout)
    receipt.write_text(json.dumps(record, indent=2))
    print(json.dumps(record))


if __name__ == '__main__':
    main()
