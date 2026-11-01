"""Durable rehearsal operations; transports are accepted only by physical hooks."""

from contextlib import contextmanager
import fcntl
from pathlib import Path
import time

from .contracts import canonical, digest, fail, load
from .installer import atomic_json
from .permit import replay_binding, SCOPE


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
                        fenced=False, identity=None)
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
            journal = self.directory/(request['operation_id']+'.json')
            if journal.exists():
                previous = load(journal.read_bytes())
                replay_binding(previous['binding'], self.permit, request)
                if previous['result'] == 'RUNNING':
                    fail('interrupted_operation_requires_recovery')
                return previous
            if any(load(path.read_bytes()).get('result') == 'RUNNING' for path in self.directory.glob('*.json')
                   if path.name != 'state.json'):
                fail('interrupted_operation_requires_recovery')
            state = self.status()
            if state['fenced'] or state['state'] == 'RETIRED':
                fail('rehearsal_mutations_fenced')
            started = self.clock()
            receipt = dict(schema=1, scope=SCOPE, operation_id=request['operation_id'],
                instance_id=state['instance_id'], action=action, target_bundle=target,
                previous_bundle=state['actual_bundle'], binding=binding, result='RUNNING',
                first_failure=None, rollback=None, elapsed_seconds=0, state_before=state['state'])
            atomic_json(journal, receipt)
            original = dict(state)
            try:
                self.apply(state, action, target, request['parameters'])
                receipt['result'] = 'PASS'
            except Exception:
                receipt['first_failure'] = 'rehearsal_'+action.replace('-', '_')+'_failed'
                receipt['result'] = 'FAIL'
                if action in ('verify', 'activate-local', 'upgrade', 'rollback'):
                    predecessor = original['actual_bundle']
                    try:
                        self.runtime.stop()
                        self.runtime.switch(predecessor)
                        if predecessor:
                            self.runtime.start(predecessor)
                            self.runtime.accept(predecessor, fresh=True)
                        state.update(original)
                        state['state'] = 'ACTIVE' if predecessor else 'FAILED'
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
            return receipt

    def apply(self, state, action, target, parameters):
        if type(parameters) is not dict or parameters:
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
            if state['state'] != 'ACTIVE':
                state['state'] = 'STAGED'
            return
        if action == 'verify':
            if state['state'] != 'STAGED' or target not in state['staged']:
                fail('verify_state')
            self.runtime.configure(target)
            self.runtime.switch(target)
            self.runtime.start(target)
            evidence = self.runtime.accept(target, fresh=True)
            state['health'] = dict(bundle_id=target, digest=digest(canonical(evidence)), observed_at=int(self.clock()))
            state['state'] = 'VERIFIED'
            return
        if action == 'activate-local':
            if (state['state'] != 'VERIFIED' or state['health'] is None or state['health']['bundle_id'] != target
                    or not 0 <= self.clock()-state['health']['observed_at'] <= 300):
                fail('verified_health_required')
            self.runtime.accept(target, fresh=True)
            state['state'] = 'ACTIVE'
            state['actual_bundle'] = target
            state['accepted'] = sorted(set(state['accepted']) | {target})
            return
        if action in ('upgrade', 'rollback'):
            if state['state'] != 'ACTIVE' or target == state['actual_bundle'] or target not in state['staged']:
                fail('upgrade_state')
            if action == 'rollback' and target not in state['accepted']:
                fail('rollback_predecessor_not_accepted')
            self.runtime.configure(target)
            self.runtime.stop()
            self.runtime.switch(target)
            self.runtime.start(target)
            evidence = self.runtime.accept(target, fresh=True)
            state['previous_bundle'] = state['actual_bundle']
            state['actual_bundle'] = target
            state['accepted'] = sorted(set(state['accepted']) | {target})
            state['health'] = dict(bundle_id=target, digest=digest(canonical(evidence)), observed_at=int(self.clock()))
            return
        if action == 'reboot-verify':
            if state['state'] != 'ACTIVE' or target != state['actual_bundle']:
                fail('reboot_state')
            self.runtime.reboot_check(target, state['identity'])
            self.runtime.accept(target, fresh=True)
            return
        if action == 'drain':
            if state['state'] != 'ACTIVE':
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
