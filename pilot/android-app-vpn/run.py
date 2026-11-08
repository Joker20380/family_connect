"""Run real distinct-UID routing only on one explicitly selected emulator."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serial', required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--gradle', default='gradle')
    parser.add_argument('--visual-only', action='store_true')
    args = parser.parse_args()
    if not args.serial.startswith('emulator-') or not args.serial[9:].isdigit():
        raise SystemExit('An emulator serial is required')
    os.umask(0o077)
    output = args.out.resolve()
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    adb = ['adb', '-s', args.serial]

    def run(command, **kwargs):
        return subprocess.check_output(command, text=True, timeout=kwargs.pop('timeout', 30), **kwargs)

    if run(adb+['shell', 'getprop', 'ro.kernel.qemu']).strip() != '1':
        raise SystemExit('Disposable emulator required')
    native = ROOT/'clients/android/awg-generated'
    log = (output/'fixture.log').open('w')
    fixture = subprocess.Popen([sys.executable, str(ROOT/'pilot/android-app-vpn/fixture.py'),
                                '--out', str(output/'fixture'), '--awg-peer', str(native/'app-vpn-peer'),
                                '--xray', str(native/'xray-peer')], stdout=log, stderr=subprocess.STDOUT)
    try:
        deadline = time.monotonic()+30
        while not (output/'fixture/ready.json').exists():
            if fixture.poll() is not None or time.monotonic()>deadline:
                raise RuntimeError('Isolated fixture not ready')
            time.sleep(.2)
        subprocess.run([args.gradle, '--no-daemon', '--max-workers=2', '-p', str(ROOT/'pilot/android-app-vpn/probes'),
                        '-PfcProbeAssets='+str(output/'fixture/probe-assets'), 'assembleDebug'], check=True, timeout=300)
        app = ROOT/'clients/android/app/build/outputs/apk'
        probes = ROOT/'pilot/android-app-vpn/probes/app/build/outputs/apk'
        apks = [app/'debug/app-debug.apk', app/'androidTest/debug/app-debug-androidTest.apk',
                probes/'alpha/debug/app-alpha-debug.apk', probes/'beta/debug/app-beta-debug.apk']
        for apk in apks:
            if 'Success' not in run(adb+['install', '-r', str(apk)], timeout=90):
                raise RuntimeError('Fixture installation failed')
        run(adb+['push', str(apks[2]), '/data/local/tmp/fc-app-probe-alpha.apk'])
        selection = 'com.familyconnect.app.AppVpnRuntimeTest'+('#screenSavesRealRoutingAndPendingSelection' if args.visual_only else '')
        completed = subprocess.run(adb+['shell', 'am', 'instrument', '-w', '-r', '-e', 'class', selection,
                         '-e', 'fc_app_vpn', 'true', 'com.familyconnect.app.pilot.test/androidx.test.runner.AndroidJUnitRunner'],
                         capture_output=True, text=True, timeout=600)
        result = completed.stdout
        (output/'instrumentation.log').write_text(result+completed.stderr)
        if completed.returncode:
            raise RuntimeError('Instrumentation command failed; see instrumentation.log')
        if ('OK (1 test)' if args.visual_only else 'OK (7 tests)') not in result or any(value in result for value in ('FAILURES!!!', 'INSTRUMENTATION_FAILED', 'INSTRUMENTATION_STATUS_CODE: -3', 'INSTRUMENTATION_STATUS_CODE: -4')):
            raise RuntimeError('Per-app routing acceptance failed; see instrumentation.log')
        for name in (('screen',) if args.visual_only else ('routing', 'automatic', 'screen', 'owner-health', 'package-removal', 'service')):
            raw = run(adb+['shell', 'run-as', 'com.familyconnect.app.pilot', 'cat', 'files/app-vpn-'+name+'.json'])
            (output/(name+'.json')).write_text(json.dumps(json.loads(raw), indent=2))
        visuals = output/'visuals'
        visuals.mkdir()
        remote_visuals = '/sdcard/Android/data/com.familyconnect.app.pilot/files/app-vpn-visual/'
        subprocess.run(adb+['pull', remote_visuals, str(visuals/'en')], check=True, timeout=30)
        scale = run(adb+['shell', 'settings', 'get', 'system', 'font_scale']).strip()
        try:
            run(adb+['shell', 'settings', 'put', 'system', 'font_scale', '1.5'])
            result = run(adb+['shell', 'am', 'instrument', '-w', '-r', '-e', 'class',
                             'com.familyconnect.app.AppVpnRuntimeTest#screenSavesRealRoutingAndPendingSelection',
                             '-e', 'fc_app_vpn', 'true', '-e', 'app_vpn_language', 'ru',
                             'com.familyconnect.app.pilot.test/androidx.test.runner.AndroidJUnitRunner'], timeout=90)
            (output/'visual-ru-large.log').write_text(result)
            subprocess.run(adb+['pull', remote_visuals, str(visuals/'ru-large')], check=True, timeout=30)
            if 'OK (1 test)' not in result:
                raise RuntimeError('Large-font visual/runtime fixture failed; see visual-ru-large.log')
        finally:
            run(adb+['shell', 'settings', 'put', 'system', 'font_scale', scale if scale != 'null' else '1.0'])
        print(json.dumps(dict(api=run(adb+['shell','getprop','ro.build.version.sdk']).strip(), result='PASS',
                              scope='screen/TCP only' if args.visual_only else 'real AWG/TCP/Auto; MESH owned TUN with REALITY substitute carrier')))
    finally:
        if fixture.poll() is None:
            fixture.terminate()
            try:
                fixture.wait(timeout=10)
            except subprocess.TimeoutExpired:
                fixture.kill(); fixture.wait(timeout=5)
        log.close()


if __name__ == '__main__':
    main()
