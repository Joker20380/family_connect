"""Preserve the current1011 source, never substitute the historical4b baseline."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[3]
WORK = ROOT / 'state-client-build/queue-retry-20261019'
PARENT = ROOT / 'state-client-build/tunnel-restart-20261019'
GATEWAY = 'b9ae880731517753e456637e52dcc421b9f7d7b881b400c856989ae93193e9ba'
APK = '68cbcccfb5adf8656e8203436126330e780de099670ee2031d71019baadc3e9a'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    os.umask(0o077)
    assert digest(PARENT / 'gateway-seed-recovery') == GATEWAY
    build = json.loads((PARENT / 'gateway-build.json').read_text())
    assert build['source_inventory'] == '4722b7353ba93209657f66b45c47874915362f1fbe732845ec61745abdb673e6'
    assert all(digest(PARENT / 'gateway-source/carrier' / name) == value for name, value in build['files'].items())
    apk = PARENT / 'delivery/FamilyConnect-0.1.18-beta90-stability.apk'
    assert digest(apk) == APK
    WORK.mkdir(mode=0o700, exist_ok=False)
    for name in ('gateway-build.json', 'upgrade-receipt.json', 'identity-after.json', 'delivery/signing-receipt.json', 'android-build/receipt.json', 'receipts/final-readiness.json'):
        target = WORK / 'parent-receipts' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(PARENT / name, target)
    shutil.copyfile(PARENT / 'gateway-seed-recovery', WORK / 'gateway-baseline')
    shutil.copytree(PARENT / 'gateway-source', WORK / 'baseline-source')
    (WORK / 'tests').mkdir()
    (WORK / 'entry-status.txt').write_text(subprocess.check_output(['git','status','--short'], cwd=ROOT, text=True))
    print('CURRENT1011_BASELINE_PRESERVED')


if __name__ == '__main__':
    main()
