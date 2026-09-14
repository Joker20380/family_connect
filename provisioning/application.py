"""Provisioning boundary over existing import/connect/disconnect/healthy methods.

The shared backend arbiter excludes GUI mutations until the journal commits or
rolls back. Durable pending ownership blocks GUI changes after process death.
Manual NetworkManager/root operations and older clients do not participate.
An interrupted import can leave an inactive profile; journal recovery finds it
from its pre-apply inventory while the shared operation owner excludes new imports.
"""
import base64
import hashlib
from contextlib import contextmanager
import os
from pathlib import Path
import tempfile

from .configuration import LOCAL_KEY


class BackendApplication:
    def __init__(self, driver, device):
        self.driver, self.device = driver, device
        self.current = None
        self.current_endpoint = None

    @contextmanager
    def transaction(self, journal):
        owner=hashlib.sha256(str(journal.path.resolve()).encode()).hexdigest()
        with self.driver.control_transaction(owner) as lease:
            self.lease=lease
            try:
                yield
            finally:
                # Core has released its journal lock here. Never clear ownership
                # after an unreadable journal or an unfinished rollback.
                with journal._locked() as directory:
                    record=journal.read(directory)
                if record['phase']=='IDLE':lease.finish()
                self.lease=None

    def reserve(self):
        self.lease.reserve()

    def snapshot(self, previous=None):
        profiles = [ident for ident, _ in self.driver.profiles()]
        active = [ident for ident in profiles if self.driver.active(ident)]
        if len(active) > 1:
            raise ValueError('ambiguous active VPN state')
        if previous is not None:
            previous = self._snapshot(previous)
            if active and active != previous['active']:
                raise ValueError('active connection changed outside control transaction')
            active = previous['active']
        return dict(known=profiles, active=active)

    @staticmethod
    def _snapshot(value):
        import re
        if (type(value) is not dict or set(value) != {'known', 'active'} or
                any(type(value[k]) is not list for k in value) or
                any(type(item) is not str or not re.fullmatch(r'(?:[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}|fcawg[0-9a-f]{8}|fctcp[0-9a-f]{8})', item)
                    for key in value for item in value[key]) or
                not set(value['active']) <= set(value['known']) or len(value['active']) > 1):
            raise ValueError('invalid application recovery metadata')
        return value

    def _install(self, profile):
        raw = profile.config
        if profile.transport != 'vless-reality':
            private = base64.b64encode(self.device._wireguard_key.private_bytes_raw()).decode()
            raw = raw.replace(LOCAL_KEY, private)
        with tempfile.TemporaryDirectory(prefix='fc-control-profile-') as directory:
            path = Path(directory) / 'profile.conf'
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, 'w') as stream:
                stream.write(raw)
            return self.driver.import_profile(path)

    def apply(self, verified, baseline):
        baseline = self._snapshot(baseline)
        self.current = None
        self.current_endpoint = None
        # Import is inactive in all existing Linux drivers. Snapshot was durably
        # recorded first, so crash during an import is recoverable without its ID.
        candidates = [self._install(profile) for profile in verified.state.transport_profiles]
        for ident in baseline['active']:
            if self.driver.active(ident):
                self.driver.disconnect(ident)
        gateways = {gateway.gateway_id: gateway.endpoint for gateway in verified.state.gateways}
        for ident, profile in zip(candidates, verified.state.transport_profiles):
            endpoint = gateways[profile.gateway_id]
            try:
                self.driver.connect(ident)
                if self.driver.control_healthy(ident, endpoint):
                    self.current = ident
                    self.current_endpoint = endpoint
                    return
            except Exception:
                # Authorization cancellation must stop this operation, not advance
                # to another transport and trigger another authorization prompt.
                if self.driver.active(ident):
                    self.driver.disconnect(ident)
                raise
            if self.driver.active(ident):
                self.driver.disconnect(ident)
        raise RuntimeError('configuration health failed')

    def healthy(self, verified):
        return (self.current is not None and self.current_endpoint is not None and
                self.driver.control_healthy(self.current, self.current_endpoint) is True)

    def rollback(self, staged, previous, baseline):
        expired = baseline.get('expired_active', [])
        baseline = self._snapshot({k:v for k,v in baseline.items() if k != 'expired_active'})
        if expired:
            self._snapshot(dict(known=baseline['known'], active=expired))
            for ident in expired:
                if self.driver.active(ident):
                    self.driver.disconnect(ident)
        current = {ident for ident, _ in self.driver.profiles()}
        # Shared durable ownership excludes GUI imports through crash recovery.
        for ident in sorted(current - set(baseline['known'])):
            if self.driver.active(ident):
                self.driver.disconnect(ident)
        for ident in baseline['active']:
            if ident not in current:
                raise RuntimeError('last-known-good profile missing')
            if not self.driver.active(ident):
                self.driver.connect(ident)
            if not self.driver.healthy(ident):
                raise RuntimeError('last-known-good health failed')
        self.current = baseline['active'][0] if baseline['active'] else None
