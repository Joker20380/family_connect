import base64
import json
import os
import sys

import pytest

from test_activated_maintenance import Cluster, Rejected, canonical, digest, atomic, parse
import production_node
import renewal_cli
import runtime_controller
from production_transport import SystemdBarrier


RESULT = 'ROLLED_BACK_READERS_STOPPED'


@pytest.fixture
def rolled_back(tmp_path):
    cluster = Cluster(tmp_path)
    cluster.now += 12000
    def interrupt(stage):
        if stage == 'NL_PROMOTED':
            raise KeyboardInterrupt()
    cluster.controller.fault = interrupt
    with pytest.raises(KeyboardInterrupt):
        cluster.scheduled()
    cluster.controller.fault = lambda stage: None
    record = parse((cluster.controller.root/'transaction.json').read_bytes())
    record['first_cause'] = 'DIRECTORY_INVALID'
    for node in cluster.nodes.values():
        node.rollback(record['operation_id'])
    cluster.controller.save(record,'ROLLED_BACK')
    cluster.record = record
    cluster.calls = []
    for role,rpc in cluster.controller.nodes.items():
        original = rpc.call
        def call(action, operation, payload=None, role=role, original=original):
            cluster.calls.append((role,action))
            return original(action,operation,payload)
        rpc.call = call
    return cluster


def recover(cluster):
    return cluster.controller.recover(parse((cluster.controller.root/'transaction.json').read_bytes()))


def payload(node):
    owner = node.owner('test-renewal-operation-first')
    return dict(reason='PREVIOUS_LEAF_EXPIRED',expected_state_sha256=digest(canonical(owner['expected_state'])),
                controller_operation_sha256='a'*64)


def test_current_predecessor_keeps_normal_restore_and_resume(rolled_back):
    assert recover(rolled_back)['result'] == 'ABORTED'
    assert all(node.barrier.starts == 1 for node in rolled_back.nodes.values())
    assert {action for _,action in rolled_back.calls} >= {'public-directory','publish-directory','restore'}
    assert 'finalize-fenced-rollback' not in {action for _,action in rolled_back.calls}


def test_recovery_required_verified_rollback_can_terminalize(rolled_back):
    rolled_back.now += 3000
    rolled_back.controller.save(rolled_back.record,'RECOVERY_REQUIRED')
    assert recover(rolled_back)['result'] == RESULT
    assert sum(action == 'rollback' for _,action in rolled_back.calls) == 2
    assert all(node.barrier.starts == 0 for node in rolled_back.nodes.values())


def test_expired_predecessor_terminal_fields_archives_and_no_writes(rolled_back):
    cluster = rolled_back
    cluster.now += 3000
    before = {role:node.inspect() for role,node in cluster.nodes.items()}
    files = {role:{path.name:path.read_bytes() for path in node.state.iterdir() if path.is_file()
                   and path.name not in ('operation.lock','owner.json')} for role,node in cluster.nodes.items()}
    assert recover(cluster)['result'] == RESULT
    record = parse((cluster.controller.root/'transaction.json').read_bytes())
    assert record['state'] == 'ABORTED' and record['commit_decided'] is False
    assert record['operation_id'] == cluster.record['operation_id']
    assert record['first_cause'] == record['first_reason'] == 'DIRECTORY_INVALID'
    assert record['terminal_reason'] == 'PREVIOUS_LEAF_EXPIRED'
    assert record['terminal_result'] == RESULT and record['rollback_verified'] is True
    assert record['previous_material_current'] is False and record['readers_resumed'] is False
    assert record['readers_state'] == 'STOPPED'
    assert not {action for _,action in cluster.calls} & {'public-directory','publish-directory','restore','resume'}
    for role,node in cluster.nodes.items():
        assert node.inspect() == before[role] and node.barrier.stopped() and node.barrier.starts == 0
        assert not (node.state/'owner.json').exists()
        archive = node.state/'archive'/record['operation_id']
        for name,raw in files[role].items():
            assert (archive/name).read_bytes() == raw
        manifest = parse((archive/'archive-manifest.json').read_bytes())
        assert set(manifest) == set(files[role]) | {'rollback-terminal.json','owner-before-cleanup.json'}
        assert parse((archive/'owner-before-cleanup.json').read_bytes())['first_cause'] is None
        assert (archive/'rollback-terminal.json').stat().st_mode & 0o777 == 0o600
        ledger = parse((node.state/'completed.json').read_bytes())
        assert ledger[record['operation_id']]['result'] == 'CLEANED_FENCED_ROLLBACK'
        assert node.cleanup(record['operation_id'])['result'] == 'CLEANED_FENCED_ROLLBACK'
    assert recover(cluster)['result'] == RESULT
    for node in cluster.nodes.values():
        assert node.acquire('test-fresh-renewal-operation',node.inspect())['state'] == 'ACQUIRED'


