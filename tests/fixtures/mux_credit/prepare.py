"""Exact b9/1011 counter-only capsule; no live changes."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[3]
WORK = ROOT/'state-client-build/mux-credit-20261020'
FIXTURE = Path(__file__).resolve().parent
TOOLS = ROOT/'state-client-build/field65-export16/diag-source-freeze-1/resume-tools'
BASE = ROOT/'state-client-build/tunnel-restart-20261019'
APK = 'fe32f36d0705d83705e549f598512305d63fd942a415f71afaebfd91534f8e13'
GATEWAY = 'b9ae880731517753e456637e52dcc421b9f7d7b881b400c856989ae93193e9ba'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def environment():
    values = {key:value for key,value in os.environ.items() if not key.startswith(('GO','CGO','FC_','YANDEX_'))}
    values.update(GOTOOLCHAIN='local', GOWORK='off', GOPROXY='off', GOSUMDB='off', GOMAXPROCS='2',
                  GOPATH=str(TOOLS/'gopath'), GOCACHE=str(WORK/'go-cache'))
    return values


def main():
    os.umask(0o077)
    manifest = json.loads((BASE/'gateway-build.json').read_text())
    assert manifest['source_inventory']=='4722b7353ba93209657f66b45c47874915362f1fbe732845ec61745abdb673e6'
    assert digest(BASE/'gateway-seed-recovery')==GATEWAY
    assert all(digest(BASE/'gateway-source/carrier'/name)==value for name,value in manifest['files'].items())
    WORK.mkdir(mode=0o700,exist_ok=False)
    shutil.copytree(BASE/'gateway-source',WORK/'baseline-source')
    shutil.copytree(BASE/'gateway-source',WORK/'observation-source')
    shutil.copyfile(BASE/'gateway-seed-recovery',WORK/'gateway-baseline')
    shutil.copyfile(BASE/'gateway-build.json',WORK/'baseline-build.json')
    overlay = ROOT/'tests/fixtures/mesh_perf3/accepted-overlay.patch'
    assert digest(overlay)=='4a32c5e04ffa903791ff30abe80eca6103238f1d2365e9c64d7afc6076f2911c'
    subprocess.run(['patch','-p1','--fuzz=0','-i',str(overlay)],cwd=WORK/'observation-source/carrier',check=True,stdout=subprocess.DEVNULL)
    delta = FIXTURE/'counter-only.patch'
    assert digest(delta)=='5cbbaee5751eb2a7bc233a98d232524c625b0b80305b519b02474382a548c802'
    subprocess.run(['patch','-p1','--fuzz=0','-i',str(delta)],cwd=WORK/'observation-source/carrier',check=True,stdout=subprocess.DEVNULL)
    print('EXACT_B9_COUNTER_CAPSULE_PREPARED')


if __name__=='__main__':
    main()
