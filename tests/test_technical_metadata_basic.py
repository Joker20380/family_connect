import json
import hashlib
from pathlib import Path
import sqlite3
import types

import pytest

from control.friends import technical_metadata as metadata
from control.friends.access import Rejected
from test_technical_metadata import setup, report, submit


def basic(epoch=1, sequence=1, operation='sample'):
    value = report(epoch, sequence, operation)
    value.update(schema=2, processing_mode=metadata.BASIC_MODE, policy_version=metadata.BASIC_POLICY)
    for group, observation in value['observations'].items():
        observation['values'] = ({'os': 'Android', 'os_version': '15', 'app_version': 'candidate'} if group == 'profile'
            else {name: observation['values'][name] for name in metadata.BASIC_FIELDS[group]})
    return value


def test_authenticated_basic_receipt_never_claims_consent_and_legacy_remains_compatible(setup):
    assert submit(setup, report())['consent'] == 'enabled'
    setup[3][0] += 60
    receipt = submit(setup, basic(sequence=2))
    assert receipt['consent'] == 'not_requested' and receipt['schema'] == 2
    assert receipt == submit(setup, basic(sequence=2))
    row, = metadata.read_all(setup[2], setup[3][0])
    assert row['processing_mode'] == metadata.BASIC_MODE and row['policy_version'] == metadata.BASIC_POLICY
    assert row['consent'] == 'not_requested'
    assert set(row['observations']['profile']['values']) == {'os', 'os_version', 'app_version'}


@pytest.mark.parametrize('group,field,value', [('profile', 'model', 'never automatic'),
    ('profile', 'manufacturer', 'test'), ('mobile', 'radio', '5G'), ('diagnostic', 'readiness', 'READY'),
    ('session', 'preference', 'AUTO')])
def test_extended_fields_refused_not_silently_stripped(group, field, value):
    sample = basic()
    sample['observations'][group]['values'][field] = value
    with pytest.raises(ValueError):
        metadata.validate(json.dumps(sample))


def test_old_v1_server_explicitly_refuses_basic_no_extended_fallback():
    source = (Path(__file__).parent / 'fixtures/technical-metadata-v1-111866ae.py.txt').read_bytes()
    assert hashlib.sha256(source).hexdigest() == 'c0adf82aee5afd4fb71a51ba7b13ebe25f4ccab62eb4ffbde1ae72e59c49734a'
    legacy = types.ModuleType('control.friends.legacy_metadata')
    legacy.__package__ = 'control.friends'
    exec(compile(source, '<pinned legacy contract>', 'exec'), legacy.__dict__)
    with pytest.raises(ValueError):
        legacy.validate(json.dumps(basic()))
    assert legacy.validate(json.dumps(report()))['schema'] == 1


def test_offline_revoke_lost_response_old_sample_and_payload_free_floor(setup):
    submit(setup, basic())
    revoked = report(epoch=2, sequence=2, operation='revoke')
    first = submit(setup, revoked)
    assert submit(setup, revoked) == first
    with pytest.raises(Rejected):
        submit(setup, basic(sequence=30))
    with pytest.raises(Rejected):
        submit(setup, basic(epoch=2, sequence=30))
    with sqlite3.connect(setup[2]) as connection:
        epoch, payload = connection.execute('SELECT epoch,payload FROM device_metadata').fetchone()
    assert epoch == 2 and payload == '{}'
    assert metadata.read_all(setup[2], setup[3][0])[0]['consent'] == 'revoked'


def test_basic_latest_only_expiry_preserves_mode_without_observations(setup):
    submit(setup, basic())
    setup[3][0] += metadata.RETENTION + 1
    metadata.prune(setup[2], setup[3][0])
    row, = metadata.read_all(setup[2], setup[3][0])
    assert row['processing_mode'] == metadata.BASIC_MODE and row['observations'] == {}
    assert row['consent'] == 'not_requested'


@pytest.mark.parametrize('revoke_first', [False, True])
def test_late_or_restored_v1_cannot_downgrade_basic_even_with_higher_epoch(setup, revoke_first):
    submit(setup, basic())
    if revoke_first:
        submit(setup, report(epoch=2, sequence=2, operation='revoke'))
    setup[3][0] += 60
    with pytest.raises(Rejected):
        submit(setup, report(epoch=3, sequence=99))
    row, = metadata.read_all(setup[2], setup[3][0])
    assert row['processing_mode'] == metadata.BASIC_MODE
    assert row['consent'] == ('revoked' if revoke_first else 'not_requested')


def test_delayed_first_sample_cannot_refresh_old_bytes_as_clock_skew(setup):
    setup[3][0] += metadata.RETENTION + 1
    submit(setup, basic())
    row, = metadata.read_all(setup[2], setup[3][0])
    assert row['observations'] == {}


def test_basic_future_clock_is_refused_not_renewed(setup):
    value = basic()
    value['observations']['profile']['sampled_at_ms'] += 600000
    with pytest.raises(ValueError):
        submit(setup, value)


def test_legacy_database_migration_preserves_pending_floor(tmp_path):
    path = tmp_path / 'legacy.sqlite'
    with sqlite3.connect(path) as connection:
        connection.execute('CREATE TABLE device_metadata(device TEXT PRIMARY KEY, epoch INTEGER, sequence INTEGER, digest TEXT, enabled INTEGER, received INTEGER, payload TEXT)')
        connection.execute('INSERT INTO device_metadata VALUES (?,?,?,?,?,?,?)', ('device', 7, 9, 'prior', 0, 1, '{}'))
    path.chmod(0o600)
    with metadata.store(path) as connection:
        transaction = metadata.MetadataTransaction(connection)
        assert transaction.supports_basic()
        with pytest.raises(Rejected):
            metadata.record(transaction, 'device', basic(epoch=7, sequence=10), 'changed', 999)
    row, = metadata.read_all(path, 999)
    assert row['consent_epoch'] == 7 and row['sequence'] == 9 and row['observations'] == {}
