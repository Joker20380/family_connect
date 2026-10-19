"""Offline exact-source beta89 observation build; no signing/install/deployment."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[3]
STATE = ROOT / 'state-client-build'
WORK = Path(os.environ.get('MESH_TRACE_OUT', STATE / 'mesh-throughput-trace-20261019'))
SOURCE = WORK / 'android-source'
OUT = WORK / 'build'
TOOLS = STATE / 'field65-export16/diag-source-freeze-1/resume-tools'
BASE = STATE / 'transport-write-batching-1'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    os.umask(0o077)
    OUT.mkdir(mode=0o700, exist_ok=True)
    assert not (OUT / 'receipt.json').exists()
    receipt = dict(result='IN_PROGRESS', runs=[], version_code=89, version='0.1.18-beta89-mesh-trace',
                   signing=False, installed=False, distributed=False, ci='NOT_RUN')
    changed = subprocess.check_output(['git', 'diff', '--name-only'], cwd=SOURCE, text=True).splitlines()
    changed += subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard'], cwd=SOURCE, text=True).splitlines()
    inventory = {name: digest(SOURCE / name) for name in sorted(changed)}
    source_hash = hashlib.sha256(json.dumps(inventory, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    receipt['source_inventory'] = source_hash
    (OUT / 'source-inventory.json').write_text(json.dumps(inventory, indent=2))
    parent = STATE / 'beta87-product-fix-20261019/android88-source'
    for name in ('AutomaticConnection', 'ConnectivityOrchestrator', 'ConnectionService', 'TcpVpnService',
                 'RestrictedBootstrap', 'RestrictedCache', 'ConnectionResume', 'RestrictedRecovery'):
        relative = Path('clients/android/app/src/main/java/com/familyconnect/app') / (name + '.java')
        assert digest(SOURCE / relative) == digest(parent / relative)
    receipt['beta88_recovery_sources_unchanged'] = True

    def run(label, command, cwd, environment, timeout=1200):
        log = OUT / (label + '-' + str(time.time_ns()) + '.log')
        print('START', label, flush=True)
        with log.open('xb') as handle:
            completed = subprocess.run(list(map(str, command)), cwd=cwd, env=environment,
                                       stdout=handle, stderr=subprocess.STDOUT, timeout=timeout)
        receipt['runs'].append(dict(label=label, exit=completed.returncode, log=log.name, sha256=digest(log)))
        (OUT / 'progress.json').write_text(json.dumps(receipt, indent=2))
        if completed.returncode:
            raise SystemExit(label + ' failed; bounded log retained')
        print('PASS', label, flush=True)

    go = TOOLS / 'go/bin/go'
    environment = {key: value for key, value in os.environ.items()
                   if not key.startswith(('FC_', 'YANDEX_', 'GO', 'CGO_', 'CC'))}
    environment.update(GOMAXPROCS='2', GOTOOLCHAIN='local', GOWORK='off', GOPROXY='off', GOSUMDB='off',
                       GOCACHE=str(WORK / 'native-cache'), GOPATH=str(TOOLS / 'gopath'),
                       GOOS='android', GOARCH='arm64', CGO_ENABLED='1',
                       CC=str(TOOLS / 'android/ndk/28.2.13676358/toolchains/llvm/prebuilt/linux-x86_64/bin/aarch64-linux-android26-clang'),
                       CGO_LDFLAGS='-Wl,-z,max-page-size=16384')
    module = OUT / 'native.mod'
    shutil.copyfile(SOURCE / 'pilot/android-restricted/go.mod', module)
    shutil.copyfile(SOURCE / 'pilot/android-restricted/go.sum', OUT / 'native.sum')
    run('module', [go, 'mod', 'edit', '-modfile=' + str(module),
        '-replace=github.com/Joker20380/family_connect/carrier=' + str(SOURCE / 'carrier'),
        '-replace=github.com/xtls/xray-core=' + str(BASE / 'xray')], SOURCE / 'pilot/android-restricted', environment)
    native = OUT / 'native'
    binary = native / 'jniLibs/arm64-v8a/libfc_restricted.so'
    binary.parent.mkdir(parents=True, exist_ok=True)
    run('native', [go, 'build', '-p=1', '-buildvcs=false', '-modfile=' + str(module), '-trimpath',
        '-tags=fc_perf_diagnostic', '-ldflags=-checklinkname=0', '-buildmode=c-shared', '-o', binary, './native'],
        SOURCE / 'pilot/android-restricted', environment)
    receipt['native_sha256'] = digest(binary)
    receipt['native_buildinfo'] = subprocess.check_output([go, 'version', '-m', binary], text=True, env=environment)
    shutil.copytree(BASE / 'build/native/assets', native / 'assets', dirs_exist_ok=True)
    manifest_path = native / 'assets/restricted-build.json'
    manifest = json.loads(manifest_path.read_text())
    manifest.update(binary_sha256=digest(binary), source_delta_sha256=source_hash,
                    build_tags=['fc_perf_diagnostic'], performance_metadata_schema=1,
                    owner_diagnostic_fault_schema=0, actual_runner_sha256=digest(Path(__file__)),
                    actual_build_receipt='mesh-throughput-trace-20261019/build/receipt.json')
    manifest_path.write_text(json.dumps(manifest, indent=2))
    assets = OUT / 'research-assets'
    shutil.copytree(parent.parent / 'android88-build/research-assets', assets, dirs_exist_ok=True)
    asset_path = assets / 'provisioning-seam-build.json'
    asset = json.loads(asset_path.read_text())
    asset.update(source_delta_sha256=source_hash, native_source_inventory=source_hash, public_release=False, native_rebuilt=True)
    asset_path.write_text(json.dumps(asset, indent=2))
    init = OUT / 'android.init.gradle'
    init.write_text((parent.parent / 'android88-build/android.init.gradle').read_text().replace(str(parent.parent / 'android88-build'), str(OUT)))
    gradle_env = dict(environment, JAVA_HOME=str(TOOLS / 'jdk'), ANDROID_HOME=str(TOOLS / 'android'),
                      ANDROID_SDK_ROOT=str(TOOLS / 'android'), GRADLE_USER_HOME=str(TOOLS / 'gradle-home'))
    gradle_env['PATH'] = str(TOOLS / 'jdk/bin') + os.pathsep + gradle_env['PATH']
    command = [TOOLS / 'gradle-8.11.1/bin/gradle', '--offline', '--no-daemon', '--max-workers=1',
        '-I', init, '--project-cache-dir', OUT / 'cache', '-PfcTargetAbi=arm64-v8a', '-PfcFriendsCi=false',
        '-PfcProvisioningSeamSource=' + source_hash, '-PfcProvisioningSeamAssets=' + str(assets),
        '-PfcFriendsRestrictedDirectory=' + str(native),
        '-PfcBuildPython=' + str(STATE / 'field65-export16/telemost-lease-continuity-1/build/tools/python/bin/python3.10'),
        '-PfcRadioNative=' + str(STATE / 'field65-export16/exit-krasnodar-candidate-1/audio-native'),
        ':app:assemblePrivateBeta', ':app:testPrivateBetaUnitTest']
    suites = ('TransportPresentationTest', 'DiagnosticRingTest', 'ConnectionTerminalTest', 'ConnectivityOrchestratorTest',
        'FriendsReadinessProtocolTest', 'ReadinessProductTest', 'RestrictedCacheTest', 'RestrictedBootstrapTest',
        'RestrictedRecoveryTest', 'RestrictedStartupTest', 'StartupFidelityTest', 'Ui60PresentationTest',
        'CutoverRecoveryTest', 'BootstrapCorrelationTest', 'AdmissionDiagnosticsTest', 'ReadinessBootstrapRouteTest',
        'ProductionProvisioningGateTest', 'AuthenticatedBootstrapRecoveryTest', 'NightRecoveryTest',
        'ControlOperationsTest', 'ControlStartupTest', 'ControlTransactionTest')
    for suite in suites:
        command += ['--tests', 'com.familyconnect.app.' + suite]
    run('gradle', command, SOURCE / 'clients/android', gradle_env)
    results = [ET.parse(path).getroot().attrib for path in (OUT / 'android/app/test-results/testPrivateBetaUnitTest').glob('TEST-*.xml')]
    assert len(results) == len(suites)
    assert all(value['failures'] == value['errors'] == value['skipped'] == '0' for value in results)
    apk = OUT / 'android/app/outputs/apk/privateBeta/app-privateBeta-unsigned.apk'
    with zipfile.ZipFile(parent.parent / 'delivery/FamilyConnect-0.1.18-beta88-recovery.apk') as before, zipfile.ZipFile(apk) as after:
        libs = {name for name in before.namelist() if name.startswith('lib/')}
        assert len(libs) == 12 and libs == {name for name in after.namelist() if name.startswith('lib/')}
        assert [name for name in sorted(libs) if before.read(name) != after.read(name)] == ['lib/arm64-v8a/libfc_restricted.so']
        assert hashlib.sha256(after.read('lib/arm64-v8a/libfc_restricted.so')).hexdigest() == digest(binary)
    receipt.update(result='PASS_LOCAL_BUILD_JVM', apk_sha256=digest(apk), tests=sum(int(value['tests']) for value in results), suites=results)
    assert all(digest(SOURCE / name) == expected for name, expected in inventory.items())
    with (OUT / 'receipt.json').open('x') as handle:
        json.dump(receipt, handle, indent=2)
    print(json.dumps({key: receipt[key] for key in ('result', 'apk_sha256', 'native_sha256', 'source_inventory', 'tests')}))


if __name__ == '__main__':
    main()
