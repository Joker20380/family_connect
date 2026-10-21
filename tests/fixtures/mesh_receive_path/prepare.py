"""Apply only hash-pinned observation deltas to fresh beta90/b9 copies."""

import json
import os
import re
import shutil
import subprocess

from preserve import ROOT, WORK, PARENT, digest


def apply(target, patch):
    for dry in (True, False):
        subprocess.run(['patch', '-p1', '--fuzz=0', *(['--dry-run'] if dry else []), '-i', str(patch)],
                       cwd=target, check=True, stdout=subprocess.DEVNULL)


def main():
    os.umask(0o077)
    inputs = json.loads((ROOT / 'tests/fixtures/mesh_throughput_trace/source-inputs.json').read_text())
    gateway = WORK / 'gateway-source'
    android = WORK / 'android-source'
    assert not gateway.exists() and not android.exists()
    shutil.copytree(PARENT / 'gateway-source', gateway)
    shutil.copytree(PARENT / 'android-source', android, ignore=shutil.ignore_patterns('.gradle', '__pycache__'))
    for patch, expected in ((ROOT / 'tests/fixtures/mesh_perf3/accepted-overlay.patch', '4a32c5e04ffa903791ff30abe80eca6103238f1d2365e9c64d7afc6076f2911c'),
                            (ROOT / 'tests/fixtures/mesh_throughput_trace/receiver-trace.patch', '4f6d02072d57ce4b6d92d85ccd6665caa6f4ac940d97c10d4d0185171cb5f875')):
        assert digest(patch) == expected
        apply(gateway / 'carrier', patch)
    patch = ROOT / 'tests/fixtures/mesh_throughput_trace/android-trace.patch'
    assert digest(patch) == inputs['android']['patch_sha256']
    for name, expected in inputs['android']['inputs'].items():
        if name == 'clients/android/app/build.gradle':
            continue
        path = android / name
        assert (digest(path) if path.exists() else None) == expected, name
    sections = re.split(r'(?=^--- a/)', patch.read_text(), flags=re.MULTILINE)
    observation = ''.join(section for section in sections if not section.startswith('--- a/clients/android/app/build.gradle\n'))
    derived = WORK / 'android-observation-without-version.patch'
    derived.write_text(observation)
    apply(android, derived)
    for name, expected in inputs['android']['outputs'].items():
        if name != 'clients/android/app/build.gradle':
            assert digest(android / name) == expected, name
    for name in ('main.go', 'seed_recovery.go', 'seed_recovery_test.go'):
        relative = 'carrier/cmd/bootstrap-broker/' + name
        assert digest(gateway / relative) == digest(PARENT / 'gateway-source' / relative)
    (WORK / 'observation-parent-pins.json').write_text(json.dumps(dict(
        android={name:digest(path) for name in inputs['android']['outputs'] if (path:=android/name).exists()},
        gateway={str(path.relative_to(gateway)):digest(path) for path in gateway.rglob('*') if path.is_file()}), indent=2))
    print('EXACT_BETA90_B9_OBSERVATION_BASES_PREPARED_NO_VERSION_CHANGE_NO_DEPLOY')


if __name__ == '__main__':
    main()
