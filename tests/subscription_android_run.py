"""Bounded instrumentation driver for the disposable subscription package only."""
import argparse
import json
from pathlib import Path
import re
import shlex
import subprocess
import time
import xml.etree.ElementTree as ET

PACKAGE = 'com.familyconnect.app.subscriptiontest'
ADB = ['/usr/bin/adb', '-s', 'emulator-5672']


def adb(*arguments, timeout=60):
    command = ['shell', shlex.join(arguments[1:])] if arguments and arguments[0] == 'shell' else list(arguments)
    return subprocess.run(ADB + command, capture_output=True, text=True, timeout=timeout)


def check_device():
    assert adb('shell', 'getprop', 'ro.build.version.sdk').stdout.strip() == '35'
    fingerprint = adb('shell', 'getprop', 'ro.build.fingerprint').stdout
    assert 'generic' in fingerprint or 'sdk' in fingerprint


def capture(work, label):
    for name in ('subscription-runtime.json', 'subscription-screen.txt', 'subscription-network.json'):
        result = adb('exec-out', 'run-as', PACKAGE, 'cat', 'files/' + name)
        if result.returncode == 0:
            (work / 'logs' / (label + '-' + name)).write_text(result.stdout)


def test(work, label, method, values):
    assert re.fullmatch('[A-Za-z][A-Za-z0-9]+', method)
    output = work / 'logs' / (label + '-instrumentation.txt')
    assert not output.exists(), 'Preserve previous evidence; choose another label'
    command = ['shell', 'am', 'instrument', '-w', '-r', '-e', 'fc_disposable', 'true', '-e', 'class',
               'com.familyconnect.app.SubscriptionRuntimeTest#' + method]
    if method == 'enroll':
        values['invitation'] = (work / 'private/invitation').read_text()
    for name, value in values.items():
        command += ['-e', name, value]
    command += [PACKAGE + '.test/androidx.test.runner.AndroidJUnitRunner']
    result = adb(*command, timeout=120)
    output.write_text(result.stdout + result.stderr)
    passed = result.returncode == 0 and 'OK (1 test)' in result.stdout and 'FAILURES' not in result.stdout
    with (work / 'runtime-results.jsonl').open('a') as log:
        log.write(json.dumps(dict(label=label, method=method, result='PASS' if passed else 'FAIL', at=int(time.time()))) + '\n')
    capture(work, label)
    print(label, 'PASS' if passed else 'FAIL', flush=True)
    if not passed:
        raise RuntimeError('See retained instrumentation evidence: ' + str(output))


def navigate(work, label, cold):
    adb('shell', 'input', 'keyevent', 'KEYCODE_HOME')
    if cold:
        adb('shell', 'am', 'kill', PACKAGE)
        time.sleep(2)
        assert not adb('shell', 'pidof', PACKAGE).stdout.strip(), 'Cold navigation requires an absent process'
    else:
        assert adb('shell', 'pidof', PACKAGE).stdout.strip(), 'Warm navigation requires an existing process'
    adb('shell', 'cmd', 'statusbar', 'expand-notifications')
    time.sleep(1)
    adb('shell', 'uiautomator', 'dump', '/sdcard/subscription-notifications.xml')
    raw = adb('shell', 'cat', '/sdcard/subscription-notifications.xml').stdout
    (work / 'logs' / (label + '-notification.xml')).write_text(raw)
    nodes = ET.fromstring(raw).iter('node')
    target = next(node for node in nodes if node.get('text') == 'Family Connect')
    bounds = [int(number) for number in re.findall(r'\d+', target.get('bounds'))]
    adb('shell', 'input', 'tap', str((bounds[0] + bounds[2]) // 2), str((bounds[1] + bounds[3]) // 2))
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        adb('shell', 'uiautomator', 'dump', '/sdcard/subscription-navigation.xml')
        screen = adb('shell', 'cat', '/sdcard/subscription-navigation.xml').stdout
        visible='\n'.join(node.get('text','') for node in ET.fromstring(screen).iter('node'))
        if 'Subscription and access' in visible and 'Status confirmed by the service at the time shown.' in visible:
            (work / 'logs' / (label + '-screen.xml')).write_text(screen)
            print(label, 'PASS', flush=True)
            return
        time.sleep(1)
    raise RuntimeError('Notification did not open subscription screen')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('install', 'test', 'cold', 'warm'))
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--label', default='install')
    parser.add_argument('--method')
    parser.add_argument('--values', default='{}')
    args = parser.parse_args()
    assert args.work.is_absolute() and args.work.name == 'subscription-android-1'
    assert re.fullmatch('[a-z0-9-]+', args.label)
    check_device()
    if args.operation == 'install':
        for filename in ('debug/app-debug.apk', 'androidTest/debug/app-debug-androidTest.apk'):
            result = adb('install', '-r', '-t', str(args.work / 'android/app/outputs/apk' / filename))
            assert result.returncode == 0 and 'Success' in result.stdout
        print('Installed test APK and instrumentation on emulator-5672/API35')
    elif args.operation == 'test':
        test(args.work, args.label, args.method, json.loads(args.values))
    else:
        navigate(args.work, args.label, args.operation == 'cold')
