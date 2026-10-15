import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

parser = argparse.ArgumentParser()
for name in ('source', 'tools', 'xray', 'reference-classes', 'out'):
    parser.add_argument('--'+name, required=True, type=Path)
args = parser.parse_args()
args.out.mkdir(parents=True, exist_ok=False)
go = args.tools/'go/bin/go'
compiler = args.tools/'android/ndk/28.2.13676358/toolchains/llvm/prebuilt/linux-x86_64/bin/aarch64-linux-android26-clang'
env = dict(os.environ, GOTOOLCHAIN='local', GOPROXY='off', GOSUMDB='off', GOCACHE=str(args.out/'go-cache'), GOPATH=str(args.tools/'gopath'), GOOS='android', GOARCH='arm64', CGO_ENABLED='1', CC=str(compiler), CGO_LDFLAGS='-Wl,-z,max-page-size=16384')
for key in ('FC_FAMILY_TEST_FIXTURES', 'YANDEX_TELEMOST_OAUTH_TOKEN', 'FC_TELEMOST_ROOM', 'GOFLAGS'):
    env.pop(key, None)
native = args.source/'pilot/android-restricted'
module = args.out/'native.mod'
shutil.copy2(native/'go.mod', module)
shutil.copy2(native/'go.sum', args.out/'native.sum')
receipt = {'scope': 'COMPILE_LINK_ONLY_NO_APK_NO_DEVICE', 'runs': [], 'binaries': {}}
def run(command, name, cwd=native):
    with (args.out/(name+'.log')).open('wb') as output:
        try:
            status = subprocess.run(command, cwd=cwd, env=env, stdout=output, stderr=subprocess.STDOUT, timeout=600).returncode
        except subprocess.TimeoutExpired:
            status = 'TIMEOUT'
    receipt['runs'].append({'command': list(map(str, command)), 'log': name+'.log', 'exit': status, 'log_sha256': hashlib.sha256((args.out/(name+'.log')).read_bytes()).hexdigest()})
    (args.out/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(name, status, flush=True)
    if status != 0:
        raise SystemExit('Build failure preserved; no automatic retry')

run([go, 'mod', 'edit', '-modfile='+str(module), '-replace=github.com/Joker20380/family_connect/carrier='+str(args.source/'carrier'), '-replace=github.com/xtls/xray-core='+str(args.xray)], 'module')
for mode, tags in (('normal', ''), ('diagnostic', 'fc_owner_diagnostic'), ('messenger-lab', 'fc_messenger_lab')):
    target = args.out/mode/'libfc_restricted.so'
    target.parent.mkdir()
    command = [go, 'build', '-buildvcs=false', '-modfile='+str(module), '-trimpath', '-ldflags=-checklinkname=0', '-buildmode=c-shared', '-o', target]
    if tags:
        command.append('-tags='+tags)
    run(command+['./native'], mode)
    receipt['binaries'][mode] = {'sha256': hashlib.sha256(target.read_bytes()).hexdigest(), 'size': target.stat().st_size, 'tags': tags, 'go_version_m': subprocess.check_output([go, 'version', '-m', target], env=env, text=True)}

gson = list((args.tools/'gradle-home/caches/modules-2/files-2.1/com.google.code.gson/gson/2.13.2').glob('*/*.jar'))
assert len(gson) == 1
headers, classes = args.out/'headers', args.out/'classes'
headers.mkdir(); classes.mkdir()
java = args.source/'clients/android/app/src/main/java/com/familyconnect/app'
sources = [java/name for name in ('NativeRestricted.java', 'RestrictedTunnelEngine.java', 'ChatCarrier.java')]
sources.append(args.source/'clients/android/chat-runtime/app/src/lab/java/com/familyconnect/app/MessengerLabActivity.java')
classpath = os.pathsep.join(map(str, (args.reference_classes, args.tools/'android/platforms/android-35/android.jar', gson[0])))
run([args.tools/'jdk/bin/javac', '-source', '17', '-target', '17', '-implicit:none', '-classpath', classpath, '-d', classes, '-h', headers, *sources], 'java-contract')
for filename, header in (('bridge.c', 'NativeRestricted'), ('chat_lab_bridge.c', 'MessengerLabActivity')):
    run([compiler, '-fsyntax-only', '-include', headers/('com_familyconnect_app_'+header+'.h'), native/'native'/filename], 'jni-'+header)
receipt['result'] = 'PASS'
receipt['reference_classes'] = str(args.reference_classes)
(args.out/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
