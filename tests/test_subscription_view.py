import ast
from copy import deepcopy
import importlib
import json
from pathlib import Path
import sqlite3
import threading
import xml.etree.ElementTree as ET

import pytest

from control.friends import paid_beta, support_ids
from messenger.service_events import validate_feed
from messenger.store import Store


NOW = 1800000000
DEVICE = 'ab' * 16
SUPPORT = 'FC-2345-6789'
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def backend():
    database = sqlite3.connect(':memory:')
    database.row_factory = sqlite3.Row
    database.execute('CREATE TABLE devices (device TEXT PRIMARY KEY, revoked INTEGER)')
    database.execute('CREATE TABLE invites (device TEXT, revoked INTEGER)')
    support_ids.create(database)
    database.execute('INSERT INTO devices VALUES (?,0)', (DEVICE,))
    database.execute('INSERT INTO invites VALUES (?,0)', (DEVICE,))
    database.execute('INSERT INTO device_support(device,support_id,platform,app_version,version_code,last_seen) '
                     'VALUES (?,?,?,?,?,?)', (DEVICE, SUPPORT, 'android', paid_beta.PAID_ANDROID_VERSION,
                                           paid_beta.PAID_ANDROID_VERSION_CODE, NOW))
    paid_beta.migrate(database)
    yield database
    database.close()


def evidence(database, kind='payment', ident='synthetic-event-1', now=NOW, until=None):
    values = dict(period_start=now, paid_until=until or now + 3600,
                  apk_sha256=paid_beta.PAID_ANDROID_APK_SHA256) if kind == 'payment' else {}
    if kind == 'grace': values['grace_until'] = now + 7200
    event = paid_beta.apply_event(database, SUPPORT, kind, ident, 'synthetic-only-reference', now=now, **values)['event']
    return paid_beta.status(database, SUPPORT, now), event


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setattr('messenger.store.time.time', lambda: NOW)
    with_store = Store(tmp_path / 'chat', bytes(range(32)), create=True)
    yield with_store
    with_store.close()


def accept(store, status, event=None, now=NOW):
    store.accept_confirmed_subscription(status, device=DEVICE, confirmed_at=now, event=event)
    return store.subscription_status(DEVICE)


def test_empty_and_registration_are_not_paid(store):
    assert store.subscription_status(DEVICE) == dict(snapshot=None, confirmed_at=None, notice=None)
    for response in (dict(device=DEVICE, registered=True, revoked=False, active=True),
                     dict(status='success'), dict(payment_return=True)):
        with pytest.raises(ValueError): accept(store, response)
    assert store.subscription_status(DEVICE)['notice'] is None


@pytest.mark.parametrize('kind,state', [('payment', 'active'), ('expire', 'expired'),
                                       ('grace', 'grace'), ('revoke', 'revoked')])
def test_canonical_backend_states(backend, store, kind, state):
    status, event = evidence(backend)
    if kind != 'payment': status, event = evidence(backend, kind, 'synthetic-event-2')
    current = accept(store, status, event)
    assert current['snapshot']['effective_state'] == state
    assert current['snapshot']['paid_until'] == NOW + 3600
    assert current['notice']['subscription_event'] == ('activated' if kind == 'payment' else kind)
    assert 'reference_hash' not in repr(current) and 'payload_hash' not in repr(current)


def test_renewal_duplicate_old_expiry_and_restart(backend, store, tmp_path):
    first, activation = evidence(backend)
    accept(store, first, activation)
    expired, expiry = evidence(backend, 'expire', 'synthetic-expiry', now=NOW + 1)
    renewed, renewal = evidence(backend, ident='synthetic-renewal', now=NOW + 2, until=NOW + 7200)
    current = accept(store, renewed, renewal, now=NOW + 2)
    assert current['notice']['subscription_event'] == 'renewed'
    store.service_mark([current['notice']['id']], 'notified')
    assert accept(store, renewed, renewal, now=NOW + 3)['notice']['notified']
    assert accept(store, expired, expiry, now=NOW + 4)['snapshot']['version'] == 3
    assert accept(store, first, activation, now=NOW + 5)['snapshot']['version'] == 3
    store.close()
    with_store = Store(tmp_path / 'chat', bytes(range(32)), create=False)
    try:
        saved = with_store.subscription_status(DEVICE)
        assert saved['notice']['notified'] and saved['snapshot']['paid_until'] == NOW + 7200
        assert accept(with_store, renewed, renewal, now=NOW + 6)['notice']['notified']
        with_store.service_mark([saved['notice']['id']], 'read')
        assert with_store.subscription_status(DEVICE)['notice']['read']
        assert b'synthetic-renewal' not in (tmp_path / 'chat/history.sqlite').read_bytes()
        assert with_store._db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall() == [('records',)]
    finally:
        with_store.close()


