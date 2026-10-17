import hashlib
import json
import os
from pathlib import Path
import subprocess
import zipfile


root = Path(__file__).resolve().parent
state = root.parent
tools = state / 'field65-export16/diag-source-freeze-1/resume-tools'
build_tools = tools / 'android/build-tools/35.0.0'
apk = root / 'build/android/app/outputs/apk/researchProvisioning/app-researchProvisioning-unsigned.apk'
previous = state / 'browser-admission-fix-1/build/android/app/outputs/apk/researchProvisioning/app-researchProvisioning-unsigned.apk'
receipt = json.loads((root / 'build/receipt.json').read_text())
assert all(run['exit'] == 0 for run in receipt['runs']) and len(receipt['runs']) == 6
assert receipt['result'] == 'PASS_LOCAL_COMBINED_BUILD'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


assert digest(previous.read_bytes()) == 'ff4a844f8de2df2aac4df5f7e5ec35ae10746033730177e3a9f19e8c0c35edda'
assert digest(apk.read_bytes()) == receipt['unsigned_apk_sha256']
badging = subprocess.check_output([str(build_tools / 'aapt'), 'dump', 'badging', str(apk)], text=True)
old_badging = subprocess.check_output([str(build_tools / 'aapt'), 'dump', 'badging', str(previous)], text=True)
assert "name='com.familyconnect.app.friends' versionCode='84' versionName='0.1.18-research84-ui60-4-batch1'" in badging
assert "sdkVersion:'31'" in badging and "native-code: 'arm64-v8a'" in badging
assert 'application-debuggable' not in badging
permissions = [line for line in badging.splitlines() if line.startswith('uses-permission')]
assert permissions == [line for line in old_badging.splitlines() if line.startswith('uses-permission')]
subprocess.run([str(build_tools / 'zipalign'), '-c', '-P', '16', '4', str(apk)], check=True)
with zipfile.ZipFile(apk) as current, zipfile.ZipFile(previous) as old:
    libraries = {name: digest(current.read(name)) for name in current.namelist() if name.startswith('lib/') and name.endswith('.so')}
    old_libraries = {name: digest(old.read(name)) for name in old.namelist() if name.startswith('lib/') and name.endswith('.so')}
    changed_libraries = [name for name in libraries if libraries[name] != old_libraries[name]]
    assert set(libraries) == set(old_libraries)
    assert changed_libraries == ['lib/arm64-v8a/libfc_restricted.so']
    assert libraries[changed_libraries[0]] == receipt['native_sha256']
    manifest = json.loads(current.read('assets/restricted-build.json'))
    assert manifest['source_delta_sha256'] == receipt['source_inventory']
    assert manifest['patch_sha256'] == digest(current.read('assets/Xray-modifications.patch'))
    assert manifest['binary_sha256'] == receipt['native_sha256']
    assert manifest['build_tags'] == [] and manifest['diagnostic_only'] is False
    assert manifest['owner_diagnostic_fault_schema'] == 0
    native_asset = json.loads(current.read('assets/provisioning-seam-build.json'))
    assert native_asset['source_delta_sha256'] == receipt['source_inventory']
    assert native_asset['public_release'] is False
    assert native_asset['ready_write_batching_derivative'] is True
env = dict(os.environ, JAVA_HOME=str(tools / 'jdk'))
env['PATH'] = str(tools / 'jdk/bin') + os.pathsep + env['PATH']
signature = subprocess.run([str(build_tools / 'apksigner'), 'verify', str(apk)], env=env, capture_output=True, text=True)
assert signature.returncode == 1 and 'DOES NOT VERIFY' in signature.stderr + signature.stdout
result = dict(unsigned_apk_sha256=receipt['unsigned_apk_sha256'], package='com.familyconnect.app.friends',
              version_code=84, version_name=receipt['version_name'], min_sdk=31, target_sdk=35,
              abi=['arm64-v8a'], debuggable=False, alignment='PASS_16K', unsigned_verified=True,
              native_libraries=libraries, changed_native_libraries=changed_libraries, permissions_unchanged=True,
              previous_unsigned_sha256=digest(previous.read_bytes()),
              native_manifest_matches_new_build=True, phone_read=False, installed=False)
(root / 'artifact-check.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({key: value for key, value in result.items() if key != 'native_libraries'}))
