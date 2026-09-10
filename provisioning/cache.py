"""Linux reference cache. Atomic envelope/floors; explicit first initialization.

Trusted parent directory and local filesystem required. File permissions cannot
prevent an owner/root attacker restoring an entire old backup. Native platform
secure storage and tunnel lifecycle integration are separate work.
"""
import base64
import fcntl
import json
import os
import secrets
import stat
from contextlib import contextmanager
from pathlib import Path

from device_identity.device import _private_directory
from .envelope import MAX_ENVELOPE_BYTES, ProvisioningRejected, _unique_fields


class ProvisioningCache:
    def __init__(self, path, verifier):
        self.path = Path(path)
        self.verifier = verifier

    def initialize(self):
        # Never recreate a lost record in an existing cache directory.
        self.path.mkdir(mode=0o700)
        with _private_directory(self.path) as directory:
            self._write(directory, dict(revision=0, entitlement_revision=1, last_now=0, verified_at=0, envelope=None))

    @contextmanager
    def _locked(self):
        if not self.path.is_dir():
            raise ProvisioningRejected('cache requires explicit initialization')
        with _private_directory(self.path) as directory:
            fd = os.open('.lock', os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK,
                         0o600, dir_fd=directory)
            try:
                self._safe(fd)
                fcntl.flock(fd, fcntl.LOCK_EX)
                yield directory
            finally:
                os.close(fd)

    @staticmethod
    def _safe(fd):
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or
                stat.S_IMODE(info.st_mode) != 0o600 or info.st_nlink != 1):
            raise ProvisioningRejected('unsafe cache file')

    def _read(self, directory, now):
        fd = os.open('cache.json', os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        try:
            self._safe(fd)
            raw = os.read(fd, MAX_ENVELOPE_BYTES * 2 + 1)
            if len(raw) > MAX_ENVELOPE_BYTES * 2:
                raise ValueError()
            record = json.loads(raw, object_pairs_hook=_unique_fields)
            if (type(record) is not dict or
                    set(record) != {'revision', 'entitlement_revision', 'last_now', 'verified_at', 'envelope'} or
                    any(type(record[k]) is not int for k in ('revision', 'entitlement_revision', 'last_now', 'verified_at')) or
                    not 0 <= record['revision'] < 2**63 or
                    not 1 <= record['entitlement_revision'] < 2**63 or record['last_now'] < record['verified_at'] or record['verified_at'] < 0 or
                    type(now) is not int or now < record['last_now'] or
                    (record['revision'] == 0) != (record['envelope'] is None)):
                raise ValueError()
            if record['envelope'] is not None:
                envelope = base64.b64decode(record['envelope'], validate=True)
                # Authenticate persisted floors even after lease expiration. This
                # historical check never authorizes use; load verifies at now below.
                verified = self.verifier.verify(envelope, now=record['verified_at'],
                    minimum_revision=record['revision'] - 1,
                    minimum_entitlement_revision=record['entitlement_revision'])
                if (verified.state.revision != record['revision'] or
                        verified.state.entitlement_revision != record['entitlement_revision']):
                    raise ValueError()
            return record
        except (ValueError, TypeError, UnicodeError, RecursionError):
            raise ProvisioningRejected('invalid cache or clock rollback') from None
        finally:
            os.close(fd)

    @staticmethod
    def _write(directory, record):
        name = '.cache-' + secrets.token_hex(16)
        fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                     0o600, dir_fd=directory)
        try:
            with os.fdopen(fd, 'w') as stream:
                json.dump(record, stream, separators=(',', ':'))
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(name, 'cache.json', src_dir_fd=directory, dst_dir_fd=directory)
            os.fsync(directory)
        finally:
            try:
                os.unlink(name, dir_fd=directory)
            except FileNotFoundError:
                pass

    def accept(self, envelope, *, now):
        with self._locked() as directory:
            record = self._read(directory, now)
            record['last_now'] = now
            self._write(directory, record)
            if record['envelope'] is not None and envelope == base64.b64decode(record['envelope']):
                # Exact persisted bytes may be redelivered after a lost response.
                floor = record['revision'] - 1
            else:
                floor = record['revision']
            verified = self.verifier.verify(envelope, now=now, minimum_revision=floor,
                minimum_entitlement_revision=record['entitlement_revision'])
            self._write(directory, dict(revision=verified.state.revision,
                entitlement_revision=verified.state.entitlement_revision, last_now=now, verified_at=now,
                envelope=base64.b64encode(envelope).decode()))
            return verified

    def load(self, *, now):
        with self._locked() as directory:
            record = self._read(directory, now)
            record['last_now'] = now
            self._write(directory, record)
            if record['envelope'] is None:
                return None
            verified = self.verifier.verify(base64.b64decode(record['envelope']), now=now,
                minimum_revision=record['revision'] - 1,
                minimum_entitlement_revision=record['entitlement_revision'])
            record['last_now'] = now
            self._write(directory, record)
            return verified
