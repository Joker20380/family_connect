import concurrent.futures
import json
import re

import pytest

from control.friends import support_admin, support_ids
from control.friends.access import Access, Rejected
from control.friends.restricted import migrate
from device_identity.device import DeviceIdentity


@pytest.fixture
def access(tmp_path):
    value = Access(tmp_path / 'access.db', clock=lambda: 1000)
    value.initialize()
    migrate(value)
    return value


def proof(access, device, purpose, code=''):
    challenge = access.challenge(device.public_identity, device.wireguard_public_key, purpose, code)
    return device.prove_transport_key(challenge['challenge'])


def enroll(access):
    device = DeviceIdentity.generate()
    access.complete(proof(access, device, 'activate', access.invite()), 'activate')
    with access.db() as database:
        support = support_ids.registered(database, device.reference)
    return device, support


def request(access, device):
    return dict(proof=proof(access, device, 'support'), platform='android', app_version='0.1.18-beta59', version_code=59)


def original_rows(access):
    with access.db() as database:
        return {table: [tuple(row) for row in database.execute('SELECT * FROM ' + table + ' ORDER BY 1')]
                for table in ('devices', 'invites', 'restricted_grants')}


def test_backfill_stable_unique_preserves_all_existing_records(access):
    devices = [enroll(access)[0] for index in range(28)]
    with access.db() as database:
        database.execute('DROP TABLE device_support')
        for device in devices[:4]:
            database.execute('UPDATE devices SET revoked=1 WHERE device=?', (device.reference,))
        database.execute('INSERT INTO restricted_grants VALUES (?,?,?,?,0)', (devices[-1].reference, 'a' * 32, 3, 2000))
    before = original_rows(access)
    expected = dict(total=28, non_revoked=24, revoked=4, support_ids=28, platform_known=0, platform_unknown=28, version_known=0, version_unknown=28)
    assert support_ids.backfill(access) == expected
    with access.db() as database:
        identifiers = dict(database.execute('SELECT device,support_id FROM device_support'))
    assert len(set(identifiers.values())) == 28
    assert all(re.fullmatch(support_ids.PATTERN, value) for value in identifiers.values())
    with concurrent.futures.ThreadPoolExecutor(4) as pool:
        assert all(value == expected for value in pool.map(lambda unused: support_ids.backfill(access), range(8)))
    with access.db() as database:
        assert dict(database.execute('SELECT device,support_id FROM device_support')) == identifiers
    assert original_rows(access) == before


def test_delivery_never_allocates_a_missing_backfilled_id(access):
    device, support = enroll(access)
    with access.db() as database:
        database.execute('DELETE FROM device_support WHERE device=?', (device.reference,))
    before = original_rows(access)
    with pytest.raises(RuntimeError, match='Support inventory mismatch'):
        support_ids.request(access, request(access, device))
    with access.db() as database:
        assert database.execute('SELECT count(*) FROM device_support').fetchone()[0] == 0
    assert original_rows(access) == before


def test_random_collision_retries_without_changing_existing_id(access, monkeypatch):
    first, support = enroll(access)
    second, other = enroll(access)
    with access.db() as database:
        database.execute('DELETE FROM device_support WHERE device=?', (second.reference,))
    characters = iter(support.replace('FC-', '').replace('-', '') + other.replace('FC-', '').replace('-', ''))
    monkeypatch.setattr(support_ids.secrets, 'choice', lambda alphabet: next(characters))
    with access.db() as database:
        assert support_ids.registered(database, second.reference) == other
        assert support_ids.registered(database, first.reference) == support


def test_support_request_requires_existing_single_use_device_proof(access):
    device, support = enroll(access)
    before = original_rows(access)
    value = request(access, device)
    assert support_ids.request(access, value) == dict(schema=1, device_support_id=support)
    with pytest.raises(Rejected):
        support_ids.request(access, value)
    with pytest.raises(Rejected):
        support_ids.request(access, dict(value, proof=support))
    with pytest.raises(Rejected):
        support_ids.request(access, dict(value, proof=proof(access, device, 'status')))
    with pytest.raises(Rejected):
        proof(access, DeviceIdentity.generate(), 'support')
    safe = support_ids.lookup(access, support.lower(), [])
    assert safe['platform'] == 'android' and safe['version_code'] == 59 and safe['last_seen'] == 1000
    assert safe['active'] and not safe['field_admission']
    assert safe['family_state'] == 'NOT_PROVISIONED'
    assert device.reference not in json.dumps(safe)
    assert original_rows(access) == before


@pytest.mark.parametrize('field,value', [('platform', 'secret-SSID'), ('app_version', 'https://room/private'), ('version_code', True), ('version_code', 0)])
def test_rejects_unbounded_metadata(access, field, value):
    device, support = enroll(access)
    with pytest.raises(Rejected):
        support_ids.request(access, dict(request(access, device), **{field: value}))
    assert support_ids.lookup(access, support, [])['platform'] is None


