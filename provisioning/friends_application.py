"""Friends TCP apply/recovery using the desktop's shared operation owner.

Only public profile identifiers and the pre-apply inventory enter this journal.
Credentials remain in the verified configuration cache and the privileged helper.
An unfinished transaction always rolls back before another apply can start.
"""
import hashlib
import json
import os
import secrets
from pathlib import Path

from device_identity.device import _create_key, _read_key
from device_identity.friends import _exists
from .application import BackendApplication
from .friends_catalog import fields, parse, require

_NAME = 'friends.application.json'
_MARKER = b'FC-FRIENDS-APPLICATION-1\n'
_LIMIT = 65536


class FriendsApplication:
    def __init__(self, store, driver):
        self.store, self.driver = store, driver
        self.adapter = BackendApplication(driver, store.device)
        self.owner = hashlib.sha256((str(Path(store.path).resolve())+'/friends-apply').encode()).hexdigest()

    def _idle(self):
        return dict(schema=1, device=self.store.device.reference, phase='IDLE', baseline=None)

    def _read(self, directory):
        exists, marked = _exists(directory, _NAME), _exists(directory, _NAME+'.initialized')
        require(exists == marked)
        if not exists:
            return self._idle()
        require(_read_key(directory, _NAME+'.initialized', len(_MARKER)) == _MARKER)
        size = os.stat(_NAME, dir_fd=directory, follow_symlinks=False).st_size
        require(0 < size <= _LIMIT)
        record = parse(_read_key(directory, _NAME, size).decode())
        fields(record, 'schema device phase baseline')
        require(type(record['schema']) is int and record['schema'] == 1
                and record['device'] == self.store.device.reference
                and record['phase'] in ('IDLE', 'APPLYING'))
        if record['phase'] == 'IDLE':
            require(record['baseline'] is None)
        else:
            self.adapter._snapshot(record['baseline'])
        return record

    @staticmethod
    def _write(directory, record):
        raw = json.dumps(record, separators=(',', ':'), allow_nan=False).encode()
        require(len(raw) <= _LIMIT)
        if not _exists(directory, _NAME+'.initialized'):
            _create_key(directory, _NAME+'.initialized', _MARKER)
        temporary = '.friends-apply-'+secrets.token_hex(16)
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory)
        try:
            with os.fdopen(fd, 'wb') as stream:
                stream.write(raw); stream.flush(); os.fsync(stream.fileno())
            os.replace(temporary, _NAME, src_dir_fd=directory, dst_dir_fd=directory)
            os.fsync(directory)
        finally:
            if _exists(directory, temporary):os.unlink(temporary, dir_fd=directory)

    def _recover(self, directory, lease):
        record = self._read(directory)
        if record['phase'] == 'APPLYING':
            self.adapter.rollback(None, None, record['baseline'])
            self._write(directory, self._idle())
        lease.finish()

    def recover(self):
        with self.driver.control_transaction(self.owner) as lease:
            with self.store._locked() as directory:
                self._recover(directory, lease)

    def connect(self, fetch):
        """fetch verifies and durably saves configuration before any VPN mutation."""
        from types import SimpleNamespace
        with self.driver.control_transaction(self.owner) as lease:
            with self.store._locked() as directory:
                self._recover(directory, lease)
            configuration = fetch()
            with self.store._locked() as directory:
                baseline = self.adapter.snapshot()
                # Persist baseline before import/route changes. Reserve first so
                # an interrupted write blocks normal GUI mutation until recovery.
                lease.reserve()
                record = self._idle()
                record.update(phase='APPLYING', baseline=baseline)
                self._write(directory, record)
                try:
                    profile = SimpleNamespace(transport='vless-reality', config=configuration.tcp)
                    ident = self.adapter._install(profile)
                    for previous in baseline['active']:
                        self.driver.disconnect(previous)
                    self.driver.connect(ident)
                    if not self.driver.healthy(ident):
                        raise RuntimeError('Friends VPN health failed')
                    self._write(directory, self._idle())
                except Exception:
                    self.adapter.rollback(None, None, baseline)
                    self._write(directory, self._idle())
                    lease.finish()
                    raise
                lease.finish()
                return dict(profile=ident, country=configuration.country,
                            transport='tcp', sequence=configuration.sequence)
