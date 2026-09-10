import base64
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor

import pytest
import RNS
from fastapi.testclient import TestClient

from control.product.api import create_app
from control.product.provisioning import ProvisioningService
from control.product.store import ProductStore
from control.product.gateways import GatewayReconciler


class ReadyGateway:
    def apply(self, *args, **kwargs):
        pass

from device_identity.device import DeviceIdentity
from provisioning.auth import prove
from provisioning.cache import ProvisioningCache
from provisioning.client import ProvisioningClient
from provisioning.envelope import ProvisioningRejected, ProvisioningVerifier, issue


@pytest.fixture
def setup(tmp_path):
    clock = [1000]
    store = ProductStore(tmp_path / 'product.db', clock=lambda: clock[0])
    store.migrate()
    entitlement = store.create_entitlement(expires_at=10000)
    invite = store.create_invitation(entitlement['entitlement_id'], expires_at=9000, max_uses=5)
    device = DeviceIdentity.generate()
    challenge = store.challenge(invitation_token=invite['invitation_token'],
        public_identity=device.public_identity, wireguard_public_key=device.wireguard_public_key)
    store.enroll(device.prove_transport_key(challenge['challenge']))
    signer = RNS.Identity()
    network = dict(addresses=['10.77.0.4/32'], dns=['1.1.1.1'], gateways=[dict(
        gateway_id='g1', provider_id='p1', region='BE', transport='wireguard',
        endpoint='198.51.100.1', port=51820,
        public_key=DeviceIdentity.generate().wireguard_public_key)])
    service = ProvisioningService(store)
    worker = GatewayReconciler(store, {'g1':ReadyGateway()})
    worker.stage(device.reference, network, lease_seconds=9000)
    worker.run_once()
    service.publish(device.reference, network, signing_identity=signer)
    verifier = ProvisioningVerifier(trusted_signer_public=signer.get_public_key(),
        device_identity=device._identity, wireguard_public_key=device.wireguard_public_key)
    cache = ProvisioningCache(tmp_path / 'cache', verifier)
    cache.initialize()
    return store, clock, device, signer, network, service, cache


def proof(setup):
    device, service = setup[2], setup[5]
    return prove(device, service.challenge(public_identity=device.public_identity,
        wireguard_public_key=device.wireguard_public_key)['challenge'])


def test_durable_versions_and_lost_response_recovery(setup):
    store, clock, device, signer, network, service, cache = setup
    first = service.fetch(proof(setup))
    assert cache.accept(first, now=1000).state.revision == 1
    restarted = ProvisioningService(ProductStore(store.path, clock=lambda: clock[0]))
    assert restarted.fetch(proof(setup)) == first
    assert cache.accept(first, now=1001).state.revision == 1
    service.publish(device.reference, network, signing_identity=signer)
    second = service.fetch(proof(setup))
    assert cache.accept(second, now=1002).state.revision == 2
    with pytest.raises(ProvisioningRejected):
        cache.accept(first, now=1002)
    assert ProvisioningCache(cache.path, cache.verifier).load(now=1003).state.revision == 2
    assert [v['revision'] for v in restarted.versions(device.reference)] == [1, 2]


def test_concurrent_fetch_consumes_once(setup):
    service, p = setup[5], proof(setup)
    def fetch(_):
        try:
            return service.fetch(p)
        except ProvisioningRejected:
            return None
    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sum(v is not None for v in pool.map(fetch, range(8))) == 1


@pytest.mark.parametrize('attack', ['expired', 'device_revoked', 'entitlement_revoked',
    'key_revoked', 'bad_signature', 'other_identity', 'wrong_key', 'registration_proof', 'entitlement_expired'])
def test_fetch_rechecks_authorization_and_purpose(setup, attack):
    store, clock, device, _, _, service, _ = setup
    p = proof(setup)
    if attack == 'expired':
        clock[0] = 1120
    elif attack == 'device_revoked':
        store.revoke_device(device.reference)
    elif attack == 'entitlement_revoked':
        store.revoke_entitlement(store.authorization(device.reference)['entitlement_id'])
    elif attack == 'key_revoked':
        with store._transaction() as db:
            db.execute('UPDATE transport_keys SET revoked_at=1000')
    elif attack == 'bad_signature':
        p['signature'] = base64.b64encode(bytes(64)).decode()
    elif attack == 'other_identity':
        p = prove(DeviceIdentity.generate(), p['challenge'])
    elif attack == 'wrong_key':
        p = prove(DeviceIdentity(device._identity, DeviceIdentity.generate()._wireguard_key), p['challenge'])
    elif attack == 'registration_proof':
        p = device.prove_transport_key(p['challenge'])
    else:
        clock[0] = 10000
    with pytest.raises(ProvisioningRejected):
        service.fetch(p)


