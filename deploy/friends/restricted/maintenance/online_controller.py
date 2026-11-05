import re
from concurrent.futures import ThreadPoolExecutor

from credential_renewal import Rejected, atomic, canonical, digest, parse, read_private, require
from online_contract import CONTRACT, eligible, publication_receipt, ready_receipt, window
import gateway_set


def call(controller, role, operation, command, **payload):
    return controller.nodes[role].call('online', operation, dict(command=command, **payload))


def round_trip(controller, operation, command, payloads):
    with ThreadPoolExecutor(max_workers=3) as executor:
        jobs = {role: executor.submit(call, controller, role, operation, command, **payload)
                for role, payload in payloads.items()}
        return {role: job.result() for role, job in jobs.items()}


def prepared_receipt(receipt, role, operation, plan):
    fields = {'slot', 'operation_id', 'plan_sha256'} | ({'runtime', 'target_sha256'} if role != 'RU' else set())
    require(type(receipt) is dict and set(receipt) - {'directory'} == fields and receipt['slot'] == role
            and receipt['operation_id'] == operation and receipt['plan_sha256'] == digest(canonical(plan)),
            'ONLINE_PREPARED_RECEIPT')
    if role != 'RU':
        ready_receipt(role, operation, plan, receipt['runtime'])
        require(re.fullmatch('[0-9a-f]{64}', receipt['target_sha256']) is not None, 'ONLINE_PREPARED_RECEIPT')
    return receipt


