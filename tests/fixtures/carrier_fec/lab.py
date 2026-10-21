import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
FIX = Path(__file__).resolve().parent
PARENT = ROOT / 'state-client-build/p-stack-interaction-20261021'
WORK = ROOT / 'state-client-build/carrier-fec-20261021'
SOURCE = WORK / 'source'
TOOLS = ROOT / 'state-client-build/field65-export16/diag-source-freeze-1/resume-tools'
sys.path.insert(0, str(ROOT / 'tests/fixtures/tls_rs_packing'))
from interaction_prepare import write, digest, inventory, delta


def save(path, value):
    assert not path.exists(), path
    write(path, json.dumps(value, indent=2) + '\n')


def environment(network=False):
    result = {key: value for key, value in os.environ.items()
              if not key.startswith(('GO', 'CGO', 'FC_', 'YANDEX_'))}
    result.update(GOTOOLCHAIN='local', GOWORK='off', GOPROXY='https://proxy.golang.org' if network else 'off',
                  GOSUMDB='sum.golang.org' if network else 'off', GOMAXPROCS='2',
                  GOPATH=str(TOOLS/'gopath'), GOCACHE=str(WORK/'go-cache'), FC_EXPECT_SEED_OBSERVABILITY='1')
    return result


def replace(path, old, new):
    text = path.read_text()
    assert text.count(old) == 1, (str(path), old)
    write(path, text.replace(old, new))


def main():
    assert not WORK.exists()
    parent = json.loads((PARENT/'build.json').read_text())
    assert inventory(PARENT/'source') == parent['source_inventory']
    WORK.mkdir()
    shutil.copytree(PARENT/'source', SOURCE)
    for name in ['run_phase.py', 'worker.py']:
        shutil.copy2(PARENT/name, WORK/name)
    save(WORK/'entry.json', dict(parent_binary=parent['binary_sha256'], parent_build=digest(PARENT/'build.json'),
         git_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
         git_status=subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True),
         baseline='RS32/32 Mux128 OFF Q0 mediaA phase0; 2ms/frame and 33ms timestamp unchanged',
         limits=dict(source=128*1024**2, media=256*1024**2, transfer_s=180),
         reserved_P_bulk=48*1024**2, reserved_P_controls=6*(3*65536+12*64+4096),
         planned=['carrier L/S smoke','R32 L/S/SF short','P L/S/SF/SF/S/L'],
         common_media_ceiling_bytes_per_second=1048576,
         production='read-only; bootstrap96 gateway1011 A0 LEGACY64; no identities/floors/routes changed'))
    print('PINNED', parent['binary_sha256'])


if __name__ == '__main__':
    main()
