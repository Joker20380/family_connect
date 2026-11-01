import base64
import copy
import importlib.util
import json
import os
import http.client
import threading
from pathlib import Path
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from http.server import ThreadingHTTPServer
from types import SimpleNamespace

import pytest

from control.friends.access import Access, Rejected
from control.friends.gateway_routing import Policy, administer, canonical, configuration, digest, install, move, replace_policy
from device_identity.device import DeviceIdentity
from provisioning.friends_catalog import verify


ROOT = Path(__file__).resolve().parents[1]
VECTORS = json.loads((ROOT / 'tests/vectors/friends-multinode-v2.json').read_text())


def activate(access):
    identity = DeviceIdentity.generate()
    challenge = access.challenge(identity.public_identity, identity.wireguard_public_key, 'activate', access.invite())
    access.complete(identity.prove_transport_key(challenge['challenge']), 'activate')
    return identity


@pytest.fixture
def routing(tmp_path):
    access = Access(tmp_path / 'access.db')
    access.initialize()
    owner = activate(access)
    envelopes = [canonical(case['reply']['catalog']) for case in VECTORS['cases']]
    hashes = [digest(raw) for raw in envelopes]
    value = dict(schema=1, generation=1, legacy=hashes[0], admit=hashes[1], catalogs=[
        dict(node=node, sha256=sha256) for node, sha256 in zip(('nl-first', 'nl-second', 'nl-first'), hashes)])
    raw = canonical(value)
    anchor = base64.b64decode(VECTORS['anchor'])
    policy = Policy(raw, anchor, dict(zip(hashes, envelopes)))
    directory = tmp_path / 'gateway-routing'
    directory.mkdir(mode=0o700)
    files = {'anchor.pub': base64.b64encode(anchor), policy.sha256 + '.policy.json': raw}
    files.update({sha256 + '.catalog.json': envelope for sha256, envelope in zip(hashes, envelopes)})
    for name, content in files.items():
        target = directory / name
        target.write_bytes(content)
        target.chmod(0o600)
    return dict(access=access, owner=owner, policy=policy, hashes=hashes, directory=directory,
                root=tmp_path, envelopes=envelopes, anchor=anchor)


def enable(routing):
    return install(routing['access'], routing['policy'], routing['envelopes'][0])


def read_route(routing, identity, country='nl'):
    return configuration(routing['access'], routing['root'], country, identity.reference)


def test_existing_device_and_both_countries_stay_on_same_catalog(routing):
    result = enable(routing)
    assert result['preserved_devices'] == 1
    assert install(routing['access'], routing['policy'], routing['envelopes'][0])['result'] == 'UNCHANGED'
    old = read_route(routing, routing['owner'])
    assert old[1] == '192.0.2.20'
    assert read_route(routing, routing['owner'], 'ru')[0] == old[0]
    new = activate(routing['access'])
    second = read_route(routing, new)
    assert second[1] == '192.0.2.21'
    assert read_route(routing, new, 'ru')[0] == second[0]
    assert read_route(routing, routing['owner']) == old


def test_unconfigured_backend_preserves_legacy_path(routing):
    assert read_route(routing, routing['owner']) is None


def test_concurrent_first_assignment_is_durable_and_unique(routing):
    enable(routing)
    new = activate(routing['access'])
    with ThreadPoolExecutor(8) as pool:
        results = list(pool.map(lambda unused: read_route(routing, new), range(16)))
    assert all(result == results[0] for result in results)
    with routing['access'].db() as database:
        assert database.execute('SELECT COUNT(*) FROM gateway_assignments WHERE device=?', (new.reference,)).fetchone()[0] == 1


@pytest.mark.parametrize('field', ['devices', 'invites'])
def test_revoked_devices_cannot_obtain_or_create_assignment(routing, field):
    enable(routing)
    with routing['access'].db() as database:
        database.execute('UPDATE '+field+' SET revoked=1 WHERE device=?', (routing['owner'].reference,))
    with pytest.raises(Rejected):
        read_route(routing, routing['owner'])


