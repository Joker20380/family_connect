from copy import deepcopy
import json
from types import SimpleNamespace

import pytest

from control.friends import paid_beta, transport_membership, transport_policy as policy
from control.friends.transport_gateway import write
from test_transport_enforcement import engine, envelope, event, registry, NOW
from test_paid_beta import snapshot


def configure(registry):
    root = registry[0].path.parent
    write(root/'transport-enforcement.json', dict(schema=1, profile=policy.PROFILE, enabled=True,
        hosts={node: node for node in policy.NODES}))
    write(root/'transport-commands.json', {node: [node] for node in policy.NODES})


def test_all_node_preparation_lost_ack_retry_and_old_snapshot(engine, registry, monkeypatch):
    gateway, current, live, initial = engine
    noncohort = envelope(registry)
    gateway.accept(noncohort)
    configure(registry)
    before = snapshot(registry[0])
    prepared = {}
    failing = [True]

    def call(command, *, input, **kwargs):
        request = json.loads(input)
        node = command[0]
        assert request['operation'] == 'prepare' and request['paid']['node'] == node
        prepared[node] = request['token']
        if node == 'gateway-ru':
            with gateway.serialized():
                with gateway.lock():
                    gateway.prepare(request['paid'], request['token'])
                gateway.apply_serialized()
        if node == 'nl-amsterdam-1' and failing[0]:
            raise TimeoutError('lost acknowledgement after durable preparation')
        return SimpleNamespace(stdout=json.dumps(dict(schema=1,node=node,result='prepared',token=request['token'])).encode())

    monkeypatch.setattr(transport_membership.subprocess, 'run', call)
    with pytest.raises(paid_beta.PaidBetaError, match='TRANSPORT_PREPARATION_REQUIRED'):
        event(registry)
    assert snapshot(registry[0]) == before
    assert set(prepared) == {'gateway-ru','nl-amsterdam-1'}
    assert not gateway.peer_allowed(initial['public_key'])
    current[0] += policy.LEASE_SECONDS * 3
    gateway.accept(envelope(registry, current[0]))
    gateway.apply()
    assert not gateway.peer_allowed(initial['public_key'])
    assert gateway.load()['records'][initial['device']]['prepared']
    assert live['awg'] == {'foreign-key'}
    failing[0] = False
    event(registry, now=current[0], period_start=NOW, paid_until=NOW+3600)
    assert set(prepared) == set(policy.NODES) and len(set(prepared.values())) == 1
    gateway.accept(envelope(registry, current[0]))
    gateway.apply()
    assert gateway.peer_allowed(initial['public_key'])
    late = deepcopy(noncohort)
    late['observed_at'] = current[0] + 1
    late['decisions'][0].update(observed_at=current[0]+1,valid_until=current[0]+121)
    with pytest.raises(ValueError, match='TERMINAL'):
        gateway.accept(late)
    monkeypatch.setattr(transport_membership.subprocess, 'run', lambda *args, **kwargs: pytest.fail('replay must not prepare'))
    replay = event(registry, now=current[0]+2, period_start=NOW, paid_until=NOW+3600)
    assert replay['duplicate']


def test_noncohort_survives_outage_and_restart_but_identity_denial_is_retained(engine, registry, monkeypatch):
    gateway, current, live, initial = engine
    gateway.accept(envelope(registry))
    current[0] += 86400
    monkeypatch.setattr('control.friends.transport_gateway.boot_id', lambda: 'new-boot')
    gateway.apply()
    assert initial['public_key'] in live['awg'] and live['restarts'] == 0
    with registry[0].db() as database:
        database.execute('UPDATE devices SET revoked=1')
    gateway.accept(envelope(registry, current[0]))
    gateway.apply()
    assert not gateway.peer_allowed(initial['public_key'])
    current[0] += 86400
    gateway.apply()
    assert not gateway.peer_allowed(initial['public_key'])


@pytest.mark.parametrize('marker', ['', False, 0, 'invalid'])
def test_corrupt_preparation_marker_is_not_noncohort_allow(engine, registry, marker):
    gateway, current, live, initial = engine
    gateway.accept(envelope(registry))
    state = gateway.load()
    state['records'][initial['device']]['prepared'] = marker
    write(gateway.path, state)
    with pytest.raises(ValueError, match='INVALID_MEMBERSHIP_CACHE'):
        gateway.apply()


@pytest.mark.parametrize('reply', [b'{}', b'not-json', b'x'*1025])
def test_invalid_ack_never_commits_membership(registry, monkeypatch, reply):
    configure(registry)
    before = snapshot(registry[0])
    monkeypatch.setattr(transport_membership.subprocess, 'run', lambda *args, **kwargs: SimpleNamespace(stdout=reply))
    with pytest.raises(paid_beta.PaidBetaError, match='TRANSPORT_PREPARATION_REQUIRED'):
        event(registry)
    assert snapshot(registry[0]) == before
