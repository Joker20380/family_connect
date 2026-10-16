import hashlib
import json
from pathlib import Path
import re
import shutil

root = Path(__file__).resolve().parent
publication = root.parent/'owner-cumulative-client-acceptance-1-resume/review-publication'
target = publication/'research/browser-admission-fix-20261017'
build = json.loads((root/'build/receipt.json').read_text())
assert build['result'] == 'PASS_LOCAL_COMBINED_BUILD'
assert len(build['runs']) == 6 and all(item['exit'] == 0 for item in build['runs'])
artifact = json.loads((root/'artifact-check.json').read_text())
assert artifact['unsigned_verified'] and artifact['native_manifest_matches_new_build']
for name in ('candidate.patch','boundary.json','cumulative-source.json','gateway-source.json',
             'seal.py','check.py','check_followup.py','check_jvm.py','build.py','bounded.py',
             'check_artifact.py','publish_safe.py','artifact-check.json','thermal.json'):
    shutil.copyfile(root/name,target/name)
shutil.copytree(root/'fixtures',target/'fixtures',dirs_exist_ok=True)
checks = []
for batch in ('checks-1','checks-2','checks-jvm'):
    output = target/batch
    output.mkdir(exist_ok=True)
    receipts = json.loads((root/batch/'receipts.json').read_text())
    for entry in receipts:
        log = root/batch/(entry['label']+'.log')
        text = log.read_text()
        passed = re.findall(r'^--- PASS: (\S+)',text,re.M)
        skipped = re.findall(r'^--- SKIP: (\S+)',text,re.M)
        failed = re.findall(r'^--- FAIL: (\S+)',text,re.M)
        checks.append(dict(batch=batch,**entry,top_level_passes=len(passed),
                           top_level_skips=len(skipped),top_level_failures=len(failed)))
        if entry['label'] != 'fixture-generate':
            shutil.copyfile(log,output/log.name)
    shutil.copyfile(root/batch/'receipts.json',output/'receipts.json')
safe_build = {name:build[name] for name in ('result','version_name','version_code','source_inventory',
    'native_sha256','unsigned_apk_sha256','apk_size','gateway_source_inventory','gateway_sha256',
    'gateway_dependencies_unchanged','gateway_executed','gateway_deployed','jvm_suites')}
safe_build['runs'] = [{name:entry[name] for name in ('label','exit','log_sha256')} for entry in build['runs']]
thermal = json.loads((root/'thermal.json').read_text())
safe = dict(result='PASS_LOCAL_BOUNDED_CANDIDATE_NOT_DEPLOYED',build=safe_build,checks=checks,
    thermal=thermal,source_boundary=json.loads((root/'boundary.json').read_text()),
    limits=dict(owner_failed_request_binding='NOT_PROVEN',ten_minute_cutoff_cause='NOT_PROVEN',
                origin_close_server_protocol_errors_normal=[0,1],origin_close_server_protocol_errors_race=28,
                device_browser_acceptance='NOT_RUN',mobile_throughput='NOT_MEASURED'),
    action_counts=dict(ssh=0,adb=0,connect=0,export=0,sign=0,install=0,rollback=0,
                       deploy=0,restart=0,maintenance=0,emulator=0,native_stats_pollers=0))
evidence = publication/'docs/releases/evidence/2026-10-17-browser-admission-fix-1.json'
evidence.write_text(json.dumps(safe,indent=2)+'\n')
manifest = {str(filename.relative_to(target)):hashlib.sha256(filename.read_bytes()).hexdigest()
    for filename in target.rglob('*') if filename.is_file() and filename.name != 'publication-files.json'}
(target/'publication-files.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(dict(files=len(manifest),top_level_passes=sum(item['top_level_passes'] for item in checks),
                     evidence_sha256=hashlib.sha256(evidence.read_bytes()).hexdigest())))
