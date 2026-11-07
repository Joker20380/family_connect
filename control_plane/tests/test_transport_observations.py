from copy import deepcopy
from datetime import timedelta
import hashlib
import json

from django.db import DatabaseError, transaction
from django.utils import timezone
import pytest

from apps.console import subscriptions, transports, transport_collector
from apps.console.inventory import SnapshotError
from apps.console.models import TransportSnapshot
from test_subscriptions import observation


def transport_observation():
    now = int(timezone.now().timestamp())
    return dict(schema=1, source='gateway-ru', observed_at=now, status='ok', runtime_sha256='c'*64,
        devices=[dict(pseudonym='a'*64, expected_revision=1, applied_revision=1, applied_at=now,
            decision_observed_at=now, valid_until=now+120, reason='canonical',
            registered=True, awg_allowed=False, tcp_allowed=False, result='applied')])


def test_distinct_canonical_and_application_read_only(console, client):
    subscriptions.ingest(observation(), attempt=True)
    current = transports.ingest(transport_observation(), 'gateway-ru')
    assert transports.ingest(transport_observation(), 'gateway-ru').pk == current.pk
    client.force_login(console)
    response = client.get('/subscriptions/')
    text = response.content.decode()
    assert 'Активна' in text and 'AWG: peer удалён' in text and 'TCP: пользователь удалён' in text
    assert 'Schema 1 · проверенный archive SHA256' in text
    assert 'Амстердам 1' in text and 'Неизвестно' in text
    assert response['Cache-Control'] == 'no-store'
    assert client.post('/subscriptions/').status_code == 405
    with pytest.raises(DatabaseError), transaction.atomic():
        TransportSnapshot.objects.filter(pk=current.pk).update(status='ok')
    with pytest.raises(DatabaseError), transaction.atomic():
        current.delete()


def test_attempt_error_wins_over_future_snapshot_and_pending_revision(console, client):
    subscriptions.ingest(observation(), attempt=True)
    value = transport_observation()
    value['observed_at'] += 120
    transports.ingest(value, 'gateway-ru')
    transports.attempt('gateway-ru', 'collection_failed')
    client.force_login(console)
    text = client.get('/subscriptions/').content.decode()
    assert 'Ошибка сбора' in text and 'AWG: peer удалён' not in text
    value = transport_observation()
    value['devices'][0]['expected_revision'] = 2
    transports.ingest(value, 'gateway-ru')
    assert 'Ожидается сверка актуальной ревизии' in client.get('/subscriptions/').content.decode()


@pytest.mark.parametrize('change', [lambda value: value.update(schema=True),
    lambda value: value.update(source='nl-amsterdam-1'), lambda value: value.update(runtime_sha256='wrong'),
    lambda value: value['devices'][0].update(applied_revision=2),
    lambda value: value['devices'][0].update(applied_at=value['observed_at']+1),
    lambda value: value['devices'][0].update(tcp_allowed=None),
    lambda value: value['devices'][0].update(device='private')])
def test_invalid_application_snapshot_rejected(db, change):
    value = transport_observation()
    change(value)
    with pytest.raises(SnapshotError):
        transports.ingest(value, 'gateway-ru')
    assert not TransportSnapshot.objects.exists()


def test_filters_and_no_zero_on_error(console, client):
    subscriptions.ingest(observation(), attempt=True)
    client.force_login(console)
    assert 'Активна' not in client.get('/subscriptions/?state=noncohort').content.decode().split('<section class="subscription-list"')[1].split('</section>')[0]
    assert len(client.get('/subscriptions/?query=aaaa').context['rows']) == 1
    assert len(client.get('/subscriptions/?query=private-person').context['rows']) == 0
    subscriptions.record_attempt('import_failed')
    text = client.get('/subscriptions/').content.decode()
    assert 'Ошибка импорта' in text and 'Устройств в снимке</span><strong>0' not in text


