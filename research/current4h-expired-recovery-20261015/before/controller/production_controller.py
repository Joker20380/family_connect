import base64
from pathlib import Path
import re
import time

from credential_renewal import (Rejected, atomic, canonical, digest, evaluate, parse, private_directory,
                               read_private, require)
from maintenance_policy import maintenance_gate
from production_transport import DurableOperation
from offline_handoff import verify as verify_handoff


class ProductionController:
    def __init__(self, root, nodes, validator, *, clock=time.time, fault=lambda stage:None):
        self.root,self.nodes,self.validator,self.clock,self.fault = Path(root),nodes,validator,clock,fault
        private_directory(self.root)
        require(set(nodes) == {'RU','NL'}, 'NODE_SET')
        self.operation = DurableOperation(self.root)

    def read(self, operation):
        authority = self.nodes['RU'].call('public-authority',operation)
        gateway = self.nodes['NL'].call('public-gateway',operation)
        snapshot = dict(schema=1,authority=authority['authority'],crl=authority['crl'],
                        certificate=gateway['certificate'],grants=authority['grants'])
        value = self.validator.validate(canonical(snapshot),int(self.clock()),expired_leaf_predecessor=True)
        require(authority['crl'] == gateway['revocations'] and value[1]['authority'] == gateway['authority'], 'RU_NL_MISMATCH')
        require(all(value[1][name] == gateway[name] for name in ('family','gateway','minimum_revision')), 'GATEWAY_BINDING')
        current = {role:node.call('inspect',operation) for role,node in self.nodes.items()}
        return snapshot,gateway,current,authority['pending_revocations'] > 0

    def save(self, record, state):
        record['state'] = state
        atomic(self.root/'transaction.json',canonical(record))
        self.fault(state)

    def receipts(self, record):
        safe = {key:record[key] for key in ('schema','operation_id','state','first_cause','before_sha256')}
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
                with self.operation.lock():
                    return self.recover(previous_record)
        previous,gateway,current,revocations_changed = self.read(operation)
        decision = evaluate(self.validator.validate(canonical(previous),int(self.clock()),expired_leaf_predecessor=True),
                            int(self.clock()),revocations_changed)
        if decision['result'] == 'NOOP':
            return dict(decision,files_changed=0,remote_writes=0,restarts=0)
        scheduled_scope = (scheduled and approved_leaf_crl_schedule and not revocations_changed
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
                            and not plan['grant_plan']['predecessors'], 'SCHEDULED_SCOPE_CHANGED')
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
                node.call('cleanup',operation)
        except Exception:
            self.receipts(record)
            return dict(result='CLEANUP_REQUIRED',operation_id=operation,readers='UNCHANGED')
        terminal = 'COMMITTED' if record['commit_decided'] else 'ABORTED'
        self.save(record,terminal)
        receipt_written = self.receipts(record)
        return dict(result=terminal,operation_id=operation,receipt_written=receipt_written,
                    first_cause=record['first_cause'])

    def recover(self, record):
        operation = record['operation_id']
        record['first_cause'] = record['first_cause'] or 'CONTROLLER_INTERRUPTED'
        if record['state'] == 'CLEANING':
            return self.cleanup(record)
        try:
            if record['commit_decided']:
                receipts = {role:node.call('readback',operation) for role,node in self.nodes.items()}
                require(receipts == record['reconciliation'], 'COMMITTED_READBACK_MISMATCH')
                return self.finish(record)
            self.validator.validate(canonical(record['previous']),int(self.clock()),expired_leaf_predecessor=True)
            if record['state'] != 'ROLLED_BACK':
                for role,node in self.nodes.items():
                    node.call('acquire',operation,record['before'][role])
                    node.call('fence',operation)
                require(all(node.call('stopped',operation)['stopped'] for node in self.nodes.values()), 'READERS_NOT_QUIESCED')
                for role,node in self.nodes.items():
                    node.call('rollback',operation)
            require(all(node.call('rollback-readback',operation)['result'] == 'PREVIOUS_SNAPSHOT_RESTORED'
                        for node in self.nodes.values()), 'ROLLBACK_READBACK_MISMATCH')
            self.save(record,'ROLLED_BACK')
            self.validator.validate(canonical(record['previous']),int(self.clock()))
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
