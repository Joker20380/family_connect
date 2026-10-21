"""Seal a laboratory capsule from the accepted host-comparison inventory."""
import difflib
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
FIX = Path(__file__).resolve().parent
BASE = ROOT / 'state-client-build/host-compare-20261020'
WORK = ROOT / 'state-client-build/mesh-capacity-20261020'
SOURCE = WORK / 'source'
TOOLS = ROOT / 'state-client-build/field65-export16/diag-source-freeze-1/resume-tools'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def environment():
    values = {key: value for key, value in os.environ.items() if not key.startswith(('GO', 'CGO', 'FC_', 'YANDEX_'))}
    values.update(GOTOOLCHAIN='local', GOWORK='off', GOPROXY='off', GOSUMDB='off', GOMAXPROCS='2', GOPATH=str(TOOLS/'gopath'), GOCACHE=str(BASE/'go-cache'))
    return values


def patch_file(path, text):
    if path.exists():
        before = path.read_text()
        patch = '*** Update File: '+str(path)+'\n@@\n'+''.join('-'+line+'\n' for line in before.splitlines())+''.join('+'+line+'\n' for line in text.splitlines())
    else:
        patch = '*** Add File: '+str(path)+'\n'+''.join('+'+line+'\n' for line in text.splitlines())
    subprocess.run(['apply_patch'], input='*** Begin Patch\n'+patch+'*** End Patch\n', text=True, check=True, stdout=subprocess.DEVNULL)


def prepare():
    original = json.loads((BASE/'build.json').read_text())
    assert all(digest(BASE/'source'/name) == value for name,value in original['source_inventory'].items())
    shutil.copytree(BASE/'source', SOURCE)
    for name,target in [('capacity.go','cmd/telemost-binary/capacity.go'),('capacity_test.go','cmd/telemost-binary/capacity_test.go'),('lab_wire.go','telemost/lab_wire.go'),('windows_test.go','reliablestream/capacity_window_test.go'),('assembly_test.go','telemost/capacity_assembly_test.go')]:
        patch_file(SOURCE/target,(FIX/name).read_text())
    changes = {
        'cmd/telemost-binary/main.go': [('flag.Parse()', 'capacityFile := flag.String("capacity-config", "", "isolated synthetic capacity configuration")\nflag.Parse()'),('var data familysession.PacketEndpoint = session', 'if *capacityFile != "" { if *role == "probe" { select { case <-time.After(*settle): case <-ctx.Done(): return ctx.Err() } }; return capacityRun(ctx, session, *capacityFile, *familyConfig, *role == "echo", emit) }\nvar data familysession.PacketEndpoint = session'),('"event": "summary", "stats": session.Stats()', '"event": "summary", "transport": session.PerformanceSnapshot(), "stats": session.Stats()')],
        'telemost/session.go': [('registry := &interceptor.Registry{}','registry := &interceptor.Registry{}\nregistry.Add(&labWireFactory{})')],
        'telemost/performance.go': [('result := map[string]any{','result := map[string]any{"lab_wire":labWireSnapshot(),')],
    }
    for name,replacements in changes.items():
        text = (SOURCE/name).read_text()
        for old,new in replacements:
            assert text.count(old)==1,(name,old)
            text=text.replace(old,new)
        patch_file(SOURCE/name,text)
    original_tests=(SOURCE/'reliablestream/engine_test.go').read_text()
    functions=original_tests[original_tests.index('func connectedEngines()'):original_tests.index('func TestDeterministicFaultMatrix(')]
    functions=functions.replace('func connectedEngines()','func capacityEngines(config Config)').replace('\n\tconfig := DefaultConfig()','').replace('func simulate(test *testing.T, injection faults)','func capacitySimulate(test *testing.T, injection faults, config Config)').replace('states := connectedEngines()','states := capacityEngines(config)').replace('len(state.sent) > 8 || len(state.buffer) > 16 || state.stats.BufferedBytes > 24*16384','len(state.sent) > config.SendWindow || len(state.buffer) > config.ReceiveWindow || state.stats.BufferedBytes > (config.SendWindow+config.ReceiveWindow)*16384').replace('stats.SendHighWater < 8','stats.SendHighWater < config.SendWindow')
    patch_file(SOURCE/'reliablestream/capacity_simulation_test.go','package reliablestream\nimport ("bytes";"testing";"time")\n'+functions)
    changed=[path for path in SOURCE.rglob('*.go') if str(path.relative_to(SOURCE)) not in original['source_inventory'] or digest(path)!=original['source_inventory'][str(path.relative_to(SOURCE))]]
    subprocess.run([TOOLS/'go/bin/gofmt','-w',*changed],check=True)


def build():
    with (WORK/'local-tests.log').open('x') as log:
        subprocess.run([TOOLS/'go/bin/go','test','-p=1','-race','-tags=fc_perf_diagnostic','-v','-run','TestCapacity|TestAdapter|TestDeterministicFaultMatrix|TestQueue|TestRTP|TestFraming','-count=1','-timeout=150s','./cmd/telemost-binary','./reliablestream','./telemost'],cwd=SOURCE,env=environment(),stdout=log,stderr=subprocess.STDOUT,timeout=260,check=True)
    with (WORK/'build.log').open('x') as log:
        subprocess.run([TOOLS/'go/bin/go','build','-p=1','-trimpath','-buildvcs=false','-tags=fc_perf_diagnostic','-o',WORK/'telemost-capacity','./cmd/telemost-binary'],cwd=SOURCE,env=environment(),stdout=log,stderr=subprocess.STDOUT,timeout=180,check=True)
    original=json.loads((BASE/'build.json').read_text())['source_inventory']
    inventory={str(path.relative_to(SOURCE)):digest(path) for path in SOURCE.rglob('*') if path.is_file()}
    delta=[]
    for name,value in inventory.items():
        if original.get(name)!=value:
            before=(BASE/'source'/name).read_text().splitlines(True) if name in original else []
            delta.extend(difflib.unified_diff(before,(SOURCE/name).read_text().splitlines(True),fromfile='a/'+name,tofile='b/'+name))
    patch_file(WORK/'lab-only.patch',''.join(delta))
    manifest=dict(binary_sha256=digest(WORK/'telemost-capacity'),source_inventory=inventory,base_build_sha256=digest(BASE/'build.json'),lab_patch_sha256=digest(WORK/'lab-only.patch'),rs_defaults=dict(payload=16384,send_window=8,receive_window=16,max_window=32,sack_bits=32,rto_seconds=1,max_retries=8,max_age_seconds=20),baseline='beta96/A0/OFF/Q0/LEGACY64; pinned host-compare capsule',wire_boundary='first Pion interceptor: every outgoing RTP/RTCP attempt including NACK retransmits; RTP/RTCP length + conservative64bytes/packet; no receiver RX double count')
    patch_file(WORK/'build.json',json.dumps(manifest,indent=2))


if __name__=='__main__':
    os.umask(0o077)
    if '--build' in sys.argv: build()
    else: prepare()
