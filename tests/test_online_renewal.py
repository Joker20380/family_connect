import json

import pytest

from test_multi_gateway_renewal import fleet, profiles
from test_activated_maintenance import atomic, canonical, digest, proof, Rejected
from control.friends.restricted import iso, ChallengeUnavailable
from online_contract import CONTRACT


class Crash(BaseException):
    pass


def enable(fleet):
    fleet.now += 12000
    for node in fleet.nodes.values():
        node.online_qualification = True
    for slot in ('NL', 'NL2'):
        node = fleet.nodes[slot]
        value = json.loads((node.live/'directory.json').read_bytes())
        value.update(issued_at=iso(fleet.now), expires_at=iso(fleet.now+3599))
        atomic(node.live/'directory.json', canonical(value))
        atomic(fleet.nodes['RU'].directory_destination(slot), canonical(value))
        node.online_reader = lambda candidate, node=node, slot=slot: dict(contract=CONTRACT,
            gateway=fleet.identities[slot], profile_sha256=digest(node.read('gateway.json')[0]),
            instance=digest(slot.encode()))
    for node in fleet.controller.nodes.values():
        node.timeout_seconds = 1
    fleet.service.publication_source = lambda: ((fleet.nodes['RU'].live/'online-delivery.json').read_bytes()
        if (fleet.nodes['RU'].live/'online-delivery.json').exists() else None)


def test_online_transaction_uses_existing_readiness_and_does_not_stop(fleet):
    enable(fleet)
    before = profiles(fleet)
    original = fleet.service.fetch(proof(fleet.service, fleet.device))
    result = fleet.controller.run_online('test-online-transaction', schedule_seconds=0)
    assert result['result'] == 'COMMITTED', result
    delivered = fleet.service.fetch(proof(fleet.service, fleet.device))
    assert delivered['revocations'] != original['revocations']
    assert delivered['revocations'] == profiles(fleet)['NL']['revocations'] == profiles(fleet)['NL2']['revocations']
    assert not any(node.barrier.stopped() or node.barrier.starts for node in fleet.nodes.values())
    assert all(profiles(fleet)[slot]['private_key'] == before[slot]['private_key'] for slot in before)
    duplicate = fleet.service.fetch(proof(fleet.service, fleet.device))
    assert delivered['certificate'] == duplicate['certificate']
    assert fleet.controller.run_online('test-online-transaction', schedule_seconds=0)['replay']


def test_retry_retains_first_failure_and_reports_current_blocker(fleet):
    enable(fleet)
    def fail(cause):
        def inject(event):
            if event == 'online-prepared':
                raise Rejected(cause)
        return inject
    fleet.nodes['NL'].fault = fail('RPC_RESPONSE_SCHEMA')
    first = fleet.controller.run_online('test-online-retry-cause', schedule_seconds=0)
    assert first['cause'] == first['last_cause'] == 'RPC_RESPONSE_SCHEMA'
    fleet.nodes['NL'].fault = fail('ONLINE_RUNTIME_UNAVAILABLE')
    second = fleet.controller.run_online('test-online-retry-cause', schedule_seconds=0, resume=True)
    assert second['cause'] == 'RPC_RESPONSE_SCHEMA' and second['last_cause'] == 'ONLINE_RUNTIME_UNAVAILABLE'
    assert second['decision'] is None


@pytest.mark.parametrize('boundary', ['ONLINE_ACQUIRING', 'ONLINE_FENCING', 'ONLINE_RU_ACQUIRED',
    'ONLINE_NL_ACQUIRED', 'ONLINE_NL2_ACQUIRED', 'ONLINE_PREPARED', 'ONLINE_RU_STAGED',
    'ONLINE_NL_STAGED', 'ONLINE_NL2_STAGED', 'ONLINE_COMMIT_DECIDED', 'ONLINE_RU_DECIDED',
    'ONLINE_NL_DECIDED', 'ONLINE_NL2_DECIDED', 'ONLINE_NL_PUBLISHED', 'ONLINE_NL2_PUBLISHED',
    'ONLINE_CLEANING', 'COMMITTED'])
def test_controller_crash_reconciles_same_decision(fleet, boundary):
    enable(fleet)
    def crash(event):
        if event == boundary:
            raise Crash()
    fleet.controller.fault = crash
    with pytest.raises(Crash):
        fleet.controller.run_online('test-online-controller-crash', schedule_seconds=0)
    record = json.loads((fleet.controller.root/'transaction.json').read_bytes())
    committed = record['commit_decided']
    plan_hash = record.get('plan_sha256')
    fleet.controller.fault = lambda event: None
    result = fleet.controller.run_online('test-online-controller-crash', schedule_seconds=0, resume=True)
    assert result['result'] == 'COMMITTED', result
    if committed:
        assert json.loads((fleet.controller.root/'transaction.json').read_bytes())['plan_sha256'] == plan_hash
    assert not any(node.barrier.stopped() or node.barrier.starts for node in fleet.nodes.values())


