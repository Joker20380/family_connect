"""Owned rehearsal filesystem boundary, independent of transport inputs."""

import os
from pathlib import Path
import stat
import tempfile

from .contracts import fail
from .installer import fsync_directory


def checked(path, *, directory=False, owner=None):
    path = Path(path)
    if not path.is_absolute() or '..' in path.parts:
        fail('private_path')
    for parent in reversed((path, *path.parents)):
        metadata = parent.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            fail('private_symlink')
        if parent != path and not stat.S_ISDIR(metadata.st_mode):
            fail('private_parent')
    metadata = path.stat()
    if owner is not None and metadata.st_uid != owner:
        fail('private_owner')
    if directory:
        if not stat.S_ISDIR(metadata.st_mode):
            fail('private_directory')
    elif not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        fail('private_file')
    return path


def read_private(path, *, modes=(0o600,), owner=None, limit=1024*1024):
    path = checked(path, owner=owner)
    metadata = path.stat()
    if stat.S_IMODE(metadata.st_mode) not in modes or metadata.st_size > limit:
        fail('private_mode_or_size')
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(descriptor, 'rb') as source:
        actual = os.fstat(source.fileno())
        if (actual.st_dev, actual.st_ino, actual.st_nlink) != (metadata.st_dev, metadata.st_ino, 1):
            fail('private_file_changed')
        return source.read(limit + 1)


def write_private(path, content, *, mode=0o600, uid=None, gid=None, replace=False):
    path = Path(path)
    checked(path.parent, directory=True)
    if path.exists() or path.is_symlink():
        checked(path, owner=uid)
        if not replace:
            fail('private_file_exists')
    descriptor, temporary = tempfile.mkstemp(prefix='.pending-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as output:
            os.fchmod(output.fileno(), mode)
            if uid is not None and gid is not None:
                os.fchown(output.fileno(), uid, gid)
            output.write(content)
            output.flush()
            os.fsync(output.fileno())
        if replace:
            os.replace(temporary, path)
        else:
            os.link(temporary, path, follow_symlinks=False)
            os.unlink(temporary)
        fsync_directory(path.parent)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def remove_private(path, *, owner=None):
    path = checked(path, owner=owner)
    metadata = path.stat()
    if metadata.st_mode & stat.S_IWUSR:
        descriptor = os.open(path, os.O_WRONLY | os.O_NOFOLLOW)
        with os.fdopen(descriptor, 'wb') as output:
            actual = os.fstat(output.fileno())
            if (actual.st_dev, actual.st_ino, actual.st_nlink) != (metadata.st_dev, metadata.st_ino, 1):
                fail('private_file_changed')
            remaining = actual.st_size
            while remaining:
                amount = min(remaining,65536)
                output.write(bytes(amount))
                remaining -= amount
            output.flush()
            os.fsync(output.fileno())
    path.unlink()
    fsync_directory(path.parent)
