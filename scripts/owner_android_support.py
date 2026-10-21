"""Bounded ADB support for an explicitly enabled owner app. No touch injection/root."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import time

URI = 'content://com.familyconnect.app.friends.owner.support'


def adb(serial, *arguments):
    result = subprocess.run(['adb', '-s', serial, *arguments], capture_output=True, timeout=12)
    if result.returncode or b'SecurityException' in result.stdout or b'Exception' in result.stderr:
        raise RuntimeError('ADB support unavailable: unlock app and enable USB support once; no permission bypass')
    if len(result.stdout) > 256*1024:
        raise RuntimeError('Snapshot bound exceeded')
    return result.stdout


def command(serial, method, argument=None):
    args = ['shell', 'content', 'call', '--uri', URI, '--method', method]
    if argument is not None:
        args += ['--arg', argument]
    raw = adb(serial, *args).decode()
    match = re.search(r'\bresult=([A-Za-z0-9_]+)', raw)
    if not match:
        raise RuntimeError('Unknown command receipt; inspect status, do not blindly repeat')
    return match[1]


def snapshot(serial):
    raw = adb(serial, 'exec-out', 'content', 'read', '--uri', URI+'/snapshot')
    value = json.loads(raw)
    if not isinstance(value, dict) or value.get('schema') != 1 or 'restricted_session' not in value:
        raise RuntimeError('Not a complete app diagnostic snapshot')
    return value


def save(path, value):
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(descriptor, 'w') as output:
        json.dump(value, output, indent=2)
        output.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serial', required=True)
    parser.add_argument('action', choices=['status','snapshot','collect','connect','disconnect','profile','disable'])
    parser.add_argument('--profile', choices=['P0','P1','P2'])
    parser.add_argument('--output', type=Path)
    parser.add_argument('--seconds', type=int, default=300)
    parser.add_argument('--interval', type=int, default=10)
    args = parser.parse_args()
    if not re.fullmatch('[A-Za-z0-9._:-]{1,80}', args.serial):
        parser.error('Invalid serial')
    if args.action == 'profile' and not args.profile:
        parser.error('--profile required; gateway profile is separate, never inferred')
    if args.action in ('snapshot','collect') and args.output is None:
        parser.error('--output required (private local evidence)')
    if args.action == 'snapshot':
        save(args.output, snapshot(args.serial))
        print('SNAPSHOT_SAVED', args.output)
    elif args.action == 'collect':
        if not 1 <= args.seconds <= 1800 or not 5 <= args.interval <= 60:
            parser.error('Collection bound: duration<=1800s, interval5..60s')
        args.output.mkdir(mode=0o700, parents=True, exist_ok=False)
        deadline = time.monotonic()+args.seconds
        index = 0
        while time.monotonic() < deadline:
            record = dict(observed_utc=datetime.now(timezone.utc).isoformat())
            try:
                record['snapshot'] = snapshot(args.serial)
            except Exception as error:
                record['status'] = 'COLLECTION_FAILED'
                record['reason'] = type(error).__name__
                save(args.output/f'{index:04}.json', record)
                raise SystemExit('Collection stopped; first failure saved, no reconnect/retry')
            save(args.output/f'{index:04}.json', record)
            index += 1
            time.sleep(max(0,min(args.interval,deadline-time.monotonic())))
        print('COLLECTION_COMPLETE', index)
    else:
        print(command(args.serial, args.action, args.profile if args.action=='profile' else None))


if __name__ == '__main__':
    main()
