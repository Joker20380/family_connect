"""Non-activating operator completion of an acquired, never-prepared expired renewal."""
from scripts.reconcile_unprepared_renewal import reconcile


def checked_intent(intent):
    from credential_renewal import canonical, digest, require

    require(set(intent) == {'schema', 'record', 'binding'} and intent['schema'] == 1,
            'UNPREPARED_INTENT_INVALID')
    record = intent['record']
    require(record['state'] == 'RECOVERY_REQUIRED' and record['first_cause'] == 'STALE_NODE_STATE'
            and not record['commit_decided'] and not record['quiesced']
            and not record.get('mode') and not record.get('reconciliation')
            and not record.get('fenced_rollback') and not record.get('terminal_result')
            and record['acquired'] == ['RU', 'NL', 'NL2']
            and set(record['before']) == set(record['acquired']), 'UNPREPARED_REQUIRED')
    require(record['before_sha256'] == digest(canonical(record['before']))
            and len(record['unprepared_rebase_sha256']) == 64, 'BEFORE_BINDING')
    binding = dict(operation_id=record['operation_id'], before_sha256=record['before_sha256'],
                   previous_sha256=digest(canonical(record['previous'])),
                   unprepared_rebase_sha256=record['unprepared_rebase_sha256'],
                   first_cause=record['first_cause'], commit_decided=False)
    require(intent['binding'] == binding, 'UNPREPARED_INTENT_INVALID')
    return record


def begin(controller, node, operation, *, apply=False):
    from credential_renewal import atomic, canonical, digest, parse, read_private, require

    path = controller.root / ('expired-unprepared-' + operation + '.json')
    if path.exists():
        with controller.operation.lock():
            intent = parse(read_private(path))
            require(checked_intent(intent)['operation_id'] == operation, 'OPERATION_ID')
            require(parse(read_private(controller.root / 'transaction.json')) == intent['record'],
                    'UNPREPARED_RECORD_CHANGED')
            return intent
    reconcile(controller, node, operation, apply=apply, expired_leaf_predecessor=True)
    if not apply:
        return dict(result='EXPIRED_UNPREPARED_RECONCILABLE', readers_resumed=False,
                    database_writes=0, authority_writes=0, grant_writes=0)
    with controller.operation.lock():
        record = parse(read_private(controller.root / 'transaction.json'))
        binding = dict(operation_id=operation, before_sha256=record['before_sha256'],
                       previous_sha256=digest(canonical(record['previous'])),
                       unprepared_rebase_sha256=record['unprepared_rebase_sha256'],
                       first_cause=record['first_cause'], commit_decided=False)
        intent = dict(schema=1, record=record, binding=binding)
        checked_intent(intent)
        atomic(path, canonical(intent))
        return intent


def finish_node(node, intent, *, apply=False):
    from credential_renewal import canonical, digest, require

    record = checked_intent(intent)
    operation = record['operation_id']
    expected = record['before'][node.gateway_slot]
    with node.operation.lock():
        owner = node.owner(operation)
        require(owner['state'] in ('ACQUIRED', 'ROLLED_BACK', 'ABORTED_FENCED')
                and not owner.get('commit_decided') and not owner.get('mode')
                and owner['expected_state'] == expected, 'UNPREPARED_OWNER_REQUIRED')
        allowed = {'owner.json', 'operation.lock', 'services-before.json', 'completed.json',
                   'archive', 'directory-before.json'}
        if owner['state'] in ('ROLLED_BACK', 'ABORTED_FENCED'):
            allowed.add('rollback-terminal.json')
        require({path.name for path in node.state.iterdir()} <= allowed,
                'PREPARATION_ARTIFACT_PRESENT')
        require(node.barrier.stopped(), 'READERS_NOT_QUIESCED')
        require(node.inspect() == expected, 'STALE_NODE_STATE')
        now = int(node.clock())
        snapshot = record['previous_secondary'] if node.gateway_slot == 'NL2' else record['previous']
        material = node.validator.validate(canonical(snapshot), now, expired_leaf_predecessor=True)
        require(material[4].not_valid_after_utc.timestamp() <= now, 'PREVIOUS_LEAF_NOT_EXPIRED')
    payload = dict(reason='PREVIOUS_LEAF_EXPIRED', expected_state_sha256=digest(canonical(expected)),
                   controller_operation_sha256=digest(canonical(intent['binding'])))
    if not apply:
        return dict(result='EXPIRED_UNPREPARED_NODE_READY', operation_id=operation,
                    readers_resumed=False, database_writes=0)
    if owner['state'] == 'ACQUIRED':
        node.rollback(operation)
    return node.finalize_fenced_rollback(operation, payload)


def complete(controller, intent):
    from credential_renewal import canonical, digest, parse, read_private, require

    original = checked_intent(intent)
    operation = original['operation_id']
    with controller.operation.lock():
        record = parse(read_private(controller.root / 'transaction.json'))
        terminal = dict(original, state='CLEANING', fenced_rollback=intent['binding'],
                        terminal_result='ROLLED_BACK_READERS_STOPPED')
        require(record in (original, terminal, dict(terminal, state='ABORTED')),
                'UNPREPARED_RECORD_CHANGED')
        if record == original:
            for role, remote in controller.nodes.items():
                expected = original['before'][role]
                require(remote.call('inspect', operation) == expected, 'STALE_NODE_STATE')
                require(remote.call('stopped', operation)['stopped'], 'READERS_NOT_QUIESCED')
                payload = dict(reason='PREVIOUS_LEAF_EXPIRED',
                    expected_state_sha256=digest(canonical(expected)),
                    controller_operation_sha256=digest(canonical(intent['binding'])))
                receipt = remote.call('finalize-fenced-rollback', operation, payload)
                require(receipt['result'] == 'ROLLED_BACK_READERS_STOPPED'
                        and receipt['operation_id'] == operation
                        and all(receipt[name] == value for name, value in payload.items()),
                        'ROLLBACK_TERMINAL_BINDING_MISMATCH')
            controller.save(terminal, 'CLEANING')
            record = terminal
        return controller.cleanup(record)