@pytest.mark.parametrize('slot,event', [('RU','online-acquired'), ('NL','online-acquired'),
    ('NL2','online-acquired'), ('RU','online-prepared'), ('NL','online-prepared'), ('NL2','online-prepared'),
    ('RU','online-decision'), ('NL','online-decision'), ('NL2','online-decision'),
    ('NL','online-before-rename-gateway.json'), ('NL2','online-after-rename-gateway.json'),
    ('RU','online-delivery-fenced'), ('RU','online-sequence'), ('RU','online-after-rename-revocations.pem'),
    ('RU','online-delivery-ready'), ('NL','archive-plan.json'), ('RU','completed-ledger')])
def test_node_crash_and_lost_response(fleet, slot, event):
    enable(fleet)
    fired = False
    def crash(actual):
        nonlocal fired
        if actual == event and not fired:
            fired = True
            raise OSError('injected lost response')
    fleet.nodes[slot].fault = crash
    result = fleet.controller.run_online('test-online-node-crash', schedule_seconds=0)
    assert result['result'] == 'ONLINE_RECOVERY_REQUIRED', result
    assert fired
    fleet.nodes[slot].fault = lambda event: None
    result = fleet.controller.run_online('test-online-node-crash', schedule_seconds=0, resume=True)
    assert result['result'] == 'COMMITTED', result


@pytest.mark.parametrize('boundary', ['ONLINE_ACQUIRING', 'ONLINE_FENCING', 'ONLINE_PREPARED', 'ONLINE_NL2_STAGED'])
def test_precommit_abort_is_durable_and_does_not_rollback(fleet, boundary):
    enable(fleet)
    before = profiles(fleet)
    def crash(event):
        if event == boundary:
            raise Crash()
    fleet.controller.fault = crash
    with pytest.raises(Crash):
        fleet.controller.run_online('test-online-abort-operation', schedule_seconds=0)
    fleet.controller.fault = lambda event: None
    assert fleet.controller.abort_online('test-online-abort-operation')['result'] == 'ABORTED'
    assert fleet.controller.abort_online('test-online-abort-operation')['replay']
    assert profiles(fleet) == before


def test_online_insufficient_window_has_no_writes(fleet):
    enable(fleet)
    fleet.now += 2000
    before = profiles(fleet)
    with pytest.raises(Rejected, match='ONLINE_WINDOW_INSUFFICIENT'):
        fleet.controller.run_online('test-online-too-late-operation', schedule_seconds=0)
    assert profiles(fleet) == before
    assert not (fleet.controller.root/'transaction.json').exists()


@pytest.mark.parametrize('boundary', ['ONLINE_COMMIT_DECIDED','ONLINE_NL_PUBLISHED'])
def test_revoke_during_commit_fences_without_rollback_or_delivery(fleet, boundary):
    enable(fleet)
    def revoke(event):
        if event == boundary:
            with fleet.service.access.db() as database:
                database.execute('UPDATE devices SET revoked=1 WHERE device=?',(fleet.device.reference,))
    fleet.controller.fault = revoke
    result = fleet.controller.run_online('test-online-revocation-fault', schedule_seconds=0)
    assert result['result'] == 'ONLINE_EMERGENCY_REQUIRED',result
    assert all(node.barrier.stopped() for node in fleet.nodes.values())
    assert not (fleet.nodes['RU'].live/'online-delivery.json').exists()
    with pytest.raises(Rejected,match='ONLINE_DECISION_IMMUTABLE'):
        fleet.controller.abort_online('test-online-revocation-fault')
    with pytest.raises(Rejected,match='ONLINE_EMERGENCY_REQUIRED'):
        fleet.controller.run_online('test-online-revocation-fault',schedule_seconds=0,resume=True)


def test_production_constructor_does_not_enable_qualification_route(fleet):
    with pytest.raises(Rejected,match='ONLINE_QUALIFICATION_ONLY'):
        fleet.controller.nodes['RU'].call('online','test-online-disabled-route',dict(command='inspect'))


def test_stale_epoch_cannot_mutate_and_maintenance_cannot_compete(fleet):
    enable(fleet)
    def crash(event):
        if event == 'ONLINE_NL2_STAGED':
            raise Crash()
    fleet.controller.fault = crash
    with pytest.raises(Crash):
        fleet.controller.run_online('test-online-fenced-operation',schedule_seconds=0)
    with pytest.raises(Rejected,match='ONLINE_RECOVERY_REQUIRED'):
        fleet.controller.nodes['NL'].call('quiesce','test-online-fenced-operation')
    node = fleet.nodes['NL']
    owner = node.owner('test-online-fenced-operation')
    fleet.controller.nodes['NL'].call('online','test-online-fenced-operation',dict(command='acquire',
        fence=2,expected=owner['expected_state'],online=owner['online']))
    for command in ('publish','fence','abort'):
        with pytest.raises(Rejected,match='ONLINE_STALE_WRITER'):
            fleet.controller.nodes['NL'].call('online','test-online-fenced-operation',dict(command=command,fence=1))
    assert not node.barrier.stopped()


