"""POSIX Friends identity owner: explicit enrollment, strict resume, no key reset.

Uses the existing private-directory/key format and shared flock. An existing paired
identity can be adopted explicitly without replacing either key. The marker records
that Friends enrollment has begun; incomplete storage requires recovery, not a new
identity. Private keys are permission-protected files, not a desktop keyring claim.
"""
import os
import stat

import RNS
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey

from .device import DeviceIdentity, _private_directory, _read_key, _create_key, _FRIENDS_MARKER

_MARKER = _FRIENDS_MARKER


def _exists(directory, name):
    try:
        os.stat(name, dir_fd=directory, follow_symlinks=False)
        return True
    except FileNotFoundError:
        return False


def load_friends_identity(path, *, create):
    if type(create) is not bool:
        raise ValueError('Explicit creation policy required')
    import fcntl
    with _private_directory(path, create=create) as directory:
        flags = os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK
        if create:
            flags |= os.O_CREAT
        lock = os.open('.lock', flags, 0o600, dir_fd=directory)
        try:
            info = os.fstat(lock)
            if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                    or stat.S_IMODE(info.st_mode) != 0o600 or info.st_nlink != 1):
                raise ValueError('Unsafe identity lock')
            fcntl.flock(lock, fcntl.LOCK_EX)
            marked = _exists(directory, 'friends.initialized')
            have_rns = _exists(directory, 'reticulum.key')
            have_wg = _exists(directory, 'wireguard.key')
            if have_rns != have_wg or (marked and not have_rns):
                raise ValueError('Identity recovery required')
            if not marked and not create:
                raise ValueError('Friends identity not enrolled')
            if marked and _read_key(directory, 'friends.initialized', len(_MARKER)) != _MARKER:
                raise ValueError('Invalid identity marker')
            if have_rns:
                raw = _read_key(directory, 'reticulum.key', 64)
                wg = _read_key(directory, 'wireguard.key', 32)
                identity = RNS.Identity(create_keys=False)
                if not identity.load_private_key(raw):
                    raise ValueError('Invalid identity key')
                device = DeviceIdentity(identity, X25519PrivateKey.from_private_bytes(wg))
                if not marked:
                    _create_key(directory, 'friends.initialized', _MARKER)
                return device
            # No remote proof can be sent until every write completes and we return.
            device = DeviceIdentity.generate()
            _create_key(directory, 'friends.initialized', _MARKER)
            _create_key(directory, 'reticulum.key', device._identity.get_private_key())
            _create_key(directory, 'wireguard.key', device._wireguard_key.private_bytes_raw())
            return device
        finally:
            os.close(lock)
