"""UI-only subscription actions; instrumentation inspects, never schedules delivery."""
import argparse
import json
from pathlib import Path
import re
import time
import xml.etree.ElementTree as ET

import subscription_android_run as driver

PACKAGE = 'com.familyconnect.app.subscriptionnatural.friends'
driver.PACKAGE = PACKAGE


def screen(work, label):
    path = '/sdcard/subscription-natural.xml'
    raw = ''
    for attempt in range(3):
        driver.adb('shell', 'rm', '-f', path)
        result = driver.adb('shell', 'uiautomator', 'dump', path)
        if result.returncode == 0:
            raw = driver.adb('shell', 'cat', path).stdout
            if raw.startswith('<?xml'):
                break
        time.sleep(1)
    assert raw.startswith('<?xml'), 'UI hierarchy unavailable'
    nodes = list(ET.fromstring(raw).iter('node'))
    (work / 'logs' / (label + '-screen.xml')).write_text(raw)
    return nodes


def tap(work, label, text):
    nodes = screen(work, label)
    node = next(node for node in nodes if node.get('text') == text)
    assert node.get('enabled') == 'true'
    bounds = [int(value) for value in re.findall(r'\d+', node.get('bounds'))]
    driver.adb('shell', 'input', 'tap', str((bounds[0] + bounds[2]) // 2), str((bounds[1] + bounds[3]) // 2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('install', 'enroll', 'recover', 'launch', 'open', 'refresh-home', 'tap', 'capture', 'inspect'))
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--label', required=True)
    parser.add_argument('--text')
    parser.add_argument('--values', default='{}')
    args = parser.parse_args()
    assert args.work.is_absolute() and args.work.name == 'subscription-android-2'
    assert re.fullmatch('[a-z0-9-]+', args.label)
    driver.check_device()
    if args.action == 'install':
        for filename in ('debug/app-debug.apk', 'androidTest/debug/app-debug-androidTest.apk'):
            result = driver.adb('install', '-r', '-t', str(args.work / 'android/app/outputs/apk' / filename))
            assert result.returncode == 0 and 'Success' in result.stdout
        assert driver.adb('shell', 'pm', 'grant', PACKAGE, 'android.permission.POST_NOTIFICATIONS').returncode == 0
    elif args.action in ('enroll', 'inspect', 'recover'):
        driver.test(args.work, args.label, {'enroll':'enroll','inspect':'inspectNatural','recover':'recoverThroughUi'}[args.action], json.loads(args.values))
    elif args.action in ('launch', 'open'):
        driver.adb('shell', 'am', 'start', '-n', PACKAGE + '/com.familyconnect.app.FriendsActivity', '--ei', 'tab', '3' if args.action == 'open' else '0')
        time.sleep(3)
        if args.action == 'open':
            tap(args.work, args.label, 'Subscription and access')
    elif args.action in ('tap', 'refresh-home'):
        tap(args.work, args.label, 'REFRESH' if args.action == 'refresh-home' else args.text)
        if args.action == 'refresh-home':
            driver.adb('shell', 'input', 'keyevent', 'KEYCODE_HOME')
    else:
        screen(args.work, args.label)
