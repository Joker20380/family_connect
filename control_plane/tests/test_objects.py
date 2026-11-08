from copy import deepcopy
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import DatabaseError, transaction
from django.utils import timezone
import pytest

from apps.console import inventory, measurements, objects, subscriptions, transports
from apps.console.models import (DeviceLabel, DeviceProjection, MeasurementSnapshot,
    SubscriptionEventObservation, SubscriptionSnapshot)
from tests.test_observability import snapshot
from tests.test_subscriptions import observation


def metrics(source='gateway-ru'):
    return dict(schema=1, source=source, observed_at=int(timezone.now().timestamp()),
        node=dict(boot='a'*64, interface='eth0', ifindex=2, rx=100, tx=200, cpu_total=1000, cpu_idle=700, cpu_count=2),
        awg_status='ok', unknown_peers=1, tcp_status='not_collected', mesh_status='not_collected',
        devices=[dict(pseudonym='a'*64, rx=10, tx=20, epoch='b'*64+':4', last_handshake=None)])


def event_data():
    data = observation()
    data['devices'][0]['event'] = dict(event_id='f'*64, event_type='payment', occurred_at=data['observed_at'],
        previous_state=None, new_state='active', result='APPLIED')
    data.update(schema=2, history=dict(truncated=False,
        events=[dict(data['devices'][0]['event'], pseudonym='a'*64)]))
    return data


def test_join_full_hmac_not_prefix_and_bidirectional_links(console, client):
    data = snapshot()
    second = 'a'*12 + 'b'*52
    data['devices'].append(dict(data['devices'][0], pseudonym=second))
    inventory.ingest(data)
    inventory.ingest(dict(data, observed_at=(timezone.now()+timedelta(seconds=1)).isoformat()))
    subscriptions.ingest(event_data(), attempt=True)
    DeviceLabel.objects.create(pseudonym='a'*64, label='Семейный телефон')
    value = metrics(); measurements.ingest(value, value['source'])
    now = value['observed_at']
    transports.ingest(dict(schema=2, source='gateway-ru', observed_at=now, status='ok', runtime_sha256='c'*64,
        devices=[dict(pseudonym='a'*64, expected_revision=1, applied_revision=1, applied_at=now,
            registered=True, awg_allowed=True, tcp_allowed=True, result='applied', decision_observed_at=now,
            valid_until=now+120, reason='canonical', managed=True)]), 'gateway-ru')
    client.force_login(console)
    page = client.get('/inventory/')
    assert page.context['total'] == 3
    assert len(page.context['devices']) == 3 and DeviceProjection.objects.count() == 50
    card = client.get('/inventory/'+'a'*64+'/')
    assert card.status_code == 200
    assert 'Семейный телефон' in card.content.decode()
    assert 'event-'+'f'*64 in card.content.decode()
    assert '/servers/gateway-ru/' in card.content.decode()
    assert len(card.context['device']['nodes']) == 1
    other = client.get('/inventory/'+second+'/')
    assert not other.context['device']['nodes'] and other.context['device']['cohort'] is None
    node = client.get('/servers/gateway-ru/')
    assert '/inventory/'+'a'*64+'/' in node.content.decode()
    assert client.get('/inventory/?q=семейный').context['total'] == 1
    events = client.get('/events/?q=семейный&kind=event')
    assert len(events.context['events']) == 1
    assert '/inventory/'+'a'*64+'/#event-'+'f'*64 in events.content.decode()
    assert client.get('/').context['device_count'] == 2


@pytest.mark.parametrize('applied_revision,allowed', [(0, True), (1, False)])
def test_node_disagreement_is_visible_on_device_and_server(console, client, applied_revision, allowed):
    subscriptions.ingest(event_data(), attempt=True)
    inventory.ingest(snapshot())
    now = int(timezone.now().timestamp())
    transports.ingest(dict(schema=2, source='gateway-ru', observed_at=now, status='ok', runtime_sha256='c'*64,
        devices=[dict(pseudonym='a'*64, expected_revision=1, applied_revision=applied_revision, applied_at=now,
            registered=True, awg_allowed=allowed, tcp_allowed=allowed, result='applied', decision_observed_at=now,
            valid_until=now+120, reason='canonical', managed=True)]), 'gateway-ru')
    client.force_login(console)
    card = client.get('/inventory/'+'a'*64+'/').context['device']
    assert card['problem'] and card['issues']
    server = client.get('/servers/gateway-ru/').context['server']
    assert server['pending_count'] == 1 and server['issue']


