"""Publish only input-guarded source overlays and safe immutable artifact hashes."""

import difflib
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
WORK = ROOT / 'state-client-build/mesh-throughput-trace-20261019'
HERE = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def overlay(before, after, paths, label):
    delta, inputs, outputs = [], {}, {}
    for name in sorted(paths):
        old, new = before / name, after / name
        old_text, new_text = old.read_text() if old.exists() else '', new.read_text()
        if old_text == new_text:
            continue
        inputs[name] = digest(old) if old.exists() else None
        outputs[name] = digest(new)
        delta.extend(difflib.unified_diff(old_text.splitlines(True), new_text.splitlines(True),
                                        fromfile='a/' + name, tofile='b/' + name))
    path = HERE / (label + '.patch')
    with path.open('x') as handle:
        handle.write(''.join(delta))
    return dict(patch_sha256=digest(path), inputs=inputs, outputs=outputs)


def main():
    baseline = ROOT / 'state-client-build/mesh-perf-3/source/carrier'
    candidate = WORK / 'source/carrier'
    expected = json.loads((WORK / 'observation-input.json').read_text())
    assert all(digest(baseline / name) == checksum for name, checksum in expected['files'].items())
    gateway = overlay(baseline, candidate, [str(path.relative_to(candidate)) for path in candidate.rglob('*.go')], 'receiver-trace')
    android = WORK / 'android-source'
    parent = ROOT / 'state-client-build/beta87-product-fix-20261019/android88-source'
    inventory = json.loads((WORK / 'build/source-inventory.json').read_text())
    assert all(digest(android / name) == checksum for name, checksum in inventory.items())
    client = overlay(parent, android, inventory, 'android-trace')
    record = dict(base_checkpoint='76df691961aa88a46b73e7a355687fa6f9a3c457',
        gateway_input_inventory=expected['inventory'], gateway=gateway, android=client,
        build_receipt_sha256=digest(WORK / 'build/receipt.json'),
        signing_receipt_sha256=digest(WORK / 'delivery/signing-receipt.json'),
        installed_apk_sha256='b6ab744740726676dca8f51a73460db82b435c719828af14e6564c764ed11856',
        native_sha256='3ca3119ac12c9a3a61b5ebb1ee0244650db39dc36743e355d35bf523b53ef992',
        gateway_sha256=digest(WORK / 'gateway-trace-final'),
        android_delta_inventory=json.loads((WORK / 'build/receipt.json').read_text())['source_inventory'])
    with (HERE / 'source-inputs.json').open('x') as handle:
        json.dump(record, handle, indent=2)
    print(json.dumps(dict(gateway_files=len(gateway['inputs']), android_files=len(client['inputs']), gateway_patch=gateway['patch_sha256'], android_patch=client['patch_sha256'])))


if __name__ == '__main__':
    main()