@pytest.mark.parametrize('table', ['devices', 'invites'])
def test_support_rejects_revoked_registration(access, table):
    device, support = enroll(access)
    value = request(access, device)
    with access.db() as database:
        database.execute('UPDATE ' + table + ' SET revoked=1 WHERE device=?', (device.reference,))
    with pytest.raises(Rejected):
        support_ids.request(access, value)
    assert not support_ids.lookup(access, support, [])['active']


def test_receipt_backfill_never_infers_platform(access):
    device, support = enroll(access)
    with access.db() as database:
        database.execute("INSERT INTO restricted_readiness_results(correlation,nonce,challenge_at,device,ack,ack_at,expires) VALUES ('test','nonce',998,?,?,?,?)",
                         (device.reference, json.dumps(dict(app_version='0.1.18-canary58-physical', version_code=58, result='READY')), 999, 1001))
    counts = support_ids.backfill(access)
    assert counts['platform_unknown'] == counts['version_known'] == 1
    assert support_ids.lookup(access, support, [])['restricted_readiness'] == 'READY'
    support_ids.request(access, request(access, device))
    support_ids.backfill(access)
    assert support_ids.lookup(access, support, [])['version_code'] == 59
    access.clock = lambda: 1002
    assert support_ids.lookup(access, support, [])['restricted_readiness'] == 'EXPIRED'


@pytest.mark.parametrize('devices', [['*'], ['a' * 32] * 2, [str(index) * 32 for index in range(4)]])
def test_operator_rejects_wildcard_duplicate_or_wide_cohort(tmp_path, devices):
    path = tmp_path / 'admission.json'
    path.write_text(json.dumps(dict(devices=devices)))
    with pytest.raises(ValueError):
        support_admin.admission(path)


def test_operator_uses_real_grants_and_crl_and_safe_audit(tmp_path, monkeypatch):
    from tests.test_friends_restricted import configured
    service, owner, now = configured(tmp_path, 1800000000)
    access = service.access
    path = tmp_path / 'admission.json'
    path.write_text(json.dumps(dict(devices=[owner.reference])))
    monkeypatch.setattr(support_admin, 'from_env', lambda unused: service)
    second, support = enroll(access)
    assert support_admin.change(access, path, support, True, now + 3600)['field_admission']
    assert (tmp_path / 'revocations.pem').is_file()
    assert support_ids.lookup(access, support, support_admin.admission(path))['family_state'] == 'ACTIVE'
    assert not support_admin.change(access, path, support, False)['field_admission']
    assert support_ids.lookup(access, support, support_admin.admission(path))['family_state'] == 'REVOKED'
    assert support_admin.admission(path) == [owner.reference]
    with access.db() as database:
        audit = [dict(row) for row in database.execute('SELECT * FROM field_support_audit')]
    assert len(audit) == 2 and all(row['outcome'] == 'APPLIED' for row in audit)
    assert second.reference not in json.dumps(audit) and owner.reference not in json.dumps(audit)


def test_operator_publication_failure_does_not_admit(tmp_path, monkeypatch):
    from tests.test_friends_restricted import configured
    service, owner, now = configured(tmp_path, 1800000000)
    path = tmp_path / 'admission.json'
    path.write_text(json.dumps(dict(devices=[owner.reference])))
    monkeypatch.setattr(support_admin, 'from_env', lambda unused: service)
    def fail(*args):
        raise RuntimeError('private issuer detail')
    monkeypatch.setattr(support_admin, 'publish_crl', fail)
    device, support = enroll(service.access)
    with pytest.raises(RuntimeError, match='FIELD operation incomplete'):
        support_admin.change(service.access, path, support, True, now + 3600)
    assert support_admin.admission(path) == [owner.reference]
    assert support_ids.lookup(service.access, support, [owner.reference])['family_state'] == 'REVOKED'
    with service.access.db() as database:
        assert database.execute('SELECT outcome FROM field_support_audit').fetchone()[0] == 'INCOMPLETE'


def test_operator_retains_owner_and_caps_admission(access, tmp_path):
    pairs = [enroll(access) for index in range(4)]
    path = tmp_path / 'admission.json'
    path.write_text(json.dumps(dict(devices=[pairs[0][0].reference])))
    with pytest.raises(ValueError, match='owner'):
        support_admin.change(access, path, pairs[0][1], False)
    path.write_text(json.dumps(dict(devices=[device.reference for device, support in pairs[:3]])))
    with pytest.raises(ValueError, match='limit'):
        support_admin.change(access, path, pairs[3][1], True, 2000)


def test_operator_artifact_is_reproducible_and_isolated(tmp_path):
    import subprocess
    import sys
    from scripts.package_support_operator import build
    first, second = tmp_path / 'first.pyz', tmp_path / 'second.pyz'
    assert build(first) == build(second)
    result = subprocess.run([sys.executable, '-I', str(first), '--help'], cwd=tmp_path, capture_output=True, text=True, check=True)
    assert 'enable-field' in result.stdout and 'disable-field' in result.stdout
