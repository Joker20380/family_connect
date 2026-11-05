import os
import re
import base64

from cryptography import x509

from credential_renewal import atomic, canonical, digest, parse, read_private, require
from online_contract import CONTRACT, directory_material, projection, publication_receipt, ready_receipt, validate_plan
import gateway_set


def owned(node, operation, token):
    owner = node.owner(operation)
    require(owner.get('mode') == 'online' and type(token) is int and owner['fence'] == token,
            'ONLINE_STALE_WRITER')
    require(not node.barrier.stopped(), 'ONLINE_READER_STOPPED')
    return owner


def check_policy(node, owner, plan):
    actual = node.inspect(online=True)
    require(actual.get('policy') == owner['expected_state'].get('policy'), 'ONLINE_POLICY_CHANGED')
    if node.role == 'RU':
        before = projection(plan['grant_plan']['before'])
        now = projection(node.database.snapshot())
        require({key: value for key, value in now.items() if key != 'restricted_crl_sequence'} ==
                {key: value for key, value in before.items() if key != 'restricted_crl_sequence'}, 'ONLINE_POLICY_CHANGED')
        old = before['restricted_crl_sequence'][0]['sequence']
        crl = x509.load_pem_x509_crl(plan['candidate']['crl'].encode())
        new = crl.extensions.get_extension_for_class(x509.CRLNumber).value.crl_number
        require(now['restricted_crl_sequence'][0]['sequence'] in (old, new), 'ONLINE_SEQUENCE_CHANGED')
        require(node.database.pending_revocations(crl, int(node.clock())) == 0, 'ONLINE_REVOCATION_FORBIDDEN')


def reader(node, candidate=None):
    require(node.online_reader is not None, 'ONLINE_RUNTIME_CONTRACT_UNKNOWN')
    result = node.online_reader(candidate)
    require(type(result) is dict and result.get('contract') == CONTRACT, 'ONLINE_RUNTIME_CONTRACT_UNKNOWN')
    require(result['gateway'] == node.gateway_ids[node.gateway_slot]
            and result['profile_sha256'] == digest(node.read('gateway.json')[0]), 'ONLINE_RUNTIME_READBACK')
    return result


def acquire(node, operation, payload):
    with node.operation.lock():
        token, expected, contract = payload['fence'], payload['expected'], payload['online']
        require(type(token) is int and token > 0 and contract['contract'] == CONTRACT, 'ONLINE_CONTRACT')
        ledger = parse(read_private(node.state/'completed.json')) if (node.state/'completed.json').exists() else {}
        require(operation not in ledger, 'OPERATION_REPLAY')
        path = node.state/'owner.json'
        if path.exists():
            owner = node.owner(operation)
            require(owner.get('mode') == 'online' and owner['expected_state'] == expected and
                    owner['online'] == contract and token >= owner['fence'], 'ONLINE_STALE_WRITER')
            owner['fence'] = token
        else:
            require(node.inspect(online=True) == expected, 'STALE_NODE_STATE')
            require(node.gateway_ids is not None and node.validator.all_activated, 'ONLINE_MEMBERSHIP_REQUIRED')
            require(not node.barrier.stopped(), 'ONLINE_READER_STOPPED')
            owner = dict(schema=1, operation_id=operation, expected_state=expected, state='ONLINE_ACQUIRED',
                         first_cause=None, mode='online', fence=token, online=contract, commit_decided=False)
        atomic(path, canonical(owner))
        node.fault('online-acquired')
        return dict(operation_id=operation, fence=token, slot=node.gateway_slot)