def test_unregistered_device_is_rejected(routing):
    enable(routing)
    with pytest.raises(Rejected):
        read_route(routing, DeviceIdentity.generate())


@pytest.mark.parametrize('name', ['anchor.pub', 'policy', 'catalog'])
@pytest.mark.parametrize('failure', ['missing', 'symlink', 'hardlink', 'mode', 'tamper'])
def test_broken_policy_fails_closed_without_legacy_fallback(routing, name, failure):
    enable(routing)
    name = {'policy': routing['policy'].sha256+'.policy.json', 'catalog': routing['hashes'][1]+'.catalog.json'}.get(name, name)
    target = routing['directory'] / name
    if failure == 'missing':
        target.unlink()
    elif failure == 'symlink':
        other = target.with_suffix('.original')
        target.rename(other)
        target.symlink_to(other)
    elif failure == 'hardlink':
        os.link(target, target.with_suffix('.hardlink'))
    elif failure == 'mode':
        target.chmod(0o644)
    else:
        target.write_bytes(b'{}')
    with pytest.raises((ValueError, OSError)):
        read_route(routing, routing['owner'])


@pytest.mark.parametrize('change', ['traversal', 'duplicate', 'generation', 'unknown', 'wrong_node_host', 'same_host_two_nodes'])
def test_invalid_policy_rejected(routing, change):
    value = copy.deepcopy(routing['policy'].value)
    if change == 'traversal':
        value['catalogs'][0]['sha256'] = '../anchor.pub'
    elif change == 'duplicate':
        value['catalogs'].append(value['catalogs'][0])
    elif change == 'generation':
        value['generation'] = True
    elif change == 'unknown':
        value['command'] = 'register; false'
    elif change == 'wrong_node_host':
        value['catalogs'][1]['node'] = 'nl-first'
    else:
        value['catalogs'][2]['node'] = 'nl-other'
    with pytest.raises(ValueError):
        Policy(canonical(value), routing['anchor'], dict(zip(routing['hashes'], routing['envelopes'])))


def test_install_failure_does_not_commit_partial_schema(routing):
    with routing['access'].db() as database:
        database.execute('CREATE TABLE gateway_assignment_events (unrelated INTEGER)')
    with pytest.raises(sqlite3.OperationalError):
        enable(routing)
    with routing['access'].db() as database:
        assert database.execute("SELECT name FROM sqlite_master WHERE name='gateway_assignments'").fetchone() is None
        assert database.execute("SELECT name FROM sqlite_master WHERE name='gateway_routing_state'").fetchone() is None


def test_install_requires_exact_predecessor(routing):
    with pytest.raises(ValueError):
        install(routing['access'], routing['policy'], routing['envelopes'][1])


def test_explicit_move_rollback_replay_and_conflict(routing):
    enable(routing)
    access, policy, device = routing['access'], routing['policy'], routing['owner'].reference
    first, second, rollback = routing['hashes']
    args = dict(device=device, expected=first, destination=second, operation_id='operation-forward')
    assert move(access, policy, **args)['result'] == 'ASSIGNED'
    assert move(access, policy, **args)['result'] == 'UNCHANGED'
    assert read_route(routing, routing['owner'])[1] == '192.0.2.21'
    with pytest.raises(ValueError):
        move(access, policy, **{**args, 'destination': rollback})
    with pytest.raises(ValueError):
        move(access, policy, device=device, expected=second, destination=first, operation_id='operation-rollback')
    move(access, policy, device=device, expected=second, destination=rollback, operation_id='operation-rollback')
    assert read_route(routing, routing['owner'])[1] == '192.0.2.20'
    for statement in ('UPDATE gateway_assignment_events SET device=?', 'DELETE FROM gateway_assignment_events WHERE device=?'):
        with pytest.raises(sqlite3.IntegrityError):
            with access.db() as database:
                database.execute(statement, (device,))


