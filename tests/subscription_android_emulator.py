"""One disposable API35 AVD, guarded by the existing shared qualification lock."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time

from android_core_emulators import emulator_slot, require_nvidia_renderer


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tools', type=Path, required=True)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--lock-directory', type=Path, required=True)
    parser.add_argument('--reuse-avd', type=Path)
    args = parser.parse_args()
    assert args.work.is_absolute() and args.work.name in ('subscription-android-1', 'subscription-android-2')
    sdk = args.tools / 'android'
    avd = args.reuse_avd or args.work / 'avd'
    avd.mkdir(mode=0o700, exist_ok=True)
    environment = dict(os.environ, JAVA_HOME=str(args.tools / 'jdk'), ANDROID_HOME=str(sdk),
        ANDROID_SDK_ROOT=str(sdk), ANDROID_AVD_HOME=str(avd), ANDROID_USER_HOME=str(args.work / 'android-user'),
        ANDROID_EMULATOR_HOME=str(args.work / 'emulator-user'),
        __NV_PRIME_RENDER_OFFLOAD='1', __GLX_VENDOR_LIBRARY_NAME='nvidia')
    with emulator_slot(args.lock_directory):
        assert 'emulator-' not in subprocess.check_output(['/usr/bin/adb', 'devices'], text=True)
        if args.reuse_avd:
            assert (avd / 'fc-subscription35.ini').is_file()
        else:
            created = subprocess.run([str(sdk / 'cmdline-tools/latest/bin/avdmanager'), 'create', 'avd',
                '-n', 'fc-subscription35', '-k', 'system-images;android-35;google_apis;x86_64', '-d', 'pixel_2'],
                input='no\n', text=True, capture_output=True, env=environment, timeout=90)
            (args.work / 'logs/avd-create.log').write_text(created.stdout + created.stderr)
            assert created.returncode == 0, 'AVD creation failed'
        with (args.work / 'logs/emulator.log').open('wb') as output:
            emulator = subprocess.Popen([str(sdk / 'emulator/emulator'), '-avd', 'fc-subscription35', '-port', '5672',
                '-no-window', '-no-audio', '-no-snapshot', '-no-boot-anim', '-gpu', 'host', '-accel', 'on',
                '-memory', '2048', '-cores', '2'], env=environment, stdout=output, stderr=subprocess.STDOUT)
            try:
                adb = ['/usr/bin/adb', '-s', 'emulator-5672']
                deadline = time.monotonic() + 150
                while time.monotonic() < deadline:
                    assert emulator.poll() is None, 'Emulator exited'
                    boot = subprocess.run(adb + ['shell', 'getprop', 'sys.boot_completed'], capture_output=True, text=True, timeout=5)
                    if boot.returncode == 0 and boot.stdout.strip() == '1':
                        break
                    time.sleep(2)
                else:
                    raise RuntimeError('Boot deadline exceeded')
                surface = subprocess.check_output(adb + ['shell', 'dumpsys', 'SurfaceFlinger'], text=True, timeout=10)
                renderer = require_nvidia_renderer(surface)
                api = subprocess.check_output(adb + ['shell', 'getprop', 'ro.build.version.sdk'], text=True).strip()
                assert api == '35'
                guest = int(subprocess.check_output(adb + ['shell', 'date', '+%s'], text=True).strip())
                assert abs(int(time.time()) - guest) < 5, 'Unacceptable guest clock skew'
                receipt = dict(serial='emulator-5672', api=api, renderer=renderer, gpu='host', acceleration='KVM', pid=emulator.pid)
                (args.work / 'emulator.json').write_text(json.dumps(receipt, indent=2) + '\n')
                print(json.dumps(receipt), flush=True)
                while not (args.work / 'stop-emulator').exists():
                    assert emulator.poll() is None, 'Emulator exited'
                    time.sleep(2)
            finally:
                if emulator.poll() is None:
                    emulator.terminate()
                    emulator.wait(timeout=30)


if __name__ == '__main__':
    main()
