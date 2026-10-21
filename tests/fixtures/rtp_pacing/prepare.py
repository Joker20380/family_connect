"""Pin current compatible gateway and beta96 without changing either runtime."""
import hashlib
import json
import os
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[3]
WORK = ROOT / 'state-client-build/rtp-pacing-20261020'
BASE = ROOT / 'state-client-build/mux-profile-20261020'
TOOLS = ROOT / 'state-client-build/field65-export16/diag-source-freeze-1/resume-tools'
APK = '07a90f03269e1df683289bc1fbe7fa7e88647c5629f71db1f784d6566aa9228d'
GATEWAY = '272bbc3fed90bbcf740a58f812e93511c976c114e2190f2c8711b55fa0dfb0c4'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def environment():
    values = {key: value for key, value in os.environ.items() if not key.startswith(('GO', 'CGO', 'FC_', 'YANDEX_'))}
    values.update(GOTOOLCHAIN='local', GOWORK='off', GOPROXY='off', GOSUMDB='off', GOMAXPROCS='2',
                  GOPATH=str(TOOLS / 'gopath'), GOCACHE=str(WORK / 'go-cache'))
    return values


def main():
    os.umask(0o077)
    manifest = json.loads((BASE / 'negotiated-build.json').read_text())
    assert manifest['sha256'] == digest(BASE / 'gateway-negotiated') == GATEWAY
    source = BASE / 'gateway-source/carrier'
    assert all(digest(source / name) == value for name, value in manifest['files'].items())
    android = ROOT / 'state-client-build/mobile-bootstrap-20261020'
    assert digest(android / 'delivery/FamilyConnect-0.1.18-beta96-bootstrap.apk') == APK
    build = json.loads((android / 'build/source-inventory.json').read_text())
    assert all(digest(android / 'android-source' / name) == value for name, value in build.items())
    WORK.mkdir(mode=0o700, exist_ok=False)
    for variant in ('baseline', 'candidate'):
        shutil.copytree(source, WORK / variant)
    (WORK / 'baseline-manifest.json').write_text(json.dumps(manifest, indent=2))
    (WORK / 'preservation.json').write_text(json.dumps(dict(apk=APK, gateway=GATEWAY,
        gateway_manifest_sha256=digest(BASE / 'negotiated-build.json'), android_inventory_sha256=digest(android / 'build/source-inventory.json'),
        profile='LEGACY64', receiver='A0', credit128=False, measurement_bytes=0, deployed=False), indent=2))
    print('EXACT96_AND_COMPATIBLE_GATEWAY_PINNED_NO_RUNTIME_CHANGE')


if __name__ == '__main__':
    main()
