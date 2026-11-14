import hashlib
import hmac
import json
import socket
import os
import threading
import time

import pytest
import RNS

from control.friends.chat import ChatAccess
from control.friends.subscription_events import read
from messenger.tests.test_support import support
from messenger.tests.test_offline import Peer
from provisioning.chat_transport import SystemMailbox
from provisioning.support_worker import SupportError, SupportOwner, SupportStore
from provisioning.subscription_notifications import Notifications
from tests.test_paid_beta import registry, event, activated_device, snapshot


@pytest.fixture
def route(registry, support):
    access, device, reference = registry
    owner, clients, bindings = support
    ChatAccess(access).initialize()
    second, second_reference = activated_device(access)
    for index, identity in enumerate((device, second)):
        public = clients[index].profile()['public']
        with access.db() as database:
            database.execute('INSERT INTO chat_bindings VALUES (?,?,?)',
                             (identity.reference, public, owner.chat.public.hex()))
        bindings['devices'][index].update(device=identity.reference,
            pseudonym=hmac.new(b'h' * 32, identity.reference.encode(), hashlib.sha256).hexdigest())
    with owner.store._lock, owner.store._db:
        owner.store._put('support-threads', {})
    bindings['sequence'] += 1
    owner.update(bindings)
    return registry, (access, second, second_reference), owner, clients, bindings


def cycle(route, *, now=None, dispatch=True, limit=128):
    registry, _, owner, _, _ = route
    now = int(time.time()) if now is None else now
    value = read(registry[0].path, b'h' * 32, **owner.notifications.cursor(), now=now, limit=limit)
    owner.notifications.ingest(value, now=now)
    if dispatch:
        owner.notifications.dispatch(now=now)
    return value


def pay(registry, ident='payment-0001', *, now=None, until=None):
    now = int(time.time()) if now is None else now
    return event(registry, event_id=ident, now=now, period_start=now-100, paid_until=until or now+3600)


def test_canonical_commit_pagination_equal_times_clock_reversal_and_replay(route):
    registry, second, owner, _, _ = route
    now = int(time.time())
    cycle(route, now=now)
    pay(registry, now=now)
    pay(registry, now=now)
    pay(registry, 'renewal-0001', now=now, until=now+7200)
    event(registry, 'grace', 'grace-00001', now=now-1, grace_until=now+9000)
    pay(second, 'payment-0002', now=now-2)
    before = snapshot(registry[0])
    for _ in range(4):
        cycle(route, now=now, limit=1)
    jobs = owner.notifications.jobs()
    assert len(jobs) == 4
    assert [job['source']['event_type'] for job in jobs] == ['payment', 'payment', 'grace', 'payment']
    assert 'Оплата учтена' in jobs[0]['text'] and 'продлён' in jobs[1]['text']
    assert len(owner.history(jobs[0]['pseudonym'])['messages']) == 3
    assert len(owner.history(jobs[-1]['pseudonym'])['messages']) == 1
    assert all(job['status'] == 'queued' for job in jobs)
    assert snapshot(registry[0]) == before
    with pytest.raises(Exception, match='EVENT_ID_CONFLICT'):
        pay(registry, 'payment-0001', now=now, until=now+8000)
    cursor = owner.notifications.cursor()
    with pytest.raises(ValueError, match='source_position_changed'):
        read(registry[0].path, b'h'*32, cursor['cursor'], '0'*64, now=now)


def test_atomic_job_and_cursor_rollback_then_restart(route, monkeypatch):
    registry, _, owner, _, _ = route
    cycle(route)
    pay(registry)
    previous = owner.notifications.cursor()
    original = owner.notifications.create
    def crash(*args, **kwargs):
        original(*args, **kwargs)
        raise RuntimeError('crash before cursor commit')
    monkeypatch.setattr(owner.notifications, 'create', crash)
    with pytest.raises(RuntimeError):
        cycle(route)
    assert owner.notifications.cursor() == previous and not owner.notifications.jobs()
    monkeypatch.setattr(owner.notifications, 'create', original)
    cycle(route, dispatch=False)
    owner.notifications = Notifications(owner)
    cycle(route)
    assert len(owner.notifications.jobs()) == len(owner.store.pending_outbox()) == 1


