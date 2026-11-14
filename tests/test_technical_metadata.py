import hashlib
import json
import sqlite3

import pytest

from control.friends import technical_metadata as metadata
from control.friends.access import Access, Rejected
from control.friends.referrals import RateLimited
from test_support_ids import enroll, proof


@pytest.fixture
def setup(tmp_path):
    clock = [1800000000]
    access = Access(tmp_path / 'access.db', clock=lambda: clock[0])
    access.initialize()
    device, support = enroll(access)
    return access, device, tmp_path / 'technical.sqlite', clock


def report(epoch=1, sequence=1, operation='sample'):
    groups = {
        'profile': dict(manufacturer='Google', model='Pixel test', android_version='15',
                        api_level=35, app_version='test-unpublished', version_code=125),
        'network': dict(kind='WIFI', scope='default_network'),
        'mobile': dict(sim_operator=None, registered_operator=None, radio='UNKNOWN',
                       sim_reason='no_sim', registered_reason='no_registered_network', radio_reason='permission_not_granted'),
        'session': dict(preference='AUTO', attempt='TCP', transport='TCP', gateway='nl-amsterdam-1', state='CONNECTED'),
        'diagnostic': dict(error='NONE', error_at_ms=None, readiness='UNKNOWN'),
    }
    sources = dict(profile='android_build_package', network='android_default_network',
                   mobile='android_telephony_public', session='connection_service', diagnostic='connection_terminal')
    observations = {name: dict(sampled_at_ms=1800000000000, age_ms=0, source=sources[name],
                              status='partial' if name in ('mobile', 'diagnostic') else 'available',
                              reason='not_observed' if name in ('mobile', 'diagnostic') else 'none', values=values)
                    for name, values in groups.items()} if operation == 'sample' else {}
    return dict(schema=1, report_id=f'{epoch:016x}{sequence:016x}', consent_epoch=epoch,
                sequence=sequence, operation=operation, observations=observations)


def submit(setup, value):
    access, device, path, clock = setup
    raw = json.dumps(value, separators=(',', ':'))
    purpose = 'technical-metadata-v1:' + hashlib.sha256(raw.encode()).hexdigest()
    return metadata.request(access, path, dict(report=raw, proof=proof(access, device, purpose)))


def test_real_identity_latest_only_idempotent_and_private(setup):
    receipt = submit(setup, report())
    assert receipt == submit(setup, report())
    assert receipt['received_at'] == setup[3][0]
    assert setup[2].stat().st_mode & 0o777 == 0o600
    row = metadata.read_all(setup[2], setup[3][0])[0]
    assert row['device'] == setup[1].reference
    assert row['observations']['profile']['values']['model'] == 'Pixel test'
    setup[3][0] += 60
    submit(setup, report(sequence=2))
    with sqlite3.connect(setup[2]) as database:
        assert database.execute('SELECT count(*) FROM device_metadata').fetchone()[0] == 1


def test_proof_binds_exact_bytes_not_just_identity(setup):
    access, device, path, clock = setup
    raw = json.dumps(report())
    signed = proof(access, device, 'technical-metadata-v1:' + hashlib.sha256(raw.encode()).hexdigest())
    changed = raw.replace('Pixel test', 'Different model')
    with pytest.raises(Rejected):
        metadata.request(access, path, dict(report=changed, proof=signed))
    assert not path.exists()
    metadata.request(access, path, dict(report=raw, proof=signed))
    with pytest.raises(Rejected):
        metadata.request(access, path, dict(report=raw, proof=signed))


def test_other_identity_cannot_write_the_first_devices_row(setup):
    submit(setup, report())
    other, support = enroll(setup[0])
    submit((setup[0], other, setup[2], setup[3]), report())
    assert {row['device'] for row in metadata.read_all(setup[2], setup[3][0])} == {setup[1].reference, other.reference}


def test_conflicting_id_old_sequence_and_id_reuse_rejected(setup):
    submit(setup, report())
    changed = report()
    changed['observations']['profile']['values']['model'] = 'Other'
    with pytest.raises(Rejected):
        submit(setup, changed)
    setup[3][0] += 60
    submit(setup, report(sequence=2))
    with pytest.raises(Rejected):
        submit(setup, report())
    reused = report(sequence=3)
    reused['report_id'] = report()['report_id']
    with pytest.raises(ValueError):
        submit(setup, reused)


def test_revoke_bypasses_rate_limit_and_never_resurrects_after_restart_or_ttl(setup):
    submit(setup, report())
    with pytest.raises(RateLimited):
        submit(setup, report(sequence=2))
    revoked = submit(setup, report(epoch=2, sequence=2, operation='revoke'))
    assert revoked['consent'] == 'revoked'
    metadata.prune(setup[2], setup[3][0] + 10 * metadata.RETENTION)
    assert metadata.read_all(setup[2], setup[3][0])[0]['observations'] == {}
    for delayed in (report(sequence=100), report(epoch=2, sequence=3)):
        with pytest.raises(Rejected):
            submit(setup, delayed)
    setup[3][0] += 60
    submit(setup, report(epoch=3, sequence=3))
    assert metadata.read_all(setup[2], setup[3][0])[0]['consent'] == 'enabled'


