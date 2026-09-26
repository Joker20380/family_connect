"""Private server snapshot stream. Run only through a consumer which encrypts stdout.

No network transport or persistence here. main emits a binary archive, never diagnostics
containing source values. See docs/server-secret-backup.ru.md before use.
"""
import argparse
import contextlib
import fcntl
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import resource
import sqlite3
import stat
import sys
import tarfile
import time

LIMIT = 16 * 1024 * 1024


def regular(root, path):
    relative = path.relative_to(root)
    for parent in [root, *[root.joinpath(*relative.parts[:i]) for i in range(1, len(relative.parts))]]:
        if parent.is_symlink() or not parent.is_dir():
            raise ValueError('unsafe source directory')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    info = os.fstat(fd)
    if not stat.S_ISREG(info.st_mode) or info.st_size > LIMIT:
        os.close(fd)
        raise ValueError('unsafe source file')
    return fd, info


def database(raw):
    with sqlite3.connect(':memory:') as connection:
        connection.deserialize(raw)
        if connection.execute('PRAGMA quick_check').fetchall() != [('ok',)]:
            raise ValueError('database integrity failed')
        # Do not return table names, row counts, SQL or record contents to public logs.


def infrastructure_sources(root, role):
    """Explicit recovery dependencies only; TLS links stored as private metadata."""
    selected = []
    links = []
    ssh = root / 'etc/ssh'
    for algorithm in ('rsa', 'ecdsa', 'ed25519'):
        for suffix in ('', '.pub'):
            path = ssh / ('ssh_host_' + algorithm + '_key' + suffix)
            if path.exists(): selected.append(path)
    if not any(p.name.endswith('_key') for p in selected):
        raise ValueError('missing host keys')
    selected.append(root / 'root/.ssh/authorized_keys')
    base = root / 'opt/apps/family_connect'
    if role == 'nl':
        node = base / 'mailbox-pilot'
        selected += [node / name for name in (
            'node.identity', 'settings.json', 'members.json', 'state/.volume-id',
            'state/rns/config', 'state/rns/storage/transport_identity',
            'state/spool/spool.sqlite')]
    else:
        tls = base / 'state-product-https/certificates'
        if tls.is_symlink() or not tls.is_dir():
            raise ValueError('missing TLS root')
        for path in sorted(tls.rglob('*')):
            if path.is_symlink():
                target = path.resolve(strict=True)
                if not target.is_relative_to(tls) or not target.is_file():
                    raise ValueError('unsafe TLS link')
                links.append(dict(path=str(path.relative_to(root)),
                                  target=str(target.relative_to(root))))
            elif path.is_file(): selected.append(path)
        names = {str(p.relative_to(root)) for p in selected}
        if not links or any(link['target'] not in names for link in links):
            raise ValueError('missing TLS link target')
    return selected, links


