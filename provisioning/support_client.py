"""GTK projection of support state; only the session service owns consent and uploads."""
import threading

from messenger.local import LocalError
from .chat_client import ChatClient


class SupportClient:
    STATES = frozenset(('OFF', 'WAITING', 'SENDING', 'STORED', 'RATE_LIMITED', 'AUTH_REJECTED', 'TIMEOUT', 'UNAVAILABLE'))

    def __init__(self, *, client=None):
        self.client = client or ChatClient()
        self.lock = threading.RLock()
        self.current = dict(enabled=False, until=0, state='UNAVAILABLE', available=False, background=True,
                            storage_error=False, revision='')
        self.closed = self.polling = self.mutating = False
        self.epoch = 0
        self.worker = None

    @classmethod
    def validate(cls, value):
        import re
        if (type(value) is not dict or set(value) != {'enabled', 'until', 'state', 'revision', 'available', 'background', 'storage_error'} or
                any(type(value[name]) is not bool for name in ('enabled', 'available', 'background', 'storage_error')) or
                value['background'] is not True or type(value['until']) is not int or not 0 <= value['until'] <= 2**53-1 or
                type(value['revision']) is not str or not re.fullmatch('[a-f0-9]{32}', value['revision']) or
                type(value['state']) is not str or value['state'] not in cls.STATES or
                (value['enabled'] and (not value['available'] or not value['until'])) or
                (not value['enabled'] and value['until'] != 0)):
            raise LocalError('support_unavailable')
        return dict(value)

    def status(self):
        with self.lock:
            return dict(self.current)

    def _read(self, epoch):
        try:
            state = self.validate(self.client.request('support_status', {}))
        except Exception:
            state = None
        with self.lock:
            self.polling = False
            if self.closed or epoch != self.epoch:
                return
            if state is not None:
                self.current = state
            else:
                self.current = dict(self.current, state='UNAVAILABLE', available=False)

    def tick(self):
        with self.lock:
            if self.closed or self.polling or self.mutating:
                return False
            self.polling = True
            self.worker = threading.Thread(target=self._read, args=(self.epoch,), name='fc-support-status', daemon=True)
            try:self.worker.start()
            except RuntimeError:
                self.polling = False
                self.current = dict(self.current, state='UNAVAILABLE', available=False)
                return False
            return True

    def cancel(self):
        with self.lock:
            self.epoch += 1

    def _change(self, enabled):
        with self.lock:
            if self.closed or self.mutating or not self.current['available']:
                raise LocalError('support_unavailable')
            self.epoch += 1
            epoch, revision = self.epoch, self.current['revision']
            self.mutating = True
        try:
            state = self.validate(self.client.request('support_consent', dict(enabled=enabled, revision=revision)))
            with self.lock:
                if not self.closed and epoch == self.epoch:
                    self.current = state
        except Exception:
            with self.lock:
                if not self.closed and epoch == self.epoch:
                    self.current = dict(self.current, state='UNAVAILABLE', available=False)
            raise
        finally:
            with self.lock:
                self.mutating = False

    def enable(self):
        self._change(True)

    def disable(self):
        self._change(False)

    def close(self):
        with self.lock:
            self.closed = True
            self.epoch += 1
            self.client.closed = True
            connection = self.client.connection
        if connection is not None:
            try:connection.close(None, None)
            except Exception:pass
