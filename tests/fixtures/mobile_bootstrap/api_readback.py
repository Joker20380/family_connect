"""Read-only server projection: alias lookup, bounded receipts, source paths; no secrets."""
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess

root = Path('/opt/apps/family_connect')
connection = sqlite3.connect('file:' + str(root / 'friends-access/access.db') + '?mode=ro', uri=True)
connection.row_factory = sqlite3.Row
row = connection.execute('SELECT device,app_version,version_code,last_seen FROM device_support WHERE support_id=?', ('FC-ZMVK-MM7C',)).fetchone()
result = dict(support='FC-ZMVK-MM7C', found=row is not None, receipts=[])
if row:
    result['observed_version'] = {key: row[key] for key in ('app_version','version_code','last_seen')}
    for record in connection.execute('SELECT correlation,challenge_at,fetch_id,fetch_at,revision,minimum_crl,expires,ack,ack_at FROM restricted_readiness_results WHERE device=? ORDER BY challenge_at DESC LIMIT 16', (row['device'],)):
        safe = dict(record)
        raw = safe.pop('ack')
        if raw:
            value = json.loads(raw)
            safe['ack'] = {key: value.get(key) for key in ('result','observed_at','phase','expires_at','version_code','failure_reason')}
        result['receipts'].append(safe)
unit = 'family-connect-friends-http-candidate.service'
result['state'] = subprocess.check_output(['systemctl','show',unit,'-p','MainPID,InvocationID,ActiveState,ExecStart,WorkingDirectory'],text=True).splitlines()
result['nginx_readiness_paths'] = []
for path in (root / 'state-product-https/config').rglob('*'):
    if path.is_file() and path.stat().st_size < 100000:
        result['nginx_readiness_paths'] += [line.strip() for line in path.read_text().splitlines() if any(term in line for term in ('8443','access_log','probe','restricted-readiness','proxy_pass'))]
print(json.dumps(result, indent=2))
