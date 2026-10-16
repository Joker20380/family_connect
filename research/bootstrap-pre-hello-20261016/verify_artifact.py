import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

parser = argparse.ArgumentParser()
for name in ('task', 'retained', 'tools'):
    parser.add_argument('--'+name, type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parent
old = json.loads((args.retained/'cumulative-source.json').read_text())
build = args.task/'gradle-native-export-final'
new = json.loads((build/'cumulative-source.json').read_text())
assert old['source_delta_sha256'] == 'c2dc3dd860044b31696893244995cbc5cc8eb805ee34319df99cce085cf40d08'
assert hashlib.sha256(json.dumps(old['files'], sort_keys=True, separators=(',', ':')).encode()).hexdigest() == old['source_delta_sha256']
changed = {name for name in old['files'].keys() | new['files'].keys() if old['files'].get(name) != new['files'].get(name)}
assert changed == set(json.loads((root/'source-manifest.json').read_text())['files'])
receipt = json.loads((build/'receipt.json').read_text())
apk = build/'android/app/outputs/apk/researchProvisioning/app-researchProvisioning-unsigned.apk'
previous = args.retained/'android/app/outputs/apk/researchProvisioning/app-researchProvisioning-unsigned.apk'
build_tools = args.tools/'android/build-tools/35.0.0'
def inspect(path):
    return subprocess.check_output([build_tools/'aapt','dump','badging',path], text=True)
badging, old_badging = inspect(apk), inspect(previous)
identity = lambda text: [line for line in text.splitlines() if line.startswith(('package:', 'sdkVersion:', 'targetSdkVersion:', 'uses-permission:'))]
assert identity(badging) == identity(old_badging)
with zipfile.ZipFile(apk) as bundle, zipfile.ZipFile(previous) as prior:
    assert hashlib.sha256(prior.read('lib/arm64-v8a/libfc_restricted.so')).hexdigest() == '253e0e15f38223288571d3e682f6876269aa9c6d1c0c5157588ed8287ba6f3a3'
    native = hashlib.sha256(bundle.read('lib/arm64-v8a/libfc_restricted.so')).hexdigest()
    assert native == receipt['native_sha256']
    assert bundle.read('AndroidManifest.xml') == prior.read('AndroidManifest.xml')
    embedded = json.loads(bundle.read('assets/restricted-build.json'))
    assert embedded['binary_sha256'] == native and embedded['source_delta_sha256'] == new['source_delta_sha256']
    assert json.loads(bundle.read('assets/provisioning-seam-build.json'))['source_delta_sha256'] == new['source_delta_sha256']
alignment = subprocess.run([build_tools/'zipalign','-c','-P','16','4',apk], capture_output=True, text=True)
assert alignment.returncode == 0, alignment.stderr
signing = subprocess.run([args.tools/'jdk/bin/java','-jar',build_tools/'lib/apksigner.jar','verify',apk], capture_output=True, text=True)
assert signing.returncode != 0 and 'Missing META-INF/MANIFEST.MF' in signing.stderr
result = dict(result='PASS_UNSIGNED_LOCAL', identity=identity(badging), manifest_byte_identical=True,
              alignment_16k=True, unsigned_verify_exit=signing.returncode, unsigned_reason=signing.stderr.strip(),
              apk_sha256=hashlib.sha256(apk.read_bytes()).hexdigest(), native_sha256=native,
              source_inventory=new['source_delta_sha256'], delta_files=sorted(changed),
              runtime_policy_files_unchanged=True, signing_install_live_actions=0)
(root/'results/artifact-checks.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result, indent=2))