def test_policy_change_does_not_reassign_devices(routing):
    enable(routing)
    new = activate(routing['access'])
    before = read_route(routing, new)
    value = {**routing['policy'].value, 'generation': 2, 'admit': routing['hashes'][2]}
    raw = canonical(value)
    updated = Policy(raw, routing['anchor'], dict(zip(routing['hashes'], routing['envelopes'])))
    target = routing['directory'] / (updated.sha256+'.policy.json')
    target.write_bytes(raw)
    target.chmod(0o600)
    replace_policy(routing['access'], routing['policy'], updated)
    assert read_route(routing, new) == before
    assert read_route(routing, activate(routing['access']))[1] == '192.0.2.20'


@pytest.mark.parametrize('case', VECTORS['cases'], ids=lambda case: case['name'])
def test_linux_verifies_each_physical_node_with_unchanged_parser(case):
    reply = case['reply']
    result = verify(reply, base64.b64decode(VECTORS['anchor']), VECTORS['device'], 'nl',
                    base64.b64decode(VECTORS['wireguard_key']), floor=case['sequence'])
    assert json.loads(result.tcp)['server'] == case['host']
    assert 'Endpoint = '+case['host']+':' in result.awg
    with pytest.raises(ValueError):
        verify(reply, base64.b64decode(VECTORS['anchor']), VECTORS['device'], 'nl',
               base64.b64decode(VECTORS['wireguard_key']), floor=case['sequence']+1)


