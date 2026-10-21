"""Pin accepted94/b9 sources; create a separate compatibility capsule."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[3]
WORK = ROOT/'state-client-build/mux-profile-20261020'
FIXTURE = Path(__file__).resolve().parent
BASE = ROOT/'state-client-build/tunnel-restart-20261019'
ANDROID = ROOT/'state-client-build/rtp-deadline-20261020/normal94'
TOOLS = ROOT/'state-client-build/field65-export16/diag-source-freeze-1/resume-tools'
GATEWAY = 'b9ae880731517753e456637e52dcc421b9f7d7b881b400c856989ae93193e9ba'
APK = 'fe32f36d0705d83705e549f598512305d63fd942a415f71afaebfd91534f8e13'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def environment():
    values = {key:value for key,value in os.environ.items() if not key.startswith(('GO', 'CGO', 'FC_', 'YANDEX_'))}
    values.update(GOTOOLCHAIN='local', GOWORK='off', GOPROXY='off', GOSUMDB='off', GOMAXPROCS='2',
                  GOPATH=str(TOOLS/'gopath'), GOCACHE=str(WORK/'go-cache'))
    return values


def main():
    os.umask(0o077)
    manifest = json.loads((BASE/'gateway-build.json').read_text())
    assert digest(BASE/'gateway-seed-recovery') == GATEWAY
    assert all(digest(BASE/'gateway-source/carrier'/name) == value for name,value in manifest['files'].items())
    inventory = json.loads((ANDROID/'android-build/source-inventory.json').read_text())
    assert all(digest(ANDROID/'android-source'/name) == value for name,value in inventory.items())
    assert digest(ANDROID/'delivery/FamilyConnect-0.1.18-beta94-stability.apk') == APK
    WORK.mkdir(mode=0o700, exist_ok=False)
    shutil.copytree(BASE/'gateway-source/carrier', WORK/'carrier')
    shutil.copytree(ANDROID/'android-source', WORK/'android-source', ignore=shutil.ignore_patterns('.gradle', '__pycache__'))
    shutil.copyfile(BASE/'gateway-build.json', WORK/'baseline-build.json')
    shutil.copyfile(BASE/'gateway-seed-recovery', WORK/'gateway-baseline')
    print('PINNED_94_B9_NO_LIVE_CHANGE')


if __name__ == '__main__':
    main()
