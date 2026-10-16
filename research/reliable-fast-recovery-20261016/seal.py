import difflib
import hashlib
import json
from pathlib import Path


root = Path(__file__).resolve().parent
retained = root.parent / 'ui60-layout-current-style-1/source'
candidate = root / 'candidate'
receipt = json.loads((root.parent / 'ui60-layout-current-style-1/build/cumulative-source.json').read_text())
assert receipt['source_delta_sha256'] == 'e90893aee5fdc04aae1cacd296d5291ca8a743350de42334b290f08504c48fce'
product = 'carrier/reliablestream/engine.go'
tests = ['carrier/reliablestream/fast_recovery_test.go', 'carrier/reliablestream/throughput_comparison_test.go']


def digest(source):
    return hashlib.sha256(source.read_bytes()).hexdigest()


def files(directory):
    return {str(source.relative_to(directory)): source for source in directory.rglob('*')
            if source.is_file() and not any(part in {'.git', 'build', '.gradle', '__pycache__'}
                                           for part in source.relative_to(directory).parts)}


for name, expected in receipt['files'].items():
    assert digest(retained / name) == expected, name
before, after = files(retained), files(candidate)
changed = sorted(name for name in before.keys() | after.keys()
                 if name not in before or name not in after or digest(before[name]) != digest(after[name]))
assert changed == sorted([product, *tests]), changed
baseline = files(root / 'baseline')
assert set(baseline) == set(before) | {tests[1]}
assert all(digest(baseline[name]) == digest(source) for name, source in before.items())
assert digest(baseline[tests[1]]) == digest(after[tests[1]])
inventory = {name: digest(candidate / name) for name in sorted(set(receipt['files']) | set(changed))}
identity = hashlib.sha256(json.dumps(inventory, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
patch = ''.join(''.join(difflib.unified_diff(before[name].read_text().splitlines(True) if name in before else [],
                    after[name].read_text().splitlines(True),
                    fromfile='a/'+name if name in before else '/dev/null', tofile='b/'+name)) for name in changed)
(root / 'candidate.patch').write_text(patch)
(root / 'cumulative-source.json').write_text(json.dumps(dict(base=receipt['base'], source_delta_sha256=identity, files=inventory), indent=2)+'\n')
boundary = dict(parent_inventory=receipt['source_delta_sha256'], candidate_inventory=identity,
                changed_files=changed, product_changed_files=[product],
                all_other_sources_identical=True, baseline_sources_identical=True, comparison_fixture_identical=True,
                parent_engine_sha256=digest(before[product]), candidate_engine_sha256=digest(after[product]),
                patch_sha256=hashlib.sha256(patch.encode()).hexdigest(),
                candidate_native_built=False, candidate_apk_built=False, candidate_gateway_built=False,
                installed_apk_and_gateway_untouched=True)
(root / 'boundary.json').write_text(json.dumps(boundary, indent=2)+'\n')
print(json.dumps(boundary, indent=2))
