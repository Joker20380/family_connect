import base64
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from control.product.api import create_app
from control.product.store import EnrollmentRejected, ProductStore
from device_identity.device import DeviceIdentity


@pytest.fixture
def setup(tmp_path):
    clock = [1000]
    store = ProductStore(tmp_path / 'product.db', clock=lambda: clock[0])
    store.migrate()
    entitlement = store.create_entitlement(expires_at=10000)
    invitation = store.create_invitation(entitlement['entitlement_id'], expires_at=9000, max_uses=5)
    return store, clock, entitlement, invitation


def proof_for(store, invitation, device=None):
    device = device or DeviceIdentity.generate()
    challenge = store.challenge(invitation_token=invitation['invitation_token'],
                                public_identity=device.public_identity,
                                wireguard_public_key=device.wireguard_public_key)
    return device, device.prove_transport_key(challenge['challenge'])


def counts(store):
    with sqlite3.connect(store.path) as db:
        return {table: db.execute(f'SELECT count(*) FROM {table}').fetchone()[0]
                for table in ('devices', 'device_entitlements', 'transport_keys')}


def test_migration_is_idempotent_and_enrollment_survives_restart(setup):
    store, clock, entitlement, invite = setup
    device, proof = proof_for(store, invite)
    enrolled = store.enroll(proof)
    store.migrate()
    restarted = ProductStore(store.path, clock=lambda: clock[0])
    authorization = restarted.authorization(enrolled['device_identity'])
    assert authorization['entitlement_id'] == entitlement['entitlement_id']
    assert authorization['wireguard_public_key'] == device.wireguard_public_key
    assert counts(store) == dict(devices=1, device_entitlements=1, transport_keys=1)


def test_proof_is_single_use_and_does_not_consume_extra_invitation_use(setup):
    store, _, _, invite = setup
    _, proof = proof_for(store, invite)
    store.enroll(proof)
    with pytest.raises(EnrollmentRejected):
        store.enroll(proof)
    with sqlite3.connect(store.path) as db:
        assert db.execute('SELECT uses FROM invitations').fetchone()[0] == 1
        assert db.execute('SELECT count(*) FROM product_audit WHERE event="device_enrolled"').fetchone()[0] == 1


@pytest.mark.parametrize('attack', ['expired', 'wrong_identity', 'wrong_key', 'bad_signature',
                                    'revoked_invite', 'revoked_entitlement', 'expired_entitlement'])
def test_failed_registration_has_no_partial_writes(setup, attack):
    store, clock, entitlement, invite = setup
    _, proof = proof_for(store, invite)
    other = DeviceIdentity.generate()
    if attack == 'expired':
        clock[0] = 1120
    elif attack == 'wrong_identity':
        proof = other.prove_transport_key(proof['challenge'])
    elif attack == 'wrong_key':
        proof['wireguard_public_key'] = other.wireguard_public_key
    elif attack == 'bad_signature':
        proof['signature'] = base64.b64encode(bytes(64)).decode()
    elif attack == 'revoked_invite':
        store.revoke_invitation(invite['invitation_id'])
    elif attack == 'revoked_entitlement':
        store.revoke_entitlement(entitlement['entitlement_id'])
    else:
        clock[0] = 10000
    with pytest.raises(EnrollmentRejected):
        store.enroll(proof)
    assert counts(store) == dict(devices=0, device_entitlements=0, transport_keys=0)


def test_valid_signature_cannot_replace_key_bound_at_challenge(setup):
    store, _, _, invite = setup
    device, proof = proof_for(store, invite)
    # Same permanent identity with a different, independently generated WG key.
    replacement = DeviceIdentity(device._identity, DeviceIdentity.generate()._wireguard_key)
    swapped = replacement.prove_transport_key(proof['challenge'])
    with pytest.raises(EnrollmentRejected):
        store.enroll(swapped)
    assert store.enroll(proof)['device_identity'] == device.reference


