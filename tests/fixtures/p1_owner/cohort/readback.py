import json
import os
from pathlib import Path
import shlex
import subprocess

ROOT = Path(__file__).resolve().parents[4]
WORK = ROOT / 'state-client-build/tester-p1-cohort-20261023'


def main():
    os.umask(0o077)
    target = WORK / 'cohort-identity-readback.json'
    assert not target.exists()
    remote = '''import base64,hashlib,json,sqlite3,time
connection=sqlite3.connect("file:/opt/apps/family_connect/friends-access/access.db?mode=ro",uri=True)
connection.row_factory=sqlite3.Row
connection.execute("PRAGMA query_only=ON")
identifiers=("FC-4D8Q-REEG","FC-ZMVK-MM7C","FC-YHQB-9VJN")
rows=connection.execute("SELECT s.support_id,s.device,s.platform,s.app_version,s.version_code,s.last_seen,s.observation_source,d.public,d.revoked,i.revoked AS invite_revoked FROM device_support s JOIN devices d ON d.device=s.device LEFT JOIN invites i ON i.device=s.device WHERE s.support_id IN (?,?,?)",identifiers).fetchall()
assert len(rows)==3
output=[]
for row in rows:
    value=dict(row)
    encoded=value.pop("public")
    public=base64.urlsafe_b64decode(encoded+"="*(-len(encoded)%4))
    assert len(public)==64 and hashlib.sha256(public).hexdigest()[:32]==value["device"]
    assert value["revoked"]==value["invite_revoked"]==0
    grant=connection.execute("SELECT revoked FROM restricted_grants WHERE device=?",(value["device"],)).fetchone()
    assert grant is None or grant["revoked"]==0
    value["family_signing_key_sha256_128"]=hashlib.sha256(public[32:]).hexdigest()[:32]
    value["key_binding_verified"]=True
    output.append(value)
connection.close()
print(json.dumps(dict(epoch=time.time(),devices=output,read_only=True,public_keys_exported=False)))
'''
    result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
                             '-o', 'ConnectTimeout=8', 'root@185.251.89.19',
                             'python3 -B -c ' + shlex.quote(remote)], capture_output=True, timeout=40)
    target.with_suffix('.stderr').write_bytes(result.stderr)
    result.check_returncode()
    value = json.loads(result.stdout)
    owner = next(row for row in value['devices'] if row['support_id'] == 'FC-4D8Q-REEG')
    assert owner['family_signing_key_sha256_128'] == '3865fd21a391b23ad2b37130f11b8e3e'
    target.write_bytes(result.stdout)
    print(json.dumps(value))


if __name__ == '__main__':
    main()
