from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import http.client
import importlib
import importlib.util
import json
from pathlib import Path
import threading
from types import SimpleNamespace

import pytest

from control.friends.access import Access
from control.friends import paid_beta, support_ids
from device_identity.device import DeviceIdentity
from messenger.local import LocalChat, LocalError
from messenger.store import Store
from messenger.subscription_view import decode_response


ROOT = Path(__file__).resolve().parents[1]
NOW = 1800000000
PATH = '/friends/device/subscription'


def post(server, path, body):
    connection = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=4)
    try:
        connection.request('POST', path, json.dumps(body), {'Content-Type': 'application/json'})
        response = connection.getresponse()
        return response.status, response.read(16385), dict(response.getheaders())
    finally:
        connection.close()


@pytest.fixture
def runtime(tmp_path):
    spec = importlib.util.spec_from_file_location('subscription_test_handler', ROOT / 'deploy/friends/access-api.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    now = [NOW]
    access = Access(tmp_path / 'synthetic.db', clock=lambda: now[0])
    access.initialize()
    devices = [DeviceIdentity.generate(), DeviceIdentity.generate()]
    supports = []
    for device in devices:
        challenge = access.challenge(device.public_identity, device.wireguard_public_key, 'activate', access.invite())
        access.complete(device.prove_transport_key(challenge['challenge']), 'activate')
        with access.db() as database:
            supports.append(support_ids.registered(database, device.reference))
            database.execute('UPDATE device_support SET platform=?,app_version=?,version_code=?,last_seen=? WHERE device=?',
                             ('android', paid_beta.PAID_ANDROID_VERSION, paid_beta.PAID_ANDROID_VERSION_CODE, NOW, device.reference))
    with access.db() as database:
        paid_beta.migrate(database)
    module.access, module.ROOT = access, tmp_path
    server = module.ThreadingHTTPServer(('127.0.0.1', 0), module.Handler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, kwargs=dict(poll_interval=0.01))
    thread.start()
    yield SimpleNamespace(access=access, devices=devices, supports=supports, server=server, module=module, now=now)
    server.shutdown()
    server.server_close()
    thread.join(2)
    assert not thread.is_alive()


def proof(runtime, index=0, purpose='subscription'):
    device = runtime.devices[index]
    status, raw, _ = post(runtime.server, '/friends/challenge', dict(public_identity=device.public_identity,
        wireguard_public_key=device.wireguard_public_key, purpose=purpose, invitation=''))
    assert status == 200
    return device.prove_transport_key(json.loads(raw)['challenge'])


def read(runtime, index=0):
    return post(runtime.server, PATH, proof(runtime, index))


def payment(runtime, kind='payment', index=0, ident='synthetic-payment-1', until=None):
    now = runtime.now[0]
    values = dict(period_start=now, paid_until=until or now + 3600,
                  apk_sha256=paid_beta.PAID_ANDROID_APK_SHA256) if kind == 'payment' else {}
    if kind == 'grace': values['grace_until'] = now + 7200
    with runtime.access.db() as database:
        return paid_beta.apply_event(database, runtime.supports[index], kind, ident, 'SYNTHETIC-private-receipt', now=now, **values)


def protected(runtime):
    with runtime.access.db() as database:
        names = [row[0] for row in database.execute("SELECT name FROM sqlite_master WHERE type='table' AND name!='challenges'")]
        return {name: [tuple(row) for row in database.execute('SELECT * FROM ' + name + ' ORDER BY 1')] for name in names}


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / 'clients/android/app/src/main/python'))
    bridge = importlib.import_module('fc_chat_store')
    store = Store(tmp_path / 'chat', bytes(range(32)), create=True)
    local = LocalChat.__new__(LocalChat)
    local._lock, local._store, local._chat, local._closing = threading.RLock(), store, object(), False
    session = bridge.Session.__new__(bridge.Session)
    session.local = local
    yield session, store
    store.close()


def ingest(client, runtime, raw):
    return json.loads(client[0].accept_subscription(raw.decode('utf-8'), runtime.devices[0].reference))


def test_real_http_decoder_encrypted_store_event_path(runtime, client):
    payment(runtime)
    before = protected(runtime)
    ownership = proof(runtime)
    status, raw, headers = post(runtime.server, PATH, ownership)
    assert status == 200 and headers['Cache-Control'] == 'no-store' and len(raw) < 16384
    assert b'reference_hash' not in raw and b'payload_hash' not in raw and b'SYNTHETIC-private-receipt' not in raw
    assert runtime.supports[0].encode() not in raw and runtime.devices[1].reference.encode() not in raw
    accepted = ingest(client, runtime, raw)
    assert accepted['accepted'] and accepted['view']['snapshot']['effective_state'] == 'active'
    assert accepted['view']['notice']['subscription_event'] == 'activated'
    assert accepted['view']['confirmed_at'] == NOW
    assert protected(runtime) == before
    assert post(runtime.server, PATH, ownership)[0] == 403
    assert protected(runtime) == before