def test_absent_state_is_not_confirmed_access_and_bad_archive_unavailable(tmp_path):
    value = transport_collector.collect_transport('gateway-ru', b'a'*32, None, tmp_path)
    assert value['status'] == 'not_installed' and not value['devices']
    (tmp_path/'paid-transport.pyz').write_bytes(b'unknown')
    value = transport_collector.collect_transport('gateway-ru', b'a'*32, 'b'*64, tmp_path)
    assert value['status'] == 'unavailable' and not value['devices']


def test_collector_clock_is_taken_after_receipt_read(tmp_path, monkeypatch, console):
    raw = b'isolated-archive'
    now = int(timezone.now().timestamp())
    (tmp_path/'paid-transport.pyz').write_bytes(raw)
    node = 'gateway-ru'
    (tmp_path/'transport-enforcement.json').write_text(json.dumps(dict(schema=1, profile='paid-transports-v2', node=node, enabled=True)))
    (tmp_path/'transport-attempt.json').write_text(json.dumps(dict(schema=1, node=node, observed_at=now+1, result='applied')))
    (tmp_path/'transport-state.json').write_text(json.dumps(dict(schema=1,node=node,records={'a'*32:dict(decision=dict(revision=1,observed_at=now,valid_until=now+120,cohort=True),applied=dict(applied_revision=1,observed_at=now+1,registered=True,allowed=False,reason='canonical'))})))
    clock = iter((now, now+2))
    monkeypatch.setattr(transport_collector.time, 'time', lambda: next(clock))
    value = transport_collector.collect_transport(node,b'k'*32,hashlib.sha256(raw).hexdigest(),tmp_path)
    assert value['observed_at'] == now+2 and value['status'] == 'ok'
    monkeypatch.undo()
    assert transports.ingest(value,node).devices[0]['applied_at'] == now+1


def test_transport_error_is_visible_despite_old_source_clock(console, client):
    subscriptions.ingest(observation(),attempt=True)
    previous=transports.ingest(transport_observation(),'gateway-ru')
    broken=dict(schema=1,source='gateway-ru',observed_at=previous.devices[0]['applied_at']-600,
                status='unavailable',runtime_sha256=None,devices=[])
    transports.ingest(broken,'gateway-ru')
    client.force_login(console)
    response=client.get('/subscriptions/')
    node=response.context['transport_nodes'][0]
    assert node['text']=='Ошибка источника' and node['previous'].pk==previous.pk
    assert 'Последнее успешное наблюдение' in response.content.decode()


def test_v2_noncohort_and_prepared_membership_are_not_lease_expiry(console, client):
    subscriptions.ingest(observation(),attempt=True)
    value = transport_observation()
    value['schema'] = 2
    value['devices'][0].update(expected_revision=0,applied_revision=0,managed=False,valid_until=None,
        reason='noncohort',awg_allowed=True,tcp_allowed=True)
    transports.ingest(value,'gateway-ru')
    client.force_login(console)
    text = client.get('/subscriptions/').content.decode()
    assert 'Schema 2 · проверенный archive SHA256' in text
    assert 'paid-таймер не применяется' in text and 'paid-срок не применяется' in text
    value['devices'][0].update(managed=True,reason='membership-pending',awg_allowed=False,tcp_allowed=False)
    transports.ingest(value,'gateway-ru')
    assert 'Первое включение: узел подготовлен' in client.get('/subscriptions/').content.decode()
    value['devices'][0]['tcp_allowed'] = True
    with pytest.raises(SnapshotError):
        transports.ingest(value,'gateway-ru')


def test_historical_observation_does_not_invent_schema(console, client, monkeypatch):
    original = transports.attempt
    monkeypatch.setattr(transports, 'attempt', lambda source, status, snapshot=None, **kwargs: original(source, status, snapshot))
    subscriptions.ingest(observation(), attempt=True)
    transports.ingest(transport_observation(), 'gateway-ru')
    client.force_login(console)
    assert 'Schema не сохранена в историческом наблюдении' in client.get('/subscriptions/').content.decode()
