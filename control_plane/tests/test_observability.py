from copy import deepcopy
from datetime import timedelta
import hashlib
import json
import sqlite3

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.db import DatabaseError, transaction
from django.test import Client
from django.utils import timezone
import pytest

from apps.console import backend, collector, inventory, workflow
from apps.console.models import (InventorySnapshot, InventoryDevice, TechnicalSample, OperationSwitch,
    PaymentRecord, OperationRequest, DeviceProjection, ServerObservation)


def snapshot():
    now = timezone.now().replace(microsecond=0)
    return dict(schema=1, scope='production', source='gateway-ru', observed_at=now.isoformat(), registry_status='ok',
        devices=[dict(pseudonym='a' * 64, activated=True, revoked=False, version_code=106,
            version_source='support', last_seen=(now - timedelta(minutes=1)).isoformat())],
        server=dict(load_1m=0.5, memory_used_percent=45.0, disk_used_percent=30.0, uptime_seconds=200,
            services={name: 'active' for name in collector.SERVICES}))


def test_strict_import_is_isolated_idempotent_and_read_only(console, client):
    before = backend.checked_path().read_bytes()
    data = snapshot()
    first = inventory.ingest(data)
    assert inventory.ingest(data).pk == first.pk
    assert InventorySnapshot.objects.count() == InventoryDevice.objects.count() == 1
    assert DeviceProjection.objects.count() == 50
    assert PaymentRecord.objects.count() == OperationRequest.objects.count() == 0
    assert backend.checked_path().read_bytes() == before
    client.force_login(console)
    page = client.get('/inventory/' + 'a' * 64 + '/')
    assert page.status_code == 200 and 'История наблюдений' in page.content.decode()
    for model, key in [('inventorysnapshot', first.pk), ('inventorydevice', first.devices.first().pk),
        ('serverobservation', first.server.pk), ('technicalsample', 1), ('operationswitch', 1)]:
        assert client.get(f'/admin/console/{model}/add/').status_code == 403
        assert client.post(f'/admin/console/{model}/{key}/change/', {'scope': 'synthetic'}).status_code == 403
    response = client.post('/operations/new/', dict(device='a' * 64, action='revoke'))
    assert response.status_code == 200 and not OperationRequest.objects.exists()


@pytest.mark.parametrize('mutation', [
    lambda data: data.update(support_id='PRIVATE_SELECTOR'),
    lambda data: data.update(schema=True),
    lambda data: data.update(source='unapproved-host'),
    lambda data: data.update(scope='synthetic'),
    lambda data: data.update(observed_at='2026-10-27T00:00:00'),
    lambda data: data.update(observed_at=(timezone.now() + timedelta(days=1)).isoformat()),
    lambda data: data.update(registry_status='unavailable'),
    lambda data: data['devices'].append(deepcopy(data['devices'][0])),
    lambda data: data['devices'][0].update(pseudonym='real-canonical-key'),
    lambda data: data['devices'][0].update(version_code=True),
    lambda data: data['devices'][0].update(activated='true'),
    lambda data: data['devices'][0].update(last_seen=(timezone.now() + timedelta(minutes=1)).isoformat()),
    lambda data: data['server'].update(memory_used_percent=101),
    lambda data: data['server'].update(load_1m=float('nan')),
    lambda data: data['server'].update(uptime_seconds=2.5),
    lambda data: data['server']['services'].update(unapproved='active'),
])
def test_bad_snapshots_rejected_atomically(console, mutation):
    data = snapshot()
    mutation(data)
    with pytest.raises(inventory.SnapshotError):
        inventory.ingest(data)
    assert not InventorySnapshot.objects.exists()


@pytest.mark.parametrize('raw', [b'{"schema":1,"schema":1}', b'{"value":NaN}', b'{"value":Infinity}', b'\xff', b'[]' * 3000000])
def test_strict_json(raw):
    with pytest.raises(inventory.SnapshotError):
        inventory.strict_load(raw)


