import json
import os
from pathlib import Path
import re
import runpy
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
WORK = ROOT / 'state-client-build/tester-p1-cohort-20261023'


def main():
    os.umask(0o077)
    assert sys.argv[1:] in (['apply'], ['readback'])
    mode = sys.argv[1]
    destination = WORK/('policy-'+mode+'.json')
    assert not destination.exists(), 'READ_EXISTING_RECEIPT_FIRST'
    helpers = runpy.run_path(str(ROOT/'tests/fixtures/speed_candidate/prepare.py'))
    build = json.loads((WORK/'gateway-build.json').read_text())
    assert helpers['digest'](WORK/'gateway-group') == build['sha256']
    mapping = json.loads((WORK/'cohort-identity-readback.json').read_text())
    identifiers = {'FC-4D8Q-REEG','FC-ZMVK-MM7C','FC-YHQB-9VJN'}
    assert {row['support_id'] for row in mapping['devices']} == identifiers
    targets = sorted(row['family_signing_key_sha256_128'] for row in mapping['devices'])
    assert len(set(targets)) == 3 and all(re.fullmatch('[0-9a-f]{32}',value) for value in targets)
    config = dict(mode=mode,targets=targets,binary=build['sha256'],owner='3865fd21a391b23ad2b37130f11b8e3e')
    remote = '''import hashlib,json,os,stat,subprocess,time
from pathlib import Path
config=CONFIG
unit="family-connect-restricted-bootstrap.service"
state=dict(line.split("=",1) for line in subprocess.check_output(["systemctl","show",unit,"-p","MainPID,InvocationID,ActiveState"],text=True).splitlines())
assert state["ActiveState"]=="active"
process=Path("/proc")/state["MainPID"]
assert hashlib.sha256((process/"exe").read_bytes()).hexdigest()==config["binary"]
directory=Path("/opt/apps/family_connect/friends-restricted/diag67")
info=directory.lstat()
assert stat.S_ISDIR(info.st_mode) and stat.S_IMODE(info.st_mode)==0o700
uid=int(next(line for line in (process/"status").read_text().splitlines() if line.startswith("Uid:")).split()[2])
assert info.st_uid==uid
expected={"speed-target":config["owner"],"speed-profile":"P1","rtp-pacing":"OFF","mux-profile":"LEGACY64","mux-counters":"OFF"}
for name,value in expected.items():
    entry=directory/name
    metadata=entry.lstat()
    assert stat.S_ISREG(metadata.st_mode) and stat.S_IMODE(metadata.st_mode)==0o600 and metadata.st_uid==uid
    assert entry.read_text().strip()==value
path=directory/"speed-targets"
raw="\\n".join(config["targets"]).encode()
assert len(raw)==98 and config["owner"] in config["targets"]
if config["mode"]=="apply":
    assert not path.exists() and not path.is_symlink(),"EXISTING_GROUP_RECONCILE_FIRST"
    temporary=directory/(".speed-targets-"+str(time.time_ns()))
    descriptor=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    try:
        os.fchown(descriptor,info.st_uid,info.st_gid)
        assert os.write(descriptor,raw)==len(raw)
        os.fsync(descriptor)
    finally:os.close(descriptor)
    os.replace(temporary,path)
    descriptor=os.open(directory,os.O_DIRECTORY)
    try:os.fsync(descriptor)
    finally:os.close(descriptor)
metadata=path.lstat()
assert stat.S_ISREG(metadata.st_mode) and stat.S_IMODE(metadata.st_mode)==0o600 and metadata.st_uid==uid
assert path.read_bytes()==raw
assert state["InvocationID"]==subprocess.check_output(["systemctl","show",unit,"--value","-p","InvocationID"],text=True).strip()
print(json.dumps(dict(epoch=time.time(),result="EXACT_THREE_P1_POLICY_VERIFIED",mode=config["mode"],targets=config["targets"],binary=config["binary"],state=state,policy_sha256=hashlib.sha256(raw).hexdigest(),new_sessions_only=True,restart=False,diagnostic_target_unchanged=True)))
'''.replace('CONFIG',repr(config))
    compile(remote,'<p1-group-policy>','exec')
    if mode == 'apply':
        with (WORK/'policy-apply-intent.json').open('x') as output:
            json.dump(config,output,indent=2)
    result = subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8',
                             'root@186.246.45.246','python3 -B -c '+shlex.quote(remote)],capture_output=True,timeout=40)
    destination.with_suffix('.stderr').write_bytes(result.stderr)
    destination.with_suffix('.stdout').write_bytes(result.stdout)
    result.check_returncode()
    value = json.loads(result.stdout)
    destination.write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps(value))


if __name__ == '__main__':
    main()
