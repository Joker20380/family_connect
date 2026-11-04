import copy
import json

import pytest

from test_activated_maintenance import Cluster, activate, proof
from credential_renewal import Rejected, atomic, canonical, parse, read_private
from scripts.reconcile_unprepared_renewal import reconcile
from control.friends.restricted import iso
from test_multi_gateway_renewal import fleet


def issue_certificate(cluster):
    directory = json.loads(cluster.service.seed_source())
    directory.update(issued_at=iso(cluster.now), expires_at=iso(cluster.now + 1800))
    cluster.service.seed_source = lambda: canonical(directory)
    return cluster.service.fetch(proof(cluster.service, cluster.device))


def interrupted(cluster, change):
    cluster.now += 12000
    node = cluster.nodes['RU']
    original = node.barrier.quiesce
    fired = False

    def quiesce():
        nonlocal fired
        original()
        if not fired:
            fired = True
            change()

    node.barrier.quiesce = quiesce
    result = cluster.scheduled('unprepared')
    assert result['result'] == 'RECOVERY_REQUIRED'
    record = parse(read_private(cluster.controller.root / 'transaction.json'))
    assert record['first_cause'] == 'STALE_NODE_STATE'
    assert record['quiesced'] == []
    return record['operation_id']


@pytest.mark.parametrize('change', ['activation', 'certificate'])
def test_reconcile_preserves_live_database_and_recovers(tmp_path, change):
    cluster = Cluster(tmp_path)
    mutation = lambda: activate(cluster.service)
    if change == 'certificate':
        mutation = lambda: issue_certificate(cluster)
    operation = interrupted(cluster, mutation)
    node = cluster.nodes['RU']
    before = node.database.snapshot()
    owner = read_private(node.state / 'owner.json')
    assert reconcile(cluster.controller, node, operation)['result'] == 'UNPREPARED_RECONCILABLE'
    assert read_private(node.state / 'owner.json') == owner
    result = reconcile(cluster.controller, node, operation, apply=True)
    assert result['database_writes'] == result['grant_writes'] == result['authority_writes'] == 0
    assert node.database.snapshot() == before
    assert all(remote.barrier.stopped() for remote in cluster.nodes.values())
    record = parse(read_private(cluster.controller.root / 'transaction.json'))
    assert cluster.controller.recover(record)['result'] == 'ABORTED'
    assert node.database.snapshot() == before
    assert all(not remote.barrier.stopped() for remote in cluster.nodes.values())
    assert cluster.scheduled('after-reconcile')['result'] == 'COMMITTED'


@pytest.mark.parametrize('point', ['intent', 'owner', 'record'])
def test_reconcile_replays_interrupted_metadata_write(tmp_path, point):
    cluster = Cluster(tmp_path)
    operation = interrupted(cluster, lambda: activate(cluster.service))
    node = cluster.nodes['RU']

    def fault(event):
        if event == point:
            raise OSError('simulated interruption')

    with pytest.raises(OSError):
        reconcile(cluster.controller, node, operation, apply=True, fault=fault)
    assert reconcile(cluster.controller, node, operation, apply=True)['result'] == 'UNPREPARED_RECONCILED'
    record = parse(read_private(cluster.controller.root / 'transaction.json'))
    assert cluster.controller.recover(record)['result'] == 'ABORTED'


@pytest.mark.parametrize('change', ['activation', 'certificate'])
def test_three_node_reconcile_then_common_renewal(fleet, change):
    operation = interrupted(fleet, lambda: activate(fleet.service) if change == 'activation' else issue_certificate(fleet))
    node = fleet.nodes['RU']
    before = node.database.snapshot()
    identities = copy.deepcopy(fleet.identities)
    assert reconcile(fleet.controller, node, operation, apply=True)['result'] == 'UNPREPARED_RECONCILED'
    record = parse(read_private(fleet.controller.root / 'transaction.json'))
    assert fleet.controller.recover(record)['result'] == 'ABORTED'
    assert node.database.snapshot() == before
    assert fleet.scheduled('after-reconcile')['result'] == 'COMMITTED'
    assert fleet.identities == identities
    assert all(not remote.barrier.stopped() for remote in fleet.nodes.values())


def test_reconcile_refuses_secondary_drift(fleet):
    operation = interrupted(fleet, lambda: activate(fleet.service))
    node = fleet.nodes['RU']
    fleet.nodes['NL2'].policy_paths = {'extra': fleet.nodes['NL2'].live / 'policy'}
    atomic(fleet.nodes['NL2'].live / 'policy', b'changed')
    before = read_private(node.state / 'owner.json')
    with pytest.raises(Rejected, match='NON_DATABASE_STATE_CHANGED'):
        reconcile(fleet.controller, node, operation, apply=True)
    assert read_private(node.state / 'owner.json') == before


@pytest.mark.parametrize('failure', ['prepared', 'commit', 'owner', 'policy', 'expired', 'revoked', 'operation', 'changed_after_intent'])
def test_reconcile_refuses_unsafe_state_without_metadata_writes(tmp_path, failure):
    cluster = Cluster(tmp_path)
    operation = interrupted(cluster, lambda: issue_certificate(cluster))
    node = cluster.nodes['RU']
    marker = cluster.controller.root / 'transaction.json'
    owner_path = node.state / 'owner.json'
    if failure == 'prepared':
        atomic(node.state / 'prepared-plan.json', canonical({}))
    elif failure == 'commit':
        record = parse(read_private(marker)); record['commit_decided'] = True
        atomic(marker, canonical(record))
    elif failure == 'owner':
        owner = parse(read_private(owner_path)); owner['state'] = 'QUIESCED'
        atomic(owner_path, canonical(owner))
    elif failure == 'policy':
        node.policy_paths = {'extra': tmp_path / 'policy'}
        atomic(tmp_path / 'policy', b'changed')
    elif failure == 'expired':
        cluster.now += 8000
    elif failure == 'revoked':
        with cluster.service.access.db() as database:
            database.execute('UPDATE devices SET revoked=1 WHERE device=?', (cluster.device.reference,))
    elif failure == 'operation':
        operation = 'test-other-operation-wrong'
    elif failure == 'changed_after_intent':
        def fault(event):
            if event == 'intent':
                raise OSError('simulated interruption')
        with pytest.raises(OSError):
            reconcile(cluster.controller, node, operation, apply=True, fault=fault)
        activate(cluster.service)
    before = (read_private(marker), read_private(owner_path), copy.deepcopy(node.database.snapshot()))
    with pytest.raises(Rejected):
        reconcile(cluster.controller, node, operation, apply=True)
    assert (read_private(marker), read_private(owner_path), node.database.snapshot()) == before
    assert all(remote.barrier.stopped() for remote in cluster.nodes.values())
