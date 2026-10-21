"""Pinned, disposable TLS-to-RS laboratory capsule; no production edits."""
import difflib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
FIX = Path(__file__).resolve().parent
BASE = ROOT / 'state-client-build/mesh-capacity-phase3-20261020'
WORK = ROOT / 'state-client-build/tls-rs-packing-20261021'
SOURCE = WORK / 'source'
spec = importlib.util.spec_from_file_location('previous_prepare', ROOT/'tests/fixtures/mesh_capacity_phase3/prepare.py')
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)
digest, environment, patch_file, TOOLS = previous.digest, previous.environment, previous.patch_file, previous.TOOLS

def replace(name, old, new):
    path = SOURCE/name
    text = path.read_text()
    assert text.count(old) == 1, (name, old)
    patch_file(path, text.replace(old, new))

def prepare():
    assert not WORK.exists()
    parent = json.loads((BASE/'build.json').read_text())
    assert all(digest(BASE/'source'/name) == value for name,value in parent['source_inventory'].items())
    assert digest(BASE/'telemost-capacity') == parent['binary_sha256']
    WORK.mkdir(mode=0o700)
    shutil.copytree(BASE/'source', SOURCE)
    replace('familysession/session.go', 'once     sync.Once', 'once     sync.Once\n lab *labPackingConn')
    replace('familysession/session.go', 'connection.workers.Add(2)', 'connection.lab = newLabPackingConn(ctx, local, endpoint)\n connection.Conn = connection.lab\n connection.workers.Add(2)')
    replace('familysession/session.go', 'buffer := make([]byte, MaxPayload)', 'if connection.lab.policy != "A" { connection.lab.run(); return }\n buffer := make([]byte, MaxPayload)')
    replace('familysession/session.go', 'if _, err := peer.Write(payload); err != nil {', 'connection.lab.observeReceive(payload)\n if _, err := peer.Write(payload); err != nil {')
    replace('cmd/telemost-binary/capacity.go', 'MediaPolicy      string', 'Packing string\n MediaPolicy      string')
    replace('cmd/telemost-binary/capacity.go', 'endpoint := &capacityEndpoint', 'ctx = familysession.WithLabPacking(ctx, config.Packing)\n endpoint := &capacityEndpoint')
    replace('cmd/telemost-binary/capacity.go', 'var reliableStats func() any', 'var packingStats = func() any { return nil }\n var reliableStats func() any')
    replace('cmd/telemost-binary/capacity.go', 'defer secured.Close()', 'defer func(){ closeErr := secured.Close(); _ = emit(map[string]any{"event":"packing_closed", "error":fmt.Sprint(closeErr), "packing":secured.LabPackingStats()}) }()\n packingStats = func() any { return secured.LabPackingStats() }')
    replace('cmd/telemost-binary/capacity.go', 'result["histograms"] = endpoint.snapshot()', 'result["histograms"] = endpoint.snapshot()\n result["packing"] = packingStats()')
    assert (FIX/'run.py').is_file() and (FIX/'worker.py').is_file()
    patch_file(WORK/'matrix.json', json.dumps(dict(source_limit=128*1024**2,media_limit=256*1024**2,plan=['local A/B0/B2, A8/B8/A32/B32; faults and legacy','T8 A/B 4MiB; T32 A/B/B/A 4MiB','P32 A/B/B/A single4MiB parallel2x2MiB; P8 A/B same; reserve ~54MiB'],media='A/phase0 unchanged',RS='8/16 or32/32, all other defaults unchanged'),indent=2))

def build():
    assert not list(WORK.glob('*/reservation.json')), 'Preserve reserved builds; use a separate capsule for new code.'
    for path in FIX.glob('*.go'):
        package='tcpforward' if path.name.startswith('mux_') else 'cmd/telemost-binary' if path.name.startswith('harness_') else 'familysession'
        patch_file(SOURCE/package/('lab_'+path.name),path.read_text())
    changed = [path for path in SOURCE.rglob('*.go') if not (BASE/'source'/path.relative_to(SOURCE)).exists() or digest(path)!=digest(BASE/'source'/path.relative_to(SOURCE))]
    subprocess.run([TOOLS/'go/bin/gofmt','-w',*changed],check=True)
    attempt = len(list(WORK.glob('local-*.log')))+1
    with (WORK/f'local-{attempt}.log').open('x') as log:
        subprocess.run([TOOLS/'go/bin/go','test','-p=1','-race','-tags=fc_perf_diagnostic','-v','-run','TestPacking','-count=1','-timeout=180s','./familysession','./tcpforward','./cmd/telemost-binary'],cwd=SOURCE,env=environment(),stdout=log,stderr=subprocess.STDOUT,check=True,timeout=240)
    with (WORK/f'build-{attempt}.log').open('x') as log:
        subprocess.run([TOOLS/'go/bin/go','build','-p=1','-trimpath','-buildvcs=false','-tags=fc_perf_diagnostic','-o',WORK/'telemost-capacity','./cmd/telemost-binary'],cwd=SOURCE,env=environment(),stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
    inventory = {str(path.relative_to(SOURCE)):digest(path) for path in SOURCE.rglob('*') if path.is_file()}
    delta=[]
    for name,value in inventory.items():
        parent=BASE/'source'/name
        if not parent.exists() or digest(parent)!=value:
            delta.extend(difflib.unified_diff(parent.read_text().splitlines(True) if parent.exists() else [],(SOURCE/name).read_text().splitlines(True),fromfile='a/'+name,tofile='b/'+name))
    patch_file(WORK/'lab-only.patch',''.join(delta))
    patch_file(WORK/'build.json',json.dumps(dict(binary_sha256=digest(WORK/'telemost-capacity'),source_inventory=inventory,parent_build_sha256=digest(BASE/'build.json'),patch_sha256=digest(WORK/'lab-only.patch'),media='A for every live phase',packing='A/B2 before RS sequence; no ALPN change'),indent=2))

if __name__=='__main__':
    os.umask(0o077)
    build() if '--build' in sys.argv else prepare()
