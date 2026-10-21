"""Rebase only the sealed completion-correctness delta, retaining Mux instrumentation."""
import difflib
import json
import re
import subprocess
from prepare import ROOT, WORK, digest

source = ROOT / 'state-client-build/queue-retry-20261019'
assert not (WORK/'queue-prerequisite.json').exists(), 'Completion delta already applied; preserve later edits'
pins = json.loads((ROOT / 'tests/fixtures/queue_retry/source-pins.json').read_text())['patches']['completion']
assert digest(ROOT / 'tests/fixtures/queue_retry/completion.patch') == pins['patch_sha256']
changes = {}
for name, hashes in pins['changes'].items():
    before = source / 'baseline-source/carrier' / name
    after = source / 'candidate-source/carrier' / name
    current = WORK / 'candidate' / name
    assert (digest(before) if before.exists() else None) == hashes['input_sha256']
    assert digest(after) == hashes['output_sha256']
    old = current.read_text() if current.exists() else ''
    if not before.exists() or old == before.read_text():
        new = after.read_text()
    else:
        result = subprocess.run(['git', 'merge-file', '-p', str(current), str(before), str(after)], text=True, capture_output=True)
        (WORK / ('merge-' + name.replace('/', '-') + '.log')).write_text(result.stdout + result.stderr)
        new = result.stdout
        if result.returncode == 3 and name == 'reliablestream/stream.go':
            conflicts = re.findall(r'^<<<<<<< [^\n]*\n(.*?)^=======\n(.*?)^>>>>>>> [^\n]*\n', new, re.M | re.S)
            assert len(conflicts) == 3
            assert 'submitted time.Time' in conflicts[0][0] and 'obsolete chan struct{}' in conflicts[0][1]
            assert 'CarrierAcceptedDATA.Add' in conflicts[1][0] and 'completion.Wait()' in conflicts[1][1]
            assert 'job.submitted = state.first' in conflicts[2][0] and 'job.block = state' in conflicts[2][1]
            resolutions = iter(['\t\tsubmitted time.Time\n' + conflicts[0][1],
                conflicts[1][0] + '\t\t}\n' + conflicts[1][1], conflicts[2][0] + conflicts[2][1]])
            new = re.sub(r'^<<<<<<< [^\n]*\n.*?^=======\n.*?^>>>>>>> [^\n]*\n', lambda _: next(resolutions), new, flags=re.M | re.S)
        else:
            assert result.returncode == 0, 'REVIEW_MERGE_CONFLICT_' + name
    if current.exists():
        patch = '*** Update File: ' + str(current) + '\n@@\n' + ''.join('-' + line + '\n' for line in old.splitlines())
    else:
        patch = '*** Add File: ' + str(current) + '\n'
    patch += ''.join('+' + line + '\n' for line in new.splitlines())
    subprocess.run(['apply_patch'], input='*** Begin Patch\n' + patch + '*** End Patch\n', text=True, check=True, stdout=subprocess.DEVNULL)
    changes[name] = dict(input=digest(WORK / 'baseline' / name) if (WORK / 'baseline' / name).exists() else None, output=digest(current))
(WORK / 'queue-prerequisite.json').write_text(json.dumps(dict(original_patch=pins['patch_sha256'], changes=changes, live=False, common_to_both_arms=True), indent=2))
print('COMPLETION_DELTA_REBASED_LOCAL_ONLY_BOTH_ARMS')
