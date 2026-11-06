import json

import pytest

from test_multi_gateway_renewal import fleet
from test_reconcile_unprepared_renewal import issue_certificate
from credential_renewal import Rejected, atomic, canonical, parse, read_private
from scripts.reconcile_unprepared_renewal import abort_unacquired, main


def blocked(fleet):
    fleet.now += 12000
    with fleet.nodes['RU'].operation.lock():
        result = fleet.scheduled('first-acquire-busy')
    assert result['result'] == 'RECOVERY_REQUIRED'
    record = parse(read_private(fleet.controller.root / 'transaction.json'))
    assert record['first_cause'] == 'OPERATION_BUSY' and record['acquired'] == []
    assert all(not (node.state / 'owner.json').exists() for node in fleet.nodes.values())
    return record['operation_id']


def test_expired_unacquired_abort_preserves_database_then_normal_renewal(fleet):
    operation = blocked(fleet)
    issue_certificate(fleet)
    fleet.now += 15000
    original = read_private(fleet.controller.root / 'transaction.json')
    assert fleet.controller.recover(parse(original))['result'] == 'RECOVERY_REQUIRED'
    node = fleet.nodes['RU']
    database = node.database.snapshot()
    profiles = {slot: remote.inspect() for slot, remote in fleet.nodes.items()}
    starts = {slot: remote.barrier.starts for slot, remote in fleet.nodes.items()}
    assert abort_unacquired(fleet.controller, node, operation)['result'] == 'UNACQUIRED_ABORTABLE'
    assert read_private(fleet.controller.root / 'transaction.json') == original
    assert not list(fleet.controller.root.glob('unacquired-abort-*.json'))
    for repeat in range(2):
        result = abort_unacquired(fleet.controller, node, operation, apply=True)
        assert result['result'] == 'UNACQUIRED_ABORTED'
        assert not result['readers_changed']
        assert node.database.snapshot() == database
        assert profiles == {slot: remote.inspect() for slot, remote in fleet.nodes.items()}
        assert starts == {slot: remote.barrier.starts for slot, remote in fleet.nodes.items()}
    intent = parse(read_private(fleet.controller.root / ('unacquired-abort-' + operation + '.json')))
    assert canonical(intent['record_before']) == original
    assert fleet.scheduled('after-unacquired-abort')['result'] == 'COMMITTED'
    assert all(remote.barrier.starts == starts[slot] + 1 for slot, remote in fleet.nodes.items())
    with pytest.raises(Rejected, match='OPERATION_ID'):
        abort_unacquired(fleet.controller, node, operation, apply=True)


@pytest.mark.parametrize('point', ['intent', 'record'])
def test_unacquired_abort_crash_replay(fleet, point):
    operation = blocked(fleet)

    def fault(event):
        if event == point:
            raise OSError('interrupted metadata write')

    with pytest.raises(OSError):
        abort_unacquired(fleet.controller, fleet.nodes['RU'], operation, apply=True, fault=fault)
    assert abort_unacquired(fleet.controller, fleet.nodes['RU'], operation, apply=True)['result'] == 'UNACQUIRED_ABORTED'


@pytest.mark.parametrize('failure', ['owner', 'artifact', 'plan', 'ledger', 'commit', 'acquired', 'quiesced',
                                    'cause', 'operation', 'mode', 'binding', 'remote-profile', 'policy', 'revoked'])
def test_unacquired_abort_refuses_ambiguous_or_changed_state(fleet, failure):
    operation = blocked(fleet)
    node = fleet.nodes['RU']
    marker = fleet.controller.root / 'transaction.json'
    record = parse(read_private(marker))
    if failure == 'owner':
        node.acquire(operation, node.inspect())
    elif failure == 'artifact':
        atomic(node.state / 'services-before.json', b'{}')
    elif failure == 'plan':
        atomic(fleet.controller.root / 'plan.json', canonical(dict(operation_id=operation)))
    elif failure == 'ledger':
        atomic(node.state / 'completed.json', canonical({operation: {}}))
    elif failure in ('commit', 'acquired', 'quiesced', 'cause', 'operation', 'mode', 'binding'):
        updates = dict(commit={'commit_decided': True}, acquired={'acquired': ['RU']},
                       quiesced={'quiesced': ['RU']}, cause={'first_cause': 'UNKNOWN'},
                       operation={'operation_id': 'different-operation-id'}, mode={'mode': 'online'},
                       binding={'before_sha256': '0' * 64})
        atomic(marker, canonical(dict(record, **updates[failure])))
    elif failure == 'remote-profile':
        path = fleet.nodes['NL2'].live / 'gateway.json'
        atomic(path, canonical(dict(parse(read_private(path)), minimum_crl=999999)))
    elif failure == 'policy':
        node.policy_paths = {'extra': node.live / 'extra-policy'}
        atomic(node.live / 'extra-policy', b'changed')
    else:
        issue_certificate(fleet)
        with fleet.service.access.db() as database:
            database.execute('UPDATE devices SET revoked=1 WHERE device=?', (fleet.device.reference,))
    before = read_private(marker)
    with pytest.raises(Rejected):
        abort_unacquired(fleet.controller, node, operation, apply=True)
    assert read_private(marker) == before
    assert not list(fleet.controller.root.glob('unacquired-abort-*.json'))


@pytest.mark.parametrize('lock', ['controller', 'node'])
def test_unacquired_abort_respects_existing_writer_locks(fleet, lock):
    operation = blocked(fleet)
    owner = fleet.controller if lock == 'controller' else fleet.nodes['RU']
    with owner.operation.lock(), pytest.raises(Rejected, match='OPERATION_BUSY'):
        abort_unacquired(fleet.controller, fleet.nodes['RU'], operation, apply=True)
    assert not list(fleet.controller.root.glob('unacquired-abort-*.json'))


def test_unacquired_cli_imports_pinned_runtime(tmp_path, monkeypatch, capsys):
    from test_activated_maintenance import MAINTENANCE
    monkeypatch.setattr('sys.argv', ['reconcile', '--runtime', str(MAINTENANCE), '--config',
                        str(tmp_path / 'absent.json'), '--operation', 'test-unacquired-entrypoint', '--abort-unacquired'])
    with pytest.raises(SystemExit) as result:
        main()
    assert result.value.code == 1
    assert json.loads(capsys.readouterr().out)['result'] == 'FAIL_CLOSED'
