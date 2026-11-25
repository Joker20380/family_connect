"""One-process startup authority for the HA-02 candidate, never a restart lease."""
import hashlib
import json
import os
from pathlib import Path
import runpy
import stat
import sys
import time


def binding():
    root = Path('/proc/self')
    return dict(pid=os.getpid(), start=(root / 'stat').read_text().rsplit(')', 1)[1].split()[19],
                boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                command=hashlib.sha256((root / 'cmdline').read_bytes()).hexdigest(),
                cgroup=hashlib.sha256((root / 'cgroup').read_bytes()).hexdigest())


def admitted(path, owner, archive):
    for parent in path.parents:
        info = parent.lstat()
        if not (stat.S_ISDIR(info.st_mode) and info.st_uid in (0, owner) and
                (not info.st_mode & 0o022 or info.st_uid == 0 and info.st_mode & stat.S_ISVTX)):
            raise ValueError('START_AUTHORITY_PARENT')
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    with os.fdopen(descriptor, 'rb') as source:
        info = os.fstat(source.fileno())
        if not (stat.S_ISREG(info.st_mode) and info.st_uid == owner and info.st_nlink == 1 and
                not info.st_mode & 0o022):
            raise ValueError('START_AUTHORITY_FILE')
        value = json.loads(source.read(8193))
    expected = dict(schema=1, binding=binding(), archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest())
    if value != expected:
        raise ValueError('START_AUTHORITY_CHANGED')


def main():
    archive, authority, owner, *options = sys.argv[1:]
    archive, authority, owner = Path(archive), Path(authority), int(owner)
    deadline = time.monotonic() + 5
    while True:
        try:
            admitted(authority, owner, archive)
            break
        except FileNotFoundError:
            if time.monotonic() >= deadline:
                raise ValueError('START_AUTHORITY_MISSING') from None
            time.sleep(.02)
    sys.argv = [str(archive), *options]
    runpy.run_path(str(archive), run_name='__main__')


if __name__ == '__main__':
    try:
        main()
    except Exception:
        raise SystemExit(78) from None
