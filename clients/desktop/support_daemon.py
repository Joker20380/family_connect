"""Read-only VPN sampling and opt-in support in the existing non-root session owner."""
import copy
import json
from pathlib import Path
import re
import threading
import time
import uuid

from backend import DesktopDiagnostics, backend
from messenger.local import LocalError


def version_info(root):
    with (Path(root)/'VERSION').open('rb') as source:
        raw = source.read(65)
    version = raw.decode('ascii').strip()
    if len(raw) > 64 or not re.fullmatch(r'\d{1,3}\.\d{1,3}\.\d{1,3}', version):
        raise ValueError('Invalid packaged version')
    major, minor, patch = map(int, version.split('.'))
    return version, major*1000000 + minor*1000 + patch


class SupportCollector:
    def __init__(self, version, *, driver=None, environment=DesktopDiagnostics.environment):
        self.version = version
        self.driver = driver or backend()
        self.environment = environment
        self.collector = DesktopDiagnostics(version)
        self.last_session = {}
        self.last_state = 'DISCONNECTED'
        self.generation = ''

    def __call__(self):
        environment = self.environment()
        unavailable = dict(state='UNKNOWN', network_class=environment.get('network_class', 'UNKNOWN'),
                           restricted_readiness='UNKNOWN', vpn_capture_open=False)
        try:
            service = self.driver.auto_status()
            if service.get('desired_connected') or service.get('state') != 'DISCONNECTED':
                transport = 'auto'
                generation = service.get('generation', '')
                if generation and generation != self.generation:
                    self.collector = DesktopDiagnostics(self.version)
                    self.last_session = {}
                    self.generation = generation
            else:
                service = self.driver.mesh_status()
                if service.get('desired_connected') or service.get('state') != 'DISCONNECTED':
                    transport = 'mesh'
                else:
                    state, transport = self.driver.support_normal_state()
                    service = dict(state=state)
            if service['state'] == 'CONNECTING' and self.last_state not in ('CONNECTING', 'RESTORING'):
                self.last_session = {}
            self.last_state = service['state']
            self.collector.sample(service['state'], transport, service.get('requested_profile', 'P0'), service)
            result = json.loads(self.collector.export(environment))['ring']
            if result['restricted_session'].get('session_tag'):
                self.last_session = copy.deepcopy(result['restricted_session'])
            elif service['state'] in ('DISCONNECTED', 'FAILED'):
                result['restricted_session'] = copy.deepcopy(self.last_session)
            return result
        except Exception:
            unavailable['restricted_session'] = copy.deepcopy(self.last_session)
            return unavailable


class SupportSession:
    def __init__(self, friends, snapshot, version_code, *, clock=time.monotonic):
        self.friends, self.snapshot, self.version_code = friends, snapshot, version_code
        self.clock = clock
        self.lock = threading.RLock()
        self.upload = None
        self.revision = uuid.uuid4().hex
        self.next_load = 0
        self.storage_error = False
        self.closed = False

    def poll(self):
        with self.lock:
            if self.closed:
                return
            if self.upload is None and self.clock() >= self.next_load:
                self.next_load = self.clock() + 60
                try:
                    self.upload = self.friends.support_upload(self.snapshot, self.version_code)
                except Exception:
                    return
            if self.upload is not None:
                self.upload.tick()

    def status(self):
        with self.lock:
            state = self.upload.status() if self.upload is not None else dict(enabled=False, until=0, state='UNAVAILABLE')
            return dict(state, revision=self.revision, available=self.upload is not None and not self.closed,
                        background=True, storage_error=self.storage_error)

    def change(self, enabled, revision):
        with self.lock:
            if self.closed or self.upload is None:
                raise LocalError('support_unavailable')
            if type(enabled) is not bool or revision != self.revision:
                raise LocalError('support_conflict')
            self.revision = uuid.uuid4().hex
            try:
                if enabled:
                    if not self.upload.status()['enabled']:
                        self.upload.enable()
                else:
                    self.upload.disable()
            except Exception:
                self.storage_error = True
                self.upload.cancel()
                raise LocalError('support_unavailable') from None
            self.storage_error = False
            self.upload.tick()
            return self.status()

    def close(self):
        with self.lock:
            self.closed = True
            if self.upload is not None:
                self.upload.close()