def staged(node, operation, payload):
    node.stage(operation, payload['plan'], online_token=payload['fence'])
    with node.operation.lock():
        owner = owned(node, operation, payload['fence'])
        plan = parse(read_private(node.state/'plan.json'))
        check_policy(node, owner, plan)
        receipt = dict(operation_id=operation, slot=node.gateway_slot, plan_sha256=digest(canonical(plan)))
        if node.role == 'NL':
            staged = node.state/'gateway.json.staged'
            candidate = parse(read_private(staged)) if staged.exists() else parse(node.read('gateway.json')[0])
            candidate.pop('private_key')
            receipt['runtime'] = reader(node, candidate)
            profile = node.public_gateway()
            from control.friends.restricted import directory, clock_nanoseconds
            directory(node.read_directory()[0], profile['family'], profile['gateway'],
                      now_ns=clock_nanoseconds(node.clock))
            if node.profile_store is not None:
                receipt['directory'] = node.profile_store.locator.directory_port.read(profile, node.clock())
            metadata = parse(read_private(node.state/'files.json'))
            receipt['target_sha256'] = metadata.get('gateway.json', {}).get('after',
                owner['expected_state']['files']['gateway.json'])
        atomic(node.state/'online-prepared.json', canonical(receipt))
        node.fault('online-prepared')
        return receipt


