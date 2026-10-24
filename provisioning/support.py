"""Accepted106 opt-in snapshots and completion-based upload scheduling."""
import json
import os
import re
import stat
import threading
import time
import uuid

from device_identity.device import _private_directory
from .friends import FriendsError


class SupportSnapshot:
    LIMIT = 4096
    MAX_NUMBER = 2**53 - 1
    COUNTERS = ('protocol_errors', 'retransmissions', 'retry_bytes', 'sent_bytes',
                'received_bytes', 'recovery_timeouts', 'mux_window', 'observed_at_ms')
    REASONS = ('open_replay', 'unknown_stream', 'open_state', 'data_state', 'credit_state',
               'fin_state', 'close_state', 'frame_kind', 'dns_replay', 'dns_role', 'dns_unmatched')
    WINDOWS = dict(local_send='send_window', local_receive='receive_window',
                   peer_receive='peer_receive_window', effective_send='effective_send_window')
    ENUMS = dict(state='DISCONNECTED CONNECTING CONNECTED RESTORING FAILED STOPPING',
                 network='WIFI CELLULAR ETHERNET VPN NONE', readiness='READY NOT_READY',
                 speed_profile='P0 P1 P2', mux_profile='LEGACY64 CREDIT128',
                 terminal_reason='NONE CANCELLED REMOTE_RESET RELIABLE_EXHAUSTED IO_CLOSED MUX_PROTOCOL RELIABLE_PROTOCOL FAMILY_REJECTED DEADLINE NETWORK_TIMEOUT')

    @classmethod
    def number(cls, value):
        return type(value) is int and 0 <= value <= cls.MAX_NUMBER

    @staticmethod
    def object(value):
        return value if type(value) is dict else {}

    @classmethod
    def project(cls, ring, version, now, *, platform='linux', report_id=None):
        ring = cls.object(ring)
        session = cls.object(ring.get('restricted_session'))
        metrics = {}
        for target, source, field in [('state', ring, 'state'), ('network', ring, 'network_class'),
                                     ('readiness', ring, 'restricted_readiness')]:
            value = source.get(field)
            metrics[target] = value if type(value) is str and value in cls.ENUMS[target].split() else 'UNKNOWN'
        for field in ('speed_profile', 'mux_profile', 'terminal_reason'):
            value = session.get(field)
            metrics[field] = value if type(value) is str and value in cls.ENUMS[field].split() else 'UNKNOWN'
        if type(ring.get('vpn_capture_open')) is bool:
            metrics['vpn_capture_open'] = ring['vpn_capture_open']
        tag = session.get('session_tag')
        if type(tag) is str and re.fullmatch('[0-9a-f]{32}|[0-9a-f]{64}', tag):
            metrics['session_tag'] = tag
        limits = cls.object(session.get('reliable_limits'))
        reasons = cls.object(session.get('protocol_error_reasons'))
        for source, names in ((session, {key: key for key in cls.COUNTERS}),
                              (limits, cls.WINDOWS), (reasons, {key: key for key in cls.REASONS})):
            for field, target in names.items():
                if cls.number(source.get(field)):
                    metrics[target] = source[field]
        result = dict(schema=1, report_id=report_id or uuid.uuid4().hex, platform=platform,
                      version_code=version, sampled_at_ms=now, consent=True, metrics=metrics)
        cls.encode(result)
        return result

    @classmethod
    def encode(cls, report):
        if (type(report) is not dict or set(report) != {'schema', 'report_id', 'platform', 'version_code', 'sampled_at_ms', 'consent', 'metrics'} or
                type(report['schema']) is not int or report['schema'] != 1 or report['consent'] is not True or
                report['platform'] not in ('linux', 'windows') or
                type(report['report_id']) is not str or not re.fullmatch('[0-9a-f]{32}', report['report_id']) or
                not cls.number(report['version_code']) or not cls.number(report['sampled_at_ms'])):
            raise FriendsError('invalid_input')
        metrics = report['metrics']
        numbers = set(cls.COUNTERS + cls.REASONS) | set(cls.WINDOWS.values())
        if type(metrics) is not dict or not set(metrics) <= numbers | cls.ENUMS.keys() | {'session_tag', 'vpn_capture_open'}:
            raise FriendsError('invalid_input')
        for field, value in metrics.items():
            if field in numbers:
                valid = cls.number(value)
            elif field in cls.ENUMS:
                valid = type(value) is str and value in cls.ENUMS[field].split() + ['UNKNOWN']
            elif field == 'session_tag':
                valid = type(value) is str and re.fullmatch('[0-9a-f]{32}|[0-9a-f]{64}', value)
            else:
                valid = type(value) is bool
            if not valid:
                raise FriendsError('invalid_input')
        raw = json.dumps(report, separators=(',', ':'), allow_nan=False)
        if len(raw.encode()) > cls.LIMIT:
            raise FriendsError('invalid_input')
        return raw


