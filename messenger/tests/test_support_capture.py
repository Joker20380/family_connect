import json
import os
from pathlib import Path
import select
import socket
import subprocess
import sys
import threading
import time
from types import SimpleNamespace

import pytest

from control.capture_gate import Busy, CURRENT, GateError, initialize
from messenger.delivery import DeliveryController
from messenger.mailbox import ExchangeResult, MailboxError
from messenger.tests.test_support import queued, support
from provisioning import support_worker as worker


@pytest.fixture
def gated_support(support, tmp_path):
    owner, clients, snapshot = support
    owner.store.close()
    gate = initialize(tmp_path / 'capture')
    store = worker.SupportStore(tmp_path / 'support', b's' * 32, create=False, capture_gate=gate)
    owner = worker.SupportOwner(store, snapshot['sender_public'])
    owner.update(snapshot)
    yield owner, clients, snapshot
    store.close()


def pending(gate):
    return sorted((gate.directory / 'pending').iterdir())


def mailbox_for(owner, snapshot, tmp_path):
    path = tmp_path / 'bindings'
    path.write_text(json.dumps(snapshot))
    path.chmod(0o600)
    return worker.SupportMailbox(owner, path, None)


@pytest.mark.parametrize('operation', ['update', 'send', 'enqueue', 'invoke', 'outbox', 'ingest', 'dispatch', 'refresh', 'close'])
def test_closed_worker_gate_precedes_store_and_feed_work(gated_support, tmp_path, operation):
    owner, clients, snapshot = gated_support
    request, ident = queued(owner, clients[0])
    calls = {
        'update': lambda: owner.update(None),
        'send': lambda: owner.send(**request),
        'enqueue': lambda: owner.enqueue('bad', None, None, None, None),
        'invoke': lambda: owner.invoke(None),
        'outbox': owner.store.pending_outbox,
        'ingest': lambda: owner.notifications.ingest(None),
        'dispatch': owner.notifications.dispatch,
        'refresh': lambda: owner.notifications.refresh(tmp_path / 'missing'),
        'close': owner.store.close,
    }
    before = (tmp_path / 'support/history.sqlite').read_bytes()
    with owner.capture_gate.drain(.2):
        with pytest.raises(Busy):
            calls[operation]()
        assert (tmp_path / 'support/history.sqlite').read_bytes() == before
    assert not pending(owner.capture_gate)
    assert owner.send(**request)['id'] == ident


def test_main_and_store_refuse_before_opening_key_or_state(tmp_path):
    gate = initialize(tmp_path / 'capture')
    with gate.drain(.2):
        with pytest.raises(Busy):
            worker.SupportStore(tmp_path / 'unopened', b's' * 32, create=True, capture_gate=gate)
        with pytest.raises(Busy):
            worker.main(['--capture-gate', str(gate.directory), '--store', str(tmp_path / 'unopened'),
                '--key', str(tmp_path / 'missing-key'), '--sender-public', 'invalid', '--snapshot', 'missing',
                '--runtime', 'missing', '--socket', 'missing'])
    assert not (tmp_path / 'unopened').exists() and not pending(gate)


def test_replaced_worker_gate_cannot_fall_back_to_unprotected_exchange(gated_support, tmp_path, monkeypatch):
    owner, clients, snapshot = gated_support
    mailbox = mailbox_for(owner, snapshot, tmp_path)
    calls = []
    monkeypatch.setattr(mailbox, 'refresh', lambda: calls.append('unprotected'))
    lock = owner.capture_gate.directory / 'admission.lock'
    original = lock.with_suffix('.original')
    lock.rename(original)
    lock.touch(mode=0o600)
    try:
        with pytest.raises(MailboxError, match='unavailable'):
            mailbox.exchange()
        assert not calls and not pending(owner.capture_gate)
    finally:
        lock.unlink()
        original.rename(lock)


