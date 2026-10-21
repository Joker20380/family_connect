"""One explicit forward reconciliation of the already committed 17:02 renewal.

No new bundle, rollback, security-floor edit, history deletion or candidate deploy.
"""

import json
import os
import select
import subprocess

from preserve import WORK

OPERATION = 'scheduled-1792429318-4cbbcf5dda81698b'
COMMON = r'''
import datetime,json,sys
from pathlib import Path
root=Path('/opt/apps/family_connect/friends-restricted')
sys.path.insert(0,str(root/'renewal'))
from node import construct
from credential_renewal import parse,read_private,canonical,atomic
operation='scheduled-1792429318-4cbbcf5dda81698b'
node,source=construct(root/'renewal/node.json')
audit=root/'renewal-reconcile-20261019'
audit.mkdir(mode=0o700,exist_ok=False)
'''
RU = COMMON + r'''
from runtime_controller import LocalNode
from production_transport import SshNode
from production_controller import ProductionController
config=parse(read_private(root/'renewal/controller.json'))
nodes={'RU':LocalNode(node,source),'NL':SshNode('NL',config['nl_source_sha256'],forced=config['ssh'])}
controller=ProductionController(Path(config['coordinator_state']),nodes,node.validator)
with controller.operation.lock():
 record=parse(read_private(controller.root/'transaction.json'))
 assert record['operation_id']==operation and record['commit_decided'] and record['state']=='RECOVERY_REQUIRED'
 readbacks={role:peer.call('readback',operation) for role,peer in nodes.items()}
 assert readbacks==record['reconciliation'] and readbacks['RU']==readbacks['NL']
 atomic(audit/'intent.json',canonical(dict(operation=operation,action='FORWARD_CURRENT_COMMITTED_ONLY',readbacks=readbacks)))
 print(json.dumps(dict(result='LOCKED_COMMITTED_EQUAL',operation=operation)),flush=True)
 import select
 assert select.select([sys.stdin],[],[],180)[0] and sys.stdin.readline().strip()=='NL_CURRENT_STARTED'
 result=controller.recover(record)
 atomic(audit/'result.json',canonical(result))
 print(json.dumps(result),flush=True)
 assert result['result']=='COMMITTED'
'''
NL = COMMON + r'''
import hashlib,subprocess
from cryptography import x509
unit='family-connect-restricted-bootstrap.service'
binary=root/'bin/bootstrap-broker-signal-observation-20261012'
expected='4b722d2d7f2159b96953e27777494bf596768f860ee8da7e634fb1100b08fab7'
digest=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
with node.operation.lock():
 owner=node.owner(operation)
 assert owner['state']=='RESUMED'
 local=node.readback(operation)
 assert all(value==local for value in parse(read_private(node.state/'reconciliation.json')).values())
 before=parse(read_private(node.state/'services-before.json'))
 intent=parse(read_private(node.state/'start-intent-0.json'))
 assert set(before)=={unit} and before[unit]['ActiveState'] in ('active','activating') and intent['unit']==unit
 state=node.barrier.state(unit)
 assert state['ActiveState']=='inactive' and state['MainPID']=='0' and digest(binary)==expected
 profile=parse(node.read('gateway.json')[0])
 ca=x509.load_pem_x509_certificate(profile['authority'].encode())
 leaf=x509.load_pem_x509_certificate(profile['certificate'].encode())
 crl=x509.load_pem_x509_crl(profile['revocations'].encode())
 leaf.verify_directly_issued_by(ca);assert crl.is_signature_valid(ca.public_key())
 now=datetime.datetime.now(datetime.UTC)
 assert ca.not_valid_before_utc<=now and leaf.not_valid_before_utc<=now and crl.last_update_utc<=now
 assert min((expiry-now).total_seconds() for expiry in (ca.not_valid_after_utc,leaf.not_valid_after_utc,crl.next_update_utc))>1800
 atomic(audit/'intent.json',canonical(dict(operation=operation,action='RECONCILE_RETAINED_START_INTENT',before=state,loaded_target=expected,readback=local)))
 node.barrier.invoke('start',unit)
 after=node.barrier.state(unit)
 assert after['ActiveState']=='active' and after['MainPID']!='0'
 assert digest(Path('/proc/'+after['MainPID']+'/exe'))==expected
 assert node.readback(operation)==local
 result=dict(result='CURRENT_COMMITTED_GATEWAY_STARTED',operation=operation,state=after,binary_sha256=expected)
 atomic(audit/'result.json',canonical(result))
 print(json.dumps(result),flush=True)
'''


def main():
    os.umask(0o077)
    target = WORK / 'forward-current-renewal.jsonl'
    assert not target.exists(), 'Reconcile existing outcome; never blindly repeat'
    import shlex
    with target.open('xb') as receipt, (WORK / 'forward-current-renewal.stderr').open('xb') as error:
        base = ['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=8']
        command = '/opt/apps/family_connect/friends-access/venv/bin/python -B -c '
        controller = subprocess.Popen(base + ['root@185.251.89.19', command + shlex.quote(RU)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=error)
        try:
            assert select.select([controller.stdout], [], [], 140)[0], 'Coordinator lock response unknown'
            ready = controller.stdout.readline(); receipt.write(ready); receipt.flush()
            assert json.loads(ready)['result'] == 'LOCKED_COMMITTED_EQUAL'
            remote = subprocess.run(base + ['root@186.246.45.246', command + shlex.quote(NL)], capture_output=True, timeout=90)
            receipt.write(remote.stdout); receipt.flush(); error.write(remote.stderr)
            assert remote.returncode == 0 and json.loads(remote.stdout)['result'] == 'CURRENT_COMMITTED_GATEWAY_STARTED'
            controller.stdin.write(b'NL_CURRENT_STARTED\n'); controller.stdin.flush()
            result, _ = controller.communicate(timeout=360)
            receipt.write(result); receipt.flush()
            assert controller.returncode == 0
            print(result.decode().strip())
        finally:
            if controller.poll() is None:
                controller.stdin.close()
                controller.wait(timeout=180)


if __name__ == '__main__':
    main()
