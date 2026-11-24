from copy import deepcopy
import json
from pathlib import Path
import sqlite3
from types import SimpleNamespace

import pytest

from control.friends import paid_beta, transport_policy as policy
from control.friends.transport_gateway import Gateway, write
from test_paid_beta import NOW, event, registry, snapshot as registry_snapshot


def test_bounded_reconciler_preserves_registry_and_node_failure_is_not_allow(registry, tmp_path, monkeypatch):
    import sys
    from control.friends import transport_reconcile
    before = registry_snapshot(registry[0])
    commands = {node: [sys.executable, '-I', '-c',
        'import json,sys; value=json.load(sys.stdin); assert value["operation"]=="reconcile"; '
        'print(json.dumps(dict(schema=1,node=value["paid"]["node"],result="applied")))'] for node in policy.NODES}
    assert transport_reconcile.cycle(registry[0].path, commands) == dict.fromkeys(policy.NODES, 'applied')
    commands['nl-amsterdam-1'] = [sys.executable, '-I', '-c', 'print("{}")']
    assert transport_reconcile.cycle(registry[0].path, commands) == dict(zip(policy.NODES, ('applied','unavailable','applied')))
    assert registry_snapshot(registry[0]) == before


def envelope(registry, now=NOW):
    return policy.snapshot(registry[0].path, 'gateway-ru', clock=lambda: now)


@pytest.mark.parametrize('kind,offset,state,allowed', [
    ('payment', 0, 'active', True), ('payment', 3600, 'expired', False),
    ('grace', 4000, 'grace', True), ('grace', 7200, 'expired', False),
    ('expire', 0, 'expired', False), ('revoke', 0, 'revoked', False)])
def test_canonical_snapshot_is_read_only(registry, kind, offset, state, allowed):
    event(registry)
    if kind != 'payment':
        event(registry, kind, 'event-transport-state', **({'grace_until': NOW + 7200} if kind == 'grace' else {}))
    before = registry_snapshot(registry[0])
    data = envelope(registry, NOW + offset)
    assert policy.validate(data, 'gateway-ru', NOW + offset) == data
    assert data['decisions'][0]['state'] == state
    assert data['decisions'][0]['allowed'] is allowed
    assert registry_snapshot(registry[0]) == before


def test_noncohort_and_missing_schema_are_distinct(registry):
    assert envelope(registry)['decisions'][0]['state'] == 'noncohort'
    with registry[0].db() as database:
        database.execute('DROP TABLE paid_beta_events')
        database.execute('DROP TABLE paid_beta_subscriptions')
    with pytest.raises(paid_beta.PaidBetaError, match='PAID_SCHEMA_REQUIRED'):
        envelope(registry)


@pytest.fixture
def engine(tmp_path, registry):
    root = tmp_path / 'friends-awg'
    root.mkdir()
    tcp = tmp_path / 'friends-tcp'
    tcp.mkdir()
    initial = envelope(registry)['decisions'][0]
    write(root / 'transport-enforcement.json', dict(schema=1, profile=policy.PROFILE, node='gateway-ru', enabled=True))
    write(root / 'transport-state.json', dict(schema=1, node='gateway-ru', observed_at=NOW, records={}))
    client = dict(id=initial['tcp_id'], email=initial['device']+'@family.test', flow='xtls-rprx-vision')
    foreign = dict(id='foreign', email='unmanaged@example.invalid')
    write(tcp / 'server.json', dict(inbounds=[dict(tag='friends', settings=dict(clients=[client, foreign]))]))
    with sqlite3.connect(root / 'peers.db') as database:
        database.execute('CREATE TABLE peers(id INTEGER PRIMARY KEY, public TEXT)')
        database.execute('INSERT INTO peers VALUES(1,?)', (initial['public_key'],))
    live = {'awg': {initial['public_key'], 'foreign-key'}, 'addresses': {initial['public_key']: '10.1.0.2/32', 'foreign-key': '10.1.0.3/32'},
        'tcp': [client, foreign], 'restarts': 0, 'calls': [], 'sets': []}
    def run(arguments):
        live['calls'].append(arguments)
        if arguments[:2] == ['systemctl', 'restart']:
            live['restarts'] += 1
            live['tcp'] = json.loads((tcp/'server.json').read_text())['inbounds'][0]['settings']['clients']
        if arguments[1:3] == ['api', 'inbounduser']:
            return json.dumps({'users': [dict(email=item['email'], account={key: value for key, value in item.items() if key != 'email'}) for item in live['tcp']]}).encode()
        if arguments[1] == 'show':
            if arguments[-1] == 'allowed-ips':
                return '\n'.join(key+'\t'+live['addresses'][key] for key in live['awg']).encode()
            return '\n'.join(live['awg']).encode()
        if arguments[-1] == 'remove':
            live['awg'].discard(arguments[-2])
        return b''
    def add_peer(key, address):
        live['sets'].append((key, address))
        live['awg'].add(key)
        live['addresses'][key] = address
    runtime = SimpleNamespace(ROOT=root, IFACE='fixture', database=lambda: sqlite3.connect(root/'peers.db'),
        address=lambda index: '10.1.0.2/32', add_peer=add_peer)
    current = [NOW]
    gateway = Gateway(runtime, clock=lambda: current[0], monotonic=lambda: current[0], run=run)
    return gateway, current, live, initial


