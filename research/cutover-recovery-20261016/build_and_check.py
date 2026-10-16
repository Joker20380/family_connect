import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import zipfile
import xml.etree.ElementTree as ET


root = Path(__file__).resolve().parent
state = root.parent
source = root / 'source'
baseline = state / 'ui60-layout-current-style-1'
accepted = state / 'bootstrap-pre-hello-correlation-1/gradle-native-export-final'
tools = state / 'field65-export16/diag-source-freeze-1/resume-tools'
out = root / 'build'
out.mkdir(exist_ok=True)


def digest(filename):
    return hashlib.sha256(filename.read_bytes()).hexdigest()


def git(*args):
    return subprocess.check_output(['git', '-C', str(source), *args], text=True).strip()


names = set(git('diff', '--name-only').splitlines() + git('ls-files', '--others', '--exclude-standard').splitlines())
inventory = {name: digest(source / name) for name in sorted(names)}
delta = hashlib.sha256(json.dumps(inventory, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
(out / 'cumulative-source.json').write_text(json.dumps(dict(base=git('rev-parse', 'HEAD'), source_delta_sha256=delta, files=inventory), indent=2) + '\n')
for folder in ['carrier', 'pilot/android-restricted/native']:
    for filename in (baseline / 'source' / folder).rglob('*'):
        if filename.is_file():
            assert digest(filename) == digest(source / filename.relative_to(baseline / 'source'))
native = out / 'native'
shutil.copytree(accepted / 'native', native, dirs_exist_ok=True)
manifest = json.loads((native / 'assets/restricted-build.json').read_bytes())
assert manifest['source_delta_sha256'] == 'b36c4a21ee6cf04acb192a0e6d140fa565b3e5ae75f6fc8d028d029c3152781d'
assert digest(native / 'jniLibs/arm64-v8a/libfc_restricted.so') == manifest['binary_sha256'] == 'be70a66ccc2bcbf0478915fd414c32de3bedb2a0ae0c3222a53e65eebd0a92b2'
assets = out / 'research-assets'
assets.mkdir(exist_ok=True)
asset = json.loads((accepted / 'research-assets/provisioning-seam-build.json').read_bytes())
asset.update(source_delta_sha256=delta, public_release=False, ui_only_derivative=False,
             java_recovery_derivative=True, native_source_inventory=manifest['source_delta_sha256'])
(assets / 'provisioning-seam-build.json').write_text(json.dumps(asset, indent=2) + '\n')
init = out / 'android.init.gradle'
init.write_text((baseline / 'build/android.init.gradle').read_text().replace('/mnt/data/PycharmProjects/family_connect', str(state.parent)).replace(str(baseline / 'build'), str(out)))
env = dict(os.environ, JAVA_HOME=str(tools / 'jdk'), ANDROID_HOME=str(tools / 'android'),
           ANDROID_SDK_ROOT=str(tools / 'android'), GRADLE_USER_HOME=str(tools / 'gradle-home'))
env['PATH'] = str(tools / 'jdk/bin') + os.pathsep + env['PATH']
command = [str(tools / 'gradle-8.11.1/bin/gradle'), '--offline', '--no-daemon', '--max-workers=1',
           '-I', str(init), '--project-cache-dir', str(out / 'cache'), '-PfcTargetAbi=arm64-v8a',
           '-PfcFriendsCi=false', '-PfcProvisioningSeamSource=' + delta,
           '-PfcProvisioningSeamAssets=' + str(assets), '-PfcFriendsRestrictedDirectory=' + str(native),
           '-PfcBuildPython=' + str(state / 'field65-export16/telemost-lease-continuity-1/build/tools/python/bin/python3.10'),
           '-PfcRadioNative=' + str(state / 'field65-export16/exit-krasnodar-candidate-1/audio-native')]
tests = ['CutoverRecoveryTest', 'ConnectivityOrchestratorTest', 'RestrictedBootstrapTest',
         'RestrictedRecoveryTest', 'ReadinessProductTest', 'RestrictedCacheTest',
         'FriendsReadinessProtocolTest', 'RestrictedStartupTest', 'StartupFidelityTest',
         'DiagnosticRingTest', 'BootstrapCorrelationTest', 'Ui60PresentationTest']
receipt = dict(source_inventory=delta, native_sha256=manifest['binary_sha256'],
               native_source_inventory=manifest['source_delta_sha256'], native_rebuilt=False,
               version_name='0.1.18-research84-ui60-4-recovery1', version_code=84, runs=[])
for label, selected, tasks in [('assemble-tests', tests, [':app:assembleResearchProvisioning', ':app:testResearchProvisioningUnitTest']),
                              ('fixed-repeat', ['CutoverRecoveryTest'], [':app:testResearchProvisioningUnitTest'])]:
    invocation = command + tasks
    for test in selected:
        invocation += ['--tests', 'com.familyconnect.app.' + test]
    log = out / (label + '.log')
    with log.open('wb') as output:
        result = subprocess.run(invocation, cwd=source / 'clients/android', env=env,
                                stdout=output, stderr=subprocess.STDOUT, timeout=1200)
    summary = dict(label=label, exit=result.returncode, log_sha256=digest(log), suites=[])
    reports = out / ('reports-' + label)
    reports.mkdir(exist_ok=True)
    for filename in (out / 'android/app/test-results/testResearchProvisioningUnitTest').glob('TEST-*.xml'):
        shutil.copy2(filename, reports / filename.name)
        suite = ET.parse(filename).getroot()
        summary['suites'].append({key: suite.attrib.get(key) for key in ['name', 'tests', 'failures', 'errors', 'skipped']})
    receipt['runs'].append(summary)
    (out / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    if result.returncode:
        raise SystemExit(result.returncode)
apk = out / 'android/app/outputs/apk/researchProvisioning/app-researchProvisioning-unsigned.apk'
with zipfile.ZipFile(apk) as bundle:
    assert hashlib.sha256(bundle.read('lib/arm64-v8a/libfc_restricted.so')).hexdigest() == manifest['binary_sha256']
    assert bundle.read('assets/restricted-build.json') == (native / 'assets/restricted-build.json').read_bytes()
receipt.update(unsigned_apk_sha256=digest(apk), apk_size=apk.stat().st_size,
               embedded_native_verified=True, signing=False, installed=False)
(out / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt))