def test_revocation_is_independent_and_no_implicit_reactivation(setup):
    store, _, _, invite = setup
    first, proof = proof_for(store, invite)
    store.enroll(proof)
    second, proof = proof_for(store, invite)
    store.enroll(proof)
    store.revoke_device(first.reference)
    with pytest.raises(EnrollmentRejected):
        store.authorization(first.reference)
    assert store.authorization(second.reference)['device_identity'] == second.reference
    _, proof = proof_for(store, invite, first)
    with pytest.raises(EnrollmentRejected):
        store.enroll(proof)


def test_no_cross_family_move_or_shared_transport_key(setup):
    store, _, _, invite = setup
    first, proof = proof_for(store, invite)
    store.enroll(proof)
    family2 = store.create_entitlement(expires_at=10000)
    invitation2 = store.create_invitation(family2['entitlement_id'], expires_at=9000)
    _, proof = proof_for(store, invitation2, first)
    with pytest.raises(EnrollmentRejected):
        store.enroll(proof)
    shared_key = DeviceIdentity(DeviceIdentity.generate()._identity, first._wireguard_key)
    _, proof = proof_for(store, invitation2, shared_key)
    with pytest.raises(EnrollmentRejected):
        store.enroll(proof)
    assert counts(store)['devices'] == 1


def test_concurrent_proof_replay_has_exactly_one_winner(setup):
    store, _, _, invite = setup
    _, proof = proof_for(store, invite)
    def enroll(_):
        try:
            return store.enroll(proof)
        except EnrollmentRejected:
            return None
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(enroll, range(8)))
    assert sum(result is not None for result in results) == 1
    assert counts(store)['devices'] == 1


@pytest.mark.parametrize('limit_kind', ['invitation', 'family'])
def test_concurrent_capacity_cannot_be_exceeded(setup, limit_kind):
    store, _, entitlement, _ = setup
    if limit_kind == 'family':
        entitlement = store.create_entitlement(expires_at=10000, device_limit=1)
    invite = store.create_invitation(entitlement['entitlement_id'], expires_at=9000,
                                     max_uses=1 if limit_kind == 'invitation' else 5)
    proofs = [proof_for(store, invite)[1] for _ in range(4)]
    def enroll(proof):
        try:
            return store.enroll(proof)
        except EnrollmentRejected:
            return None
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(enroll, proofs))
    assert sum(result is not None for result in results) == 1
    assert counts(store)['devices'] == 1


def test_challenge_limits_pruning_and_hash_only_storage(setup):
    store, clock, _, invite = setup
    device, proof = proof_for(store, invite)
    for _ in range(15):
        proof_for(store, invite)
    with pytest.raises(EnrollmentRejected):
        proof_for(store, invite)
    with sqlite3.connect(store.path) as db:
        dump = '\n'.join(db.iterdump())
    for secret in [invite['invitation_token'], proof['challenge'],
                   base64.b64encode(device._identity.get_private_key()).decode(),
                   base64.b64encode(device._wireguard_key.private_bytes_raw()).decode()]:
        assert secret not in dump
    clock[0] = 1120
    assert store.prune_challenges() == 16
    proof_for(store, invite)
    with pytest.raises(EnrollmentRejected):
        store.enroll(proof)


def test_http_registration_and_errors_do_not_echo_sensitive_input(setup):
    store, _, _, invite = setup
    device = DeviceIdentity.generate()
    with TestClient(create_app(store)) as client:
        response = client.post('/v2/registration/challenge', json=dict(
            invitation_token=invite['invitation_token'], public_identity=device.public_identity,
            wireguard_public_key=device.wireguard_public_key))
        assert response.status_code == 200
        assert response.headers['cache-control'] == 'no-store'
        proof = device.prove_transport_key(response.json()['challenge'])
        response = client.post('/v2/registration/complete', json=proof)
        assert response.status_code == 200
        assert response.json()['device_identity'] == device.reference
        assert client.post('/v2/registration/complete', json=proof).status_code == 403
        for payload in [{'private_key': 'secret-do-not-echo'}, {**proof, 'private_key': 'secret-do-not-echo'}]:
            response = client.post('/v2/registration/complete', json=payload)
            assert response.status_code == 403
            assert 'secret-do-not-echo' not in response.text
        assert client.post('/v2/entitlements', json={}).status_code == 404