@pytest.mark.parametrize('after', [False, True])
def test_enqueue_crash_preserves_same_job_and_no_duplicate(route, monkeypatch, after):
    registry, _, owner, _, _ = route
    cycle(route)
    pay(registry)
    cycle(route, dispatch=False)
    job = owner.notifications.jobs()[0]
    original = owner.enqueue
    def crash(*args, **kwargs):
        if after:
            original(*args, **kwargs)
        raise RuntimeError('crash')
    monkeypatch.setattr(owner, 'enqueue', crash)
    with pytest.raises(RuntimeError):
        owner.notifications.dispatch()
    assert not owner.store.visible_messages()
    monkeypatch.setattr(owner, 'enqueue', original)
    cycle(route)
    cycle(route)
    assert owner.notifications.jobs()[0]['request_id'] == job['request_id']
    assert owner.notifications.jobs()[0]['text'] == job['text']
    assert len(owner.store.visible_messages()) == 1


def test_initial_baseline_excludes_old_events_and_expired_periods_atomically(route):
    registry, second, owner, _, _ = route
    now = int(time.time())
    pay(registry, now=now-20, until=now-10)
    pay(second, 'payment-0002', now=now, until=now+20)
    cycle(route, now=now)
    baseline = owner.store._get('subscription-baseline')
    assert baseline['excluded_events'] == 2 and baseline['status'] == 'baseline_excluded'
    assert not owner.store.visible_messages()
    assert [job['status'] for job in owner.notifications.jobs()] == ['baseline_excluded']
    owner.notifications = Notifications(owner)
    cycle(route, now=now+21)
    cycle(route, now=now+22)
    assert len(owner.store.visible_messages()) == 1
    assert owner.store._get('subscription-baseline') == baseline
    pay(registry, 'renewal-new', now=now+22)
    cycle(route, now=now+22)
    assert len(owner.store.visible_messages()) == 2


def test_baseline_crash_is_atomic_and_new_explicit_expire_is_not_historical(route, monkeypatch):
    registry, _, owner, _, _ = route
    now = int(time.time())
    pay(registry, now=now-20, until=now-10)
    original = owner.notifications.create
    def crash(*args, **kwargs):
        original(*args, **kwargs)
        raise RuntimeError('initialization crash')
    monkeypatch.setattr(owner.notifications, 'create', crash)
    with pytest.raises(RuntimeError):
        cycle(route, now=now)
    assert owner.store._get('subscription-baseline') is None
    assert owner.notifications.cursor()['cursor'] == -1 and not owner.notifications.jobs()
    monkeypatch.setattr(owner.notifications, 'create', original)
    cycle(route, now=now)
    event(registry, 'expire', 'new-expire-001', now=now+1)
    cycle(route, now=now+1)
    assert [job['status'] for job in owner.notifications.jobs()] == ['baseline_excluded', 'queued']


@pytest.mark.parametrize('grace', [False, True])
def test_natural_end_explicit_expire_dedup_and_renewal_before_enqueue(route, grace):
    registry, _, owner, _, _ = route
    now = int(time.time())
    pay(registry, now=now, until=now+2)
    if grace:
        event(registry, 'grace', 'grace-0001', now=now, grace_until=now+3)
    cycle(route, now=now)
    cycle(route, now=now+4, dispatch=False)
    job = owner.notifications.jobs()[0]
    assert job['source']['kind'] == 'deadline'
    pay(registry, 'renewal-0001', now=now+4)
    cycle(route, now=now+4)
    assert owner.notifications.jobs()[0]['status'] == 'superseded'
    assert len(owner.store.visible_messages()) == 1
    event(registry, 'expire', 'expire-0001', now=now+5)
    cycle(route, now=now+5)
    assert len(owner.store.visible_messages()) == 2
    cycle(route, now=now+6)
    assert len(owner.store.visible_messages()) == 2


@pytest.mark.parametrize('grace', [False, True])
def test_explicit_expire_after_natural_end_has_one_notification(route, grace):
    registry, _, owner, _, _ = route
    now = int(time.time())
    pay(registry, now=now, until=now+1)
    if grace:
        event(registry, 'grace', 'grace-0001', now=now, grace_until=now+2)
    cycle(route, now=now)
    cycle(route, now=now+3)
    cycle(route, now=now+4)
    event(registry, 'expire', 'expire-0001', now=now+3)
    cycle(route, now=now+5)
    assert len(owner.notifications.jobs()) == len(owner.store.visible_messages()) == 1
    assert owner.notifications.jobs()[0]['events'] == ['expire-0001']


@pytest.mark.parametrize('change,reason', [('missing', 'identity_missing_at_capture'),
    ('enrollment', 'support_not_enrolled'), ('revoked', 'revoked'), ('changed', 'identity_changed'),
    ('expired', 'binding_expired')])
