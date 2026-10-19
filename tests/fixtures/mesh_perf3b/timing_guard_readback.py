import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[3]
os.umask(0o077)
RU = r'''
import base64, datetime, hashlib, json, sqlite3, subprocess
from pathlib import Path
root=Path('/opt/apps/family_connect/friends-restricted')
envelope=json.loads((root/'issuer.json').read_bytes())
trust=json.loads(base64.b64decode(envelope['payload'],validate=True))
database=sqlite3.connect('file:/opt/apps/family_connect/friends-access/access.db?mode=ro',uri=True)
database.row_factory=sqlite3.Row
rows=database.execute('SELECT operation,phase,deadline,canary,return_view,floor FROM restricted_owner_handoff').fetchall()
summary=[]
for row in rows:
    floor=json.loads(row['floor']) if row['floor'] else None
    summary.append(dict(operation=row['operation'],phase=row['phase'],deadline=row['deadline'],
        canary_absent=row['canary'] is None,return_absent=row['return_view'] is None,
        floor_present=floor is not None,floor_fields=None if floor is None else
        {name:floor[name] for name in ('issued_at','revision','minimum_crl','sequence')},
        directory_floor_issued=None if floor is None else floor['directory']['issued_at']))
grants=database.execute('SELECT MIN(expires),COUNT(*) FROM restricted_grants WHERE revoked=0').fetchone()
print(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    issuer_envelope_sha256=hashlib.sha256((root/'issuer.json').read_bytes()).hexdigest(),
    authority_sequence=trust['sequence'],authority_issued_at=trust['issued_at'],authority_expires_at=trust['expires_at'],
    minimum_active_grant_expiry=grants[0],active_grants=grants[1],handoff_rows=summary,
    api_override_absent=not Path('/etc/systemd/system/family-connect-friends-http-candidate.service.d/97-mesh-perf-3b.conf').exists())))
'''
NL = r'''
import datetime, hashlib, json, subprocess
from pathlib import Path
def run(arguments):
    return subprocess.check_output(arguments,text=True,stderr=subprocess.PIPE,timeout=15)
states={}
for suffix in ('01','02'):
    unit='family-connect-mesh-perf-3b-20261018-'+suffix+'.service'
    states[suffix]=dict(line.split('=',1) for line in run(['systemctl','show',unit,'--property=LoadState,ActiveState,SubState,MainPID,NRestarts,ControlGroup']).splitlines())
listener=run(['ss','-H','-lnt','sport = :18445']).strip()
root=Path('/opt/apps/family_connect/friends-restricted')
print(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    prior_canaries=states,canary_listener_absent=not listener,
    profile_sha256=hashlib.sha256((root/'gateway.json').read_bytes()).hexdigest(),
    directory_sha256=hashlib.sha256((root/'directory.json').read_bytes()).hexdigest())))
'''


def main():
    destination = ROOT / 'state-client-build/mesh-perf-3b/receipts' / sys.argv[1]
    assert destination.parent.name == 'receipts' and not destination.exists()
    records = {}
    for role, host, code in (('RU', '185.251.89.19', RU), ('NL', '186.246.45.246', NL)):
        result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10',
                                 'root@' + host, "python3 - <<'PY'\n" + code + '\nPY'],
                                capture_output=True, text=True, timeout=65)
        if result.returncode:
            destination.with_suffix('.' + role + '.error.txt').write_text(result.stderr)
            raise RuntimeError('READ_ONLY_GUARD_READBACK_FAILED_' + role)
        records[role] = json.loads(result.stdout)
    with destination.open('x') as handle:
        json.dump(records, handle, indent=2)
        handle.flush()
        os.fsync(handle.fileno())
    print(json.dumps(records, indent=2))


if __name__ == '__main__':
    main()
