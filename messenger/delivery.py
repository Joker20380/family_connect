"""Foreground exchange worker: bounded batches/retries, no idle mailbox polling."""
import math
import threading
import time

from .mailbox import ExchangeResult, MailboxError


class DeliveryController:
    """One owner must forward lifecycle, queue changes and incoming-mail hints.

    Request exchange only after the outgoing message commits. This controller
    replaces SyncController for a bidirectional mailbox; never run both together.
    A successful close must precede closing the router, carrier and Store.
    """
    TRANSIENT = frozenset(('timeout', 'request_failed', 'link_failed', 'full', 'rate_limited', 'unavailable', 'busy'))
    ERRORS = TRANSIENT | frozenset(('cancelled', 'busy', 'access_denied', 'rejected',
                                   'invalid_response', 'invalid_list', 'invalid_batch',
                                   'invalid_ciphertext', 'unexpected_message', 'invalid_purge_response'))

    def __init__(self, mailbox, *, cooldown=4, max_backoff=300, timeout=12, max_retries=3):
        for value in (cooldown, max_backoff, timeout):
            if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
                raise ValueError('Positive finite delivery limits required')
        if max_backoff < cooldown or timeout > 30 or type(max_retries) is not int or not 0 <= max_retries <= 5:
            raise ValueError('Invalid delivery limits')
        self.mailbox = mailbox
        self.cooldown, self.max_backoff, self.timeout = cooldown, max_backoff, timeout
        self.max_retries = max_retries
        self._condition = threading.Condition()
        self._online = self._foreground = self._pending = self._closed = False
        self._generation = self._attempts = self._failures = 0
        self._next = 0
        self._cancel = self._result = self._error = None
        self._worker = threading.Thread(target=self._run, name='chat-delivery', daemon=True)
        self._worker.start()

    def update(self, *, online=None, foreground=None):
        if any(value is not None and type(value) is not bool for value in (online, foreground)):
            raise ValueError('Explicit lifecycle booleans required')
        with self._condition:
            if self._closed:
                return False
            changed = False
            for name, value in (('_online', online), ('_foreground', foreground)):
                if value is not None and value != getattr(self, name):
                    setattr(self, name, value)
                    changed = True
            if changed:
                self._generation += 1
                self._pending = True
                self._result = self._error = None
                if self._cancel is not None:
                    self._cancel.set()
                self._condition.notify_all()
            return changed

    def request_sync(self):
        """A committed queue item, explicit refresh or new-mail hint; coalesced."""
        with self._condition:
            if self._closed:
                return False
            self._pending = True
            # Events never reset cooldown/backoff or the consecutive failure count.
            self._condition.notify_all()
            return True

    def snapshot(self):
        with self._condition:
            return dict(online=self._online, foreground=self._foreground,
                        pending=self._pending, running=self._cancel is not None,
                        closed=self._closed, attempts=self._attempts,
                        failures=self._failures, result=self._result, error=self._error)

    def close(self, *, timeout=31):
        if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0 <= timeout <= 31:
            raise ValueError('Close timeout must be within [0,31] seconds')
        with self._condition:
            self._closed = True
            self._pending = False
            self._generation += 1
            self._result = self._error = None
            if self._cancel is not None:
                self._cancel.set()
            self._condition.notify_all()
        self._worker.join(timeout)
        return not self._worker.is_alive()

    def _run(self):
        while True:
            with self._condition:
                while True:
                    if self._closed:
                        return
                    if self._pending and self._online and self._foreground:
                        wait = self._next - time.monotonic()
                        if wait <= 0:
                            break
                        self._condition.wait(wait)
                    else:
                        self._condition.wait()
                self._pending = False
                cancel = self._cancel = threading.Event()
                generation = self._generation
                self._attempts += 1
            result = error = None
            try:
                result = self.mailbox.exchange(timeout=self.timeout, cancel=cancel)
                if not isinstance(result, ExchangeResult):
                    raise ValueError('Invalid exchange result')
            except MailboxError as failure:
                error = str(failure) if str(failure) in self.ERRORS else 'exchange_failed'
            except Exception:
                error = 'exchange_failed'  # No storage path/plaintext/traceback in UI state.
            with self._condition:
                self._cancel = None
                stale = self._generation != generation or cancel.is_set()
                if not stale:
                    self._result, self._error = result if error is None else None, error
                    self._failures = min(self._failures + 1, 16) if error else 0
                    if error in self.TRANSIENT and self._failures <= self.max_retries:
                        self._pending = True
                    elif error is None and result.more:
                        self._pending = True
                delay = min(self.max_backoff, self.cooldown * 2 ** max(0, self._failures - 1))
                self._next = time.monotonic() + delay
                self._condition.notify_all()