@pytest.mark.parametrize('body', [b'[]', b'{"a":1,"a":2}', b'x' * 8193, b'bad json'])
def test_bad_http_bodies_rejected(setup, body):
    with TestClient(create_app(setup[0])) as client:
        response = client.post('/v2/registration/complete', content=body,
                               headers={'content-type': 'application/json'})
        assert response.status_code == 400
        assert response.json() == {'code': 'INVALID_REQUEST'}


def test_database_requires_private_storage(tmp_path):
    unsafe = tmp_path / 'shared'
    unsafe.mkdir(mode=0o755)
    with pytest.raises(RuntimeError):
        ProductStore(unsafe / 'product.db').migrate()
    assert not (unsafe / 'product.db').exists()


def test_migration_rejects_newer_schema_without_changes(setup):
    store = setup[0]
    with sqlite3.connect(store.path) as db:
        db.execute('PRAGMA user_version=4')
    with pytest.raises(RuntimeError, match='unsupported'):
        store.migrate()
    with sqlite3.connect(store.path) as db:
        assert db.execute('PRAGMA user_version').fetchone()[0] == 4


def test_sqlite_unavailable_response_is_sanitized(setup, monkeypatch):
    def unavailable(proof):
        raise sqlite3.OperationalError('secret-database-path-and-query')
    store = setup[0]
    monkeypatch.setattr(store, 'enroll', unavailable)
    with TestClient(create_app(store)) as client:
        response = client.post('/v2/registration/complete', json={})
    assert response.status_code == 503
    assert response.json() == {'code': 'REGISTRATION_UNAVAILABLE'}


def test_expired_invitation_and_invalid_token_create_no_challenges(setup):
    store, clock, _, invite = setup
    device = DeviceIdentity.generate()
    with pytest.raises(EnrollmentRejected):
        store.challenge(invitation_token='f' * 64, public_identity=device.public_identity,
                        wireguard_public_key=device.wireguard_public_key)
    clock[0] = 9000
    with pytest.raises(EnrollmentRejected):
        proof_for(store, invite, device)
    with sqlite3.connect(store.path) as db:
        assert db.execute('SELECT count(*) FROM challenges').fetchone()[0] == 0


def test_api_factory_requires_migrated_database(setup, monkeypatch):
    from control.product.api import app_from_env
    store = setup[0]
    monkeypatch.setenv('FC_PRODUCT_DB', store.path)
    assert app_from_env() is not None
    with sqlite3.connect(store.path) as db:
        db.execute('PRAGMA user_version=4')
    with pytest.raises(RuntimeError, match='migration required'):
        app_from_env()


def test_admin_invitation_output_is_private_and_not_printed(setup, monkeypatch, capsys, tmp_path):
    from control.product.admin import main
    store, _, entitlement, _ = setup
    # Use the same injected test clock for the trusted operator command.
    import control.product.admin as admin
    monkeypatch.setattr(admin, 'ProductStore', lambda path: store)
    monkeypatch.setattr(admin.time, 'time', lambda: 1000)
    output = tmp_path / 'invitation.json'
    monkeypatch.setattr('sys.argv', ['admin', '--database', store.path, 'create-invitation',
                                    '--entitlement', entitlement['entitlement_id'], '--hours', '1',
                                    '--output', str(output)])
    main()
    assert capsys.readouterr().out == ''
    assert output.stat().st_mode & 0o777 == 0o600
    assert len(json.loads(output.read_text())['invitation_token']) == 64
    with pytest.raises(FileExistsError):
        main()


def test_product_health_checks_current_database_schema(setup):
    with TestClient(create_app(setup[0])) as client:
        response = client.get('/healthz')
        assert response.status_code == 200
        assert response.json() == {'status':'ok','service':'family-connect-product','schema_version':3}
        assert response.headers['cache-control'] == 'no-store'
