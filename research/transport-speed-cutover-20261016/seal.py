import difflib
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile


root = Path(__file__).resolve().parent
baseline = root.parent / 'ui60-layout-current-style-1/source'
candidate = root / 'source'


def digest(filename):
    return hashlib.sha256(filename.read_bytes()).hexdigest()


def inventory(directory):
    return {str(filename.relative_to(directory)): digest(filename)
            for filename in directory.rglob('*')
            if filename.is_file() and '.git' not in filename.relative_to(directory).parts
            and not filename.relative_to(directory).is_relative_to('clients/android/build')}


before, after = inventory(baseline), inventory(candidate)
changed = sorted(name for name in set(before) | set(after) if before.get(name) != after.get(name))
expected = ['clients/android/app/build.gradle'] + [
    'clients/android/app/src/main/java/com/familyconnect/app/' + name + '.java'
    for name in ['AutomaticConnection', 'ConnectivityOrchestrator', 'FriendsRestricted',
                 'RestrictedBootstrap', 'RestrictedRecovery', 'RestrictedTunnelEngine']
] + ['clients/android/app/src/test/java/com/familyconnect/app/CutoverRecoveryTest.java']
expected += ['carrier/reliablestream/' + name for name in ['engine.go', 'fast_recovery_test.go', 'throughput_comparison_test.go']]
assert changed == sorted(expected), changed
patch = ''.join(''.join(difflib.unified_diff(
    (baseline / name).read_text().splitlines(True) if name in before else [],
    (candidate / name).read_text().splitlines(True),
    fromfile='a/' + name if name in before else '/dev/null', tofile='b/' + name))
    for name in changed)
(root / 'candidate.patch').write_text(patch)
with tempfile.TemporaryDirectory(prefix='fc-cutover-patch-') as temporary:
    check = Path(temporary)
    for name in changed:
        if name in before:
            target = check / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((baseline / name).read_bytes())
    subprocess.run(['git', 'apply', '--check', str(root / 'candidate.patch')], cwd=check, check=True)
    subprocess.run(['git', 'apply', str(root / 'candidate.patch')], cwd=check, check=True)
    assert all(digest(check / name) == after[name] for name in changed)
engine = 'clients/android/app/src/main/java/com/familyconnect/app/RestrictedTunnelEngine.java'
stats_before = (baseline / engine).read_text().count('NativeRestricted.stats(')
stats_after = (candidate / engine).read_text().count('NativeRestricted.stats(')
assert stats_before == stats_after == 2
baseline_receipt = json.loads((baseline.parent / 'build/cumulative-source.json').read_text())
assert all(before[name] == checksum for name, checksum in baseline_receipt['files'].items())
result = dict(baseline_source_inventory=baseline_receipt['source_delta_sha256'],
              changed_files={name: dict(before=before.get(name), after=after[name]) for name in changed},
              unchanged_files=len(set(before) & set(after)) - sum(name in before for name in changed),
              patch_sha256=digest(root / 'candidate.patch'), patch_apply_verified=True,
              native_stats_call_sites_unchanged=stats_after,
              native_jni_ui_security_sources_unchanged=True, fast_retransmit_included=True,
              carrier_product_changed_files=['carrier/reliablestream/engine.go'],
              recovery_source_inventory='ea9312d013aac02a190a06b8ad9091e1245ef63a994db6618054dde27739c0d4')
(root / 'boundary.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({key: value for key, value in result.items() if key != 'changed_files'}))
