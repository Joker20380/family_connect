import base64
import copy
import http.client
import importlib.util
import json
import sqlite3
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace

import pytest

from control.friends.access import Access, Rejected
from control.friends.gateway_routing import Policy, administer, canonical, digest, install, configuration as assigned
from control.friends.gateway_selection import configuration, load
from device_identity.friends import load_friends_identity
from provisioning.friends_catalog import GATEWAY_CHOICES, verify, verify_catalog
from provisioning.friends_store import FriendsConfigurationStore

ROOT = Path(__file__).resolve().parents[1]
VECTORS = json.loads((ROOT / 'tests/vectors/friends-selection-v3.json').read_bytes())
ANCHOR = base64.b64decode(VECTORS['anchor'])


@pytest.mark.parametrize('sample', VECTORS['cases'], ids=lambda sample: sample['name'])
def test_selection_vectors(sample):
    args = (sample['reply'], ANCHOR, VECTORS['device'], sample['target'], base64.b64decode(VECTORS['wireguard_key']))
    kwargs = dict(floor=sample['floor'], previous_hash=sample.get('previous_hash'))
    if sample['valid']:
        result = verify(*args, **kwargs)
        assert result.gateway_id == sample['target'] and result.country == 'nl'
        assert 'DEVICE_CREDENTIAL' not in result.tcp and 'LOCAL_DEVICE_KEY' not in result.awg
        assert sample['reply']['tcp_id'] not in repr(result)
    else:
        with pytest.raises(ValueError):
            verify(*args, **kwargs)
    with pytest.raises(ValueError):
        verify_catalog(sample['reply']['catalog'], ANCHOR)


@pytest.fixture
def node_selection(tmp_path):
    access = Access(tmp_path / 'access.db')
    access.initialize()
    identity = load_friends_identity(tmp_path / 'identity', create=True)
    challenge = access.challenge(identity.public_identity, identity.wireguard_public_key, 'activate', access.invite())
    access.complete(identity.prove_transport_key(challenge['challenge']), 'activate')
    envelopes = [canonical(envelope) for envelope in VECTORS['legacy_catalogs']]
    hashes = [digest(raw) for raw in envelopes]
    raw = canonical(dict(schema=1, generation=1, legacy=hashes[0], admit=hashes[1], catalogs=[
        dict(node=target, sha256=sha) for target, sha in zip((*GATEWAY_CHOICES, GATEWAY_CHOICES[0]), hashes)]))
    policy = Policy(raw, ANCHOR, dict(zip(hashes, envelopes)))
    directory = tmp_path / 'gateway-routing'
    directory.mkdir(mode=0o700)
    selection = canonical(VECTORS['cases'][0]['reply']['catalog'])
    files = {'anchor.pub': base64.b64encode(ANCHOR), policy.sha256 + '.policy.json': raw,
             digest(selection) + '.selection.json': selection}
    files.update({sha + '.catalog.json': envelope for sha, envelope in zip(hashes, envelopes)})
    for name, content in files.items():
        target = directory / name
        target.write_bytes(content)
        target.chmod(0o600)
    install(access, policy, envelopes[0])
    request = dict(schema=1, action='install-selection', operation_id='selection-test-01', policy_sha256=policy.sha256,
                   catalog_sha256=digest(selection), previous_sha256=None)
    return SimpleNamespace(access=access, identity=identity, root=tmp_path, directory=directory, request=request)


def response(identity, target):
    return dict(copy.deepcopy(VECTORS['cases'][0]['reply']), device=identity.reference, gateway_id=target)


def test_legacy_floor_and_identity_unchanged_by_alternating_selection(node_selection):
    owner = node_selection.identity
    path = node_selection.root / 'identity'
    legacy = FriendsConfigurationStore(path, owner, ANCHOR)
    legacy_reply = dict(response(owner, GATEWAY_CHOICES[0]), catalog=VECTORS['legacy_catalogs'][0])
    del legacy_reply['gateway_id']
    legacy.accept('nl', lambda *_: legacy_reply)
    baseline = {file.name: file.read_bytes() for file in path.iterdir() if file.is_file()}
    selected = FriendsConfigurationStore(path, owner, ANCHOR, selection=True)
    floors = []
    for target in GATEWAY_CHOICES * 3:
        def fetch(floor, previous):
            floors.append(floor)
            return response(owner, target)
        assert selected.accept(target, fetch).gateway_id == target
    assert floors == [0, 1, 1, 1, 1, 1]
    assert all((path / name).read_bytes() == raw for name, raw in baseline.items())
    assert (path / selected.name).stat().st_mode & 0o777 == 0o600
    assert legacy.accept('nl', lambda *_: legacy_reply).sequence == 4
    with pytest.raises(ValueError):
        selected.accept('nl', lambda *_: legacy_reply)
    with pytest.raises(ValueError):
        legacy.accept(GATEWAY_CHOICES[0], lambda *_: response(owner, GATEWAY_CHOICES[0]))