def test_send_commit_uses_one_worker_marker_and_preserves_queue(gated_support):
    owner, clients, snapshot = gated_support
    commits = []
    owner.store._db.set_trace_callback(lambda sql: commits.append(
        (CURRENT.get() is not None, len(pending(owner.capture_gate)))) if sql == 'COMMIT' else None)
    request, ident = queued(owner, clients[0])
    owner.store._db.set_trace_callback(None)
    assert commits and all(item == (True, 1) for item in commits)
    assert owner.send(**request)['id'] == ident and not pending(owner.capture_gate)
    with owner.capture_gate.drain(.2):
        assert owner.store.messages()[0]['status'] == 'queued'
    assert owner.store.pending_outbox() == [ident]


def test_real_ipc_refuses_before_refresh_or_scheduling(gated_support, tmp_path, monkeypatch):
    owner, clients, snapshot = gated_support
    mailbox = mailbox_for(owner, snapshot, tmp_path)
    calls = []
    monkeypatch.setattr(mailbox, 'refresh', lambda: calls.append('refresh'))
    delivery = SimpleNamespace(request_sync=lambda: calls.append('scheduled'))
    endpoint = tmp_path / 'worker.sock'
    with worker.SupportServer(endpoint, owner, mailbox, delivery) as server:
        server.timeout = 2
        thread = threading.Thread(target=server.handle_request)
        with owner.capture_gate.drain(.2):
            thread.start()
            try:
                with socket.socket(socket.AF_UNIX) as connection:
                    connection.settimeout(2)
                    connection.connect(str(endpoint))
                    connection.sendall(b'{"operation":"inbox","arguments":{}}\n')
                    with connection.makefile('rb') as stream:
                        assert json.loads(stream.readline()) == dict(ok=False, error='capture_busy')
            finally:
                thread.join(3)
        assert not thread.is_alive()
    assert calls == [] and not pending(owner.capture_gate)


def test_exchange_gate_remains_held_through_cleanup(gated_support, tmp_path, monkeypatch):
    owner, clients, snapshot = gated_support
    mailbox = mailbox_for(owner, snapshot, tmp_path)
    closing, release = threading.Event(), threading.Event()
    observed = []

    class Transport:
        def __init__(self, *args):
            assert CURRENT.get() is not None

        def exchange(self, **kwargs):
            return ExchangeResult(0, 0, 0, False)

        def close(self):
            closing.set()
            assert release.wait(3)
            observed.append(len(pending(owner.capture_gate)))

    monkeypatch.setattr(worker, 'SystemMailbox', Transport)
    results = []
    thread = threading.Thread(target=lambda: results.append(mailbox.exchange()))
    thread.start()
    try:
        assert closing.wait(3)
        with pytest.raises(Busy, match='DRAIN_TIMEOUT'):
            with owner.capture_gate.drain(.05):
                pytest.fail('cleanup still running')
    finally:
        release.set()
        thread.join(3)
    assert not thread.is_alive() and len(results) == 1 and observed == [1]
    assert not pending(owner.capture_gate)
    with owner.capture_gate.drain(.2):
        with pytest.raises(MailboxError, match='busy'):
            mailbox.exchange()


@pytest.mark.parametrize('phase', ['exchange', 'close'])
def test_failed_external_work_stays_pending_after_success(gated_support, tmp_path, monkeypatch, phase):
    owner, clients, snapshot = gated_support
    mailbox = mailbox_for(owner, snapshot, tmp_path)
    failed = [True]

    class Transport:
        def __init__(self, *args):
            pass

        def exchange(self, **kwargs):
            if failed[0] and phase == 'exchange':
                raise MailboxError('timeout')
            return ExchangeResult(0, 0, 0, False)

        def close(self):
            if failed[0] and phase == 'close':
                raise OSError('synthetic private cleanup detail')

    monkeypatch.setattr(worker, 'SystemMailbox', Transport)
    with pytest.raises((MailboxError, OSError)):
        mailbox.exchange()
    retained = pending(owner.capture_gate)
    assert len(retained) == 1 and b'private' not in retained[0].read_bytes()
    failed[0] = False
    mailbox.exchange()
    assert pending(owner.capture_gate) == retained
    with pytest.raises(GateError, match='UNSETTLED_OPERATION'):
        with owner.capture_gate.drain(.2):
            pytest.fail('retry is not settlement')


