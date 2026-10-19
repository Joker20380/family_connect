import json
import os
from pathlib import Path
import subprocess


os.umask(0o077)
OUT=Path(__file__).resolve().parents[3]/'state-client-build/mesh-perf-3b/retry02'
CODE=r'''
import datetime,hashlib,json,os,subprocess
from pathlib import Path
stage=Path('/opt/apps/family_connect/friends-restricted/mesh-perf-3b-20261018-02')
unit='family-connect-mesh-perf-3b-20261018-02.service'
prod='family-connect-restricted-bootstrap.service'
def run(arguments,timeout=15):return subprocess.check_output(arguments,text=True,stderr=subprocess.PIPE,timeout=timeout)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def state(name):return dict(line.split('=',1) for line in run(['systemctl','show',name,'--property=MainPID,ActiveState,SubState,NRestarts,InvocationID,ControlGroup,Result,ExecMainStatus']).splitlines())
def save(name,value):
    with (stage/name).open('x') as handle:json.dump(value,handle,sort_keys=True);handle.flush();os.fsync(handle.fileno())
    descriptor=os.open(stage,os.O_RDONLY|os.O_DIRECTORY);os.fsync(descriptor);os.close(descriptor)
ready=json.loads((stage/'ready-receipt.json').read_bytes())
before=state(unit);production=state(prod)
assert before['InvocationID']==ready['state']['InvocationID'] and before['MainPID']==ready['state']['MainPID']
assert before['NRestarts']=='0'
assert sha(Path('/proc')/before['MainPID']/'exe')==ready['loaded_sha256']
production_hash=sha(Path('/proc')/production['MainPID']/'exe')
assert production_hash=='4b722d2d7f2159b96953e27777494bf596768f860ee8da7e634fb1100b08fab7'
save('cleanup-intent.json',dict(operation=ready['operation'],reason='REAL_RETURN_GATE_NOT_AVAILABLE',
    canary=before,production=production,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),owner_handoff=False))
run(['systemctl','stop',unit],timeout=35)
after=state(unit)
assert after['MainPID']=='0' and after['ActiveState'] in ('inactive','failed')
assert not after['ControlGroup']
assert not any(':18445 ' in line for line in run(['ss','-H','-lntp']).splitlines())
assert state(prod)==production and sha(Path('/proc')/production['MainPID']/'exe')==production_hash
preflight=state(unit.removesuffix('.service')+'-environment.service')
assert preflight['MainPID']=='0' and preflight['ActiveState']!='active'
fatal=[]
for path in (stage/'state/fatal').glob('*.json'):
    value=json.loads(path.read_bytes())
    fatal.append(dict(sha256=sha(path),fields={key:value[key] for key in value if key in ('stage','cause','safe_error_class','cleanup_completed','signal','exit_code','loaded_executable_sha256')}))
result=dict(operation=ready['operation'],result='CLEANED_NEVER_ROUTED',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    canary=after,environment_check=preflight,production_unchanged=True,production=production,production_loaded_sha256=production_hash,
    listener_18445_absent=True,owner_handoff=False,provider_room_deletion='NOT_CLAIMED_BY_EXISTING_CLOSE_CONTRACT',fatal_receipts=fatal)
save('cleanup-receipt.json',result)
result['receipt_sha256']=sha(stage/'cleanup-receipt.json');result['intent_sha256']=sha(stage/'cleanup-intent.json')
print(json.dumps(result))
'''
reply=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','root@186.246.45.246',"python3 - <<'PY'\n"+CODE+'\nPY'],capture_output=True,text=True,timeout=65)
(OUT/'cleanup.stderr').write_text(reply.stderr)
with (OUT/'cleanup-outcome.json').open('x') as handle:json.dump(dict(exit=reply.returncode,readback_required=reply.returncode!=0),handle)
assert reply.returncode==0,'CLEANUP_OUTCOME_UNCERTAIN_READBACK_NO_BLIND_REPLAY'
result=json.loads(reply.stdout)
with (OUT/'cleanup.json').open('x') as handle:json.dump(result,handle,indent=2)
print(json.dumps(result,indent=2))