def snapshot(root, role, *, infrastructure=False):
    if role not in {'ru', 'nl'}:
        raise ValueError('unknown role')
    root = Path(root)
    started = int(time.time())
    files = {}
    manifest = []
    with contextlib.ExitStack() as stack:
        links = []
        if infrastructure:
            selected, links = infrastructure_sources(root, role)
        else:
            lock = root / 'friends-awg/registration.lock'
            fd, _ = regular(root, lock)
            stack.callback(os.close, fd)
            # Never block live provisioning indefinitely; retry explicitly if busy.
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            required = ['friends-awg/server.conf', 'friends-awg/settings.json',
                        'friends-awg/peers.db', 'friends-tcp/server.json']
            areas = ['friends-awg', 'friends-tcp']
            if role == 'ru':
                required += ['friends-access/access.db', 'friends-access/referral.key',
                             'friends-access/notices.sqlite', 'friends-access/catalog.json']
                areas += ['friends-access']
            excluded = {'awg', 'amneziawg-go', 'xray'}
            selected = []
            for area in areas:
                folder = root / area
                if folder.is_symlink() or not folder.is_dir():
                    raise ValueError('missing or unsafe required area')
                for path in sorted(folder.iterdir()):
                    if path.is_symlink():
                        raise ValueError('source symlink refused')
                    if path.is_dir() or path.name in excluded or path.name.endswith(('.lock', '-wal', '-shm')):
                        continue
                    if path.suffix == '.pending' or path.name == 'user-request.json':
                        raise ValueError('unfinished registration')
                    selected.append(path)
            if role == 'ru':
                product = root / 'state-product'
                if not product.is_dir() or product.is_symlink():
                    raise ValueError('missing Product state')
                for path in sorted(product.rglob('*')):
                    if path.is_symlink():
                        raise ValueError('source symlink refused')
                    if path.is_file() and not path.name.endswith(('.lock', '-wal', '-shm')):
                        selected.append(path)
            if not set(required) <= {str(p.relative_to(root)) for p in selected}:
                raise ValueError('missing required files')
        total = 0
        for path in selected:
            fd, before = regular(root, path)
            try:
                if path.suffix in {'.db', '.sqlite', '.sqlite3'}:
                    deadline = time.monotonic() + 15
                    def progress(*_):
                        if time.monotonic() > deadline:
                            raise TimeoutError('database backup deadline')
                    with sqlite3.connect(path.as_uri() + '?mode=ro', uri=True, timeout=5) as source:
                        with sqlite3.connect(':memory:') as destination:
                            source.backup(destination, pages=128, progress=progress, sleep=.05)
                            if destination.execute('PRAGMA quick_check').fetchall() != [('ok',)]:
                                raise ValueError('database integrity failed')
                            raw = destination.serialize()
                            # SQLite's documented deserialize workaround for a complete
                            # backup image originating in WAL mode; source is untouched.
                            # https://www.sqlite.org/c3ref/deserialize.html
                            if raw[:16] != b'SQLite format 3\x00' or raw[18:20] not in {b'\x01\x01', b'\x02\x02'}:
                                raise ValueError('invalid SQLite image')
                            raw = raw[:18] + b'\x01\x01' + raw[20:]
                    method = 'sqlite-online-backup'
                else:
                    with os.fdopen(os.dup(fd), 'rb') as stream:
                        raw = stream.read(LIMIT + 1)
                    after = os.fstat(fd)
                    if (before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns):
                        raise ValueError('source changed during read')
                    method = 'file-copy'
                if path.stat().st_ino != before.st_ino:
                    raise ValueError('source replaced during read')
                total += len(raw)
                if total > LIMIT or len(selected) > 1024:
                    raise ValueError('snapshot size limit')
                relative = str(path.relative_to(root))
                files[relative] = raw
                manifest.append(dict(path=relative, size=len(raw), sha256=hashlib.sha256(raw).hexdigest(),
                    mode=stat.S_IMODE(before.st_mode), uid=before.st_uid, gid=before.st_gid, method=method))
            finally:
                os.close(fd)
    inventory = dict(schema=1, role=role, started_at=started, finished_at=int(time.time()),
        scope='infrastructure' if infrastructure else 'application', symlinks=links,
        consistency=('individual SQLite online snapshots; no global transaction' if infrastructure else
                     'gateway registration lock; individual SQLite online snapshots; not a global transaction'),
        excluded=(['runtime originals', 'system configuration', 'RNS caches', 'volume image', 'legacy state-v2'] if infrastructure else
                  ['old backup directories', 'binaries', 'TLS', 'system SSH', 'messenger node', 'legacy state-v2']), files=manifest)
    files['PRIVATE-INVENTORY.json'] = json.dumps(inventory, sort_keys=True).encode()
    out = io.BytesIO()
    with tarfile.open(fileobj=out, mode='w:gz') as archive:
        for name, raw in files.items():
            item = tarfile.TarInfo(name); item.size = len(raw); item.mode = 0o600
            archive.addfile(item, io.BytesIO(raw))
    return out.getvalue()


def verify(raw):
    """Isolated in-memory restore: exact inventory, hashes and SQLite quick_check."""
    if len(raw) > LIMIT:
        raise ValueError('archive size limit')
    files = {}; total = 0
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r|gz') as archive:
        for item in archive:
            path = PurePosixPath(item.name)
            total += item.size
            if (not item.isfile() or path.is_absolute() or '..' in path.parts or
                    str(path) != item.name or item.name in files or total > LIMIT or len(files) >= 1024):
                raise ValueError('unsafe archive')
            files[item.name] = archive.extractfile(item).read()
    inventory = json.loads(files.pop('PRIVATE-INVENTORY.json'))
    expected = inventory['files']
    if len(expected) != len(files) or {r['path'] for r in expected} != set(files):
        raise ValueError('inventory mismatch')
    for link in inventory.get('symlinks', []):
        path = PurePosixPath(link['path'])
        if (path.is_absolute() or '..' in path.parts or str(path) != link['path'] or
                link['path'] in files or link['target'] not in files):
            raise ValueError('unsafe link inventory')
    databases = 0
    for record in expected:
        data = files[record['path']]
        if record['size'] != len(data) or hashlib.sha256(data).hexdigest() != record['sha256']:
            raise ValueError('snapshot digest mismatch')
        if record['method'] == 'sqlite-online-backup':
            database(data); databases += 1
    return {'files': len(files), 'databases_verified': databases, 'role': inventory['role']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--role', choices=['ru', 'nl'], required=True)
    parser.add_argument('--private-stream', action='store_true', required=True)
    parser.add_argument('--infrastructure', action='store_true')
    args = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    if sys.stdout.isatty():
        raise SystemExit('Refusing private stream to terminal')
    try:
        raw = snapshot(Path('/') if args.infrastructure else Path('/opt/apps/family_connect'),
                       args.role, infrastructure=args.infrastructure)
        verify(raw)
        sys.stdout.buffer.write(raw)
    except Exception:
        raise SystemExit('Private snapshot failed; diagnostics suppressed') from None


if __name__ == '__main__':
    main()
