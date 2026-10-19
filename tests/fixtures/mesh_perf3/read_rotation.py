import json
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[3]
target = root / 'state-client-build/mesh-perf-3/receipts/rotation.json'
assert not target.exists()
code = r'''
import datetime,json,subprocess
def state(unit,properties):
    return dict(line.split('=',1) for line in subprocess.check_output(['systemctl','show',unit,'--property='+properties],text=True,timeout=8).splitlines())
service=state('family-connect-credential-renewal.service','ActiveState,SubState,Result,ExecMainStatus,ExecMainStartTimestamp,ExecMainExitTimestamp')
timer=state('family-connect-credential-renewal.timer','ActiveState,SubState,LastTriggerUSec,NextElapseUSecRealtime,NextElapseUSecMonotonic')
rows=[]
try:
    output=subprocess.check_output(['journalctl','-u','family-connect-credential-renewal.service','--since','2026-10-18 13:18:00 UTC','--until','2026-10-18 13:35:00 UTC','--no-pager','-n','12','-o','json'],text=True,timeout=10)
    for line in output.splitlines():
        event=json.loads(line);message=event.get('MESSAGE') or ''
        try:
            data=json.loads(message)
            if type(data) is dict:
                safe={key:data[key] for key in ('result','mode','files_changed','remote_writes','restarts','status') if key in data and type(data[key]) in (str,int,bool)}
                rows.append(dict(utc_us=event.get('__REALTIME_TIMESTAMP'),fields=safe))
        except ValueError:
            if any(term in message for term in ('Starting ', 'Finished ', 'Deactivated successfully')):
                rows.append(dict(utc_us=event.get('__REALTIME_TIMESTAMP'),systemd_completion='Finished ' in message or 'Deactivated successfully' in message))
except subprocess.TimeoutExpired:
    rows=[dict(journal='TIMEOUT_NOT_RETRIED')]
print(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),service=service,timer=timer,events=rows)))
'''
try:
    result = subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','root@185.251.89.19',"python3 - <<'PY'\n"+code+'\nPY'],capture_output=True,text=True,timeout=30)
    record=json.loads(result.stdout) if result.returncode==0 else dict(error='READ_FAILED', exit=result.returncode)
except subprocess.TimeoutExpired:
    record=dict(error='READ_TIMEOUT')
with target.open('x') as handle:
    json.dump(record,handle,indent=2)
print(json.dumps(record,indent=2))
