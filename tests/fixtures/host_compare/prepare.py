"""Adapt only the existing CLI's synthetic workload, never product transport."""
import difflib
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[3]
WORK = ROOT / 'state-client-build/host-compare-20261020'
BASE = ROOT / 'state-client-build/rtp-pacing-20261020'
TOOLS = ROOT / 'state-client-build/field65-export16/diag-source-freeze-1/resume-tools'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def environment():
    values = {key: value for key, value in os.environ.items() if not key.startswith(('GO', 'CGO', 'FC_', 'YANDEX_'))}
    values.update(GOTOOLCHAIN='local', GOWORK='off', GOPROXY='off', GOSUMDB='off', GOMAXPROCS='2',
                  GOPATH=str(TOOLS / 'gopath'), GOCACHE=str(WORK / 'go-cache'))
    return values


def main():
    os.umask(0o077)
    inventory = json.loads((BASE / 'source-inventory.json').read_text())
    assert all(digest(BASE / 'candidate' / name) == expected for name, expected in inventory.items())
    source = WORK / 'source'
    shutil.copytree(BASE / 'candidate', source)
    replacements = {
        'cmd/telemost-binary/main.go': [
            ('session, err := telemost.New(ctx,', 'if os.Getenv("FC_HOST_COMPARE_FIXTURE") == "1" {\nif !*muxGateway || *muxLoopback == 0 { return errors.New("isolated fixture requires mux gateway") }; stop, err := hostFixture(ctx, *muxLoopback, func(map[string]any) error { return nil }); if err != nil { return err }; defer stop()\n}\n session, err := telemost.New(ctx,')],
        'cmd/telemost-binary/mux.go': [
            ('config.Mode != "public" && config.Mode != "mixed"', 'config.Mode != "public" && config.Mode != "mixed" && config.Mode != "host-compare"'),
            ('if config.Mode == "public" {', 'if config.Mode == "host-compare" {\nerr = muxHostCompare(ctx, mux, config.Port, snapshot, emit)\n} else if config.Mode == "public" {'),
            ('"stats": mux.Stats(), "transport": snapshot()', '"stats": mux.Stats(), "mux_performance": mux.PerformanceSnapshot(), "transport": snapshot()')],
        'telemost/performance.go': [
            ('case "inbound-rtp",', 'case "local-candidate", "remote-candidate", "inbound-rtp",'),
            ('case float64, bool:', 'case string:\n switch key { case "id", "localCandidateId", "remoteCandidateId", "selectedCandidatePairId", "networkType", "protocol", "candidateType", "ip", "address": row[key] = value }\n case float64, bool:')],
    }
    patch = []
    for name, changes in replacements.items():
        path = source / name
        before = path.read_text()
        after = before
        for old, new in changes:
            assert old in after, (name, old)
            after = after.replace(old, new)
        subprocess.run(['apply_patch'], input='*** Begin Patch\n*** Update File: '+str(path)+'\n@@\n-'+before.replace('\n','\n-').rstrip('-')+'+'+after.replace('\n','\n+').rstrip('+')+'*** End Patch\n', text=True, check=True)
    for name in ['host_compare.go', 'host_compare_test.go']:
        target = source / 'cmd/telemost-binary' / name
        text = (ROOT / 'tests/fixtures/host_compare' / name).read_text()
        subprocess.run(['apply_patch'], input='*** Begin Patch\n*** Add File: '+str(target)+'\n'+''.join('+'+line+'\n' for line in text.splitlines())+'*** End Patch\n', text=True, check=True)
    subprocess.run([TOOLS/'go/bin/gofmt','-w',*list(source.glob('cmd/telemost-binary/host_compare*.go')),*[source/name for name in replacements]],check=True)
    for name in replacements:
        patch.extend(difflib.unified_diff((BASE/'candidate'/name).read_text().splitlines(True),(source/name).read_text().splitlines(True),fromfile='a/'+name,tofile='b/'+name))
    for name in ['host_compare.go','host_compare_test.go']:
        patch.extend(difflib.unified_diff([], (source/'cmd/telemost-binary'/name).read_text().splitlines(True),fromfile='/dev/null',tofile='b/cmd/telemost-binary/'+name))
    (WORK/'harness-only.patch').write_text(''.join(patch))
    with (WORK/'local-tests.log').open('x') as log:
        subprocess.run([TOOLS/'go/bin/go','test','-p=1','-race','-tags=fc_perf_diagnostic','-run','TestHost|TestMux|TestTCPConfig','-count=1','-timeout=90s','./cmd/telemost-binary'],cwd=source,env=environment(),stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
    with (WORK/'build.log').open('x') as log:
        subprocess.run([TOOLS/'go/bin/go','build','-p=1','-trimpath','-buildvcs=false','-tags=fc_perf_diagnostic','-o',str(WORK/'telemost-host-compare'),'./cmd/telemost-binary'],cwd=source,env=environment(),stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
    manifest=dict(binary_sha256=digest(WORK/'telemost-host-compare'),source_inventory={str(path.relative_to(source)):digest(path) for path in source.rglob('*') if path.is_file()},harness_patch_sha256=digest(WORK/'harness-only.patch'),base_inventory_sha256=digest(BASE/'source-inventory.json'),transport_changes=[],observability_only=['telemost/performance.go'],workload_only=list(replacements)[:2]+['cmd/telemost-binary/host_compare.go'],mode='OFF/Q0 LEGACY64 A0 IPv4 VP8',build_tags='fc_perf_diagnostic',application_bytes_per_phase=8388608+3*65536+5*5+32)
    (WORK/'build.json').write_text(json.dumps(manifest,indent=2))
    print(json.dumps({key:value for key,value in manifest.items() if key!='source_inventory'}))


if __name__ == '__main__':
    main()