def test_snapshot_alone_never_announces_payment_and_event_can_follow(backend, store):
    status, event = evidence(backend)
    assert accept(store, status)['notice'] is None
    confirmed = accept(store, status, event)
    assert confirmed['notice']['subscription_event'] == 'activated'
    store.service_mark([confirmed['notice']['id']], 'read')
    assert accept(store, status)['notice']['read']


def test_no_connection_does_not_change_confirmed_state(backend, store, monkeypatch):
    status, event = evidence(backend)
    original = accept(store, status, event)
    monkeypatch.setattr('messenger.store.time.time', lambda: NOW + 3600)
    offline = store.subscription_status(DEVICE)
    assert offline['snapshot'] == original['snapshot']
    assert offline['confirmed_at'] == NOW
    assert offline['notice']['notification_suppressed']
    assert not offline['notice']['notified']


def test_natural_expiry_without_new_revision_never_resurrects(backend, store):
    active, event = evidence(backend)
    accept(store, active, event)
    expired = paid_beta.status(backend, SUPPORT, NOW + 3600)
    assert accept(store, expired, now=NOW + 3600)['snapshot']['effective_state'] == 'expired'
    assert accept(store, active, event)['snapshot']['effective_state'] == 'expired'
    with pytest.raises(ValueError): accept(store, active, event, now=NOW + 3601)


def test_conflicting_equal_revision_is_atomic(backend, store):
    status, event = evidence(backend)
    original = accept(store, status, event)
    changed = deepcopy(status)
    changed['subscription']['paid_until'] += 100
    changed['entitlement_until'] += 100
    with pytest.raises(ValueError): accept(store, changed)
    with pytest.raises(ValueError): accept(store, status, dict(event, previous_state='active'))
    assert store.subscription_status(DEVICE) == original


def test_other_recipient_is_never_displayed(backend, store):
    status, event = evidence(backend)
    accept(store, status, event)
    assert store.subscription_status('cd' * 16)['snapshot'] is None
    with pytest.raises(ValueError):
        store.accept_confirmed_subscription(status, device='cd' * 16, confirmed_at=NOW, event=event)
    with pytest.raises(ValueError): store.subscription_status('')


@pytest.mark.parametrize('field,value', [('version', True), ('paid_until', NOW),
                                         ('updated_at', NOW * 1000), ('last_event_id', 'bad')])
def test_invalid_snapshot_does_not_modify_store(backend, store, field, value):
    status, event = evidence(backend)
    original = accept(store, status, event)
    changed = deepcopy(status)
    changed['subscription'][field] = value
    with pytest.raises(ValueError): accept(store, changed)
    assert store.subscription_status(DEVICE) == original


@pytest.mark.parametrize('field,value', [('result', 'PENDING'), ('device', 'cd' * 16),
                                         ('event_id', 'unmatched-event'), ('paid_until', NOW + 9000)])
def test_unmatched_or_unapplied_event_is_rejected(backend, store, field, value):
    status, event = evidence(backend)
    with pytest.raises(ValueError): accept(store, status, dict(event, **{field: value}))
    assert store.subscription_status(DEVICE)['snapshot'] is None


def test_first_seen_renewal_does_not_invent_prior_period(backend, store):
    evidence(backend)
    status, event = evidence(backend, ident='synthetic-renewal', now=NOW + 1)
    assert accept(store, status, event, now=NOW + 1)['notice']['subscription_event'] == 'confirmed'


def test_same_end_payment_is_not_an_extension(backend, store):
    status, event = evidence(backend)
    accept(store, status, event)
    status, event = evidence(backend, ident='synthetic-payment-2', now=NOW + 1, until=NOW + 3600)
    assert accept(store, status, event, now=NOW + 1)['notice']['subscription_event'] == 'confirmed'


def test_late_event_cannot_be_attached_to_newer_snapshot(backend, store):
    first, activation = evidence(backend)
    latest, renewal = evidence(backend, ident='synthetic-renewal', now=NOW + 1)
    original = accept(store, latest, renewal, now=NOW + 1)
    with pytest.raises(ValueError): accept(store, latest, activation, now=NOW + 2)
    assert store.subscription_status(DEVICE) == original


