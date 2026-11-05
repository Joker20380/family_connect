import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import socket
import ssl
import subprocess
import time
import urllib.request
import zipfile


SUCCESS_SCOPES = frozenset(('PASS_POSITIVE_PATH_ONLY', 'PASS_OWNER_RACE_ONLY', 'PASS_PARTIAL_CONNECT_ONLY'))


def require_success(record):
    assert record['result'] in SUCCESS_SCOPES, record.get('failure', record['result'])


def require_wall_clock(before, guest, after):
    assert 0 <= after-before <= 3 and before-2 <= guest <= after+2, 'Disposable clock skew; no clock adjustment or relaxed certificate validation allowed'


def observe_wall_clock(adb, record):
    deadline = time.monotonic()+60
    record['clock_samples'] = []
    while True:
        before = time.time()
        guest = int(subprocess.check_output(adb+['shell', 'date', '+%s'], text=True, timeout=10))
        after = time.time()
        observation = dict(host_before=before, host_after=after, guest=guest)
        record['clock_samples'].append(observation)
        record['clock_observation'] = observation
        record['guest_wall_seconds'] = guest
        try:
            require_wall_clock(before, guest, after)
            return
        except AssertionError:
            if time.monotonic() >= deadline:
                raise
        time.sleep(3)


@contextmanager
def emulator_slot(directory):
    with (directory/'android-emulator.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError('Another qualification emulator is already running') from error
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def require_nvidia_renderer(surface):
    renderer = next((line.strip() for line in surface.splitlines() if line.strip().startswith('GLES:')), '')
    software = ('swiftshader', 'llvmpipe', 'lavapipe', 'software rasterizer')
    if 'nvidia' not in renderer.lower() or any(name in renderer.lower() for name in software):
        raise RuntimeError('NVIDIA hardware renderer required; software fallback is forbidden')
    return renderer


def configure_network(adb, wifi, record):
    deadline = time.monotonic()+60
    record['network_setup'] = []
    while True:
        results = []
        for service, enabled in (('wifi', wifi), ('data', not wifi)):
            result = subprocess.run(adb+['shell', 'svc', service, 'enable' if enabled else 'disable'],
                                    capture_output=True, text=True, timeout=10)
            record['network_setup'].append(dict(service=service, enabled=enabled, code=result.returncode,
                output=(result.stdout+result.stderr)[-2048:]))
            results.append(result.returncode)
        if results == [0, 0]:
            return
        if time.monotonic() >= deadline:
            raise RuntimeError('Android network services unavailable; see network_setup receipt')
        time.sleep(2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tools', type=Path, required=True)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--port', type=int, default=5630)
    parser.add_argument('--service', action='store_true')
    parser.add_argument('--api', type=int, choices=(27, 35), required=True)
    parser.add_argument('--isolated-network', action='store_true')
    args = parser.parse_args()
    with emulator_slot(args.work.parent):
        run(args)


def run(args):
    args.work.mkdir(mode=0o700)
    avd = args.work/'avd'
    avd.mkdir(mode=0o700)
    sdk = args.tools/'android'
    bridge = json.loads((args.build/'bridge.json').read_bytes())
    if args.isolated_network:
        assert Path('/.dockerenv').exists()
        assert all(line.split()[1] != '00000000' for line in Path('/proc/net/route').read_text().splitlines()[1:])
        trust = ssl.create_default_context(cafile=args.build/'test-assets/core-ca.pem')
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPSHandler(context=trust))
        with opener.open('https://185.251.89.19:8443/', timeout=10) as response:
            assert response.read() == b'verified-isolated-origin'
    else:
        assert args.api == 27, 'API35 needs a no-egress namespace; Wi-Fi must not rely on emulator HTTP proxy'
    apk = args.build/'android/app/outputs/apk/friends/app-friends.apk'
    tests = args.build/'android/app/outputs/apk/androidTest/friends/app-friends-androidTest.apk'
    native = args.native/'jniLibs/x86_64/libfc_restricted.so'
    with zipfile.ZipFile(apk) as archive:
        assert archive.read('lib/x86_64/libfc_restricted.so') == native.read_bytes()
        metadata = json.loads(archive.read('assets/restricted-build.json'))
        assert metadata['provider'] == 'isolated-local-core' and metadata['diagnostic_only']
        assert archive.read('assets/control-anchor.pub') == (args.build/'app-assets/control-anchor.pub').read_bytes()
    environment = dict(os.environ, JAVA_HOME=str(args.tools/'jdk'), ANDROID_HOME=str(sdk),
        ANDROID_SDK_ROOT=str(sdk), ANDROID_AVD_HOME=str(avd),
        __NV_PRIME_RENDER_OFFLOAD='1', __GLX_VENDOR_LIBRARY_NAME='nvidia')
    receipt = dict(scope='working-Android-HTTP-cache-owner-positive-not-complete-G3',
        apk_sha256=hashlib.sha256(apk.read_bytes()).hexdigest(),
        tests_sha256=hashlib.sha256(tests.read_bytes()).hexdigest(),
        native_sha256=hashlib.sha256(native.read_bytes()).hexdigest(), native=metadata, bridge=bridge,
        no_egress_namespace=args.isolated_network,
        tls_ca_sha256=hashlib.sha256((args.build/'test-assets/core-ca.pem').read_bytes()).hexdigest())
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
        proxy = [] if args.isolated_network else ['-http-proxy', 'http://127.0.0.1:'+str(bridge['https_proxy'])]
        emulator = subprocess.Popen([str(sdk/'emulator/emulator'), '-avd', name, '-port', str(port),
            '-no-window', '-no-audio', '-no-snapshot', '-no-boot-anim', '-gpu', 'host', '-accel', 'on',
            '-memory', '2048', '-cores', '2', *proxy],
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
            surface = subprocess.check_output(adb+['shell', 'dumpsys', 'SurfaceFlinger'], text=True, timeout=15)
            (args.work/f'api{api}-renderer.txt').write_text(surface)
            record['renderer'] = require_nvidia_renderer(surface)
            record['gpu_mode'] = 'host'
            record['acceleration'] = 'on'
            wifi = args.isolated_network or api == 35
            configure_network(adb, wifi, record)
            time.sleep(5)
            record['network_scope'] = 'owned-emulator-'+('wifi' if wifi else 'cellular')+'-not-mobile-field'
            for artifact in (apk, tests):
                result = subprocess.run(adb+['install', '--no-streaming', '-t', str(artifact)], capture_output=True, text=True, timeout=90)
                assert result.returncode == 0 and 'Success' in result.stdout, 'Owned emulator install failed'
            subprocess.run(adb+['shell', 'sync'], check=True, capture_output=True, timeout=30)
            installed = subprocess.check_output(adb+['shell', 'pm', 'path', 'com.familyconnect.app.friends'], text=True).strip()
            assert installed.startswith('package:/data/app/') and installed.endswith('/base.apk') and '\n' not in installed
            installed_apk = subprocess.check_output(adb+['shell', 'su', '0', 'sha256sum', installed.removeprefix('package:')], text=True).split()[0]
            assert installed_apk == receipt['apk_sha256'], 'Installed APK differs from supplied artifact'
            record['installed_apk_sha256'] = installed_apk
            native_path = installed.removeprefix('package:').removesuffix('/base.apk')+'/lib/x86_64/libfc_restricted.so'
            installed_native = subprocess.check_output(adb+['shell', 'su', '0', 'sha256sum', native_path], text=True).split()[0]
            record['installed_native_sha256'] = installed_native
            assert installed_native == receipt['native_sha256'], 'Installed native bytes differ from verified APK'
            subprocess.run(adb+['reverse', 'tcp:19091', 'tcp:'+str(bridge['relay'])], check=True, capture_output=True, timeout=10)
            subprocess.run(adb+['shell', 'appops', 'set', 'com.familyconnect.app.friends', 'ACTIVATE_VPN', 'allow'], check=True, capture_output=True, timeout=10)
            record.update(result='RUNNING', started=time.time())
            observe_wall_clock(adb, record)
            (args.work/f'api{api}-receipt.json').write_text(json.dumps(record)+'\n')
            arguments = ['-e', 'fc_core_service', 'true'] if args.service else []
            with (args.work/f'api{api}-runtime.log').open('wb') as log:
                result = subprocess.run(adb+['shell', 'am', 'instrument', '-w', '-r', '-e', 'class',
                    'com.familyconnect.app.OnlineReadinessRuntimeTest', '-e', 'fc_core_runtime', 'true', *arguments,
                    'com.familyconnect.app.friends.test/androidx.test.runner.AndroidJUnitRunner'],
                    stdout=log, stderr=subprocess.STDOUT, timeout=12000)
            log = (args.work/f'api{api}-runtime.log').read_text()
            assert result.returncode == 0 and 'OK (1 test)' in log, 'HTTP/cache/owner runtime failed; retained log'
            scope = 'PASS_OWNER_RACE_ONLY' if 'OWNER_RACE_VALID_SUCCESSOR_NEW_EXPLICIT_OWNER' in log else 'PASS_POSITIVE_PATH_ONLY'
            if 'PARTIAL_EXPLICIT_CONNECT_AND_SAME_COMMIT_RESUME' in log:
                scope = 'PASS_PARTIAL_CONNECT_ONLY'
            record.update(result=scope, finished=time.time())
        except BaseException as error:
            record.update(result='FAIL', failure_type=type(error).__name__, failure=str(error))
            raise
        finally:
            if owned:
                if 'installed_native_sha256' in record:
                    checked = subprocess.run(adb+['shell', 'su', '0', 'sha256sum', native_path], capture_output=True, text=True, timeout=15)
                    record['final_native_sha256'] = checked.stdout.split()[0] if checked.returncode == 0 else 'unavailable'
                    if record['result'] in SUCCESS_SCOPES and record['final_native_sha256'] != receipt['native_sha256']:
                        record.update(result='FAIL', failure='Native artifact changed during runtime')
                events = subprocess.run(adb+['shell', 'su', '0', 'cat', '/data/data/com.familyconnect.app.friends/files/connectivity-events.json'], capture_output=True, timeout=15)
                (args.work/f'api{api}-connectivity.json').write_bytes(events.stdout)
                diagnostic = subprocess.run(adb+['shell', 'su', '0', 'cat', '/data/data/com.familyconnect.app.friends/no_backup/diag-ring.json'], capture_output=True, timeout=15)
                (args.work/f'api{api}-diagnostic.json').write_bytes(diagnostic.stdout)
                logs = subprocess.run(adb+['logcat', '-d', '-s', 'GoLog:I', 'AndroidRuntime:E'], capture_output=True, timeout=15)
                (args.work/f'api{api}-native.log').write_bytes(logs.stdout+logs.stderr)
                subprocess.run(adb+['emu', 'kill'], capture_output=True, timeout=15)
            if emulator.poll() is None:
                emulator.terminate()
            emulator.wait(timeout=30)
            output.close()
            record['owned_emulator_stopped'] = True
            (args.work/f'api{api}-receipt.json').write_text(json.dumps(record, indent=2)+'\n')
        require_success(record)
        return record

    variant = 'default' if args.api == 27 else 'google_apis'
    receipt['apis'] = [qualify(args.api, variant, args.port)]
    (args.work/'result.json').write_text(json.dumps(receipt, indent=2)+'\n')


if __name__ == '__main__':
    main()