def test_expiry_stale_replay_and_recovery(engine, registry):
    gateway, current, live, initial = engine
    event(registry)
    original = envelope(registry)
    gateway.accept(original)
    gateway.apply()
    current[0] += policy.LEASE_SECONDS - 1
    gateway.accept(original)
    current[0] += 1
    with pytest.raises(ValueError, match='INVALID_TRANSPORT_ENVELOPE'):
        gateway.accept(original)
    gateway.apply()
    assert initial['public_key'] not in live['awg'] and live['restarts'] == 1
    assert live['awg'] == {'foreign-key'} and live['tcp'] == [dict(id='foreign', email='unmanaged@example.invalid')]
    gateway.accept(envelope(registry, current[0]))
    gateway.apply()
    assert initial['public_key'] in live['awg'] and live['restarts'] == 2


@pytest.mark.parametrize('kind', ['expire', 'revoke'])
def test_new_denial_rejects_old_allow_and_survives_reload(engine, registry, kind):
    gateway, current, live, initial = engine
    event(registry)
    original = envelope(registry)
    gateway.accept(original)
    gateway.apply()
    event(registry, kind, 'event-new-denial', now=NOW+1)
    current[0] += 1
    gateway.accept(envelope(registry, current[0]))
    gateway.apply()
    with pytest.raises(ValueError, match='STALE|TERMINAL'):
        gateway.accept(original)
    gateway.apply(starting=True)
    assert initial['public_key'] not in live['awg']
    assert not gateway.peer_allowed(initial['public_key'])
    if kind == 'expire':
        event(registry, event_id='event-renewal', now=NOW+2, paid_until=NOW+7200)
        current[0] += 1
        gateway.accept(envelope(registry, current[0]))
        gateway.apply()
        assert gateway.peer_allowed(initial['public_key'])
    else:
        with pytest.raises(paid_beta.PaidBetaError, match='REVOCATION_TERMINAL'):
            event(registry, event_id='event-illegal-renewal', now=NOW+2)


def test_node_binding_and_same_revision_conflict(engine, registry):
    gateway, current, live, initial = engine
    event(registry)
    original = envelope(registry)
    gateway.accept(original)
    wrong = deepcopy(original)
    wrong['node'] = 'nl-amsterdam-1'
    with pytest.raises(ValueError):
        gateway.accept(wrong)
    wrong = deepcopy(original)
    wrong['decisions'][0]['paid_until'] += 10
    with pytest.raises(ValueError, match='CONFLICTING'):
        gateway.accept(wrong)
    wrong = deepcopy(original)
    wrong['decisions'][0]['public_key'] = 'A'*43+'='
    with pytest.raises(ValueError, match='BINDING'):
        gateway.accept(wrong)


def test_partial_restart_failure_does_not_restore_persisted_user(engine, registry):
    gateway, current, live, initial = engine
    event(registry)
    gateway.accept(envelope(registry))
    current[0] += policy.LEASE_SECONDS + 1
    execute = gateway.run
    def failed(arguments):
        if arguments[:2] == ['systemctl', 'restart']:
            raise RuntimeError('synthetic restart failure')
        return execute(arguments)
    gateway.run = failed
    with pytest.raises(RuntimeError):
        gateway.apply()
    clients = json.loads((gateway.root.parent/'friends-tcp/server.json').read_text())['inbounds'][0]['settings']['clients']
    assert not any(item.get('id') == initial['tcp_id'] for item in clients)
    assert gateway.load()['records'][initial['device']]['applied'] is None


def test_noncohort_survives_controller_outage_without_ignoring_known_denial(engine, registry):
    gateway, current, live, initial = engine
    gateway.accept(envelope(registry))
    assert gateway.peer_allowed(initial['public_key'])
    current[0] += policy.LEASE_SECONDS
    assert gateway.peer_allowed(initial['public_key'])
    assert gateway.load()['records'][initial['device']]['decision']['state'] == 'noncohort'
    gateway.accept(envelope(registry, current[0]))
    assert gateway.peer_allowed(initial['public_key'])
    gateway.path.write_text('{}')
    with pytest.raises(ValueError):
        gateway.peer_allowed(initial['public_key'])