def test_live_client_certificate_insufficient_headroom_rejects(fleet):
    enable(fleet)
    fleet.service.fetch(proof(fleet.service,fleet.device))
    with fleet.service.access.db() as database:
        database.execute('UPDATE restricted_certificates SET expires=?',(fleet.now+400,))
    result = fleet.controller.run_online('test-online-client-headroom',schedule_seconds=0)
    assert result['result']=='ONLINE_RECOVERY_REQUIRED' and result['cause']=='ONLINE_CLIENT_WINDOW_INSUFFICIENT'
    assert fleet.controller.abort_online('test-online-client-headroom')['result']=='ABORTED'


def test_unavailable_participant_allows_proven_precommit_abort(fleet):
    enable(fleet)
    before = profiles(fleet)
    original = fleet.controller.nodes['NL2'].call
    def unavailable(action, operation, payload=None):
        if action=='online' and payload['command']=='acquire':
            raise OSError('isolated unavailable participant')
        return original(action, operation, payload)
    fleet.controller.nodes['NL2'].call = unavailable
    result = fleet.controller.run_online('test-online-unavailable-node',schedule_seconds=0)
    assert result['result']=='ONLINE_RECOVERY_REQUIRED' and result['decision'] is None
    fleet.controller.nodes['NL2'].call = original
    assert fleet.controller.abort_online('test-online-unavailable-node')['result']=='ABORTED'
    assert profiles(fleet)==before


@pytest.mark.parametrize('advance,expected',[(2400,'COMMITTED'),(20000,'ONLINE_EMERGENCY_REQUIRED')])
def test_postcommit_expiry_never_rolls_back(fleet, advance, expected):
    enable(fleet)
    def crash(event):
        if event=='ONLINE_COMMIT_DECIDED':
            raise Crash()
    fleet.controller.fault=crash
    with pytest.raises(Crash):
        fleet.controller.run_online('test-online-expiry-operation',schedule_seconds=0)
    decision=json.loads((fleet.controller.root/'transaction.json').read_bytes())
    fleet.now+=advance
    fleet.controller.fault=lambda event:None
    if expected=='COMMITTED':
        for slot in ('NL','NL2'):
            node=fleet.nodes[slot]
            value=json.loads((node.live/'directory.json').read_bytes())
            value.update(issued_at=iso(fleet.now),expires_at=iso(fleet.now+3599))
            atomic(node.live/'directory.json',canonical(value))
    result=fleet.controller.run_online('test-online-expiry-operation',schedule_seconds=0,resume=True)
    assert result['result']==expected,result
    final=json.loads((fleet.controller.root/'transaction.json').read_bytes())
    assert final['decision']=='COMMIT' and final['plan_sha256']==decision['plan_sha256']


@pytest.mark.parametrize('change', ['not-ready','digest','gateway','operation','duplicate','truncated'])
def test_unready_or_corrupt_delivery_does_not_consume_challenge(fleet, change):
    enable(fleet)
    assert fleet.controller.run_online('test-online-readiness-gate',schedule_seconds=0)['result']=='COMMITTED'
    marker=fleet.nodes['RU'].live/'online-delivery.json'
    original=marker.read_bytes()
    value=json.loads(original)
    if change=='not-ready':value['ready']=False
    if change=='digest':value['crl_sha256']='0'*64
    if change=='gateway':value['gateways']['NL']='0'*32
    if change=='operation':value['operation_id']='invalid'
    corrupted=canonical(value)
    if change=='duplicate':corrupted=corrupted[:-1]+b',"ready":true}'
    if change=='truncated':corrupted=corrupted[:10]
    atomic(marker,corrupted)
    request=proof(fleet.service,fleet.device)
    with pytest.raises(ChallengeUnavailable):
        fleet.service.fetch(request)
    atomic(marker,original)
    assert fleet.service.fetch(request)['device']==fleet.device.reference


def test_corrupt_durable_decision_fences_instead_of_guessing(fleet):
    enable(fleet)
    def crash(event):
        if event=='ONLINE_COMMIT_DECIDED':raise Crash()
    fleet.controller.fault=crash
    with pytest.raises(Crash):fleet.controller.run_online('test-online-corrupt-decision',schedule_seconds=0)
    marker=fleet.controller.root/'transaction.json'
    value=json.loads(marker.read_bytes())
    value['plan_sha256']='0'*64
    atomic(marker,canonical(value))
    fleet.controller.fault=lambda event:None
    result=fleet.controller.run_online('test-online-corrupt-decision',schedule_seconds=0,resume=True)
    assert result['result']=='ONLINE_EMERGENCY_REQUIRED' and result['decision']=='COMMIT'
    assert all(node.barrier.stopped() for node in fleet.nodes.values())
