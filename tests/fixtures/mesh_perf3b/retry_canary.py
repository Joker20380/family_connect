import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess

import stage_canary


ROOT = Path(__file__).resolve().parents[3]
STATE = ROOT / 'state-client-build/mesh-perf-3b'
OPERATION = 'mesh-perf-3b-20261018-02'
STAGE = '/opt/apps/family_connect/friends-restricted/' + OPERATION
LOCAL = STATE / 'retry02'
HOST = 'root@186.246.45.246'
os.umask(0o077)


def replace_once(source, old, new):
    assert source.count(old) == 1
    return source.replace(old, new)


def remote_source():
    source = stage_canary.REMOTE.replace('mesh-perf-3b-20261018-01', OPERATION)
    source = replace_once(source, "save('start-intent.json',dict(", r'''
validator=stage/'canary_prestart.py'
environment_values={value.removeprefix('--setenv=').split('=',1)[0]:value.split('=',2)[2] for value in arguments if value.startswith('--setenv=')}
candidate_index=arguments.index(str(candidate))
base_arguments=arguments[:candidate_index]
manifest=dict(operation=guard['operation'],unit=unit,uid=account.pw_uid,gid=gid,user=user,
    working_directory=str(private),environment=environment_values,executable_arguments=arguments[candidate_index:],
    receipt=str(private/'prestart-result.json'))
validation_unit=unit.removesuffix('.service')+'-environment.service'
assert run(['systemctl','show',validation_unit,'--property=LoadState','--value']).strip()=='not-found'
validation_manifest=dict(manifest,unit=validation_unit,receipt=str(private/'environment-result.json'))
validation_manifest_path=stage/'environment-manifest.json'
validation_command=['/usr/bin/python3','-I','-B',str(validator),str(validation_manifest_path)]
validation_manifest['executable_arguments']=validation_command
for name,value in [('environment-manifest.json',validation_manifest),('launch-manifest.json',manifest)]:
    save(name,value);os.chown(stage/name,0,gid);os.chmod(stage/name,0o640)
os.chown(validator,0,gid);os.chmod(validator,0o550)
validation_arguments=[('--unit='+validation_unit if value=='--unit='+unit else
    '--property=RuntimeMaxSec=60' if value.startswith('--property=RuntimeMaxSec=') else value) for value in base_arguments]
save('environment-intent.json',dict(arguments=validation_arguments+['--wait']+validation_command,
    validator_sha256=sha(validator),production=before,operation=guard['operation']))
run(validation_arguments+['--wait']+validation_command,timeout=45)
assert json.loads((private/'environment-result.json').read_bytes())['result']=='PASS'
arguments.insert(candidate_index,'--property=ExecStartPre=/usr/bin/python3 -I -B '+str(validator)+' '+str(stage/'launch-manifest.json'))
save('start-intent.json',dict(''')
    source = replace_once(source, "run(arguments,timeout=30)", "run(arguments,timeout=30)\nassert json.loads((private/'prestart-result.json').read_bytes())['result']=='PASS'")
    return source


def save(path, value):
    with path.open('x') as handle:
        json.dump(value, handle, sort_keys=True, indent=2)
        handle.flush()
        os.fsync(handle.fileno())


def main():
    config = json.loads((STATE/'receipts/retry02-owner-preflight-v2.json').read_bytes())
    assert config['previous_operation_cleaned'] and config['local_candidate_hashes_match']
    assert config['minimum_validity_headroom_seconds'] > 7800
    assert (datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(config['utc'])).total_seconds() < 900
    LOCAL.mkdir(mode=0o700)
    now = datetime.datetime.now(datetime.timezone.utc)
    guard = dict(config['owner_guard_identity'], operation=OPERATION, not_before=now.isoformat(),
                 not_after=(now+datetime.timedelta(hours=2)).isoformat())
    save(LOCAL/'guard-input.json', guard)
    (LOCAL/'stage-remote.py').write_text(remote_source())
    files = [LOCAL/'guard-input.json', LOCAL/'stage-remote.py', STATE/'diagnostic-broker-owner-final',
             Path(__file__).with_name('canary_prestart.py')]
    expected = {path.name:hashlib.sha256(path.read_bytes()).hexdigest() for path in files}
    save(LOCAL/'upload-intent.json', dict(operation=OPERATION,predecessor='mesh-perf-3b-20261018-01',
         stage=STAGE,hashes=expected,utc=now.isoformat(),api_changed=False,owner_routed=False))
    ssh = ['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10',HOST]
    subprocess.run(ssh+['mkdir','-m','700',STAGE],check=True,timeout=20)
    subprocess.run(['scp','-q','-o','BatchMode=yes',*map(str,files),HOST+':'+STAGE+'/'],check=True,timeout=45)
    output = subprocess.check_output(ssh+['sha256sum',*[STAGE+'/'+name for name in expected]],text=True,timeout=20)
    actual = {Path(line.split()[1]).name:line.split()[0] for line in output.splitlines()}
    assert actual == expected
    save(LOCAL/'upload-receipt.json',actual)
    result = subprocess.run(ssh+['python3','-I','-B',STAGE+'/stage-remote.py'],capture_output=True,text=True,timeout=210)
    (LOCAL/'start.stderr').write_text(result.stderr)
    (LOCAL/'start.stdout').write_text(result.stdout)
    save(LOCAL/'launch-outcome.json',dict(exit=result.returncode,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
         outcome='READY' if result.returncode==0 else 'READBACK_REQUIRED_NO_RETRY'))
    if result.returncode:
        raise RuntimeError('LAUNCH_OR_PREFLIGHT_FAILED; read back actual state and clean up; no repeat')
    receipt = json.loads(result.stdout)
    save(LOCAL/'ready-receipt.json',receipt)
    subprocess.run(['scp','-q','-o','BatchMode=yes',HOST+':'+STAGE+'/state/directory.json',str(LOCAL/'canary-directory.json')],check=True,timeout=20)
    assert hashlib.sha256((LOCAL/'canary-directory.json').read_bytes()).hexdigest()==receipt['directory_sha256']
    print(json.dumps(receipt,indent=2))


if __name__ == '__main__':
    main()
