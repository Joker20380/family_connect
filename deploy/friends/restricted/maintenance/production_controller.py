import base64
from pathlib import Path
import re
import time

from credential_renewal import (Rejected, atomic, canonical, digest, evaluate, parse, private_directory,
                               read_private, require, utc)
from maintenance_policy import maintenance_gate
from production_transport import DurableOperation
from offline_handoff import verify as verify_handoff


class ProductionController:
    def __init__(self, root, nodes, validator, *, clock=time.time, fault=lambda stage:None):
        self.root,self.nodes,self.validator,self.clock,self.fault = Path(root),nodes,validator,clock,fault
        private_directory(self.root)
        require(set(nodes) == {'RU','NL'}, 'NODE_SET')
        self.operation = DurableOperation(self.root)

    def recovery_checkpoint(self):
        marker = self.root/'transaction.json'
        require(marker.exists() and (self.root/'plan.json').exists(), 'RECOVERY_CHECKPOINT_UNCONFIRMED')
        record = parse(read_private(marker))
        require(record['state'] == 'COMMITTED' and record['commit_decided'], 'OTHER_OPERATION_RECOVERY_REQUIRED')
        plan = parse(read_private(self.root/'plan.json'))
        plan_hash = digest(canonical(plan))
        require(plan['operation_id'] == record['operation_id']
                and all(value['plan_sha256'] == plan_hash for value in record['reconciliation'].values()),
                'RECOVERY_CHECKPOINT_UNCONFIRMED')
        return dict(operation_id=record['operation_id'], plan_sha256=plan_hash,
                    snapshot_sha256=digest(canonical(plan['candidate'])))

    def recovery_state(self, operation):
        from expired_recovery import historical
        checkpoint = self.recovery_checkpoint()
        authority = self.nodes['RU'].call('public-authority', operation)
        gateway = self.nodes['NL'].call('public-gateway', operation)
        predecessor = historical(canonical(dict(schema=1, authority=authority['authority'], crl=authority['crl'],
            certificate=gateway['certificate'], grants=authority['grants'])), self.validator.anchor,
            all_activated=self.validator.all_activated)
        require(gateway['authority'] == predecessor.trust['authority'] and gateway['revocations'] == authority['crl']
                and all(gateway[name] == predecessor.trust[name] for name in ('family', 'gateway', 'minimum_revision')),
                'RECOVERY_SCOPE')
        from expired_recovery import floors
        require(0 < gateway['minimum_crl'] <= floors(predecessor)['crl'], 'RECOVERY_FLOOR')
        current = {role: node.call('recovery-evidence', operation, checkpoint)['current']
                   for role, node in self.nodes.items()}
        self.check_admission(current)
        require(current['NL']['files']['gateway.json'] == gateway['profile_sha256'], 'RECOVERY_STALE_APPROVAL')
        return predecessor, gateway, current, checkpoint

    def recovery_request(self, operation, grant_scope):
        from expired_recovery import PURPOSE, UPDATES, floors
        require(type(operation) is str and re.fullmatch('[a-z0-9-]{16,96}', operation), 'OPERATION_ID')
        require(type(grant_scope) is list and all(type(device) is str for device in grant_scope), 'RECOVERY_GRANT_SCOPE')
        with self.operation.lock():
            requests = self.root/'recovery-requests'
            requests.mkdir(mode=0o700, exist_ok=True)
            private_directory(requests)
            path = requests/(operation+'.json')
            if path.exists():
                request = parse(read_private(path))
                require(request['grant_scope'] == sorted(grant_scope), 'RECOVERY_REPLAY_MISMATCH')
                return request
            require(len(list(requests.iterdir())) < 256, 'OPERATION_HISTORY_CAPACITY')
            predecessor, _, current, checkpoint = self.recovery_state(operation)
            now = int(self.clock())
            require(predecessor.trust['expires_at'] <= now, 'RECOVERY_NOT_REQUIRED')
            request = dict(schema=3, purpose=PURPOSE, operation_id=operation, predecessor=predecessor.snapshot,
                predecessor_sha256=digest(predecessor.encoded), scope={name:predecessor.trust[name] for name in ('family', 'gateway')},
                floors=floors(predecessor), checkpoint=checkpoint, expected=current, grant_scope=sorted(grant_scope),
                updates=UPDATES, successor_payload=None, created_at=now, expires_at=now+86400)
            request = self.nodes['RU'].call('recovery-authority-request', operation, request)
            require({role:node.call('inspect', operation) for role,node in self.nodes.items()} == current,
                    'RECOVERY_STALE_APPROVAL')
            atomic(path, canonical(request))
            return request

    def run_expired(self, operation, bundle, *, approval=None, resume=False):
        from expired_recovery import verify
        require(type(operation) is str and re.fullmatch('[a-z0-9-]{16,96}', operation), 'OPERATION_ID')
        with self.operation.lock():
            results = self.root/'recovery-results'
            results.mkdir(mode=0o700, exist_ok=True)
            private_directory(results)
            completed = results/(operation+'.json')
            binding = digest(bundle)
            if completed.exists():
                receipt = parse(read_private(completed))
                require(receipt['bundle_sha256'] == binding, 'RECOVERY_REPLAY_MISMATCH')
                return dict(result='COMMITTED', operation_id=operation, idempotent=True,
                            current={role:node.call('inspect', operation) for role,node in self.nodes.items()})
            marker = self.root/'transaction.json'
            record = parse(read_private(marker)) if marker.exists() else None
            if record and record.get('mode') == 'expired' and record['operation_id'] == operation:
                require(record['bundle_sha256'] == binding, 'RECOVERY_REPLAY_MISMATCH')
                if record['state'] == 'COMMITTED':
                    atomic(completed, canonical(dict(bundle_sha256=binding, operation_id=operation)))
                    return dict(result='COMMITTED', operation_id=operation, idempotent=True)
                require(resume, 'RECOVERY_EXPLICIT_RESUME_REQUIRED')
            else:
                require(not resume, 'RECOVERY_OPERATION_MISMATCH')
                require(record is not None and record['state'] == 'COMMITTED', 'OTHER_OPERATION_RECOVERY_REQUIRED')
                authorization = verify(bundle, self.validator, operation, int(self.clock()))
                request = authorization.request
                require(read_private(self.root/'recovery-requests'/(operation+'.json')) == canonical(request),
                        'RECOVERY_STALE_APPROVAL')
                predecessor, gateway, current, checkpoint = self.recovery_state(operation)
                require(predecessor.encoded == authorization.predecessor.encoded and current == request['expected']
                        and checkpoint == request['checkpoint'], 'RECOVERY_STALE_APPROVAL')
                gate = maintenance_gate(operation, current, int(self.clock()), approval=approval)
                require(gate['result'] == 'RENEWAL_READY', 'MAINTENANCE_APPROVAL_REQUIRED')
                record = dict(schema=1, mode='expired', operation_id=operation, state='ACQUIRING', cursor=0,
                    first_cause=None, before_sha256=digest(canonical(current)), before=current,
                    previous=predecessor.snapshot, gateway=gateway, bundle=base64.b64encode(bundle).decode(),
                    bundle_sha256=binding, commit_decided=False, gate=gate)
                self.save(record, 'ACQUIRING')
            try:
                result = self.expired_rollforward(record)
                if result['result'] == 'COMMITTED':
                    atomic(completed, canonical(dict(bundle_sha256=binding, operation_id=operation)))
                return result
            except Exception as error:
                record['first_cause'] = record['first_cause'] or (str(error) if isinstance(error, Rejected) else 'IO_OR_TRANSPORT_FAILURE')
                if record['state'] != 'CLEANING':
                    for node in self.nodes.values():
                        try:
                            node.call('fence', operation)
                        except Exception:
                            pass
                    self.save(record, 'RECOVERY_REQUIRED')
                self.receipts(record)
                return dict(result='PUBLICATION_INCOMPLETE', first_cause=record['first_cause'], automatic_restart=False)

    def expired_rollforward(self, record):
        operation = record['operation_id']
        if record['state'] == 'CLEANING':
            return self.cleanup(record)
        steps = [('RU','acquire'), ('NL','acquire'), ('RU','quiesce'), ('NL','quiesce'),
                 ('RU','prepare-expired'), ('RU','stage'), ('NL','stage'), ('RU','promote'), ('NL','promote')]
        while record['cursor'] < len(steps):
            role, action = steps[record['cursor']]
            payload = None
            if action == 'acquire':
                payload = record['before'][role]
            elif action == 'prepare-expired':
                payload = dict(gateway=record['gateway'], bundle=record['bundle'])
            elif action == 'stage':
                payload = parse(read_private(self.root/'plan.json'))
            response = self.nodes[role].call(action, operation, payload)
            if action == 'prepare-expired':
                require(response['operation_id'] == operation and response['previous'] == record['previous'], 'PLAN_BINDING')
                atomic(self.root/'plan.json', canonical(response))
            if action == 'stage':
                require(response['plan_sha256'] == digest(canonical(payload)), 'STAGE_RECEIPT_MISMATCH')
            record['cursor'] += 1
            self.save(record, 'RECOVERY_STEP_'+str(record['cursor']))
        if not record['commit_decided']:
            receipts = {role:node.call('readback', operation) for role,node in self.nodes.items()}
            require(receipts['RU'] == receipts['NL'] and receipts['RU']['plan_sha256']
                    == digest(read_private(self.root/'plan.json')), 'RU_NL_MISMATCH')
            record['reconciliation'] = receipts
            record['commit_decided'] = True
            self.save(record, 'COMMIT_DECIDED')
        return self.finish(record)

    def read(self, operation):
        authority = self.nodes['RU'].call('public-authority',operation)
        gateway = self.nodes['NL'].call('public-gateway',operation)
        snapshot = dict(schema=1,authority=authority['authority'],crl=authority['crl'],
                        certificate=gateway['certificate'],grants=authority['grants'])
        value = self.validator.validate(canonical(snapshot),int(self.clock()),expired_leaf_predecessor=True)
        require(authority['crl'] == gateway['revocations'] and value[1]['authority'] == gateway['authority'], 'RU_NL_MISMATCH')
        require(all(value[1][name] == gateway[name] for name in ('family','gateway','minimum_revision')), 'GATEWAY_BINDING')
        current = {role:node.call('inspect',operation) for role,node in self.nodes.items()}
        self.check_admission(current)
        return snapshot,gateway,current,authority['pending_revocations'] > 0

    def check_admission(self, current):
        expected = 'all_activated' if self.validator.all_activated else 'legacy'
        require(all(value.get('admission_mode', 'legacy') == expected for value in current.values()),
                'ADMISSION_MODE_MISMATCH')

    def save(self, record, state):
        record['state'] = state
        atomic(self.root/'transaction.json',canonical(record))
        self.fault(state)

    def receipts(self, record):
        safe = {key:record[key] for key in ('schema','operation_id','state','first_cause','before_sha256')}
        for key in ('terminal_result','rollback_verified','previous_material_current','readers_resumed',
                    'readers_state','terminal_reason','first_reason','registry_overlay_preserved','registry_overlay_result',
                    'registry_devices_added','registry_invites_added','historical_expected_state_unchanged'):
            if key in record:
                safe[key] = record[key]
        safe.update(timestamp=int(self.clock()),remote_alert_delivery='UNAVAILABLE',
                    grant_successor_model='MAINTENANCE_CUTOVER_NO_OVERLAP')
        try:
            atomic(self.root/'last-receipt.json',canonical(safe))
            return True
        except OSError:
            return False

    def run(self, operation, *, approval=None, inventory=None, scheduled=False, authority_handoff=None,
            approved_leaf_crl_schedule=False):
        require(type(operation) is str and re.fullmatch('[a-z0-9-]{16,96}',operation), 'OPERATION_ID')
        marker = self.root/'transaction.json'
        if marker.exists():
            previous_record = parse(read_private(marker))
            if previous_record['state'] not in ('COMMITTED','ABORTED'):
                require(previous_record.get('mode') != 'expired', 'OPERATOR_RECOVERY_REQUIRED')
                with self.operation.lock():
                    return self.recover(previous_record)
        previous,gateway,current,revocations_changed = self.read(operation)
        decision = evaluate(self.validator.validate(canonical(previous),int(self.clock()),expired_leaf_predecessor=True),
                            int(self.clock()),revocations_changed,all_activated=self.validator.all_activated)
        if authority_handoff is not None and self.validator.all_activated:
            verify_handoff(authority_handoff,self.validator,previous['authority'],operation,int(self.clock()))
            decision['due'] = sorted(set(decision['due']) | {'authority'})
            decision['result'] = 'RENEWAL_REQUIRED'
        if decision['result'] == 'NOOP':
            return dict(decision,files_changed=0,remote_writes=0,restarts=0)
        scheduled_scope = (scheduled and approved_leaf_crl_schedule and (not revocations_changed or self.validator.all_activated)
                           and bool(decision['due']) and set(decision['due']) <= {'leaf','crl'})
        if scheduled_scope:
            gate = dict(result='RENEWAL_READY',authorization='OPERATOR_APPROVED_LEAF_CRL_SCHEDULE',
                        pre_stop_sessions='UNKNOWN',zero_downtime=False)
        else:
            gate = maintenance_gate(operation,current,int(self.clock()),inventory=inventory,approval=approval,scheduled=scheduled)
        if gate['result'] != 'RENEWAL_READY':
            return gate
        if 'authority' in decision['due'] and authority_handoff is None:
            return dict(result='OFFLINE_AUTHORITY_RENEWAL_REQUIRED',mutations=0)
        if authority_handoff is not None:
            verify_handoff(authority_handoff,self.validator,previous['authority'],operation,int(self.clock()))
        with self.operation.lock():
            fresh,gateway,fresh_state,fresh_revocations_changed = self.read(operation)
            require(fresh == previous and fresh_state == current and fresh_revocations_changed == revocations_changed, 'STALE_OPERATION')
            if not scheduled_scope:
                gate = maintenance_gate(operation,current,int(self.clock()),inventory=inventory,approval=approval,scheduled=scheduled)
            require(gate['result'] == 'RENEWAL_READY', 'MAINTENANCE_REQUIRED')
            record = dict(schema=1,operation_id=operation,state='ACQUIRING',first_cause=None,
                before_sha256=digest(canonical(current)),before=current,previous=previous,
                acquired=[],quiesced=[],commit_decided=False,gate=gate)
            self.save(record,'ACQUIRING')
            try:
                for role,node in self.nodes.items():
                    node.call('acquire',operation,current[role])
                    record['acquired'].append(role)
                    self.save(record,role+'_ACQUIRED')
                for role,node in self.nodes.items():
                    node.call('quiesce',operation)
                    record['quiesced'].append(role)
                    self.save(record,role+'_QUIESCED')
                require(all(node.call('stopped',operation)['stopped'] for node in self.nodes.values()), 'READERS_NOT_QUIESCED')
                payload = dict(gateway=gateway,authority_handoff=base64.b64encode(authority_handoff).decode() if authority_handoff else None)
                plan = self.nodes['RU'].call('prepare',operation,payload)
                require(plan['operation_id'] == operation and plan['previous'] == previous, 'PLAN_BINDING')
                self.validator.transition(canonical(previous),canonical(plan['candidate']),int(self.clock()),revoke=True,
                                          expired_leaf_predecessor=True)
                if scheduled_scope:
                    require(plan['candidate']['grants'] == previous['grants']
                            and plan['candidate']['authority'] == previous['authority']
                            and (self.validator.all_activated or not plan['grant_plan']['predecessors']), 'SCHEDULED_SCOPE_CHANGED')
                atomic(self.root/'plan.json',canonical(plan))
                self.save(record,'PREPARED')
                for role,node in self.nodes.items():
                    receipt = node.call('stage',operation,plan)
                    require(receipt['plan_sha256'] == digest(canonical(plan)), 'STAGE_RECEIPT_MISMATCH')
                    self.save(record,role+'_STAGED')
                for role,node in self.nodes.items():
                    node.call('promote',operation)
                    self.save(record,role+'_PROMOTED')
                receipts = {role:node.call('readback',operation) for role,node in self.nodes.items()}
                require(receipts['RU'] == receipts['NL'] and receipts['RU']['plan_sha256'] == digest(canonical(plan)), 'RU_NL_MISMATCH')
                record['reconciliation'] = receipts
                record['commit_decided'] = True
                self.save(record,'COMMIT_DECIDED')
                return self.finish(record)
            except Exception as error:
                record['first_cause'] = record['first_cause'] or (str(error) if isinstance(error,Rejected) else 'IO_OR_TRANSPORT_FAILURE')
                self.save(record,'RECOVERY_REQUIRED')
                return self.recover(record)

    def finish(self, record):
        operation = record['operation_id']
        for role,node in self.nodes.items():
            node.call('commit-decision',operation,record['reconciliation'])
        self.save(record,'DECISION_REPLICATED')
        for role in ('NL','RU'):
            if role == 'RU':
                directory = self.nodes['NL'].call('public-directory',operation)
                published = self.nodes['RU'].call('publish-directory',operation,directory)
                require(published['sha256'] == directory['sha256'], 'DIRECTORY_RECONCILIATION_FAILED')
            self.nodes[role].call('resume',operation)
            self.save(record,role+'_RESUMED')
        self.save(record,'CLEANING')
        return self.cleanup(record)

    def cleanup(self, record):
        operation = record['operation_id']
        try:
            for node in self.nodes.values():
                result = node.call('cleanup',operation)
                if record.get('terminal_result') == 'ROLLED_BACK_READERS_STOPPED':
                    require(not record['commit_decided'] and result['result'] == 'CLEANED_FENCED_ROLLBACK',
                            'FENCED_CLEANUP_MISMATCH')
        except Exception:
            self.receipts(record)
            return dict(result='CLEANUP_REQUIRED',operation_id=operation,readers='UNCHANGED')
        terminal = 'COMMITTED' if record['commit_decided'] else 'ABORTED'
        self.save(record,terminal)
        receipt_written = self.receipts(record)
        return dict(result=record.get('terminal_result',terminal),operation_id=operation,receipt_written=receipt_written,
                    first_cause=record['first_cause'])

    def finalize_fenced_rollback(self, record, leaf, now, *, preserve_registry_overlay=False):
        require(not record['commit_decided'] and not record.get('reconciliation'), 'COMMIT_DECISION_PRESENT')
        require(leaf.not_valid_before_utc <= utc(now) and leaf.not_valid_after_utc <= utc(now), 'PREVIOUS_LEAF_NOT_EXPIRED')
        require(digest(canonical(record['before'])) == record['before_sha256'], 'ROLLBACK_READBACK_MISMATCH')
        plan = parse(read_private(self.root/'plan.json'))
        require(plan['operation_id'] == record['operation_id'] and plan['previous'] == record['previous'], 'PLAN_BINDING')
        for role,node in self.nodes.items():
            actual,expected = node.call('inspect',record['operation_id']),dict(record['before'][role])
            if role == 'RU' and preserve_registry_overlay:
                actual.pop('database_sha256')
                expected.pop('database_sha256')
            require(actual == expected, 'ROLLBACK_READBACK_MISMATCH')
            require(node.call('stopped',record['operation_id'])['stopped'], 'READERS_NOT_QUIESCED')
            if role == 'NL' or not preserve_registry_overlay:
                require(node.call('rollback-readback',record['operation_id'])['result'] == 'PREVIOUS_SNAPSHOT_RESTORED',
                        'ROLLBACK_READBACK_MISMATCH')
        binding = dict(operation_id=record['operation_id'],before_sha256=record['before_sha256'],
                       previous_sha256=digest(canonical(record['previous'])),plan_sha256=digest(canonical(plan)),
                       first_cause=record['first_cause'],commit_decided=False)
        overlay = None
        if preserve_registry_overlay:
            expected_database = record['before']['RU']['database_sha256']
            require(digest(canonical(plan['grant_plan']['before'])) == plan['grant_plan']['before_sha256'] == expected_database,
                    'ROLLBACK_EXPECTED_DATABASE_BINDING_MISMATCH')
            overlay = self.nodes['RU'].call('rollback-registry-overlay',record['operation_id'],
                dict(expected_database_sha256=expected_database,controller_operation_sha256=digest(canonical(binding))))
            require(overlay['result'] == 'APPEND_ONLY_REGISTRY_OVERLAY_PRESERVED'
                    and overlay['expected_database_sha256'] == expected_database
                    and overlay['controller_operation_sha256'] == digest(canonical(binding))
                    and all(overlay[name] is True for name in ('baseline_rows_preserved','restricted_state_exact','schema_exact','foreign_keys_valid'))
                    and overlay['current_database_sha256'] == self.nodes['RU'].call('inspect',record['operation_id'])['database_sha256']
                    and overlay['receipt_sha256'] == digest(canonical({key:value for key,value in overlay.items() if key != 'receipt_sha256'})),
                    'ROLLBACK_REGISTRY_OVERLAY_STALE')
            binding.update(historical_database_sha256=expected_database,current_database_sha256=overlay['current_database_sha256'],
                registry_overlay_receipt_sha256=overlay['receipt_sha256'],restricted_projection_sha256=overlay['restricted_projection_sha256'],
                devices_added=overlay['devices_added'],invites_added=overlay['invites_added'])
        if 'fenced_rollback' in record:
            require(record['fenced_rollback'] == binding, 'ROLLBACK_TERMINAL_BINDING_MISMATCH')
        else:
            record['fenced_rollback'] = binding
            self.save(record,'ROLLED_BACK')
        for role,node in self.nodes.items():
            payload = dict(reason='PREVIOUS_LEAF_EXPIRED',expected_state_sha256=digest(canonical(record['before'][role])),
                           controller_operation_sha256=digest(canonical(binding)))
            if role == 'RU' and overlay is not None:
                payload['registry_overlay_receipt_sha256'] = overlay['receipt_sha256']
            receipt = node.call('finalize-fenced-rollback',record['operation_id'],payload)
            require(receipt['result'] == 'ROLLED_BACK_READERS_STOPPED' and receipt['operation_id'] == record['operation_id']
                    and receipt['role'] == role and all(receipt[name] == value for name,value in payload.items())
                    and receipt['rollback_verified'] is True and receipt['readers_resumed'] is False
                    and receipt['readers_state'] == 'STOPPED', 'ROLLBACK_TERMINAL_RECEIPT_INVALID')
        record.update(terminal_result='ROLLED_BACK_READERS_STOPPED',rollback_verified=True,previous_material_current=False,
                      readers_resumed=False,readers_state='STOPPED',terminal_reason='PREVIOUS_LEAF_EXPIRED')
        record.setdefault('first_reason',record['first_cause'])
        if overlay is not None:
            record.update(registry_overlay_preserved=True,registry_overlay_result=overlay['result'],
                          registry_devices_added=overlay['devices_added'],registry_invites_added=overlay['invites_added'],
                          historical_expected_state_unchanged=True)
        self.save(record,'CLEANING')
        return self.cleanup(record)

    def recover(self, record, *, preserve_registry_overlay=False):
        require(record.get('mode') != 'expired', 'OPERATOR_RECOVERY_REQUIRED')
        operation = record['operation_id']
        record['first_cause'] = record['first_cause'] or 'CONTROLLER_INTERRUPTED'
        if record['state'] == 'CLEANING':
            return self.cleanup(record)
        if record['state'] == 'ABORTED' and record.get('terminal_result') == 'ROLLED_BACK_READERS_STOPPED':
            return self.cleanup(record)
        try:
            if record['commit_decided']:
                receipts = {role:node.call('readback',operation) for role,node in self.nodes.items()}
                require(receipts == record['reconciliation'], 'COMMITTED_READBACK_MISMATCH')
                return self.finish(record)
            now = int(self.clock())
            _,_,_,_,leaf = self.validator.validate(canonical(record['previous']),now,expired_leaf_predecessor=True)
            if preserve_registry_overlay or record.get('fenced_rollback',{}).get('registry_overlay_receipt_sha256'):
                try:
                    self.validator.validate(canonical(record['previous']),int(self.clock()))
                except Rejected as error:
                    if str(error) != 'LEAF_EXPIRED_OR_FUTURE':
                        raise
                    return self.finalize_fenced_rollback(record,leaf,int(self.clock()),preserve_registry_overlay=True)
                require(False, 'PREVIOUS_LEAF_NOT_EXPIRED')
            if record['state'] != 'ROLLED_BACK' and 'fenced_rollback' not in record:
                for role,node in self.nodes.items():
                    node.call('acquire',operation,record['before'][role])
                    node.call('fence',operation)
                require(all(node.call('stopped',operation)['stopped'] for node in self.nodes.values()), 'READERS_NOT_QUIESCED')
                for role,node in self.nodes.items():
                    node.call('rollback',operation)
            require(all(node.call('rollback-readback',operation)['result'] == 'PREVIOUS_SNAPSHOT_RESTORED'
                        for node in self.nodes.values()), 'ROLLBACK_READBACK_MISMATCH')
            self.save(record,'ROLLED_BACK')
            try:
                self.validator.validate(canonical(record['previous']),int(self.clock()))
            except Rejected as error:
                if str(error) != 'LEAF_EXPIRED_OR_FUTURE':
                    raise
                return self.finalize_fenced_rollback(record,leaf,int(self.clock()))
            require('fenced_rollback' not in record, 'FENCED_ROLLBACK_CANNOT_RESUME')
            for role in ('NL','RU'):
                if role == 'RU':
                    directory = self.nodes['NL'].call('public-directory',operation)
                    self.nodes['RU'].call('publish-directory',operation,directory)
                self.nodes[role].call('restore',operation,record['previous'])
            self.save(record,'CLEANING')
            return self.cleanup(record)
        except Exception:
            for node in self.nodes.values():
                try:
                    node.call('fence',operation)
                except Exception:
                    pass
            self.save(record,'RECOVERY_REQUIRED')
            self.receipts(record)
            return dict(result='RECOVERY_REQUIRED',first_cause=record['first_cause'],automatic_restart=False)