def run(controller, operation, *, schedule_seconds, resume):
    require(type(operation) is str and re.fullmatch('[a-z0-9-]{16,96}', operation), 'OPERATION_ID')
    require(controller.multiple and controller.validator.all_activated, 'ONLINE_MEMBERSHIP_REQUIRED')
    timing = window(max(getattr(node, 'timeout_seconds', 120) for node in controller.nodes.values()), schedule_seconds)
    marker = controller.root/'transaction.json'
    with controller.operation.lock():
        record = parse(read_private(marker)) if marker.exists() else None
        if record is not None and record['operation_id'] == operation:
            require(record.get('mode') == 'online' and record['online']['timing'] == timing, 'ONLINE_OPERATION_BINDING')
            if record['state'] in ('COMMITTED', 'ABORTED'):
                return dict(result=record['state'], operation_id=operation, replay=True)
            require(resume, 'ONLINE_RECOVERY_REQUIRED')
        else:
            require(record is None or record['state'] in ('COMMITTED', 'ABORTED'), 'OTHER_OPERATION_RECOVERY_REQUIRED')
            require(not resume, 'ONLINE_OPERATION_MISSING')
            previous, gateway, _, changed = controller.read(operation)
            require(not changed, 'ONLINE_REVOCATION_FORBIDDEN')
            decision = controller.decision(previous, gateway, changed)
            require(decision['result'] == 'RENEWAL_REQUIRED' and set(decision['due']) <= {'leaf', 'crl'},
                    'ONLINE_REFRESH_NOT_DUE')
            eligible(controller.validator, previous, int(controller.clock()), timing)
            eligible(controller.validator, gateway['secondary_snapshot'], int(controller.clock()), timing)
            before = round_trip(controller, operation, 'inspect', {role: {} for role in controller.nodes})
            controller.check_admission(before)
            eligible(controller.validator, previous, int(controller.clock()), timing)
            eligible(controller.validator, gateway['secondary_snapshot'], int(controller.clock()), timing)
            record = dict(schema=1, mode='online', operation_id=operation, online=dict(contract=CONTRACT, timing=timing),
                          before=before, before_sha256=digest(canonical(before)), previous=previous,
                          gateway=gateway, prepared={}, published={}, acquired=[], cleaned=[],
                          fence=0, first_cause=None, commit_decided=False, decision=None)
            controller.save(record, 'ONLINE_ACQUIRING')
        if record['state'] == 'ONLINE_CLEANING':
            return cleanup(controller, record)
        require(record.get('decision') != 'ABORT', 'ONLINE_ABORT_RECOVERY_REQUIRED')
        require(record['state'] != 'ONLINE_EMERGENCY_REQUIRED', 'ONLINE_EMERGENCY_REQUIRED')
        record['fence'] += 1
        controller.save(record, 'ONLINE_FENCING')
        try:
            acquired = round_trip(controller, operation, 'acquire', {role: dict(fence=record['fence'],
                expected=record['before'][role], online=record['online']) for role in controller.nodes})
            for role, receipt in acquired.items():
                require(receipt == dict(operation_id=operation, fence=record['fence'], slot=role), 'ONLINE_FENCE_RECEIPT')
                if role not in record['acquired']:
                    record['acquired'].append(role)
                controller.save(record, 'ONLINE_'+role+'_ACQUIRED')
            if not record['commit_decided']:
                plan = call(controller, 'RU', operation, 'prepare', fence=record['fence'], gateway=record['gateway'])
                require(plan['operation_id'] == operation and plan['previous'] == record['previous']
                        and plan['online'] == record['online'], 'PLAN_BINDING')
                gateway_set.validate(plan, controller.validator, int(controller.clock()), record['before']['RU']['gateway_ids'])
                atomic(controller.root/'plan.json', canonical(plan))
                record['plan_sha256'] = digest(canonical(plan))
                controller.save(record, 'ONLINE_PREPARED')
                staged = round_trip(controller, operation, 'stage', {role: dict(fence=record['fence'], plan=plan)
                    for role in controller.nodes})
                for role, receipt in staged.items():
                    record['prepared'][role] = prepared_receipt(receipt, role, operation, plan)
                    controller.save(record, 'ONLINE_'+role+'_STAGED')
                for role in ('NL', 'NL2'):
                    selected = gateway_set.selected(plan, role)
                    eligible(controller.validator, selected['previous'], int(controller.clock()), timing,
                             candidate=selected['candidate'], full_window=True)
                record.update(commit_decided=True, decision='COMMIT')
                controller.save(record, 'ONLINE_COMMIT_DECIDED')
            plan = parse(read_private(controller.root/'plan.json'))
            require(digest(canonical(plan)) == record['plan_sha256'] and record['decision'] == 'COMMIT', 'ONLINE_DECISION_CORRUPT')
            round_trip(controller, operation, 'decide', {role: dict(fence=record['fence'],
                plan_sha256=record['plan_sha256'], prepared=record['prepared']) for role in controller.nodes})
            for role in controller.nodes:
                controller.save(record, 'ONLINE_'+role+'_DECIDED')
            published = round_trip(controller, operation, 'publish', {role: dict(fence=record['fence'])
                for role in ('NL', 'NL2')})
            for role, receipt in published.items():
                publication_receipt(role, operation, plan, receipt, int(controller.clock()))
                require(receipt['runtime']['profile_sha256'] == record['prepared'][role]['target_sha256']
                        and receipt['runtime']['instance'] == record['prepared'][role]['runtime']['instance'],
                        'ONLINE_RUNTIME_READBACK')
                record['published'][role] = receipt
                controller.save(record, 'ONLINE_'+role+'_PUBLISHED')
            confirmed = round_trip(controller, operation, 'confirm', {role: dict(fence=record['fence'])
                for role in ('NL', 'NL2')})
            require(confirmed == record['published'], 'ONLINE_RUNTIME_CONFIRMATION')
            controller.save(record, 'ONLINE_RUNTIME_CONFIRMED')
            receipt = call(controller, 'RU', operation, 'publish', fence=record['fence'], receipts=record['published'])
            require(receipt['operation_id'] == operation and receipt['plan_sha256'] == record['plan_sha256']
                    and receipt['slot'] == 'RU', 'ONLINE_DELIVERY_RECEIPT')
            record['delivery'] = receipt
            record['reconciliation'] = {role: dict(plan_sha256=record['plan_sha256'],
                crl_sha256=digest(plan['candidate']['crl'].encode()), state='PROMOTED') for role in controller.nodes}
            controller.save(record, 'ONLINE_CLEANING')
            return cleanup(controller, record)
        except Exception as error:
            record['last_cause'] = str(error) if isinstance(error, Rejected) else 'IO_OR_TRANSPORT_FAILURE'
            record['first_cause'] = record['first_cause'] or record['last_cause']
            if isinstance(error, Rejected) and str(error) in {
                    'ONLINE_POLICY_CHANGED', 'ONLINE_REVOCATION_FORBIDDEN', 'ONLINE_SEQUENCE_CHANGED',
                    'ONLINE_RUNTIME_REPLACED', 'ONLINE_READER_STOPPED', 'ONLINE_DECISION_CORRUPT', 'LEAF_EXPIRED_OR_FUTURE',
                    'CRL_EXPIRED_OR_FUTURE'}:
                record['fenced'] = {}
                controller.save(record, 'ONLINE_EMERGENCY_REQUIRED')
                for role in controller.nodes:
                    try:
                        record['fenced'][role] = call(controller, role, operation, 'fence', fence=record['fence'])
                    except Exception:
                        record['fenced'][role] = dict(stopped=None)
                    controller.save(record, 'ONLINE_EMERGENCY_REQUIRED')
                return dict(result='ONLINE_EMERGENCY_REQUIRED', operation_id=operation,
                    decision=record['decision'], cause=record['first_cause'], last_cause=record['last_cause'], fenced=record['fenced'])
            controller.save(record, 'ONLINE_CLEANING' if record['state'] == 'ONLINE_CLEANING' else 'ONLINE_RECOVERY_REQUIRED')
            return dict(result='ONLINE_RECOVERY_REQUIRED', operation_id=operation, decision=record['decision'],
                        cause=record['first_cause'], last_cause=record['last_cause'], automatic_retry=False)