def test_expired_latest_never_falls_back(setup):
    _, clock, device, signer, network, service, _ = setup
    service.publish(device.reference, network, signing_identity=signer, lease_seconds=1)
    clock[0] = 1001
    with pytest.raises(ProvisioningRejected):
        service.fetch(proof(setup))


def test_publication_failure_rolls_back_revision(setup):
    store, _, device, signer, network, service, _ = setup
    class BrokenSigner:
        def sign(self, data):
            raise RuntimeError('failure')
    with pytest.raises(RuntimeError):
        service.publish(device.reference, network, signing_identity=BrokenSigner())
    assert service.publish(device.reference, network, signing_identity=signer)['revision'] == 2
    with store._transaction() as db:
        assert db.execute('SELECT count(*) FROM provisioning_versions').fetchone()[0] == 2


def test_parallel_publication_and_cache_updates(setup):
    _, _, device, signer, network, service, cache = setup
    with ThreadPoolExecutor(max_workers=4) as pool:
        revisions = list(pool.map(lambda _: service.publish(device.reference, network,
            signing_identity=signer)['revision'], range(4)))
    assert sorted(revisions) == [2, 3, 4, 5]
    envelope = service.fetch(proof(setup))
    with ThreadPoolExecutor(max_workers=4) as pool:
        assert list(pool.map(lambda _: cache.accept(envelope, now=1000).state.revision,
                             range(4))) == [5] * 4


def test_cache_expiry_and_clock_rollback_do_not_resurrect(setup):
    cache = setup[-1]
    cache.accept(setup[5].fetch(proof(setup)), now=1000)
    with pytest.raises(ProvisioningRejected):
        cache.load(now=4600)
    with pytest.raises(ProvisioningRejected):
        cache.load(now=1001)
    setup[1][0] = 4600
    setup[5].publish(setup[2].reference, setup[4], signing_identity=setup[3])
    assert cache.accept(setup[5].fetch(proof(setup)), now=4600).state.revision == 2


@pytest.mark.parametrize('attack', ['corrupt', 'missing', 'mode', 'symlink', 'hardlink'])
def test_cache_storage_fails_closed(setup, attack):
    cache = setup[-1]
    path = cache.path / 'cache.json'
    cache.accept(setup[5].fetch(proof(setup)), now=1000)
    if attack == 'corrupt':
        path.write_text('{}')
    elif attack == 'missing':
        path.unlink()
    elif attack == 'mode':
        path.chmod(0o644)
    elif attack == 'symlink':
        path.rename(cache.path / 'old')
        path.symlink_to(cache.path / 'old')
    else:
        (cache.path / 'hard').hardlink_to(path)
    with pytest.raises((ValueError, OSError)):
        cache.load(now=1000)
    with pytest.raises(FileExistsError):
        cache.initialize()


def test_same_revision_different_envelope_rejected(setup):
    _, _, device, signer, _, service, cache = setup
    first = service.fetch(proof(setup))
    state = cache.accept(first, now=1000).state
    alternate = issue(state, recipient_public=base64.b64decode(device.public_identity), signing_identity=signer)
    with pytest.raises(ProvisioningRejected):
        cache.accept(alternate, now=1000)
    assert cache.load(now=1000).state == state


def test_http_provider_and_cache(setup):
    store, _, device, _, _, _, cache = setup
    with TestClient(create_app(store), base_url='https://testserver') as http:
        client = ProvisioningClient(http, device, cache)
        assert client.refresh(now=1000).state.revision == 1
        assert client.refresh(now=1000).state.revision == 1
        response = http.post('/v2/provisioning/fetch', json={'private_key': 'never-echo'})
        assert response.status_code == 403
        assert response.json() == {'code': 'PROVISIONING_REJECTED'}
        assert response.headers['cache-control'] == 'no-store'
        assert http.post('/v2/provisioning/challenge', content='{}', headers={
            'content-type': 'application/json'}).status_code == 400
        store.revoke_device(device.reference)
        import httpx
        with pytest.raises(httpx.HTTPStatusError):
            client.refresh(now=1000)
        # Offline lease is not a push revocation or running-tunnel controller.
        assert client.cached(now=1000).state.revision == 1