def test_binding_failures_do_not_redirect_old_jobs(route, change, reason):
    registry, _, owner, clients, binding = route
    cycle(route)
    pay(registry)
    if change in ('missing', 'enrollment'):
        with registry[0].db() as database:
            if change == 'missing':
                database.execute('DELETE FROM chat_bindings WHERE device=?', (registry[1].reference,))
            else:
                database.execute('UPDATE chat_bindings SET support_sender=NULL')
    cycle(route, dispatch=False)
    if change == 'changed':
        with registry[0].db() as database:
            database.execute('UPDATE chat_bindings SET public=? WHERE device=?',
                             (RNS.Identity().get_public_key().hex(), registry[1].reference))
    elif change == 'revoked':
        with registry[0].db() as database:
            database.execute('UPDATE devices SET revoked=1')
    elif change == 'expired':
        with owner.store._lock, owner.store._db:
            binding['expires_at'] = 0
            owner.store._put('support-bindings', binding)
    cycle(route)
    assert owner.notifications.jobs()[0]['reason'] == reason
    assert not owner.store.visible_messages()
    if change == 'missing':
        with registry[0].db() as database:
            database.execute('INSERT INTO chat_bindings VALUES (?,?,?)',
                (registry[1].reference, clients[0].profile()['public'], owner.chat.public.hex()))
        cycle(route)
        assert owner.notifications.jobs()[0]['reason'] == reason


def test_quota_ttl_late_payment_and_no_idle_state_writes(route, monkeypatch):
    registry, _, owner, _, _ = route
    now = int(time.time())
    cycle(route, now=now)
    pay(registry, now=now-100, until=now-1)
    cycle(route, now=now, dispatch=False)
    def full(*args, **kwargs):
        raise SupportError('history_full')
    monkeypatch.setattr(owner, 'enqueue', full)
    owner.notifications.dispatch(now=now)
    assert owner.notifications.jobs()[0]['reason'] == 'history_full'
    cycle(route, now=now+1)
    changes = owner.store._db.total_changes
    cycle(route, now=now+1)
    assert owner.store._db.total_changes == changes
    cycle(route, now=now+8*86400)
    assert all(job['status'] == 'expired' for job in owner.notifications.jobs())
    assert 'сейчас активна' not in owner.notifications.jobs()[0]['text']


def test_service_source_cannot_be_forged_by_panel_send(route):
    _, _, owner, clients, _ = route
    with pytest.raises(SupportError, match='invalid_request'):
        owner.invoke(dict(operation='enqueue', arguments={}))
    with pytest.raises(SupportError, match='invalid_message'):
        owner.send('1'*64, clients[0].profile()['address'], '12345678-1234-1234-1234-123456789012',
                   dict(service='subscription-notifications-v1'), 'forged')


def test_committed_enqueue_unknown_result_keeps_source_request_and_bytes(route):
    registry, _, owner, _, _ = route
    cycle(route)
    pay(registry)
    cycle(route)
    job = owner.notifications.jobs()[0]
    saved = owner.store._get('support-request:' + job['request_id'])
    assert saved['request']['source']['service'] == 'subscription-notifications-v1'
    assert 'actor' not in saved['request']
    packed = owner.store._get('message:' + job['message_id'])['packed']
    owner.notifications = Notifications(owner)
    for _ in range(3):
        cycle(route)
    assert owner.store._get('message:' + job['message_id'])['packed'] == packed
    assert len(owner.store.visible_messages()) == 1


def test_lost_readonly_ipc_response_does_not_reinitialize_baseline(route, tmp_path):
    from provisioning.support_worker import SupportServer, SupportMailbox
    from messenger.tests.test_support_security import IdleDelivery
    from provisioning.subscription_collector import command
    registry, _, owner, _, bindings = route
    cycle(route)
    pay(registry)
    cycle(route)
    baseline = owner.store._get('subscription-baseline')
    path = tmp_path / 'binding.json'
    path.write_text(json.dumps(bindings))
    path.chmod(0o600)
    endpoint = tmp_path / 'worker.sock'
    with SupportServer(endpoint, owner, SupportMailbox(owner, path, None), IdleDelivery()) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
                connection.connect(str(endpoint))
                connection.sendall(b'{"operation":"notification_cursor","arguments":{}}\n')
            first = command(endpoint)
            assert command(endpoint) == first
            assert first.startswith('subscription-notifications 1 ')
            assert owner.store._get('subscription-baseline') == baseline
            assert len(owner.store.visible_messages()) == 1
        finally:
            server.shutdown()
            thread.join(5)


def test_private_feed_missing_expired_or_mutable_is_fail_closed(route, tmp_path):
    registry, _, owner, _, _ = route
    cycle(route)
    pay(registry)
    feed = read(registry[0].path, b'h'*32, **owner.notifications.cursor())
    path = tmp_path / 'feed.json'
    path.write_text(json.dumps(feed))
    path.chmod(0o644)
    cursor = owner.notifications.cursor()
    owner.notifications.refresh(path, uid=os.getuid())
    assert owner.notifications.error == 'source_unavailable'
    assert owner.notifications.cursor() == cursor
    path.chmod(0o600)
    owner.notifications.refresh(path, uid=os.getuid())
    assert len(owner.store.pending_outbox()) == 1
    path.unlink()
    owner.notifications.refresh(path, uid=os.getuid())
    assert not owner.store.pending_outbox()
    assert len(owner.notifications.jobs()) == 1


