import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[3]
STATE = ROOT / 'state-client-build/mesh-perf-3b'
os.umask(0o077)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    destination = STATE / 'receipts' / sys.argv[1]
    assert destination.parent == STATE / 'receipts' and not destination.exists()
    seal = json.loads((STATE / 'receipts/seal.json').read_bytes())
    assert sha(STATE / 'friends-http-owner-candidate.pyz') == seal['api_candidate_sha256']
    assert sha(STATE / 'diagnostic-broker-owner-final') == seal['owner_candidate_sha256']
    assert sha(ROOT / 'tests/fixtures/mesh_perf3b/api-overlay.patch') == seal['api_overlay_sha256']
    assert sha(ROOT / 'tests/fixtures/mesh_perf3b/gateway-owner-overlay.patch') == seal['gateway_delta_sha256']
    for name, digest in seal['receipts'].items():
        assert sha(STATE / 'receipts' / name) == digest, name
    code = r'''
import base64, datetime, hashlib, json, os, sqlite3, subprocess, sys, time
from pathlib import Path
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
unit='family-connect-friends-http-candidate.service'
state=dict(line.split('=',1) for line in subprocess.check_output(['systemctl','show',unit,'--property=MainPID,InvocationID,ActiveState,SubState,NRestarts'],text=True).splitlines())
assert state['ActiveState']=='active' and state['NRestarts']=='0'
process=Path('/proc')/state['MainPID']
args=[value.decode() for value in (process/'cmdline').read_bytes().split(b'\0') if value]
archive,=[Path(arg) for arg in args if arg.endswith('.pyz')]
assert sha(archive)=='12ca0c72a89ff20c1b3c70a1182a2d5d98d4d78d25e7a079bb4d75bdf34060ed'
environment=dict(item.decode().split('=',1) for item in (process/'environ').read_bytes().split(b'\0') if item)
material=Path(environment['FC_FRIENDS_RESTRICTED_DIR'])
database=(Path(args[args.index('--root')+1]) if '--root' in args else Path('/opt/apps/family_connect/friends-access'))/'access.db'
sys.path.insert(0,str(archive))
os.environ['FC_FRIENDS_RESTRICTED_DIR']=str(material)
os.environ['FC_FRIENDS_RESTRICTED_DELIVERY_LIFETIME']=environment['FC_FRIENDS_RESTRICTED_DELIVERY_LIFETIME']
from control.friends.access import Access
from control.friends.restricted import from_env, directory
service=from_env(Access(database))
assert service.eligible_devices is not None and '*' not in service.eligible_devices
now=int(time.time())
trust,authority,crl,crl_pem,crl_number=service._trust(now)
connection=sqlite3.connect('file:'+str(database)+'?mode=ro',uri=True)
connection.row_factory=sqlite3.Row
observed=[]
for selected in service.eligible_devices:
    recent=connection.execute('SELECT ack FROM restricted_readiness_results WHERE device=? AND ack IS NOT NULL ORDER BY ack_at DESC LIMIT 1',(selected,)).fetchone()
    if recent:
        value=json.loads(recent['ack'])
        if value['result']=='READY' and value['version_code']==84 and value['app_version']=='0.1.18-research84-ui60-4-batch1':observed.append(selected)
assert len(observed)==1, 'EXACT_ACCEPTED_UI84_IDENTITY_NOT_UNIQUE'
owner,=observed
grant=service._grant(connection,owner,now)
identity=base64.b64decode(grant['public'],validate=True)
assert len(identity)==64 and hashlib.sha256(identity).hexdigest()[:32]==owner
last=connection.execute('SELECT fetch_at,ack,ack_at FROM restricted_readiness_results WHERE device=? AND ack IS NOT NULL ORDER BY ack_at DESC LIMIT 1',(owner,)).fetchone()
assert last is not None
ack=json.loads(last['ack'])
assert ack['result']=='READY' and ack['version_code']==84 and ack['app_version']=='0.1.18-research84-ui60-4-batch1'
exists=connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='restricted_owner_handoff'").fetchone()
if exists is not None:
    rows=connection.execute('SELECT operation,phase,canary,return_view FROM restricted_owner_handoff').fetchall()
    assert len(rows)==1 and rows[0]['operation']=='mesh-perf-3b-20261018-01'
    assert rows[0]['phase']=='CLEANED' and rows[0]['canary'] is None and rows[0]['return_view'] is None
raw=(material/'directory.json').read_bytes()
view=directory(raw,trust['family'],trust['gateway'],now=now)
config_path=material/'renewal/controller.json'
controller=json.loads(config_path.read_bytes())
node=json.loads(Path(controller['node_config']).read_bytes())
assert sha(Path(node['api_archive']))==node['api_sha256']
deadline=min(int(authority.not_valid_after_utc.timestamp()),int(crl.next_update_utc.timestamp()),trust['expires_at'],grant['expires'] or trust['expires_at'])
result=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),state=state,archive=str(archive),archive_sha256=sha(archive),database=str(database),material=str(material),args=args,
    admitted_owner_verified=True,admitted_device_count=len(service.eligible_devices),accepted_ui84_identity_count=len(observed),owner_ack_at=last['ack_at'],owner_fetch_at=last['fetch_at'],owner_ack_build=ack['version_code'],owner_ack_result=ack['result'],
    directory_sha256=sha(material/'directory.json'),directory_issued_at=view['issued_at'],directory_expires_at=view['expires_at'],minimum_crl=crl_number,
    authority_sequence=trust['sequence'],grant_revision=grant['revision'],minimum_validity_headroom_seconds=deadline-now,
    renewal_validator_archive_is_current_api=Path(node['api_archive'])==archive,renewal_validator_sha256=node['api_sha256'],handoff_table_absent=exists is None,previous_operation_cleaned=exists is not None,
    owner_guard_identity=dict(family=trust['family'],device=owner,public_key=identity[32:].hex()))
print(json.dumps(result))
'''
    command = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', 'root@185.251.89.19',
               "/opt/apps/family_connect/friends-access/venv/bin/python -I -B - <<'PY'\n" + code + '\nPY']
    result = subprocess.run(command, capture_output=True, text=True, timeout=40)
    if result.returncode:
        destination.with_suffix('.error.txt').write_text(result.stderr)
        raise RuntimeError('READ_ONLY_PREFLIGHT_FAILED; private error preserved')
    record = json.loads(result.stdout)
    record['local_seal_receipts_rechecked'] = len(seal['receipts'])
    record['local_candidate_hashes_match'] = True
    with destination.open('x') as handle:
        json.dump(record, handle, indent=2)
        handle.flush()
        os.fsync(handle.fileno())
    visible = {name: value for name, value in record.items() if name not in ('owner_guard_identity', 'args', 'database', 'material')}
    print(json.dumps(visible, indent=2))


if __name__ == '__main__':
    main()
