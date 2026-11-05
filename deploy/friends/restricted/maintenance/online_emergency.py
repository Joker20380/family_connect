import os

from cryptography import x509

from credential_renewal import Rejected, atomic, canonical, digest, parse, private_directory, read_private, require
from maintenance_policy import maintenance_gate
import gateway_set


def sequence(snapshot):
    return x509.load_pem_x509_crl(snapshot['crl'].encode()).extensions.get_extension_for_class(x509.CRLNumber).value.crl_number


def origin_check(node, origin, operation):
    from online_controller import prepared_receipt
    require(type(origin) is dict and set(origin) == {'operation_id', 'decision', 'plan', 'prepared', 'fence'},
            'ONLINE_EMERGENCY_ORIGIN')
    plan = origin['plan']
    require(origin['operation_id'] == operation == plan['operation_id'] and origin['decision'] == 'COMMIT'
            and type(origin['fence']) is int and origin['fence'] > 0
            and plan['gateway_ids'] == node.gateway_ids and set(origin['prepared']) == {'RU', 'NL', 'NL2'},
            'ONLINE_EMERGENCY_ORIGIN')
    for slot, receipt in origin['prepared'].items():
        prepared_receipt(receipt, slot, operation, plan)
    issued = plan['grant_plan']['issued_at']
    for slot in ('NL', 'NL2'):
        local = gateway_set.selected(plan, slot)
        node.validator.transition(canonical(local['previous']), canonical(local['candidate']), issued)
    return plan


