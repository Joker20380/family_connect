import threading
import time
import pytest
from messenger.sync import SyncController
from messenger.mailbox import MailboxError,SyncResult


def wait_for(check):
    end=time.monotonic()+2
    while time.monotonic()<end:
        if check():return
        time.sleep(.005)
    assert check()


class Pull:
    def __init__(self):
        self.calls=0;self.started=threading.Event();self.release=threading.Event()
        self.failure=False
    def sync(self, *, timeout, cancel):
        self.calls+=1;self.started.set()
        while not self.release.wait(.005):
            if cancel.is_set():raise MailboxError('cancelled')
        if self.failure:raise OSError('private path or message must not escape')
        return SyncResult(1,0,0,1)


def test_events_coalesce_and_idle_never_polls():
    pull=Pull();sync=SyncController(pull,cooldown=.05,max_backoff=.2)
    try:
        sync.request_sync();sync.update(online=True)
        assert not pull.started.wait(.03) # Background cannot fetch.
        sync.update(foreground=True);assert pull.started.wait(1)
        for _ in range(100):sync.request_sync();sync.update(online=True,foreground=True)
        assert pull.calls==1
        pull.release.set()
        wait_for(lambda:pull.calls==2 and not sync.snapshot()['running'])
        time.sleep(.15);assert pull.calls==2 # No timer polling after completion.
    finally:assert sync.close()


def test_loss_resume_cancels_stale_result_and_keeps_one_followup():
    pull=Pull();sync=SyncController(pull,cooldown=.02,max_backoff=.1)
    try:
        sync.update(online=True,foreground=True);assert pull.started.wait(1)
        sync.update(online=False)
        wait_for(lambda:not sync.snapshot()['running'])
        assert sync.snapshot()['result'] is None and sync.snapshot()['error'] is None
        time.sleep(.04);assert pull.calls==1
        pull.release.set();sync.update(online=True)
        wait_for(lambda:sync.snapshot()['result'] is not None)
        assert pull.calls==2
    finally:assert sync.close()


def test_failure_requires_new_event_and_backoff_cannot_be_bypassed():
    pull=Pull();pull.release.set();pull.failure=True
    sync=SyncController(pull,cooldown=.08,max_backoff=.32)
    try:
        sync.update(online=True,foreground=True)
        wait_for(lambda:sync.snapshot()['error'] is not None)
        assert sync.snapshot()['error']=='sync_failed'
        time.sleep(.1);assert pull.calls==1
        sync.request_sync();wait_for(lambda:pull.calls==2 and not sync.snapshot()['running'])
        for _ in range(10):sync.update(online=False);sync.update(online=True);sync.request_sync()
        time.sleep(.05);assert pull.calls==2
        wait_for(lambda:pull.calls==3 and not sync.snapshot()['running'])
        time.sleep(.35);assert pull.calls==3
    finally:assert sync.close()


def test_close_cancels_worker_and_refuses_late_events():
    pull=Pull();sync=SyncController(pull,cooldown=.02,max_backoff=.1)
    sync.update(online=True,foreground=True);assert pull.started.wait(1)
    assert sync.close()
    assert not sync.request_sync() and not sync.update(online=False)
    assert sync.snapshot()['closed'] and sync.snapshot()['result'] is None


@pytest.mark.parametrize('kwargs',[{'timeout':31},{'cooldown':0},{'cooldown':float('nan')},{'max_backoff':1}])
def test_invalid_limits(kwargs):
    with pytest.raises(ValueError):SyncController(Pull(),**kwargs)


def test_real_reticulum_resume_delivers_without_duplicate_event_fetch(tmp_path):
    from messenger.tests.test_compact import setup_peers
    from messenger.codec import address
    peers,publics=setup_peers(tmp_path,'budget-node')
    node,alice,bob=peers
    try:
        ident=alice.call('queue',peer=address(publics[1]).hex(),text='resume delivery')
        assert alice.call('publish',id=ident) is True
        bob.call('lifecycle',online=True,foreground=False)
        time.sleep(.15)
        assert bob.call('sync_state')['attempts']==0
        assert node.call('stats')['count']==1
        bob.call('lifecycle',online=True,foreground=True)
        wait_for(lambda:bob.call('sync_state')['result'] is not None)
        assert bob.call('sync_state')['result']==dict(stored=1,duplicates=0,rejected=0,purged=1)
        assert any(m['id']==ident for m in bob.call('messages'))
        assert node.call('stats')['count']==0
        for _ in range(20):bob.call('lifecycle',online=True,foreground=True)
        time.sleep(.2)
        assert bob.call('sync_state')['attempts']==1
        assert bob.call('sync_close') is True
    finally:
        for peer in reversed(peers):peer.close()


def test_close_timeout_does_not_claim_storage_safe_or_accept_late_success():
    class SlowPull(Pull):
        def sync(self, **kwargs):
            self.started.set();self.release.wait(2)
            return SyncResult(1,0,0,1)
    pull=SlowPull();sync=SyncController(pull,cooldown=.02,max_backoff=.1)
    try:
        sync.update(online=True,foreground=True);assert pull.started.wait(1)
        assert sync.close(timeout=0) is False
        pull.release.set()
        assert sync.close() is True
        assert sync.snapshot()['result'] is None
    finally:
        pull.release.set();sync.close()
