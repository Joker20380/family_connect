import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
FIX = Path(__file__).resolve().parent
WORK = ROOT / 'state-client-build/quic-carrier-20261021'
PARENT = ROOT / 'state-client-build/carrier-fec-20261021'
SOURCE = WORK / 'source'
TOOLS = ROOT / 'state-client-build/field65-export16/diag-source-freeze-1/resume-tools'
sys.path.insert(0, str(ROOT / 'tests/fixtures/tls_rs_packing'))
from interaction_prepare import write, save, digest, inventory, delta


def environment(network=False):
    result = {key: value for key, value in os.environ.items() if not key.startswith(('GO', 'CGO', 'FC_', 'YANDEX_'))}
    result.update(GOTOOLCHAIN='local', GOWORK='off', GOPROXY='https://proxy.golang.org' if network else 'off', GOSUMDB='sum.golang.org' if network else 'off', GOMAXPROCS='2', GOPATH=str(TOOLS / 'gopath'), GOCACHE=str(WORK / 'go-cache'), FC_EXPECT_SEED_OBSERVABILITY='1')
    return result


def replace(path, old, new):
    text = path.read_text()
    assert text.count(old) == 1, (str(path), old)
    write(path, text.replace(old, new))


if __name__ == '__main__':
    assert not WORK.exists()
    parent = json.loads((PARENT / 'build.json').read_text())
    assert inventory(PARENT / 'source') == parent['source_inventory']
    WORK.mkdir()
    shutil.copytree(PARENT / 'source', SOURCE)
    for name in ['run_phase.py', 'worker.py']:
        shutil.copy2(PARENT / name, WORK / name)
    save(WORK / 'entry.json', dict(parent_build=digest(PARENT / 'build.json'), parent_binary=parent['binary_sha256'], git_head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(), git_status=subprocess.check_output(['git', 'status', '--short'], text=True), baseline='L RS32/32 Family TLS Mux128 packing OFF Q0; no FEC/timebase fix', live_limits=dict(source=64*2**20, media=128*2**20, transfer_s=180), local_accounting='separate; no local reservation charged to live', reserved_main_bulk=32*2**20))
    print('parent pinned', parent['binary_sha256'])
