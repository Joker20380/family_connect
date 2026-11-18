import copy

import pytest

from test_activated_maintenance import activate
from test_multi_gateway_renewal import fleet
from test_reconcile_unprepared_renewal import interrupted
from credential_renewal import Rejected, atomic, canonical, read_private
from scripts.finish_unprepared_expired_renewal import begin, complete, finish_node


def expired(fleet):
    operation = interrupted(fleet, lambda: activate(fleet.service))
    fleet.now += 8000
    return operation


def test_expired_unprepared_completion_never_resumes_or_restores_database(fleet):
    operation = expired(fleet)
    before = copy.deepcopy(fleet.nodes['RU'].database.snapshot())
    marker = read_private(fleet.controller.root / 'transaction.json')
    assert begin(fleet.controller, fleet.nodes['RU'], operation)['result'] == 'EXPIRED_UNPREPARED_RECONCILABLE'
    assert read_private(fleet.controller.root / 'transaction.json') == marker
    intent = begin(fleet.controller, fleet.nodes['RU'], operation, apply=True)
    for node in fleet.nodes.values():
        assert finish_node(node, intent)['result'] == 'EXPIRED_UNPREPARED_NODE_READY'
        assert finish_node(node, intent, apply=True)['readers_resumed'] is False
        assert finish_node(node, intent, apply=True)['readers_resumed'] is False
    assert begin(fleet.controller, fleet.nodes['RU'], operation, apply=True) == intent
    assert complete(fleet.controller, intent)['result'] == 'ROLLED_BACK_READERS_STOPPED'
    assert complete(fleet.controller, intent)['result'] == 'ROLLED_BACK_READERS_STOPPED'
    assert fleet.nodes['RU'].database.snapshot() == before
    assert all(node.barrier.stopped() and not (node.state / 'owner.json').exists() for node in fleet.nodes.values())
    assert fleet.scheduled('after-expired-unprepared')['result'] == 'COMMITTED'


@pytest.mark.parametrize('failure', ['active', 'artifact', 'owner', 'profile', 'intent'])
def test_node_rejects_unsafe_state_without_mutation(fleet, failure):
    operation = expired(fleet)
    intent = begin(fleet.controller, fleet.nodes['RU'], operation, apply=True)
    node = fleet.nodes['NL2']
    if failure == 'active':
        node.barrier.quiet = False
    elif failure == 'artifact':
        atomic(node.state / 'prepared-plan.json', canonical({}))
    elif failure == 'owner':
        node.operation.advance(node.owner(operation), 'QUIESCED')
    elif failure == 'profile':
        node.policy_paths = {'unexpected': node.live / 'extra'}
        atomic(node.live / 'extra', b'changed')
    else:
        intent['binding']['before_sha256'] = '0' * 64
    owner = read_private(node.state / 'owner.json')
    with pytest.raises(Rejected):
        finish_node(node, intent, apply=True)
    assert read_private(node.state / 'owner.json') == owner


@pytest.mark.parametrize('failure', ['not_expired', 'pending_revocation', 'authority_expired'])
def test_begin_rejects_unsafe_predecessor(fleet, failure):
    operation = interrupted(fleet, lambda: activate(fleet.service))
    if failure != 'not_expired':
        fleet.now += 8000
    if failure == 'pending_revocation':
        original = fleet.controller.read
        fleet.controller.read = lambda operation: (*original(operation)[:3], True)
    if failure == 'authority_expired':
        fleet.now += 100 * 86400
    marker = read_private(fleet.controller.root / 'transaction.json')
    owner = read_private(fleet.nodes['RU'].state / 'owner.json')
    with pytest.raises(Rejected):
        begin(fleet.controller, fleet.nodes['RU'], operation, apply=True)
    assert read_private(fleet.controller.root / 'transaction.json') == marker
    assert read_private(fleet.nodes['RU'].state / 'owner.json') == owner


def test_complete_refuses_unfinished_node_and_resumes_from_partial_finish(fleet):
    operation = expired(fleet)
    intent = begin(fleet.controller, fleet.nodes['RU'], operation, apply=True)
    finish_node(fleet.nodes['RU'], intent, apply=True)
    before = read_private(fleet.controller.root / 'transaction.json')
    with pytest.raises(Rejected):
        complete(fleet.controller, intent)
    assert read_private(fleet.controller.root / 'transaction.json') == before
    for node in fleet.nodes.values():
        finish_node(node, intent, apply=True)
    assert complete(fleet.controller, intent)['result'] == 'ROLLED_BACK_READERS_STOPPED'
