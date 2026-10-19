import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[3]
os.umask(0o077)
CODE = r'''
import ast, datetime, hashlib, json, shlex, subprocess, time
from pathlib import Path
def run(args):
    return subprocess.check_output(args,text=True,stderr=subprocess.PIPE,timeout=15)
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
unit='family-connect-credential-renewal.timer'
object_path=shlex.split(run(['busctl','call','org.freedesktop.systemd1','/org/freedesktop/systemd1','org.freedesktop.systemd1.Manager','GetUnit','s',unit]))[1]
def timer_property(name):
    return run(['busctl','get-property','org.freedesktop.systemd1',object_path,'org.freedesktop.systemd1.Timer',name]).strip()
timer={name:timer_property(name) for name in ('NextElapseUSecMonotonic','LastTriggerUSec','AccuracyUSec','RandomizedDelayUSec','TimersMonotonic')}
mono=time.clock_gettime(time.CLOCK_MONOTONIC)
wall=time.time()
next_mono=int(timer['NextElapseUSecMonotonic'].split()[1])/1000000
timer['forecast_utc']=datetime.datetime.fromtimestamp(wall+next_mono-mono,datetime.timezone.utc).isoformat()
timer['sample_utc']=datetime.datetime.fromtimestamp(wall,datetime.timezone.utc).isoformat()
timer['sample_monotonic_seconds']=mono
properties='ActiveState,SubState,Result,ExecMainStartTimestamp,ExecMainExitTimestamp,ExecMainStatus'
service=dict(line.split('=',1) for line in run(['systemctl','show','family-connect-credential-renewal.service','--property='+properties]).splitlines())
raw=run(['systemctl','show','family-connect-credential-renewal.service','--property=ExecStart','--value'])
arguments=shlex.split(raw.split('argv[]=',1)[1].split(' ;',1)[0])
script,=[Path(arg) for arg in arguments if arg.endswith('runtime_controller.py')]
config_path=Path(arguments[arguments.index('--config')+1])
config=json.loads(config_path.read_bytes())
source={name:sha(script.with_name(name)) for name in ('runtime_controller.py','production_controller.py','production_transport.py','production_node.py','credential_renewal.py','maintenance_policy.py')}
policy={}
for node in ast.parse(script.with_name('credential_renewal.py').read_bytes()).body:
    if isinstance(node,ast.Assign) and any(isinstance(target,ast.Name) and target.id in ('THRESHOLD','VALIDITY') for target in node.targets):
        policy[ast.unparse(node.targets[0])]=ast.unparse(node.value)
coordinator=Path(config['coordinator_state'])
records=[]
for path in sorted(coordinator.glob('*.json')):
    value=json.loads(path.read_bytes())
    records.append(dict(name=path.name,sha256=sha(path),fields={key:value[key] for key in ('state','result','first_cause','commit_decided') if key in value}))
print(json.dumps(dict(timer=timer,service=service,source_sha256=source,policy=policy,
    approved_leaf_crl_schedule=config['approved_leaf_crl_schedule'],coordinator_records=records)))
'''


def main():
    destination = ROOT / 'state-client-build/mesh-perf-3b/receipts' / sys.argv[1]
    assert destination.parent.name == 'receipts' and not destination.exists()
    reply = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10',
                            'root@185.251.89.19', "python3 - <<'PY'\n" + CODE + '\nPY'],
                           capture_output=True, text=True, timeout=100)
    if reply.returncode:
        destination.with_suffix('.error.txt').write_text(reply.stderr)
        raise RuntimeError('READ_ONLY_TIMING_READBACK_FAILED')
    value = json.loads(reply.stdout)
    with destination.open('x') as handle:
        json.dump(value, handle, indent=2)
        handle.flush()
        os.fsync(handle.fileno())
    print(json.dumps(value, indent=2))


if __name__ == '__main__':
    main()
