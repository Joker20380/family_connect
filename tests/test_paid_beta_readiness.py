import copy
import json
import sqlite3

import pytest
from cryptography import x509

from control.friends import paid_beta
from control.friends.access import Access, Rejected
from control.friends.restricted_admin import publish_crl
from test_friends_restricted import configured, proof
from test_paid_beta import NOW, activated_device


@pytest.fixture
def paid_setup(tmp_path):
    service, device, now = configured(tmp_path, NOW)
    service.all_activated = True
    with service.access.db() as database:
        database.execute('UPDATE device_support SET platform=?,app_version=?,version_code=106,last_seen=? WHERE device=?',
            ('android', paid_beta.VERSION, now, device.reference))
        support = database.execute('SELECT support_id FROM device_support WHERE device=?', (device.reference,)).fetchone()[0]
    return service, device, support, now


def payment(setup, duration=600, event_id='payment-00000001'):
    service, _, support, now = setup
    with paid_beta.connection(service.access.path, write=True) as database:
        return paid_beta.apply_event(database, support, 'payment', event_id, 'synthetic-confirmation', now=now,
            period_start=now, paid_until=now + duration, apk_sha256=paid_beta.APK_SHA256)


def change(setup, action, **values):
    service, _, support, now = setup
    with paid_beta.connection(service.access.path, write=True) as database:
        return paid_beta.apply_event(database, support, action, action + '-00000001', 'synthetic-confirmation', now=now, **values)


@pytest.mark.parametrize('all_activated', [True, False])
@pytest.mark.parametrize('cohort', ['absent', 'empty', 'other'])
def test_non_cohort_readiness_is_byte_identical_to_legacy(paid_setup, tmp_path, monkeypatch, all_activated, cohort):
    service, device, _, now = paid_setup
    service.all_activated = all_activated
    clone = tmp_path / 'legacy.db'
    with sqlite3.connect(service.access.path) as source, sqlite3.connect(clone) as target:
        source.backup(target)
    with sqlite3.connect(clone) as database:
        database.execute('DROP TABLE paid_beta_subscriptions')
        database.execute('DROP TABLE paid_beta_events')
    legacy = copy.copy(service)
    legacy.access = Access(clone, clock=lambda: now)
    if cohort == 'absent':
        with sqlite3.connect(service.access.path) as database:
            database.execute('DROP TABLE paid_beta_subscriptions')
            database.execute('DROP TABLE paid_beta_events')
    elif cohort == 'other':
        other, support = activated_device(service.access)
        payment((service, other, support, now))
    monkeypatch.setattr('control.friends.restricted.secrets.token_bytes', lambda size: b'\x13' * size)
    monkeypatch.setattr(x509, 'random_serial_number', lambda: 123456789)
    legacy_challenge = legacy.challenge(device.public_identity, device.wireguard_public_key)
    current_challenge = service.challenge(device.public_identity, device.wireguard_public_key)
    assert current_challenge == legacy_challenge
    signed = device.prove_transport_key(current_challenge['challenge'])
    assert json.dumps(service.fetch(signed), separators=(',', ':')) == json.dumps(legacy.fetch(signed), separators=(',', ':'))
    with pytest.raises(Rejected):
        service.fetch(signed)


@pytest.mark.parametrize('state', ['active', 'trial', 'grace'])
def test_certificate_and_readiness_end_at_entitlement_boundary(paid_setup, state):
    service, device, support, now = paid_setup
    payment(paid_setup)
    until = now + 600
    if state == 'grace':
        until = now + 900
        change(paid_setup, 'grace', grace_until=until)
    elif state == 'trial':
        with paid_beta.connection(service.access.path, write=True) as database:
            database.execute("UPDATE paid_beta_subscriptions SET state='trial'")
    result = service.fetch(proof(service, device))
    certificate = x509.load_pem_x509_certificate(result['certificate'].encode())
    assert result['expires_at'] == int(certificate.not_valid_after_utc.timestamp()) == until
    assert support not in json.dumps(result)
    assert set(result) == {'version', 'device', 'challenge', 'issued_at', 'expires_at', 'revision', 'issuer',
                           'certificate', 'revocations', 'minimum_crl', 'directory'}
    service.access.clock = lambda: until
    with pytest.raises(Rejected):
        proof(service, device)
    assert not certificate.not_valid_before_utc.timestamp() <= until < certificate.not_valid_after_utc.timestamp()


def test_prior_long_certificate_is_not_returned_after_paid_enrollment(paid_setup):
    service, device, _, now = paid_setup
    original = service.fetch(proof(service, device))
    assert x509.load_pem_x509_certificate(original['certificate'].encode()).not_valid_after_utc.timestamp() > now + 600
    payment(paid_setup)
    current = service.fetch(proof(service, device))
    assert current['certificate'] != original['certificate']
    assert x509.load_pem_x509_certificate(current['certificate'].encode()).not_valid_after_utc.timestamp() == now + 600