@pytest.mark.parametrize('mutation', ['future','signature','previous','before-hash','node-state','readback','active','commit'])
def test_ineligible_recovery_stays_nonterminal(rolled_back, mutation, monkeypatch):
    cluster = rolled_back
    cluster.now += 3000
    record = cluster.record
    if mutation == 'future':
        cluster.now -= 16000
    elif mutation == 'signature':
        record['previous']['authority']['signature'] = base64.b64encode(bytes(64)).decode()
    elif mutation == 'previous':
        record['previous']['grants'] = [dict(invalid=True)]
    elif mutation == 'before-hash':
        record['before_sha256'] = '0'*64
    elif mutation == 'node-state':
        monkeypatch.setattr(cluster.nodes['NL'],'inspect',lambda: {})
    elif mutation == 'readback':
        monkeypatch.setattr(cluster.nodes['NL'],'previous_readback',lambda operation: dict(result='MISMATCH'))
    elif mutation == 'active':
        cluster.nodes['NL'].barrier.quiet = False
    else:
        record['commit_decided'] = True
        record['reconciliation'] = {}
    cluster.controller.save(record,'ROLLED_BACK')
    assert recover(cluster)['result'] == 'RECOVERY_REQUIRED'
    assert not {action for _,action in cluster.calls} & {'finalize-fenced-rollback','restore','resume','publish-directory'}
    assert all(node.barrier.starts == 0 for node in cluster.nodes.values())


def test_other_strict_validation_failure_is_not_expiry_exception(rolled_back, monkeypatch):
    cluster = rolled_back
    cluster.now += 3000
    validate = cluster.controller.validator.validate
    def reject(raw, now, **options):
        if not options.get('expired_leaf_predecessor'):
            raise Rejected('CRL_EXPIRED_OR_FUTURE')
        return validate(raw,now,**options)
    monkeypatch.setattr(cluster.controller.validator,'validate',reject)
    assert recover(cluster)['result'] == 'RECOVERY_REQUIRED'
    assert 'finalize-fenced-rollback' not in {action for _,action in cluster.calls}


@pytest.mark.parametrize('role', ['RU','NL'])
def test_node_fenced_replay_binding_and_new_owner_gate(rolled_back, role):
    node = rolled_back.nodes[role]
    operation = rolled_back.record['operation_id']
    node.operation.advance(node.owner(operation),'ROLLED_BACK','DIRECTORY_INVALID')
    request = payload(node)
    receipt = node.finalize_fenced_rollback(operation,request)
    assert node.owner(operation)['state'] == 'ABORTED_FENCED'
    assert node.owner(operation)['first_cause'] == 'DIRECTORY_INVALID'
    assert node.finalize_fenced_rollback(operation,request) == receipt
    assert node.previous_readback(operation)['result'] == 'PREVIOUS_SNAPSHOT_RESTORED'
    with pytest.raises(Rejected,match='ROLLBACK_TERMINAL_BINDING_MISMATCH'):
        node.finalize_fenced_rollback(operation,dict(request,controller_operation_sha256='b'*64))
    with pytest.raises(Rejected,match='OTHER_OPERATION_RECOVERY_REQUIRED'):
        node.acquire('test-fresh-renewal-operation',node.inspect())
    node.barrier.quiet = False
    with pytest.raises(Rejected,match='READERS_NOT_QUIESCED'):
        node.previous_readback(operation)
    with pytest.raises(Rejected,match='READERS_NOT_QUIESCED'):
        node.cleanup(operation)
    assert (node.state/'owner.json').exists()


@pytest.mark.parametrize('obstacle', ['start-intent-0.json','reconciliation.json','directory-accepted.json','active','hash','payload'])
def test_node_rejects_conflicts_without_terminal_receipt(rolled_back, obstacle):
    node = rolled_back.nodes['RU']
    operation = rolled_back.record['operation_id']
    request = payload(node)
    if obstacle.endswith('.json'):
        node.barrier.units = ('fixture.service',)
        atomic(node.state/obstacle,canonical(dict(schema=1,unit='fixture.service',timestamp=0)))
    elif obstacle == 'active':
        node.barrier.quiet = False
    elif obstacle == 'hash':
        request['expected_state_sha256'] = '0'*64
    else:
        request['path'] = '/caller-selected'
    with pytest.raises(Rejected):
        node.finalize_fenced_rollback(operation,request)
    assert not (node.state/'rollback-terminal.json').exists()
    assert node.barrier.starts == 0


@pytest.mark.parametrize('stage', ['rollback-terminal-receipt','aborted-fenced','archive-rollback-terminal.json',
                                 'archive-owner-before-cleanup.json','archive-plan.json','completed-ledger'])
def test_fenced_faults_are_recoverable_without_resuming_or_losing_owner(rolled_back, stage):
    cluster = rolled_back
    cluster.now += 3000
    node = cluster.nodes['NL']
    def interrupt(current):
        if current == stage:
            raise OSError('synthetic fault')
    node.fault = interrupt
    assert recover(cluster)['result'] in ('RECOVERY_REQUIRED','CLEANUP_REQUIRED')
    assert (node.state/'owner.json').exists()
    assert node.barrier.stopped() and node.barrier.starts == 0
    node.fault = lambda current: None
    assert recover(cluster)['result'] == RESULT
    assert all(not (member.state/'owner.json').exists() for member in cluster.nodes.values())


