"""Bounded reuse of the USB snapshot and existing journal continuation parser."""
import argparse
import ast
import json
import os
from pathlib import Path
import re
import runpy
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[3]
WORK=ROOT/'state-client-build/p1-owner-acceptance-20261021'
sys.path.insert(0,str(ROOT))
from scripts.owner_android_support import snapshot,save


def remote_observation(tag,rows=6000):
    source=(ROOT/'tests/fixtures/queue_retry/journal.py').read_text()
    node=next(node for node in ast.parse(source).body if isinstance(node,ast.FunctionDef) and node.name=='reassemble')
    assert re.fullmatch('[0-9a-f]{64}',tag) and 1<=rows<=22000
    code='import json,subprocess,hashlib,glob,time\nfrom pathlib import Path\n'+ast.get_source_segment(source,node)+'\n'
    code+='tag='+repr(tag)+'\nlimit='+repr(rows)+'\n'+'''
state=dict(line.split('=',1) for line in subprocess.check_output(['systemctl','show','family-connect-restricted-bootstrap.service','-p','MainPID,InvocationID,ActiveState'],text=True).splitlines())
assert state['ActiveState']=='active'
paths=glob.glob('/var/log/journal/*/system.journal');assert len(paths)==1
raw=subprocess.check_output(['journalctl','--file='+paths[0],'--no-pager','--all','-n',str(limit),'-o','json'],timeout=20)
assert len(raw)<96*1024*1024
allrows=[json.loads(line) for line in raw.splitlines()]
selected=[json.dumps(row) for row in allrows if row.get('_SYSTEMD_UNIT')=='family-connect-restricted-bootstrap.service']
records,errors=reassemble(selected)
profiles=[];latest=None;failures=[];active={}
for row in records:
 try: message=json.loads(row.get('MESSAGE',''))
 except (ValueError,TypeError): continue
 diagnostic=message.get('diagnostic',{})
 if row.get('_SYSTEMD_INVOCATION_ID')==state['InvocationID']:
  if message.get('event')=='session_profile':active[diagnostic.get('session_tag')]=row['__REALTIME_TIMESTAMP']
  elif message.get('event')=='session_terminal':active.pop(diagnostic.get('session_tag'),None)
 if message.get('event') in ('session_profile','session_terminal') and diagnostic.get('session_tag')==tag:
  profiles.append(dict(at=row['__REALTIME_TIMESTAMP'],invocation=row.get('_SYSTEMD_INVOCATION_ID'),**message))
 trace=message.get('trace',{})
 if message.get('event')=='restricted_trace' and trace.get('session_tag')==tag:
  latest=dict(at=row['__REALTIME_TIMESTAMP'],**trace)
  if trace.get('state') in ('FAILED','CLOSED'): failures.append(latest)
root=Path('/opt/apps/family_connect/friends-restricted')
flags={name:(root/'diag67'/name).read_text().strip() if (root/'diag67'/name).exists() else None for name in ('speed-profile','speed-target','rtp-pacing','mux-profile','mux-counters')}
print(json.dumps(dict(active_session_tags=active,epoch=time.time(),state=state,binary_sha256=hashlib.sha256((Path('/proc')/state['MainPID']/'exe').read_bytes()).hexdigest(),profile_sha256=hashlib.sha256((root/'gateway.json').read_bytes()).hexdigest(),operator=flags,records=profiles,latest=latest,failures=failures[-32:],parser_errors=errors,coverage_first=allrows[0]['__REALTIME_TIMESTAMP'],coverage_last=allrows[-1]['__REALTIME_TIMESTAMP'],input_rows=len(allrows))))
'''
    result=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','root@186.246.45.246','python3 -B -'],input=code,text=True,capture_output=True,timeout=40)
    if result.returncode or len(result.stdout)>2*1024*1024:raise RuntimeError('Bounded gateway observation failed')
    return json.loads(result.stdout)


def main():
    os.umask(0o077);parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('label');parser.add_argument('--tag');parser.add_argument('--rows',type=int,default=6000)
    args=parser.parse_args();assert re.fullmatch('[a-zA-Z0-9-]+',args.label)
    phone=snapshot('31ce63ba');save(WORK/(args.label+'-phone.json'),phone)
    tag=args.tag or phone['restricted_session'].get('session_tag');assert tag,'No current session tag; no invented gateway match'
    gateway=remote_observation(tag,args.rows);save(WORK/(args.label+'-gateway.json'),gateway)
    print(json.dumps(dict(state=phone['state'],tag=tag,version=phone['version_code'],phone={k:phone['restricted_session'].get(k) for k in ('speed_profile','reliable_limits','mux_profile','protocol_errors','terminal_reason','mux_lifecycle')},gateway_records=[dict(event=r['event'],**{k:r['diagnostic'].get(k) for k in ('speed_profile','reliable_limits','mux_profile','protocol_errors','terminal_reason')}) for r in gateway['records']],gateway_errors=gateway['parser_errors'])))


if __name__=='__main__':main()