def test_backend_handler_uses_authenticated_device_assignment(routing, monkeypatch):
    spec = importlib.util.spec_from_file_location('routing_test_handler', ROOT / 'deploy/friends/access-api.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, 'ROOT', routing['root'])
    monkeypatch.setattr(module, 'access', routing['access'])
    enable(routing)
    new = activate(routing['access'])
    assert module.configuration_catalog('nl', routing['owner'].reference)[1] == '192.0.2.20'
    assert module.configuration_catalog('nl', new.reference)[1] == '192.0.2.21'
    with pytest.raises(Rejected):
        module.configuration_catalog('nl', DeviceIdentity.generate().reference)


def test_real_http_proof_routes_registration_and_never_exposes_admin(routing, monkeypatch):
    spec = importlib.util.spec_from_file_location('routing_http_test', ROOT / 'deploy/friends/access-api.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, 'ROOT', routing['root'])
    monkeypatch.setattr(module, 'access', routing['access'])
    enable(routing)
    new = activate(routing['access'])
    commands = []
    def registration(command, *, input, capture_output, timeout):
        record = json.loads(input)
        assert set(record) == {'device', 'public_key', 'tcp_id'}
        assert capture_output is True and timeout == 15
        assert command[-1] == 'register'
        assert 'StrictHostKeyChecking=yes' in command
        assert record['device'] not in ' '.join(command)
        assert record['public_key'] not in ' '.join(command)
        assert record['tcp_id'] not in ' '.join(command)
        commands.append(command)
        return SimpleNamespace(returncode=0, stdout=canonical(dict(public_key=record['public_key'],
                               address='10.83.0.2/32', transport='amneziawg-3.1')))
    monkeypatch.setattr(module.subprocess, 'run', registration)
    server = ThreadingHTTPServer(('127.0.0.1', 0), module.Handler)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    def request(path, body):
        connection = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=5)
        try:
            connection.request('POST', path, canonical(body), {'Content-Type': 'application/json'})
            response = connection.getresponse()
            return response.status, json.loads(response.read())
        finally:
            connection.close()
    try:
        for identity, host in ((routing['owner'], '192.0.2.20'), (new, '192.0.2.21')):
            status, challenge = request('/friends/challenge', dict(public_identity=identity.public_identity,
                wireguard_public_key=identity.wireguard_public_key, purpose='nl', invitation=''))
            assert status == 200
            proof = identity.prove_transport_key(challenge['challenge'])
            status, reply = request('/friends/configuration/nl', proof)
            assert status == 200 and commands[-1][-2] == 'root@'+host
            accepted = verify(reply, routing['anchor'], identity.reference, 'nl', identity._wireguard_key.private_bytes_raw())
            assert json.loads(accepted.tcp)['server'] == host
            previous = len(commands)
            assert request('/friends/configuration/nl', proof)[0] == 403
            assert len(commands) == previous
        assert request('/friends/gateway-routing', dict(action='install'))[0] == 404
        assert len(commands) == 2
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        assert not thread.is_alive()


def test_assignment_journal_failure_rolls_back_route(routing):
    enable(routing)
    with routing['access'].db() as database:
        database.execute("CREATE TRIGGER fail_event BEFORE INSERT ON gateway_assignment_events "
                         "BEGIN SELECT RAISE(ABORT, 'injected event failure'); END")
    with pytest.raises(sqlite3.IntegrityError):
        move(routing['access'], routing['policy'], device=routing['owner'].reference,
             expected=routing['hashes'][0], destination=routing['hashes'][1], operation_id='injected-failure')
    assert read_route(routing, routing['owner'])[1] == '192.0.2.20'


def test_policy_generation_corruption_fails_closed(routing):
    enable(routing)
    with routing['access'].db() as database:
        database.execute('UPDATE gateway_routing_state SET generation=generation+1')
    with pytest.raises(ValueError):
        read_route(routing, routing['owner'])


@pytest.mark.parametrize('damage', ['signature', 'anchor'])
def test_correct_file_hash_cannot_replace_signature_verification(routing, damage):
    envelopes = list(routing['envelopes'])
    anchor = routing['anchor']
    if damage == 'signature':
        envelope = json.loads(envelopes[1])
        envelope['signature'] = base64.b64encode(bytes(64)).decode()
        envelopes[1] = canonical(envelope)
    else:
        anchor = bytes(32)
    hashes = [digest(raw) for raw in envelopes]
    value = copy.deepcopy(routing['policy'].value)
    value['legacy'], value['admit'] = hashes[:2]
    for record, sha256 in zip(value['catalogs'], hashes):
        record['sha256'] = sha256
    with pytest.raises(ValueError):
        Policy(canonical(value), anchor, dict(zip(hashes, envelopes)))


def test_operator_request_is_bound_safe_and_replayable(routing):
    root = routing['root']
    root.chmod(0o700)
    legacy = root / 'catalog.json'
    legacy.write_bytes(routing['envelopes'][0])
    legacy.chmod(0o600)
    access = routing['access']
    assert administer(access, root, dict(schema=1, action='status'))['result'] == 'LEGACY_SINGLE_NL'
    request = dict(schema=1, action='install', operation_id='install-operation-1',
                   policy_sha256=routing['policy'].sha256, legacy_sha256=routing['hashes'][0])
    assert administer(access, root, request)['result'] == 'INSTALLED'
    assert administer(access, root, request)['result'] == 'UNCHANGED'
    with pytest.raises(ValueError):
        administer(access, root, {**request, 'legacy_sha256': routing['hashes'][1]})
    result = administer(access, root, dict(schema=1, action='status'))
    assert result['dataplane_acceptance'] == 'NOT_CHECKED'
    assert result['restricted_routing'] == 'UNCHANGED'
    assert result['assigned_counts'] == {'nl-first': 1}
    assert routing['owner'].reference not in json.dumps(result)
    assert routing['owner'].public_identity not in json.dumps(result)


@pytest.mark.parametrize('payload', [
    {'schema': True, 'action': 'status'}, {'schema': 1, 'action': 'retire'},
    {'schema': 1, 'action': 'status', 'command': 'echo invalid'},
    {'schema': 1, 'action': 'assign', 'device': '../escape'},
    {'schema': 1, 'action': ['status']},
])
def test_operator_unknown_and_injected_requests_fail_closed(routing, payload):
    with pytest.raises(ValueError):
        administer(routing['access'], routing['root'], payload)
    assert administer(routing['access'], routing['root'], dict(schema=1, action='status'))['result'] == 'LEGACY_SINGLE_NL'
