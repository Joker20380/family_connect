import json
import threading
import socket
import sqlite3
import time

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import Client
from django.urls import reverse
import pytest

from apps.console import inventory
from apps.console.models import AuditRecord
from tests.test_observability import snapshot as inventory_snapshot

pytest.importorskip('messenger', reason='Worker integration runs from source; the web image intentionally excludes it')

from messenger.tests.test_support import support
from messenger.tests.test_support_security import IdleDelivery
from provisioning.support_worker import SupportMailbox, SupportServer
from messenger.tests.conftest import chat_runtime


@pytest.fixture
def support_panel(console, support, settings, tmp_path):
    owner, clients, snapshot = support
    observed = inventory_snapshot()
    observed['devices'][0]['pseudonym'] = '1' * 64
    inventory.ingest(observed)
    path = tmp_path / 'lease.json'
    path.write_text(json.dumps(snapshot))
    path.chmod(0o600)
    endpoint = tmp_path / 'support.sock'
    settings.SUPPORT_SOCKET = str(endpoint)
    with SupportServer(endpoint, owner, SupportMailbox(owner, path, None), IdleDelivery()) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield owner, clients
        finally:
            server.shutdown()
            thread.join(5)


def page(client):
    return client.get(reverse('console:support_history', args=['1' * 64]))


@pytest.mark.parametrize('terminal', [None, 'superseded', 'expired'])
def test_canonical_notification_real_mailbox_ack_and_panel(console, support_panel, tmp_path, chat_runtime, terminal):
    from control.friends import paid_beta
    from control.friends.subscription_events import read
    from messenger.tests.test_offline import Peer
    from provisioning.chat_transport import SystemMailbox
    owner, clients = support_panel
    registry = tmp_path / 'canonical.db'
    database = sqlite3.connect(registry)
    database.executescript('CREATE TABLE devices(device TEXT PRIMARY KEY,revoked INTEGER);'
        'CREATE TABLE invites(device TEXT,revoked INTEGER);'
        'CREATE TABLE chat_bindings(device TEXT,public TEXT,support_sender TEXT);')
    device = '1'*32
    now = int(time.time())
    with database:
        database.execute('INSERT INTO devices VALUES (?,0)', (device,))
        database.execute('INSERT INTO invites VALUES (?,0)', (device,))
        database.execute('INSERT INTO chat_bindings VALUES (?,?,?)',
                         (device, clients[0].profile()['public'], owner.chat.public.hex()))
        paid_beta.migrate(database)
    def ingest():
        feed = read(registry, b'h'*32, **owner.notifications.cursor())
        for item in feed['subscriptions']:
            item['pseudonym'] = '1'*64
        owner.notifications.ingest(feed)
        owner.notifications.dispatch()
    ingest()
    with database:
        database.execute('INSERT INTO paid_beta_events VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',
            ('synthetic-payment-1', device, 'payment', now, None, 'active', now, now+3600,
             None, 'a'*64, 'b'*64, now, 'APPLIED'))
        database.execute('INSERT INTO paid_beta_subscriptions VALUES (?,?,?,?,?,?,?,?,?,?)',
            (device, 'active', now, now+3600, None, now, now, 1, 'synthetic-payment-1', None))
    before = registry.read_bytes()
    ingest()
    job = owner.notifications.jobs()[0]
    allowed = tmp_path / 'allowed.json'
    allowed.write_text(json.dumps([owner.chat.public.hex(), clients[0].profile()['public']]))
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        port = probe.getsockname()[1]
    node = Peer('budget-node', tmp_path / 'node', port, script='closed_peer.py', extra=[str(allowed)])
    lease = dict(host='127.0.0.1', port=port, public_key=node.info['public'], expires_at=now+119)
    carriers = [SystemMailbox(owner.chat, lease, chat_runtime), SystemMailbox(clients[0]._chat, lease, chat_runtime)]
    try:
        assert carriers[0].exchange(timeout=20).relayed == 1
        owner.notifications.dispatch()
        if terminal:
            job = owner.notifications.jobs()[0]
            job.update(status=terminal, reason=terminal)
            with owner.store._lock, owner.store._db:
                owner.notifications.save(job)
            assert not owner.notifications.allow(job['message_id'])
        assert carriers[1].exchange(timeout=20).received.stored == 1
        carriers[0].exchange(timeout=20)
        client = Client()
        client.force_login(console)
        response = page(client)
        assert response.status_code == 200
        text = response.content.decode()
        assert 'Автоматические уведомления подписки' in text
        assert 'Сохранено клиентом' in text and 'synthetic-payment-1' in text
        assert '#message-'+job['message_id'] in text
        card = client.get(reverse('console:inventory_device', args=['1'*64]))
        assert card.status_code == 200
        assert 'Сохранено клиентом' in card.content.decode()
        owner.notifications.dispatch()
        assert owner.notifications.jobs()[0]['status'] == (terminal or 'recipient_stored')
        assert owner.notifications.jobs()[0]['delivery_status'] == 'recipient_stored'
        if terminal:
            assert ('Замещено' if terminal == 'superseded' else 'Срок доставки истёк') in text
        assert not owner.notifications.allow(job['message_id'])
        owner.notifications.dispatch()
        assert not owner.store.pending_outbox()
        assert len(owner.store.visible_messages()) == 1
        assert not clients[1].history(owner.chat.address.hex())['messages']
        assert registry.read_bytes() == before
    finally:
        for carrier in carriers:
            carrier.close()
        node.close()
        database.close()