def test_collector_queries_no_keys_no_aliases_no_writes(console):
    path = backend.checked_path()
    before = path.read_bytes()
    rows = collector.registry_rows(path, b's' * 32)
    assert len(rows) == 50 and path.read_bytes() == before
    assert rows == collector.registry_rows(path, b's' * 32)
    assert rows[0]['pseudonym'] != collector.registry_rows(path, b't' * 32)[0]['pseudonym']
    with backend.registry() as database:
        canonical = database.execute('SELECT device FROM devices LIMIT 1').fetchone()[0]
        alias = backend.selector(database, canonical)
    assert canonical not in json.dumps(rows) and alias not in json.dumps(rows)
    assert set(rows[0]) == {'pseudonym', 'activated', 'revoked', 'version_code', 'version_source', 'last_seen'}


def test_collector_missing_database_does_not_create(tmp_path):
    missing = tmp_path / 'absent.db'
    with pytest.raises(sqlite3.OperationalError):
        collector.registry_rows(missing, b's' * 32)
    assert not missing.exists()


def test_collector_only_reads_fixed_services_and_marks_absence(tmp_path, monkeypatch):
    from types import SimpleNamespace
    commands = []
    def run(command, **kwargs):
        commands.append(command)
        return SimpleNamespace(stdout='LoadState=not-found\nActiveState=inactive\n')
    monkeypatch.setattr(collector.subprocess, 'run', run)
    data = collector.collect('gateway-nl', b's' * 32, tmp_path / 'missing.db')
    assert data['registry_status'] == 'unavailable' and data['devices'] == []
    assert all(value == 'not_found' for value in data['server']['services'].values())
    assert len(commands) == len(collector.SERVICES)
    assert all(command[:2] == ['systemctl', 'show'] for command in commands)
    with pytest.raises(ValueError):
        collector.collect('unapproved', b's' * 32)


@pytest.mark.parametrize('path', ['/observability/', '/inventory/', '/servers/gateway-ru/', '/telemetry.json', '/stop/'])
def test_observability_authentication_and_russian(console, client, path):
    assert client.get(path).status_code == 302
    client.force_login(console)
    result = client.get(path)
    assert result.status_code == 200 and result['Cache-Control'] == 'no-store'
    if path != '/telemetry.json':
        text = result.content.decode()
        assert 'lang="ru"' in text and 'Наблюдаемость' in text


def test_missing_telemetry_is_null_not_zero_and_demo_is_separate(console, client):
    call_command('seed_observability', verbosity=0)
    call_command('seed_observability', verbosity=0)
    assert TechnicalSample.objects.count() == 1400
    client.force_login(console)
    production = client.get('/telemetry.json').json()
    assert all(row['count'] is None and row['value'] is None for row in production['metrics'])
    demo = client.get('/telemetry.json?scope=synthetic').json()
    assert all(row['count'] == 350 and row['value'] is not None for row in demo['metrics'])
    device = DeviceProjection.objects.first()
    page = client.get(f'/devices/{device.pk}/telemetry/?scope=synthetic')
    assert page.status_code == 200
    assert client.get('/observability/?scope=synthetic').status_code == 200
    assert PaymentRecord.objects.count() == OperationRequest.objects.count() == 0


def test_filters_latest_snapshot_staleness_and_pagination(console, client):
    data = snapshot()
    data['devices'] = [dict(data['devices'][0], pseudonym=hashlib.sha256(str(number).encode()).hexdigest()) for number in range(30)]
    old = deepcopy(data)
    old['observed_at'] = (timezone.now() - timedelta(minutes=10)).isoformat()
    for item in old['devices']:
        item['last_seen'] = (timezone.now() - timedelta(hours=1)).isoformat()
    inventory.ingest(old)
    inventory.ingest(data)
    client.force_login(console)
    page = client.get('/inventory/')
    assert len(page.context['page']) == 25 and page.context['page'].paginator.count == 30
    assert len(client.get('/inventory/?page=2').context['page']) == 5
    assert client.get('/inventory/?query=' + data['devices'][0]['pseudonym']).context['page'].paginator.count == 1
    assert client.get('/inventory/?source=gateway-nl').context['page'].paginator.count == 0
    assert client.get('/telemetry.json?start=2025-01-01&end=2024-01-01').status_code == 400
    assert client.get('/telemetry.json?query=private-selector').status_code == 400
    assert client.get('/servers/unknown/').status_code == 404
    assert client.get('/inventory/unknown/').status_code == 404