def replace(node, name, metadata, permit):
    raw = read_private(node.state/(name+'.staged'))
    require(digest(raw) == metadata['after'], 'STAGED_FILE_CHANGED')
    current, information = node.read(name)
    require(information == {key: metadata[key] for key in ('uid', 'gid', 'mode')}, 'ACTIVE_FILE_METADATA_CHANGED')
    require(digest(current) in (metadata['before'], metadata['after']), 'ACTIVE_FILE_UNEXPECTED')
    permit()
    if current == raw:
        return
    if node.profile_store is not None:
        from control.friends.profile_store import parse as profile_parse
        port = node.profile_store.locator.directory_port
        before = port.read(profile_parse(current), node.clock())
        node.profile_store.replace(raw, expected=current, permit=permit)
        port.after(before, profile_parse(raw), node.clock())
    else:
        temporary = node.state/(name+'.promoting')
        atomic(temporary, raw)
        os.chown(temporary, metadata['uid'], metadata['gid'])
        permit()
        node.fault('online-before-rename-'+name)
        os.replace(temporary, node.live_path(name))
        descriptor = os.open(node.live_path(name).parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    node.fault('online-after-rename-'+name)
    require(node.read(name)[0] == raw, 'ONLINE_PUBLICATION_READBACK')


def publish(node, operation, payload):
    with node.operation.lock(), node.profile_lock():
        owner = owned(node, operation, payload['fence'])
        require(owner['commit_decided'], 'ONLINE_COMMIT_REQUIRED')
        plan = parse(read_private(node.state/'plan.json'))
        validate_plan(node, plan, committed=True)
        check_policy(node, owner, plan)
        metadata = parse(read_private(node.state/'files.json'))
        permit = lambda: (owned(node, operation, payload['fence']), validate_plan(node, plan, committed=True), check_policy(node, owner, plan))
        if node.role == 'RU':
            receipts = payload['receipts']
            require(set(receipts) == {'NL', 'NL2'}, 'ONLINE_RUNTIME_RECEIPT')
            for slot, receipt in receipts.items():
                publication_receipt(slot, operation, plan, receipt, int(node.clock()))
                require(receipt['runtime']['instance'] == owner['prepared'][slot]['runtime']['instance'],
                        'ONLINE_RUNTIME_REPLACED')
                require(receipt['runtime']['profile_sha256'] == owner['prepared'][slot]['target_sha256'],
                        'ONLINE_RUNTIME_READBACK')
            marker = dict(schema=1, contract=CONTRACT, operation_id=operation, plan_sha256=digest(canonical(plan)),
                          ready=False, crl_sha256=digest(plan['candidate']['crl'].encode()),
                          gateways=plan['gateway_ids'], issued_at=plan['grant_plan']['issued_at'])
            atomic(node.live/'online-delivery.json', canonical(marker))
            node.fault('online-delivery-fenced')
            with node.database.connect(write=True) as database:
                current = projection(node.database.snapshot(database))
                expected = projection(plan['grant_plan']['before'])
                require({key: value for key, value in current.items() if key != 'restricted_crl_sequence'} ==
                        {key: value for key, value in expected.items() if key != 'restricted_crl_sequence'},
                        'ONLINE_POLICY_CHANGED')
                crl = x509.load_pem_x509_crl(plan['candidate']['crl'].encode())
                number = crl.extensions.get_extension_for_class(x509.CRLNumber).value.crl_number
                require(current['restricted_crl_sequence'][0]['sequence'] in
                        (expected['restricted_crl_sequence'][0]['sequence'], number), 'ONLINE_SEQUENCE_CHANGED')
                database.execute('UPDATE restricted_crl_sequence SET sequence=? WHERE singleton=1', (number,))
            node.fault('online-sequence')
        for name, information in metadata.items():
            replace(node, name, information, permit)
        if node.role == 'NL':
            runtime = reader(node)
            prepared = parse(read_private(node.state/'online-prepared.json'))
            require(runtime['instance'] == prepared['runtime']['instance'], 'ONLINE_RUNTIME_REPLACED')
            require(runtime['profile_sha256'] == metadata.get('gateway.json', {}).get('after',
                    owner['expected_state']['files']['gateway.json']), 'ONLINE_RUNTIME_READBACK')
            receipt = ready_receipt(node.gateway_slot, operation, plan, runtime)
            raw = node.read_directory()[0]
            receipt['directory'] = dict(payload=base64.b64encode(raw).decode(), sha256=digest(raw))
            publication_receipt(node.gateway_slot, operation, plan, receipt, int(node.clock()))
        else:
            from production_node import pinned
            from control.friends.restricted import directory, timestamp_ns
            for slot, published in payload['receipts'].items():
                selected = gateway_set.selected(plan, slot)
                trust = node.validator.validate(canonical(selected['candidate']), int(node.clock()))[1]
                raw, issued, expires = directory_material(published['directory'], trust['family'],
                    plan['gateway_ids'][slot], int(node.clock()))
                destination = node.directory_destination(slot)
                previous = pinned(destination, {os.geteuid()})[0]
                value = directory(previous, trust['family'], plan['gateway_ids'][slot], now_ns=int(node.clock())*1_000_000_000)
                require(issued >= timestamp_ns(value['issued_at']) and expires >= timestamp_ns(value['expires_at'])
                        and (raw == previous or issued > timestamp_ns(value['issued_at'])), 'DIRECTORY_TIME_ROLLBACK')
                permit()
                atomic(destination, raw)
                node.fault('online-directory-'+slot)
            permit()
            marker['ready'] = True
            atomic(node.live/'online-delivery.json', canonical(marker))
            node.fault('online-delivery-ready')
            receipt = dict(operation_id=operation, slot='RU', plan_sha256=digest(canonical(plan)),
                           delivery_sha256=digest(canonical(marker)))
        atomic(node.state/'online-published.json', canonical(receipt))
        node.operation.advance(owner, 'ONLINE_PUBLISHED')
        return receipt


def dispatch(node, operation, payload):
    require(node.online_qualification is True or getattr(node, 'online_runtime', None) is not None,
            'ONLINE_QUALIFICATION_ONLY')
    require(type(operation) is str and re.fullmatch('[a-z0-9-]{16,96}', operation), 'OPERATION_ID')
    require(type(payload) is dict and type(payload.get('command')) is str, 'ONLINE_RPC_SCHEMA')
    command = payload['command']
    schemas = {'capabilities': set(), 'inspect': set(), 'acquire': {'fence', 'expected', 'online'}, 'prepare': {'fence', 'gateway'},
               'emergency-handoff': {'origin'}, 'emergency-prepare': {'origin', 'gateway'},
               'stage': {'fence', 'plan'}, 'decide': {'fence', 'plan_sha256', 'prepared'},
               'complete': {'fence', 'reconciliation'}, 'abort': {'fence'}, 'fence': {'fence'},
               'publish': {'fence'} | ({'receipts'} if node.role == 'RU' else set())}
    require(command in schemas and set(payload) == schemas[command] | {'command'}, 'ONLINE_RPC_SCHEMA')
    if command == 'capabilities':
        from online_runtime import capabilities
        return capabilities(node)
    if command == 'inspect':
        return node.inspect(online=True)
    if command == 'emergency-handoff':
        from online_emergency import handoff
        return handoff(node, operation, payload['origin'])
    if command == 'emergency-prepare':
        return node.prepare(operation, payload['gateway'], emergency_handoff=payload['origin'])
    if command == 'acquire':
        return acquire(node, operation, payload)
    if command == 'prepare':
        return node.prepare(operation, payload['gateway'], online_token=payload['fence'])
    if command == 'stage':
        return staged(node, operation, payload)
    if command == 'publish':
        return publish(node, operation, payload)
    if command == 'fence':
        with node.operation.lock():
            owner = node.owner(operation)
            require(owner.get('mode') == 'online' and owner['fence'] == payload['fence'], 'ONLINE_STALE_WRITER')
            node.operation.advance(owner, 'ONLINE_EMERGENCY_REQUIRED')
            node.barrier.quiesce()
            require(node.barrier.stopped(), 'READERS_NOT_QUIESCED')
            return dict(stopped=True, operation_id=operation, slot=node.gateway_slot)
    if command in ('complete', 'abort'):
        with node.operation.lock():
            if (node.state/'owner.json').exists():
                owner = owned(node, operation, payload['fence'])
                require(owner['commit_decided'] == (command == 'complete'), 'ONLINE_DECISION_IMMUTABLE')
                if owner['state'] not in ('RESUMED', 'ABORTED', 'CLEANING'):
                    if command == 'complete':
                        require(owner['state'] == 'ONLINE_PUBLISHED', 'ONLINE_NOT_PUBLISHED')
                        local = node.readback(operation)
                        require(set(payload['reconciliation']) == {'RU','NL','NL2'} and
                                all(value == local for value in payload['reconciliation'].values()),
                                'RU_NL_RECONCILIATION_FAILED')
                        atomic(node.state/'reconciliation.json', canonical(payload['reconciliation']))
                    else:
                        actual, expected = node.inspect(online=True), dict(owner['expected_state'])
                        for name in ('database_sha256', 'policy'):
                            actual.pop(name, None)
                            expected.pop(name, None)
                        require(actual == expected, 'ONLINE_ABORT_NOT_PROVEN')
                    node.operation.advance(owner, 'RESUMED' if command == 'complete' else 'ABORTED')
            elif command == 'abort':
                ledger = parse(read_private(node.state/'completed.json')) if (node.state/'completed.json').exists() else {}
                if operation not in ledger:
                    return dict(result='NOT_ACQUIRED', operation_id=operation)
        return node.cleanup(operation)
    with node.operation.lock():
        owner = owned(node, operation, payload['fence'])
        if command == 'decide':
            from online_controller import prepared_receipt
            plan = parse(read_private(node.state/'plan.json'))
            require(payload['plan_sha256'] == digest(canonical(plan)), 'PLAN_BINDING')
            validate_plan(node, plan, committed=True)
            check_policy(node, owner, plan)
            require(set(payload['prepared']) == {'RU', 'NL', 'NL2'}, 'ONLINE_PREPARED_RECEIPT')
            for slot, receipt in payload['prepared'].items():
                prepared_receipt(receipt, slot, operation, plan)
            require(payload['prepared'][node.gateway_slot] == parse(read_private(node.state/'online-prepared.json')),
                    'ONLINE_PREPARED_RECEIPT')
            require(not owner['commit_decided'] or owner['prepared'] == payload['prepared'], 'ONLINE_DECISION_IMMUTABLE')
            owner.update(commit_decided=True, prepared=payload['prepared'])
            atomic(node.state/'owner.json', canonical(owner))
            node.fault('online-decision')
            return dict(result='DECIDED', operation_id=operation)
        require(False, 'ONLINE_RPC_SCHEMA')
