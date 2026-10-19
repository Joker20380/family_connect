"""Create an exclusive exact accepted-source workspace, never patch installed trees."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[3]
STATE = ROOT / 'state-client-build'
OUT = Path(os.environ.get('MESH_TRACE_OUT', STATE / 'mesh-throughput-trace-20261019'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    os.umask(0o077)
    accepted = STATE / 'transport-write-batching-1/gateway-source/carrier'
    manifest = json.loads((accepted.parent.parent / 'gateway-source.json').read_text())
    assert all(digest(accepted / name) == value for name, value in manifest['files'].items())
    destination = OUT / 'source/carrier'
    assert not destination.exists()
    shutil.copytree(accepted, destination)
    overlay = ROOT / 'tests/fixtures/mesh_perf3/accepted-overlay.patch'
    subprocess.run(['patch', '-p1', '--dry-run', '-i', str(overlay)], cwd=destination, check=True, stdout=subprocess.DEVNULL)
    subprocess.run(['patch', '-p1', '-i', str(overlay)], cwd=destination, check=True, stdout=subprocess.DEVNULL)
    files = {str(path.relative_to(destination)): digest(path) for path in destination.rglob('*') if path.is_file()}
    inventory = hashlib.sha256(json.dumps(files, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    assert inventory == 'bc3721ec8c30c6fb304c478b22398926fe3bfc0c576216c49ed53809d78c3051'
    (OUT / 'receipts').mkdir(mode=0o700, exist_ok=True)
    with (OUT / 'observation-input.json').open('x') as handle:
        json.dump(dict(inventory=inventory, overlay_sha256=digest(overlay), files=files), handle, indent=2)
    trace = Path(__file__).with_name('receiver-trace.patch')
    pins = json.loads(Path(__file__).with_name('source-inputs.json').read_text())['gateway']
    assert digest(trace) == pins['patch_sha256']
    assert all((digest(destination / name) if (destination / name).exists() else None) == value for name, value in pins['inputs'].items())
    for check in (True, False):
        subprocess.run(['patch', '-p1', '--fuzz=0', *(['--dry-run'] if check else []), '-i', str(trace)], cwd=destination, check=True, stdout=subprocess.DEVNULL)
    assert all(digest(destination / name) == value for name, value in pins['outputs'].items())
    print(json.dumps(dict(result='EXACT_OBSERVATION_REPRODUCED', inventory=inventory)))


if __name__ == '__main__':
    main()
