"""Isolated emulator acceptance; never targets a real Family Connect package."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
PACKAGE = 'com.familyconnect.chatchecks'
SERIAL = None


def adb(*args):
    selector = ['-s', SERIAL] if SERIAL else []
    result = subprocess.run(['adb', *selector, *args], capture_output=True, text=True, timeout=120)
    if result.returncode:
        raise RuntimeError('Chat acceptance adb operation failed')
    return result.stdout


def instrument(method, count):
    result = adb('shell', 'am', 'instrument', '-w', '-r', '-e', 'class', method,
                 PACKAGE + '.test/androidx.test.runner.AndroidJUnitRunner')
    if f'OK ({count} test' not in result or 'FAILURES' in result or 'INSTRUMENTATION_FAILED' in result:
        # Test output can include fixture text: keep it out of CI/command logs.
        raise RuntimeError('Chat runtime acceptance failed: ' + method)
    print('PASS', method, flush=True)


if __name__ == '__main__':
    devices = [line.split()[0] for line in adb('devices').splitlines()
               if line.startswith('emulator-') and line.split()[-1] == 'device']
    if len(devices) != 1:
        raise RuntimeError('Exactly one running Android emulator is required')
    SERIAL = devices[0]
    adb('install', '-r', str(ROOT/'app/build/outputs/apk/debug/app-debug.apk'))
    adb('install', '-r', str(ROOT/'app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk'))
    instrument('com.familyconnect.app.ChatLocalRuntimeTest', 4)
    instrument('com.familyconnect.app.ChatProcessRuntimeTest#prepare', 1)
    adb('shell', 'am', 'force-stop', PACKAGE)
    instrument('com.familyconnect.app.ChatProcessRuntimeTest#resume', 1)
