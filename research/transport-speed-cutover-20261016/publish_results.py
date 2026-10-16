import hashlib
import json
from pathlib import Path
import shutil


root = Path(__file__).resolve().parent
state = root.parent
review = state/'owner-cumulative-client-acceptance-1-resume/review-publication'
public = review/'research/transport-speed-cutover-20261016'
stack = state/'reliable-full-stack-1'
receipt = json.loads((root/'build/receipt.json').read_text())
assert receipt['result'] == 'PASS_LOCAL_COMBINED_BUILD'
assert json.loads((root/'artifact-check.json').read_text())['unsigned_verified']
public.mkdir(parents=True,exist_ok=True)
(public/'full-stack').mkdir(exist_ok=True)


def safe_json(value):
    if isinstance(value, dict):
        return {key:safe_json(item) for key,item in value.items()}
    if isinstance(value, list):
        return [safe_json(item) for item in value]
    if isinstance(value, str):
        legacy_state = str(Path.home()/'PycharmProjects/family_connect/state-client-build')
        return value.replace(str(state), '$STATE').replace(legacy_state, '$STATE')
    return value


for name in ('prepare.py','build.py','bounded.py','seal.py','check_artifact.py','publish_results.py',
             'candidate.patch','boundary.json','artifact-check.json','thermal.json'):
    shutil.copyfile(root/name,public/name)
for name in ('cumulative-source.json','gateway-source.json'):
    shutil.copyfile(root/'build'/name,public/name)
(public/'build-receipt.json').write_text(json.dumps(safe_json(receipt),indent=2)+'\n')
for name in ('prepare.py','run.py','run_gateway.py','prepare_gateway.py','summarize.py','summarize_gateway.py',
             'full_stack_test.go','gateway_stack_test.go','fixture_dns.go','results.json','gateway-results.json'):
    shutil.copyfile(stack/name,public/'full-stack'/name)
for directory in ('run-1','run-2','run-gateway-1'):
    shutil.copyfile(stack/directory/'receipts.json',public/'full-stack'/(directory+'-receipts.json'))
    if (stack/directory/'binaries.json').exists():
        shutil.copyfile(stack/directory/'binaries.json',public/'full-stack'/(directory+'-binaries.json'))
history = dict(first_batch=dict(result='FIXTURE_FAILURE',product_changed=False,
    clean_loss_passed=4,reorder_final_readback_failed=2,
    fixture_sha256=hashlib.sha256((stack/'run-1/full_stack_test.go').read_bytes()).hexdigest(),
    cause='delayed fixture kept per-call send context after sender cancelled it on return'),
    corrected_client_matrix=dict(normal=24,race=12,result='PASS'),
    exact_gateway_supplement=dict(normal=12,race=12,result='PASS'),
    automatic_retries=False,
    build_batches=1,phone_actions=0,server_actions=0,live_connects=0)
(public/'validation-history.json').write_text(json.dumps(history,indent=2)+'\n')
lines = [hashlib.sha256(filename.read_bytes()).hexdigest()+'  '+str(filename.relative_to(public))
         for filename in sorted(public.rglob('*')) if filename.is_file() and filename.name != 'SHA256SUMS']
(public/'SHA256SUMS').write_text('\n'.join(lines)+'\n')
print('Published safe research files:',len(lines))
