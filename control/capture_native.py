"""Scoped native-file seal after writer-domain shutdown; never a writer census permit."""
import ctypes
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import select
import stat
import struct
import subprocess
import time


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def fingerprint(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def unique_mount(path):
    library = ctypes.CDLL(None, use_errno=True)
    buffer = ctypes.create_string_buffer(256)
    result = library.statx(-100, os.fsencode(path), 0x800, 0x4000, buffer)
    require(result == 0 and struct.unpack_from('I', buffer.raw)[0] & 0x4000,
            'NATIVE_UNIQUE_MOUNT_UNSUPPORTED')
    return struct.unpack_from('Q', buffer.raw, 144)[0]


def identity(path):
    info = path.stat()
    return [info.st_dev, info.st_ino, info.st_uid, stat.S_IMODE(info.st_mode)]


def readonly(path):
    return bool(os.statvfs(path).f_flag & os.ST_RDONLY)


def record(root, name, value):
    descriptor = os.open(root / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'wb') as stream:
        stream.write(encoded(value))
        stream.flush()
        os.fsync(stream.fileno())
    descriptor = os.open(root, os.O_DIRECTORY | os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def read(root, name):
    target = root / name
    info = target.lstat()
    require(stat.S_ISREG(info.st_mode) and info.st_uid == os.geteuid() and
            stat.S_IMODE(info.st_mode) == 0o600 and info.st_nlink == 1 and info.st_size <= 65536,
            'NATIVE_JOURNAL_FILE')
    return json.loads(target.read_bytes())


def command(arguments):
    subprocess.run(arguments, check=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL, timeout=5)


class ReadOnlyTrees:
    def __init__(self, roots, journal, operation):
        require(os.geteuid() == 0 and re.fullmatch('[a-zA-Z0-9_-]{1,96}', operation), 'NATIVE_PRIVILEGE_OPERATION')
        self.roots = tuple(sorted(Path(value) for value in roots))
        require(1 <= len(self.roots) <= 8 and len(set(self.roots)) == len(self.roots), 'NATIVE_ROOT_COVERAGE')
        self.journal = Path(journal)
        for path in (*self.roots, self.journal):
            require(path.is_absolute() and len(path.parts) >= 4 and
                    not any(item.is_symlink() for item in (path, *path.parents)), 'NATIVE_PRIVATE_PATH')
        require(all(not (first == second or first in second.parents or second in first.parents)
                    for index, first in enumerate((*self.roots, self.journal))
                    for second in (*self.roots, self.journal)[index + 1:]), 'NATIVE_ROOT_OVERLAP')
        require(all(path.is_dir() and not readonly(path) for path in self.roots), 'NATIVE_PRESTATE')
        mountpoints = [Path(line.split()[4]) for line in Path('/proc/self/mountinfo').read_text().splitlines()]
        require(not any(root in mount.parents for root in self.roots for mount in mountpoints),
                'NATIVE_NESTED_MOUNT')
        self.journal.mkdir(mode=0o700, exist_ok=False)
        self.boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
        self.before = {str(path): dict(identity=identity(path), mount=unique_mount(path)) for path in self.roots}
        record(self.journal, 'plan.json', dict(operation=operation, boot=self.boot, roots=self.before,
            mount_namespace=os.readlink('/proc/self/ns/mnt'), purpose='family-connect/native-ro-trees/v1'))
        self.plan_hash = fingerprint(read(self.journal, 'plan.json'))
        self.controller = os.open(self.journal / 'controller.lock', os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o600)
        fcntl.flock(self.controller, fcntl.LOCK_EX | fcntl.LOCK_NB)
        self.attempted = self.active = False
        self.mounts = {}
        self.continuity_fd = None

    def acquire(self):
        require(not self.attempted, 'NATIVE_NO_REACQUIRE')
        self.attempted = True
        try:
            for index, path in enumerate(self.roots):
                require(identity(path) == self.before[str(path)]['identity'] and
                        unique_mount(path) == self.before[str(path)]['mount'] and not readonly(path),
                        'NATIVE_PRESTATE_CHANGED')
                record(self.journal, f'bind-{index}-intent.json', dict(path=str(path)))
                command(['/usr/bin/mount', '--bind', str(path), str(path)])
                mount = unique_mount(path)
                require(mount != self.before[str(path)]['mount'], 'NATIVE_BIND_ID')
                self.mounts[str(path)] = mount
                record(self.journal, f'bind-{index}-observed.json', dict(path=str(path), mount=mount))
                command(['/usr/bin/mount', '-o', 'remount,bind,ro', str(path)])
                require(readonly(path), 'NATIVE_READONLY_REQUIRED')
            self.continuity_fd = os.open('/proc/self/mounts', os.O_RDONLY | os.O_CLOEXEC)
            self.continuity = select.poll()
            self.continuity.register(self.continuity_fd, select.POLLPRI | select.POLLERR)
            self.active = True
            self.lease = fingerprint(dict(boot=self.boot, mounts=self.mounts, roots=self.before))
            self.check()
            record(self.journal, 'held.json', dict(lease=self.lease, mounts=self.mounts))
            return self
        except BaseException as error:
            self.active = False
            self.failure(error)
            raise

    def failure(self, error):
        if not (self.journal / 'failed.json').exists():
            reason = str(error)
            try:
                record(self.journal, 'failed.json', dict(reason=reason if re.fullmatch('[A-Z][A-Z0-9_]{0,95}', reason)
                    else type(error).__name__, cleanup='REQUIRES_EXPLICIT_RECONCILIATION', capture_permitted=False))
            except Exception as cleanup:
                error.add_note('NATIVE_FAILURE_RECORD_' + type(cleanup).__name__)

    def check(self):
        try:
            require(self.active, 'NATIVE_NOT_HELD')
            require(fingerprint(read(self.journal, 'plan.json')) == self.plan_hash, 'NATIVE_PLAN_CHANGED')
            require(self.boot == Path('/proc/sys/kernel/random/boot_id').read_text().strip(), 'NATIVE_BOOT_CHANGED')
            for path in self.roots:
                require(identity(path) == self.before[str(path)]['identity'] and readonly(path) and
                        unique_mount(path) == self.mounts[str(path)], 'NATIVE_MOUNT_LOST')
            require(not self.continuity.poll(0), 'NATIVE_MOUNT_NAMESPACE_CHANGED')
            require(not (self.journal / 'failed.json').exists(), 'NATIVE_FAILED')
            return self.lease
        except BaseException as error:
            self.active = False
            self.failure(error)
            raise

    def release(self):
        self.active = False
        if self.continuity_fd is not None:
            os.close(self.continuity_fd)
            self.continuity_fd = None
        if self.controller is not None:
            os.close(self.controller)
            self.controller = None
        return reconcile(self.journal, self.plan_hash)

    def __enter__(self):
        return self.acquire()

    def __exit__(self, error_type, error, traceback):
        try:
            self.release()
        except Exception as cleanup:
            if error is None:
                raise
            error.add_note('NATIVE_CLEANUP_' + type(cleanup).__name__)


def reconcile(journal, plan_hash):
    root = Path(journal)
    require(root.is_absolute() and not any(item.is_symlink() for item in (root, *root.parents)) and
            identity(root)[2:] == [os.geteuid(), 0o700], 'NATIVE_RECONCILE_ROOT')
    descriptor = os.open(root / 'controller.lock', os.O_RDWR | os.O_NOFOLLOW)
    try:
        info = os.fstat(descriptor)
        require(stat.S_ISREG(info.st_mode) and info.st_uid == os.geteuid() and
                stat.S_IMODE(info.st_mode) == 0o600 and info.st_size == 0 and info.st_nlink == 1,
                'NATIVE_CONTROLLER_LOCK')
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return reconcile_locked(root, plan_hash)
    finally:
        os.close(descriptor)


def reconcile_locked(root, plan_hash):
    plan = read(root, 'plan.json')
    require(fingerprint(plan) == plan_hash, 'NATIVE_PLAN_CHANGED')
    require(plan['boot'] == Path('/proc/sys/kernel/random/boot_id').read_text().strip() and
            plan['mount_namespace'] == os.readlink('/proc/self/ns/mnt'), 'NATIVE_RECONCILE_KERNEL')
    if (root / 'released.json').exists():
        return read(root, 'released.json')
    for index, (name, before) in reversed(tuple(enumerate(plan['roots'].items()))):
        path = Path(name)
        require(identity(path) == before['identity'], 'NATIVE_RECONCILE_PATH_CHANGED')
        observed = root / f'bind-{index}-observed.json'
        if not observed.exists():
            require(not (root / f'bind-{index}-intent.json').exists(), 'NATIVE_ACQUIRE_OUTCOME_UNKNOWN')
            continue
        owned = read(root, observed.name)
        require(owned['path'] == name, 'NATIVE_RECONCILE_BINDING')
        current = unique_mount(path)
        intent = root / f'release-{index}-intent.json'
        if current == before['mount']:
            require(intent.exists(), 'NATIVE_EXTERNAL_UNMOUNT')
        else:
            require(current == owned['mount'], 'NATIVE_RECONCILE_FOREIGN_MOUNT')
            if not intent.exists():
                record(root, intent.name, owned)
            command(['/usr/bin/umount', str(path)])
        require(unique_mount(path) == before['mount'] and not readonly(path), 'NATIVE_RELEASE_UNCONFIRMED')
    receipt = dict(result='OWN_NATIVE_MOUNTS_RELEASED', operation=plan['operation'],
                   writer_resume='NOT_PERFORMED', capture_permitted=False)
    record(root, 'released.json', receipt)
    return receipt


def reject_old_handles(roots, *, proc=Path('/proc'), seconds=5):
    roots = tuple(Path(path) for path in roots)
    require(all(readonly(path) for path in roots), 'NATIVE_AUDIT_BEFORE_SEAL')
    deadline = time.monotonic() + seconds
    identities = set()
    for root in roots:
        for directory, names, files in os.walk(root, followlinks=False):
            require(time.monotonic() < deadline, 'NATIVE_HANDLE_AUDIT_TIMEOUT')
            for path in (Path(directory), *(Path(directory) / name for name in names + files)):
                info = path.lstat()
                require(stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode), 'NATIVE_AUDIT_FILE_TYPE')
                identities.add((info.st_dev, info.st_ino))
                require(len(identities) <= 32768, 'NATIVE_AUDIT_TREE_BOUNDS')
    for process in proc.iterdir():
        require(time.monotonic() < deadline, 'NATIVE_HANDLE_AUDIT_TIMEOUT')
        if not process.name.isdecimal() or int(process.name) == os.getpid():
            continue
        try:
            mappings = (process / 'maps').read_text()
            require(len(mappings) <= 4 * 1024 * 1024, 'NATIVE_MAP_BOUNDS')
            for line in mappings.splitlines():
                fields = line.split(None, 5)
                if len(fields) >= 5 and fields[1][1:4] == 'w-s':
                    major, minor = fields[3].split(':')
                    require((os.makedev(int(major, 16), int(minor, 16)), int(fields[4])) not in identities,
                            'NATIVE_UNMANAGED_SHARED_MAPPING')
            entries = list((process / 'fd').iterdir())
            require(len(entries) <= 8192, 'NATIVE_FD_BOUNDS')
            for entry in (*entries, process / 'cwd', process / 'root'):
                try:
                    info = entry.stat()
                    if (info.st_dev, info.st_ino) in identities:
                        require(readonly(entry), 'NATIVE_UNMANAGED_OLD_MOUNT_FD')
                except FileNotFoundError:
                    continue
        except FileNotFoundError:
            continue
    return dict(result='NO_OBSERVED_OLD_HANDLES', atomic=False, launch_coverage='REQUIRED_SEPARATELY')
