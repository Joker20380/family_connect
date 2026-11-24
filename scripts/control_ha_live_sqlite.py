"""One-second RU SQLite writer barrier; binary output must go to a private encryptor.

This captures only the four application stores, not external files, fleet state or
the OWNER panel. It is never full-recovery acceptance or a production cutover.
"""
import argparse
from contextlib import ExitStack, closing
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

ROOT = Path('/opt/apps/family_connect/friends-access')
STORES = {'registry': 'access.db', 'diagnostics': 'diagnostics.sqlite',
          'notices': 'notices.sqlite', 'metadata': 'technical-metadata.sqlite'}
LIMIT = 8 * 1024 * 1024
SECONDS = 1.0
PURPOSE = 'family-connect/four-live-sqlite-stores/v1/not-for-activation'


def require(condition, code):
    if not condition:
        raise ValueError(code)


def identity(path):
    require(path.is_absolute() and '..' not in path.parts, 'UNSAFE_PATH')
    require(all(not parent.is_symlink() for parent in (path, *path.parents)), 'UNSAFE_PATH')
    info = path.stat()
    require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size <= LIMIT,
            'UNSAFE_FILE')
    return info.st_dev, info.st_ino


def source_check(root):
    require(hasattr(sqlite3.Connection, 'setconfig') and
            hasattr(sqlite3, 'SQLITE_DBCONFIG_NO_CKPT_ON_CLOSE'), 'SQLITE_CONFIG_REQUIRED')
    selected = {}
    for store, name in sorted(STORES.items()):
        path = root / name
        selected[store] = (path, identity(path))
        require(path.stat().st_size >= 512, 'EMPTY_DATABASE')
        sidecars = {suffix: Path(str(path) + suffix) for suffix in ('-wal', '-shm', '-journal')}
        for candidate in sidecars.values():
            require(not candidate.is_symlink(), 'UNSAFE_SIDECAR')
            if candidate.exists():
                identity(candidate)
        with path.open('rb') as stream:
            header = stream.read(100)
        require(header[:16] == b'SQLite format 3\x00', 'INVALID_DATABASE')
        if header[18:20] == b'\x02\x02':
            require(all(sidecars[suffix].exists() for suffix in ('-wal', '-shm')),
                    'WAL_SIDECARS_REQUIRED')
        else:
            require(header[18:20] == b'\x01\x01', 'INVALID_JOURNAL_MODE')
        journal = sidecars['-journal']
        if journal.exists():
            with journal.open('rb') as stream:
                require(not any(stream.read(8)), 'POSSIBLY_HOT_JOURNAL')
    return selected


def capture(root=ROOT):
    selected = source_check(root)
    require(signal.getsignal(signal.SIGALRM) == signal.SIG_DFL and
            signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0), 'ALARM_NOT_EXCLUSIVE')
    acquired = {}
    images = {}
    started = time.monotonic()
    signal.setitimer(signal.ITIMER_REAL, SECONDS)
    try:
        with ExitStack() as stack:
            for store, (path, expected) in selected.items():
                connection = sqlite3.connect(path.as_uri() + '?mode=rw', uri=True,
                                             timeout=0, isolation_level=None)
                stack.enter_context(closing(connection))
                connection.setconfig(sqlite3.SQLITE_DBCONFIG_NO_CKPT_ON_CLOSE, True)
                connection.execute('BEGIN IMMEDIATE')
                stack.callback(connection.rollback)
                require(identity(path) == expected, 'DATABASE_REPLACED')
                acquired[store] = connection
            common_at = time.time_ns()
            for store, connection in acquired.items():
                require(connection.execute('PRAGMA page_count').fetchone()[0] *
                        connection.execute('PRAGMA page_size').fetchone()[0] <= LIMIT,
                        'DATABASE_TOO_LARGE')
                image = connection.serialize()
                require(len(image) <= LIMIT and image[:16] == b'SQLite format 3\x00' and
                        image[18:20] in (b'\x01\x01', b'\x02\x02'), 'INVALID_IMAGE')
                images[store] = image[:18] + b'\x01\x01' + image[20:]
            require(all(identity(path) == expected for path, expected in selected.values()),
                    'DATABASE_REPLACED')
            captured_at = time.time_ns()
        elapsed = time.monotonic() - started
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
    require(elapsed < SECONDS, 'BARRIER_DEADLINE')
    records = {}
    for store, raw in images.items():
        with closing(sqlite3.connect(':memory:')) as connection:
            connection.deserialize(raw)
            require(connection.execute('PRAGMA quick_check').fetchall() == [('ok',)],
                    'IMAGE_INTEGRITY')
            tables = connection.execute("SELECT count(*) FROM sqlite_master WHERE type='table' "
                                        "AND name NOT LIKE 'sqlite_%'").fetchone()[0]
        records[store] = dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(), tables=tables)
    return images, dict(purpose=PURPOSE, common_locked_at_ns=common_at,
                       captured_at_ns=captured_at, barrier_seconds=elapsed,
                       deadline_seconds=SECONDS, stores=records,
                       external_files_captured=False, fleet_barrier=False, full_recovery=False)


def archive(images, manifest):
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode='w') as bundle:
        entries = {store + '.sqlite': raw for store, raw in images.items()}
        entries['manifest.json'] = json.dumps(manifest, sort_keys=True).encode()
        for name, raw in sorted(entries.items()):
            entry = tarfile.TarInfo(name)
            entry.size, entry.mode = len(raw), 0o600
            bundle.addfile(entry, io.BytesIO(raw))
    return output.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture', action='store_true', required=True)
    parser.parse_args()
    require(not sys.stdout.isatty(), 'PRIVATE_CONSUMER_REQUIRED')
    os.umask(0o077)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    try:
        images, manifest = capture()
        sys.stdout.buffer.write(archive(images, manifest))
        sys.stdout.buffer.flush()
    except Exception:
        print('LIVE_SQLITE_CAPTURE_REFUSED', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
