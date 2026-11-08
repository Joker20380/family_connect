"""Fail before entry start; resolve the launcher and fence a later Connect."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import time

try:
    from . import prepare_cold_field_apk as finalizer
except ImportError:
    import prepare_cold_field_apk as finalizer


def launcher(badging, expected_package=finalizer.PACKAGE):
    packages = re.findall(r"^package: name='([^']+)'", badging, re.M)
    activities = re.findall(r"^launchable-activity: name='([^']+)'", badging, re.M)
    if packages != [expected_package] or len(activities) != 1:
        raise ValueError('package or unique launcher missing')
    activity = activities[0]
    if activity.startswith('.'):
        activity = expected_package + activity
    elif '.' not in activity:
        activity = expected_package + '.' + activity
    if not re.fullmatch(r'[A-Za-z_][\w$]*(?:\.[A-Za-z_][\w$]*)+', activity):
        raise ValueError('invalid launcher')
    return expected_package + '/' + activity


def installed_launcher(resolution, expected):
    components = [line.strip() for line in resolution.splitlines() if '/' in line]
    if components != [expected]:
        raise ValueError('installed launcher does not match inspected APK')
    return expected


def preflight(args):
    accepted, receipt, payload = finalizer.accepted_prebuild(args)
    verifier_pin = accepted.get('verifier_sha256',
        'c7ed0b15b38fc3f215ef23f8a8687076ed5e73ade1c099d6ffc2d69ca3a8a96c')
    if finalizer.digest(args.verifier.read_bytes()) != verifier_pin:
        raise ValueError('unqualified locator verifier')
    for name, options in (('aapt', ['version']), ('zipalign', ['-h']), ('apksigner', ['version'])):
        result = subprocess.run([str(getattr(args, name)), *options], capture_output=True, timeout=10)
        if result.returncode not in ((0, 2) if name == 'zipalign' else (0,)):
            raise ValueError('required release tool unavailable: '+name)
    badging = subprocess.check_output([str(args.aapt), 'dump', 'badging', str(args.unsigned)],
                                     text=True, timeout=10)
    component = launcher(badging)
    if ("versionCode='"+str(accepted['version_code'])+"'" not in badging or
            "versionName='"+accepted['version']+"'" not in badging or
            "sdkVersion:'27'" not in badging or "native-code: 'arm64-v8a'" not in badging or
            'application-debuggable' in badging):
        raise ValueError('incompatible manifest')
    return dict(state='PREFLIGHT_PASS_NO_ENTRY_STARTED', package=finalizer.PACKAGE,
                version_code=accepted['version_code'], launcher=component,
                apk_sha256=receipt['apk_sha256'], verification_sha256=accepted['verification_sha256'],
                entry_started=False, locator_present=False)


def check_entry(status, ready, locator, expected_invocation, *, now, handoff_seconds=0):
    if (not re.fullmatch('[0-9a-f]{32}', expected_invocation) or
            status.get('invocation_id') != expected_invocation or
            ready.get('invocation_id') != expected_invocation or
            status.get('active_state') != 'active' or status.get('sub_state') != 'running' or
            type(status.get('main_pid')) is not int or status['main_pid'] <= 0 or
            status.get('stopped') is not False or
            not 0 <= now-status.get('observed_at', 0) <= 5):
        raise ValueError('entry not proven live in the original invocation')
    finalizer.check_window(locator, ready, now=now, handoff_seconds=handoff_seconds)
    return dict(state='ENTRY_LIVE_CONNECT_WINDOW', invocation_id=expected_invocation,
                connect_not_after=locator['expires_at']-200, observed_at=now)


def run_field(args, start, operation, stop):
    receipt = preflight(args)
    entry = None
    try:
        entry = start(receipt)
        return operation(receipt, entry)
    finally:
        stop(entry)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prepare = commands.add_parser('preflight')
    for name in ('unsigned', 'verification', 'verifier', 'anchor', 'aapt', 'zipalign', 'apksigner'):
        prepare.add_argument('--'+name, type=Path, required=True)
    prepare.add_argument('--qualification', type=Path)
    prepare.add_argument('--qualification-sha256')
    connect = commands.add_parser('check-entry')
    for name in ('status', 'ready', 'locator'):
        connect.add_argument('--'+name, type=Path, required=True)
    connect.add_argument('--invocation', required=True)
    resolve = commands.add_parser('check-launcher')
    resolve.add_argument('--resolution', type=Path, required=True)
    resolve.add_argument('--expected', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'preflight':
            result = preflight(args)
        elif args.command == 'check-launcher':
            result = dict(launcher=installed_launcher(args.resolution.read_text(), args.expected))
        else:
            result = check_entry(json.loads(args.status.read_bytes()), json.loads(args.ready.read_bytes()),
                                 json.loads(args.locator.read_bytes()), args.invocation, now=int(time.time()))
        print(json.dumps(result, indent=2))
    except Exception:
        parser.exit(1, 'FIELD_PREFLIGHT_REJECTED_NO_CONNECT\n')


if __name__ == '__main__':
    main()
