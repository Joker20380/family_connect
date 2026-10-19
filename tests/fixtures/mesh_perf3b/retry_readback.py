import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'state-client-build/mesh-perf-3b/retry02'
os.umask(0o077)
NL = r'''
import datetime,hashlib,json,subprocess
from pathlib import Path
root=Path('/opt/apps/family_connect/friends-restricted')
stage=root/'mesh-perf-3b-20261018-02'
unit='family-connect-mesh-perf-3b-20261018-02.service'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def run(args):return subprocess.check_output(args,text=True,stderr=subprocess.PIPE,timeout=15)
def state(name):return dict(line.split('=',1) for line in run(['systemctl','show',name,'--property=MainPID,ActiveState,SubState,NRestarts,InvocationID,ExecMainStatus,Result,ControlGroup,EnvironmentFiles,User,Group,WorkingDirectory,ReadWritePaths,Restart']).splitlines())
result=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),canary=state(unit),production=state('family-connect-restricted-bootstrap.service'))
for name in ('canary','production'):
    pid=result[name]['MainPID']
    result[name]['loaded_sha256']=sha(Path('/proc')/pid/'exe') if pid!='0' else None
result['profile_sha256']=sha(root/'gateway.json')
for name in ('environment-result.json','prestart-result.json'):
    path=stage/'state'/name
    result[name]=dict(receipt=json.loads(path.read_bytes()),sha256=sha(path))
result['receipts']={name:sha(stage/name) for name in ('environment-intent.json','start-intent.json','ready-receipt.json','launch-manifest.json','environment-manifest.json','stage-remote.py','canary_prestart.py')}
for name,path in [('canary_directory',stage/'state/directory.json'),('production_directory',root/'directory.json')]:
    value=json.loads(path.read_bytes())
    result[name]=dict(sha256=sha(path),issued_at=value['issued_at'],expires_at=value['expires_at'])
    result[name+'_private']=value
try:records=run(['journalctl','--since','-10min','-u',unit,'-n','50','--no-pager','-o','json'])
except subprocess.TimeoutExpired:
    records='';result['journal_observation']='BOUNDED_READ_TIMEOUT'
events={}
for line in records.splitlines():
    message=json.loads(line).get('MESSAGE','')
    try:value=json.loads(message)
    except (ValueError,TypeError):continue
    event=value.get('event')
    if isinstance(event,str) and event.startswith(('bootstrap_','broker_','restricted_')):events[event]=events.get(event,0)+1
result['bounded_event_counts']=events
result['listeners']=[line for line in run(['ss','-H','-lntp']).splitlines() if ':18445 ' in line or ':18444 ' in line]
print(json.dumps(result))
'''
RU = r'''
import datetime,hashlib,json,sqlite3,subprocess
from pathlib import Path
root=Path('/opt/apps/family_connect/friends-restricted')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def run(args):return subprocess.check_output(args,text=True,stderr=subprocess.PIPE,timeout=15)
unit='family-connect-friends-http-candidate.service'
state=dict(line.split('=',1) for line in run(['systemctl','show',unit,'--property=MainPID,ActiveState,SubState,NRestarts,InvocationID']).splitlines())
args=[value.decode() for value in (Path('/proc')/state['MainPID']/'cmdline').read_bytes().split(b'\0') if value]
archive,=[Path(value) for value in args if value.endswith('.pyz')]
database=sqlite3.connect('file:/opt/apps/family_connect/friends-access/access.db?mode=ro',uri=True)
database.row_factory=sqlite3.Row
row=database.execute('SELECT operation,phase,canary,return_view,device FROM restricted_owner_handoff').fetchone()
last=database.execute('SELECT fetch_at,ack_at,ack FROM restricted_readiness_results WHERE device=? AND ack IS NOT NULL ORDER BY ack_at DESC LIMIT 1',(row['device'],)).fetchone()
ack=json.loads(last['ack'])
result=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),api=state,archive_sha256=sha(archive),
    handoff=dict(operation=row['operation'],phase=row['phase'],canary_present=row['canary'] is not None,return_present=row['return_view'] is not None),
    owner_ack=dict(fetch_at=last['fetch_at'],ack_at=last['ack_at'],result=ack['result'],version_code=ack['version_code']),
    dropin_exists=Path('/etc/systemd/system/'+unit+'.d/97-mesh-perf-3b.conf').exists())
directory=json.loads((root/'directory.json').read_bytes())
result['directory']=dict(sha256=sha(root/'directory.json'),issued_at=directory['issued_at'],expires_at=directory['expires_at'])
result['directory_private']=directory
result['renewal_timer']=run(['systemctl','show','family-connect-credential-renewal.timer','--property=ActiveState,LastTriggerUSec,NextElapseUSecMonotonic']).splitlines()
try:messages=run(['journalctl','--since','-25min','-u','family-connect-credential-renewal.service','-n','15','--no-pager','-o','json'])
except subprocess.TimeoutExpired:
    messages='';result['renewal_journal_observation']='BOUNDED_READ_TIMEOUT'
safe=[]
for line in messages.splitlines():
    record=json.loads(line)
    try:value=json.loads(record.get('MESSAGE',''))
    except (ValueError,TypeError):continue
    safe.append(dict(utc_microseconds=record['__REALTIME_TIMESTAMP'],fields={key:value[key] for key in value if key in ('result','reason','action','maintenance_required','next_renewal_at','renew_at','seconds_remaining','mutations','files_changed','remote_writes','restarts')}))
result['renewal_safe_records']=safe
print(json.dumps(result))
'''


def main():
    import sys
    name=sys.argv[1]
    assert name.isalnum() or all(character.isalnum() or character=='-' for character in name)
    results={}
    for node,host,code in [('nl','186.246.45.246',NL),('ru','185.251.89.19',RU)]:
        reply=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','root@'+host,"python3 - <<'PY'\n"+code+'\nPY'],capture_output=True,text=True,timeout=45)
        (OUT/(name+'-'+node+'.stderr')).write_text(reply.stderr)
        assert reply.returncode==0,'READBACK_FAILED_'+node
        value=json.loads(reply.stdout)
        for key in list(value):
            if key.endswith('_private'):
                with (OUT/(name+'-'+node+'-'+key+'.json')).open('x') as handle:json.dump(value.pop(key),handle)
        results[node]=value
    results['local_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    with (OUT/(name+'.json')).open('x') as handle:json.dump(results,handle,indent=2)
    print(json.dumps(results,indent=2))


if __name__=='__main__':
    main()
