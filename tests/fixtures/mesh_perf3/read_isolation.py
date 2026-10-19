import hashlib
import json
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[3]
output = root / 'state-client-build/mesh-perf-3/receipts/isolation-readback.json'
assert not output.exists()
remote = r'''
import datetime,hashlib,json
from pathlib import Path
import zipfile
path=Path('/opt/apps/family_connect/friends-access/friends-http.pyz')
with zipfile.ZipFile(path) as archive:
    source=archive.read('control/friends/restricted.py')
text=source.decode()
print(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),archive_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),module_sha256=hashlib.sha256(source).hexdigest(),global_directory_lambda="seed_source=lambda: bounded_file(root / 'directory.json', 8192)" in text,seed_fetch_without_device_argument='directory(self.seed_source(),' in text)))
'''
command = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', 'root@185.251.89.19', "python3 - <<'PY'\n" + remote + '\nPY']
try:
    result = subprocess.run(command, capture_output=True, text=True, timeout=20)
    record = dict(exit=result.returncode)
    if result.returncode == 0:
        record['remote'] = json.loads(result.stdout)
        preserved = root / 'state-client-build/field65-export16/restricted-canary-identity-policy-1/baseline-api/control/friends/restricted.py'
        record['matches_preserved_api_module'] = record['remote']['module_sha256'] == hashlib.sha256(preserved.read_bytes()).hexdigest()
    else:
        record['error_class'] = 'SSH_UNAVAILABLE'
except subprocess.TimeoutExpired:
    record = dict(error_class='SSH_TIMEOUT')
with output.open('x') as handle:
    json.dump(record, handle, indent=2)
print(json.dumps(record, indent=2))
