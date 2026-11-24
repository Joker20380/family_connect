import base64
from contextlib import closing
from copy import deepcopy
import io
import json
import os
import sqlite3
from types import SimpleNamespace
import uuid
import zipfile

import pytest

from control.friends import transport_policy as policy
from control.friends.access import Access
from scripts import control_ha_joint_nodes as joint
from scripts import control_ha_node_capture as capture
from scripts import control_ha_node_restore as recovery
from scripts import control_ha_node_qualify as native
from scripts.control_ha_import import digest, encoded, import_snapshot
from scripts.paid_postgres_rehearsal import snapshot
from scripts.referral_postgres_rehearsal import NOW
from tests.test_control_ha_import import repository
from tests.test_control_ha_installed_composite import source, prepared


def reseal(point):
    point.manifest['files'] = {name: dict(bytes=len(raw), sha256=digest(raw)) for name, raw in point.files.items()}
    capsule, checkpoint = recovery.seal(capture.archive(point.files, point.manifest), point.key)
    return capsule, point.key, checkpoint


@pytest.fixture
def inputs(source, monkeypatch):
    canonical = prepared(source)
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, 'w') as bundle:
        for name in ('transport_gateway.py', 'transport_policy.py'):
            relative = 'control/friends/' + name
            bundle.writestr(relative, (native.SOURCE / relative).read_bytes())
    points = {}
    for slot, node in capture.NODES.items():
        with closing(sqlite3.connect(':memory:')) as database:
            database.deserialize(source[0]['registry'])
            database.row_factory = sqlite3.Row
            decisions = policy.read_snapshot(database, node, NOW)['decisions']
        with closing(sqlite3.connect(':memory:')) as database:
            database.execute(recovery.PEER_SCHEMA[1][3])
            database.executemany('INSERT INTO peers(public) VALUES (?)', [(row['public_key'],) for row in decisions])
            database.execute("UPDATE sqlite_sequence SET seq=7 WHERE name='peers'")
            database.commit()
            peers = database.serialize()
        boot = str(uuid.uuid4())
        network = '10.84' if slot == 'RU' else '10.83'
        files = {'settings.json': encoded(dict(network=network+'.0.0/16', address=network+'.0.1/16', external='ens3')),
            'state.json': encoded(dict(schema=1, node=node, observed_at=NOW, records={row['device']:
                dict(decision=row, boot=boot, deadline=220.0, applied=None, prepared=None) for row in decisions})),
            'enforcement.json': encoded(dict(schema=1, profile=policy.PROFILE, node=node, enabled=True)),
            'server.conf': b'fixture-only', 'tcp.json': b'{"inbounds":[]}', 'peers.sqlite': peers,
            'gateway.py': (native.SOURCE / 'deploy/friends/awg-gateway.py').read_bytes(),
            'transport.pyz': archive.getvalue()}
        monkeypatch.setitem(capture.SOURCES, slot, tuple(digest(files[name]) for name in ('gateway.py', 'transport.pyz')))
        manifest = dict(purpose=capture.PURPOSE, slot=slot, node=node, boot=boot, monotonic=101.0,
            locked_at_ns=(NOW+1)*10**9, captured_at_ns=(NOW+1)*10**9+1000000,
            barrier_seconds=.001, deadline_seconds=.25, fleet_fence=False, activation=False, files={})
        points[slot] = SimpleNamespace(files=files, manifest=manifest, key=os.urandom(32))
    return canonical, source[0]['registry'], points


def preflight(inputs):
    canonical, registry, points = inputs
    return joint.prepare(canonical, {slot: reseal(point) for slot, point in points.items()})


def compare_sqlite(inputs, prepared_joint=None):
    with closing(sqlite3.connect(':memory:')) as database:
        database.deserialize(inputs[1])
        database.row_factory = sqlite3.Row
        database.execute('PRAGMA query_only=ON')
        return joint.compare(database, prepared_joint or preflight(inputs))


def test_all_nodes_native_bindings_and_gap_without_renewal(inputs):
    before = deepcopy(inputs[2])
    prepared_joint = preflight(inputs)
    receipt = compare_sqlite(inputs, prepared_joint)
    assert receipt['allocated_peers'] == receipt['decisions'] > 0
    assert all(item['sequence_floor'] == 7 for item in receipt['nodes'].values())
    assert receipt['comparison_time'] == 'ORIGINAL_DECISION_TIME'
    assert all(receipt[name] is False for name in ('activation', 'fleet_fence', 'independent_forward_trust', 'full_recovery'))
    assert 'key' not in repr(prepared_joint) and 'decision' not in repr(prepared_joint)
    assert all(inputs[2][slot].files == point.files for slot, point in before.items())


