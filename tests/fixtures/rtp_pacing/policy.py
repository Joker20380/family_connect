"""Select an authenticated owner for the existing protected per-session policy."""

import json
import os
import subprocess
import sys

from prepare import ROOT, WORK, GATEWAY


def remote(host, source, label):
    result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
                             '-o', 'ConnectTimeout=8', 'root@' + host, 'python3 -B -'],
                            input=source, text=True, capture_output=True, timeout=30)
    if result.returncode:
        with (WORK / ('policy-' + label + '-error.txt')).open('x') as output:
            output.write(result.stderr)
        raise RuntimeError('POLICY_CHECK_FAILED_READBACK_REQUIRED')
    return json.loads(result.stdout)


def main():
    os.umask(0o077)
    mode, counters, label = sys.argv[1:]
    assert mode in ('CHECK', 'OFF', 'OBSERVE', 'FIXED4M') and counters in ('ON', 'OFF')
    assert label.isalnum()
    receipt = WORK / ('policy-' + label + '.json')
    assert not receipt.exists()
    reference = json.loads((ROOT / 'state-client-build/mobile-bootstrap-20261020/identity-after.json').read_text())
    identity = remote('185.251.89.19', '''
import base64,datetime,hashlib,json,sqlite3
from pathlib import Path
configuration=json.loads(Path('/opt/apps/family_connect/friends-restricted/renewal/node.json').read_bytes())
database=sqlite3.connect('file:'+configuration['database']+'?mode=ro',uri=True)
database.row_factory=sqlite3.Row
database.execute('PRAGMA query_only=ON')
owners=database.execute('SELECT DISTINCT device FROM restricted_owner_handoff_operations').fetchall()
assert len(owners)==1
owner=owners[0]['device']
row=dict(database.execute('SELECT device,public,wg,tcp,revoked FROM devices WHERE device=?',(owner,)).fetchone())
assert not row['revoked']
support=database.execute('SELECT support_id FROM device_support WHERE device=?',(owner,)).fetchone()
digest=lambda value:hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
public=base64.urlsafe_b64decode(row['public']+'='*(-len(row['public'])%4))
assert len(public)==64
print(json.dumps(dict(utc=datetime.datetime.now(datetime.UTC).isoformat(),identity_bindings_sha256=digest(row),support_id_sha256=digest(support['support_id']),owner_revoked=False,target=hashlib.sha256(public[32:]).hexdigest()[:32])))
''', label + 'identity')
    assert all(identity[key] == reference[key] for key in ('identity_bindings_sha256', 'support_id_sha256'))
    candidate = json.loads((WORK / 'build-result.json').read_text())['binary_sha256']
    configuration = dict(mode=mode, counters=counters, target=identity['target'],
                         allowed=[GATEWAY, candidate] if mode == 'CHECK' else [candidate])
    result = remote('186.246.45.246', '''
import hashlib,json,os,stat,subprocess,time
from pathlib import Path
configuration=CONFIGURATION
unit='family-connect-restricted-bootstrap.service'
state=dict(line.split('=',1) for line in subprocess.check_output(['systemctl','show',unit,'-p','MainPID,InvocationID,ActiveState'],text=True).splitlines())
process=Path('/proc')/state['MainPID']
loaded=hashlib.sha256((process/'exe').read_bytes()).hexdigest()
assert state['ActiveState']=='active' and loaded in configuration['allowed']
environment=dict(item.split(b'=',1) for item in (process/'environ').read_bytes().split(b'\\0') if b'=' in item)
directory=(process/'cwd'/environment[b'FC_DIAGNOSTIC_CONTROL_DIR'].decode()).resolve()
assert directory==Path('/opt/apps/family_connect/friends-restricted/diag67')
info=directory.stat()
uid=int(next(line for line in (process/'status').read_text().splitlines() if line.startswith('Uid:')).split()[2])
assert stat.S_ISDIR(info.st_mode) and stat.S_IMODE(info.st_mode)==0o700 and info.st_uid==uid
def read(name):
 path=directory/name
 if not path.exists():
  assert name.startswith('rtp-pacing') and not path.is_symlink()
  return ''
 metadata=path.lstat()
 assert stat.S_ISREG(metadata.st_mode) and stat.S_IMODE(metadata.st_mode)==0o600 and metadata.st_uid==uid
 raw=path.read_bytes()
 assert len(raw)<=32
 return raw.decode().strip()
names=('mux-profile','mux-counters','rtp-pacing','rtp-pacing-target')
before={name:read(name) for name in names}
assert before['mux-profile']=='LEGACY64'
assert before['rtp-pacing'] in ('','OFF','OBSERVE','FIXED4M')
assert before['rtp-pacing'] in ('','OFF') or before['rtp-pacing-target']==configuration['target']
def write(name,value):
 raw=value.encode()
 assert len(raw)<=32
 temporary=directory/(name+'.new-'+str(time.time_ns()))
 descriptor=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 try:
  os.fchown(descriptor,info.st_uid,info.st_gid)
  assert os.write(descriptor,raw)==len(raw)
  os.fsync(descriptor)
 finally:os.close(descriptor)
 os.replace(temporary,directory/name)
 descriptor=os.open(directory,os.O_DIRECTORY)
 try:os.fsync(descriptor)
 finally:os.close(descriptor)
if configuration['mode']!='CHECK':
 write('rtp-pacing','OFF')
 write('rtp-pacing-target',configuration['target'])
 write('mux-counters',configuration['counters'])
 write('rtp-pacing',configuration['mode'])
after={name:read(name) for name in names}
print(json.dumps(dict(epoch=time.time(),state=state,binary_sha256=loaded,before=before,after=after,new_sessions_only=True,changed=configuration['mode']!='CHECK',directory=str(directory),uid=uid)))
'''.replace('CONFIGURATION', repr(configuration)), label)
    result['owner_identity'] = identity
    with receipt.open('x') as output:
        json.dump(result, output, indent=2)
    print(json.dumps(dict(receipt=str(receipt),mode=result['after']['rtp-pacing'] or 'OFF',
                         counters=result['after']['mux-counters'],profile=result['after']['mux-profile'],
                         gateway=result['state'],identity_preserved=True,changed=result['changed'])))


if __name__ == '__main__':
    main()