def test_revoke_before_delayed_first_report(setup):
    submit(setup, report(epoch=2, operation='revoke'))
    with pytest.raises(Rejected):
        submit(setup, report())


def test_expiry_is_independent_for_each_group_not_refreshed_by_new_profile(setup):
    value = report()
    value['observations']['network']['age_ms'] = (metadata.RETENTION - 10) * 1000
    value['observations']['network']['sampled_at_ms'] -= (metadata.RETENTION - 10) * 1000
    submit(setup, value)
    setup[3][0] += 11
    assert 'network' not in metadata.read_all(setup[2], setup[3][0])[0]['observations']
    assert 'profile' in metadata.read_all(setup[2], setup[3][0])[0]['observations']
    metadata.prune(setup[2], setup[3][0])
    with sqlite3.connect(setup[2]) as database:
        assert 'network' not in json.loads(database.execute('SELECT payload FROM device_metadata').fetchone()[0])
    setup[3][0] += metadata.RETENTION
    metadata.prune(setup[2], setup[3][0])
    assert metadata.read_all(setup[2], setup[3][0])[0]['observations'] == {}
    assert submit(setup, value)['received_at'] == 1800000000
    assert metadata.read_all(setup[2], setup[3][0])[0]['observations'] == {}


@pytest.mark.parametrize('offset', [-864000000, 864000000])
def test_wrong_client_clock_does_not_override_received_or_monotonic_age(setup, offset):
    value = report()
    for observation in value['observations'].values():
        observation['sampled_at_ms'] += offset
        observation['age_ms'] = 60000
    submit(setup, value)
    observation = metadata.read_all(setup[2], setup[3][0])[0]['observations']['profile']
    assert observation['clock_status'] == 'clock_skew'
    assert observation['received_at'] == setup[3][0]
    assert observation['expires_at'] == setup[3][0] + metadata.RETENTION - 60


@pytest.mark.parametrize('field,value', [('schema', True), ('sequence', True), ('consent_epoch', -1),
    ('sequence', 2**53), ('report_id', 'a' * 32), ('operation', 'enable'), ('observations', []),
    ('phone', 'forbidden'), ('ip', '203.0.113.1')])
def test_strict_top_level(setup, field, value):
    candidate = report()
    candidate[field] = value
    with pytest.raises(ValueError):
        submit(setup, candidate)
    assert not setup[2].exists()


@pytest.mark.parametrize('mutation', ['oversize', 'unknown', 'control', 'bool', 'underlay', 'inactive_transport', 'missing_reason'])
def test_strict_observation_contract(setup, mutation):
    value = report()
    groups = value['observations']
    if mutation == 'oversize': groups['profile']['values']['model'] = 'a' * 101
    if mutation == 'unknown': groups['profile']['values']['imei'] = 'forbidden'
    if mutation == 'control': groups['profile']['values']['model'] = 'model\nprivate log'
    if mutation == 'bool': groups['profile']['values']['api_level'] = True
    if mutation == 'underlay': groups['network']['values']['scope'] = 'session_underlay'
    if mutation == 'inactive_transport': groups['session']['values']['state'] = 'CONNECTING'
    if mutation == 'missing_reason': groups['mobile']['values']['radio_reason'] = 'none'
    with pytest.raises(ValueError):
        submit(setup, value)


def test_duplicate_json_and_size_limits():
    with pytest.raises(ValueError):
        metadata.validate('{"schema":1,"schema":1}')
    with pytest.raises(ValueError):
        metadata.validate(' ' * (metadata.MAX_REPORT + 1))


def test_bounded_store_keeps_existing_device_revoke_possible(setup, monkeypatch):
    monkeypatch.setattr(metadata, 'MAX_DEVICES', 1)
    submit(setup, report())
    other, support = enroll(setup[0])
    with pytest.raises(RateLimited):
        submit((setup[0], other, setup[2], setup[3]), report())
    submit(setup, report(epoch=2, operation='revoke'))
    assert metadata.read_all(setup[2], setup[3][0])[0]['observations'] == {}


def test_unknown_optional_values_are_explicit(setup):
    value = report()
    groups = value['observations']
    for group in groups.values():
        group['status'] = 'unavailable'
        group['reason'] = 'service_unavailable'
    groups['profile']['values']['model'] = None
    submit(setup, value)
    assert metadata.read_all(setup[2], setup[3][0])[0]['observations']['profile']['values']['model'] is None