@pytest.mark.parametrize('kind', ('missing', 'extra', 'wrong-node', 'stale-pin', 'wrong-key', 'source-drift'))
def test_authentication_and_exact_three_node_scope(inputs, kind):
    capsules = {slot: reseal(point) for slot, point in inputs[2].items()}
    if kind == 'missing': del capsules['NL2']
    elif kind == 'extra': capsules['unexpected'] = capsules['RU']
    elif kind == 'wrong-node': capsules['NL2'] = capsules['NL1']
    elif kind == 'stale-pin': capsules['RU'][2]['archive_sha256'] = '0'*64
    elif kind == 'wrong-key': capsules['RU'] = (capsules['RU'][0], b'X'*32, capsules['RU'][2])
    else:
        point = inputs[2]['RU']
        point.files['gateway.py'] += b'\n'
        with pytest.raises(ValueError, match='INSTALLED_SOURCE_CHANGED'): reseal(point)
        return
    with pytest.raises(ValueError): joint.prepare(inputs[0], capsules)


@pytest.mark.parametrize('field', ('public_key', 'tcp_id', 'revision', 'paid_until', 'grace_until',
                                  'identity_allowed', 'allowed', 'valid_until', 'device', 'missing'))
def test_individually_valid_receiver_drift_refuses_joint_pass(inputs, field):
    point = inputs[2]['NL1']
    state = json.loads(point.files['state.json'])
    identity, cached = next((identity, cached) for identity, cached in state['records'].items()
                            if cached['decision']['allowed'] and cached['decision']['cohort'])
    decision = cached['decision']
    if field == 'public_key':
        previous = decision[field]
        decision[field] = base64.b64encode(b'X'*32).decode()
        with closing(sqlite3.connect(':memory:')) as database:
            database.deserialize(point.files['peers.sqlite'])
            database.execute('UPDATE peers SET public=? WHERE public=?', (decision[field], previous))
            database.commit()
            point.files['peers.sqlite'] = database.serialize()
    elif field == 'tcp_id': decision[field] = str(uuid.uuid4())
    elif field in ('revision', 'paid_until'): decision[field] += 1
    elif field == 'grace_until': decision[field] = decision['paid_until'] + 60
    elif field == 'identity_allowed': decision[field] = False; decision['allowed'] = False
    elif field == 'allowed': decision[field] = False
    elif field == 'valid_until': decision[field] -= 1
    elif field == 'device':
        decision[field] = 'f'*32
        state['records']['f'*32] = state['records'].pop(identity)
    else:
        del state['records'][identity]
        with closing(sqlite3.connect(':memory:')) as database:
            database.deserialize(point.files['peers.sqlite'])
            database.execute('DELETE FROM peers WHERE public=?', (decision['public_key'],))
            database.commit()
            point.files['peers.sqlite'] = database.serialize()
    point.files['state.json'] = encoded(state)
    prepared_joint = preflight(inputs)
    with pytest.raises(ValueError, match='CANONICAL_RECEIVER_DECISION_MISMATCH|RECEIVER_DEVICE_COVERAGE'):
        compare_sqlite(inputs, prepared_joint)


def test_custody_changes_are_bound_but_do_not_extend_authority(inputs):
    original = preflight(inputs)
    inputs[2]['RU'].files['tcp.json'] = b'{"inbounds":[],"fixture":true}'
    changed = preflight(inputs)
    assert original.fingerprint != changed.fingerprint
    assert compare_sqlite(inputs, changed)['full_recovery'] is False
    assert dict(original.points[-1][1])['tcp.json'] == b'{"inbounds":[]}'


def test_postgres_native_parity_revocation_and_restart(inputs, repository, tmp_path):
    prepared_joint = preflight(inputs)
    import_snapshot(repository, inputs[0].snapshot)
    before = snapshot(repository)
    with repository.transaction() as transaction:
        assert joint.compare(transaction.paid(), prepared_joint) == compare_sqlite(inputs, prepared_joint)
        identity = transaction.paid().devices()[0]['device']
    assert snapshot(repository) == before
    assert Access(None, enrollment_repository=repository).revoke_device(identity)
    revoked = snapshot(repository)
    delivery = joint.revocation_readback(repository, prepared_joint, identity, tmp_path, NOW+2)
    assert len(delivery) == 3 and all(item['native_commands_executed'] == 0 for item in delivery.values())
    assert snapshot(repository) == revoked
    with repository.transaction() as transaction:
        with pytest.raises(ValueError, match='CANONICAL_RECEIVER_DECISION_MISMATCH'):
            joint.compare(transaction.paid(), prepared_joint)