def test_authenticated_form_to_real_worker_and_encrypted_outbox(console, support_panel):
    owner, clients = support_panel
    client = Client(enforce_csrf_checks=True)
    client.force_login(console)
    response = page(client)
    assert response.status_code == 200
    assert response['Cache-Control'] == 'no-store'
    assert clients[0].profile()['address'] in response.content.decode()
    token = response.context['token']
    address = reverse('console:support_send', args=['1' * 64])
    assert client.get(address).status_code == 405
    assert client.post(address, dict(token=token, text='private synthetic text')).status_code == 403
    payload = dict(token=token, text='<script>synthetic private text</script>',
                   csrfmiddlewaretoken=client.cookies['csrftoken'].value)
    for _ in range(2):
        assert client.post(address, payload).status_code == 302
    history = owner.history('1' * 64)['messages']
    assert len(history) == 1 and history[0]['status'] == 'queued'
    response = page(client)
    assert '&lt;script&gt;' in response.content.decode()
    assert not owner.history('2' * 64)['messages']
    audit = json.dumps(list(AuditRecord.objects.filter(action__startswith='support.').values('action', 'target', 'details')))
    assert 'synthetic private text' not in audit
    assert history[0]['id'] in audit
    assert client.get(reverse('console:support_history', args=['3' * 64])).status_code == 404


def test_view_is_not_send_authority(console, support_panel):
    user = get_user_model().objects.create_user(username='support-reader', is_staff=True)
    user.user_permissions.add(Permission.objects.get(codename='view_support_messages'))
    client = Client()
    client.force_login(user)
    assert page(client).status_code == 200
    assert 'data-support-send' not in page(client).content.decode()
    assert client.post(reverse('console:support_send', args=['1' * 64]), dict(text='no')).status_code == 403
    assert support_panel[0].history('1' * 64)['messages'] == []


def test_signed_recipient_actor_limit_and_changed_binding(console, support_panel):
    owner, clients = support_panel
    client = Client()
    client.force_login(console)
    token = page(client).context['token']
    address = reverse('console:support_send', args=['1' * 64])
    assert client.post(address, dict(token=token+'invalid', text='no')).status_code == 400
    assert client.post(address, dict(token=token, text='я' * 2049)).status_code == 400
    second = get_user_model().objects.create_superuser(username='second-operator')
    client.force_login(second)
    assert client.post(address, dict(token=token, text='no')).status_code == 400
    client.force_login(console)
    with owner.store._lock, owner.store._db:
        threads = owner.store._get('support-threads')
        threads['1' * 64]['blocked'] = 'identity_changed'
        owner.store._put('support-threads', threads)
    assert client.post(address, dict(token=token, text='no')).status_code == 400
    assert owner.history('1' * 64)['messages'] == []
