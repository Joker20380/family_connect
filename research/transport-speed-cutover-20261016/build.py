import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile


root = Path(__file__).resolve().parent
state = root.parent
source = root / 'source'
out = root / 'build'
out.mkdir(exist_ok=False)
tools = state / 'field65-export16/diag-source-freeze-1/resume-tools'
accepted = state / 'bootstrap-pre-hello-correlation-1/gradle-native-export-final'
native_source = source / 'pilot/android-restricted'
native = out / 'native'
go = tools / 'go/bin/go'
compiler = tools / 'android/ndk/28.2.13676358/toolchains/llvm/prebuilt/linux-x86_64/bin/aarch64-linux-android26-clang'
receipt = dict(result='IN_PROGRESS', version_name='0.1.18-research84-ui60-4-speed-recovery1',
               version_code=84, native_rebuilt=True, signing=False, installed=False, runs=[])


def digest(filename):
    return hashlib.sha256(filename.read_bytes()).hexdigest()


def git(*args):
    return subprocess.check_output(['git', '-C', str(source), *args], text=True).strip()


def save():
    (out / 'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')


def run(label, command, cwd, environment, timeout=900):
    logfile = out / (label+'.log')
    print('START', label, flush=True)
    status = 'INTERRUPTED'
    try:
        with logfile.open('xb') as output:
            status = subprocess.run(list(map(str, command)), cwd=cwd, env=environment,
                                    stdout=output, stderr=subprocess.STDOUT, timeout=timeout).returncode
    finally:
        receipt['runs'].append(dict(label=label, exit=status, command=list(map(str,command)), log_sha256=digest(logfile)))
        save()
    print('END', label, status, flush=True)
    if status != 0:
        raise SystemExit('Build/check failed; no automatic retry')


