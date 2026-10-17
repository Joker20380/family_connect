import hashlib
import json
from pathlib import Path
import re
import shutil

root=Path(__file__).resolve().parent
publication=root.parent/'owner-cumulative-client-acceptance-1-resume/review-publication'
target=publication/'research/transport-write-batching-20261017'
target.mkdir(exist_ok=True)
build=json.loads((root/'build/receipt.json').read_text())
assert build['result']=='PASS_LOCAL_COMBINED_BUILD'
assert len(build['runs'])==6 and all(item['exit']==0 for item in build['runs'])
artifact=json.loads((root/'artifact-check.json').read_text())
assert artifact['unsigned_verified'] and artifact['native_manifest_matches_new_build']
for name in ('candidate.patch','boundary.json','cumulative-source.json','gateway-source.json','seal.py',
             'check.py','verify.py','build.py','bounded.py','check_artifact.py','postcheck.py','postbuild-seal.json','postbuild-seal-initial.json',
             'publish_safe.py','artifact-check.json','thermal.json'):
    shutil.copyfile(root/name,target/name)
shutil.copytree(root/'fixtures',target/'fixtures',dirs_exist_ok=True)
checks=[]
timings={}
for batch in ('baseline-1','candidate-1','baseline-heavy','baseline-tcp','candidate-tcp',
              'baseline-heavy-long','candidate-heavy-long','gateway-tcp','candidate-loss','gateway-loss'):
    output=target/batch
    output.mkdir(exist_ok=True)
    receipts=json.loads((root/batch/'receipts.json').read_text())
    for entry in receipts:
        log=root/batch/(entry['label']+'.log')
        text=log.read_text()
        assert not re.search(r'-----BEGIN (?:[A-Z]+ )?PRIVATE KEY|https://(?:telemost|meet)\.',text)
        assert hashlib.sha256(log.read_bytes()).hexdigest()==entry['log_sha256']
        checks.append(dict(batch=batch,**entry,
            top_level_passes=len(re.findall(r'^--- PASS:',text,re.M)),
            top_level_skips=len(re.findall(r'^--- SKIP:',text,re.M)),
            top_level_failures=len(re.findall(r'^--- FAIL:',text,re.M))))
        shutil.copyfile(log,output/log.name)
        if entry['label']=='tcp-envelope':
            timings[batch]=[dict(elapsed_ms=int(match[0]),client_frames=int(match[1]),server_frames=int(match[2]),retransmits=int(match[3]))
                for match in re.findall(r'elapsed_ms=(\d+) client_frames=(\d+) server_frames=(\d+) retransmits=(\d+)',text)]
    shutil.copyfile(root/batch/'receipts.json',output/'receipts.json')
safe_build={name:build[name] for name in ('result','version_name','version_code','source_inventory','native_sha256',
    'unsigned_apk_sha256','apk_size','gateway_source_inventory','gateway_sha256','gateway_dependencies_unchanged',
    'gateway_executed','gateway_deployed','jvm_suites')}
safe_build['runs']=[{name:entry[name] for name in ('label','exit','log_sha256')} for entry in build['runs']]
safe=dict(result='PASS_LOCAL_BOUNDED_CANDIDATE_NOT_DEPLOYED',build=safe_build,checks=checks,
    tcp_synthetic_40ms_one_way=timings,thermal=json.loads((root/'thermal.json').read_text()),
    postbuild_seal=json.loads((root/'postbuild-seal.json').read_text()),
    source_boundary=json.loads((root/'boundary.json').read_text()),
    limits=dict(initial_inherited_race_15s='FAILED_BOTH_PARENT_AND_CANDIDATE',
                bounded_test_only_60s_overlay='PASS_BOTH',production_timeouts='UNCHANGED',
                phone_throughput='NOT_MEASURED',all_idle_64_slot_waits='NOT_FIXED_BY_BATCHING',
                overnight_mux_37_error_causes='NOT_PROVEN',field_acceptance='NOT_RUN'),
    action_counts=dict(ssh=0,adb=0,connect=0,export=0,sign=0,install=0,rollback=0,deploy=0,restart=0,
                       maintenance=0,emulator=0,native_stats_pollers=0))
evidence=publication/'docs/releases/evidence/2026-10-17-transport-write-batching-1.json'
evidence.write_text(json.dumps(safe,indent=2)+'\n')
manifest={str(filename.relative_to(target)):hashlib.sha256(filename.read_bytes()).hexdigest()
    for filename in target.rglob('*') if filename.is_file() and filename.name!='publication-files.json'}
(target/'publication-files.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(dict(files=len(manifest),evidence_sha256=hashlib.sha256(evidence.read_bytes()).hexdigest())))
