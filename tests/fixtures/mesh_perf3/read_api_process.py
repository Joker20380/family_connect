import json
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[3]
target = root / 'state-client-build/mesh-perf-3/receipts/api-process-readback.json'
assert not target.exists()
remote = r'''
import datetime,hashlib,json,subprocess,zipfile
from pathlib import Path
units=json.loads(subprocess.check_output(['systemctl','list-units','--all','--type=service','--output=json','--no-pager','family-connect*'],text=True))
rows=[]
for unit in units:
    name=unit['unit']
    if 'friends' not in name:continue
    pid=subprocess.check_output(['systemctl','show',name,'--property=MainPID','--value'],text=True).strip()
    if pid=='0':continue
    paths=[Path(value.decode()) for value in (Path('/proc')/pid/'cmdline').read_bytes().split(b'\0') if value.endswith(b'.pyz') and value.startswith(b'/opt/apps/family_connect/')]
    for path in paths:
        with zipfile.ZipFile(path) as archive:
            if 'control/friends/restricted.py' not in archive.namelist():continue
            source=archive.read('control/friends/restricted.py')
        text=source.decode()
        rows.append(dict(unit=name,pid=pid,archive_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),module_sha256=hashlib.sha256(source).hexdigest(),global_directory_lambda="seed_source=lambda: bounded_file(root / 'directory.json', 8192)" in text,seed_fetch_without_device_argument='directory(self.seed_source(),' in text))
print(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),process_archives=rows)))
'''
try:
    result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', 'root@185.251.89.19', "python3 - <<'PY'\n"+remote+'\nPY'], capture_output=True, text=True, timeout=30)
    record = json.loads(result.stdout) if result.returncode == 0 else dict(error='SSH_READ_FAILED', exit=result.returncode)
except subprocess.TimeoutExpired:
    record = dict(error='SSH_TIMEOUT')
with target.open('x') as handle:
    json.dump(record, handle, indent=2)
print(json.dumps(record, indent=2))
