"""POSIX Friends configuration owner with durable, serialized sequence acceptance.

Private 0700/0600 files use the existing identity directory. This is not an encrypted
keyring. Neither a cache hit nor a successful write applies a VPN or grants entitlement.
"""
import fcntl
import os
import secrets
import stat
from contextlib import contextmanager

from device_identity.device import _private_directory, _read_key, _create_key, _FRIENDS_MARKER
from device_identity.friends import _exists
from .friends_catalog import parse, fields, verify, require

_NAME = 'friends.configuration.json'
_MARKER = b'FC-FRIENDS-CONFIGURATION-1\n'
_LIMIT = 65536


class FriendsConfigurationStore:
    def __init__(self, path, device, anchor):
        self.path, self.device, self.anchor = path, device, anchor

    @contextmanager
    def _locked(self):
        with _private_directory(self.path, create=False) as directory:
            lock = os.open('.lock', os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
            try:
                info = os.fstat(lock)
                require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid()
                        and stat.S_IMODE(info.st_mode) == 0o600 and info.st_nlink == 1)
                fcntl.flock(lock, fcntl.LOCK_EX)
                require(_read_key(directory, 'friends.initialized', len(_FRIENDS_MARKER)) == _FRIENDS_MARKER)
                # Ensure the caller still owns the same persisted identity, before any HTTP.
                require(_read_key(directory, 'reticulum.key', 64) == self.device._identity.get_private_key())
                require(_read_key(directory, 'wireguard.key', 32) == self.device._wireguard_key.private_bytes_raw())
                yield directory
            finally:
                os.close(lock)

    @staticmethod
    def _read(directory):
        exists = _exists(directory, _NAME); marked = _exists(directory, _NAME+'.initialized')
        require(exists == marked)
        if not exists:
            return {}
        require(_read_key(directory, _NAME+'.initialized', len(_MARKER)) == _MARKER)
        info = os.stat(_NAME, dir_fd=directory, follow_symlinks=False)
        require(0 < info.st_size <= _LIMIT)
        data = parse(_read_key(directory, _NAME, info.st_size).decode('utf-8'))
        require(type(data) is dict and 1 <= len(data) <= 2 and set(data) <= {'ru', 'nl'})
        return data

    def _verify(self, reply, country, floor=0, previous_hash=None):
        return verify(reply, self.anchor, self.device.reference, country,
                      self.device._wireguard_key.private_bytes_raw(), floor=floor, previous_hash=previous_hash)

    def accept(self, country, fetch):
        """fetch(floor, hash) -> response; serialize verification, fetch and durable save.

        Never returns a stale profile after HTTP denial or malformed new configuration.
        Caller runs off the GUI thread. A single lock protects both countries' floor.
        """
        require(country in ('ru', 'nl'))
        with self._locked() as directory:
            cache = self._read(directory)
            prior = [self._verify(reply, region) for region, reply in cache.items()]
            floor = max((p.sequence for p in prior), default=0)
            hashes = {p.catalog_hash for p in prior if p.sequence == floor}
            require(len(hashes) <= 1)
            previous = next(iter(hashes), None)
            response = fetch(floor, previous)
            accepted = self._verify(response, country, floor, previous)
            cache[country] = response
            import json
            raw = json.dumps(cache, separators=(',', ':'), allow_nan=False).encode()
            require(len(raw) <= _LIMIT)
            if not _exists(directory, _NAME+'.initialized'):
                _create_key(directory, _NAME+'.initialized', _MARKER)
            temporary = '.friends-config-'+secrets.token_hex(16)
            fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory)
            try:
                with os.fdopen(fd, 'wb') as stream:
                    stream.write(raw); stream.flush(); os.fsync(stream.fileno())
                os.replace(temporary, _NAME, src_dir_fd=directory, dst_dir_fd=directory)
                os.fsync(directory)
            finally:
                if _exists(directory, temporary):os.unlink(temporary, dir_fd=directory)
            return accepted