def test_production_empty_error_and_demo_are_distinct(console, client):
    client.force_login(console)
    assert client.get('/').context['device_count'] is None
    data = snapshot(); data['devices'] = []; inventory.ingest(data)
    assert client.get('/').context['device_count'] == 0
    data = observation(); subscriptions.ingest(data, attempt=True)
    subscriptions.record_attempt('collection_failed')
    page = client.get('/inventory/')
    assert len(page.context['devices']) == 2
    assert not page.context['canonical_fresh']
    assert page.context['subscription_attempt_text'] == 'Ошибка сбора'
    assert client.get('/inventory/?problem=1').context['total'] == 2
    assert DeviceProjection.objects.count() == 50
    assert client.get('/demo/').context['data']['devices'] == 50


def test_old_event_keeps_its_device_url_when_current_inventory_is_empty(console, client):
    data = event_data(); subscriptions.ingest(data)
    data = observation(); data.update(devices=[], observed_at=data['observed_at']+1)
    subscriptions.ingest(data)
    client.force_login(console)
    card = client.get('/inventory/'+'a'*64+'/')
    assert card.status_code == 200 and not card.context['device']['canonical_fresh']
    assert 'Историческое наблюдение' in card.content.decode()
    assert len(card.context['events']) == 1


def test_historical_event_without_current_device_keeps_an_honest_card(console, client):
    event = event_data()['devices'][0]['event']
    SubscriptionEventObservation.objects.create(event_id=event['event_id'], pseudonym='a'*64,
        occurred_at=objects.moment(event['occurred_at']), details=event)
    client.force_login(console)
    card = client.get('/inventory/'+'a'*64+'/')
    assert card.status_code == 200 and card.context['device']['inventory'] is None
    assert card.context['device']['cohort'] is None and len(card.context['events']) == 1
    assert 'Историческое наблюдение' in card.content.decode()


def test_events_deduplicate_across_snapshots_and_reject_conflict(console):
    data = event_data()
    subscriptions.ingest(data)
    data['observed_at'] += 1
    subscriptions.ingest(data)
    assert SubscriptionSnapshot.objects.count() == 2
    assert SubscriptionEventObservation.objects.count() == 1
    invalid = deepcopy(data); invalid['history']['events'][0]['pseudonym'] = 'b'*64
    with pytest.raises(inventory.SnapshotError):
        subscriptions.ingest(invalid)
    assert SubscriptionSnapshot.objects.count() == 2
    record = SubscriptionEventObservation.objects.get()
    with pytest.raises(DatabaseError), transaction.atomic():
        record.delete()


def test_counter_actual_time_restart_reset_gap_duplicate_and_missing():
    values = [dict(at=100, epoch='one', rx=100, tx=100, cpu_total=100, cpu_idle=50),
        dict(at=120, epoch='one', rx=300, tx=500, cpu_total=200, cpu_idle=80),
        dict(at=120, epoch='one', rx=300, tx=500),
        dict(at=140, epoch='one', rx=1, tx=2),
        dict(at=160, epoch='two', rx=500, tx=600),
        dict(at=600, epoch='two', rx=600, tx=700),
        dict(at=620, epoch=None), dict(at=640, epoch='two', rx=800, tx=900)]
    rates = measurements.counter_rates(values)
    assert len(rates) == 7
    assert rates[1]['rx'] == 10 and rates[1]['tx'] == 20 and rates[1]['cpu'] == 70
    assert all(point['rx'] is None for point in rates[2:])
    assert [point['reason'] for point in rates[2:6]] == ['Сброс счётчика', 'Перезапуск счётчика', 'Пропуск измерений', 'Измерение недоступно']


def test_metrics_strict_idempotent_append_only_and_schema4(console):
    value = metrics()
    saved = measurements.ingest(value, value['source'])
    assert measurements.ingest(value, value['source']).pk == saved.pk
    with pytest.raises(DatabaseError), transaction.atomic():
        saved.delete()
    invalid = deepcopy(value); invalid['devices'].append(invalid['devices'][0])
    with pytest.raises(inventory.SnapshotError):
        measurements.ingest(invalid, value['source'])
    invalid = deepcopy(value); invalid['node']['rx'] = -1
    with pytest.raises(inventory.SnapshotError):
        measurements.ingest(invalid, value['source'])
    data = snapshot(); data.update(schema=4, metrics=value, transport_observation=dict(schema=2,
        source='gateway-ru', observed_at=value['observed_at'], status='not_installed', runtime_sha256=None, devices=[]))
    assert inventory.ingest(data).source == 'gateway-ru'
    assert MeasurementSnapshot.objects.count() == 1


@pytest.mark.parametrize('path', ['/', '/inventory/', '/inventory/'+'a'*64+'/', '/servers/', '/servers/gateway-ru/', '/events/'])
def test_new_pages_permissions_and_no_write(console, client, path):
    inventory.ingest(snapshot())
    assert client.get(path).status_code == 302
    user = get_user_model().objects.create_user(username='no-inventory', is_staff=True)
    client.force_login(user)
    assert client.get(path).status_code == 403
    client.force_login(console)
    response = client.get(path)
    assert response.status_code == 200 and response['Cache-Control'] == 'no-store'
    assert client.post(path).status_code == 405
