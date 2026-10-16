import difflib
import hashlib
import json
from pathlib import Path
import re

root = Path(__file__).resolve().parent
source = root / 'source'
accepted = root.parent / 'bootstrap-pre-hello-correlation-1/reconstructed-final'
java = 'clients/android/app/src/main/java/com/familyconnect/app/'
allowed = {java + name + '.java' for name in ['FriendsActivity', 'TerminalUi', 'LiveNetworkPanel', 'TerminalToggle', 'RouteMapView', 'Ui60Presentation']}
allowed |= {'clients/android/app/build.gradle', 'clients/android/app/src/main/res/values/ui60.xml', 'clients/android/app/src/main/res/values-ru/ui60.xml', 'clients/android/app/src/test/java/com/familyconnect/app/Ui60PresentationTest.java'}
allowed.add('clients/android/app/src/androidTest/java/com/familyconnect/app/DashboardLayoutRuntimeTest.java')

def files(directory):
    return {str(path.relative_to(directory)): path for path in directory.rglob('*') if path.is_file() and not any(part in {'.git', 'build', '.gradle', '__pycache__'} for part in path.relative_to(directory).parts)}

old, new = files(accepted), files(source)
changed = sorted(name for name in old.keys() | new.keys() if name not in old or name not in new or old[name].read_bytes() != new[name].read_bytes())
assert set(changed) <= allowed, set(changed) - allowed
assert all(name in new for name in old), 'Removed accepted source'
before = old[java + 'FriendsActivity.java'].read_text()
after = new[java + 'FriendsActivity.java'].read_text()
for start, end in [('    void navigate(', '    private LinearLayout dialogContent('), ('    private void showRoute(', '    private void render(){'), ('    private String pendingInvitation=', '    private String loadTarget('), ('    private String loadTarget(', None)]:
    assert before[before.index(start):before.index(end) if end else len(before)] == after[after.index(start):after.index(end) if end else len(after)], start
before_panel, after_panel = old[java + 'LiveNetworkPanel.java'].read_text(), new[java + 'LiveNetworkPanel.java'].read_text()
assert before_panel[before_panel.index('    void sample()'):before_panel.index('    private void display()')] == after_panel[after_panel.index('    void sample()'):after_panel.index('    private void display()')]
patch = ''.join(''.join(difflib.unified_diff(old[name].read_text().splitlines(True) if name in old else [], new[name].read_text().splitlines(True), fromfile='a/'+name if name in old else '/dev/null', tofile='b/'+name)) for name in changed)
(root / 'ui-only.patch').write_text(patch)
receipt = dict(changed_files=changed, non_ui_sources_identical=True, friends_navigation_lifecycle_and_operations_identical=True, telemetry_sample_accept_pause_identical=True, native_rebuilt=False, delta_patch_sha256=hashlib.sha256(patch.encode()).hexdigest())
previous_inventory = root / 'revisions/ui60-2/cumulative-source.json'
if previous_inventory.exists():
    previous_files = json.loads(previous_inventory.read_text())['files']
    revision_changes = sorted(name for name, digest in previous_files.items() if hashlib.sha256((source / name).read_bytes()).hexdigest() != digest)
    assert revision_changes == ['clients/android/app/build.gradle', java + 'RouteMapView.java'], revision_changes
    receipt['revision3_changes_from_revision2'] = revision_changes
(root / 'boundary.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt))
