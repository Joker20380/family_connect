"""Root-only, fail-closed MESH admission across service processes."""
import fcntl
import os
from pathlib import Path
import stat
import threading
import time

DIRECTORY = Path('/run/family-connect-mesh-owner')


class OwnershipError(RuntimeError):
    pass


def prepare_runtime(directory):
    for parent in reversed(directory.parents):
        info = parent.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o022:
            raise OwnershipError('UNSAFE_OWNERSHIP')
    directory.mkdir(mode=0o711, exist_ok=True)
    expected = directory.lstat()
    descriptor = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        actual = os.fstat(descriptor)
        if ((actual.st_dev, actual.st_ino) != (expected.st_dev, expected.st_ino) or
                actual.st_uid != 0 or actual.st_mode & 0o022):
            raise OwnershipError('UNSAFE_OWNERSHIP')
        os.fchmod(descriptor, 0o711)
    finally:
        os.close(descriptor)


def locked_file(path):
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    info = os.fstat(descriptor)
    if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_nlink != 1 or stat.S_IMODE(info.st_mode) != 0o600:
        os.close(descriptor)
        raise OwnershipError('UNSAFE_OWNERSHIP')
    return descriptor


class Ownership:
    def __init__(self, role, directory=DIRECTORY):
        if role not in ('vpn', 'chat'):
            raise OwnershipError('UNSAFE_OWNERSHIP')
        self.role, self.directory = role, Path(directory)
        self.intent = self.descriptor = None
        self.active = False
        self.lock = threading.RLock()

    def acquire(self, cancel, deadline):
        with self.lock:
            return self._acquire(cancel, deadline)

    def _acquire(self, cancel, deadline):
        if os.geteuid() != 0:
            raise OwnershipError('UNSAFE_OWNERSHIP')
        if self.descriptor is not None or self.intent is not None:
            raise OwnershipError('STALE_OWNERSHIP')
        prepare_runtime(self.directory)
        try:
            self.intent = locked_file(self.directory / 'vpn.lock')
            if self.role == 'vpn':
                fcntl.flock(self.intent, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.descriptor = locked_file(self.directory / 'transport.lock')
            while True:
                if cancel.is_set() or time.monotonic() >= deadline:
                    raise OwnershipError('ADMISSION_CANCELLED')
                if self.role == 'chat' and self.preempted():
                    raise OwnershipError('VPN_RESERVED')
                try:
                    fcntl.flock(self.descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if self.role == 'chat':
                        raise OwnershipError('OWNER_BUSY') from None
                    cancel.wait(min(.05, max(0, deadline - time.monotonic())))
            if os.fstat(self.descriptor).st_size:
                raise OwnershipError('CLEANUP_UNCONFIRMED')
            if self.role == 'chat' and self.preempted():
                raise OwnershipError('VPN_RESERVED')
            os.write(self.descriptor, self.role.encode('ascii'))
            os.fsync(self.descriptor)
            self.active = True
            return self
        except BaseException:
            self.close()
            raise

    def preempted(self):
        with self.lock:
            if self.role != 'chat' or self.intent is None:
                return False
            try:
                fcntl.flock(self.intent, fcntl.LOCK_SH | fcntl.LOCK_NB)
            except BlockingIOError:
                return True
            fcntl.flock(self.intent, fcntl.LOCK_UN)
            return False

    def finish(self):
        with self.lock:
            if not self.active or self.descriptor is None:
                raise OwnershipError('STALE_OWNERSHIP')
            os.ftruncate(self.descriptor, 0)
            os.fsync(self.descriptor)
            self.active = False
            self.close()

    def close(self):
        with self.lock:
            for name in ('descriptor', 'intent'):
                descriptor = getattr(self, name)
                if descriptor is not None:
                    os.close(descriptor)
                    setattr(self, name, None)
