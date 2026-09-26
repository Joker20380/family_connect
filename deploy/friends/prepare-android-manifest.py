"""Build the Android friends discovery manifest from an accepted signed APK.

Read-only helper: computes size and SHA256 from the APK and prints the JSON that
`deploy/friends/install-android-update.py` accepts. It never signs or publishes.
Run this only after `pilot/android-awg/verify-apk.py --abis arm64-v8a` has passed
and the artifact has been accepted on a real device.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

BASE = 'https://185.251.89.19:8443'
PACKAGE = 'com.familyconnect.app.friends'
ABI = 'arm64-v8a'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('apk', type=Path)
    parser.add_argument('--version', required=True, help='e.g. 0.1.18-beta51')
    parser.add_argument('--version-code', type=int, required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()

    version = args.version
    if not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+-beta[0-9]+', version):
        raise SystemExit('invalid version; expected e.g. 0.1.18-beta51')
    if args.version_code <= 0:
        raise SystemExit('version_code must be positive')
    filename = f'FamilyConnect-Test-{version}.apk'
    if args.apk.name != filename:
        raise SystemExit(f'APK must be named {filename}')

    raw = args.apk.read_bytes()
    if not 1 <= len(raw) <= 512 * 1024 * 1024:
        raise SystemExit('invalid APK size')

    data = {
        'schema': 1,
        'package': PACKAGE,
        'abi': ABI,
        'version_code': args.version_code,
        'version': version,
        'url': f'{BASE}/downloads/{filename}',
        'size': len(raw),
        'sha256': hashlib.sha256(raw).hexdigest(),
    }
    text = json.dumps(data, indent=2) + '\n'
    if args.output:
        args.output.write_text(text)
        print(f'wrote {args.output}', file=sys.stderr)
    else:
        sys.stdout.write(text)


if __name__ == '__main__':
    main()
