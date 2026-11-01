"""Durable rehearsal operations; transports are accepted only by physical hooks."""

from contextlib import contextmanager
import copy
import fcntl
from pathlib import Path
import secrets
import time

from . import acceptance
from .contracts import canonical, digest, fail, load
from .installer import atomic_json
from .permit import replay_binding, SCOPE


def local_digest(evidence):
    return digest(canonical({name:value for name,value in evidence.items() if name!='observations'}))


class RehearsalState:
    def __init__(self, directory, authorization, runtime, clock=time.time):
        self.directory = Path(directory)
        self.permit = authorization
        self.runtime = runtime
        self.clock = clock

    @contextmanager
    def lock(self):
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        if self.directory.is_symlink() or self.directory.stat().st_mode & 0o077:
            fail('rehearsal_state_directory')
        path = self.directory/'lock'
        if path.is_symlink():
            fail('rehearsal_state_link')
        with path.open('a') as descriptor:
            fcntl.flock(descriptor, fcntl.LOCK_EX)
            yield

    def status(self):
        path = self.directory/'state.json'
        if not path.exists():
            return dict(instance_id=self.permit['body']['instance_id'], state='PREFLIGHTED',
                        actual_bundle=None, previous_bundle=None, accepted=[], staged=[], health=None,
                        fenced=False, identity=None, verification=None)
        state = load(path.read_bytes())
        if state['instance_id'] != self.permit['body']['instance_id']:
            fail('private_identity_conflict')
        return state

    def execute(self, request):
        binding = replay_binding(None, self.permit, request)
        action, target = request['action'], request['bundle_id']
        if target not in (self.permit['body']['bundle_a'], self.permit['body']['bundle_b']):
            fail('rehearsal_bundle_binding')
        with self.lock():
            if action == 'status':
                return dict(state=self.status(), operations=[load(path.read_bytes()) for path in sorted(self.directory.glob('*.json'))
                            if path.name != 'state.json'])
            journal = self.directory/(request['operation_id']+'.json')
            if journal.exists():
                previous = load(journal.read_bytes())
                replay_binding(previous['binding'], self.permit, request)
                if previous['result'] == 'RUNNING':
                    fail('interrupted_operation_requires_recovery')
                return previous
            interrupted=[(path,load(path.read_bytes())) for path in self.directory.glob('*.json')
                         if path.name!='state.json' and load(path.read_bytes()).get('result')=='RUNNING']
            recovery=None
            if interrupted:
                parameters=request['parameters']
                if (len(interrupted)!=1 or action!='drain' or type(parameters) is not dict
                        or set(parameters)!={'recover_operation_id','recover_binding'}
                        or parameters['recover_operation_id']!=interrupted[0][1]['operation_id']
                        or parameters['recover_binding']!=interrupted[0][1]['binding']):
                    fail('interrupted_operation_requires_recovery')
                recovery=interrupted[0]
            state = self.status()
            if state['fenced'] or state['state'] == 'RETIRED':
                fail('rehearsal_mutations_fenced')
            started = self.clock()
            receipt = dict(schema=1, scope=SCOPE, operation_id=request['operation_id'],
                instance_id=state['instance_id'], action=action, target_bundle=target,
                previous_bundle=state['actual_bundle'], binding=binding, result='RUNNING',
                first_failure=None, rollback=None, elapsed_seconds=0, state_before=state['state'])
            atomic_json(journal, receipt)
            original = copy.deepcopy(state)
            self.switching = False
            self.rollback_target = original['actual_bundle']
            try:
                if recovery:
                    self.runtime.drain()
                    state['state']='DRAINING'
                    result=dict(recovered_operation_id=recovery[1]['operation_id'],recovery='STOPPED_NOT_RETRIED')
                else:
                    result = self.apply(state, action, target, request['parameters'], request['operation_id'])
                receipt['result'] = 'AWAITING_EXTERNAL_ACCEPTANCE' if state['state']=='AWAITING_EXTERNAL_ACCEPTANCE' else 'PASS'
                if result is not None:
                    receipt['evidence'] = result
            except Exception:
                receipt['first_failure'] = 'rehearsal_'+action.replace('-', '_')+'_failed'
                receipt['result'] = 'FAIL'
                if self.switching:
                    predecessor = self.rollback_target
                    try:
                        self.runtime.stop()
                        self.runtime.switch(predecessor)
                        if predecessor:
                            self.runtime.start(predecessor)
                            self.runtime.accept(predecessor, fresh=True)
                        state.update(original)
                        state['state'] = 'ACTIVE' if predecessor in original['accepted'] else 'VERIFIED' if original['state']=='VERIFIED' else 'FAILED'
                        state['actual_bundle'] = predecessor
                        state['verification'] = None
                        receipt['rollback'] = 'PASS'
                    except Exception:
                        state['fenced'] = True
                        state['state'] = 'QUARANTINED'
                        receipt['rollback'] = 'FAIL'
                elif action == 'retire':
                    state['fenced'] = True
                    state['state'] = 'QUARANTINED'
            receipt['state_after'] = state['state']
            receipt['actual_bundle'] = state['actual_bundle']
            receipt['elapsed_seconds'] = round(self.clock()-started, 3)
            atomic_json(self.directory/'state.json', state)
            atomic_json(journal, receipt)
            if recovery and receipt['result']=='PASS':
                recovery[1].update(result='RECOVERED',first_failure='interrupted_operation',recovered_by=request['operation_id'])
                atomic_json(recovery[0],recovery[1])
            return receipt

    def apply(self, state, action, target, parameters, operation_id):
        if type(parameters) is not dict:
            fail('rehearsal_parameters_not_supported')
        if action == 'enroll':
            if state['state']!='PREFLIGHTED':
                fail('enrollment_state')
            return self.runtime.enroll(parameters)
        if action == 'deliver-materials':
            if state['state']!='PREFLIGHTED' or set(parameters)!={'envelope'}:
                fail('material_state')
            return self.runtime.material_store().deliver(parameters['envelope'],
                permit_expires_at=self.permit['body']['expires_at'],now=self.clock())
        if action == 'complete-verification':
            if state['state']!='AWAITING_EXTERNAL_ACCEPTANCE' or state['verification']['bundle_id']!=target:
                fail('verification_state')
            if not parameters:
                return state['verification']
            if set(parameters)!={'receipt'}:
                fail('verification_parameters')
            challenge = state['verification']
            receipt_hash = acceptance.verify(parameters['receipt'],self.runtime.authority,challenge,now=self.clock(),require_pass=False)
            external = parameters['receipt']['body']
            if external['cleanup']!='PASS' or any(value!='PASS' for role in external['roles'].values() for value in role.values()):
                self.switching = True
                self.rollback_target = state['previous_bundle']
                fail('external_acceptance_failed')
            evidence = self.runtime.accept(target,fresh=True)
            if local_digest(evidence)!=challenge['local_health_sha256']:
                fail('verification_local_health_drift')
            state['health'] = dict(bundle_id=target,digest=challenge['local_health_sha256'],observed_at=int(self.clock()),
                                   external_receipt_sha256=receipt_hash,external_expires_at=parameters['receipt']['body']['expires_at'])
            state['state'] = 'VERIFIED'
            state['verification'] = None
            return dict(local_health=evidence,external_acceptance=parameters['receipt'])
        if parameters:
            fail('rehearsal_parameters_not_supported')
        if action == 'stage':
            if state['state'] not in ('PREFLIGHTED', 'STAGED', 'VERIFIED', 'ACTIVE', 'FAILED'):
                fail('stage_state')
            identity = self.runtime.enrolled_identity()
            if state['identity'] not in (None, identity):
                fail('private_identity_conflict')
            self.runtime.stage(target)
            state['identity'] = identity
            if target not in state['staged']:
                state['staged'] = [*state['staged'], target]
            if state['state'] not in ('ACTIVE','VERIFIED'):
                state['state'] = 'STAGED'
            return
        if action == 'start-verification':
            if state['state'] != 'STAGED' or target not in state['staged']:
                fail('verify_state')
            self.switching = True
            self.runtime.configure(target)
            self.runtime.stop()
            self.runtime.switch(target)
            self.runtime.start(target)
            return self.await_acceptance(state,target,operation_id)
        if action == 'activate-local':
            if (state['state'] != 'VERIFIED' or state['health'] is None or state['health']['bundle_id'] != target
                    or not 0 <= self.clock()-state['health']['observed_at'] <= 300
                    or not self.clock() < state['health']['external_expires_at']):
                fail('verified_health_required')
            if local_digest(self.runtime.accept(target, fresh=True))!=state['health']['digest']:
                fail('activation_health_drift')
            state['state'] = 'ACTIVE'
            state['actual_bundle'] = target
            state['accepted'] = sorted(set(state['accepted']) | {target})
            return
        if action in ('upgrade', 'rollback'):
            if state['state'] != 'ACTIVE' or target == state['actual_bundle'] or target not in state['staged']:
                fail('upgrade_state')
            if action == 'rollback' and target not in state['accepted']:
                fail('rollback_predecessor_not_accepted')
            self.switching = True
            self.runtime.configure(target)
            self.runtime.stop()
            self.runtime.switch(target)
            self.runtime.start(target)
            return self.await_acceptance(state,target,operation_id)
        if action == 'reboot-verify':
            if state['state'] != 'ACTIVE' or target != state['actual_bundle']:
                fail('reboot_state')
            self.runtime.reboot_check(target, state['identity'])
            return self.await_acceptance(state,target,operation_id)
        if action == 'drain':
            if state['state'] not in ('ACTIVE','AWAITING_EXTERNAL_ACCEPTANCE','VERIFIED','STAGED','FAILED'):
                fail('drain_state')
            self.runtime.drain()
            state['state'] = 'DRAINING'
            return
        if action == 'retire':
            if state['state'] != 'DRAINING':
                fail('retire_state')
            self.runtime.retire()
            state['state'] = 'RETIRED'
            return
        fail('rehearsal_action')

    def await_acceptance(self, state, target, operation_id):
        evidence = self.runtime.accept(target,fresh=True)
        started = int(self.clock())
        challenge = dict(instance_id=state['instance_id'],bundle_id=target,operation_id=operation_id,
            verification_nonce=secrets.token_hex(32),ipv4=self.permit['body']['ipv4'],
            local_health_sha256=local_digest(evidence),started_at=started,expires_at=self.permit['body']['expires_at'])
        state['previous_bundle'] = state['actual_bundle']
        state['actual_bundle'] = target
        state['verification'] = challenge
        state['state'] = 'AWAITING_EXTERNAL_ACCEPTANCE'
        return dict(challenge=challenge,local_health=evidence)
