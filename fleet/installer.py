"""Atomic release simulation inside an explicitly isolated root. Never live SSH writes."""

from contextlib import contextmanager
import fcntl
import os
from pathlib import Path
import re
import tempfile
import time

from . import health, preflight
from .bundle import verify
from .contracts import canonical, digest, fail, load, transition, typed, validate
from .enrollment import verify_receipt


def fsync_directory(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def atomic_json(path, value):
    descriptor, temporary = tempfile.mkstemp(prefix='.pending-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as output:
            output.write(canonical(value))
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
        fsync_directory(path.parent)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


class SandboxInstaller:
    def __init__(self, root, instance, bundle, public_key, enrollment=None, enrollment_key=None):
        validate('instance', instance)
        path = Path(root).absolute()
        if (path == Path('/') or not path.is_relative_to(Path(tempfile.gettempdir()).resolve())
                or any(parent.is_symlink() for parent in [path] + list(path.parents))):
            fail('isolated_temporary_root_required')
        self.root = path
        self.instance = instance
        self.bundle = Path(bundle)
        self.key = public_key
        self.enrollment = enrollment
        self.enrollment_key = enrollment_key
        self.manifest, self.contents = verify(bundle, public_key, instance['desired_bundle'])
        if self.manifest['scope'] != 'synthetic' or set(self.manifest['roles']) != set(instance['roles']):
            fail('synthetic_scope_or_roles')
        self.releases = path/'opt/family-connect/releases'
        self.current = path/'opt/family-connect/current'
        self.state_path = path/'var/lib/family-connect/instance.json'
        self.operations = path/'var/lib/family-connect/operations'
        self.configuration = path/'etc/family-connect'
        if (path/'.fleet-sandbox').exists():
            self.secure_tree()
            if load((path/'.fleet-sandbox').read_bytes()) != dict(instance_id=instance['instance_id'],logical_gateway=instance['logical_gateway']):
                fail('sandbox_instance_binding')

    def plan(self):
        return dict(scope='synthetic', instance_id=self.instance['instance_id'], bundle_id=self.manifest['bundle_id'],
                    manifest_sha256=digest(canonical(self.manifest)), roles=self.manifest['roles'], remote_writes=0)

    def initialize(self, report):
        preflight.accept(report, self.instance)
        if self.root.exists() or self.root.is_symlink():
            self.secure_tree()
        if self.root.exists() and not (self.root/'.fleet-sandbox').exists() and any(self.root.iterdir()):
            fail('sandbox_not_empty')
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        marker = self.root/'.fleet-sandbox'
        binding = dict(instance_id=self.instance['instance_id'], logical_gateway=self.instance['logical_gateway'])
        if marker.exists() and load(marker.read_bytes()) != binding:
            fail('sandbox_instance_binding')
        for directory in (self.releases, self.operations, self.configuration, self.root/'run/family-connect'):
            directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        if not marker.exists():
            atomic_json(marker, binding)
        if not self.state_path.exists():
            atomic_json(self.state_path, dict(state='DISCOVERED', actual_bundle=None, previous_bundle=None,
                accepted={}, preflight=None, health=None, instance_id=self.instance['instance_id']))

    def secure_tree(self):
        for path in [self.root] + list(self.root.rglob('*')):
            if path == self.current:
                if path.is_symlink() and re.fullmatch(r'releases/gw-[0-9a-f]{32}', os.readlink(path)):
                    continue
            if path.is_symlink() or path.is_file() and path.stat().st_nlink != 1:
                fail('sandbox_link')
            if path.exists() and path.stat().st_uid != os.getuid():
                fail('sandbox_owner')

    @contextmanager
    def locked(self):
        self.secure_tree()
        lock = self.root/'run/family-connect/deploy.lock'
        with lock.open('a') as descriptor:
            fcntl.flock(descriptor, fcntl.LOCK_EX)
            self.secure_tree()
            yield

    def status(self):
        if not self.state_path.exists():
            return dict(state='DISCOVERED', scope='synthetic')
        self.secure_tree()
        state = load(self.state_path.read_bytes())
        return dict(state=state['state'], actual_bundle=state['actual_bundle'], previous_bundle=state['previous_bundle'], scope='synthetic')

    def check_release(self, manifest):
        release = self.releases/manifest['bundle_id']
        expected = {member['path'] for member in manifest['members']}
        if {str(path.relative_to(release)) for path in release.rglob('*') if path.is_file()} != expected:
            fail('release_inventory')
        for member in manifest['members']:
            path = release/member['path']
            if (not path.is_file() or path.is_symlink() or path.stat().st_nlink != 1
                    or path.stat().st_mode & 0o777 != member['mode'] or digest(path.read_bytes()) != member['sha256']):
                fail('release_tamper')

    def stage(self):
        release = self.releases/self.manifest['bundle_id']
        if release.exists():
            self.check_release(self.manifest)
            return
        temporary = Path(tempfile.mkdtemp(prefix='.staging-', dir=self.releases))
        for member in self.manifest['members']:
            path = temporary/member['path']
            path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            with path.open('xb') as output:
                output.write(self.contents[member['path']])
                output.flush()
                os.fchmod(output.fileno(), member['mode'])
                os.fsync(output.fileno())
        for directory in sorted([temporary] + [path for path in temporary.rglob('*') if path.is_dir()], reverse=True):
            os.chmod(directory, 0o555)
            fsync_directory(directory)
        os.rename(temporary, release)
        fsync_directory(self.releases)
        self.check_release(self.manifest)

    def slots(self):
        for name in self.manifest['secret_slots']:
            path = self.configuration/(name+'.slot')
            if (not path.is_file() or path.is_symlink() or path.stat().st_mode & 0o777 != 0o600
                    or path.stat().st_uid != os.getuid() or not 1 <= path.stat().st_size <= 65536):
                fail('secret_slot_unresolved')

    def switch(self, bundle):
        temporary = self.current.with_name('.current-next')
        if temporary.exists() or temporary.is_symlink():
            fail('pending_activation_pointer')
        if bundle is None:
            if self.current.is_symlink():
                self.current.unlink()
        else:
            os.symlink('releases/'+bundle, temporary)
            os.replace(temporary, self.current)
        fsync_directory(self.current.parent)

    def execute(self, action, operation_id, *, report=None, health_report=None, dry_run=False, activation_hook=None):
        if not typed(operation_id,'id') or action not in ('preflight','stage','verify','activate','rollback','drain','quarantine'):
            fail('operation_contract')
        if dry_run:
            return dict(self.plan(), dry_run=True, action=action)
        if action == 'preflight':
            self.initialize(report)
        if not self.state_path.exists():
            fail('preflight_required')
        with self.locked():
            request = dict(action=action, instance=self.instance['instance_id'], target=self.manifest['bundle_id'],
                report_digest=digest(canonical(report)), health_digest=digest(canonical(health_report)))
            journal = self.operations/(operation_id+'.json')
            if journal.exists():
                retained = load(journal.read_bytes())
                if retained['request'] != request:
                    fail('operation_id_conflict')
                if retained['state'] == 'RUNNING':
                    fail('operation_recovery_required')
                return retained
            state = load(self.state_path.read_bytes())
            before = load(canonical(state))
            operation = dict(operation_id=operation_id, request=request, state='RUNNING', first_failure=None,
                             previous_bundle=state['actual_bundle'], scope='synthetic')
            atomic_json(journal,operation)
            try:
                target = self.manifest['bundle_id']
                if action == 'preflight':
                    if state['state'] != 'PREFLIGHTED':
                        state['state'] = transition(state['state'],'PREFLIGHTED')
                    state['preflight'] = dict(report=report, observed_at=int(time.time()))
                    state['health'] = None
                elif action == 'stage':
                    if state['state'] != 'STAGED':
                        state['state'] = transition(state['state'],'STAGED')
                    if not state['preflight'] or time.time()-state['preflight']['observed_at'] > 600:
                        fail('fresh_preflight_required')
                    self.stage()
                    state['candidate'] = target
                    state['health'] = None
                    configuration = dict(schema=1, instance_id=self.instance['instance_id'],
                        logical_gateway=self.instance['logical_gateway'], bundle_id=target, roles=self.manifest['roles'])
                    atomic_json(self.configuration/(target+'.json'),configuration)
                elif action in ('verify','activate'):
                    if not state['preflight'] or not 0 <= time.time()-state['preflight']['observed_at'] <= 600:
                        fail('fresh_preflight_required')
                    if state.get('candidate') != target:
                        fail('candidate_binding')
                    if self.instance['enrollment_state'] != 'ENROLLED' or not self.instance['deployment_identity']:
                        fail('instance_enrollment_required')
                    if self.enrollment is None or self.enrollment_key is None:
                        fail('instance_receipt_required')
                    enrolled_bundle=self.enrollment['body']['binding']['bundle_id']
                    if enrolled_bundle!=target and enrolled_bundle not in state['accepted']:
                        fail('instance_receipt_bundle')
                    binding=dict(instance_id=self.instance['instance_id'],logical_gateway=self.instance['logical_gateway'],
                        bundle_id=enrolled_bundle,provider=self.instance['provider'],region=self.instance['region'],
                        ipv4=self.instance['ipv4'],roles=self.instance['roles'])
                    if verify_receipt(self.enrollment,self.enrollment_key,binding)!=self.instance['deployment_identity']:
                        fail('instance_identity_mismatch')
                    self.check_release(self.manifest)
                    self.slots()
                    configuration = load((self.configuration/(target+'.json')).read_bytes())
                    if configuration != dict(schema=1, instance_id=self.instance['instance_id'],
                            logical_gateway=self.instance['logical_gateway'], bundle_id=target, roles=self.manifest['roles']):
                        fail('configuration_binding')
                    accepted = health.accept(health_report if action=='verify' else state['health'], self.instance['instance_id'],target,self.manifest['roles'])
                    if action == 'verify':
                        state['state'] = transition(state['state'],'VERIFIED',health_pass=True)
                        state['health'] = accepted
                    else:
                        state['state'] = transition(state['state'],'ACTIVE',health_pass=True)
                        previous = state['actual_bundle']
                        if previous:
                            self.check_release(state['accepted'][previous])
                        elif self.current.exists() or self.current.is_symlink():
                            fail('bootstrap_rollback_not_empty')
                        state['previous_bundle'] = previous
                        self.switch(target)
                        if activation_hook:
                            activation_hook()
                        state['actual_bundle'] = target
                        state['accepted'][target] = self.manifest
                elif action == 'rollback':
                    previous = state['previous_bundle']
                    if previous:
                        self.check_release(state['accepted'][previous])
                    self.switch(previous)
                    state['actual_bundle'] = previous
                    state['state'] = 'STAGED' if previous else 'DISCOVERED'
                    state['health'] = None
                    state['candidate'] = previous
                else:
                    state['state'] = transition(state['state'], 'DRAINING' if action=='drain' else 'QUARANTINED')
                atomic_json(self.state_path,state)
                operation.update(state='SUCCEEDED', result=self.status())
            except Exception as error:
                if action == 'activate':
                    self.switch(before['actual_bundle'])
                operation.update(state='FAILED', first_failure=str(error) if type(error).__name__=='FleetError' else 'operation_failed',
                                 rollback_pointer=before['actual_bundle'])
                atomic_json(journal, operation)
                raise
            atomic_json(journal,operation)
            return operation
