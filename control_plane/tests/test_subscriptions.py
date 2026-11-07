from copy import deepcopy
from datetime import timedelta
import hashlib
import json
import sqlite3

from django.contrib.auth import get_user_model
from django.db import DatabaseError, transaction
from django.utils import timezone
import pytest

from apps.console import backend, inventory, subscription_collector, subscriptions
from apps.console.models import SubscriptionSnapshot, DeviceProjection, PaymentRecord
from control.friends import paid_beta


def observation():
    now = int(timezone.now().timestamp())
    return dict(schema=1, scope='production', source='gateway-ru', observed_at=now,
        status='ok', runtime_sha256='c' * 64, devices=[dict(pseudonym='a' * 64, cohort=True,
            subscription=dict(state='active', effective_state='active', paid_allow=True,
                period_start=now - 60, paid_until=now + 3600, grace_until=None,
                entitlement_until=now + 3600, version=1), event=None),
            dict(pseudonym='b' * 64, cohort=False, subscription=None, event=None)])


def test_import_permissions_immutability_and_no_demo_writes(console, client):
    before = backend.checked_path().read_bytes()
    data = observation()
    saved = subscriptions.ingest(data)
    assert subscriptions.ingest(data).pk == saved.pk
    assert SubscriptionSnapshot.objects.count() == 1
    assert backend.checked_path().read_bytes() == before
    assert DeviceProjection.objects.count() == 50 and PaymentRecord.objects.count() == 0
    assert client.get('/subscriptions/').status_code == 302
    ordinary = get_user_model().objects.create_user(username='no-permission', is_staff=True)
    client.force_login(ordinary)
    assert client.get('/subscriptions/').status_code == 403
    client.force_login(console)
    response = client.get('/subscriptions/')
    assert response.status_code == 200 and response['Cache-Control'] == 'no-store'
    assert 'Вне платного пилота' in response.content.decode()
    assert 'Соответствующего события нет' in response.content.decode()
    assert client.post('/subscriptions/', {}).status_code == 405
    assert client.get('/admin/console/subscriptionsnapshot/add/').status_code == 404
    with pytest.raises(DatabaseError), transaction.atomic():
        SubscriptionSnapshot.objects.filter(pk=saved.pk).update(status='ok')
    with pytest.raises(DatabaseError), transaction.atomic():
        saved.delete()


@pytest.mark.parametrize('mutation', [
    lambda data: data.update(schema=True), lambda data: data.update(scope='synthetic'),
    lambda data: data.update(source='other-host'), lambda data: data.update(observed_at=True),
    lambda data: data.update(runtime_sha256=None), lambda data: data.update(status='unavailable'),
    lambda data: data.update(reference_hash='private'),
    lambda data: data['devices'].append(deepcopy(data['devices'][0])),
    lambda data: data['devices'][0].update(support_id='private'),
    lambda data: data['devices'][0]['subscription'].update(version=True),
    lambda data: data['devices'][1].update(cohort=1),
    lambda data: data['devices'][0].update(event=dict(event_id='d'*64, event_type='other',
        occurred_at=data['observed_at'], previous_state=None, new_state='active', result='APPLIED')),
])
def test_invalid_snapshot_atomic(db, mutation):
    data = observation()
    mutation(data)
    with pytest.raises(inventory.SnapshotError):
        subscriptions.ingest(data)
    assert not SubscriptionSnapshot.objects.exists()


def test_freshness_error_missing_zero_and_stored_time(console, client):
    client.force_login(console)
    assert 'Нет наблюдений' in client.get('/subscriptions/').content.decode()
    data = observation()
    data['devices'] = []
    saved = subscriptions.ingest(data)
    assert '0 устройств' in client.get('/subscriptions/').content.decode()
    assert 'Устарело' in subscriptions.freshness(saved, timezone.now() + timedelta(minutes=6))
    assert 'Ошибка часов' in subscriptions.freshness(saved, timezone.now() - timedelta(minutes=1))
    for status in ('unsupported', 'unavailable'):
        data.update(status=status, observed_at=data['observed_at'] + 1)
        subscriptions.ingest(data)
        text = client.get('/subscriptions/').content.decode()
        assert 'Это не нулевой cohort' in text and 'Последнее успешное чтение' in text