def test_periodic_and_mailbox_refusal_do_not_read_or_schedule(gated_support, tmp_path, monkeypatch):
    owner, clients, snapshot = gated_support
    mailbox = mailbox_for(owner, snapshot, tmp_path)
    calls = []
    monkeypatch.setattr(owner.notifications, 'refresh', lambda *args, **kwargs: calls.append('feed'))
    monkeypatch.setattr(mailbox, 'refresh', lambda: calls.append('bindings'))
    delivery = SimpleNamespace(request_sync=lambda: calls.append('scheduled'))
    with owner.capture_gate.drain(.2):
        assert worker.periodic(owner, delivery, tmp_path / 'missing', uid=os.getuid()) is False
        with pytest.raises(MailboxError, match='busy'):
            mailbox.exchange()
    assert calls == [] and not pending(owner.capture_gate)
    assert worker.periodic(owner, delivery, tmp_path / 'missing', uid=os.getuid()) is True
    assert calls == ['feed', 'scheduled']


def test_background_delivery_retries_after_admission_reopens(gated_support, tmp_path, monkeypatch):
    owner, clients, snapshot = gated_support
    mailbox = mailbox_for(owner, snapshot, tmp_path)
    exchanged = threading.Event()

    class Transport:
        def __init__(self, *args):
            assert CURRENT.get() is not None

        def exchange(self, **kwargs):
            exchanged.set()
            return ExchangeResult(0, 0, 0, False)

        def close(self):
            assert CURRENT.get() is not None

    monkeypatch.setattr(worker, 'SystemMailbox', Transport)
    delivery = DeliveryController(mailbox, cooldown=.02, max_backoff=.05, timeout=.1, max_retries=1)
    try:
        with owner.capture_gate.drain(.2):
            delivery.update(online=True, foreground=True)
            deadline = time.monotonic() + 3
            while delivery.snapshot()['error'] != 'busy' and time.monotonic() < deadline:
                time.sleep(.005)
            assert delivery.snapshot()['error'] == 'busy'
            assert not exchanged.is_set() and not pending(owner.capture_gate)
        delivery.request_sync()
        assert exchanged.wait(3)
    finally:
        assert delivery.close(timeout=3)
    assert not pending(owner.capture_gate)


def test_caught_notification_failure_retains_uncertainty(gated_support, tmp_path):
    owner, clients, snapshot = gated_support
    feed = tmp_path / 'feed'
    feed.write_text(json.dumps(dict(cursor=-1, anchor=None, schema=999)))
    feed.chmod(0o600)
    assert owner.notifications.refresh(feed, uid=os.getuid()) is None
    assert owner.notifications.error == 'source_unavailable'
    assert len(pending(owner.capture_gate)) == 1


def test_native_worker_death_leaves_pending(tmp_path):
    gate = initialize(tmp_path / 'capture')
    body = '''import sys,threading
from control.capture_gate import Gate
from provisioning import support_worker as worker
gate=Gate(sys.argv[1])
store=worker.SupportStore(sys.argv[2],b's'*32,create=True,capture_gate=gate)
with gate.operation():
    public=store.chat_identity().get_public_key().hex()
owner=worker.SupportOwner(store,public)
class Transport:
    def __init__(self,*args): pass
    def exchange(self,**kwargs):
        print('READY',flush=True)
        threading.Event().wait(30)
    def close(self): pass
worker.SystemMailbox=Transport
mailbox=worker.SupportMailbox(owner,None,None)
mailbox.refresh=lambda:dict(node={})
mailbox.exchange()
'''
    process = subprocess.Popen([sys.executable, '-B', '-c', body, str(gate.directory), str(tmp_path / 'synthetic-store')],
        cwd=Path(__file__).resolve().parents[2], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        assert select.select([process.stdout], [], [], 10)[0]
        assert process.stdout.readline() == b'READY\n'
        with pytest.raises(Busy, match='DRAIN_TIMEOUT'):
            with gate.drain(.05):
                pytest.fail('external worker still running')
        process.kill()
        process.wait(5)
        assert len(pending(gate)) == 1
        with pytest.raises(GateError, match='UNSETTLED_OPERATION'):
            with gate.drain(.2):
                pytest.fail('dead worker is not settled')
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(5)
        process.stdout.close()
        process.stderr.close()