def test_paid_certificate_capped_by_directory_and_existing_crypto(paid_setup):
    service, device, _, now = paid_setup
    payment(paid_setup, duration=7200)
    directory = json.loads(service.seed_source())
    from control.friends.restricted import iso
    directory['expires_at'] = iso(now + 500)
    service.seed_source = lambda: json.dumps(directory).encode()
    result = service.fetch(proof(service, device))
    assert result['expires_at'] == now + 500
    assert x509.load_pem_x509_certificate(result['certificate'].encode()).not_valid_after_utc.timestamp() == now + 500


@pytest.mark.parametrize('action', ['expire', 'revoke', 'time'])
def test_paid_decision_rechecked_between_challenge_and_fetch(paid_setup, action):
    service, device, _, now = paid_setup
    payment(paid_setup, duration=30)
    signed = proof(service, device)
    if action == 'time':
        service.access.clock = lambda: now + 30
    else:
        change(paid_setup, action)
    with pytest.raises(Rejected):
        service.fetch(signed)
    with pytest.raises(Rejected):
        proof(service, device)
    with service.access.db() as database:
        assert database.execute('SELECT count(*) FROM restricted_certificates').fetchone()[0] == 0


def test_reused_successful_proof_and_existing_activation_cannot_extend_cache(paid_setup):
    service, device, _, now = paid_setup
    payment(paid_setup, duration=30)
    signed = proof(service, device)
    saved = service.fetch(signed)
    with pytest.raises(Rejected):
        service.fetch(signed)
    service.access.clock = lambda: now + 30
    for operation in (lambda: service.fetch(signed), lambda: proof(service, device)):
        with pytest.raises(Rejected):
            operation()
    assert saved['expires_at'] == now + 30
    with service.access.db() as database:
        assert database.execute('SELECT count(*) FROM restricted_certificates').fetchone()[0] == 1
        assert database.execute('SELECT revoked FROM devices').fetchone()[0] == 0


def test_challenge_checks_server_time_after_transaction_wait(paid_setup):
    service, device, _, now = paid_setup
    payment(paid_setup, duration=30)
    times = iter((now, now + 30))
    service.access.clock = lambda: next(times)
    with pytest.raises(Rejected):
        proof(service, device)


@pytest.mark.parametrize('action', ['expire', 'revoke'])
def test_existing_crl_publisher_observes_paid_deny(paid_setup, tmp_path, action):
    service, device, _, _ = paid_setup
    payment(paid_setup)
    delivery = service.fetch(proof(service, device))
    certificate = x509.load_pem_x509_certificate(delivery['certificate'].encode())
    change(paid_setup, action)
    path = tmp_path / 'revocations.pem'
    publish_crl(service, path)
    crl = x509.load_pem_x509_crl(path.read_bytes())
    assert crl.get_revoked_certificate_by_serial_number(certificate.serial_number) is not None


def test_newer_authenticated106_ack_overrides_stale84_support_row(paid_setup):
    service, device, _, now = paid_setup
    with service.access.db() as database:
        database.execute("UPDATE device_support SET version_code=84,app_version='0.1.18-beta84',last_seen=?", (now - 60,))
        database.execute('INSERT INTO restricted_readiness_results(nonce,correlation,device,challenge_at,ack,ack_at) VALUES (?,?,?,?,?,?)',
            ('a' * 64, 'a' * 32, device.reference, now - 10,
             json.dumps(dict(app_version=paid_beta.VERSION, version_code=106)), now))
    payment(paid_setup)


@pytest.mark.parametrize('ack_offset,code', [(1, 84), (0, 84), (1, '106')])
def test_latest_or_conflicting_non106_observation_prevents_payment(paid_setup, ack_offset, code):
    service, device, _, now = paid_setup
    with service.access.db() as database:
        database.execute('INSERT INTO restricted_readiness_results(nonce,correlation,device,challenge_at,ack,ack_at) VALUES (?,?,?,?,?,?)',
            ('b' * 64, 'b' * 32, device.reference, now - 10,
             json.dumps(dict(app_version=paid_beta.VERSION, version_code=code)), now + ack_offset))
    with pytest.raises(paid_beta.PaidBetaError, match='ANDROID106_REQUIRED'):
        payment(paid_setup)
    with paid_beta.connection(service.access.path) as database:
        assert database.execute('SELECT count(*) FROM paid_beta_events').fetchone()[0] == 0
        assert database.execute('SELECT count(*) FROM paid_beta_subscriptions').fetchone()[0] == 0
