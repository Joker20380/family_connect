"""Explicit operator recovery for unprepared renewals without restoring the product DB."""
import argparse
import copy
import json
from pathlib import Path
import re
import sys


def reconcile(controller, node, operation, *, apply=False, fault=lambda event: None):
    from credential_renewal import atomic, canonical, digest, parse, read_private, require

    require(re.fullmatch('[a-z0-9-]{16,96}', operation) is not None, 'OPERATION_ID')
    require(node.role == 'RU' and controller.validator.all_activated, 'ACTIVATED_RU_REQUIRED')
    marker = controller.root / 'transaction.json'
    owner_path = node.state / 'owner.json'
    intent_path = controller.root / ('unprepared-rebase-' + operation + '.json')
    with controller.operation.lock(), node.operation.lock():
        record = parse(read_private(marker))
        owner = parse(read_private(owner_path))
        if intent_path.exists():
            intent = parse(read_private(intent_path))
            require(set(intent) == {'schema', 'operation_id', 'record_before', 'owner_before', 'current'},
                    'REBASE_INTENT_INVALID')
            require(intent['schema'] == 1 and intent['operation_id'] == operation, 'REBASE_INTENT_INVALID')
            original, original_owner = intent['record_before'], intent['owner_before']
        else:
            original, original_owner = record, owner
            intent = None
        require(original['operation_id'] == original_owner['operation_id'] == operation, 'OPERATION_ID')
        require(original['state'] == 'RECOVERY_REQUIRED' and original['first_cause'] == 'STALE_NODE_STATE'
                and not original['commit_decided'] and not original.get('reconciliation')
                and not original.get('mode') and not original.get('fenced_rollback'), 'UNPREPARED_REQUIRED')
        require(original['acquired'] == list(controller.nodes) and not original['quiesced'], 'UNPREPARED_REQUIRED')
        require(original_owner['state'] == 'ACQUIRED' and not original_owner.get('commit_decided')
                and original_owner['expected_state'] == original['before']['RU'], 'UNPREPARED_REQUIRED')
        require(digest(canonical(original['before'])) == original['before_sha256'], 'BEFORE_BINDING')
        allowed = {'owner.json', 'operation.lock', 'services-before.json', 'completed.json', 'archive'}
        require({path.name for path in node.state.iterdir()} <= allowed, 'PREPARATION_ARTIFACT_PRESENT')
        plan_path = controller.root / 'plan.json'
        if plan_path.exists():
            require(parse(read_private(plan_path))['operation_id'] != operation, 'PREPARATION_ARTIFACT_PRESENT')
        require(all(remote.call('stopped', operation)['stopped'] for remote in controller.nodes.values()),
                'READERS_NOT_QUIESCED')
        snapshot, gateway, current, pending_revocations = controller.read(operation)
        require(not pending_revocations, 'PENDING_REVOCATIONS')
        require(snapshot == original['previous'], 'AUTHORITY_OR_GRANTS_CHANGED')
        controller.validator.validate(canonical(snapshot), int(controller.clock()))
        if controller.multiple:
            require(gateway['secondary_snapshot'] == original['previous_secondary'], 'SECONDARY_CHANGED')
            controller.validator.validate(canonical(gateway['secondary_snapshot']), int(controller.clock()))
        require(set(current) == set(original['before']), 'NODE_SET')
        for role, actual in current.items():
            expected = copy.deepcopy(original['before'][role])
            compared = copy.deepcopy(actual)
            if role == 'RU':
                expected.pop('database_sha256')
                compared.pop('database_sha256')
            require(compared == expected, 'NON_DATABASE_STATE_CHANGED')
        require(current['RU']['database_sha256'] != original['before']['RU']['database_sha256'], 'NO_DATABASE_DRIFT')
        if intent is None:
            intent = dict(schema=1, operation_id=operation, record_before=original,
                          owner_before=original_owner, current=current)
        require(intent['current'] == current, 'REBASE_CURRENT_CHANGED')
        rebound_owner = dict(original_owner, expected_state=current['RU'])
        rebound = dict(original, before=current, before_sha256=digest(canonical(current)),
                       unprepared_rebase_sha256=digest(canonical(intent)))
        require(owner in (original_owner, rebound_owner) and record in (original, rebound), 'REBASE_STATE_CHANGED')
        if apply:
            if not intent_path.exists():
                atomic(intent_path, canonical(intent))
            fault('intent')
            atomic(owner_path, canonical(rebound_owner))
            fault('owner')
            atomic(marker, canonical(rebound))
            fault('record')
        return dict(result='UNPREPARED_RECONCILED' if apply else 'UNPREPARED_RECONCILABLE',
                    operation_id=operation, readers_resumed=False, database_writes=0,
                    authority_writes=0, grant_writes=0, recovery_required=True)


