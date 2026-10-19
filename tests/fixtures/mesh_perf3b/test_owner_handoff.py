import concurrent.futures
import importlib.util
import json
import os
from pathlib import Path
import sys
import threading

import pytest


ROOT = Path(__file__).resolve().parents[3]
API = ROOT / 'state-client-build/mesh-perf-3b/api'
sys.path.insert(0, str(API))
from control.friends import owner_handoff as handoff
from control.friends.restricted import Rejected, iso
from device_identity.device import DeviceIdentity

assert Path(handoff.__file__).is_relative_to(API)
spec = importlib.util.spec_from_file_location('baseline_fixtures', ROOT / 'tests/test_friends_restricted.py')
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)
BOOT = 'c' * 32


def test_inflight_common_read_before_arm_cannot_leak_return(setup):
    service, owner, now, first, canary, returning = setup
    captured, release = threading.Event(), threading.Event()
    proof = fixtures.proof(service, owner)

    def delayed_common():
        raw = json.dumps(returning).encode()
        captured.set()
        assert release.wait(3)
        return raw

    service.seed_source = delayed_common
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(service.fetch, proof)
        try:
            assert captured.wait(3)
            activate(setup)
        finally:
            release.set()
        selected = pending.result(timeout=3)
    assert selected['directory'] == canary
    assert handoff.preserves(handoff.floor(selected), handoff.floor(first))


def test_inflight_common_read_before_return_obeys_return_phase(setup):
    service, owner, now, first, canary, returning = setup
    activate(setup)
    middle = service.fetch(fixtures.proof(service, owner))
    captured, release = threading.Event(), threading.Event()
    proof = fixtures.proof(service, owner)

    def delayed_common():
        captured.set()
        assert release.wait(3)
        return json.dumps(first['directory']).encode()

    service.seed_source = delayed_common
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(service.fetch, proof)
        try:
            assert captured.wait(3)
            with service.access.db() as database:
                handoff.return_only(database, owner.reference, 'test-operation')
        finally:
            release.set()
        selected = pending.result(timeout=3)
    assert selected['directory'] == returning
    assert handoff.preserves(handoff.floor(selected), handoff.floor(middle))


def test_initial_return_import_prevents_older_canary_arm(setup):
    service, owner, now, first, canary, returning = setup
    with service.access.db() as database:
        database.execute('UPDATE restricted_owner_handoff SET floor=NULL,fetch_id=NULL')
    service.seed_source = lambda: json.dumps(returning).encode()
    observed = service.fetch(fixtures.proof(service, owner))
    assert observed['directory'] == returning
    with pytest.raises(ValueError):
        activate(setup)
    assert phase(setup) == 'PREPARED'


@pytest.fixture
def setup(tmp_path, monkeypatch):
    service, owner, now = fixtures.configured(tmp_path, 1800000000, directory_lifetime=10800)
    monkeypatch.setenv('INVOCATION_ID', BOOT)
    with service.access.db() as database:
        handoff.migrate(database)
        handoff.prepare(database, 'test-operation', owner.reference, 'a' * 32, 'b' * 32, now + 2400, now)
    first = service.fetch(fixtures.proof(service, owner))
    canary = json.loads(json.dumps(first['directory']))
    canary['issued_at'] = iso(now)
    canary['seeds'][0]['join_url'] = 'https://telemost.yandex.ru/j/fixture-canary'
    returning = json.loads(json.dumps(first['directory']))
    returning['issued_at'] = iso(now + 10)
    returning['seeds'][0]['join_url'] = 'https://telemost.yandex.ru/j/fixture-new-production'
    service.access.clock = lambda: now + 10
    return service, owner, now + 10, first, canary, returning


def activate(setup):
    service, owner, now, first, canary, returning = setup
    with service.access.db() as database:
        handoff.arm(database, owner.reference, 'test-operation', canary, returning, BOOT, now)


def phase(setup):
    service, owner, *_ = setup
    with service.access.db() as database:
        return handoff.read(database, owner.reference)['phase']


def other(service, now):
    device = DeviceIdentity.generate()
    invite = service.access.invite()
    challenge = service.access.challenge(device.public_identity, device.wireguard_public_key, 'activate', invite)
    service.access.complete(device.prove_transport_key(challenge['challenge']), 'activate')
    with service.access.db() as database:
        database.execute('INSERT INTO restricted_grants VALUES (?,?,?,?,0)', (device.reference, 'a' * 32, 1, now + 86400))
    return device


