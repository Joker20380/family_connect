"""Compile/test the reviewed UI84 presentation overlay; no signing or installation."""

import hashlib
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile


ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / 'state-client-build'
BASE = STATE / 'transport-write-batching-1'
WORK = STATE / 'mesh-product-20261018'
SOURCE = WORK / 'source'
OUTPUT = WORK / 'build'
TOOLS = STATE / 'field65-export16/diag-source-freeze-1/resume-tools'
CHANGED = {
    'clients/android/app/src/main/java/com/familyconnect/app/FriendsActivity.java',
    'clients/android/app/src/main/java/com/familyconnect/app/DiagnosticRing.java',
    'clients/android/app/src/main/java/com/familyconnect/app/TransportPresentation.java',
    'clients/android/app/src/test/java/com/familyconnect/app/DiagnosticRingTest.java',
    'clients/android/app/src/test/java/com/familyconnect/app/TransportPresentationTest.java',
    'clients/android/app/src/main/res/values/connection_terminal.xml',
    'clients/android/app/src/main/res/values-ru/connection_terminal.xml',
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--resume-after-sandbox', action='store_true')
    args = parser.parse_args()
    baseline = json.loads((BASE / 'cumulative-source.json').read_bytes())
    assert baseline['source_delta_sha256'] == 'cdd089478624ff5113d14590a340092684127a674565c3acfe6750aa76a17790'
    assert all(digest(BASE / 'source' / name) == expected for name, expected in baseline['files'].items())
    assert all(digest(SOURCE / name) == expected for name, expected in baseline['files'].items() if name not in CHANGED)
    assert digest(SOURCE / 'clients/android/app/build.gradle') == digest(BASE / 'source/clients/android/app/build.gradle')
    for name in ('TransportPresentation.java', 'TransportPresentationTest.java'):
        directory = 'main' if not name.endswith('Test.java') else 'test'
        path = Path('clients/android/app/src') / directory / 'java/com/familyconnect/app' / name
        assert digest(SOURCE / path) == digest(ROOT / path)
    if args.resume_after_sandbox:
        assert not (OUTPUT / 'receipt.json').exists()
        assert 'Operation not permitted' in (OUTPUT / 'gradle.log').read_text()
    OUTPUT.mkdir(mode=0o700, exist_ok=args.resume_after_sandbox)
    inventory = dict(baseline['files'])
    inventory.update({name: digest(SOURCE / name) for name in CHANGED})
    source_hash = hashlib.sha256(json.dumps(inventory, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    assets = OUTPUT / 'research-assets'
    shutil.copytree(BASE / 'build/research-assets', assets, dirs_exist_ok=args.resume_after_sandbox)
    manifest = json.loads((assets / 'provisioning-seam-build.json').read_bytes())
    manifest.update(source_delta_sha256=source_hash, presentation_only_derivative=True,
                    native_source_inventory=baseline['source_delta_sha256'], public_release=False)
    (assets / 'provisioning-seam-build.json').write_text(json.dumps(manifest, indent=2) + '\n')
    init = OUTPUT / 'android.init.gradle'
    init.write_text((BASE / 'build/android.init.gradle').read_text().replace(str(BASE / 'build'), str(OUTPUT)))
    environment = dict(os.environ, JAVA_HOME=str(TOOLS / 'jdk'), ANDROID_HOME=str(TOOLS / 'android'),
                       ANDROID_SDK_ROOT=str(TOOLS / 'android'), GRADLE_USER_HOME=str(TOOLS / 'gradle-home'))
    environment['PATH'] = str(TOOLS / 'jdk/bin') + os.pathsep + environment['PATH']
    command = [str(TOOLS / 'gradle-8.11.1/bin/gradle'), '--offline', '--no-daemon', '--max-workers=1',
        '-I', str(init), '--project-cache-dir', str(OUTPUT / 'cache'), '-PfcTargetAbi=arm64-v8a',
        '-PfcFriendsCi=false', '-PfcProvisioningSeamSource=' + source_hash,
        '-PfcProvisioningSeamAssets=' + str(assets), '-PfcFriendsRestrictedDirectory=' + str(BASE / 'build/native'),
        '-PfcBuildPython=' + str(STATE / 'field65-export16/telemost-lease-continuity-1/build/tools/python/bin/python3.10'),
        '-PfcRadioNative=' + str(STATE / 'field65-export16/exit-krasnodar-candidate-1/audio-native'),
        ':app:assembleResearchProvisioning', ':app:testResearchProvisioningUnitTest']
    for suite in ('TransportPresentationTest', 'DiagnosticRingTest', 'ConnectionTerminalTest',
                  'ConnectivityOrchestratorTest', 'FriendsReadinessProtocolTest', 'ReadinessProductTest',
                  'RestrictedCacheTest', 'RestrictedBootstrapTest', 'RestrictedRecoveryTest',
                  'RestrictedStartupTest', 'StartupFidelityTest', 'Ui60PresentationTest',
                  'CutoverRecoveryTest', 'BootstrapCorrelationTest', 'AdmissionDiagnosticsTest'):
        command.extend(['--tests', 'com.familyconnect.app.' + suite])
    log_name = 'gradle-outside-sandbox.log' if args.resume_after_sandbox else 'gradle.log'
    with (OUTPUT / log_name).open('xb') as log:
        completed = subprocess.run(command, cwd=SOURCE / 'clients/android', env=environment,
                                   stdout=log, stderr=subprocess.STDOUT, timeout=1200)
    assert completed.returncode == 0, 'Gradle failed: inspect build/gradle.log'
    results = [ET.parse(path).getroot().attrib for path in
               (OUTPUT / 'android/app/test-results/testResearchProvisioningUnitTest').glob('TEST-*.xml')]
    assert len(results) == 15 and all(item['failures'] == item['errors'] == item['skipped'] == '0' for item in results)
    apk = OUTPUT / 'android/app/outputs/apk/researchProvisioning/app-researchProvisioning-unsigned.apk'
    with zipfile.ZipFile(apk) as archive:
        native = hashlib.sha256(archive.read('lib/arm64-v8a/libfc_restricted.so')).hexdigest()
        assert native == 'dd722eada0da7c890a8d71a72099cba5d0bbac1ce73377bbdbc8e7b85d820c23'
    receipt = dict(result='PASS_BUILD_JVM', apk_sha256=digest(apk), native_sha256=native,
        source_inventory=source_hash, baseline_inventory=baseline['source_delta_sha256'], changed=sorted(CHANGED),
        suites=results, tests=sum(int(item['tests']) for item in results), signed=False, installed=False,
        distributed=False, release_version_changed=False, visual_device_qa=False)
    (OUTPUT / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, sort_keys=True))


if __name__ == '__main__':
    main()
