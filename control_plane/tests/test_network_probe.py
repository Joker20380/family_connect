from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import DatabaseError, transaction
from django.utils import timezone
import pytest

from apps.console import backend, inventory, network_probe, probe_inventory
from apps.console.models import NetworkProbe, PaymentRecord, OperationRequest, InventorySnapshot, AuditRecord
from tests.test_observability import snapshot


def sample(source='nl-amsterdam-1', age=0, outcome='reachable'):
    address, port = network_probe.ENDPOINTS[source]
    return dict(schema=1, scope='production', source=source, probe='tcp_connect', vantage='operator-workstation',
        address=address, port=port, observed_at=(timezone.now().replace(microsecond=0) - timedelta(seconds=age)).isoformat(),
        outcome=outcome, duration_ms=12.5)


def test_strict_idempotent_append_only_import_without_product_mutations(console):
    before = backend.checked_path().read_bytes()
    data = sample()
    first = probe_inventory.ingest(data)
    assert probe_inventory.ingest(data).pk == first.pk
    assert NetworkProbe.objects.count() == 1
    assert AuditRecord.objects.filter(action='network_probe.import').count() == 1
    assert PaymentRecord.objects.count() == OperationRequest.objects.count() == InventorySnapshot.objects.count() == 0
    assert backend.checked_path().read_bytes() == before
    conflict = dict(data, outcome='timeout')
    with pytest.raises(inventory.SnapshotError):
        probe_inventory.ingest(conflict)
    for operation in (lambda: NetworkProbe.objects.filter(pk=first.pk).update(outcome='timeout'),
        lambda: NetworkProbe.objects.filter(pk=first.pk).delete()):
        with pytest.raises(DatabaseError), transaction.atomic():
            operation()


@pytest.mark.parametrize('change', [
    {'schema': True}, {'scope': 'synthetic'}, {'source': 'gateway-nl'}, {'source': ['nl-amsterdam-1']},
    {'source': 'nl-amsterdam-2'}, {'address': '127.0.0.1'}, {'port': 22}, {'port': 443.0},
    {'probe': 'vpn_ready'}, {'vantage': 'server'}, {'outcome': 'healthy'}, {'outcome': []},
    {'duration_ms': True}, {'duration_ms': float('nan')}, {'duration_ms': -1}, {'duration_ms': 60001},
    {'observed_at': 'no time'}, {'observed_at': '2026-11-03T10:00:00'}, {'private_key': 'never-store'},
])
def test_import_rejects_wrong_scope_binding_types_or_extra_data(db, change):
    data = sample()
    data.update(change)
    with pytest.raises(inventory.SnapshotError):
        probe_inventory.ingest(data)
    assert not NetworkProbe.objects.exists()


def test_import_rejects_duplicate_keys_and_missing_fields(db):
    with pytest.raises(inventory.SnapshotError):
        probe_inventory.ingest(inventory.strict_load(b'{"schema":1,"schema":1}'))
    data = sample()
    del data['port']
    with pytest.raises(inventory.SnapshotError):
        probe_inventory.ingest(data)


def test_live_cards_never_substitute_nodes_or_mix_scopes(console, client):
    data = snapshot()
    data.update(source='nl-amsterdam-1', registry_status='not_collected', devices=[])
    inventory.ingest(data)
    for age in (120, 60, 0):
        probe_inventory.ingest(sample(age=age))
    client.force_login(console)
    response = client.get('/observability/')
    assert response.status_code == 200
    cards = {card['source']: card for card in response.context['servers']}
    assert cards['nl-amsterdam-1']['network']['state'] == 'observe'
    assert cards['nl-amsterdam-2']['network']['state'] == 'no_data'
    assert cards['gateway-ru']['network']['state'] == 'no_data'
    assert 'VPN ещё не проверен' in response.content.decode()
    page = client.get('/servers/nl-amsterdam-1/')
    assert page.context['network']['state'] == 'observe'
    assert page.context['network']['automatic_action'] is False
    assert client.get('/servers/gateway-nl/').context['network'] is None
    assert client.get('/servers/nl-amsterdam-1/?source=nl-amsterdam-2').context['network'] is None
    assert client.get('/servers/nl-amsterdam-1/?scope=synthetic').context['network'] is None
    old = timezone.now().date() - timedelta(days=1)
    assert client.get(f'/servers/nl-amsterdam-1/?start={old}&end={old}').context['network']['state'] == 'no_data'
    assert not client.get('/observability/?scope=synthetic').context['servers']


def test_network_readback_requires_existing_inventory_permissions(console, client):
    assert client.get('/observability/').status_code == 302
    actor = get_user_model().objects.create_user(username='no-inventory', is_staff=True)
    client.force_login(actor)
    assert client.get('/observability/').status_code == 403
    assert client.get('/servers/nl-amsterdam-1/').status_code == 403
    actor.groups.add(Group.objects.get(name='Наблюдатели панели'))
    assert client.get('/observability/').status_code == 200
    assert client.get('/servers/nl-amsterdam-1/').status_code == 200
    assert client.post('/admin/console/networkprobe/add/', sample()).status_code == 404


def test_future_timestamp_never_looks_healthy(console, client):
    data = sample()
    data['observed_at'] = (timezone.now() + timedelta(seconds=30)).isoformat()
    probe_inventory.ingest(data)
    client.force_login(console)
    response = client.get('/servers/nl-amsterdam-1/')
    assert response.context['network']['state'] == 'hold'
