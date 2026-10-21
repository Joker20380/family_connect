"""Publish only input-hashed source overlays, never private runtime materials."""

import difflib
import hashlib
import json
import subprocess

from preserve import ROOT, WORK, digest


def add(path, text):
    assert not path.exists()
    relative = str(path.relative_to(ROOT))
    patch = '*** Begin Patch\n*** Add File: ' + relative + '\n' + ''.join('+' + line + '\n' for line in text.splitlines()) + '*** End Patch\n'
    subprocess.run(['apply_patch', patch], cwd=ROOT, check=True)


def main():
    fixtures = ROOT / 'tests/fixtures/tunnel_restart'
    pins = {}
    for role, parent, destination, names in [
        ('gateway', ROOT / 'state-client-build/transport-write-batching-1/gateway-source', WORK / 'gateway-source',
         ['carrier/cmd/bootstrap-broker/main.go', 'carrier/cmd/bootstrap-broker/seed_recovery.go', 'carrier/cmd/bootstrap-broker/seed_recovery_test.go']),
        ('android', ROOT / 'state-client-build/beta87-product-fix-20261019/android88-source', WORK / 'android-source',
         ['clients/android/app/build.gradle'])]:
        patch, inputs, outputs = '', {}, {}
        for name in names:
            before, after = parent / name, destination / name
            inputs[name] = digest(before) if before.exists() else None
            outputs[name] = digest(after)
            patch += ''.join(difflib.unified_diff(before.read_text().splitlines(True) if before.exists() else [],
                after.read_text().splitlines(True), fromfile='a/' + name if before.exists() else '/dev/null', tofile='b/' + name))
        filename = role + '.patch'
        add(fixtures / filename, patch)
        pins[role] = dict(patch=filename, sha256=hashlib.sha256(patch.encode()).hexdigest(), inputs=inputs, outputs=outputs)
    pins['gateway']['accepted_inventory'] = 'aeeb6755bd235160127cfed67da4a870ae340cfebe89fc6d0f937908607d9483'
    pins['gateway']['candidate_inventory'] = json.loads((WORK / 'gateway-build.json').read_text())['source_inventory']
    pins['android']['ancestry'] = 'sealed beta88 recovery, normal upgrade over beta89; no extended performance instrumentation'
    add(fixtures / 'source-pins.json', json.dumps(pins, indent=2) + '\n')


if __name__ == '__main__':
    main()
