"""Seal tested source and build one local gateway; never deploy or alter policy."""
import collections
import difflib
import json
import subprocess
from pathlib import Path
from prepare import ROOT, WORK, BASE, TOOLS, APK, GATEWAY, digest, environment


def patch_file(path, text):
    assert not path.exists()
    subprocess.run(['apply_patch'], input='*** Begin Patch\n*** Add File: '+str(path)+'\n'+''.join('+'+line+'\n' for line in text.splitlines())+'*** End Patch\n',text=True,check=True)


def events(name):
    rows=[json.loads(line) for line in (WORK/name).read_text().splitlines() if line.startswith('{')]
    assert not any(row['Action']=='fail' for row in rows), name
    assert any(row['Action']=='pass' and not row.get('Test') for row in rows), name
    return rows


def observations(rows):
    output=collections.defaultdict(str)
    for row in rows:
        if row['Action']=='output':output[(row['Package'],row.get('Test',''))]+=row['Output']
    values=[]
    for text in output.values():
        for line in text.splitlines():
            if ': {' in line:
                values.append(json.loads(line[line.index('{'):]))
    return values


def main():
    source=WORK/'candidate'
    before=BASE/'gateway-source/carrier'
    logs=['candidate-paced-scoped-final.log','candidate-observed-final.log','candidate-exporter-final.log','candidate-legacy-preserved.log','baseline-queue-only.log']
    rows={name:events(name) for name in logs}
    passed={(row['Package'],row['Test']) for name in logs if name.startswith('candidate-') for row in rows[name] if row['Action']=='pass' and row.get('Test')}
    manifest=json.loads((WORK/'baseline-manifest.json').read_text())
    assert all(digest(before/name)==value for name,value in manifest['files'].items())
    protected=['go.mod','go.sum','telemost/rtp.go','telemost/vp8.go','tcpforward/mux.go','reliablestream/protocol.go','reliablestream/engine.go',
        'cmd/bootstrap-broker/main.go','cmd/bootstrap-broker/seed_recovery.go','cmd/bootstrap-broker/seed_recovery_test.go']
    assert all(digest(source/name)==digest(before/name) for name in protected)
    files={str(path.relative_to(source)):digest(path) for path in source.rglob('*') if path.is_file()}
    changes={};patch=[]
    for name in sorted(set(files)|set(manifest['files'])):
        old,new=before/name,source/name
        if old.exists() and new.exists() and digest(old)==digest(new):continue
        changes[name]=dict(before=digest(old) if old.exists() else None,after=digest(new) if new.exists() else None)
        patch.extend(difflib.unified_diff(old.read_text().splitlines(True) if old.exists() else [],new.read_text().splitlines(True) if new.exists() else [],fromfile='a/'+name if old.exists() else '/dev/null',tofile='b/'+name if new.exists() else '/dev/null'))
    patch_path=ROOT/'tests/fixtures/rtp_pacing/packet-pacing.patch'
    patch_file(patch_path,''.join(patch))
    inventory=WORK/'source-inventory.json';inventory.write_text(json.dumps(files,sort_keys=True,indent=2))
    binary=WORK/'gateway-pacing';assert not binary.exists()
    with (WORK/'build.log').open('x') as log:
        subprocess.run([str(TOOLS/'go/bin/go'),'build','-p=1','-trimpath','-buildvcs=false','-tags=fc_perf_diagnostic','-o',str(binary),'./cmd/bootstrap-broker'],cwd=source,env=environment(),stdout=log,stderr=subprocess.STDOUT,check=True,timeout=300)
    values=observations(rows['candidate-observed-final.log'])
    models=[value for value in values if 'complete_frames' in value]
    burst=[value for value in values if value.get('scope')=='actual_bound_pion_local_sink_not_network']
    queues={name:[value for value in observations(data) if 'pending_attempts_before_first_write' in value] for name,data in rows.items()}
    result=dict(schema=1,baseline_apk=APK,baseline_gateway=GATEWAY,source=str(source.relative_to(ROOT)),
        binary=str(binary.relative_to(ROOT)),binary_sha256=digest(binary),source_inventory_sha256=digest(inventory),patch_sha256=digest(patch_path),
        changes=changes,protected_files={name:digest(source/name) for name in protected},
        passed_candidate_cases_including_subtests=len(passed),test_logs={name:digest(WORK/name) for name in logs},
        queue_safety=queues,burst_local=burst,models=models,overhead_log_sha256=digest(WORK/'overhead-final.log'),
        physical='NOT_RUN_COORDINATE_SHARED_GATEWAY_RESTART_AFTER_TESTER_BETA96_ATTEMPT',physical_bytes=0,speed_acceptance='INCONCLUSIVE',
        modes=dict(OFF='accepted send/completion policy; no pacing histograms',OBSERVE='scoped local-completion prerequisite + same bounded histograms, no packet rate cap',FIXED4M='same prerequisite/metrics +500000 RTP bytes/s synchronous pacing'),
        no_adaptive_cc=True,live_change=False,apk_rebuilt=False,public_release=False,push=False)
    (WORK/'build-result.json').write_text(json.dumps(result,indent=2))
    patch_file(ROOT/'docs/releases/2026-10-20-rtp-packet-pacing.evidence.json',json.dumps(result,indent=2))
    print(json.dumps({key:result[key] for key in ('binary','binary_sha256','patch_sha256','source_inventory_sha256','passed_candidate_cases_including_subtests','physical','physical_bytes')}))


if __name__=='__main__':main()
