"""Apply the sealed Android-only overlay once to exact beta88, retaining recovery."""

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
    parent = STATE / 'beta87-product-fix-20261019/android88-source'
    inventory = json.loads((parent.parent / 'android88-build/source-inventory.json').read_text())
    assert all(digest(parent / name) == value for name, value in inventory.items())
    pins = json.loads(Path(__file__).with_name('source-inputs.json').read_text())['android']
    patch = Path(__file__).with_name('android-trace.patch')
    assert digest(patch) == pins['patch_sha256']
    assert all((digest(parent / name) if (parent / name).exists() else None) == value for name, value in pins['inputs'].items())
    destination = OUT / 'android-source'
    assert not destination.exists()
    shutil.copytree(parent, destination, ignore=shutil.ignore_patterns('.gradle', '__pycache__'))
    for check in (True, False):
        subprocess.run(['patch', '-p1', '--fuzz=0', *(['--dry-run'] if check else []), '-i', str(patch)],
                       cwd=destination, check=True, stdout=subprocess.DEVNULL)
    assert all(digest(destination / name) == value for name, value in pins['outputs'].items())
    with (OUT / 'android-inputs.json').open('x') as handle:
        json.dump(dict(parent_inventory=inventory, overlay=pins), handle, indent=2)
    print(json.dumps(dict(result='BETA88_EXACT_OVERLAY_VERIFIED', changed=len(pins['inputs']))))


if __name__ == '__main__':
    main()
