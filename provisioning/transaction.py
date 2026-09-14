"""Carrier-neutral durable apply/health/commit/rollback and ACK outbox.

Only the application boundary mutates VPN state. Its apply/rollback must be
idempotent and serialized with other local connection operations. Crash recovery
always rolls an unfinished application back, never guesses that health succeeded.
"""
import base64
from contextlib import nullcontext
import functools
import hashlib
import json
import logging
import os

from . import ack
from .cache import ProvisioningCache
from .configuration import ConfigError
from .envelope import _unique_fields, ProvisioningRejected

LOG = logging.getLogger('family_connect.control')
MAX_STATE_BYTES = 1024 * 1024


class ControlJournal(ProvisioningCache):
    @staticmethod
    def _write(directory, record):
        if len(json.dumps(record, separators=(',', ':')).encode()) > MAX_STATE_BYTES:
            raise ProvisioningRejected('control journal too large')
        ProvisioningCache._write(directory, record)

    def initialize(self):
        self.path.mkdir(mode=0o700)
        with self._locked() as directory:
            self._write(directory, dict(schema=1, committed=None, staged=None, phase='IDLE',
                baseline=None, floor=0, last_now=0, outbox=[], result=None))

    def read(self, directory):
        fd = os.open('cache.json', os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        try:
            self._safe(fd)
            raw = os.read(fd, MAX_STATE_BYTES + 1)
            if len(raw) > MAX_STATE_BYTES:
                raise ValueError()
            record = json.loads(raw, object_pairs_hook=_unique_fields)
            if (type(record) is not dict or set(record) != {'schema', 'committed', 'staged', 'phase',
                    'baseline', 'floor', 'last_now', 'outbox', 'result'} or record['schema'] != 1 or
                    type(record['floor']) is not int or not 0 <= record['floor'] < 2**63 or
                    type(record['last_now']) is not int or record['last_now'] < 0 or
                    record['phase'] not in {'IDLE', 'STAGED', 'APPLYING', 'APPLIED_PENDING', 'ROLLING_BACK'} or
                    (record['phase'] == 'IDLE') != (record['staged'] is None) or
                    type(record['outbox']) is not list or len(record['outbox']) > 64):
                raise ValueError()
            for name in ('committed', 'staged'):
                entry = record[name]
                if entry is not None:
                    verified = self.unpack(entry, historical=True)
                    if verified.state.revision > record['floor'] or entry['at'] > record['last_now']:
                        raise ValueError()
            for raw_ack in record['outbox']:
                body = ack.verify(base64.b64decode(raw_ack, validate=True))
                if body['device'] != self.verifier.device.reference:
                    raise ValueError()
            if record['result'] is not None:
                body = ack.verify(base64.b64decode(record['result'], validate=True))
                if body['device'] != self.verifier.device.reference or body['sequence'] > record['floor']:
                    raise ValueError()
            return record
        except (ValueError, TypeError, KeyError, UnicodeError, RecursionError):
            raise ProvisioningRejected('invalid control journal') from None
        finally:
            os.close(fd)

    def unpack(self, entry, *, historical=False, now=None):
        if type(entry) is not dict or set(entry) != {'envelope', 'at', 'digest', 'applied_at', 'runtime'}:
            raise ValueError('invalid journal configuration')
        verified = self.verifier.verify(base64.b64decode(entry['envelope'], validate=True),
            now=entry['at'] if historical else now)
        if (verified.digest != entry['digest'] or type(entry['at']) is not int or
                (entry['applied_at'] is not None and (type(entry['applied_at']) is not int or entry['applied_at'] < entry['at']))):
            raise ValueError('journal hash mismatch')
        return verified

    @staticmethod
    def pack(verified, now):
        return dict(envelope=base64.b64encode(verified.envelope).decode(), at=now, digest=verified.digest, applied_at=None, runtime=None)


def application_transaction(method):
    @functools.wraps(method)
    def call(self,*args,**kwargs):
        transaction=getattr(self.application,'transaction',None)
        with transaction(self.journal) if transaction else nullcontext():
            return method(self,*args,**kwargs)
    return call


class ProvisioningCore:
    def __init__(self, *, journal, application, device, clock):
        self.journal, self.application, self.device, self.clock = journal, application, device, clock

    def event(self, event, record=None, *, error='NONE', verified=None, receipt=None):
        state = verified.state if verified else None
        LOG.info(event, extra=dict(control_event=event, config_id=state.config_id if state else (receipt or {}).get('config_id'),
            sequence=state.revision if state else (receipt or {}).get('sequence'), state=record['phase'] if record else None,
            error_category=error))

    def _time(self, record):
        now = self.clock()
        if type(now) is not int or now < record['last_now']:
            raise ConfigError('CLOCK')
        record['last_now'] = now
        return now

    def _ack(self, record, *, digest, verified=None, status, error='NONE', now, final=False):
        for existing in record['outbox']:
            body = ack.verify(base64.b64decode(existing))
            if body['envelope_hash'] == digest and body['status'] == status and body['error'] == error:
                if final:
                    record['result'] = existing
                return status
        raw = ack.create(self.device, digest=digest,
            config_id=verified.state.config_id if verified else None,
            sequence=verified.state.revision if verified else 0, status=status, error=error, now=now)
        encoded = base64.b64encode(raw).decode()
        if encoded not in record['outbox']:
            if len(record['outbox']) >= 64:
                raise ProvisioningRejected('ACK outbox full')
            record['outbox'].append(encoded)
        if final:
            record['result'] = encoded
        return status

    def _rollback(self, directory, record, *, error):
        now = self._time(record)
        staged = self.journal.unpack(record['staged'], historical=True)
        record['phase'] = 'ROLLING_BACK'
        self.journal._write(directory, record)
        self.event('control.config.rollback', record, error=error, verified=staged)
        try:
            # An expired last-known-good is retained for evidence but cannot
            # authorize a new connection. Application still cleans the candidate.
            previous = None
            baseline = record['baseline']
            if record['committed'] is not None:
                try:
                    previous = self.journal.unpack(record['committed'], now=now)
                except ConfigError:
                    # Cleanup still runs, but an expired lease cannot reconnect.
                    baseline = {**baseline, 'expired_active': baseline['active'], 'active': []}
            self.application.rollback(staged, previous, baseline)
        except Exception:
            # Leave durable ROLLING_BACK intent. Retry before any future delivery.
            self._ack(record, digest=staged.digest, verified=staged,
                status='FAILED', error='ROLLBACK', now=now)
            self.journal._write(directory, record)
            return 'FAILED'
        record['phase'], record['staged'], record['baseline'] = 'IDLE', None, None
        self._ack(record, digest=staged.digest, verified=staged,
            status='ROLLED_BACK', error=error, now=now, final=True)
        self.journal._write(directory, record)
        return 'ROLLED_BACK'

    @application_transaction
    def recover(self):
        with self.journal._locked() as directory:
            record = self.journal.read(directory)
            self._time(record)
            if record['staged'] is not None:
                return self._rollback(directory, record, error='RECOVERY')
            self.journal._write(directory, record)
            return 'IDLE'

    @application_transaction
    def receive(self, raw):
        # Use the wire hash for rejected messages; never echo unverified fields.
        if type(raw) is not bytes:
            raise ConfigError('SIZE')
        digest = hashlib.sha256(raw).hexdigest()
        with self.journal._locked() as directory:
            record = self.journal.read(directory)
            if record['staged'] is not None:
                self._rollback(directory, record, error='RECOVERY')
                if record['staged'] is not None:
                    return 'FAILED'
            now = self._time(record)
            # Reserve space for all result events before any application mutation.
            if len(record['outbox']) > 58:
                raise ProvisioningRejected('ACK outbox requires delivery')
            self.event('control.message.received', record)
            try:
                verified = self.journal.verifier.verify(raw, now=now)
                # Exact previously committed/failed delivery returns its result;
                # validation still checks current signature/lease/client version.
                if record['result'] is not None:
                    result = ack.verify(base64.b64decode(record['result']))
                    if result['envelope_hash'] == digest:
                        if record['result'] not in record['outbox']:
                            record['outbox'].append(record['result'])
                        self.journal._write(directory, record)
                        return result['status']
                if record['committed'] is not None and record['committed']['digest'] == digest:
                    self._ack(record, digest=digest, verified=verified, status='COMMITTED', now=now)
                    self.journal._write(directory, record)
                    return 'COMMITTED'
                if verified.state.revision <= record['floor']:
                    raise ConfigError('REPLAY')
                previous_hash = record['committed']['digest'] if record['committed'] else None
                if verified.state.previous_config_hash != previous_hash:
                    raise ConfigError('PREVIOUS_HASH')
            except ConfigError as exc:
                self.event('control.config.rejected', record, error=exc.category)
                self._ack(record, digest=digest, status='REJECTED', error=exc.category, now=now)
                self.journal._write(directory, record)
                return 'REJECTED'
            self.event('control.config.verified', record, verified=verified)
            # Snapshot is read-only; failures here cannot mutate system state.
            baseline = self.application.snapshot(previous=record['committed']['runtime'] if record['committed'] else None)
            reserve=getattr(self.application,'reserve',None)
            if reserve is not None:reserve()
            record.update(staged=self.journal.pack(verified, now), baseline=baseline,
                phase='STAGED', floor=verified.state.revision)
            self._ack(record, digest=digest, verified=verified, status='RECEIVED', now=now)
            self.journal._write(directory, record)
            self.event('control.config.staged', record, verified=verified)
            record['phase'] = 'APPLYING'
            self.journal._write(directory, record)
            try:
                self.application.apply(verified, baseline)
            except Exception:
                return self._rollback(directory, record, error='APPLY')
            record['phase'] = 'APPLIED_PENDING'
            self._ack(record, digest=digest, verified=verified, status='APPLIED', now=self._time(record))
            self.journal._write(directory, record)
            self.event('control.config.applied', record, verified=verified)
            try:
                healthy = self.application.healthy(verified) is True
                self.journal.verifier.verify(raw, now=self._time(record))
            except Exception:
                healthy = False
            if not healthy:
                return self._rollback(directory, record, error='HEALTH')
            record['committed'] = {**record['staged'], 'applied_at': record['last_now'],
                'runtime': self.application.snapshot()}
            record.update(staged=None, baseline=None, phase='IDLE')
            self._ack(record, digest=digest, verified=verified, status='COMMITTED',
                now=record['last_now'], final=True)
            # Commit pointer and pending COMMITTED ACK share one atomic replace.
            self.journal._write(directory, record)
            self.event('control.config.committed', record, verified=verified)
            return 'COMMITTED'

    def flush_acks(self, carrier):
        with self.journal._locked() as directory:
            record = self.journal.read(directory)
            while record['outbox']:
                raw = base64.b64decode(record['outbox'][0])
                try:
                    if carrier.send_ack(raw) is not True:
                        raise OSError()
                except Exception:
                    self.event('control.ack.retry', record, receipt=ack.verify(raw))
                    return False
                record['outbox'].pop(0)
                self.journal._write(directory, record)
                self.event('control.ack.sent', record, receipt=ack.verify(raw))
            return True

    def refresh(self, carrier):
        self.flush_acks(carrier)
        self.recover()
        self.event('control.channel.started')
        # Network errors happen outside state mutation and application calls.
        result = self.receive(carrier.receive())
        self.flush_acks(carrier)
        return result
