"""Normal code90 update: exact beta88 recovery/native, no extended beta89 trace."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import xml.etree.ElementTree as ET
import zipfile

from preserve import ROOT, WORK, digest


def main():
    os.umask(0o077)
    state = ROOT / 'state-client-build'
    parent = state / 'beta87-product-fix-20261019'
    source = WORK / 'android-source'
    output = WORK / 'android-build'
    output.mkdir(mode=0o700, exist_ok=True)
    assert not (output / 'receipt.json').exists()
    original = json.loads((parent / 'android88-build/source-inventory.json').read_text())
    assert all(digest(source / name) == value for name, value in original.items() if name != 'clients/android/app/build.gradle')
    inventory = dict(original)
    inventory['clients/android/app/build.gradle'] = digest(source / 'clients/android/app/build.gradle')
    import hashlib
    source_hash = hashlib.sha256(json.dumps(inventory, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    (output / 'source-inventory.json').write_text(json.dumps(inventory, indent=2))
    assets = output / 'research-assets'
    shutil.copytree(parent / 'android88-build/research-assets', assets, dirs_exist_ok=True)
    asset_path = assets / 'provisioning-seam-build.json'
    asset = json.loads(asset_path.read_text())
    asset['source_delta_sha256'] = source_hash
    asset_path.write_text(json.dumps(asset, indent=2))
    init = output / 'android.init.gradle'
    init.write_text((parent / 'android88-build/android.init.gradle').read_text().replace(str(parent / 'android88-build'), str(output)))
    tools = state / 'field65-export16/diag-source-freeze-1/resume-tools'
    environment = dict(os.environ, JAVA_HOME=str(tools / 'jdk'), ANDROID_HOME=str(tools / 'android'),
                       ANDROID_SDK_ROOT=str(tools / 'android'), GRADLE_USER_HOME=str(tools / 'gradle-home'))
    environment['PATH'] = str(tools / 'jdk/bin') + os.pathsep + environment['PATH']
    command = [tools / 'gradle-8.11.1/bin/gradle', '--offline', '--no-daemon', '--max-workers=1',
        '-I', init, '--project-cache-dir', output / 'cache', '-PfcTargetAbi=arm64-v8a', '-PfcFriendsCi=false',
        '-PfcProvisioningSeamSource=' + source_hash, '-PfcProvisioningSeamAssets=' + str(assets),
        '-PfcFriendsRestrictedDirectory=' + str(state / 'transport-write-batching-1/build/native'),
        '-PfcBuildPython=' + str(state / 'field65-export16/telemost-lease-continuity-1/build/tools/python/bin/python3.10'),
        '-PfcRadioNative=' + str(state / 'field65-export16/exit-krasnodar-candidate-1/audio-native'),
        ':app:assemblePrivateBeta', ':app:testPrivateBetaUnitTest']
    suites = ('TransportPresentationTest', 'DiagnosticRingTest', 'ConnectionTerminalTest', 'ConnectivityOrchestratorTest',
        'FriendsReadinessProtocolTest', 'ReadinessProductTest', 'RestrictedCacheTest', 'RestrictedBootstrapTest',
        'RestrictedRecoveryTest', 'RestrictedStartupTest', 'StartupFidelityTest', 'Ui60PresentationTest',
        'CutoverRecoveryTest', 'BootstrapCorrelationTest', 'AdmissionDiagnosticsTest', 'ReadinessBootstrapRouteTest',
        'ProductionProvisioningGateTest', 'AuthenticatedBootstrapRecoveryTest', 'NightRecoveryTest',
        'ControlOperationsTest', 'ControlStartupTest', 'ControlTransactionTest')
    for suite in suites:
        command += ['--tests', 'com.familyconnect.app.' + suite]
    log = output / ('gradle-' + str(time.time_ns()) + '.log')
    with log.open('xb') as handle:
        response = subprocess.run(list(map(str, command)), cwd=source / 'clients/android', env=environment,
                                  stdout=handle, stderr=subprocess.STDOUT, timeout=1200)
    if response.returncode:
        raise SystemExit('BUILD_FAILED_LOG_PRESERVED ' + str(log))
    results = [ET.parse(path).getroot().attrib for path in (output / 'android/app/test-results/testPrivateBetaUnitTest').glob('TEST-*.xml')]
    assert len(results) == len(suites)
    assert all(value['failures'] == value['errors'] == value['skipped'] == '0' for value in results)
    apk = output / 'android/app/outputs/apk/privateBeta/app-privateBeta-unsigned.apk'
    with zipfile.ZipFile(parent / 'delivery/FamilyConnect-0.1.18-beta88-recovery.apk') as before, zipfile.ZipFile(apk) as after:
        libraries = {name for name in before.namelist() if name.startswith('lib/')}
        assert len(libraries) == 12 and libraries == {name for name in after.namelist() if name.startswith('lib/')}
        assert all(before.read(name) == after.read(name) for name in libraries)
        manifest = json.loads(after.read('assets/restricted-build.json'))
        assert not manifest.get('build_tags') and not manifest.get('owner_diagnostic_fault_schema', 0)
        for name in after.namelist():
            if name.endswith('.dex'):
                assert b'FamilyConnectPerf' not in after.read(name)
    receipt = dict(result='PASS_LOCAL_BUILD_JVM', version_code=90, apk_sha256=digest(apk),
                   native_sha256='dd722eada0da7c890a8d71a72099cba5d0bbac1ce73377bbdbc8e7b85d820c23',
                   source_inventory=source_hash, all_12_native_libraries_equal_beta88=True,
                   java_equal_beta88=True, tests=sum(int(value['tests']) for value in results),
                   suites=results, build_log_sha256=digest(log), ci='NOT_RUN_PRIVATE_OWNER_UPDATE')
    assert all(digest(source / name) == expected for name, expected in inventory.items())
    (output / 'receipt.json').write_text(json.dumps(receipt, indent=2))
    print(json.dumps({key: receipt[key] for key in ('result', 'tests', 'apk_sha256', 'native_sha256', 'source_inventory')}))


if __name__ == '__main__':
    main()
