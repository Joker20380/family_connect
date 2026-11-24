"""Bounded installed-node custody, never transport activation or a fleet fence."""
import argparse
from contextlib import ExitStack, closing
import fcntl
import hashlib
import io
import json
import os
from pathlib import Path
import resource
import signal
import sqlite3
import stat
import sys
import tarfile
import time
import uuid

from scripts.control_ha_installed_inventory import Reader
from scripts.control_ha_live_sqlite import identity, require

ROOT = Path('/opt/apps/family_connect')
SECONDS = 0.25
LIMIT = 1024 * 1024
PURPOSE = 'family-connect/installed-node-custody/v1/not-for-activation'
NODES = {'RU': 'gateway-ru', 'NL1': 'nl-amsterdam-1', 'NL2': 'nl-amsterdam-2'}
FILES = {'settings.json': 'friends-awg/settings.json',
         'state.json': 'friends-awg/transport-state.json',
         'enforcement.json': 'friends-awg/transport-enforcement.json',
         'server.conf': 'friends-awg/server.conf', 'tcp.json': 'friends-tcp/server.json',
         'gateway.py': 'friends-awg/awg-gateway.py', 'transport.pyz': 'friends-awg/paid-transport.pyz'}
SOURCES = {
    'RU': ('9023d2c3f7c3a5127d67c509a16eb2d974810ff54d5b76cc225cd9b93e0b4234',
           '125c796a30c3fba1772c47b96963517350087ad04aad675b6f33a31a5383276c'),
    'NL1': ('69f32dbfdf0db5f57fb598d58935b5f2b098e53d0c0e2ac24517ad299ced26bf',
            'f7571bd42bbd583017fc590b20c7c7097059d7f202fef8323558c4fa8f47885d'),
    'NL2': ('69f32dbfdf0db5f57fb598d58935b5f2b098e53d0c0e2ac24517ad299ced26bf',
            'f7571bd42bbd583017fc590b20c7c7097059d7f202fef8323558c4fa8f47885d'),
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def source_check(root, slot):
    require(slot in NODES and hasattr(sqlite3.Connection, 'setconfig') and
            hasattr(sqlite3, 'SQLITE_DBCONFIG_NO_CKPT_ON_CLOSE'), 'NODE_OR_SQLITE_UNSUPPORTED')
    reader = Reader()
    for name, expected in zip(('gateway.py', 'transport.pyz'), SOURCES[slot]):
        require(digest(reader.raw(root / FILES[name])) == expected, 'INSTALLED_SOURCE_CHANGED')
    path = root / 'friends-awg/peers.db'
    expected = identity(path)
    require(512 <= path.stat().st_size <= LIMIT, 'ALLOCATOR_BOUNDS')
    for suffix in ('-wal', '-shm', '-journal'):
        candidate = Path(str(path) + suffix)
        require(not candidate.exists() and not candidate.is_symlink(), 'ALLOCATOR_SIDECAR_PRESENT')
    with path.open('rb') as stream:
        header = stream.read(100)
    require(header[:16] == b'SQLite format 3\x00' and header[18:20] == b'\x01\x01',
            'ROLLBACK_JOURNAL_REQUIRED')
    return reader, path, expected


def capture(slot, root=ROOT):
    reader, path, expected = source_check(root, slot)
    require(signal.getsignal(signal.SIGALRM) == signal.SIG_DFL and
            signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0), 'ALARM_NOT_EXCLUSIVE')
    started = time.monotonic()
    signal.setitimer(signal.ITIMER_REAL, SECONDS)
    try:
        with ExitStack() as stack:
            for name in ('application.lock', 'registration.lock'):
                descriptor = stack.enter_context(reader.opened(root / 'friends-awg' / name))
                info = os.fstat(descriptor)
                require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size == 0, 'LOCK_FILE_SHAPE')
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            connection = stack.enter_context(closing(sqlite3.connect(
                path.as_uri() + '?mode=rw', uri=True, timeout=0, isolation_level=None)))
            connection.setconfig(sqlite3.SQLITE_DBCONFIG_NO_CKPT_ON_CLOSE, True)
            connection.execute('PRAGMA trusted_schema=OFF')
            connection.execute('BEGIN IMMEDIATE')
            stack.callback(connection.rollback)
            require(identity(path) == expected, 'ALLOCATOR_REPLACED')
            require(connection.execute('PRAGMA journal_mode').fetchone() == ('delete',), 'JOURNAL_CHANGED')
            locked_at = time.time_ns()
            monotonic = time.monotonic()
            boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
            require(str(uuid.UUID(boot)) == boot, 'BOOT_ID')
            files = {name: reader.raw(root / relative) for name, relative in FILES.items()}
            require(connection.execute('PRAGMA page_count').fetchone()[0] *
                    connection.execute('PRAGMA page_size').fetchone()[0] <= LIMIT, 'ALLOCATOR_BOUNDS')
            files['peers.sqlite'] = connection.serialize()
            require(len(files['peers.sqlite']) <= LIMIT, 'ALLOCATOR_BOUNDS')
            require(identity(path) == expected, 'ALLOCATOR_REPLACED')
            reader.verify()
            captured_at = time.time_ns()
        elapsed = time.monotonic() - started
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
    require(elapsed < SECONDS, 'BARRIER_DEADLINE')
    manifest = dict(purpose=PURPOSE, slot=slot, node=NODES[slot], boot=boot, monotonic=monotonic,
                    locked_at_ns=locked_at, captured_at_ns=captured_at, barrier_seconds=elapsed,
                    deadline_seconds=SECONDS, fleet_fence=False, activation=False,
                    files={name: dict(bytes=len(raw), sha256=digest(raw)) for name, raw in files.items()})
    return files, manifest


def archive(files, manifest):
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode='w') as bundle:
        for name, raw in sorted(dict(files, **{'manifest.json': json.dumps(manifest, sort_keys=True).encode()}).items()):
            entry = tarfile.TarInfo(name)
            entry.size, entry.mode = len(raw), 0o600
            bundle.addfile(entry, io.BytesIO(raw))
    return output.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture', action='store_true', required=True)
    parser.add_argument('--slot', choices=NODES, required=True)
    args = parser.parse_args()
    os.umask(0o077)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    try:
        require(not sys.stdout.isatty(), 'PRIVATE_CONSUMER_REQUIRED')
        sys.stdout.buffer.write(archive(*capture(args.slot)))
        sys.stdout.buffer.flush()
    except Exception:
        print('NODE_CAPTURE_REFUSED', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