@pytest.mark.parametrize('model', [InventorySnapshot, InventoryDevice, ServerObservation, TechnicalSample])
def test_observation_rows_are_immutable(console, model):
    inventory.ingest(snapshot())
    call_command('seed_observability', verbosity=0)
    with pytest.raises(DatabaseError), transaction.atomic():
        model.objects.all().delete()


def test_emergency_stop_csrf_rbac_and_backend_boundary(console, client, operation):
    request = workflow.prepare(console, operation().pk)
    viewer = get_user_model().objects.create_user(username='read-only', is_staff=True)
    viewer.groups.add(Group.objects.get(name='Наблюдатели панели'))
    client.force_login(viewer)
    assert client.post('/stop/change/', {'confirmed': 'on', 'action': 'stop'}).status_code == 403
    protected = Client(enforce_csrf_checks=True)
    protected.force_login(console)
    failure = protected.post('/stop/change/', {'confirmed': 'on', 'action': 'stop'})
    assert failure.status_code == 403 and 'Доступ запрещён' in failure.content.decode()
    client.force_login(console)
    assert client.get('/stop/change/').status_code == 405
    client.post('/stop/change/', {'action': 'stop'})
    assert not OperationSwitch.objects.get().stopped
    client.post('/stop/change/', {'confirmed': 'on', 'action': 'stop'})
    before = backend.checked_path().read_bytes()
    with pytest.raises(workflow.WorkflowError, match='EMERGENCY_STOP'):
        workflow.execute(console, request.pk, workflow.confirmation_token(console, request))
    assert backend.checked_path().read_bytes() == before
    client.post('/stop/change/', {'confirmed': 'on', 'action': 'resume'})
    assert workflow.execute(console, request.pk, workflow.confirmation_token(console, request)).status == 'APPLIED'
    client.post('/stop/change/', {'confirmed': 'on', 'action': 'stop'})
    assert workflow.execute(console, request.pk, 'unused-on-receipt-readback').status == 'APPLIED'


def test_legacy_12_to_50_preserves_identities_and_paid_events(console, operation):
    request = workflow.prepare(console, operation().pk)
    workflow.execute(console, request.pk, workflow.confirmation_token(console, request))
    from control.friends import paid_beta
    with paid_beta.connection(backend.checked_path(), write=True) as database:
        removed = [row[0] for row in database.execute("SELECT device FROM control_plane_devices WHERE label > 'Демо 12'")]
        for device in removed:
            for table in ('control_plane_devices', 'device_support', 'challenges', 'invites', 'devices'):
                database.execute('DELETE FROM ' + table + ' WHERE device=?', (device,))
        database.execute("UPDATE control_plane_fixture SET version='CONTROL-PLANE-0-SYNTHETIC-v1'")
        identities = list(database.execute('SELECT * FROM devices ORDER BY device'))
        events = list(database.execute('SELECT * FROM paid_beta_events'))
    backend.seed_fixture()
    backend.seed_fixture()
    with backend.registry() as database:
        assert len(backend.members()) == 50
        assert [tuple(row) for row in database.execute('SELECT * FROM paid_beta_events')] == [tuple(row) for row in events]
        for original in identities:
            assert tuple(database.execute('SELECT * FROM devices WHERE device=?', (original['device'],)).fetchone()) == tuple(original)
        assert database.execute('SELECT count(*) FROM paid_beta_subscriptions').fetchone()[0] == 1