@pytest.mark.parametrize('kind,state', [('payment', 'active'), ('grace', 'grace'), ('expire', 'expired'), ('revoke', 'revoked')])
def test_own_status_readable_independently_of_paid_enforcement(runtime, client, kind, state):
    payment(runtime)
    if kind != 'payment': payment(runtime, kind, ident='synthetic-event-2')
    before = protected(runtime)
    status, raw, _ = read(runtime)
    assert status == 200
    view = ingest(client, runtime, raw)['view']
    assert view['snapshot']['effective_state'] == state
    assert view['snapshot']['entitlement_until'] == (NOW + 7200 if kind == 'grace' else NOW + 3600 if kind == 'payment' else None)
    assert protected(runtime) == before


def test_non_cohort_is_confirmed_but_not_unpaid(runtime, client):
    payment(runtime, index=1, ident='synthetic-other-device')
    status, raw, _ = read(runtime)
    assert status == 200
    assert json.loads(raw) == dict(schema=1, device=runtime.devices[0].reference, observed_at=NOW,
                                   cohort=False, subscription=None, event=None)
    view = ingest(client, runtime, raw)['view']
    assert view['cohort'] is False and view['snapshot'] is None and view['notice'] is None
    payment(runtime)
    assert ingest(client, runtime, read(runtime)[1])['view']['cohort'] is True


@pytest.mark.parametrize('field', ['device', 'support', 'event_id'])
def test_arbitrary_selector_cannot_read_another_device(runtime, field):
    payment(runtime, index=1)
    ownership = proof(runtime)
    ownership[field] = runtime.devices[1].reference
    assert post(runtime.server, PATH, ownership)[0] == 403
    assert json.loads(read(runtime)[1])['cohort'] is False


@pytest.mark.parametrize('mode', ['wrong-purpose', 'expired', 'signature', 'foreign-proof', 'device-revoked', 'invite-revoked'])
def test_authentication_rejections(runtime, mode):
    ownership = proof(runtime, purpose='status' if mode == 'wrong-purpose' else 'subscription')
    if mode == 'expired': runtime.now[0] += 100
    if mode == 'signature': ownership['signature'] = 'A' * 88
    if mode == 'foreign-proof': ownership = runtime.devices[1].prove_transport_key(ownership['challenge'])
    if mode in ('device-revoked', 'invite-revoked'):
        with runtime.access.db() as database:
            database.execute('UPDATE ' + ('devices' if mode == 'device-revoked' else 'invites') + ' SET revoked=1 WHERE device=?', (runtime.devices[0].reference,))
    before = protected(runtime)
    assert post(runtime.server, PATH, ownership)[0] == 403
    assert protected(runtime) == before


def test_unregistered_identity_cannot_obtain_subscription_challenge(runtime):
    stranger = DeviceIdentity.generate()
    assert post(runtime.server, '/friends/challenge', dict(public_identity=stranger.public_identity,
        wireguard_public_key=stranger.wireguard_public_key, purpose='subscription', invitation=''))[0] == 403


@pytest.mark.parametrize('mode,code', [('absent', 501), ('partial', 503), ('corrupt-columns', 503)])
def test_schema_failure_is_not_non_cohort_and_never_migrates(runtime, mode, code):
    with runtime.access.db() as database:
        database.execute('DROP TABLE paid_beta_events')
        if mode == 'absent': database.execute('DROP TABLE paid_beta_subscriptions')
        if mode == 'corrupt-columns': database.execute('CREATE TABLE paid_beta_events (event_id TEXT)')
    before = protected(runtime)
    ownership = proof(runtime)
    status, raw, headers = post(runtime.server, PATH, ownership)
    assert status == code and headers['Cache-Control'] == 'no-store'
    assert set(json.loads(raw)) == {'error'}
    assert post(runtime.server, PATH, ownership)[0] == 403
    assert protected(runtime) == before


def test_missing_corresponding_event_is_snapshot_only(runtime, client):
    payment(runtime)
    with runtime.access.db() as database:
        database.execute("UPDATE paid_beta_subscriptions SET last_event_id='missing-applied-event'")
    status, raw, _ = read(runtime)
    assert status == 200 and json.loads(raw)['event'] is None
    assert ingest(client, runtime, raw)['view']['notice'] is None