def test_roundtrip_frozen_prepare_and_current_cleanup(setup):
    service, owner, now, first, canary, returning = setup
    assert service.fetch(fixtures.proof(service, owner))['directory'] == first['directory']
    activate(setup)
    middle = service.fetch(fixtures.proof(service, owner))
    assert middle['directory'] == canary
    with service.access.db() as database:
        handoff.return_only(database, owner.reference, 'test-operation')
    last = service.fetch(fixtures.proof(service, owner))
    assert last['directory'] == returning
    assert handoff.preserves(handoff.floor(middle), handoff.floor(first))
    assert handoff.preserves(handoff.floor(last), handoff.floor(middle))
    assert not handoff.preserves(handoff.floor(first), handoff.floor(middle))
    with service.access.db() as database:
        with pytest.raises(ValueError):
            handoff.cleanup(database, owner.reference, 'test-operation', first)
    service.seed_source = lambda: json.dumps(returning).encode()
    common = service.fetch(fixtures.proof(service, owner))
    with service.access.db() as database:
        handoff.cleanup(database, owner.reference, 'test-operation', common)
    assert phase(setup) == 'CLEANED'
    assert service.fetch(fixtures.proof(service, owner))['directory'] == returning


def test_old_return_and_equal_time_different_route_cannot_arm(setup):
    service, owner, now, first, canary, returning = setup
    for bad in [first['directory'], dict(returning, issued_at=canary['issued_at'])]:
        with service.access.db() as database:
            with pytest.raises(ValueError):
                handoff.arm(database, owner.reference, 'test-operation', canary, bad, BOOT, now)
    assert phase(setup) == 'PREPARED'


@pytest.mark.parametrize('reason', ['restart', 'expiry'])
def test_restart_or_expiry_returns_and_cannot_rearm(setup, monkeypatch, reason):
    service, owner, now, first, canary, returning = setup
    activate(setup)
    service.fetch(fixtures.proof(service, owner))
    if reason == 'restart':
        monkeypatch.setenv('INVOCATION_ID', 'd' * 32)
    else:
        service.access.clock = lambda: now + 2400
    assert service.fetch(fixtures.proof(service, owner))['directory'] == returning
    assert phase(setup) == 'RETURN'
    monkeypatch.setenv('INVOCATION_ID', BOOT)
    with service.access.db() as database:
        with pytest.raises(ValueError):
            handoff.arm(database, owner.reference, 'test-operation', canary, returning, BOOT, now)


def test_nonowner_unchanged_with_broken_canary(setup):
    service, owner, now, first, canary, returning = setup
    ordinary = other(service, now)
    activate(setup)
    with service.access.db() as database:
        database.execute('UPDATE restricted_owner_handoff SET canary=?', ('{}',))
    assert service.fetch(fixtures.proof(service, ordinary))['directory'] == first['directory']
    with pytest.raises(ValueError):
        service.fetch(fixtures.proof(service, owner))


@pytest.mark.parametrize('failure', ['revoked', 'expired', 'wrong-family', 'wrong-key', 'replay', 'revoked-certificate'])
def test_authorization_precedes_route(setup, failure):
    service, owner, now, first, canary, returning = setup
    activate(setup)
    proof = fixtures.proof(service, owner)
    with service.access.db() as database:
        if failure == 'revoked':
            database.execute('UPDATE devices SET revoked=1 WHERE device=?', (owner.reference,))
        elif failure == 'expired':
            database.execute('UPDATE restricted_grants SET expires=?', (now - 1,))
        elif failure == 'wrong-family':
            database.execute('UPDATE restricted_grants SET family=?', ('e' * 32,))
    if failure == 'wrong-key':
        proof = DeviceIdentity.generate().prove_transport_key(proof['challenge'])
    elif failure == 'replay':
        service.fetch(proof)
    elif failure == 'revoked-certificate':
        from cryptography import x509
        from cryptography.hazmat.primitives.serialization import Encoding
        from control.friends.restricted import utc
        certificate = x509.load_pem_x509_certificate(first['certificate'].encode())
        old = x509.load_pem_x509_crl(service.crl_source())
        crl = (x509.CertificateRevocationListBuilder().issuer_name(old.issuer).last_update(utc(now-1))
               .next_update(utc(now+3500)).add_extension(x509.CRLNumber(2), False)
               .add_revoked_certificate(x509.RevokedCertificateBuilder().serial_number(certificate.serial_number)
                                       .revocation_date(utc(now-1)).build()).sign(service.signing_key, None))
        service.crl_source = lambda: crl.public_bytes(Encoding.PEM)
    with pytest.raises(ValueError):
        service.fetch(proof)
    assert phase(setup) == 'ACTIVE'


