"""Forced-command read of the private, already acknowledged support projection."""
import json
import os
from pathlib import Path
import stat
import sys
import time


def read(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as stream:
        info = os.fstat(stream.fileno())
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077
                or info.st_nlink != 1 or not 0 < info.st_size <= 512 * 1024):
            raise ValueError('Unavailable')
        raw = stream.read(512 * 1024 + 1)
    document = json.loads(raw)
    if type(document.get('expires_at')) is not int or not time.time() < document['expires_at'] <= time.time() + 120:
        raise ValueError('Unavailable')
    return raw


if __name__ == '__main__':
    try:
        if len(sys.argv) != 1 or os.environ.get('SSH_ORIGINAL_COMMAND') != 'support-bindings':
            raise ValueError('Unavailable')
        sys.stdout.buffer.write(read(Path('/opt/apps/family_connect/friends-access/support-bindings.json')))
    except Exception:
        sys.exit(1)