def abort_unacquired(controller, node, operation, *, apply=False, fault=lambda event: None):
    from credential_renewal import atomic, canonical, digest, parse, read_private, require

    require(re.fullmatch('[a-z0-9-]{16,96}', operation) is not None, 'OPERATION_ID')
    require(node.role == 'RU' and controller.validator.all_activated and controller.multiple
            and list(controller.nodes) == ['RU', 'NL', 'NL2']
            and controller.nodes['RU'].node is node, 'LOCAL_RU_FIRST_REQUIRED')
    marker = controller.root / 'transaction.json'
    intent_path = controller.root / ('unacquired-abort-' + operation + '.json')
    with controller.operation.lock(), node.operation.lock():
        record = parse(read_private(marker))
        require(record['operation_id'] == operation, 'OPERATION_ID')
        intent = parse(read_private(intent_path)) if intent_path.exists() else None
        if intent is not None:
            require(set(intent) == {'schema', 'operation_id', 'record_before', 'observed'}
                    and intent['schema'] == 1 and intent['operation_id'] == operation,
                    'ABORT_INTENT_INVALID')
        original = intent['record_before'] if intent is not None else record
        require(set(original) == {'schema', 'operation_id', 'state', 'first_cause', 'before_sha256',
                    'before', 'previous', 'previous_secondary', 'acquired', 'quiesced', 'commit_decided', 'gate'}
                and original['schema'] == 1 and original['operation_id'] == operation
                and original['state'] == 'RECOVERY_REQUIRED' and original['first_cause'] == 'OPERATION_BUSY'
                and original['commit_decided'] is False and original['acquired'] == []
                and original['quiesced'] == [], 'UNACQUIRED_REQUIRED')
        require(digest(canonical(original['before'])) == original['before_sha256'], 'BEFORE_BINDING')
        require({path.name for path in node.state.iterdir()} <= {'operation.lock', 'completed.json', 'archive'},
                'LOCAL_OWNERSHIP_OR_ARTIFACT_PRESENT')
        ledger = node.state / 'completed.json'
        require(not ledger.exists() or operation not in parse(read_private(ledger)), 'OPERATION_ALREADY_EXECUTED')
        plan = controller.root / 'plan.json'
        require(not plan.exists() or parse(read_private(plan))['operation_id'] != operation,
                'PREPARATION_ARTIFACT_PRESENT')
        snapshot, gateway, current, pending_revocations = controller.read(operation)
        require(not pending_revocations, 'PENDING_REVOCATIONS')
        require(snapshot == original['previous'] and gateway['secondary_snapshot'] == original['previous_secondary'],
                'AUTHORITY_OR_GRANTS_CHANGED')
        for role, actual in current.items():
            expected = dict(original['before'][role])
            compared = dict(actual)
            if role == 'RU':
                expected.pop('database_sha256')
                compared.pop('database_sha256')
            require(compared == expected, 'NON_DATABASE_STATE_CHANGED')
        require(set(current) == set(original['before']), 'NODE_SET')
        if intent is None:
            intent = dict(schema=1, operation_id=operation, record_before=original, observed=current)
        terminal = dict(original, state='ABORTED', terminal_result='UNACQUIRED_ABORTED_READERS_UNCHANGED',
                        unacquired_abort_sha256=digest(canonical(intent)))
        require(record in (original, terminal), 'ABORT_STATE_CHANGED')
        if apply:
            if not intent_path.exists():
                atomic(intent_path, canonical(intent))
            fault('intent')
            atomic(marker, canonical(terminal))
            fault('record')
            controller.receipts(terminal)
        return dict(result='UNACQUIRED_ABORTED' if apply else 'UNACQUIRED_ABORTABLE', operation_id=operation,
                    first_cause=original['first_cause'], readers_changed=False, database_writes=0,
                    authority_writes=0, grant_writes=0, normal_renewal_required=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--operation', required=True)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--abort-unacquired', action='store_true')
    arguments = parser.parse_args()
    sys.path.insert(0, str(arguments.runtime.resolve()))
    from credential_renewal import Rejected, parse, read_private, require
    from node import construct
    from production_controller import ProductionController
    from production_transport import SshNode
    from runtime_controller import LocalNode

    try:
        config = parse(read_private(arguments.config))
        require(config['schema'] == 2 and config['approved_leaf_crl_schedule'] is True, 'FLEET_CONFIG_REQUIRED')
        node, source = construct(Path(config['node_config']))
        nodes = {'RU': LocalNode(node, source),
                 'NL': SshNode('NL', config['nl_source_sha256'], forced=config['ssh']),
                 'NL2': SshNode('NL', config['secondary']['source_sha256'], forced=config['secondary']['ssh'])}
        controller = ProductionController(Path(config['coordinator_state']), nodes, node.validator)
        action = abort_unacquired if arguments.abort_unacquired else reconcile
        print(json.dumps(action(controller, node, arguments.operation, apply=arguments.apply)))
    except Exception as error:
        print(json.dumps(dict(result='FAIL_CLOSED', cause=str(error) if isinstance(error, Rejected) else 'UNKNOWN')))
        raise SystemExit(1) from None


if __name__ == '__main__':
    main()
