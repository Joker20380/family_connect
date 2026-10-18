import contextlib
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time

from credential_renewal import MAX_BYTES, Rejected, atomic, canonical, digest, parse, private_directory, read_private, require


HOSTS = {'RU':'185.251.89.19', 'NL':'186.246.45.246'}
UNITS = {'RU':('family-connect-friends-http-candidate.service','family-connect-restricted-sync.timer',
                'family-connect-restricted-sync.service','family-connect-restricted-directory-sync.timer',
                'family-connect-restricted-directory-sync.service'),
         'NL':('family-connect-restricted-bootstrap.service',)}
NODE_COMMAND = ('/opt/apps/family_connect/friends-access/venv/bin/python -E -s -B '
                '/opt/apps/family_connect/friends-restricted/renewal/node.py '
                '--config /opt/apps/family_connect/friends-restricted/renewal/node.json')
ACTIONS = frozenset(('recovery-evidence','recovery-authority-request','prepare-expired','inspect','public-gateway','public-authority','public-directory','publish-directory','authority-request','prepare','acquire','quiesce','stopped','stage','promote','readback','restore',
                     'rollback','rollback-readback','commit-decision','resume','fence','cleanup'))


class SshNode:
    def __init__(self, role, expected_source_sha256, *, executable='/usr/bin/ssh', forced=None):
        require(role in HOSTS and re.fullmatch('[0-9a-f]{64}',expected_source_sha256), 'NODE_CONFIG')
        self.role,self.expected_source_sha256,self.executable = role,expected_source_sha256,executable
        self.forced = forced

    def call(self, action, operation_id, payload=None):
        require(action in ACTIONS and re.fullmatch('[a-z0-9-]{16,96}',operation_id), 'RPC_SCHEMA')
        raw = canonical(dict(schema=1,role=self.role,action=action,operation_id=operation_id,
                             expected_source_sha256=self.expected_source_sha256,payload=payload))
        require(len(raw) <= MAX_BYTES, 'INPUT_TOO_LARGE')
        command = [self.executable,'-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',
            '-o','ConnectTimeout=8','-o','ServerAliveInterval=5','-o','ServerAliveCountMax=2',
            'root@'+HOSTS[self.role],NODE_COMMAND]
        if self.forced is not None:
            require(self.role == 'NL' and set(self.forced) == {'key','known_hosts'}, 'SSH_CONFIG')
            for path in self.forced.values():
                require(Path(path).is_absolute() and not Path(path).is_symlink(), 'SSH_CONFIG')
            command = command[:-2] + ['-i',self.forced['key'],'-o','IdentitiesOnly=yes',
                '-o','UserKnownHostsFile='+self.forced['known_hosts'],
                'family-restricted@'+HOSTS['NL'],'restricted-sync']
            raw = canonical(dict(schema=1,operation='CREDENTIAL_RENEWAL_RPC',request=parse(raw)))
        with tempfile.TemporaryFile() as output, tempfile.TemporaryFile() as errors:
            def bounded():
                import resource
                resource.setrlimit(resource.RLIMIT_FSIZE,(MAX_BYTES+1,MAX_BYTES+1))
                resource.setrlimit(resource.RLIMIT_CORE,(0,0))
            try:
                result = subprocess.run(command,input=raw,stdout=output,stderr=errors,timeout=120,preexec_fn=bounded)
            except subprocess.TimeoutExpired:
                raise Rejected('REMOTE_OUTCOME_UNKNOWN_READBACK_REQUIRED') from None
            output.seek(0)
            try:
                value = parse(output.read(MAX_BYTES+1))
            except Rejected:
                raise Rejected('REMOTE_OUTCOME_UNKNOWN_READBACK_REQUIRED') from None
        require(set(value) == {'schema','role','operation_id','action','source_sha256','result','payload'}, 'RPC_RESPONSE_SCHEMA')
        require(value['schema'] == 1 and value['role'] == self.role and value['operation_id'] == operation_id
                and value['action'] == action and value['source_sha256'] == self.expected_source_sha256, 'RPC_RESPONSE_BINDING')
        if value['result'] == 'REJECTED':
            require(type(value['payload']) is dict and set(value['payload']) == {'cause'}, 'RPC_RESPONSE_SCHEMA')
            raise Rejected(value['payload']['cause'])
        require(result.returncode == 0 and value['result'] == 'PASS', 'REMOTE_OUTCOME_UNKNOWN_READBACK_REQUIRED')
        return value['payload']


