"""Freeze accepted local capsules, not GitHub main; no runtime writes."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[3]
FIXTURE = Path(__file__).resolve().parent
WORK = ROOT / 'state-client-build/speed-candidate-20261021'
ANDROID = ROOT / 'state-client-build/mobile-bootstrap-20261020'
GATEWAY = ROOT / 'state-client-build/rtp-pacing-20261020'
TOOLS = ROOT / 'state-client-build/field65-export16/diag-source-freeze-1/resume-tools'
APK_SHA = '07a90f03269e1df683289bc1fbe7fa7e88647c5629f71db1f784d6566aa9228d'
GATEWAY_SHA = '734b6ca6eb42be0367b703b657be87c624f3500ae408bbd771309ffaeb86128e'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def environment():
    values = {key: value for key, value in os.environ.items() if not key.startswith(('GO', 'CGO', 'FC_', 'YANDEX_'))}
    values.update(GOTOOLCHAIN='local', GOWORK='off', GOPROXY='off', GOSUMDB='off', GOMAXPROCS='2',
                  GOPATH=str(TOOLS / 'gopath'), GOCACHE=str(WORK / 'go-cache'))
    return values


def write(path, content):
    old = path.read_text() if path.exists() else None
    if old == content:
        return
    if old is None:
        patch = '*** Add File: ' + str(path) + '\n'
    else:
        patch = '*** Update File: ' + str(path) + '\n@@\n' + ''.join('-' + line + '\n' for line in old.splitlines())
    patch += ''.join('+' + line + '\n' for line in content.splitlines())
    subprocess.run(['apply_patch'], input='*** Begin Patch\n' + patch + '*** End Patch\n', text=True, check=True, stdout=subprocess.DEVNULL)


def replace(path, old, new):
    content = path.read_text()
    assert content.count(old) == 1, (path, old[:100], content.count(old))
    write(path, content.replace(old, new))


def main():
    os.umask(0o077)
    WORK.mkdir(mode=0o700, exist_ok=True)
    assert not (WORK / 'baseline.json').exists()
    gateway_inventory = json.loads((GATEWAY / 'source-inventory.json').read_text())
    assert all(digest(GATEWAY / 'candidate' / name) == expected for name, expected in gateway_inventory.items())
    android_inventory = json.loads((ANDROID / 'build/source-inventory.json').read_text())
    assert all(digest(ANDROID / 'android-source' / name) == expected for name, expected in android_inventory.items())
    assert digest(ANDROID / 'delivery/FamilyConnect-0.1.18-beta96-bootstrap.apk') == APK_SHA
    assert digest(GATEWAY / 'gateway-pacing') == GATEWAY_SHA
    runtime = json.loads((WORK / 'entry-readback.json').read_text())
    assert runtime['gateway']['sha256'] == GATEWAY_SHA
    assert runtime['gateway']['operator']['rtp-pacing'] == 'OFF'
    assert runtime['gateway']['operator']['mux-profile'] == 'LEGACY64'
    shutil.copytree(ANDROID / 'android-source', WORK / 'android-source', ignore=shutil.ignore_patterns('.git', '.gradle', '__pycache__', 'build'))
    shutil.copytree(GATEWAY / 'candidate', WORK / 'gateway-source')
    inventory = {str(path.relative_to(WORK / 'android-source')): digest(path) for path in (WORK / 'android-source').rglob('*') if path.is_file()}
    (WORK / 'android-baseline-inventory.json').write_text(json.dumps(inventory, indent=2, sort_keys=True))
    (WORK / 'gateway-baseline-inventory.json').write_text(json.dumps(gateway_inventory, indent=2, sort_keys=True))
    manifest = dict(apk_sha256=APK_SHA, gateway_sha256=GATEWAY_SHA,
                    android_source=str(ANDROID / 'android-source'), gateway_source=str(GATEWAY / 'candidate'),
                    android_inventory_sha256=digest(WORK / 'android-baseline-inventory.json'),
                    gateway_inventory_sha256=digest(WORK / 'gateway-baseline-inventory.json'), runtime=runtime,
                    phone_current='NOT_VERIFIED_NO_ADB', last_verified_code=96, reserved_candidate_code=97,
                    candidate_version='0.1.18-beta97-speed', source_basis='exact local accepted capsules')
    (WORK / 'baseline.json').write_text(json.dumps(manifest, indent=2))
    print('PINNED_LOCAL_96_734_NO_RUNTIME_CHANGE')


if __name__ == '__main__':
    main()
