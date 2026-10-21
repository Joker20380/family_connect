"""Read-only journal metadata; never export profiles, journal free text or keys."""
import datetime
import json
import shlex
import subprocess
from interaction_prepare import WORK, save

REMOTE = r'''
import hashlib,json,re,subprocess
from pathlib import Path
unit='family-connect-restricted-bootstrap.service'
props=['MainPID','InvocationID','ActiveState','ExecMainStartTimestamp','NRestarts','FragmentPath']
state=dict(line.split('=',1) for line in subprocess.check_output(['systemctl','show',unit,'-p',','.join(props)],text=True).splitlines())
state['binary']=hashlib.sha256((Path('/proc')/state['MainPID']/'exe').read_bytes()).hexdigest()
profile=Path('/opt/apps/family_connect/friends-restricted/gateway.json')
state['profile_sha256']=hashlib.sha256(profile.read_bytes()).hexdigest()
state['profile_top_level_keys']=sorted(json.loads(profile.read_bytes()))
state['flags']={name:Path('/opt/apps/family_connect/friends-restricted/diag67',name).read_text().strip() for name in ['rtp-pacing','mux-profile','mux-counters']}
timed_out=False
try:
 raw=subprocess.check_output(['journalctl','-u',unit,'--since','2026-10-20 23:03:29 UTC','--until','2026-10-20 23:09:46 UTC','--no-pager','-o','json','-n','5000'],timeout=60)
except subprocess.TimeoutExpired as error:
 raw=error.output or b''
 timed_out=True
events=[]
for line in raw.splitlines():
 try:row=json.loads(line)
 except json.JSONDecodeError:continue
 unit_name=row.get('_SYSTEMD_UNIT','');message=row.get('MESSAGE','')
 if not isinstance(message,str):continue
 if 'family-connect' not in unit_name and 'family-connect' not in message:continue
 classifications=[word for word in ['Starting','Started','Stopping','Stopped','Deactivated','Failed','renew','rotation','restart','COMMITTED','CLEANED','profile','gateway','directory','credential'] if word.lower() in message.lower()]
 events.append(dict(timestamp_us=row.get('__REALTIME_TIMESTAMP'),unit=unit_name,pid=row.get('_PID'),invocation=row.get('_SYSTEMD_INVOCATION_ID'),message_sha256=hashlib.sha256(message.encode()).hexdigest(),classifications=classifications,systemd_unit_mentions=sorted(set(re.findall(r'family-connect-[A-Za-z0-9_.@-]+\.(?:service|timer)',message)))))
units=subprocess.check_output(['systemctl','list-units','--all','--no-legend','--plain','family-connect-*'],text=True)
names=sorted(set(re.findall(r'family-connect-[A-Za-z0-9_.@-]+\.(?:service|timer)',units)))
stages=[str(path) for pattern in ['packing-20261021-*','pstack-20261021-*'] for path in Path('/opt/apps/family_connect').glob(pattern)]
print(json.dumps(dict(state=state,events=events,units=names,existing_lab_stages=stages,journal_bytes_scanned=len(raw),journal_timed_out=timed_out,profile_hash_contract='SHA256 of whole gateway.json file bytes, including whitespace; not transport-only')))
'''


def main():
    result = subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',
                             '-o','ConnectTimeout=8','root@186.246.45.246',
                             'python3 -B -c '+shlex.quote(REMOTE)], capture_output=True, timeout=200)
    if result.returncode:
        raise RuntimeError('read-only audit failed exit='+str(result.returncode))
    value = json.loads(result.stdout)
    value['read_utc'] = datetime.datetime.now(datetime.UTC).isoformat()
    save(WORK/'external-audit.json', value)
    print(json.dumps({key:item for key,item in value.items() if key!='events'}, indent=2))
    print('historical_events',len(value['events']))


if __name__ == '__main__':
    main()