def cleanup(controller, record):
    pending = {role: dict(fence=record['fence'], reconciliation=record['reconciliation'])
               for role in controller.nodes if role not in record['cleaned']}
    receipts = round_trip(controller, record['operation_id'], 'complete', pending)
    for role, receipt in receipts.items():
        require(receipt['result'] == 'CLEANED', 'ONLINE_CLEANUP_RECEIPT')
        record['cleaned'].append(role)
        controller.save(record, 'ONLINE_CLEANING')
    controller.save(record, 'COMMITTED')
    controller.receipts(record)
    return dict(result='COMMITTED', operation_id=record['operation_id'], plan_sha256=record['plan_sha256'],
                receipts=record['published'], delivery=record['delivery'], zero_stop=True)


def abort(controller, operation):
    with controller.operation.lock():
        record = parse(read_private(controller.root/'transaction.json'))
        require(record.get('mode') == 'online' and record['operation_id'] == operation, 'ONLINE_OPERATION_BINDING')
        require(not record['commit_decided'] and record.get('decision') in (None, 'ABORT'), 'ONLINE_DECISION_IMMUTABLE')
        if record['state'] == 'ABORTED':
            return dict(result='ABORTED', operation_id=operation, replay=True)
        record.update(decision='ABORT')
        controller.save(record, 'ONLINE_ABORT_DECIDED')
        for role in controller.nodes:
            if role in record['cleaned']:
                continue
            receipt = call(controller, role, operation, 'abort', fence=record['fence'])
            require(receipt['result'] in ('CLEANED', 'NOT_ACQUIRED'), 'ONLINE_CLEANUP_RECEIPT')
            record['cleaned'].append(role)
            controller.save(record, 'ONLINE_ABORT_CLEANING')
        controller.save(record, 'ABORTED')
        return dict(result='ABORTED', operation_id=operation, rollback=False)