class SupportConsent:
    DURATION = 7 * 86400
    NAME = 'support-consent.json'

    def __init__(self, path, registration, *, clock=time.time):
        self.path, self.registration, self.clock = path, registration, clock
        self.until = 0
        try:
            with _private_directory(path, create=False) as directory:
                descriptor = os.open(self.NAME, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
                with os.fdopen(descriptor, 'rb') as source:
                    info = os.fstat(source.fileno())
                    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o600 or info.st_nlink != 1:
                        return
                    raw = source.read(513)
                from .friends import FriendsClient
                value = json.loads(raw, object_pairs_hook=FriendsClient._object)
                if len(raw) <= 512 and type(value) is dict and set(value) == {'schema', 'registration', 'until'}:
                    if type(value['schema']) is int and value['schema'] == 1 and value['registration'] == registration and type(value['until']) is int:
                        self.until = value['until']
        except (OSError, ValueError, TypeError):
            pass

    def enabled(self):
        return 0 < self.until - self.clock() <= self.DURATION

    def grant(self):
        until = int(self.clock()) + self.DURATION
        raw = json.dumps(dict(schema=1, registration=self.registration, until=until), separators=(',', ':')).encode()
        with _private_directory(self.path, create=False) as directory:
            temporary = '.support-consent-' + uuid.uuid4().hex
            descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory)
            try:
                with os.fdopen(descriptor, 'wb') as target:
                    target.write(raw)
                    target.flush()
                    os.fsync(target.fileno())
                os.replace(temporary, self.NAME, src_dir_fd=directory, dst_dir_fd=directory)
                os.fsync(directory)
            finally:
                try:os.unlink(temporary, dir_fd=directory)
                except FileNotFoundError:pass
        self.until = until

    def revoke(self):
        self.until = 0
        with _private_directory(self.path, create=False) as directory:
            try:os.unlink(self.NAME, dir_fd=directory)
            except FileNotFoundError:pass
            os.fsync(directory)


class SupportUpload:
    def __init__(self, consent, sender, snapshot, version, *, monotonic=time.monotonic):
        self.consent, self.sender, self.snapshot, self.version = consent, sender, snapshot, version
        self.monotonic = monotonic
        self.lock = threading.RLock()
        self.next = 0
        self.running = False
        self.blocked = False
        self.closed = False
        self.cancelled = threading.Event()
        self.state = 'WAITING' if consent.enabled() else 'OFF'
        self.worker = None

    def enable(self):
        with self.lock:
            if self.closed:
                return
            self.consent.grant()
            self.blocked = False
            self.state = 'WAITING'

    def cancel(self):
        with self.lock:
            self.blocked = True
            self.cancelled.set()
            self.state = 'OFF'

    def disable(self):
        with self.lock:
            self.cancel()
            self.consent.revoke()

    def close(self):
        with self.lock:
            self.closed = True
            self.cancel()

    def status(self):
        with self.lock:
            enabled = not self.blocked and not self.closed and self.consent.enabled()
            if not enabled:
                self.cancelled.set()
                self.state = 'OFF'
            return dict(enabled=enabled, until=self.consent.until if enabled else 0, state=self.state)

    def tick(self):
        with self.lock:
            if not self.status()['enabled'] or self.running or self.monotonic() < self.next:
                return False
            self.cancelled = threading.Event()
            self.running = True
            self.state = 'SENDING'
            self.worker = threading.Thread(target=self._run, args=(self.cancelled,), name='fc-support-upload', daemon=True)
            try:
                self.worker.start()
            except RuntimeError:
                self.running = False
                self.state = 'UNAVAILABLE'
                self.next = self.monotonic() + 300
                return False
            return True

    def _run(self, cancellation):
        success = False
        result = 'UNAVAILABLE'
        def cancelled():
            return cancellation.is_set() or not self.consent.enabled()
        try:
            if cancelled():
                return
            report = SupportSnapshot.project(self.snapshot(), self.version, int(self.consent.clock() * 1000))
            if cancelled():
                return
            self.sender(report, cancelled=cancelled)
            success, result = True, 'STORED'
        except FriendsError as failure:
            result = {'rate_limited': 'RATE_LIMITED', 'access_rejected': 'AUTH_REJECTED', 'timeout': 'TIMEOUT', 'cancelled': 'OFF'}.get(str(failure), 'UNAVAILABLE')
        except Exception:
            result = 'UNAVAILABLE'
        finally:
            with self.lock:
                self.next = self.monotonic() + (60 if success else 300)
                self.running = False
                self.state = result if not cancelled() and self.status()['enabled'] else 'OFF'
