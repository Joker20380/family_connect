"""Forced-command read of the private, already acknowledged support projection."""
import json
import os
from pathlib import Path
import stat
import sys
import time
import re
import importlib.util


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
        command = os.environ.get('SSH_ORIGINAL_COMMAND', '')
        if len(sys.argv) != 1:
            raise ValueError('Unavailable')
        root = Path('/opt/apps/family_connect/friends-access')
        if command == 'support-bindings':
            sys.stdout.buffer.write(read(root / 'support-bindings.json'))
        else:
            match = re.fullmatch(r'subscription-notifications (-1|0|[1-9][0-9]{0,18}) (none|[0-9a-f]{64})', command)
            if match is None:
                raise ValueError('Unavailable')
            source = root / 'subscription_events.py'
            info = source.lstat()
            if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o022:
                raise ValueError('Unavailable')
            spec = importlib.util.spec_from_file_location('subscription_events', source)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            key = root / 'support-inventory-hmac.key'
            info = key.lstat()
            if not stat.S_ISREG(info.st_mode) or info.st_mode & 0o077 or info.st_uid != os.getuid() or info.st_size != 32:
                raise ValueError('Unavailable')
            value = module.read(root / 'access.db', key.read_bytes(), int(match[1]), None if match[2] == 'none' else match[2])
            sys.stdout.write(json.dumps(value, separators=(',', ':')))
    except Exception:
        sys.exit(1)
