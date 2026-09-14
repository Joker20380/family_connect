#!/usr/bin/python3 -I
"""Root-pinned IPv4/TCP relay route, owned by a bounded stdin liveness lease.

No caller-supplied address, port, uid, paths or command. Root configuration binds
one provider identity digest to one user/endpoint. Never flush unrelated rules.
"""
import fcntl
import ipaddress
import json
import os
from pathlib import Path
import re
import selectors
import signal
import stat
import subprocess
import sys
import time
import tempfile

CONFIG = Path('/etc/family-connect-control-route/pin.json')
RUN = Path('/run/family-connect-control-route')
ENV = {'PATH': '/usr/sbin:/usr/bin:/sbin:/bin', 'LANG': 'C'}


def safe_read(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o022 or info.st_nlink != 1:
            raise ValueError('unsafe broker file')
        raw = os.read(fd, 4097)
        if len(raw) > 4096:
            raise ValueError('oversized broker file')
        return json.loads(raw)
    finally:
        os.close(fd)


def validate(config, provider, uid):
    if type(config) is not dict or set(config) != {'schema', 'provider', 'uid', 'address', 'port', 'priority'}:
        raise ValueError('invalid route pin')
    if type(config['schema']) is not int or config['schema'] != 1:
        raise ValueError('invalid route pin')
    if not re.fullmatch('[0-9a-f]{64}', provider) or config['provider'] != provider:
        raise ValueError('untrusted provider')
    if type(config['uid']) is not int or config['uid'] < 1000 or config['uid'] != uid:
        raise ValueError('wrong route owner')
    address = ipaddress.IPv4Address(config['address'])
    if not address.is_global or str(address) != config['address']:
        raise ValueError('nonpublic relay')
    if type(config['port']) is not int or not 1 <= config['port'] <= 65535:
        raise ValueError('invalid relay port')
    if type(config['priority']) is not int or config['priority'] != 10590:
        raise ValueError('invalid route priority')
    return config


def command(*args):
    return subprocess.check_output(['/usr/sbin/ip', *args], env=ENV, text=True, timeout=5)


def rule(config, prohibit=False):
    uid = str(config['uid'])
    return ['priority', str(config['priority'] + int(prohibit)), 'to', config['address'] + '/32',
            'uidrange', uid + '-' + uid, 'ipproto', 'tcp', 'dport', str(config['port'])] + (
                ['prohibit'] if prohibit else ['lookup', 'main'])


def occupied(config):
    return [r for r in json.loads(command('-j', '-4', 'rule', 'show'))
            if r.get('priority') in (config['priority'], config['priority'] + 1)]


def matches(record, config, prohibit=False):
    expected = dict(priority=config['priority'] + int(prohibit), src='all', dst=config['address'],
        uid_start=config['uid'], uid_end=config['uid'], ipproto='tcp', dport=config['port'])
    expected.update({'action': 'prohibit'} if prohibit else {'table': 'main'})
    # Newer iproute2 emits an explicit exact-port mask.
    record = dict(record)
    if 'dport_mask' in record:
        if record.pop('dport_mask') != '0xffff':
            return False
    return record == expected


def persist(path, config):
    fd, name = tempfile.mkstemp(prefix='.intent-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(config, stream); stream.flush(); os.fsync(stream.fileno())
        os.replace(name, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        Path(name).unlink(missing_ok=True)


def release(config, marker):
    records = occupied(config)
    for prohibit in (False, True):
        found = [r for r in records if r['priority'] == config['priority'] + int(prohibit)]
        if len(found) > 1 or any(not matches(r, config, prohibit) for r in found):
            raise ValueError('route ownership conflict')
    # Remove lookup first: until cleanup completes, prohibit still prevents a loop.
    for prohibit in (False, True):
        if any(r['priority'] == config['priority'] + int(prohibit) for r in records):
            command('-4', 'rule', 'del', *rule(config, prohibit))
    if occupied(config):
        raise RuntimeError('route cleanup incomplete')
    marker.unlink(missing_ok=True)


def acquire(config, marker):
    if marker.exists():
        previous = safe_read(marker)
        if previous != config:
            raise ValueError('pending route belongs to another pin')
        release(config, marker)
    if occupied(config):
        raise ValueError('route priority occupied')
    persist(marker, config)
    try:
        # Install prohibit first, before lookup can fall through on link loss.
        for prohibit in (True, False):
            command('-4', 'rule', 'add', *rule(config, prohibit))
        records = occupied(config)
        if len(records) != 2 or not all(any(matches(r, config, p) for r in records) for p in (False, True)):
            raise ValueError('unexpected installed route')
    except Exception:
        release(config, marker)
        raise


def main():
    if os.geteuid() != 0 or len(sys.argv) != 2:
        raise ValueError('root broker invocation required')
    uid = int(os.environ.get('PKEXEC_UID', '-1'))
    config = validate(safe_read(CONFIG), sys.argv[1], uid)
    RUN.mkdir(mode=0o700, exist_ok=True)
    info = RUN.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != 0 or stat.S_IMODE(info.st_mode) != 0o700:
        raise ValueError('unsafe broker state')
    fd = os.open(RUN/'lock', os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o077 or info.st_nlink != 1:
            raise ValueError('unsafe broker lock')
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        marker = RUN/'intent.json'
        acquire(config, marker)
        try:
            stop = False
            def stopped(*_):
                nonlocal stop
                stop = True
            for number in (signal.SIGTERM, signal.SIGINT):
                signal.signal(number, stopped)
            print('READY', flush=True)
            with selectors.DefaultSelector() as selector:
                selector.register(sys.stdin, selectors.EVENT_READ)
                deadline = time.monotonic() + 300
                while not stop and time.monotonic() < deadline:
                    if selector.select(.2):
                        # No commands/renewals: any input or EOF ends the lease.
                        os.read(sys.stdin.fileno(), 1)
                        break
        finally:
            release(config, marker)
    finally:
        os.close(fd)


if __name__ == '__main__':
    try:
        main()
    except Exception:
        print('CONTROL_ROUTE_FAILED', file=sys.stderr)
        raise SystemExit(1)
