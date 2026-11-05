import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import time
import zipfile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tools', type=Path, required=True)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--work', type=Path, required=True)
    args = parser.parse_args()
    args.work.mkdir(mode=0o700)
    avd = args.work/'avd'
    avd.mkdir(mode=0o700)
    sdk = args.tools/'android'
    bridge = json.loads((args.build/'bridge.json').read_bytes())
    apk = args.build/'android/app/outputs/apk/friends/app-friends.apk'
    tests = args.build/'android/app/outputs/apk/androidTest/friends/app-friends-androidTest.apk'
    native = args.native/'jniLibs/x86_64/libfc_restricted.so'
    with zipfile.ZipFile(apk) as archive:
        assert archive.read('lib/x86_64/libfc_restricted.so') == native.read_bytes()
        metadata = json.loads(archive.read('assets/restricted-build.json'))
        assert metadata['provider'] == 'isolated-local-core' and metadata['diagnostic_only']
        assert archive.read('assets/control-anchor.pub') == (args.build/'app-assets/control-anchor.pub').read_bytes()
    environment = dict(os.environ, JAVA_HOME=str(args.tools/'jdk'), ANDROID_HOME=str(sdk),
        ANDROID_SDK_ROOT=str(sdk), ANDROID_AVD_HOME=str(avd))
    receipt = dict(scope='working-Android-HTTP-cache-owner-positive-not-complete-G3',
        apk_sha256=hashlib.sha256(apk.read_bytes()).hexdigest(),
        tests_sha256=hashlib.sha256(tests.read_bytes()).hexdigest(),
        native_sha256=hashlib.sha256(native.read_bytes()).hexdigest(), native=metadata, bridge=bridge)
    (args.work/'inputs.json').write_text(json.dumps(receipt, indent=2)+'\n')

    def qualify(api, variant, port):
        for number in (port, port+1):
            with socket.socket() as probe:
                probe.bind(('127.0.0.1', number))
        name='fc-core-'+args.work.name+'-'+str(api)
        result = subprocess.run([str(sdk/'cmdline-tools/latest/bin/avdmanager'), 'create', 'avd', '-n', name,
            '-k', f'system-images;android-{api};{variant};x86_64', '-d', 'pixel_2'], input='no\n',
            text=True, capture_output=True, env=environment, timeout=90)
        (args.work/f'api{api}-create.log').write_text(result.stdout+result.stderr)
        assert result.returncode == 0, 'AVD create failed'
        output=(args.work/f'api{api}-emulator.log').open('wb')
        emulator = subprocess.Popen([str(sdk/'emulator/emulator'), '-avd', name, '-port', str(port),
            '-no-window', '-no-audio', '-no-snapshot', '-no-boot-anim', '-gpu', 'swiftshader_indirect',
            '-memory', '2048', '-cores', '2', '-http-proxy', 'http://127.0.0.1:'+str(bridge['https_proxy'])],
            env=environment, stdout=output, stderr=subprocess.STDOUT)
        adb = [str(sdk/'platform-tools/adb'), '-s', f'emulator-{port}']
        record = dict(api=api, serial=f'emulator-{port}', emulator_pid=emulator.pid, result='STARTING')
        owned = False
        try:
            deadline=time.monotonic()+240
            while True:
                assert emulator.poll() is None, 'Owned emulator exited'
                result = subprocess.run(adb+['shell', 'getprop', 'sys.boot_completed'], capture_output=True, text=True, timeout=10)
                if result.returncode == 0 and result.stdout.strip() == '1':
                    break
                assert time.monotonic() < deadline, 'Boot timeout'
                time.sleep(2)
            fingerprint=subprocess.check_output(adb+['shell', 'getprop', 'ro.build.fingerprint'], text=True)
            assert 'generic' in fingerprint or 'sdk' in fingerprint
            assert subprocess.check_output(adb+['shell', 'getprop', 'ro.build.version.sdk'], text=True).strip() == str(api)
            owned = True
            for artifact in (apk, tests):
                result = subprocess.run(adb+['install', '-t', str(artifact)], capture_output=True, text=True, timeout=90)
                assert result.returncode == 0 and 'Success' in result.stdout, 'Owned emulator install failed'
            subprocess.run(adb+['reverse', 'tcp:19091', 'tcp:'+str(bridge['relay'])], check=True, capture_output=True, timeout=10)
            subprocess.run(adb+['shell', 'appops', 'set', 'com.familyconnect.app.friends', 'ACTIVATE_VPN', 'allow'], check=True, capture_output=True, timeout=10)
            record.update(result='RUNNING', started=time.time())
            (args.work/f'api{api}-receipt.json').write_text(json.dumps(record)+'\n')
            with (args.work/f'api{api}-runtime.log').open('wb') as log:
                result = subprocess.run(adb+['shell', 'am', 'instrument', '-w', '-r', '-e', 'class',
                    'com.familyconnect.app.OnlineReadinessRuntimeTest', '-e', 'fc_core_runtime', 'true',
                    'com.familyconnect.app.friends.test/androidx.test.runner.AndroidJUnitRunner'],
                    stdout=log, stderr=subprocess.STDOUT, timeout=12000)
            log = (args.work/f'api{api}-runtime.log').read_text()
            assert result.returncode == 0 and 'OK (1 test)' in log, 'HTTP/cache/owner runtime failed; retained log'
            record.update(result='PASS_POSITIVE_PATH_ONLY', finished=time.time())
        except BaseException as error:
            record.update(result='FAIL', failure_type=type(error).__name__, failure=str(error))
            raise
        finally:
            if owned:
                logs = subprocess.run(adb+['logcat', '-d', '-s', 'GoLog:I', 'AndroidRuntime:E'], capture_output=True, timeout=15)
                (args.work/f'api{api}-native.log').write_bytes(logs.stdout+logs.stderr)
                subprocess.run(adb+['emu', 'kill'], capture_output=True, timeout=15)
            if emulator.poll() is None:
                emulator.terminate()
            emulator.wait(timeout=30)
            output.close()
            record['owned_emulator_stopped'] = True
            (args.work/f'api{api}-receipt.json').write_text(json.dumps(record, indent=2)+'\n')
        return record

    with ThreadPoolExecutor(max_workers=2) as executor:
        jobs = [executor.submit(qualify, 27, 'default', 5630), executor.submit(qualify, 35, 'google_apis', 5632)]
        receipt['apis'] = [job.result() for job in jobs]
    (args.work/'result.json').write_text(json.dumps(receipt, indent=2)+'\n')


if __name__ == '__main__':
    main()