def test_trial_snapshot_is_not_payment(backend, store):
    evidence(backend)
    backend.execute("UPDATE paid_beta_subscriptions SET state='trial' WHERE device=?", (DEVICE,))
    trial = accept(store, paid_beta.status(backend, SUPPORT, NOW))
    assert trial['snapshot']['effective_state'] == 'trial' and trial['notice'] is None


def test_android_rpc_reads_real_store_but_cannot_import_payment(backend, store, monkeypatch):
    from messenger.local import LocalChat
    monkeypatch.syspath_prepend(str(ROOT / 'clients/android/app/src/main/python'))
    bridge = importlib.import_module('fc_chat_store')
    local = LocalChat.__new__(LocalChat)
    local._lock, local._store, local._chat, local._closing = threading.RLock(), store, object(), False
    session = bridge.Session.__new__(bridge.Session)
    session.local = local
    status, event = evidence(backend)
    expected = accept(store, status, event)
    assert json.loads(session.invoke('subscription_status', json.dumps(dict(device=DEVICE)))) == dict(ok=True, value=expected)
    for operation in ('accept_confirmed_subscription', 'payment_return', 'subscription_refresh'):
        assert json.loads(session.invoke(operation, '{}')) == dict(ok=False, error='invalid_input')
    assert json.loads(session.invoke('subscription_status', json.dumps(dict(device='wrong')))) == dict(ok=False, error='invalid_input')
    assert store.subscription_status(DEVICE) == expected


def test_long_delayed_payment_has_no_fresh_notification(backend, store, monkeypatch):
    status, event = evidence(backend, until=NOW + 7 * 86400)
    accept(store, status, event)
    monkeypatch.setattr('messenger.store.time.time', lambda: NOW + 86401)
    assert store.subscription_status(DEVICE)['notice']['notification_suppressed']


def test_public_feed_cannot_supply_subscription_events():
    with pytest.raises(ValueError, match='kind'):
        validate_feed(dict(version=1, events=[dict(id='ef' * 16, kind='subscription', title='Paid',
            body='Untrusted payment claim', author='Publisher', created=NOW, expires=NOW + 3600,
            platforms=['android'])]), now=NOW)


def test_android_ui_rpc_is_read_only_and_sources_are_packaged():
    source = ROOT / 'clients/android/app/src/main/python/fc_chat_store.py'
    signatures = next(ast.literal_eval(node.value) for node in ast.walk(ast.parse(source.read_text()))
                      if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'signatures' for target in node.targets))
    assert signatures['subscription_status'] == ('device',)
    assert 'accept_confirmed_subscription' not in signatures
    assert 'subscription_view.py' in (ROOT / 'clients/android/chat-python.gradle').read_text()
    assert 'accept_confirmed_subscription' not in ''.join(path.read_text() for path in
        (ROOT / 'clients/android/app/src/main').rglob('*.java'))


def test_ru_en_resources_have_matching_keys_and_format_parameters():
    resources = ROOT / 'clients/android/app/src/main/res'
    tables = [{item.attrib['name']: item.text for item in ET.parse(resources / folder / 'strings.xml').getroot()
               if item.attrib.get('name', '').startswith('subscription_')} for folder in ('values', 'values-ru')]
    assert tables[0].keys() == tables[1].keys() and len(tables[0]) == 24
    for key in tables[0]:
        assert bool('%1$s' in tables[0][key]) == bool('%1$s' in tables[1][key])


def test_notification_route_is_local_and_reuses_existing_channel():
    source = ROOT / 'clients/android/app/src/main/java/com/familyconnect/app'
    notifications = (source / 'ChatNotifications.java').read_text()
    assert 'SubscriptionUi.intent(c)' in notifications
    assert 'String channel=service?EVENTS:MESSAGES' in notifications
    assert '.setOnlyAlertOnce(subscription)' in notifications
    assert '"chat:subscription:"+message.get("id").getAsString()' in notifications
    assert '.setVisibility(Notification.VISIBILITY_PRIVATE)' in notifications
    assert 'FriendsActivity.class' in (source / 'SubscriptionUi.java').read_text()
    assert 'navigate(3);SubscriptionUi.show(this)' in (source / 'FriendsActivity.java').read_text()
