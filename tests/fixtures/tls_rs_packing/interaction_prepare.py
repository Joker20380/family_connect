"""New budget/capsule; reuse the sealed strict-drain packing harness, never product."""
import difflib
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[3]
FIX = Path(__file__).resolve().parent
PARENT = ROOT / 'state-client-build/tls-rs-packing-20261021'
WORK = ROOT / 'state-client-build/p-stack-interaction-20261021'
SOURCE = WORK / 'source'
TOOLS = ROOT / 'state-client-build/field65-export16/diag-source-freeze-1/resume-tools'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        old = path.read_text()
        if old == text:
            return
        patch = '*** Update File: ' + str(path) + '\n@@\n'
        patch += ''.join('-' + line + '\n' for line in old.splitlines())
        patch += ''.join('+' + line + '\n' for line in text.splitlines())
    else:
        patch = '*** Add File: ' + str(path) + '\n'
        patch += ''.join('+' + line + '\n' for line in text.splitlines())
    subprocess.run(['apply_patch'], input='*** Begin Patch\n' + patch + '*** End Patch\n',
                   text=True, check=True, stdout=subprocess.DEVNULL)


def save(path, value):
    assert not path.exists(), path
    write(path, json.dumps(value, indent=2) + '\n')


def environment():
    values = {key: value for key, value in os.environ.items()
              if not key.startswith(('GO', 'CGO', 'FC_', 'YANDEX_'))}
    values.update(GOTOOLCHAIN='local', GOWORK='off', GOPROXY='off', GOSUMDB='off',
                  GOMAXPROCS='2', GOPATH=str(TOOLS/'gopath'), GOCACHE=str(WORK/'go-cache'),
                  FC_EXPECT_SEED_OBSERVABILITY='1')
    return values


def inventory(root):
    return {str(path.relative_to(root)): digest(path) for path in root.rglob('*') if path.is_file()}


def delta(parent, target):
    result = []
    for name, value in inventory(target).items():
        before = parent/name
        if not before.exists() or digest(before) != value:
            result.extend(difflib.unified_diff(before.read_text().splitlines(True) if before.exists() else [],
                          (target/name).read_text().splitlines(True), fromfile='a/'+name, tofile='b/'+name))
    return ''.join(result)


def main():
    os.umask(0o077)
    parent = json.loads((PARENT/'build.json').read_text())
    assert inventory(PARENT/'source') == parent['source_inventory']
    assert digest(PARENT/'telemost-capacity') == parent['binary_sha256']
    WORK.mkdir(mode=0o700, exist_ok=False)
    shutil.copytree(PARENT/'source', SOURCE)
    save(WORK/'entry.json', dict(parent_build_sha256=digest(PARENT/'build.json'),
         parent_binary_sha256=parent['binary_sha256'], parent_source_inventory=parent['source_inventory'],
         production='bootstrap96 gateway1011 734b6ca6… A0 OFF/Q0 LEGACY64; read-only',
         source_limit=64*1024**2, media_limit=128*1024**2, transfer_seconds=180,
         common='RS32/32 payload16384 RTO1s retries8 age20s mediaA phase0 receiver unchanged',
         variants={'A':['A',65536], 'B':['B2',65536], 'C':['A',131072], 'D':['B2',131072]},
         excluded=['queue-retry candidate','pacing','timebase correction','new writer scheduling'],
         note='A is LAB RS32, not production RS8; no network reservations yet'))
    print('PINNED', parent['binary_sha256'])


if __name__ == '__main__':
    main()
