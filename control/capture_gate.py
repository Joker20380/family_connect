"""Opt-in, single-host admission/drain locks with durable ambiguous-operation markers."""
from contextlib import contextmanager, ExitStack
from contextvars import ContextVar
import fcntl
import math
import os
from pathlib import Path
import secrets
import stat
import time

CURRENT = ContextVar('capture_operation', default=None)
MARKER = b'family-connect/capture-operation/v1\n'


class GateError(OSError):
    pass


class Busy(GateError):
    pass


def require(condition, reason):
    if not condition:
        raise GateError(reason)


def identity(info):
    return info.st_dev, info.st_ino


def safe(info, directory=False):
    require((stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)) and
            info.st_uid == os.geteuid() and stat.S_IMODE(info.st_mode) == (0o700 if directory else 0o600),
            'GATE_PERMISSIONS')
    if not directory:
        require(info.st_nlink == 1 and info.st_size == 0, 'GATE_LOCK_SHAPE')


class Operation:
    def __init__(self, gate):
        self.gate = gate
        self.unsettled = False

    def uncertain(self):
        self.unsettled = True


@contextmanager
def external_operation():
    try:
        yield
    except BaseException:
        operation = CURRENT.get()
        if operation is not None:
            operation.uncertain()
        raise


def initialize(directory):
    directory = Path(directory)
    require(directory.is_absolute() and '..' not in directory.parts and
            all(not parent.is_symlink() for parent in directory.parents), 'GATE_PATH')
    directory.mkdir(mode=0o700, exist_ok=False)
    for name in ('admission.lock', 'operations.lock'):
        descriptor = os.open(directory / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    (directory / 'pending').mkdir(mode=0o700)
    descriptor = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return Gate(directory)


class Gate:
    def __init__(self, directory=None):
        self.directory = Path(directory) if directory is not None else None
        self.pins = None
        if self.directory is not None:
            with self.opened() as descriptors:
                self.pins = {name: identity(os.fstat(descriptor)) for name, descriptor in descriptors.items()}

    @contextmanager
    def opened(self):
        require(self.directory is not None and self.directory.is_absolute() and '..' not in self.directory.parts and
                all(not path.is_symlink() for path in (self.directory, *self.directory.parents)), 'GATE_PATH')
        with ExitStack() as stack:
            descriptors = {}
            for name, directory in (('.', True), ('admission.lock', False), ('operations.lock', False), ('pending', True)):
                descriptor = os.open(self.directory if name == '.' else name,
                    os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK | (os.O_DIRECTORY if directory else 0),
                    dir_fd=descriptors.get('.'))
                stack.callback(os.close, descriptor)
                info = os.fstat(descriptor)
                safe(info, directory)
                if self.pins is not None:
                    require(identity(info) == self.pins[name], 'GATE_REPLACED')
                descriptors[name] = descriptor
            yield descriptors

    @contextmanager
    def operation(self):
        current = CURRENT.get()
        if current is not None:
            require(self.directory is None or self.pins == current.gate.pins, 'NESTED_GATE_MISMATCH')
            yield current
            return
        operation = Operation(self)
        if self.directory is None:
            yield operation
            return
        with self.opened() as descriptors:
            try:
                fcntl.flock(descriptors['admission.lock'], fcntl.LOCK_SH | fcntl.LOCK_NB)
                fcntl.flock(descriptors['operations.lock'], fcntl.LOCK_SH | fcntl.LOCK_NB)
            except BlockingIOError:
                raise Busy('CAPTURE_ADMISSION_CLOSED') from None
            fcntl.flock(descriptors['admission.lock'], fcntl.LOCK_UN)
            pending = descriptors['pending']
            name = secrets.token_hex(16)
            descriptor = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                                 0o600, dir_fd=pending)
            try:
                marker_identity = identity(os.fstat(descriptor))
                require(os.write(descriptor, MARKER) == len(MARKER), 'MARKER_WRITE')
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            os.fsync(pending)
            token = CURRENT.set(operation)
            try:
                yield operation
            except BaseException:
                operation.uncertain()
                raise
            finally:
                CURRENT.reset(token)
                if not operation.unsettled:
                    info = os.stat(name, dir_fd=pending, follow_symlinks=False)
                    require(stat.S_ISREG(info.st_mode) and identity(info) == marker_identity, 'MARKER_REPLACED')
                    os.unlink(name, dir_fd=pending)
                    os.fsync(pending)

    @contextmanager
    def drain(self, timeout):
        require(type(timeout) in (int, float) and math.isfinite(timeout) and 0 < timeout <= 5,
                'DRAIN_DEADLINE')
        require(CURRENT.get() is None, 'DRAIN_INSIDE_OPERATION')
        deadline = time.monotonic() + timeout
        with self.opened() as descriptors:
            try:
                fcntl.flock(descriptors['admission.lock'], fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise Busy('CAPTURE_ALREADY_PENDING') from None
            while True:
                if time.monotonic() >= deadline:
                    raise Busy('DRAIN_TIMEOUT')
                try:
                    fcntl.flock(descriptors['operations.lock'], fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    time.sleep(min(0.01, max(0, deadline - time.monotonic())))
            with os.scandir(descriptors['pending']) as entries:
                require(next(entries, None) is None, 'UNSETTLED_OPERATION')
            yield