def test_reads_preserve_existing_admission_grants_and_certificates(runtime):
    from control.friends import restricted
    restricted.migrate(runtime.access)
    payment(runtime)
    with runtime.access.db() as database:
        database.execute('INSERT INTO restricted_grants VALUES (?,?,?,?,?)',
                         (runtime.devices[0].reference, 'synthetic-family', 1, NOW + 3600, 0))
        database.execute('INSERT INTO restricted_certificates VALUES (?,?,?,?,?)',
                         (runtime.devices[0].reference, 1, 'synthetic-serial', NOW + 3600, 'synthetic-certificate-not-a-key'))
    before = protected(runtime)
    assert read(runtime)[0] == 200
    assert protected(runtime) == before


def test_closed_owner_cannot_accept_late_response(runtime, client):
    payment(runtime)
    raw = read(runtime)[1]
    client[0].local._closing = True
    with pytest.raises(LocalError, match='closing'): ingest(client, runtime, raw)
    assert client[1].subscription_status(runtime.devices[0].reference)['snapshot'] is None


def test_non_cohort_survives_restart_without_freshness_and_cannot_erase_cohort(runtime, client, tmp_path):
    outside = read(runtime)[1]
    ingest(client, runtime, outside)
    client[1].close()
    reopened = Store(tmp_path / 'chat', bytes(range(32)), create=False)
    try:
        client[0].local._store = reopened
        saved = reopened.subscription_status(runtime.devices[0].reference)
        assert saved['cohort'] is False and saved['notice'] is None and 'refresh_status' not in saved
        payment(runtime)
        ingest(client, runtime, read(runtime)[1])
        with pytest.raises(ValueError): ingest(client, runtime, outside)
        assert reopened.subscription_status(runtime.devices[0].reference)['snapshot']['version'] == 1
    finally:
        reopened.close()


def test_grace_naturally_expires_without_new_revision_or_event(runtime, client):
    payment(runtime)
    payment(runtime, 'grace', ident='synthetic-grace-2')
    initial = ingest(client, runtime, read(runtime)[1])['view']
    runtime.now[0] += 7200
    expired = ingest(client, runtime, read(runtime)[1])['view']
    assert initial['snapshot']['effective_state'] == 'grace'
    assert expired['snapshot']['effective_state'] == 'expired'
    assert expired['snapshot']['entitlement_until'] is None and expired['snapshot']['grace_until'] == NOW + 7200
    assert initial['snapshot']['version'] == expired['snapshot']['version'] == 2
    assert initial['notice']['id'] == expired['notice']['id']


@pytest.mark.parametrize('kind', ['payment', 'revoke'])
def test_concurrent_write_cannot_split_snapshot_and_event(runtime, monkeypatch, kind):
    payment(runtime)
    ownership = proof(runtime)
    reading, release, writing, written = (threading.Event() for _ in range(4))
    original = paid_beta.effective_subscription_state

    def held(database, device, now):
        reading.set()
        assert release.wait(3)
        return original(database, device, now)

    def writer():
        writing.set()
        payment(runtime, kind, ident='synthetic-concurrent-2', until=NOW + 7200)
        written.set()

    monkeypatch.setattr(paid_beta, 'effective_subscription_state', held)
    with ThreadPoolExecutor(max_workers=2) as executor:
        response = executor.submit(post, runtime.server, PATH, ownership)
        try:
            assert reading.wait(2)
            runtime.now[0] += 1
            changing = executor.submit(writer)
            assert writing.wait(1) and not written.wait(0.05)
        finally:
            release.set()
        status, raw, _ = response.result(timeout=3)
        changing.result(timeout=3)
    assert status == 200
    result = json.loads(raw)
    assert result['observed_at'] == NOW
    assert result['subscription']['version'] == 1 and result['event']['event_id'] == 'synthetic-payment-1'
    assert result['subscription']['paid_until'] == NOW + 3600 and result['subscription']['paid_allow']
    latest = json.loads(read(runtime)[1])
    assert latest['subscription']['version'] == 2 and latest['event']['event_id'] == 'synthetic-concurrent-2'


