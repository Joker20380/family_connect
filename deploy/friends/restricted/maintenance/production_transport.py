import contextlib
import os
from pathlib import Path
import re
import shlex
import subprocess
import tempfile
import time

from credential_renewal import MAX_BYTES, Rejected, atomic, canonical, digest, parse, private_directory, read_private, require


ACTIONS = frozenset(('recovery-evidence','recovery-authority-request','prepare-expired','inspect','public-gateway','public-authority','public-directory','publish-directory','authority-request','prepare','acquire','quiesce','stopped','stage','promote','readback','restore',
                     'rollback','rollback-readback','rollback-registry-overlay','finalize-fenced-rollback','commit-decision','resume','fence','cleanup'))


def ssh_route(value, *, forced):
    require(type(value) is dict and set(value) == ({'key','known_hosts','target'} if forced else
            {'key','known_hosts','target','command'}), 'SSH_CONFIG')
    require(type(value['target']) is str and re.fullmatch(r'[a-z_][a-z0-9_-]{0,63}@[a-zA-Z0-9][a-zA-Z0-9.-]{0,252}',
            value['target']) and '..' not in value['target'], 'SSH_CONFIG')
    for name in ('key','known_hosts'):
        require(type(value[name]) is str, 'SSH_CONFIG')
        path = Path(value[name])
        require(path.is_absolute() and str(path) == os.path.normpath(path) and not path.is_symlink() and path.is_file(), 'SSH_CONFIG')
    if not forced:
        command = value['command']
        require(type(command) is list and len(command) == 7 and command[1:4] == ['-E','-s','-B'] and
                command[5] == '--config', 'SSH_CONFIG')
        for index in (0,4,6):
            require(type(command[index]) is str and command[index].startswith('/') and
                    command[index] == os.path.normpath(command[index]) and '\n' not in command[index] and
                    '\r' not in command[index], 'SSH_CONFIG')
    return value


def snapshot_command(route, *, executable='/usr/bin/ssh'):
    route = ssh_route(route, forced=True)
    return [executable,'-F','/dev/null','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8',
            '-o','ServerAliveInterval=5','-o','ServerAliveCountMax=2','-i',route['key'],'-o','IdentitiesOnly=yes',
            '-o','UserKnownHostsFile='+route['known_hosts'],route['target'],'restricted-sync']


class SshNode:
    def __init__(self, role, expected_source_sha256, *, executable='/usr/bin/ssh', forced=None, route=None):
        require(role in ('RU','NL') and re.fullmatch('[0-9a-f]{64}',expected_source_sha256), 'NODE_CONFIG')
        require((forced is None) != (route is None) and (forced is None or role == 'NL'), 'SSH_CONFIG')
        self.role,self.expected_source_sha256,self.executable = role,expected_source_sha256,executable
        self.forced = forced is not None
        self.route = parse(canonical(ssh_route(forced if self.forced else route, forced=self.forced)))

    def call(self, action, operation_id, payload=None):
        require(action in ACTIONS and re.fullmatch('[a-z0-9-]{16,96}',operation_id), 'RPC_SCHEMA')
        raw = canonical(dict(schema=1,role=self.role,action=action,operation_id=operation_id,
                             expected_source_sha256=self.expected_source_sha256,payload=payload))
        require(len(raw) <= MAX_BYTES, 'INPUT_TOO_LARGE')
        route = ssh_route(self.route, forced=self.forced)
        if self.forced:
            command = snapshot_command(route, executable=self.executable)
            raw = canonical(dict(schema=1,operation='CREDENTIAL_RENEWAL_RPC',request=parse(raw)))
        else:
            public = {name:value for name,value in route.items() if name != 'command'}
            command = snapshot_command(public, executable=self.executable)[:-1] + [shlex.join(route['command'])]
        with tempfile.TemporaryFile() as output, tempfile.TemporaryFile() as errors:
            def bounded():
                import resource
                resource.setrlimit(resource.RLIMIT_FSIZE,(MAX_BYTES+1,MAX_BYTES+1))
                resource.setrlimit(resource.RLIMIT_CORE,(0,0))
            try:
                result = subprocess.run(command,input=raw,stdout=output,stderr=errors,timeout=120,preexec_fn=bounded,
                                        env={'PATH':'/usr/bin:/bin','LANG':'C'})
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
    def __init__(self, role, state_directory, *, units, executable='/usr/bin/systemctl',clock=time.time):
        require(role in ('RU','NL'), 'NODE_ROLE')
        suffixes = ('.service','.timer','.service','.timer','.service') if role == 'RU' else ('.service',)
        require(type(units) in (list,tuple) and len(units) == len(suffixes) and len(set(units)) == len(units), 'UNIT_CONFIG')
        require(all(type(unit) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.@-]{0,127}',unit) and
                    unit.endswith(suffix) for unit,suffix in zip(units,suffixes)), 'UNIT_CONFIG')
        self.units = tuple(units)
        self.role,self.root,self.executable,self.clock = role,Path(state_directory),executable,clock
        private_directory(self.root)

    def state(self, unit):
        require(unit in self.units, 'UNIT_NOT_ALLOWLISTED')
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
        require(action in ('stop','start') and unit in self.units, 'SYSTEMD_ACTION_FORBIDDEN')
        try:
            result = subprocess.run([self.executable,action,unit],stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,timeout=45,check=False)
        except subprocess.TimeoutExpired:
            raise Rejected('SERVICE_OUTCOME_UNKNOWN') from None
        require(result.returncode == 0, 'SERVICE_ACTION_FAILED')

    def stopped(self):
        for unit in self.units:
            state = self.state(unit)
            if state['ActiveState'] not in ('inactive','failed') or state.get('MainPID','0') != '0':
                return False
        return True

    def quiesce(self):
        before = self.root/'services-before.json'
        if not before.exists():
            atomic(before,canonical({unit:self.state(unit) for unit in self.units}))
        for unit in self.units:
            current = self.state(unit)
            if current['ActiveState'] not in ('inactive','failed') or current.get('MainPID','0') != '0':
                self.invoke('stop',unit)
        require(self.stopped(), 'READERS_NOT_QUIESCED')

    def resume(self, *, commit_decided, equality_verified):
        require(commit_decided and equality_verified, 'RESUME_WITHOUT_COMMIT_RECONCILIATION')
        before = parse(read_private(self.root/'services-before.json'))
        require(set(before) == set(self.units), 'SERVICE_SNAPSHOT_SCHEMA')
        for index,unit in enumerate(self.units):
            if self.role == 'RU' and index not in (0,3):
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
