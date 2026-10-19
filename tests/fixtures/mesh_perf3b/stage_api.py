import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


ROOT = Path(__file__).resolve().parents[3]
STATE = ROOT / 'state-client-build/mesh-perf-3b'
STAGE = '/opt/apps/family_connect/friends-access/mesh-perf-3b-20261018-01'
HOST = 'root@185.251.89.19'
os.umask(0o077)


def save(path, value):
    with path.open('x') as handle:
        json.dump(value, handle, indent=2)
        handle.flush()
        os.fsync(handle.fileno())


def main():
    config = json.loads((STATE / 'receipts/owner-continuation-preflight-v4.json').read_bytes())
    config.update(operation='mesh-perf-3b-20261018-01', deadline=int(datetime.datetime(2026, 10, 18, 16, 55, tzinfo=datetime.timezone.utc).timestamp()))
    assert int(time.time()) + 3600 < config['deadline']
    local = STATE / 'api-operation'
    local.mkdir(mode=0o700)
    save(local / 'operation.json', config)
    files = [local/'operation.json', STATE/'friends-http-owner-candidate.pyz', ROOT/'tests/fixtures/mesh_perf3b/live_operator.py']
    expected = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in files}
    save(local / 'stage-intent.json', dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), stage=STAGE, files=expected))
    ssh = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', HOST]
    subprocess.run(ssh + ['mkdir', '-m', '700', STAGE], check=True, timeout=20)
    subprocess.run(['scp', '-q', '-o', 'BatchMode=yes', *map(str, files), HOST+':'+STAGE+'/'], check=True, timeout=30)
    check = subprocess.check_output(ssh + ['sha256sum', *[STAGE+'/'+name for name in expected]], text=True, timeout=20)
    actual = {Path(line.split()[1]).name: line.split()[0] for line in check.splitlines()}
    assert actual == expected
    save(local/'stage-receipt.json', dict(files=actual, hash_check='PASS', runtime_changed=False))
    result = subprocess.run(ssh + ['/opt/apps/family_connect/friends-access/venv/bin/python', '-I', '-B',
                            STAGE+'/live_operator.py', 'prepare-api', '--stage', STAGE], capture_output=True, text=True, timeout=75)
    (local/'prepare.stderr').write_text(result.stderr)
    if result.returncode:
        save(local/'prepare-outcome.json', dict(exit=result.returncode, result='READBACK_REQUIRED_NO_AUTOMATIC_RETRY'))
        raise RuntimeError('API_PREPARE_FAILED_OR_UNCERTAIN; reconcile remotely, never replay')
    receipt = json.loads(result.stdout)
    save(local/'prepare-outcome.json', receipt)
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
