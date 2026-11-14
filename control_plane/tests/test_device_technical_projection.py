from copy import deepcopy
from datetime import timedelta
import hashlib
import hmac
import json
import subprocess

from django.core.management import call_command
from django.utils import timezone
import pytest

from control.friends import technical_metadata as contract
from apps.console import inventory, technical_metadata
from apps.console.models import AuditRecord, InventorySnapshot, TechnicalMetadata, TechnicalMetadataSource
from tests.test_observability import snapshot


def observation():
    now = int(timezone.now().timestamp())
    profile = dict(sampled_at_ms=now * 1000, age_ms=0, source='android_build_package', status='available',
                   reason='none', values=dict(manufacturer='Google', model='Pixel controlled', android_version='15',
                   api_level=35, app_version='unpublished-test', version_code=126))
    return dict(schema=1, source='gateway-ru', observed_at=now, status='ok', devices=[dict(
        pseudonym='a' * 64, consent_epoch=1, sequence=1, consent='enabled', received_at=now,
        observations=contract.project(dict(profile=profile), now))])


def test_latest_only_full_hmac_no_audit_or_snapshot_copy(db):
    data = observation()
    technical_metadata.ingest(data)
    technical_metadata.ingest(data)
    second = deepcopy(data)
    second['devices'][0]['pseudonym'] = 'a' * 12 + 'b' * 52
    technical_metadata.ingest(second)
    assert TechnicalMetadata.objects.count() == 2
    assert InventorySnapshot.objects.count() == AuditRecord.objects.count() == 0
    data['devices'][0]['sequence'] += 1
    data['devices'][0]['observations']['profile']['values']['model'] = 'Replacement'
    technical_metadata.ingest(data)
    assert TechnicalMetadata.objects.count() == 2
    assert 'Pixel controlled' not in json.dumps(TechnicalMetadata.objects.get(pk='a' * 64).observations)


def test_revoke_and_delayed_import_cannot_resurrect(db):
    data = observation()
    technical_metadata.ingest(data)
    revoked = deepcopy(data)
    revoked['devices'][0].update(consent_epoch=2, sequence=2, consent='revoked', observations={})
    technical_metadata.ingest(revoked)
    with pytest.raises(inventory.SnapshotError):
        technical_metadata.ingest(data)
    assert TechnicalMetadata.objects.get(pk='a' * 64).observations == {}
    assert technical_metadata.presentation(TechnicalMetadata.objects.first(), timezone.now())['status'] == 'revoked'


def test_expiry_hides_before_cleanup_then_physically_removes(db):
    data = observation()
    technical_metadata.ingest(data)
    future = timezone.now() + timedelta(days=8)
    row = TechnicalMetadata.objects.first()
    assert technical_metadata.presentation(row, future)['observations'] == {}
    technical_metadata.prune(future)
    row.refresh_from_db()
    assert row.observations == {}
    assert row.consent_epoch == 1


def test_conflicting_receipt_and_raw_private_fields_are_rejected(db):
    data = observation()
    technical_metadata.ingest(data)
    data['devices'][0]['observations']['profile']['values']['model'] = 'Conflicting'
    with pytest.raises(inventory.SnapshotError):
        technical_metadata.ingest(data)
    data['devices'][0]['sequence'] = 2
    data['devices'][0]['observations']['profile']['values']['ip'] = '203.0.113.2'
    with pytest.raises(inventory.SnapshotError):
        technical_metadata.ingest(data)


def test_wrong_clock_and_independent_age(db):
    data = observation()
    group = data['devices'][0]['observations']['profile']
    group.update(age_at_receive_ms=3600000, clock_status='clock_skew')
    technical_metadata.ingest(data)
    source = TechnicalMetadataSource.objects.first()
    presented = technical_metadata.presentation(TechnicalMetadata.objects.first(), timezone.now(), source)
    assert presented['observations']['profile']['age_seconds'] == 3600
    assert 'не согласованы' in presented['observations']['profile']['clock_label']


def test_real_object_list_card_and_search_not_synthetic(console, client):
    inventory.ingest(snapshot())
    technical_metadata.ingest(observation())
    client.force_login(console)
    page = client.get('/inventory/?model=controlled&android=15&app=unpublished')
    assert page.status_code == 200 and page.context['total'] == 1
    assert 'Pixel controlled' in page.content.decode()
    assert client.get('/inventory/?model=absent').context['total'] == 0
    card = client.get('/inventory/' + 'a' * 64 + '/')
    html = card.content.decode()
    assert 'Pixel controlled' in html and 'Источники и независимый возраст' in html
    assert 'android_build_package' in html and 'received_at' in html
    assert 'Сбор выключен' not in html
    assert '/subscriptions/' in html and '/servers/' in html


def test_unavailable_import_prunes_without_logging_payload(db, capsys):
    technical_metadata.ingest(observation())
    call_command('import_technical_metadata', unavailable=True)
    assert TechnicalMetadataSource.objects.first().status == 'unavailable'
    assert 'Pixel' not in capsys.readouterr().out


def test_collector_transient_hmac_and_bad_pin_input(tmp_path):
    from pathlib import Path
    import sys
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    try:
        from collect_technical_metadata import collect
        local = tmp_path / '.local'
        local.mkdir()
        key = b'synthetic-hmac-test-key-32-bytes'
        assert len(key) == 32
        (local / 'inventory-hmac.key').write_bytes(key)
        (local / 'inventory-hmac.key').chmod(0o600)
        config = local / 'technical-metadata-source.json'
        config.write_text(json.dumps(dict(python='/isolated/python', archive='/isolated/runtime.pyz', archive_sha256='a' * 64)))
        config.chmod(0o600)
        code = tmp_path / 'apps/console'
        code.mkdir(parents=True)
        (code / 'technical_metadata_collector.py').write_text('')
        data = observation()
        data['devices'][0]['device'] = 'b' * 32
        del data['devices'][0]['pseudonym']
        def run(command, **kwargs):
            assert ' -I -B -' in command[-1]
            assert key not in kwargs['input']
            return subprocess.CompletedProcess(command, 0, stdout=json.dumps(data).encode())
        before = set(local.iterdir())
        result = json.loads(collect(base=tmp_path, run=run))
        assert result['devices'][0]['pseudonym'] == hmac.new(key, b'b' * 32, hashlib.sha256).hexdigest()
        assert set(local.iterdir()) == before
        config.chmod(0o644)
        with pytest.raises(ValueError): collect(base=tmp_path, run=run)
    finally:
        sys.path.pop(0)
