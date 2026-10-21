"""Copy sealed accepted sources without mutating historical build inputs."""

import hashlib
import json
import os
import shutil
import subprocess
import sys

from preserve import ROOT, WORK, digest


def main():
    os.umask(0o077)
    state = ROOT / 'state-client-build'
    gateway = state / 'transport-write-batching-1'
    manifest = json.loads((gateway / 'gateway-source.json').read_text())
    assert manifest['source_inventory'] == 'aeeb6755bd235160127cfed67da4a870ae340cfebe89fc6d0f937908607d9483'
    assert all(digest(gateway / 'gateway-source/carrier' / name) == value for name, value in manifest['files'].items())
    android = state / 'beta87-product-fix-20261019'
    inventory = json.loads((android / 'android88-build/source-inventory.json').read_text())
    assert all(digest(android / 'android88-source' / name) == value for name, value in inventory.items())
    assert digest(android / 'delivery/FamilyConnect-0.1.18-beta88-recovery.apk') == '968a61724f4e71ac0335e330960eb9b54e5ede59bae81df0b6e8499e4ce6c2ce'
    observed = state / 'mesh-throughput-trace-20261019'
    assert digest(observed / 'delivery/FamilyConnect-0.1.18-beta89-mesh-trace.apk') == 'b6ab744740726676dca8f51a73460db82b435c719828af14e6564c764ed11856'
    shutil.copytree(gateway / 'gateway-source', WORK / 'gateway-source')
    (WORK / 'gateway-source/tests/vectors').mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / 'tests/vectors/bootstrap-timestamps.json', WORK / 'gateway-source/tests/vectors/bootstrap-timestamps.json')
    shutil.copytree(android / 'android88-source', WORK / 'android-source', ignore=shutil.ignore_patterns('.gradle', '__pycache__'))
    (WORK / 'source-inputs.json').write_text(json.dumps(dict(gateway=manifest, android88=inventory,
        android89_build=json.loads((observed / 'build/receipt.json').read_text())), indent=2))
    if '--apply' in sys.argv:
        fixture = ROOT / 'tests/fixtures/tunnel_restart'
        pins = json.loads((fixture / 'source-pins.json').read_text())
        for role, destination in [('gateway', WORK / 'gateway-source'), ('android', WORK / 'android-source')]:
            pin = pins[role]
            patch = fixture / pin['patch']
            assert digest(patch) == pin['sha256']
            assert all((digest(destination / name) if (destination / name).exists() else None) == value for name, value in pin['inputs'].items())
            for check in (True, False):
                subprocess.run(['patch', '-p1', '--fuzz=0', *(['--dry-run'] if check else []), '-i', str(patch)], cwd=destination, check=True, stdout=subprocess.DEVNULL)
            assert all(digest(destination / name) == value for name, value in pin['outputs'].items())
    print('SEALED_ACCEPTED_SOURCES_COPIED')


if __name__ == '__main__':
    main()
