import base64
from copy import deepcopy
import json
import subprocess
import uuid

import pytest

from test_transport_enforcement import engine, envelope, event, registry


def test_idle_48_devices_use_three_reads_and_no_peer_writes(engine, registry):
    gateway, current, live, initial = engine
    data = envelope(registry)
    for index in range(2, 49):
        decision = deepcopy(initial)
        decision.update(device=f'{index:032x}', public_key=base64.b64encode(index.to_bytes(32, 'big')).decode(),
            tcp_id=str(uuid.UUID(int=index)))
        data['decisions'].append(decision)
        with gateway.gateway.database() as database:
            database.execute('INSERT INTO peers VALUES(?,?)', (index, decision['public_key']))
        live['awg'].add(decision['public_key'])
        live['addresses'][decision['public_key']] = '10.1.0.2/32'
        live['tcp'].append(dict(id=decision['tcp_id'], email=decision['device']+'@family.test', flow='xtls-rprx-vision'))
    config_path = gateway.root.parent/'friends-tcp/server.json'
    config = json.loads(config_path.read_text())
    config['inbounds'][0]['settings']['clients'] = live['tcp']
    config_path.write_text(json.dumps(config))
    gateway.accept(data)
    gateway.apply()
    assert len(live['calls']) == 3
    assert live['sets'] == []
    assert live['restarts'] == 0
    assert len(gateway.load()['records']) == 48
    assert all(record['applied']['result'] == 'applied' for record in gateway.load()['records'].values())


@pytest.mark.parametrize('drift', ['missing', 'wrong-address'])
def test_awg_drift_repaired_once_then_verified(engine, registry, drift):
    gateway, current, live, initial = engine
    gateway.accept(envelope(registry))
    if drift == 'missing':
        live['awg'].remove(initial['public_key'])
    else:
        live['addresses'][initial['public_key']] = '10.1.0.99/32'
    gateway.apply()
    assert live['sets'] == [(initial['public_key'], '10.1.0.2/32')]
    gateway.apply()
    assert len(live['sets']) == 1


def test_unsuccessful_awg_repair_fails_readback(engine, registry):
    gateway, current, live, initial = engine
    gateway.accept(envelope(registry))
    live['awg'].remove(initial['public_key'])
    gateway.gateway.add_peer = lambda *args: None
    with pytest.raises(ValueError, match='ENGINE_READBACK_MISMATCH'):
        gateway.apply()


@pytest.mark.parametrize('payload', [[], {'users': None}, {'users': [{}]}, {'error': 'unavailable'},
    {'users': [{'email': 'x', 'account': {'id': 'same'}}, {'email': 'y', 'account': {'id': 'same'}}]},
    {'users': [{'email': 'x', 'account': {'id': 'one'}}, {'email': 'x', 'account': {'id': 'two'}}]}])
def test_malformed_bulk_tcp_fails_closed(engine, registry, payload):
    gateway, current, live, initial = engine
    gateway.accept(envelope(registry))
    original = gateway.run
    gateway.run = lambda args: json.dumps(payload).encode() if args[1:3] == ['api', 'inbounduser'] else original(args)
    with pytest.raises(ValueError, match='INVALID_TCP_READBACK'):
        gateway.apply()


@pytest.mark.parametrize('drift', ['id', 'email', 'flow', 'split-binding'])
def test_tcp_requires_exact_same_account_binding(engine, registry, drift):
    gateway, current, live, initial = engine
    gateway.accept(envelope(registry))
    if drift == 'split-binding':
        live['tcp'][1]['id'] = initial['tcp_id']
        live['tcp'][0]['id'] = 'other'
    else:
        live['tcp'][0][drift] = 'other'
    with pytest.raises(ValueError, match='ENGINE_READBACK_MISMATCH'):
        gateway.apply()


def test_empty_bulk_tcp_can_confirm_denial(engine, registry):
    gateway, current, live, initial = engine
    event(registry)
    event(registry, 'expire', 'event-denied')
    gateway.accept(envelope(registry))
    original = gateway.run
    gateway.run = lambda args: b'{}' if args[1:3] == ['api', 'inbounduser'] else original(args)
    gateway.apply()
    assert initial['public_key'] not in live['awg']
    assert gateway.load()['records'][initial['device']]['applied']['allowed'] is False


def test_command_failure_never_produces_applied_ack(engine, registry):
    gateway, current, live, initial = engine
    gateway.accept(envelope(registry))
    original = gateway.run
    def failed(args):
        if args[1:3] == ['api', 'inbounduser']:
            raise subprocess.CalledProcessError(1, args)
        return original(args)
    gateway.run = failed
    with pytest.raises(subprocess.CalledProcessError):
        gateway.apply()
    assert gateway.load()['records'][initial['device']]['applied'] is None


def test_final_awg_snapshot_detects_concurrent_drift(engine, registry):
    gateway, current, live, initial = engine
    gateway.accept(envelope(registry))
    original = gateway.run
    def drift(args):
        result = original(args)
        if args[1:3] == ['api', 'inbounduser']:
            live['awg'].remove(initial['public_key'])
        return result
    gateway.run = drift
    with pytest.raises(ValueError, match='ENGINE_READBACK_MISMATCH'):
        gateway.apply()


@pytest.mark.parametrize('output', [b'key-only\n', b'key\t10.1.0.2/32\nkey\t10.1.0.3/32\n'])
def test_malformed_awg_snapshot_is_rejected(engine, output):
    gateway, current, live, initial = engine
    gateway.run = lambda args: output
    with pytest.raises(ValueError, match='INVALID_AWG_READBACK'):
        gateway.awg_snapshot()