def test_real_canonical_collector_readonly_events_and_expiry(console, tmp_path, monkeypatch):
    archive = tmp_path / 'runtime.pyz'
    archive.write_bytes(b'synthetic-archive-metadata')
    config = dict(archive=str(archive), archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest())
    original_path = list(subscription_collector.sys.path)
    monkeypatch.setattr(subscription_collector.sys, 'path', original_path)
    now = int(timezone.now().timestamp())
    monkeypatch.setattr(subscription_collector.time, 'time', lambda: now)
    device = DeviceProjection.objects.order_by('label').first()
    with backend.registry(write=True) as database:
        support = backend.selector(database, device.device)
        paid_beta.apply_event(database, support, 'payment', 'synthetic-ops-event', 'synthetic-only', now=now,
            period_start=now - 30, paid_until=now + 30, apk_sha256=paid_beta.PAID_ANDROID_APK_SHA256)
    before = backend.checked_path().read_bytes()
    value = subscription_collector.collect_subscriptions(config, backend.checked_path(), b's' * 32)
    assert value['status'] == 'ok' and len(value['devices']) == 50
    row = next(row for row in value['devices'] if row['cohort'])
    assert row['subscription']['effective_state'] == 'active'
    assert row['event']['event_type'] == 'payment' and row['event']['event_id'] != 'synthetic-ops-event'
    assert support not in json.dumps(value) and device.device not in json.dumps(value)
    subscriptions.ingest(value)
    monkeypatch.setattr(subscription_collector.time, 'time', lambda: now + 30)
    expired = subscription_collector.collect_subscriptions(config, backend.checked_path(), b's' * 32)
    row = next(row for row in expired['devices'] if row['cohort'])
    assert row['subscription']['state'] == 'active' and row['subscription']['effective_state'] == 'expired'
    assert row['subscription']['version'] == 1 and row['event']['event_type'] == 'payment'
    assert backend.checked_path().read_bytes() == before
    config['archive_sha256'] = '0' * 64
    assert subscription_collector.collect_subscriptions(config, backend.checked_path(), b's' * 32)['status'] == 'unavailable'


def test_missing_and_damaged_schema_are_not_empty_cohort(console, tmp_path, monkeypatch):
    archive = tmp_path / 'archive'; archive.write_bytes(b'fixture')
    config = dict(archive=str(archive), archive_sha256=hashlib.sha256(b'fixture').hexdigest())
    monkeypatch.setattr(subscription_collector.sys, 'path', list(subscription_collector.sys.path))
    path = tmp_path / 'empty.db'
    database = sqlite3.connect(path)
    database.execute('CREATE TABLE devices (device TEXT)')
    database.close()
    assert subscription_collector.collect_subscriptions(config, path, b's'*32)['status'] == 'unsupported'
    database = sqlite3.connect(path)
    database.execute('CREATE TABLE paid_beta_events (event_id TEXT)'); database.close()
    assert subscription_collector.collect_subscriptions(config, path, b's'*32)['status'] == 'unavailable'


def test_inventory_v2_imports_subscription_atomically(console):
    from test_observability import snapshot
    data = snapshot()
    data.update(schema=2, subscription_observation=observation())
    inventory.ingest(data)
    assert SubscriptionSnapshot.objects.count() == 1
    data['subscription_observation']['observed_at'] += 1
    data['server']['load_1m'] = -1
    with pytest.raises(inventory.SnapshotError):
        inventory.ingest(data)
    assert SubscriptionSnapshot.objects.count() == 1