names = set(git('diff', '--name-only').splitlines() + git('ls-files', '--others', '--exclude-standard').splitlines())
inventory = {name: digest(source / name) for name in sorted(names)}
delta = hashlib.sha256(json.dumps(inventory, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
base = git('rev-parse', 'HEAD')
assert base == 'f5240994869826c6a28f59e58e38256c688cf6eb'
(out / 'cumulative-source.json').write_text(json.dumps(dict(base=base, source_delta_sha256=delta, files=inventory), indent=2)+'\n')
receipt['source_inventory'] = delta
assert digest(source/'carrier/reliablestream/engine.go') == digest(state/'reliable-full-stack-1/candidate/carrier/reliablestream/engine.go')
assert not (source/'carrier/tcpforward/fixture_dns.go').exists()
assert not (source/'carrier/telemost/full_stack_test.go').exists()
environment = dict(os.environ, GOMAXPROCS='1', GOTOOLCHAIN='local', GOWORK='off', GOPROXY='off', GOSUMDB='off',
    GOCACHE=str(state/'bootstrap-pre-hello-correlation-1/native-build/go-cache'), GOPATH=str(tools/'gopath'),
    GOMODCACHE=str(tools/'gopath/pkg/mod'), GOOS='android', GOARCH='arm64', CGO_ENABLED='1', CC=str(compiler),
    CGO_LDFLAGS='-Wl,-z,max-page-size=16384')
for key in ('FC_FAMILY_TEST_FIXTURES', 'YANDEX_TELEMOST_OAUTH_TOKEN', 'FC_TELEMOST_ROOM', 'GOFLAGS'):
    environment.pop(key, None)
module = out/'native.mod'
shutil.copyfile(native_source/'go.mod', module)
shutil.copyfile(native_source/'go.sum', out/'native.sum')
run('module', [go, 'mod', 'edit', '-modfile='+str(module),
    '-replace=github.com/Joker20380/family_connect/carrier='+str(source/'carrier'),
    '-replace=github.com/xtls/xray-core='+str(state/'field65-export16/native-packet-tests/xray')], native_source, environment)
binary = native/'jniLibs/arm64-v8a/libfc_restricted.so'
binary.parent.mkdir(parents=True)
run('native', [go, 'build', '-p=1', '-buildvcs=false', '-modfile='+str(module), '-trimpath',
    '-ldflags=-checklinkname=0', '-buildmode=c-shared', '-o', binary, './native'], native_source, environment)
receipt['native_sha256'] = digest(binary)
receipt['native_go_version_m'] = subprocess.check_output([go, 'version', '-m', binary], env=environment, text=True)
shutil.copytree(accepted/'native/assets', native/'assets')
manifest = json.loads((native/'assets/restricted-build.json').read_text())
assert manifest['binary_sha256'] == 'be70a66ccc2bcbf0478915fd414c32de3bedb2a0ae0c3222a53e65eebd0a92b2'
manifest.update(binary_sha256=receipt['native_sha256'], source_revision=base, source_tree=git('rev-parse',base+'^{tree}'),
    source_delta_sha256=delta, local_diagnostic_derivative=True, actual_build_receipt='build/receipt.json',
    actual_runner_sha256=digest(Path(__file__)), accepted_candidate=False)
(native/'assets/restricted-build.json').write_text(json.dumps(manifest, indent=2)+'\n')
assets = out/'research-assets'
assets.mkdir()
asset = json.loads((accepted/'research-assets/provisioning-seam-build.json').read_text())
asset.update(source_delta_sha256=delta, native_source_inventory=delta, public_release=False,
             ui_only_derivative=False, java_recovery_derivative=True, fast_retransmit_derivative=True)
(assets/'provisioning-seam-build.json').write_text(json.dumps(asset, indent=2)+'\n')
init = out/'android.init.gradle'
baseline = state/'ui60-layout-current-style-1'
init.write_text((baseline/'build/android.init.gradle').read_text().replace('/mnt/data/PycharmProjects/family_connect',str(state.parent)).replace(str(baseline/'build'),str(out)))
gradle_env = dict(os.environ, JAVA_HOME=str(tools/'jdk'), ANDROID_HOME=str(tools/'android'),
    ANDROID_SDK_ROOT=str(tools/'android'), GRADLE_USER_HOME=str(tools/'gradle-home'))
gradle_env['PATH'] = str(tools/'jdk/bin')+os.pathsep+gradle_env['PATH']
command = [tools/'gradle-8.11.1/bin/gradle', '--offline', '--no-daemon', '--max-workers=1', '-I', init,
    '--project-cache-dir', out/'cache', '-PfcTargetAbi=arm64-v8a', '-PfcFriendsCi=false',
    '-PfcProvisioningSeamSource='+delta, '-PfcProvisioningSeamAssets='+str(assets),
    '-PfcFriendsRestrictedDirectory='+str(native),
    '-PfcBuildPython='+str(state/'field65-export16/telemost-lease-continuity-1/build/tools/python/bin/python3.10'),
    '-PfcRadioNative='+str(state/'field65-export16/exit-krasnodar-candidate-1/audio-native'),
    ':app:assembleResearchProvisioning', ':app:testResearchProvisioningUnitTest']
for test in ['CutoverRecoveryTest', 'ConnectivityOrchestratorTest', 'RestrictedBootstrapTest',
             'RestrictedRecoveryTest', 'ReadinessProductTest', 'RestrictedCacheTest',
             'FriendsReadinessProtocolTest', 'RestrictedStartupTest', 'StartupFidelityTest',
             'DiagnosticRingTest', 'BootstrapCorrelationTest', 'Ui60PresentationTest']:
    command += ['--tests', 'com.familyconnect.app.'+test]
run('assemble-tests', command, source/'clients/android', gradle_env)
receipt['jvm_suites'] = []
for filename in (out/'android/app/test-results/testResearchProvisioningUnitTest').glob('TEST-*.xml'):
    suite = ET.parse(filename).getroot()
    receipt['jvm_suites'].append({key:suite.attrib.get(key) for key in ['name','tests','failures','errors','skipped']})
assert len(receipt['jvm_suites']) == 12
assert sum(int(suite['tests']) for suite in receipt['jvm_suites']) == 97
assert all(suite['failures'] == suite['errors'] == suite['skipped'] == '0' for suite in receipt['jvm_suites'])
headers, classes = out/'headers', out/'classes'
headers.mkdir(); classes.mkdir()
reference_classes = out/'android/app/intermediates/javac/researchProvisioning/compileResearchProvisioningJavaWithJavac/classes'
gson, = (tools/'gradle-home/caches/modules-2/files-2.1/com.google.code.gson/gson/2.13.2').glob('*/*.jar')
classpath = os.pathsep.join(map(str,(reference_classes, tools/'android/platforms/android-35/android.jar', gson)))
run('jni-java', [tools/'jdk/bin/javac','-source','17','-target','17','-implicit:none','-classpath',classpath,
    '-d',classes,'-h',headers,source/'clients/android/app/src/main/java/com/familyconnect/app/NativeRestricted.java'], source, gradle_env)
run('jni-c', [compiler,'-fsyntax-only','-include',headers/'com_familyconnect_app_NativeRestricted.h',native_source/'native/bridge.c'], source, environment)
apk = out/'android/app/outputs/apk/researchProvisioning/app-researchProvisioning-unsigned.apk'
with zipfile.ZipFile(apk) as bundle:
    assert hashlib.sha256(bundle.read('lib/arm64-v8a/libfc_restricted.so')).hexdigest() == receipt['native_sha256']
    assert json.loads(bundle.read('assets/restricted-build.json')) == manifest
    assert json.loads(bundle.read('assets/provisioning-seam-build.json'))['source_delta_sha256'] == delta
receipt.update(unsigned_apk_sha256=digest(apk), apk_size=apk.stat().st_size, result='PASS_BUILD_JVM_JNI')
save()
gateway_source = root/'gateway-source/carrier'
gateway_files = {str(filename.relative_to(gateway_source)):digest(filename)
                 for filename in gateway_source.rglob('*') if filename.is_file()}
parent_files = json.loads((state/'reliable-full-stack-1/gateway-input-files.json').read_text())
assert set(parent_files) == set(gateway_files)
assert [name for name in parent_files if parent_files[name] != gateway_files[name]] == ['reliablestream/engine.go']
gateway_inventory = hashlib.sha256(json.dumps(gateway_files,sort_keys=True,separators=(',',':')).encode()).hexdigest()
(out/'gateway-source.json').write_text(json.dumps(dict(parent_inventory='722746429539a1307d693ce6fcc83579a842d3f1c549a626a36676a6d665c42e',
    source_inventory=gateway_inventory,files=gateway_files),indent=2)+'\n')
gateway_env = {key:value for key,value in os.environ.items() if not key.startswith(('FC_','YANDEX_'))
    and key not in ('GOFLAGS','GOEXPERIMENT','CGO_CFLAGS','CGO_LDFLAGS')}
gateway_env.update(GOMAXPROCS='1',GOTOOLCHAIN='local',GOWORK='off',GOPROXY='off',GOSUMDB='off',
    GOPATH=str(tools/'gopath'),GOCACHE=str(state/'gateway-transport-progress-burst-candidate-1/build-cache'),
    GOOS='linux',GOARCH='amd64',GOAMD64='v1',CGO_ENABLED='1')
gateway_binary = out/'bootstrap-broker-speed1'
run('gateway-build',[go,'build','-p=1','-trimpath','-buildvcs=false','-o',gateway_binary,'./cmd/bootstrap-broker'],gateway_source,gateway_env)
gateway_info = subprocess.check_output([go,'version','-m',gateway_binary],env=gateway_env,text=True)
previous_gateway = state/'gateway-transport-progress-burst-candidate-1/build/bootstrap-broker-transport-progress'
assert digest(previous_gateway) == 'a537257162348afc35b1ebc08755d8c5dc1cd90e74c49e3987fb3eb81885e61f'
previous_info = subprocess.check_output([go,'version','-m',previous_gateway],env=gateway_env,text=True)
assert [line for line in gateway_info.splitlines() if line.startswith('\tdep\t')] == [line for line in previous_info.splitlines() if line.startswith('\tdep\t')]
assert 'CGO_ENABLED=1' in gateway_info and 'go1.26.1' in gateway_info and '-tags=' not in gateway_info
receipt.update(result='PASS_LOCAL_COMBINED_BUILD', gateway_source_inventory=gateway_inventory,
               gateway_sha256=digest(gateway_binary), gateway_buildinfo=gateway_info,
               gateway_dependencies_unchanged=True,gateway_executed=False,gateway_deployed=False)
save()
print(json.dumps({key: value for key, value in receipt.items() if key not in ('runs','jvm_suites','native_go_version_m')}))