def test_uncommitted_event_invisible_and_more_than_thousand_events_retained(route):
    registry, _, owner, _, _ = route
    now = int(time.time())
    cycle(route, now=now)
    from control.friends import paid_beta
    with pytest.raises(RuntimeError):
        with paid_beta.connection(registry[0].path, write=True) as database:
            paid_beta.apply_event(database, registry[2], 'payment', 'uncommitted-1', 'synthetic',
                now=now, period_start=now-100, paid_until=now+3600, apk_sha256=paid_beta.PAID_ANDROID_APK_SHA256)
            assert not read(registry[0].path, b'h'*32, **owner.notifications.cursor(), now=now)['events']
            raise RuntimeError('rollback')
    with paid_beta.connection(registry[0].path, write=True) as database:
        for index in range(1005):
            paid_beta.apply_event(database, registry[2], 'payment', f'bulk-payment-{index:05}', 'synthetic',
                now=now, period_start=now-100, paid_until=now+3600+index, apk_sha256=paid_beta.PAID_ANDROID_APK_SHA256)
    while owner.notifications.cursor()['cursor'] != 1005:
        cycle(route, now=now, dispatch=False)
    assert len(owner.notifications.jobs()) == 1005
    assert not owner.store.visible_messages()


def test_revocation_event_and_grace_supersede_waiting_deadline(route):
    registry, _, owner, _, _ = route
    now = int(time.time())
    pay(registry, now=now, until=now+1)
    cycle(route, now=now)
    cycle(route, now=now+2, dispatch=False)
    event(registry, 'grace', 'grace-0001', now=now+2, grace_until=now+3600)
    cycle(route, now=now+2)
    assert owner.notifications.jobs()[0]['status'] == 'superseded'
    event(registry, 'revoke', 'revoke-0001', now=now+3)
    cycle(route, now=now+3)
    assert len(owner.store.visible_messages()) == 2
    assert 'Доступ отозван' in owner.notifications.jobs()[-1]['text']


def test_real_mailbox_isolated_route_restart_offline_ack_and_no_chat_entitlement(route, tmp_path, chat_runtime):
    registry, second, owner, clients, bindings = route
    cycle(route)
    pay(registry)
    pay(second, 'payment-0002')
    cycle(route)
    before = snapshot(registry[0])
    jobs = owner.notifications.jobs()
    keys = [job['request_id'] for job in jobs]
    root = tmp_path / 'support'
    owner.store.close()
    store = SupportStore(root, b's'*32, create=False)
    try:
        owner = SupportOwner(store, bindings['sender_public'])
        route = (registry, second, owner, clients, bindings)
        cycle(route)
        assert [job['request_id'] for job in owner.notifications.jobs()] == keys
        allowed = tmp_path / 'allowed.json'
        allowed.write_text(json.dumps([owner.chat.public.hex()] + [client.profile()['public'] for client in clients]))
        with socket.socket() as probe:
            probe.bind(('127.0.0.1', 0))
            port = probe.getsockname()[1]
        node = Peer('budget-node', tmp_path / 'node', port, script='closed_peer.py', extra=[str(allowed)])
        lease = dict(host='127.0.0.1', port=port, public_key=node.info['public'], expires_at=int(time.time())+119)
        carriers = [SystemMailbox(owner.chat, lease, chat_runtime)] + [SystemMailbox(client._chat, lease, chat_runtime) for client in clients]
        try:
            assert carriers[0].exchange(timeout=20).relayed == 2
            assert carriers[2].exchange(timeout=20).received.stored == 1
            assert not clients[0].history(owner.chat.address.hex())['messages']
            assert carriers[1].exchange(timeout=20).received.stored == 1
            carriers[0].exchange(timeout=20)
            owner.notifications.dispatch()
            assert all(job['status'] == 'recipient_stored' for job in owner.notifications.jobs())
            assert all(len(client.history(owner.chat.address.hex())['messages']) == 1 for client in clients)
            clients[0].queue(owner.chat.address.hex(), 'Оплата учтена, продлите VPN')
            carriers[1].exchange(timeout=20)
            carriers[0].exchange(timeout=20)
            assert snapshot(registry[0]) == before
        finally:
            for carrier in carriers:
                carrier.close()
            node.close()
    finally:
        store.close()
