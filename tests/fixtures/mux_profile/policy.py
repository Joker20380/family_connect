"""Atomic operator-only settings in the existing protected local control directory."""

import json
import subprocess
import sys

from prepare import WORK, GATEWAY


def main():
    profile,counters,label=sys.argv[1:4]
    assert profile in ('LEGACY64','CREDIT128') and counters in ('ON','OFF')
    assert label.isalnum()
    receipt=WORK/('policy-'+label+'.json');assert not receipt.exists()
    candidate=json.loads((WORK/'negotiated-build.json').read_text())['sha256']
    configuration=json.dumps(dict(profile=profile,counters=counters,allowed=[GATEWAY,candidate]))
    remote='''
import hashlib,json,os,stat,subprocess,time
from pathlib import Path
configuration=CONFIGURATION
unit='family-connect-restricted-bootstrap.service'
state=dict(line.split('=',1) for line in subprocess.check_output(['systemctl','show',unit,'-p','MainPID,InvocationID,ActiveState'],text=True).splitlines())
process=Path('/proc')/state['MainPID'];loaded=hashlib.sha256((process/'exe').read_bytes()).hexdigest()
assert state['ActiveState']=='active' and loaded in configuration['allowed']
environment=dict(item.split(b'=',1) for item in (process/'environ').read_bytes().split(b'\\0') if b'=' in item)
directory=(process/'cwd'/environment[b'FC_DIAGNOSTIC_CONTROL_DIR'].decode()).resolve()
assert directory==Path('/opt/apps/family_connect/friends-restricted/diag67')
info=directory.stat();assert stat.S_ISDIR(info.st_mode) and stat.S_IMODE(info.st_mode)==0o700
uid=int(next(line for line in (process/'status').read_text().splitlines() if line.startswith('Uid:')).split()[2]);assert info.st_uid==uid
for name,value in [('mux-profile',configuration['profile']),('mux-counters',configuration['counters'])]:
 temporary=directory/(name+'.new-'+str(time.time_ns()))
 descriptor=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 try:
  os.fchown(descriptor,info.st_uid,info.st_gid);os.write(descriptor,(value+'\\n').encode());os.fsync(descriptor)
 finally:os.close(descriptor)
 os.replace(temporary,directory/name)
print(json.dumps(dict(epoch=time.time(),state=state,binary_sha256=loaded,profile=configuration['profile'],counters=configuration['counters'],new_sessions_only=True,directory=str(directory),uid=uid)))
'''.replace('CONFIGURATION',repr(json.loads(configuration)))
    result=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=8','root@186.246.45.246','python3 -B -'],input=remote,text=True,capture_output=True,timeout=30)
    result.check_returncode();record=json.loads(result.stdout)
    receipt.write_text(json.dumps(record,indent=2));print(json.dumps(record))


if __name__=='__main__':main()
