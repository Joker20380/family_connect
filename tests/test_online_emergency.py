import json

import pytest

from test_online_renewal import Crash, enable
from test_multi_gateway_renewal import fleet, profiles
from test_activated_maintenance import MaintenanceAuthorization, Rejected, activate, canonical, digest, proof
from online_emergency import sequence


OPERATION = 'test-online-emergency-handoff'


def interrupted(fleet, boundary='ONLINE_NL_PUBLISHED'):
    enable(fleet)
    fleet.service.fetch(proof(fleet.service, fleet.device))
    def revoke(event):
        if event == boundary:
            with fleet.service.access.db() as database:
                database.execute('UPDATE devices SET revoked=1 WHERE device=?', (fleet.device.reference,))
    fleet.controller.fault = revoke
    result = fleet.controller.run_online(OPERATION, schedule_seconds=0)
    assert result['result'] == 'ONLINE_EMERGENCY_REQUIRED', result
    fleet.controller.fault = lambda event: None
    return json.loads((fleet.controller.root/'transaction.json').read_bytes())


def approved(fleet, request):
    return MaintenanceAuthorization(OPERATION, request['expected_state_sha256'], fleet.now, fleet.now+900)


@pytest.mark.parametrize('boundary', ['ONLINE_COMMIT_DECIDED', 'ONLINE_NL_PUBLISHED'])
def test_committed_revoke_handoff_requires_approval_and_recovers(fleet, boundary):
    survivor = activate(fleet.service)
    parent = interrupted(fleet, boundary)
    request = fleet.controller.recover_online_emergency(OPERATION)
    assert request['result'] == 'EMERGENCY_APPROVAL_REQUIRED', request
    assert all(node.barrier.stopped() for node in fleet.nodes.values())
    repeat = fleet.controller.recover_online_emergency(OPERATION)
    assert repeat == request
    result = fleet.controller.recover_online_emergency(OPERATION, approval=approved(fleet, request['request']))
    assert result['result'] == 'EMERGENCY_RECOVERED', result
    record = json.loads((fleet.controller.root/'transaction.json').read_bytes())
    assert record['online_parent']['decision'] == record['decision'] == 'COMMIT'
    assert digest(canonical(record['online_parent']['plan'])) == parent['plan_sha256']
    plan = json.loads((fleet.controller.root/'plan.json').read_bytes())
    assert sequence(plan['candidate']) == sequence(record['online_parent']['plan']['candidate'])+1
    assert profiles(fleet)['NL']['revocations'] == profiles(fleet)['NL2']['revocations'] == plan['candidate']['crl']
    assert not any(node.barrier.stopped() for node in fleet.nodes.values())
    assert fleet.controller.recover_online_emergency(OPERATION)['replay']
    with pytest.raises(ValueError):
        fleet.service.fetch(proof(fleet.service, fleet.device))
    assert fleet.service.fetch(proof(fleet.service, survivor))['device'] == survivor.reference


@pytest.mark.parametrize('invalid', ['expired', 'binding', 'denied'])
def test_invalid_emergency_approval_never_issues_or_starts(fleet, invalid):
    interrupted(fleet)
    request = fleet.controller.recover_online_emergency(OPERATION)['request']
    approval = approved(fleet, request)
    if invalid == 'expired':
        approval = MaintenanceAuthorization(OPERATION, request['expected_state_sha256'], fleet.now-1000, fleet.now-1)
    if invalid == 'binding':
        approval = MaintenanceAuthorization(OPERATION, '0'*64, fleet.now, fleet.now+900)
    if invalid == 'denied':
        approval = MaintenanceAuthorization(OPERATION, request['expected_state_sha256'], fleet.now, fleet.now+900, 'DENIED')
    before = profiles(fleet)
    result = fleet.controller.recover_online_emergency(OPERATION, approval=approval)
    assert result['result'] == 'EMERGENCY_BLOCKED' and result['cause'].startswith('MAINTENANCE_APPROVAL_'), result
    assert profiles(fleet) == before
    assert all(node.barrier.stopped() and node.barrier.starts == 0 for node in fleet.nodes.values())


@pytest.mark.parametrize('boundary', ['EMERGENCY_HANDOFF', 'EMERGENCY_APPROVAL_REQUIRED', 'EMERGENCY_AUTHORIZED',
                                    'EMERGENCY_PREPARED', 'EMERGENCY_PUBLISHING', 'EMERGENCY_COMMIT_DECIDED'])
def test_controller_crash_resumes_same_handoff(fleet, boundary):
    interrupted(fleet)
    request = fleet.controller.recover_online_emergency(OPERATION)['request']
    approval = approved(fleet, request)
    def crash(event):
        if event == boundary:
            raise Crash()
    fleet.controller.fault = crash
    with pytest.raises(Crash):
        fleet.controller.recover_online_emergency(OPERATION, approval=approval)
    fleet.controller.fault = lambda event: None
    result = fleet.controller.recover_online_emergency(OPERATION, approval=approval)
    assert result['result'] == 'EMERGENCY_RECOVERED', result


@pytest.mark.parametrize('slot', ['RU', 'NL', 'NL2'])
@pytest.mark.parametrize('boundary', ['emergency-handoff-decided', 'emergency-archive-plan.json', 'emergency-handoff-complete'])
def test_node_handoff_lost_response_and_stale_online_owner(fleet, slot, boundary):
    parent = interrupted(fleet)
    fired = False
    def crash(event):
        nonlocal fired
        if event == boundary and not fired:
            fired = True
            raise OSError('lost response')
    fleet.nodes[slot].fault = crash
    assert fleet.controller.recover_online_emergency(OPERATION)['result'] == 'EMERGENCY_BLOCKED'
    assert fired
    fleet.nodes[slot].fault = lambda event: None
    request = fleet.controller.recover_online_emergency(OPERATION)
    assert request['result'] == 'EMERGENCY_APPROVAL_REQUIRED', request
    for node in fleet.controller.nodes.values():
        with pytest.raises(Rejected, match='ONLINE_STALE_WRITER'):
            node.call('online', OPERATION, dict(command='fence', fence=parent['fence']))
    result = fleet.controller.recover_online_emergency(OPERATION, approval=approved(fleet, request['request']))
    assert result['result'] == 'EMERGENCY_RECOVERED', result
