from copy import deepcopy
from datetime import datetime, timedelta

import pytest
from django.utils import timezone

from apps.console import collector, inventory, network_probe, probe_inventory, subscriptions, technical_metadata
from apps.console.models import (AuditRecord, InventorySnapshot, NetworkProbe, OperationRequest, PaymentRecord,
                                SubscriptionSnapshot, TechnicalMetadata)
from control.friends import technical_metadata as contract


def snapshot():
    now = timezone.now().replace(microsecond=0)
    return dict(schema=1, scope='production', source='gateway-ru', observed_at=now.isoformat(), registry_status='ok',
        devices=[], server=dict(load_1m=0.5, memory_used_percent=45.0, disk_used_percent=30.0, uptime_seconds=200,
        services={name: 'active' for name in collector.SERVICES}))


def sample():
    address, port = network_probe.ENDPOINTS['nl-amsterdam-1']
    return dict(schema=1, scope='production', source='nl-amsterdam-1', probe='tcp_connect', vantage='operator-workstation',
                address=address, port=port, observed_at=timezone.now().isoformat(), outcome='reachable', duration_ms=1.0)


def observation():
    return dict(schema=1, scope='production', source='gateway-ru', observed_at=int(timezone.now().timestamp()),
                status='ok', runtime_sha256='c' * 64, devices=[])


def metadata():
    now = int(timezone.now().timestamp())
    profile = dict(sampled_at_ms=now * 1000, age_ms=0, source='android_build_package', status='available', reason='none',
        values=dict(manufacturer='Synthetic', model='Fixture', android_version='15', api_level=35,
                    app_version='test', version_code=126))
    return dict(schema=1, source='gateway-ru', observed_at=now, status='ok', devices=[dict(pseudonym='a' * 64,
        consent_epoch=1, sequence=1, consent='enabled', received_at=now,
        observations=contract.project(dict(profile=profile), now))])


@pytest.mark.parametrize('factory,ingest,model,action', [
    (snapshot, inventory.ingest, InventorySnapshot, 'inventory.import'),
    (sample, probe_inventory.ingest, NetworkProbe, 'network_probe.import'),
    (observation, subscriptions.ingest, SubscriptionSnapshot, 'subscriptions.import'),
])
def test_delayed_snapshot_after_newer_and_lost_reply_replay_are_read_model_only(db, factory, ingest, model, action):
    previous = factory()
    current = deepcopy(previous)
    if type(current['observed_at']) is int:
        current['observed_at'] += 1
    else:
        current['observed_at'] = (datetime.fromisoformat(current['observed_at']) + timedelta(seconds=1)).isoformat()
    latest = ingest(current)
    delayed = ingest(previous)
    repeated = ingest(previous)
    assert delayed.pk == repeated.pk != latest.pk
    assert model.objects.count() == 2
    assert model.objects.order_by('-observed_at').first().pk == latest.pk
    assert AuditRecord.objects.filter(action=action).count() == 2
    assert PaymentRecord.objects.count() == OperationRequest.objects.count() == 0


def test_delayed_metadata_cannot_cross_revocation_floor(db):
    previous = metadata()
    technical_metadata.ingest(previous)
    revoked = deepcopy(previous)
    revoked['devices'][0].update(consent_epoch=2, sequence=2, consent='revoked', observations={})
    technical_metadata.ingest(revoked)
    with pytest.raises(inventory.SnapshotError):
        technical_metadata.ingest(previous)
    assert TechnicalMetadata.objects.get(pk='a' * 64).observations == {}


def test_probe_replay_identity_cannot_change_effect(db):
    previous = sample()
    original = probe_inventory.ingest(previous)
    with pytest.raises(inventory.SnapshotError):
        probe_inventory.ingest(dict(previous, outcome='timeout'))
    original.refresh_from_db()
    assert original.outcome == 'reachable' and NetworkProbe.objects.count() == 1


def test_metadata_duplicate_has_no_audit_copy_or_second_effect(db):
    previous = metadata()
    technical_metadata.ingest(previous)
    technical_metadata.ingest(previous)
    assert TechnicalMetadata.objects.count() == 1 and AuditRecord.objects.count() == 0
    changed = deepcopy(previous)
    changed['devices'][0]['observations']['profile']['values']['model'] = 'Changed without new sequence'
    with pytest.raises(inventory.SnapshotError):
        technical_metadata.ingest(changed)
