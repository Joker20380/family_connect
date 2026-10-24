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
from .friends_catalog import parse, fields, verify, verify_catalog, require

_NAME = 'friends.configuration.json'
_MARKER = b'FC-FRIENDS-CONFIGURATION-1\n'
_LIMIT = 65536
_FLOOR = 'friends.catalog-floor.json'
_FLOOR_MARKER = b'FC-FRIENDS-CATALOG-FLOOR-1\n'


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

    def _catalog_floor(self, directory):
        exists, marked = _exists(directory, _FLOOR), _exists(directory, _FLOOR+'.initialized')
        require(exists or not marked)
        if marked:
            require(_read_key(directory, _FLOOR+'.initialized', len(_FLOOR_MARKER)) == _FLOOR_MARKER)
        if not exists:
            return None
        size = os.stat(_FLOOR, dir_fd=directory, follow_symlinks=False).st_size
        require(0 < size <= 16384)
        record = parse(_read_key(directory, _FLOOR, size).decode('utf-8'))
        fields(record, 'schema device catalog')
        require(type(record['schema']) is int and record['schema'] == 1 and record['device'] == self.device.reference)
        verify_catalog(record['catalog'], self.anchor)
        if not marked:
            _create_key(directory, _FLOOR+'.initialized', _FLOOR_MARKER)
        return record['catalog']

    def _current(self, directory, additional=None):
        cache = self._read(directory)
        entries = [(reply['catalog'], self._verify(reply, country)) for country, reply in cache.items()]
        saved = self._catalog_floor(directory)
        for envelope in (saved, additional):
            if envelope is not None:
                entries.append((envelope, verify_catalog(envelope, self.anchor)))
        floor = max((entry.sequence for _, entry in entries), default=0)
        highest = [(envelope, entry) for envelope, entry in entries if entry.sequence == floor]
        require(len({entry.catalog_hash for _, entry in highest}) <= 1)
        return cache, highest[0] if highest else (None, None), saved

    def signed_floors(self):
        with self._locked() as directory:
            cache, (envelope, _floor), saved = self._current(directory)
            return [envelope] if saved is not None else [reply['catalog'] for reply in cache.values()]

    def merge_catalog_floor(self, envelope):
        """Persist a verified public high-water mark, without changing device profiles."""
        import json
        if envelope is None:
            return
        with self._locked() as directory:
            _cache, (highest, floor), saved = self._current(directory, envelope)
            if highest is None or saved == highest:
                return
            raw = json.dumps(dict(schema=1, device=self.device.reference, catalog=highest),
                             separators=(',', ':'), allow_nan=False).encode()
            require(len(raw) <= 16384)
            temporary = '.friends-floor-'+secrets.token_hex(16)
            descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory)
            try:
                with os.fdopen(descriptor, 'wb') as output:
                    output.write(raw)
                    output.flush()
                    os.fsync(output.fileno())
                os.replace(temporary, _FLOOR, src_dir_fd=directory, dst_dir_fd=directory)
                os.fsync(directory)
            finally:
                if _exists(directory, temporary):
                    os.unlink(temporary, dir_fd=directory)
            checked = self._catalog_floor(directory)
            readback = verify_catalog(checked, self.anchor)
            require(checked == highest and (readback.sequence, readback.catalog_hash) == (floor.sequence, floor.catalog_hash))

    def accept(self, country, fetch):
        """fetch(floor, hash) -> response; serialize verification, fetch and durable save.

        Never returns a stale profile after HTTP denial or malformed new configuration.
        Caller runs off the GUI thread. A single lock protects both countries' floor.
        """
        require(country in ('ru', 'nl'))
        with self._locked() as directory:
            cache, (_envelope, accepted_floor), _saved = self._current(directory)
            floor = accepted_floor.sequence if accepted_floor else 0
            previous = accepted_floor.catalog_hash if accepted_floor else None
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