def test_fresh_controller_operation_waits_for_both_cleanups(rolled_back):
    cluster = rolled_back
    cluster.now += 3000
    node = cluster.nodes['NL']
    def interrupt(stage):
        if stage == 'completed-ledger':
            raise OSError('synthetic incomplete cleanup')
    node.fault = interrupt
    assert recover(cluster)['result'] == 'CLEANUP_REQUIRED'
    assert cluster.scheduled('fresh')['result'] == 'CLEANUP_REQUIRED'
    assert parse((cluster.controller.root/'transaction.json').read_bytes())['operation_id'] == cluster.record['operation_id']
    node.fault = lambda stage: None
    assert recover(cluster)['result'] == RESULT
    assert cluster.scheduled('fresh')['result'] == 'COMMITTED'
    assert parse((cluster.controller.root/'transaction.json').read_bytes())['operation_id'] != cluster.record['operation_id']


def test_archive_fsync_failure_retains_active_owner(rolled_back, monkeypatch):
    node = rolled_back.nodes['NL']
    operation = rolled_back.record['operation_id']
    node.finalize_fenced_rollback(operation,payload(node))
    fsync = os.fsync
    def fail(descriptor):
        target = os.readlink('/proc/self/fd/'+str(descriptor))
        if target == str(node.state/'archive'):
            raise OSError('synthetic archive fsync failure')
        fsync(descriptor)
    with monkeypatch.context() as patch:
        patch.setattr(production_node.os,'fsync',fail)
        with pytest.raises(OSError):
            node.cleanup(operation)
    assert (node.state/'owner.json').exists()
    assert node.cleanup(operation)['result'] == 'CLEANED_FENCED_ROLLBACK'


@pytest.mark.parametrize('obstacle', ['active','receipt','archive'])
def test_cleanup_replay_validates_fenced_history_and_barrier(rolled_back, obstacle):
    cluster = rolled_back
    cluster.now += 3000
    assert recover(cluster)['result'] == RESULT
    node = cluster.nodes['NL']
    operation = cluster.record['operation_id']
    if obstacle == 'active':
        node.barrier.quiet = False
    else:
        name = 'rollback-terminal.json' if obstacle == 'receipt' else 'plan.json'
        atomic(node.state/'archive'/operation/name,b'{}')
    with pytest.raises(Rejected):
        node.cleanup(operation)


@pytest.mark.parametrize('active,pid,expected', [('active','0',False),('activating','0',False),
                                             ('inactive','4',False),('inactive','0',True),('failed','0',True)])
def test_systemd_barrier_proves_no_active_or_activating_reader(tmp_path, active, pid, expected):
    tmp_path.chmod(0o700)
    barrier = SystemdBarrier('NL',tmp_path,units=['fixture.service'])
    barrier.state = lambda unit: dict(ActiveState=active,MainPID=pid)
    assert barrier.stopped() is expected


@pytest.mark.parametrize('module,explicit', [(runtime_controller,True),(runtime_controller,False),
                                          (renewal_cli,True),(renewal_cli,False)])
def test_cli_accepts_fenced_result_only_for_explicit_recover(rolled_back, monkeypatch, capsys, module, explicit, process_umask):
    cluster = rolled_back
    operation = cluster.record['operation_id']
    config_path = cluster.controller.root/'cli.json'
    if module is runtime_controller:
        config = dict(schema=1,node_config='fixture',coordinator_state=str(cluster.controller.root),
                      nl_source_sha256='a'*64,ssh={},approved_leaf_crl_schedule=True)
        arguments = ['--mode','recover' if explicit else 'scheduled']
        monkeypatch.setattr(module,'construct',lambda path: (cluster.nodes['RU'],'a'*64))
    else:
        config = dict(schema=1,state=str(cluster.controller.root),anchor=base64.b64encode(cluster.validator.anchor).decode(),
                      node_sources={'RU':'a'*64,'NL':'a'*64},ssh_routes={'RU':{},'NL':{}})
        arguments = ['recover' if explicit else 'apply']
    atomic(config_path,canonical(config))
    monkeypatch.setattr(module,'SshNode',lambda *args,**kwargs: object())
    monkeypatch.setattr(module,'ProductionController',lambda *args,**kwargs: cluster.controller)
    monkeypatch.setattr(cluster.controller,'recover',lambda record: dict(result=RESULT))
    monkeypatch.setattr(cluster.controller,'run',lambda *args,**kwargs: dict(result=RESULT))
    monkeypatch.setattr(sys,'argv',['fixture',*arguments,'--config',str(config_path),'--operation',operation])
    if explicit:
        module.main()
    else:
        with pytest.raises(SystemExit) as error:
            module.main()
        assert error.value.code == 75
    assert json.loads(capsys.readouterr().out)['result'] == RESULT


@pytest.fixture
def process_umask():
    previous = os.umask(0o022)
    yield
    os.umask(previous)