def test_concurrent_same_proof_once_and_repeated_fetch(setup):
    service, owner, *_ = setup
    activate(setup)
    proof = fixtures.proof(service, owner)
    def fetch():
        try:
            return service.fetch(proof)['directory']
        except Rejected:
            return None
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as workers:
        results = list(workers.map(lambda unused: fetch(), range(2)))
    assert sum(value is not None for value in results) == 1
    assert all(service.fetch(fixtures.proof(service, owner))['directory'] == setup[4] for unused in range(5))


def test_client_cannot_self_select_and_reply_not_cached(setup):
    import io
    import friends_http
    service, owner, *_ = setup
    activate(setup)
    proof = fixtures.proof(service, owner)
    proof['canary'] = True
    with pytest.raises(ValueError):
        service.fetch(proof)
    handler = object.__new__(friends_http.Handler)
    headers = []
    handler.send_response = lambda code: None
    handler.send_header = lambda name, value: headers.append((name, value))
    handler.end_headers = lambda: None
    handler.wfile = io.BytesIO()
    handler.reply(200, {'test': True})
    assert ('Cache-Control', 'no-store') in headers


def test_future_publication_during_prepare_does_not_advance_floor(setup):
    service, owner, now, first, canary, returning = setup
    service.seed_source = lambda: json.dumps(returning).encode()
    with pytest.raises(ValueError):
        service.fetch(fixtures.proof(service, owner))
    activate(setup)
    assert service.fetch(fixtures.proof(service, owner))['directory'] == canary


def test_failed_transaction_does_not_commit_canary_issue(setup):
    service, owner, now, first, canary, returning = setup
    with pytest.raises(RuntimeError):
        with service.access.db() as database:
            handoff.arm(database, owner.reference, 'test-operation', canary, returning, BOOT, now)
            raise RuntimeError('fixture interruption')
    assert phase(setup) == 'PREPARED'


def test_rotated_common_return_after_saved_view_expiry(setup):
    service, owner, now, first, canary, returning = setup
    activate(setup)
    service.fetch(fixtures.proof(service, owner))
    with service.access.db() as database:
        handoff.return_only(database, owner.reference, 'test-operation')
        saved = dict(returning, expires_at=iso(now - 1))
        database.execute('UPDATE restricted_owner_handoff SET return_view=?', (json.dumps(saved),))
    current = dict(returning, issued_at=iso(now + 1))
    service.access.clock = lambda: now + 1
    service.seed_source = lambda: json.dumps(current).encode()
    assert service.fetch(fixtures.proof(service, owner))['directory'] == current


def test_missing_invocation_returns_without_optional_selector(setup, monkeypatch):
    service, owner, now, first, canary, returning = setup
    activate(setup)
    service.fetch(fixtures.proof(service, owner))
    monkeypatch.delenv('INVOCATION_ID')
    assert service.fetch(fixtures.proof(service, owner))['directory'] == returning


def test_interrupted_owner_state_blocks_only_owner(setup):
    service, owner, now, first, canary, returning = setup
    ordinary = other(service, now)
    activate(setup)
    with service.access.db() as database:
        database.execute('UPDATE restricted_owner_handoff SET phase=?,return_view=?', ('RETURN', '{}'))
    with pytest.raises((ValueError, KeyError)):
        service.fetch(fixtures.proof(service, owner))
    assert service.fetch(fixtures.proof(service, ordinary))['directory'] == first['directory']


def test_expired_challenge_cannot_change_owner_state(setup):
    service, owner, now, first, canary, returning = setup
    activate(setup)
    proof = fixtures.proof(service, owner)
    service.access.clock = lambda: now + 1000
    with pytest.raises(ValueError):
        service.fetch(proof)
    assert phase(setup) == 'ACTIVE'