def sync_directory(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def handoff(node, operation, origin):
    with node.operation.lock():
        plan = origin_check(node, origin, operation)
        owner = node.owner(operation)
        location = node.state/'archive'/('online-'+digest(operation.encode()))
        if owner.get('mode') == 'online-emergency':
            require(read_private(node.state/'online-origin.json') == canonical(origin), 'ONLINE_EMERGENCY_ORIGIN')
            require(node.barrier.stopped(), 'READERS_NOT_QUIESCED')
            require(owner['state'] == 'QUIESCED' and not (node.state/'prepared-plan.json').exists(),
                    'ONLINE_EMERGENCY_ALREADY_PREPARED')
            current = node.inspect()
            require(current.get('policy') == owner['expected_state'].get('policy'),
                    'ONLINE_EMERGENCY_POLICY_AUTHORIZATION_REQUIRED')
            if current != owner['expected_state']:
                owner['expected_state'] = current
                atomic(node.state/'owner.json', canonical(owner))
            return receipt(node, operation, origin)
        require(owner.get('mode') == 'online' and owner['fence'] == origin['fence']
                and owner['state'] in ('ONLINE_EMERGENCY_REQUIRED', 'ONLINE_HANDOFF'), 'ONLINE_STALE_WRITER')
        node.barrier.quiesce()
        require(node.barrier.stopped(), 'READERS_NOT_QUIESCED')
        require(node.inspect().get('policy') == owner['expected_state'].get('policy'),
                'ONLINE_EMERGENCY_POLICY_AUTHORIZATION_REQUIRED')
        if owner['state'] != 'ONLINE_HANDOFF':
            require(read_private(node.state/'plan.json') == canonical(plan)
                    and parse(read_private(node.state/'online-prepared.json')) == origin['prepared'][node.gateway_slot],
                    'ONLINE_EMERGENCY_ORIGIN')
            location.parent.mkdir(mode=0o700, exist_ok=True)
            private_directory(location.parent)
            location.mkdir(mode=0o700, exist_ok=True)
            private_directory(location)
            sync_directory(location.parent)
            sync_directory(node.state)
            names = [path.name for path in node.state.iterdir() if path.is_file() and path.name not in
                     ('operation.lock', 'owner.json', 'completed.json', 'services-before.json')
                     and not path.name.startswith('start-intent-')]
            manifest = {name: digest(read_private(node.state/name)) for name in names}
            atomic(location/'origin.json', canonical(origin))
            atomic(location/'owner.json', canonical(owner))
            atomic(location/'manifest.json', canonical(manifest))
            owner.update(handoff_sha256=digest(canonical(origin)), manifest_sha256=digest(canonical(manifest)),
                         state='ONLINE_HANDOFF')
            atomic(node.state/'owner.json', canonical(owner))
            node.fault('emergency-handoff-decided')
        require(owner['handoff_sha256'] == digest(canonical(origin)), 'ONLINE_EMERGENCY_ORIGIN')
        manifest = parse(read_private(location/'manifest.json'))
        require(digest(canonical(manifest)) == owner['manifest_sha256'], 'ONLINE_EMERGENCY_ARCHIVE')
        for name, expected in manifest.items():
            require('/' not in name and name not in ('.', '..'), 'ARCHIVE_PATH')
            source, target = node.state/name, location/name
            if source.exists():
                require(digest(read_private(source)) == expected and not target.exists(), 'ONLINE_EMERGENCY_ARCHIVE')
                os.replace(source, target)
                sync_directory(location)
                sync_directory(node.state)
            require(digest(read_private(target)) == expected, 'ONLINE_EMERGENCY_ARCHIVE')
            node.fault('emergency-archive-'+name)
        atomic(node.state/'online-origin.json', canonical(origin))
        if node.role == 'NL':
            atomic(node.state/'directory-before.json', canonical(dict(sha256=digest(node.read_directory()[0]))))
        owner.update(mode='online-emergency', expected_state=node.inspect(), fence=origin['fence']+1,
                     online_commit_decided=True, commit_decided=False, state='QUIESCED')
        atomic(node.state/'owner.json', canonical(owner))
        node.fault('emergency-handoff-complete')
        return receipt(node, operation, origin)


def receipt(node, operation, origin):
    return dict(operation_id=operation, slot=node.gateway_slot, origin_sha256=digest(canonical(origin)),
                state=node.inspect(), stopped=node.barrier.stopped())


def validate(node, plan):
    origin = plan['online_emergency']
    parent = origin_check(node, origin, plan['operation_id'])
    require(node.owner(plan['operation_id']).get('mode') == 'online-emergency'
            and read_private(node.state/'online-origin.json') == canonical(origin), 'ONLINE_EMERGENCY_ORIGIN')
    for slot in ('NL', 'NL2'):
        current, previous = gateway_set.selected(plan, slot), gateway_set.selected(parent, slot)
        require(current['previous'] == dict(previous['candidate'], grants=plan['grant_plan']['before']['restricted_grants'])
                and current['nl_profile_sha256'] in (previous['nl_profile_sha256'], origin['prepared'][slot]['target_sha256']),
                'ONLINE_EMERGENCY_BINDING')
    floor = sequence(parent['candidate'])
    require(sequence(plan['candidate']) == floor+1
            and plan['grant_plan']['before']['restricted_crl_sequence'][0]['sequence'] in (floor-1, floor),
            'ONLINE_EMERGENCY_FLOOR')
    return floor


def gateway_inputs(node, gateway, origin):
    parent = origin_check(node, origin, origin['operation_id'])
    require(read_private(node.state/'online-origin.json') == canonical(origin), 'ONLINE_EMERGENCY_ORIGIN')
    result = dict(gateway)
    for slot in ('NL', 'NL2'):
        actual = gateway if slot == 'NL' else gateway['secondary']
        local = gateway_set.selected(parent, slot)
        target = local['candidate']
        require(actual['profile_sha256'] in (local['nl_profile_sha256'], origin['prepared'][slot]['target_sha256'])
                and any(actual['certificate'] == local[phase]['certificate'] and actual['revocations'] == local[phase]['crl']
                        for phase in ('previous', 'candidate')), 'ONLINE_EMERGENCY_BINDING')
        replacement = dict(actual, certificate=target['certificate'], revocations=target['crl'])
        if slot == 'NL':
            result.update(replacement)
        else:
            result['secondary'] = replacement
    return result


def run(controller, operation, *, approval=None):
    from online_controller import call
    with controller.operation.lock():
        record = parse(read_private(controller.root/'transaction.json'))
        require(record['operation_id'] == operation and record.get('mode') in ('online', 'online-emergency'),
                'ONLINE_OPERATION_BINDING')
        if record.get('mode') == 'online-emergency' and record['state'] == 'COMMITTED':
            return dict(result='EMERGENCY_RECOVERED', operation_id=operation, replay=True)
        if record.get('mode') == 'online':
            require(record['state'] == 'ONLINE_EMERGENCY_REQUIRED' and record['commit_decided']
                    and record['decision'] == 'COMMIT', 'ONLINE_EMERGENCY_REQUIRED')
            plan = parse(read_private(controller.root/'plan.json'))
            require(digest(canonical(plan)) == record['plan_sha256'], 'ONLINE_DECISION_CORRUPT')
            origin = dict(operation_id=operation, decision='COMMIT', plan=plan,
                          prepared=record['prepared'], fence=record['fence'])
            record.update(mode='online-emergency', online_parent=origin, handoffs={}, cursor=0,
                          continuation_id='emergency-'+digest(canonical(origin)), emergency_commit_decided=False,
                          terminal_result='EMERGENCY_RECOVERED')
            controller.save(record, 'EMERGENCY_HANDOFF')
        try:
            if record['state'] in ('EMERGENCY_HANDOFF', 'EMERGENCY_APPROVAL_REQUIRED'):
                for slot in controller.nodes:
                    received = call(controller, slot, operation, 'emergency-handoff', origin=record['online_parent'])
                    require(set(received) == {'operation_id','slot','origin_sha256','state','stopped'}
                            and received['operation_id'] == operation and received['slot'] == slot
                            and received['origin_sha256'] == digest(canonical(record['online_parent']))
                            and received['stopped'] is True, 'ONLINE_EMERGENCY_RECEIPT')
                    record['handoffs'][slot] = received
                    controller.save(record, 'EMERGENCY_HANDOFF')
                current = {slot: value['state'] for slot, value in record['handoffs'].items()}
                controller.check_admission(current)
                request = dict(operation_id=operation, continuation_id=record['continuation_id'],
                               origin_sha256=digest(canonical(record['online_parent'])), expected=current,
                               expected_state_sha256=digest(canonical(current)), purpose='OPERATOR_APPROVED_OUTAGE')
                record['emergency_request'] = request
                controller.save(record, 'EMERGENCY_APPROVAL_REQUIRED')
                gate = maintenance_gate(operation, current, int(controller.clock()), approval=approval)
                if gate['result'] != 'RENEWAL_READY':
                    return dict(result='EMERGENCY_APPROVAL_REQUIRED', request=request, automatic_retry=False)
                record.update(before=current, gate=gate)
                controller.save(record, 'EMERGENCY_AUTHORIZED')
            if record['state'] == 'EMERGENCY_AUTHORIZED':
                gateway = controller.nodes['NL'].call('public-gateway', operation)
                gateway['secondary'] = controller.nodes['NL2'].call('public-gateway', operation)
                plan = call(controller, 'RU', operation, 'emergency-prepare', gateway=gateway, origin=record['online_parent'])
                require(plan['online_emergency'] == record['online_parent'] and plan['operation_id'] == operation,
                        'ONLINE_EMERGENCY_ORIGIN')
                atomic(controller.root/'plan.json', canonical(plan))
                record['emergency_plan_sha256'] = digest(canonical(plan))
                controller.save(record, 'EMERGENCY_PREPARED')
            if not record['emergency_commit_decided']:
                plan = parse(read_private(controller.root/'plan.json'))
                steps = [(slot, action) for action in ('stage', 'promote') for slot in controller.nodes]
                while record['cursor'] < len(steps):
                    slot, action = steps[record['cursor']]
                    response = controller.nodes[slot].call(action, operation, plan if action == 'stage' else None)
                    require(response['plan_sha256'] == record['emergency_plan_sha256'], 'PLAN_BINDING')
                    record['cursor'] += 1
                    controller.save(record, 'EMERGENCY_PUBLISHING')
                receipts = {slot: node.call('readback', operation) for slot, node in controller.nodes.items()}
                require(all(value == receipts['RU'] for value in receipts.values()) and
                        receipts['RU']['plan_sha256'] == record['emergency_plan_sha256'], 'RU_NL_MISMATCH')
                record.update(reconciliation=receipts, emergency_commit_decided=True)
                controller.save(record, 'EMERGENCY_COMMIT_DECIDED')
            if record['state'] == 'CLEANING':
                return controller.cleanup(record)
            return controller.finish(record)
        except Exception as error:
            cause = str(error) if isinstance(error, Rejected) else 'IO_OR_TRANSPORT_FAILURE'
            unknown_transport = cause in ('IO_OR_TRANSPORT_FAILURE', 'REMOTE_OUTCOME_UNKNOWN_READBACK_REQUIRED',
                                          'RPC_RESPONSE_SCHEMA', 'RPC_RESPONSE_BINDING')
            if not unknown_transport and record['state'] not in ('EMERGENCY_HANDOFF', 'EMERGENCY_APPROVAL_REQUIRED', 'CLEANING'):
                for node in controller.nodes.values():
                    try:
                        node.call('fence', operation)
                    except Exception:
                        pass
            record['emergency_cause'] = cause
            controller.save(record, record['state'])
            return dict(result='EMERGENCY_BLOCKED', cause=cause, operation_id=operation, automatic_retry=False)
