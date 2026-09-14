"""Event-driven, foreground-only mailbox pulls; no periodic empty polling."""
import math
import threading
import time

from .mailbox import MailboxError


class SyncController:
    """One worker, one coalesced pending event, bounded mailbox operations.

    Native bindings must forward connectivity/lifecycle changes and close before
    closing Store. Failed pulls do not retry without another event. A pending
    event can wait for cooldown, but completion alone never schedules another pull.
    """
    def __init__(self, mailbox, *, cooldown=30, max_backoff=300, timeout=12):
        for value in (cooldown,max_backoff,timeout):
            if type(value) not in (int,float) or not math.isfinite(value) or value<=0:
                raise ValueError('Positive finite sync limits required')
        if max_backoff<cooldown or timeout>30:raise ValueError('Invalid sync limits')
        self.mailbox=mailbox
        self.cooldown,self.max_backoff,self.timeout=cooldown,max_backoff,timeout
        self._condition=threading.Condition()
        self._online=self._foreground=self._pending=self._closed=False
        self._cancel=None
        self._generation=0
        self._next=0
        self._failures=0
        self._result=self._error=None
        self._attempts=0
        self._worker=threading.Thread(target=self._run,name='mailbox-sync',daemon=True)
        self._worker.start()

    def update(self, *, online=None, foreground=None):
        if any(x is not None and type(x) is not bool for x in (online,foreground)):
            raise ValueError('Explicit lifecycle booleans required')
        with self._condition:
            if self._closed:return False
            changed=False
            for name,value in (('_online',online),('_foreground',foreground)):
                if value is not None and value!=getattr(self,name):
                    setattr(self,name,value);changed=True
            if changed:
                self._generation+=1
                self._pending=True
                self._result=self._error=None
                if self._cancel is not None:self._cancel.set()
                self._condition.notify_all()
            return changed

    def request_sync(self):
        """Explicit refresh, new-mail hint or network replacement; coalesced."""
        with self._condition:
            if self._closed:return False
            self._pending=True
            self._condition.notify_all()
            return True

    def snapshot(self):
        with self._condition:
            return dict(online=self._online,foreground=self._foreground,
                pending=self._pending,running=self._cancel is not None,
                closed=self._closed,attempts=self._attempts,
                result=self._result,error=self._error)

    def close(self, *, timeout=31):
        """Cancel and join; False means caller must keep Store alive and rejoin."""
        with self._condition:
            self._closed=True;self._pending=False;self._generation+=1
            self._result=self._error=None
            if self._cancel is not None:self._cancel.set()
            self._condition.notify_all()
        self._worker.join(timeout)
        return not self._worker.is_alive()

    def _run(self):
        while True:
            with self._condition:
                while True:
                    if self._closed:return
                    if self._pending and self._online and self._foreground:
                        wait=self._next-time.monotonic()
                        if wait<=0:break
                        self._condition.wait(wait)
                    else:self._condition.wait()
                self._pending=False
                cancel=self._cancel=threading.Event()
                generation=self._generation
                self._attempts+=1
            result=error=None
            try:result=self.mailbox.sync(timeout=self.timeout,cancel=cancel)
            except MailboxError as exc:
                code=str(exc)
                error=code if code in ('cancelled','timeout','busy','access_denied','request_failed','link_failed') else 'sync_failed'
            except Exception:error='sync_failed' # Never expose plaintext/storage paths.
            with self._condition:
                self._cancel=None
                stale=generation!=self._generation or cancel.is_set()
                if not stale:
                    self._result,self._error=result,error
                    self._failures=min(self._failures+1,16) if error else 0
                delay=min(self.max_backoff,self.cooldown*2**max(0,self._failures-1))
                self._next=time.monotonic()+delay
                self._condition.notify_all()