class SystemdBarrier:
    def __init__(self, role, state_directory, *, executable='/usr/bin/systemctl',clock=time.time):
        require(role in UNITS, 'NODE_ROLE')
        self.role,self.root,self.executable,self.clock = role,Path(state_directory),executable,clock
        private_directory(self.root)

    def state(self, unit):
        require(unit in UNITS[self.role], 'UNIT_NOT_ALLOWLISTED')
        fields = ('ActiveState','SubState','MainPID','InvocationID','NRestarts','Result')
        result = subprocess.run([self.executable,'show',unit,'--property='+','.join(fields)],
            capture_output=True,timeout=10,check=False)
        require(result.returncode == 0 and len(result.stdout) < 8192, 'SYSTEMD_READ_FAILED')
        try:
            value = dict(line.split('=',1) for line in result.stdout.decode().splitlines())
        except (ValueError,UnicodeError):
            raise Rejected('SYSTEMD_READ_INVALID') from None
        require(set(value) <= set(fields) and {'ActiveState','SubState'} <= set(value), 'SYSTEMD_READ_INVALID')
        if unit.endswith('.service'):
            require('MainPID' in value and value['MainPID'].isdigit(), 'SYSTEMD_READ_INVALID')
        return value

    def invoke(self, action, unit):
        require(action in ('stop','start') and unit in UNITS[self.role], 'SYSTEMD_ACTION_FORBIDDEN')
        try:
            result = subprocess.run([self.executable,action,unit],stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,timeout=45,check=False)
        except subprocess.TimeoutExpired:
            raise Rejected('SERVICE_OUTCOME_UNKNOWN') from None
        require(result.returncode == 0, 'SERVICE_ACTION_FAILED')

    def stopped(self):
        for unit in UNITS[self.role]:
            state = self.state(unit)
            if state['ActiveState'] not in ('inactive','failed') or state.get('MainPID','0') != '0':
                return False
        return True

    def quiesce(self):
        before = self.root/'services-before.json'
        if not before.exists():
            atomic(before,canonical({unit:self.state(unit) for unit in UNITS[self.role]}))
        for unit in UNITS[self.role]:
            current = self.state(unit)
            if current['ActiveState'] not in ('inactive','failed') or current.get('MainPID','0') != '0':
                self.invoke('stop',unit)
        require(self.stopped(), 'READERS_NOT_QUIESCED')

    def resume(self, *, commit_decided, equality_verified):
        require(commit_decided and equality_verified, 'RESUME_WITHOUT_COMMIT_RECONCILIATION')
        before = parse(read_private(self.root/'services-before.json'))
        require(set(before) == set(UNITS[self.role]), 'SERVICE_SNAPSHOT_SCHEMA')
        for index,unit in enumerate(UNITS[self.role]):
            if self.role == 'RU' and unit not in (UNITS['RU'][0],UNITS['RU'][3]):
                continue
            if before[unit]['ActiveState'] not in ('active','activating') and not (
                    self.role == 'NL' and before[unit]['ActiveState'] == 'failed'):
                continue
            intent = self.root/('start-intent-'+str(index)+'.json')
            if intent.exists():
                require(self.state(unit)['ActiveState'] == 'active', 'START_ALREADY_ATTEMPTED')
                continue
            atomic(intent,canonical(dict(schema=1,unit=unit,timestamp=self.clock())))
            self.invoke('start',unit)
            require(self.state(unit)['ActiveState'] == 'active', 'READER_START_FAILED')


class DurableOperation:
    def __init__(self, root):
        self.root = Path(root)
        private_directory(self.root)

    @contextlib.contextmanager
    def lock(self):
        import fcntl
        import stat
        descriptor = os.open(self.root/'operation.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
        try:
            info = os.fstat(descriptor)
            require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_uid == os.geteuid()
                    and info.st_mode & 0o777 == 0o600, 'LOCK_PERMISSIONS')
            try:
                fcntl.flock(descriptor,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:
                raise Rejected('OPERATION_BUSY') from None
            yield
        finally:
            os.close(descriptor)

    def acquire(self, operation_id, expected_state):
        require(re.fullmatch('[a-z0-9-]{16,96}',operation_id), 'OPERATION_ID')
        path = self.root/'owner.json'
        if path.exists():
            owner = parse(read_private(path))
            require(owner['operation_id'] == operation_id and owner['expected_state'] == expected_state,
                    'OTHER_OPERATION_RECOVERY_REQUIRED')
            return owner
        owner = dict(schema=1,operation_id=operation_id,expected_state=expected_state,state='ACQUIRED',first_cause=None)
        atomic(path,canonical(owner))
        return owner

    def advance(self, owner, state, cause=None):
        actual = parse(read_private(self.root/'owner.json'))
        require(actual == owner, 'STALE_OPERATION')
        successor = dict(owner,state=state,first_cause=owner['first_cause'] or cause)
        atomic(self.root/'owner.json',canonical(successor))
        return successor