def test_operator_import_and_selection_preserve_sticky_assignment(node_selection):
    node = node_selection
    before = assigned(node.access, node.root, 'nl', node.identity.reference)
    assert administer(node.access, node.root, node.request)['result'] == 'SELECTION_CATALOG_INSTALLED'
    assert administer(node.access, node.root, node.request)['result'] == 'UNCHANGED'
    with pytest.raises(ValueError):
        administer(node.access, node.root, dict(node.request, previous_sha256='0' * 64))
    for target, host in zip(GATEWAY_CHOICES, ('192.0.2.20', '192.0.2.21')):
        envelope, selected = configuration(node.access, node.root, target, node.identity.reference)
        assert selected == host
        assert verify_catalog(envelope, ANCHOR, schema=3).sequence == 1
    assert assigned(node.access, node.root, 'nl', node.identity.reference) == before
    for action in ('UPDATE gateway_selection_events SET sequence=99', 'DELETE FROM gateway_selection_events'):
        with pytest.raises(sqlite3.IntegrityError), node.access.db() as database:
            database.execute(action)


@pytest.mark.parametrize('target', ['nl', 'ru', '../nl-amsterdam-1', 'nl-amsterdam-3', 'nl-amsterdam-1;id'])
def test_unknown_targets_rejected(node_selection, target):
    with pytest.raises(ValueError):
        configuration(node_selection.access, node_selection.root, target, node_selection.identity.reference)
    with pytest.raises(Rejected):
        node_selection.access.challenge(node_selection.identity.public_identity, node_selection.identity.wireguard_public_key, 'gateway:' + target)


def test_no_implicit_fallback_without_selection_catalog(node_selection):
    with pytest.raises(ValueError):
        configuration(node_selection.access, node_selection.root, GATEWAY_CHOICES[0], node_selection.identity.reference)


def test_signed_selection_must_match_admitted_native_templates(node_selection):
    policy = Policy.load(node_selection.directory, node_selection.request['policy_sha256'])
    for route in policy.routes.values():
        route['node'] = GATEWAY_CHOICES[1] if route['node'] == GATEWAY_CHOICES[0] else GATEWAY_CHOICES[0]
    with pytest.raises(ValueError):
        load(node_selection.root, policy, node_selection.request['catalog_sha256'])


def test_revoked_device_cannot_select_another_node(node_selection):
    node = node_selection
    administer(node.access, node.root, node.request)
    with node.access.db() as database:
        database.execute('UPDATE devices SET revoked=1 WHERE device=?', (node.identity.reference,))
    with pytest.raises(Rejected):
        configuration(node.access, node.root, GATEWAY_CHOICES[1], node.identity.reference)


def test_loopback_http_proof_binds_exact_target_and_routes_registration(node_selection, monkeypatch):
    node = node_selection
    administer(node.access, node.root, node.request)
    spec = importlib.util.spec_from_file_location('selection_http', ROOT / 'deploy/friends/access-api.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, 'ROOT', node.root)
    monkeypatch.setattr(module, 'access', node.access)
    commands = []
    def register(command, *, input, capture_output, timeout):
        record = json.loads(input)
        assert 'StrictHostKeyChecking=yes' in command and command[-1] == 'register'
        assert all(value not in ' '.join(command) for value in record.values())
        commands.append(command)
        return SimpleNamespace(returncode=0, stdout=canonical(dict(public_key=record['public_key'], address='10.83.0.2/32', transport='amneziawg-3.1')))
    monkeypatch.setattr(module.subprocess, 'run', register)
    server = ThreadingHTTPServer(('127.0.0.1', 0), module.Handler)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    def post(path, body):
        client = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=5)
        try:
            client.request('POST', path, canonical(body), {'Content-Type': 'application/json'})
            reply = client.getresponse()
            return reply.status, json.loads(reply.read())
        finally:
            client.close()
    try:
        for target, host in zip(GATEWAY_CHOICES * 2, ('192.0.2.20', '192.0.2.21') * 2):
            status, challenge = post('/friends/challenge', dict(public_identity=node.identity.public_identity,
                wireguard_public_key=node.identity.wireguard_public_key, purpose='gateway:' + target, invitation=''))
            assert status == 200
            proof = node.identity.prove_transport_key(challenge['challenge'])
            other = GATEWAY_CHOICES[1] if target == GATEWAY_CHOICES[0] else GATEWAY_CHOICES[0]
            assert post('/friends/gateway-configuration/' + other, proof)[0] == 403
            status, reply = post('/friends/gateway-configuration/' + target, proof)
            assert status == 200 and commands[-1][-2] == 'root@' + host
            assert verify(reply, ANCHOR, node.identity.reference, target, node.identity._wireguard_key.private_bytes_raw()).gateway_id == target
            assert post('/friends/gateway-configuration/' + target, proof)[0] == 403
        assert len(commands) == 4
        assert assigned(node.access, node.root, 'nl', node.identity.reference)[1] == '192.0.2.20'
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