def test_v1_migration_preserves_product_rows(tmp_path):
    store = ProductStore(tmp_path / 'product.db')
    import os
    from pathlib import Path
    fd = os.open(store.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(fd)
    with sqlite3.connect(store.path) as db:
        db.executescript((Path(__file__).parents[1] / 'control/migrations/001_product.sql').read_text())
        db.execute("INSERT INTO families VALUES ('existing',1000)")
    store.migrate()
    store.migrate()
    store.check_ready()
    with sqlite3.connect(store.path) as db:
        assert db.execute('SELECT id FROM families').fetchone()[0] == 'existing'
        assert db.execute('PRAGMA user_version').fetchone()[0] == 3


def test_challenge_hash_limits_pruning(setup):
    store, clock, _, _, _, service, _ = setup
    p = proof(setup)
    for _ in range(15):
        proof(setup)
    with pytest.raises(ProvisioningRejected):
        proof(setup)
    with sqlite3.connect(store.path) as db:
        assert p['challenge'] not in '\n'.join(db.iterdump())
    clock[0] = 1120
    assert store.prune_challenges() == 17
    with pytest.raises(ProvisioningRejected):
        service.fetch(p)


def test_http_database_error_is_sanitized(setup, monkeypatch):
    def fail(self, proof):
        raise sqlite3.OperationalError('secret-path')
    monkeypatch.setattr(ProvisioningService, 'fetch', fail)
    with TestClient(create_app(setup[0])) as http:
        response = http.post('/v2/provisioning/fetch', json={})
    assert response.status_code == 503
    assert response.json() == {'code': 'PROVISIONING_UNAVAILABLE'}


def test_invalid_response_does_not_replace_cache(setup):
    cache = setup[-1]
    original = cache.accept(setup[5].fetch(proof(setup)), now=1000)
    with pytest.raises(ProvisioningRejected):
        cache.accept(b'{}', now=1001)
    assert cache.load(now=1001) == original


def test_atomic_cache_failure_preserves_previous_version(setup, monkeypatch):
    import provisioning.cache as module
    cache = setup[-1]
    original = cache.accept(setup[5].fetch(proof(setup)), now=1000)
    setup[5].publish(setup[2].reference, setup[4], signing_identity=setup[3])
    envelope = setup[5].fetch(proof(setup))
    replace = module.os.replace
    calls = [0]
    def fail_second(*args, **kwargs):
        calls[0] += 1
        if calls[0] == 2:
            raise OSError('disk error before publication')
        return replace(*args, **kwargs)
    with monkeypatch.context() as patch:
        patch.setattr(module.os, 'replace', fail_second)
        with pytest.raises(OSError):
            cache.accept(envelope, now=1001)
    assert cache.load(now=1001) == original


def test_operator_signer_and_publication(setup, tmp_path, monkeypatch, capsys):
    from control.product.admin import main
    import control.product.admin as admin
    store, _, device, _, network, service, _ = setup
    monkeypatch.setattr(admin, 'ProductStore', lambda _: store)
    keys = tmp_path / 'signer'
    prefix = ['admin', '--database', store.path]
    monkeypatch.setattr('sys.argv', prefix + ['init-provisioning-signer', '--key-directory', str(keys)])
    main()
    anchor = json.loads(capsys.readouterr().out)['public_identity']
    assert len(base64.b64decode(anchor)) == 64
    assert (keys / 'signer.key').stat().st_mode & 0o777 == 0o600
    with pytest.raises(FileExistsError):
        main()
    config = tmp_path / 'network.json'
    config.write_text(json.dumps(network))
    monkeypatch.setattr('sys.argv', prefix + ['publish-provisioning', device.reference,
        '--network', str(config), '--key-directory', str(keys)])
    main()
    assert json.loads(capsys.readouterr().out)['revision'] == 2
    verifier = ProvisioningVerifier(trusted_signer_public=base64.b64decode(anchor),
        device_identity=device._identity, wireguard_public_key=device.wireguard_public_key)
    assert verifier.verify(service.fetch(proof(setup)), now=1000, minimum_revision=1).state.revision == 2
    monkeypatch.setattr('sys.argv', prefix + ['provisioning-versions', device.reference])
    main()
    assert len(json.loads(capsys.readouterr().out)) == 2
