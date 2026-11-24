"""Bounded OWNER synthetic-store capture inside the existing console, no dispatch."""
import base64
from contextlib import ExitStack, closing
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import sqlite3
import stat
import time

from scripts.control_ha_installed_inventory import Reader
from scripts.control_ha_live_sqlite import identity, require

ROOT = Path('/app/control_plane/.local/synthetic')
ALIASES = Path('/run/fc-pseudonym-aliases.json')
SECONDS = 0.25
LIMIT = 1024 * 1024
SCHEMA = '69675bccf69f73e3c89010ea056b7d83017307940ec96ea603ef0b504af11952'
SCHEMA_QUERY = 'SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name'
PURPOSE = 'family-connect/owner-synthetic-capture/v1/no-dispatch'


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def capture(root=ROOT, aliases=ALIASES):
    require(hasattr(sqlite3.Connection, 'setconfig') and
            hasattr(sqlite3, 'SQLITE_DBCONFIG_NO_CKPT_ON_CLOSE'), 'SQLITE_UNSUPPORTED')
    reader = Reader()
    path = root / 'registry.sqlite3'
    expected = identity(path)
    for target, mode in ((root, 0o700), (path, 0o600)):
        info = target.stat()
        require(info.st_uid == os.getuid() and stat.S_IMODE(info.st_mode) == mode, 'PRIVATE_STORE_REQUIRED')
    require(512 <= path.stat().st_size <= LIMIT, 'STORE_BOUNDS')
    for suffix in ('-wal', '-shm', '-journal'):
        candidate = Path(str(path) + suffix)
        require(not candidate.exists() and not candidate.is_symlink(), 'STORE_SIDECAR_PRESENT')
    with path.open('rb') as stream:
        header = stream.read(100)
    require(header[:16] == b'SQLite format 3\x00' and header[18:20] == b'\x01\x01', 'ROLLBACK_JOURNAL_REQUIRED')
    require(signal.getsignal(signal.SIGALRM) == signal.SIG_DFL and
            signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0), 'ALARM_NOT_EXCLUSIVE')
    started = time.monotonic()
    signal.setitimer(signal.ITIMER_REAL, SECONDS)
    try:
        with ExitStack() as stack:
            descriptor = stack.enter_context(reader.opened(root / 'seed.lock'))
            info = os.fstat(descriptor)
            require(stat.S_ISREG(info.st_mode) and info.st_size == 0 and info.st_uid == os.getuid() and
                    not stat.S_IMODE(info.st_mode) & 0o022, 'SEED_LOCK_SHAPE')
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            connection = stack.enter_context(closing(sqlite3.connect(
                path.as_uri() + '?mode=rw', uri=True, timeout=0, isolation_level=None)))
            connection.setconfig(sqlite3.SQLITE_DBCONFIG_NO_CKPT_ON_CLOSE, True)
            connection.execute('PRAGMA trusted_schema=OFF')
            connection.execute('BEGIN IMMEDIATE')
            stack.callback(connection.rollback)
            locked_at = time.time_ns()
            require(identity(path) == expected, 'STORE_REPLACED')
            require(connection.execute('PRAGMA journal_mode').fetchone() == ('delete',), 'JOURNAL_CHANGED')
            require(digest(encoded(connection.execute(SCHEMA_QUERY).fetchall())) == SCHEMA, 'STORE_SCHEMA')
            require(connection.execute('PRAGMA page_count').fetchone()[0] *
                    connection.execute('PRAGMA page_size').fetchone()[0] <= LIMIT, 'STORE_BOUNDS')
            files = {'synthetic.sqlite': connection.serialize(), 'panel-aliases.json': reader.raw(aliases)}
            reader.verify()
            require(identity(path) == expected, 'STORE_REPLACED')
            captured_at = time.time_ns()
        elapsed = time.monotonic() - started
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
    require(elapsed < SECONDS, 'BARRIER_DEADLINE')
    return dict(purpose=PURPOSE, locked_at_ns=locked_at, captured_at_ns=captured_at,
                barrier_seconds=elapsed, files={name: base64.b64encode(raw).decode() for name, raw in files.items()},
                activation=False, pg_pair_fence=False)
