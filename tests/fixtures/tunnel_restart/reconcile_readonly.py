"""Validate the current committed renewal and retained start intent, without writes."""

import json
import os
import subprocess

from preserve import WORK

REMOTE = r'''
import datetime,json,sys,traceback
from pathlib import Path
root=Path('/opt/apps/family_connect/friends-restricted')
sys.path.insert(0,str(root/'renewal'))
from node import construct
from credential_renewal import parse,read_private
node,source=construct(root/'renewal/node.json')
owner=parse(read_private(node.state/'owner.json'))
operation='scheduled-1792429318-4cbbcf5dda81698b'
assert owner['operation_id']==operation
result=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_sha256=source,owner_state=owner['state'],first_cause=owner.get('first_cause'))
result['readback']=node.readback(operation)
result['reconciliation']=parse(read_private(node.state/'reconciliation.json'))
result['services_before']=parse(read_private(node.state/'services-before.json'))
result['start_intents']={path.name:parse(read_private(path)) for path in node.state.glob('start-intent-*.json')}
result['current_states']={unit:node.barrier.state(unit) for unit in result['services_before']}
if node.role=='RU':
 from runtime_controller import LocalNode
 from production_transport import SshNode
 config=parse(read_private(root/'renewal/controller.json'))
 remote=SshNode('NL',config['nl_source_sha256'],forced=config['ssh'])
 try: result['forced_nl_readback']=remote.call('readback',operation)
 except Exception as error:result['forced_error']=dict(type=type(error).__name__,frames=[dict(file=frame.filename.rsplit('/',1)[-1],line=frame.lineno,function=frame.name) for frame in traceback.extract_tb(error.__traceback__)])
print(json.dumps(result))
'''


if __name__ == '__main__':
    os.umask(0o077)
    for role, host in [('NL', '186.246.45.246'), ('RU', '185.251.89.19')]:
        with (WORK / (role + '-reconcile-readonly.json')).open('xb') as stdout, (WORK / (role + '-reconcile-readonly.stderr')).open('xb') as stderr:
            response = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=8', 'root@' + host,
                '/opt/apps/family_connect/friends-access/venv/bin/python -B -'], input=REMOTE.encode(), stdout=stdout, stderr=stderr, timeout=145)
        print(json.dumps(dict(role=role,exit=response.returncode)))
