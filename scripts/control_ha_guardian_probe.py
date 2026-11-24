"""Trusted stdlib bootstrap for an explicitly approved local launch probe, not a capture."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import stat
import sys

LIMIT = 262144


def verified_source(spelling, expected):
    if not re.fullmatch('[0-9a-f]{64}', expected):
        raise ValueError('SOURCE_SHA')
    path = Path(spelling)
    if not path.is_absolute() or str(path) != spelling or '..' in path.parts or any(
            item.is_symlink() for item in (path, *path.parents)):
        raise ValueError('SOURCE_PATH')
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK)
    try:
        info = os.fstat(descriptor)
        if not (stat.S_ISREG(info.st_mode) and info.st_uid in (0, os.geteuid()) and info.st_nlink == 1 and
                not info.st_mode & 0o7022 and 0 < info.st_size <= LIMIT):
            raise ValueError('SOURCE_FILE')
        with os.fdopen(os.dup(descriptor), 'rb') as source:
            raw = source.read(LIMIT + 1)
        if len(raw) > LIMIT or hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError('SOURCE_SHA')
        return raw
    finally:
        os.close(descriptor)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True)
    parser.add_argument('--source-sha256', required=True)
    parser.add_argument('--binding', required=True)
    parser.add_argument('--binding-sha256', required=True)
    args = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    descriptor = None
    try:
        if not sys.flags.isolated or not sys.flags.no_site:
            raise ValueError('ISOLATED_PYTHON_REQUIRED')
        raw = verified_source(args.source, args.source_sha256)
        descriptor = os.memfd_create('fc-approved-guardian-source', os.MFD_CLOEXEC | os.MFD_ALLOW_SEALING)
        with os.fdopen(os.dup(descriptor), 'wb') as output:
            output.write(raw)
        os.fchmod(descriptor, 0o444)
        fcntl.fcntl(descriptor, fcntl.F_ADD_SEALS,
                    fcntl.F_SEAL_WRITE | fcntl.F_SEAL_GROW | fcntl.F_SEAL_SHRINK | fcntl.F_SEAL_SEAL)
        sys.path.insert(0, '/proc/self/fd/' + str(descriptor))
        from control import capture_group, capture_launch
        capture_launch.trusted_entrypoint(args.source_sha256)
        with capture_launch.launch(args.binding, args.binding_sha256, args.source) as participants:
            with capture_group.joint(participants) as window:
                pass
        print(json.dumps(dict(status='LOCAL_LAUNCH_PROBE_CONFIRMED', receipt=window.receipt,
                              capture_permitted=False, all_writers_qualified=False), sort_keys=True))
        return 0
    except (OSError, ValueError):
        print(json.dumps(dict(status='LOCAL_LAUNCH_PROBE_REFUSED', capture_permitted=False), sort_keys=True))
        return 1
    finally:
        if descriptor is not None:
            os.close(descriptor)


if __name__ == '__main__':
    raise SystemExit(main())
