"""Read-only pre-restart guard for the one authorized Friends HTTP service."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess

UNIT = 'family-connect-friends-http-candidate.service'


def matches(description, expected):
    if description.count('{') != 1 or description.count('}') != 1:
        return False
    match = re.fullmatch(r'\{\s*path=([^;]+?)\s*;\s*argv\[\]=(.*?)\s*;\s*ignore_errors=(?:yes|no)\s*;.*\}',
        description.strip(), re.DOTALL)
    if match is None:
        return False
    try:
        arguments = shlex.split(match.group(2))
    except ValueError:
        return False
    return bool(expected) and match.group(1) == expected[0] and arguments == expected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--python', required=True)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--port', type=int, default=18086)
    args = parser.parse_args()
    if (not args.archive.is_absolute() or args.archive.suffix != '.pyz'
            or not args.archive.is_file() or args.archive.stat().st_size > 16 * 1024 * 1024
            or any(path.is_symlink() for path in (args.archive, *args.archive.parents))
            or re.fullmatch('[0-9a-f]{64}', args.sha256) is None or not 1 <= args.port <= 65535):
        parser.error('Invalid expected archive/hash/port')
    digest = hashlib.sha256(args.archive.read_bytes()).hexdigest()
    expected = [args.python, '-I', str(args.archive), '--port', str(args.port)]
    description = subprocess.check_output(['systemctl', 'show', UNIT, '-p', 'ExecStart', '--value', '--no-pager'],
        text=True, timeout=15)
    valid = digest == args.sha256 and matches(description, expected)
    print(json.dumps(dict(schema=1, unit=UNIT, archive_sha256=digest,
        result='PASS' if valid else 'BLOCKED_EFFECTIVE_EXECSTART', restarts=0), allow_nan=False))
    return int(not valid)


if __name__ == '__main__':
    raise SystemExit(main())
