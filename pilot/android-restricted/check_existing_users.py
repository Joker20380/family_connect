"""Build an identity-preserving private beta from sealed UI84, without signing."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile

from check_mesh_ui import CHANGED as PRESENTATION, TOOLS, STATE, BASE, digest


WORK = STATE / 'existing-users-beta-20261019'
SOURCE = WORK / 'android87-source'
OUTPUT = WORK / 'android87-build'
JAVA = 'clients/android/app/src/main/java/com/familyconnect/app/'
DELTA = PRESENTATION | {JAVA + name + '.java' for name in (
    'FriendsAccessAndroid', 'ControlRnsAndroid', 'ReadinessBootstrapRoute', 'RestrictedRecovery')}
DELTA |= {'clients/android/app/build.gradle',
          'clients/android/app/src/main/python/fc_rns_transport.py',
          'clients/android/app/src/test/java/com/familyconnect/app/ReadinessBootstrapRouteTest.java'}
DELTA |= {'clients/android/app/src/testPrivateBeta/java/com/familyconnect/app/ProductionProvisioningGateTest.java'}
DELTA |= {'clients/android/app/src/test/java/com/familyconnect/app/AuthenticatedBootstrapRecoveryTest.java'}


def main():
    baseline = json.loads((BASE / 'cumulative-source.json').read_bytes())
    assert baseline['source_delta_sha256'] == 'cdd089478624ff5113d14590a340092684127a674565c3acfe6750aa76a17790'
    assert all(digest(BASE / 'source' / name) == expected for name, expected in baseline['files'].items())
    assert all(digest(SOURCE / name) == expected for name, expected in baseline['files'].items() if name not in DELTA)
    inventory = dict(baseline['files'])
    inventory.update({name: digest(SOURCE / name) for name in DELTA})
    source_hash = hashlib.sha256(json.dumps(inventory, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    OUTPUT.mkdir(mode=0o700, exist_ok=True)
    assert not (OUTPUT / 'receipt.json').exists(), 'Verified output is immutable'
    assets = OUTPUT / 'research-assets'
    shutil.copytree(BASE / 'build/research-assets', assets, dirs_exist_ok=True)
    manifest = json.loads((assets / 'provisioning-seam-build.json').read_bytes())
    manifest.update(source_delta_sha256=source_hash, native_source_inventory=baseline['source_delta_sha256'],
                    public_release=False)
    (assets / 'provisioning-seam-build.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (OUTPUT / 'source-inventory.json').write_text(json.dumps(inventory, indent=2) + '\n')
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
        ':app:assemblePrivateBeta', ':app:testPrivateBetaUnitTest']
    suites = ('TransportPresentationTest', 'DiagnosticRingTest', 'ConnectionTerminalTest',
        'ConnectivityOrchestratorTest', 'FriendsReadinessProtocolTest', 'ReadinessProductTest',
        'RestrictedCacheTest', 'RestrictedBootstrapTest', 'RestrictedRecoveryTest', 'RestrictedStartupTest',
        'StartupFidelityTest', 'Ui60PresentationTest', 'CutoverRecoveryTest', 'BootstrapCorrelationTest',
        'AdmissionDiagnosticsTest', 'ReadinessBootstrapRouteTest', 'ProductionProvisioningGateTest',
        'AuthenticatedBootstrapRecoveryTest')
    for suite in suites:
        command.extend(['--tests', 'com.familyconnect.app.' + suite])
    with (OUTPUT / ('gradle-' + str(__import__('time').time_ns()) + '.log')).open('xb') as log:
        completed = subprocess.run(command, cwd=SOURCE / 'clients/android', env=environment,
                                   stdout=log, stderr=subprocess.STDOUT, timeout=1200)
    assert completed.returncode == 0, 'Gradle failed; inspect bounded log tail'
    results = [ET.parse(path).getroot().attrib for path in
        (OUTPUT / 'android/app/test-results/testPrivateBetaUnitTest').glob('TEST-*.xml')]
    assert len(results) == len(suites) and all(item['failures'] == item['errors'] == item['skipped'] == '0' for item in results)
    apk = OUTPUT / 'android/app/outputs/apk/privateBeta/app-privateBeta-unsigned.apk'
    accepted = BASE / 'owner-install/private/FamilyConnect-ui60-4-batch1-signed.apk'
    assert digest(accepted) == '697f9c244b67f75e7e3e612dbcd91a48891d32ee77e23fd9bce173a5f049233f'
    with zipfile.ZipFile(accepted) as old, zipfile.ZipFile(apk) as new:
        names = {name for name in old.namelist() if name.startswith('lib/')}
        assert names == {name for name in new.namelist() if name.startswith('lib/')}
        native = {name: hashlib.sha256(new.read(name)).hexdigest() for name in sorted(names)}
        assert all(old.read(name) == new.read(name) for name in names)
    receipt = dict(result='PASS_LOCAL_BUILD_JVM', apk_sha256=digest(apk), native=native,
        source_inventory=source_hash, baseline_inventory=baseline['source_delta_sha256'], changed=sorted(DELTA),
        suites=results, tests=sum(int(item['tests']) for item in results), signed=False, installed=False,
        distributed=False, ci='NOT_RUN', version_code=87, package='com.familyconnect.app.friends',
        variant='privateBeta', provisioning_research_gate=False)
    (OUTPUT / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({name: receipt[name] for name in ('result', 'apk_sha256', 'tests', 'source_inventory')}, sort_keys=True))


if __name__ == '__main__':
    main()
