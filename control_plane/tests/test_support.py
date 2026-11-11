import json
import threading

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