def test_expiry_duplicate_late_revision_conflict_and_restart(runtime, client, tmp_path):
    payment(runtime)
    first = read(runtime)[1]
    view = ingest(client, runtime, first)['view']
    client[1].service_mark([view['notice']['id']], 'notified')
    assert ingest(client, runtime, read(runtime)[1])['view']['notice']['notified']
    runtime.now[0] += 3600
    expired = read(runtime)[1]
    assert ingest(client, runtime, expired)['view']['snapshot']['effective_state'] == 'expired'
    assert not ingest(client, runtime, first)['accepted']
    payment(runtime, ident='synthetic-renewal-2')
    renewed = read(runtime)[1]
    current = ingest(client, runtime, renewed)['view']
    assert current['notice']['subscription_event'] == 'renewed'
    assert not ingest(client, runtime, expired)['accepted']
    conflict = json.loads(renewed)
    conflict['subscription']['paid_until'] += 100
    conflict['subscription']['entitlement_until'] += 100
    with pytest.raises(ValueError): ingest(client, runtime, json.dumps(conflict).encode())
    client[1].service_mark([current['notice']['id']], 'read')
    client[1].close()
    reopened = Store(tmp_path / 'chat', bytes(range(32)), create=False)
    try:
        saved = reopened.subscription_status(runtime.devices[0].reference)
        assert saved['notice']['read'] and saved['notice']['notified']
        assert saved['snapshot']['version'] == 2
        assert b'synthetic-renewal-2' not in (tmp_path / 'chat/history.sqlite').read_bytes()
    finally:
        reopened.close()


@pytest.mark.parametrize('mutation', ['schema', 'recipient', 'extra-private', 'boolean-time', 'float-time', 'mismatched-event', 'not-applied', 'fake-effective'])
def test_strict_wire_validation_before_store(runtime, client, mutation):
    payment(runtime)
    raw = read(runtime)[1]
    original = ingest(client, runtime, raw)['view']
    bad = json.loads(raw)
    if mutation == 'schema': bad['schema'] = 2
    if mutation == 'recipient': bad['device'] = runtime.devices[1].reference
    if mutation == 'extra-private': bad['subscription']['reference_hash'] = 'not-user-data'
    if mutation == 'boolean-time': bad['observed_at'] = True
    if mutation == 'float-time': bad['subscription']['paid_until'] = float(NOW + 3600)
    if mutation == 'mismatched-event': bad['event']['event_id'] = 'other-paid-event'
    if mutation == 'not-applied': bad['event']['result'] = 'PENDING'
    if mutation == 'fake-effective': bad['subscription']['effective_state'] = 'expired'
    with pytest.raises(ValueError): ingest(client, runtime, json.dumps(bad).encode())
    assert client[1].subscription_status(runtime.devices[0].reference) == original


@pytest.mark.parametrize('raw', [b'{"schema":1,"schema":1}', b'\xff', b' ' * 16385, b'null', b'[]'])
def test_decoder_rejects_duplicate_encoding_size_and_shape(raw):
    with pytest.raises(ValueError): decode_response(raw, 'ab' * 16)


def test_temporary_failure_keeps_cache_and_no_success_from_http200_alone(runtime, client, monkeypatch):
    payment(runtime)
    original = ingest(client, runtime, read(runtime)[1])['view']
    def unavailable(*args): raise RuntimeError('synthetic outage')
    monkeypatch.setattr('control.friends.subscription.snapshot', unavailable)
    ownership = proof(runtime)
    status, raw, _ = post(runtime.server, PATH, ownership)
    assert status == 503
    assert post(runtime.server, PATH, ownership)[0] == 403
    with pytest.raises(ValueError): ingest(client, runtime, raw)
    with pytest.raises(ValueError): ingest(client, runtime, b'{"status":"success"}')
    assert client[1].subscription_status(runtime.devices[0].reference) == original


def test_registration_status_exact_response_is_unchanged(runtime):
    status, raw, _ = post(runtime.server, '/friends/device/status', proof(runtime, purpose='status'))
    assert status == 200
    assert json.loads(raw) == dict(device=runtime.devices[0].reference, registered=True, revoked=False, active=True)


def test_personal_allowlists_and_no_paid_vpn_dependency():
    sources = ROOT / 'clients/android/app/src/main/java/com/familyconnect/app'
    client = (sources / 'FriendsAccessAndroid.java').read_text()
    runtime = (sources / 'ChatRuntime.java').read_text()
    assert 'device/(status|subscription|support|diagnostics)' in client
    assert 'new FriendsAccessAndroid(app,android.os.SystemClock.elapsedRealtime()+20000).subscription(identity)' in runtime
    assert 'direct&&!viaVpn?new ChatNetworkAndroid(context).openHttps' in client
    assert 'subscription' not in (sources / 'ReadinessBootstrapRoute.java').read_text()
    snippet = (ROOT / 'deploy/friends/subscription-location.conf').read_text()
    assert 'location = /friends/device/subscription' in snippet and 'proxy_cache off;' in snippet
    manifest = json.loads((ROOT / 'deploy/friends/restricted/http-runtime-files.json').read_text())
    assert 'control/friends/subscription.py' in manifest
    assert 'subscription-location.conf' in (ROOT / 'scripts/package_friends_http.py').read_text()
