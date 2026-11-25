"""Resumable support replacement; no data rewind, uncertainty clearing or forced stop."""
import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import pwd
import re
import select
import shlex
import socket
import stat
import subprocess
import sys
import time

from scripts import control_ha_legacy_support as admission
from scripts import control_ha_support_exit as exit_bridge
from scripts.control_ha_receiver_replace import put, sync

require = admission.require
UNIT = 'family-connect-support.service'
CANDIDATE = '621009b8df9baffb81e0d9069cfa52b3781e7dd7bf4e435dd89740e38cae5739'
DROPIN = 'zzzzzzzzzzzzzzzz-ha02-support-capture.conf'
SETTINGS = dict(KillMode='mixed', KillSignal='15', SendSIGKILL='no', TimeoutStopUSec='infinity')
CONFIG = ('Type', 'Restart', 'User', 'Group', 'Environment', 'EnvironmentFiles', 'WorkingDirectory',
          'PrivateTmp', 'ProtectHome', 'ProtectSystem', 'NoNewPrivileges', 'UMask', 'RootDirectory',
          'RootImage', 'DynamicUser', 'RuntimeDirectory', 'RuntimeDirectoryPreserve', 'StateDirectory',
          'ReadWritePaths', 'ReadOnlyPaths', 'RemainAfterExit', *SETTINGS)
FIELDS = (*CONFIG, 'MainPID', 'ControlPID', 'ActiveState', 'SubState', 'ControlGroup', 'FragmentPath',
          'DropInPaths', 'NeedDaemonReload', 'ExecMainCode', 'ExecMainStatus', 'NRestarts')
SOURCES = ('scripts/control_ha_support_replace.py', 'scripts/control_ha_support_exit.py',
           'scripts/control_ha_support_quiesce.py', 'scripts/control_ha_legacy_support.py',
           'scripts/control_ha_receiver_replace.py', 'scripts/control_ha_legacy_http.py',
           'provisioning/support_runtime.py', 'deploy/support-chat/support-capture-v1.json',
           'deploy/support-chat/support-capture-v2.json',
           'scripts/control_ha_support_entry.py', 'scripts/control_ha_handoff.py',
           'scripts/control_ha_support_witness.py', 'scripts/control_ha_mailbox_startup.py',
           'scripts/control_ha_mailbox_links.py', 'scripts/control_ha_mailbox_fence.py',
           'scripts/control_ha_mailbox_control.py')


def digest(path):
    return hashlib.sha256(admission.read(path, 64 * 1024 * 1024)).hexdigest()


def argv(pid):
    return [os.fsdecode(value) for value in admission.read(Path('/proc') / str(pid) / 'cmdline', 32768).split(b'\0') if value]


def properties(command, unit):
    raw = subprocess.check_output([*command, 'show', unit, '--property=' + ','.join(FIELDS)], timeout=10).decode()
    result = dict(line.split('=', 1) for line in raw.splitlines())
    result.setdefault('EnvironmentFiles', '')
    require(set(result) == set(FIELDS), 'UNIT_PROPERTIES')
    return result


class Manager:
    def __init__(self, unit=UNIT, user=False):
        self.fixture = bool(not user and re.fullmatch(r'fc-ha-support-replace-fixture-[0-9a-f]{32}\.service', unit))
        require((unit == UNIT or self.fixture) if not user else re.fullmatch(r'fc-ha-support-replace-test-[0-9a-f]{32}\.service', unit),
                'UNIT_SCOPE')
        self.unit, self.user = unit, user
        self.command = ['systemctl', *(['--user'] if user else [])]

    def state(self):
        return properties(self.command, self.unit)

    def call(self, *arguments):
        return subprocess.run([*self.command, *arguments], capture_output=True, check=True, timeout=10)


def files(state):
    return {path: digest(path) for path in [state['FragmentPath'], *shlex.split(state['DropInPaths'])]}


def environment_files(state):
    value = state['EnvironmentFiles']
    paths = re.findall(r'(\S+) \(ignore_errors=(?:yes|no)\)', value)
    require(not value or paths and ' '.join(re.findall(r'\S+ \(ignore_errors=(?:yes|no)\)', value)) == value,
            'ENVIRONMENT_FILE_SHAPE')
    return {path: digest(path) for path in paths}


def empty(state, original_group):
    require(state['MainPID'] == state['ControlPID'] == '0' and (state['ActiveState'] in ('inactive', 'failed') or
            (state['ActiveState'], state['SubState']) == ('active', 'exited')), 'SERVICE_NOT_EMPTY')
    for name in {state['ControlGroup'], original_group} - {''}:
        group = Path('/sys/fs/cgroup') / name.lstrip('/')
        if group.exists():
            require(not any(path.read_text().strip() for path in group.rglob('cgroup.procs')), 'CGROUP_NOT_EMPTY')


def ipc(path):
    with socket.socket(socket.AF_UNIX) as connection:
        connection.settimeout(2)
        connection.connect(str(path))
        connection.sendall(b'not-json\n')
        return json.loads(connection.makefile('rb').readline(16385))


@contextmanager
def effective_user(uid, gid):
    previous = os.geteuid(), os.getegid()
    if previous[0] != uid:
        require(previous[0] == 0, 'SERVICE_UID_REQUIRED')
        os.setegid(gid)
        os.seteuid(uid)
    try:
        yield
    finally:
        if os.geteuid() != previous[0]:
            os.seteuid(previous[0])
            os.setegid(previous[1])


def own(root, uid, gid):
    for path in [root, *root.rglob('*')]:
        require(not path.is_symlink(), 'STAGED_SYMLINK')
        os.chown(path, uid, gid)


def pins(directory):
    return {name: [path.stat().st_dev, path.stat().st_ino] for name in
            ('.', 'admission.lock', 'operations.lock', 'pending') for path in [directory / name]}


@contextmanager
def controller_lock(root):
    descriptor = os.open(root / 'controller.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    finally:
        os.close(descriptor)


def prepare(manager, baseline, candidate, root, participant, artifact, *, seconds=360, handoff=False):
    baseline, candidate, root, participant, artifact = map(lambda path: Path(path).absolute(),
                                                         (baseline, candidate, root, participant, artifact))
    repo = Path(__file__).resolve().parents[1]
    expected = json.loads(admission.read(repo / 'deploy/support-chat/support-capture-v1.json'))['baseline']
    admission.sources(baseline, expected)
    require(digest(candidate) == CANDIDATE, 'CANDIDATE_PIN')
    before = manager.state()
    require(before['Type'] == 'simple' and before['Restart'] == 'on-failure' and
            (before['ActiveState'], before['SubState']) == ('active', 'running') and
            before['NeedDaemonReload'] == 'no' and before['RootDirectory'] == before['RootImage'] == '' and
            before['DynamicUser'] == 'no', 'LEGACY_UNIT_STATE')
    if manager.user:
        uid, gid = os.geteuid(), os.getegid()
    else:
        require(os.geteuid() == 0 and before['User'] == 'fc-support' and before['Group'] == 'fc-support-ipc', 'SERVICE_SCOPE')
        account = pwd.getpwnam('fc-support')
        uid, gid = account.pw_uid, account.pw_gid
        if manager.fixture:
            fixture = Path('/run') / manager.unit.removesuffix('.service')
            require(baseline == fixture / 'source' and participant.parent == fixture / 'data' and
                    artifact.parent == fixture and root == fixture / 'controller', 'FIXTURE_PATH_SCOPE')
        else:
            require(baseline == Path('/opt/family-connect-support/app') and
                    participant.parent == Path('/var/lib/family-connect-support') and
                    artifact.parent == Path('/opt/family-connect-support'), 'PRODUCTION_PATH_SCOPE')
    pid = int(before['MainPID'])
    arguments = argv(pid)
    require('--store' in arguments and '--capture-gate' not in arguments and
            all(re.fullmatch(r'[A-Za-z0-9_./:@+-]+', value) for value in arguments), 'LEGACY_COMMAND')
    offset = arguments.index('--store')
    require(manager.user or manager.fixture or arguments[1:offset] == ['-m', 'provisioning.support_worker'], 'LEGACY_ENTRYPOINT')
    options = arguments[offset:]
    require(len(options) % 2 == 0 and len(set(options[::2])) == len(options[::2]), 'LEGACY_ARGUMENTS')
    options_map = dict(zip(options[::2], options[1::2]))
    require(set(options_map) <= {'--store', '--key', '--sender-public', '--snapshot', '--runtime', '--socket',
                                  '--snapshot-uid', '--subscription-feed'}, 'LEGACY_OPTIONS')
    socket_path = options_map['--socket']
    require(ipc(socket_path) == {'ok': False, 'error': 'support_unavailable'}, 'LEGACY_IPC')
    original_files, env_files = files(before), environment_files(before)
    dropin = Path(before['FragmentPath'] + '.d') / DROPIN
    require(not dropin.exists() and not dropin.is_symlink() and
            all(Path(path).name < DROPIN for path in shlex.split(before['DropInPaths'])), 'DROPIN_PRESTATE')
    for path in (root, participant, artifact, dropin.parent):
        require(not any(item.is_symlink() for item in (path, *path.parents)), 'OUTPUT_SYMLINK')
    require(not root.exists() and not participant.exists() and not artifact.exists(), 'NEW_PATHS_REQUIRED')
    root.mkdir(mode=0o700)
    participant.mkdir(mode=0o700)
    os.chown(participant, uid, gid)
    put(artifact, admission.read(candidate))
    artifact.chmod(0o644)
    for path in original_files:
        put(root / ('unit-' + hashlib.sha256(path.encode()).hexdigest()), admission.read(path))
    for name in SOURCES:
        path = root / name
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        put(path, admission.read(repo / name))
    stage_pins = {name: digest(root / name) for name in SOURCES}
    runner = ('import sys\nfrom pathlib import Path\nsys.path.insert(0,str(Path(__file__).resolve().parent))\n'
              'from scripts.control_ha_support_replace import main\nmain()\n')
    put(root / 'runner.py', runner.encode())
    stage_pins['runner.py'] = digest(root / 'runner.py')
    if handoff:
        put(root / 'handoff.py', runner.replace('scripts.control_ha_support_replace', 'scripts.control_ha_handoff').encode())
        stage_pins['handoff.py'] = digest(root / 'handoff.py')
    gate = participant / 'gate'
    initialize = ('import json,sys;sys.path.insert(0,sys.argv[1]);from control.capture_gate import initialize;'
                  'gate=initialize(sys.argv[2]);\nwith gate.operation() as operation:operation.uncertain()\n'
                  'print(json.dumps(sorted(path.name for path in (gate.directory/"pending").iterdir())))')
    initialized = subprocess.run([arguments[0], '-I', '-c', initialize, str(artifact), str(gate)],
                                 user=uid, group=gid, capture_output=True, check=True, timeout=10)
    pending = json.loads(initialized.stdout)
    require(len(pending) == 1, 'LEGACY_UNCERTAINTY_REQUIRED')
    newer = [arguments[0], '-I', '-B', str(artifact), *options, '--capture-gate', str(gate)]
    entry, start_authority = artifact.with_suffix('.entry.py'), artifact.with_suffix('.start.json')
    if handoff:
        require(not any(path.exists() or path.is_symlink() for path in (entry, start_authority)), 'NEW_PATHS_REQUIRED')
        put(entry, admission.read(root / 'scripts/control_ha_support_entry.py'))
        entry.chmod(0o644)
        newer = [arguments[0], '-I', '-B', str(entry), str(artifact), str(start_authority),
                 str(os.geteuid()), *options, '--capture-gate', str(gate)]
    require(all(re.fullmatch(r'[A-Za-z0-9_./:@+-]+', value) for value in newer), 'CANDIDATE_COMMAND')
    content = ('[Service]\nExecStart=\nExecStart=' + ' '.join(newer) +
               '\nKillMode=mixed\nKillSignal=SIGTERM\nSendSIGKILL=no\nTimeoutStopSec=infinity\n' +
               ('Restart=no\n' if handoff else '')).encode()
    put(root / 'support.conf', content)
    plan = dict(schema=1, root=str(root), participant=str(participant), unit=manager.unit, user=manager.user,
                uid=uid, gid=gid, baseline=str(baseline), baseline_pins=expected, artifact=str(artifact),
                before=before, files=original_files, env_files=env_files, old_argv=arguments, new_argv=newer,
                old_binding=admission.binding(pid), executable=str(Path(arguments[0]).resolve()),
                executable_sha256=digest(Path(arguments[0]).resolve()), sources=stage_pins, socket=socket_path,
                gate=str(gate), gate_pins=pins(gate), pending=pending, seconds=seconds, dropin=str(dropin),
                dropin_sha256=hashlib.sha256(content).hexdigest(), handoff=handoff,
                entry=str(entry) if handoff else None, start_authority=str(start_authority) if handoff else None)
    require(manager.state() == before and files(before) == original_files and environment_files(before) == env_files,
            'PRESTATE_CHANGED')
    admission.write(root / 'plan.json', plan)
    return plan


def supervisor_unit(plan, interpreter):
    require(all(re.fullmatch(r'[A-Za-z0-9_./:@+-]+', value) for value in
                (str(interpreter), plan['root'], plan['unit'])), 'SUPERVISOR_COMMAND')
    return ('[Unit]\nAfter=' + plan['unit'] + '\n[Service]\nType=simple\n'
            'Restart=on-failure\nRestartSec=1\nRestartPreventExitStatus=78\nRemainAfterExit=yes\n'
            'KillMode=process\nSendSIGKILL=no\nTimeoutStopSec=infinity\nUMask=0077\n'
            'ExecStart=' + str(interpreter) + ' -I -B ' + plan['root'] + '/runner.py --run ' + plan['root'] + '\n')


class Replacement:
    def __init__(self, root):
        self.root = Path(root).absolute()
        self.plan = json.loads(admission.read(self.root / 'plan.json'))
        require(self.plan['schema'] == 1 and self.plan['root'] == str(self.root) and
                self.root.stat().st_uid == os.geteuid() and self.root.stat().st_mode & 0o777 == 0o700, 'PRIVATE_PLAN')
        self.manager = Manager(self.plan['unit'], self.plan['user'])
        self.dropin = Path(self.plan['dropin'])
        self.participant = Path(self.plan['participant'])
        self.drain = self.participant / 'drain'

    def has(self, name):
        path = self.root / (name + '.json')
        return path.exists() or path.is_symlink()

    def record(self, name, **value):
        if not self.has(name):
            admission.write(self.root / (name + '.json'), dict(at=time.time(), **value))

    def terminal_failure(self):
        if self.has('terminal-failure'):
            return True
        path = self.drain / 'error.json'
        if not path.exists():
            return False
        raw = admission.read(path)
        error = json.loads(raw)
        require(type(error.get('irreversible')) is bool and error.get('capture_permitted') is False,
                'INVALID_EXIT_ERROR')
        if not error['irreversible']:
            return False
        reason = error.get('reason')
        require(isinstance(reason, str) and re.fullmatch(r'[A-Z][A-Z0-9_]{1,80}', reason), 'INVALID_EXIT_REASON')
        evidence = {'error.json': hashlib.sha256(raw).hexdigest()}
        for name in ('ready.json', 'commit.json', 'committed.json', 'threads-before-persistence.json',
                     'threads-after-persistence.json', 'threads-before-exit.json'):
            if (self.drain / name).exists():
                evidence[name] = digest(self.drain / name)
        self.record('terminal-failure', result='MANUAL_RECONCILIATION_REQUIRED', reason=reason,
                    evidence=evidence, irreversible=True, capture_permitted=False,
                    opening_permitted=False, witness_permitted=False)
        return True

    def old_exit_outcome(self):
        if self.terminal_failure():
            return 'MANUAL_RECONCILIATION_REQUIRED'
        return 'ABORTED' if self.has('aborted') else 'WAITING_OLD_EXIT'

    def validate(self):
        plan = self.plan
        require(all(digest(self.root / name) == value for name, value in plan['sources'].items()), 'SUPERVISOR_PIN')
        require(digest(plan['artifact']) == CANDIDATE and digest(plan['executable']) == plan['executable_sha256'], 'SOURCE_PIN')
        admission.sources(plan['baseline'], plan['baseline_pins'])
        require(all(digest(path) == value for path, value in plan['files'].items()), 'ORIGINAL_UNIT_CHANGED')
        require(all(digest(path) == value for path, value in plan['env_files'].items()), 'ENVIRONMENT_CHANGED')
        require(pins(Path(plan['gate'])) == plan['gate_pins'], 'GATE_REPLACED')
        require(all(admission.read(Path(plan['gate']) / 'pending' / name) == b'family-connect/capture-operation/v1\n'
                    for name in plan['pending']), 'LEGACY_UNCERTAINTY_LOST')
        require(digest(self.root / 'support.conf') == plan['dropin_sha256'], 'DROPIN_SOURCE_CHANGED')
        if self.dropin.exists() or self.dropin.is_symlink():
            require(digest(self.dropin) == plan['dropin_sha256'], 'DROPIN_CHANGED')
        require({str(path) for path in self.dropin.parent.glob('*.conf')} <= set(plan['files']) | {str(self.dropin)},
                'UNEXPECTED_DISK_DROPIN')
        state = self.manager.state()
        require({state['FragmentPath'], *shlex.split(state['DropInPaths'])} in
                (set(plan['files']), set(plan['files']) | {str(self.dropin)}), 'UNEXPECTED_UNIT_FILES')
        config_excluded = set(SETTINGS) | ({'Restart'} if plan.get('handoff') else set())
        require(all(state[key] == plan['before'][key] for key in CONFIG if key not in config_excluded), 'UNIT_CONFIG_CHANGED')
        if plan.get('handoff'):
            require(digest(plan['entry']) == plan['sources']['scripts/control_ha_support_entry.py'], 'ENTRY_CHANGED')
            restart = 'no' if str(self.dropin) in shlex.split(state['DropInPaths']) else plan['before']['Restart']
            require(state['Restart'] == restart, 'CANDIDATE_RESTART_POLICY')
        return state

    def admit_candidate(self):
        state = self.validate()
        pid = self.live(state, self.plan['new_argv'])
        value = dict(schema=1, binding=admission.binding(pid), archive_sha256=CANDIDATE)
        if self.has('candidate-binding-intent'):
            retained = json.loads(admission.read(self.root / 'candidate-binding-intent.json'))
            require({key: item for key, item in retained.items() if key != 'at'} == value,
                    'CANDIDATE_RESTART_REFUSED')
        else:
            self.record('candidate-binding-intent', **value)
        authority = Path(self.plan['start_authority'])
        if authority.exists() or authority.is_symlink():
            require(json.loads(admission.read(authority)) == value, 'START_AUTHORITY_CHANGED')
        else:
            admission.write(authority, value)
            authority.chmod(0o644)

    def live(self, state, expected):
        pid = int(state['MainPID'])
        require(pid > 1 and (state['ActiveState'], state['SubState']) == ('active', 'running') and
                argv(pid) == expected, 'LIVE_COMMAND_MISMATCH')
        return pid

    def old_exit(self, *, commit=True):
        if self.terminal_failure():
            return False
        if self.has('old-exited'):
            return True
        state = self.validate()
        if not self.has('drain-intent'):
            pid = self.live(state, self.plan['old_argv'])
            require(admission.binding(pid) == self.plan['old_binding'], 'OLD_RUNTIME_CHANGED')
            launcher = exit_bridge.prepare(pid, self.plan['baseline'], self.drain, seconds=self.plan['seconds'])
            own(self.drain, self.plan['uid'], self.plan['gid'])
            self.record('drain-intent', launcher=str(launcher),
                        pins={path.name: digest(path) for path in self.drain.iterdir()})
            sys.remote_exec(pid, str(launcher))
        retained = json.loads(admission.read(self.root / 'drain-intent.json'))
        require(all(digest(self.drain / name) == value for name, value in retained['pins'].items()), 'DRAIN_SOURCE_CHANGED')
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            state = self.validate()
            if state['MainPID'] == '0':
                empty(state, self.plan['before']['ControlGroup'])
                result = json.loads(admission.read(self.drain / 'exited.json'))
                self.record('old-exit-observed', complete=state['ExecMainCode'] != '0',
                            last_completed_step='exited-receipt-read',
                            manager={key: state[key] for key in ('MainPID', 'ControlPID', 'ActiveState', 'SubState',
                                     'ExecMainCode', 'ExecMainStatus', 'NRestarts')},
                            expected_restarts=self.plan['before']['NRestarts'],
                            exited_sha256=digest(self.drain / 'exited.json'), capture_permitted=False)
                require(result == dict(binding=self.plan['old_binding'], final_persistence=True, stores_closed=True,
                                       workers=0, exit_code=0, capture_permitted=False) and
                        state['ExecMainStatus'] == '0' and state['ExecMainCode'] == '1' and
                        state['NRestarts'] == self.plan['before']['NRestarts'], 'OLD_EXIT_NOT_ATTESTED')
                self.record('old-exited', state=state, legacy_uncertainty_preserved=True, capture_permitted=False)
                return True
            require(int(state['MainPID']) == self.plan['old_binding']['pid'], 'OLD_RUNTIME_CHANGED')
            try:
                descriptor = os.pidfd_open(int(state['MainPID']))
                try:
                    if select.select([descriptor], [], [], 0)[0]:
                        continue
                    observed = admission.binding(int(state['MainPID']))
                    if select.select([descriptor], [], [], 0)[0]:
                        continue
                    require(observed == self.plan['old_binding'], 'OLD_RUNTIME_CHANGED')
                finally:
                    os.close(descriptor)
            except (FileNotFoundError, ProcessLookupError):
                continue
            if (self.drain / 'error.json').exists():
                error = json.loads(admission.read(self.drain / 'error.json'))
                if error['irreversible']:
                    self.terminal_failure()
                    return False
                if (self.drain / 'restored.json').exists():
                    require(admission.binding(int(state['MainPID'])) == self.plan['old_binding'], 'OLD_RUNTIME_CHANGED')
                    self.record('aborted', reason=error['reason'], old_running=True)
                    return False
            if commit and (self.drain / 'ready.json').exists() and not (self.drain / 'commit.json').exists():
                self.record('commit-intent', capture_permitted=False)
                with effective_user(self.plan['uid'], self.plan['gid']):
                    exit_bridge.authorize(self.drain)
            time.sleep(.05)
        request = json.loads(admission.read(self.drain / 'request.json'))
        if time.monotonic() > request['deadline'] and not (self.drain / 'claimed-exit.json').exists():
            require(admission.binding(int(state['MainPID'])) == self.plan['old_binding'], 'OLD_RUNTIME_CHANGED')
            self.record('aborted', reason='UNCLAIMED_EXPIRED', old_running=True)
        return False

    def attest(self, pid):
        binding = admission.binding(pid)
        output = self.participant / ('readback-' + str(pid) + '-' + binding['start'])
        if not output.exists():
            output.mkdir(mode=0o700)
            code = ('import hashlib,json,os,runpy,sys,time,zipfile\nfrom pathlib import Path\n'
                    f'assert time.monotonic() < {time.monotonic()+5!r}\n'
                    f'bridge=runpy.run_path({str(self.drain / "admission.py")!r})\n'
                    f'assert bridge["binding"](os.getpid())=={binding!r}\n'
                    f'archive={self.plan["artifact"]!r}\n'
                    f'assert hashlib.sha256(Path(archive).read_bytes()).hexdigest()=={CANDIDATE!r}\n'
                    'from provisioning import support_worker,support_runtime,support_lifecycle\n'
                    'from control import capture_gate\n'
                    'for module in (support_worker,support_runtime,support_lifecycle,capture_gate):\n'
                    ' assert module.__file__.startswith(archive+"/")\n'
                    'frame=sys._getframe();owners=[]\n'
                    'while frame is not None:\n'
                    ' if frame.f_code is support_worker.main.__code__:owners.append(frame)\n'
                    ' frame=frame.f_back\n'
                    'assert len(owners)==1\n'
                    'values=owners[0].f_locals;gate=values["gate"];runtime=values["managed"]\n'
                    f'assert str(gate.directory)=={self.plan["gate"]!r}\n'
                    'assert values["store"].capture_gate is gate and runtime.gate is gate\n'
                    'assert capture_gate.CURRENT.get().gate is gate\n'
                    'assert not runtime.closed and not runtime.failed.is_set()\n'
                    'with gate.opened():pass\n'
                    'with zipfile.ZipFile(archive) as source:\n'
                    ' for function,name in ((support_worker.main,"provisioning/support_worker.py"),'
                    '(capture_gate.Gate.operation.__wrapped__,"control/capture_gate.py"),'
                    '(support_runtime.ManagedRuntime._close,"provisioning/support_runtime.py")):\n'
                    '  bridge["code_matches"](function,source.read(name),archive+"/"+name)\n'
                    f'bridge["write"](Path({str(output / "result.json")!r}),dict(binding={binding!r},'
                    f'uid=os.getuid(),archive_sha256={CANDIDATE!r},capture_permitted=False))\n')
            put(output / 'invoke.py', code.encode())
            own(output, self.plan['uid'], self.plan['gid'])
            self.record('readback-intent-' + str(pid), binding=binding)
            sys.remote_exec(pid, str(output / 'invoke.py'))
        require(json.loads(admission.read(output / 'result.json')) == dict(binding=binding, uid=self.plan['uid'],
                archive_sha256=CANDIDATE, capture_permitted=False), 'RUNTIME_ATTESTATION')
        return binding

    def verify(self, state):
        pid = self.live(state, self.plan['new_argv'])
        require(all(state[key] == value for key, value in SETTINGS.items()) and state['NeedDaemonReload'] == 'no',
                'PAIRED_SETTINGS')
        require(ipc(self.plan['socket']) == {'ok': False, 'error': 'support_unavailable'}, 'CANDIDATE_IPC')
        binding = self.attest(pid)
        admission.visible_to(pid, Path(self.plan['gate']))
        descriptor = os.open(Path(self.plan['gate']) / 'operations.lock', os.O_RDONLY | os.O_NOFOLLOW)
        try:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                pass
            else:
                raise ValueError('LIFETIME_GATE_NOT_HELD')
        finally:
            os.close(descriptor)
        require(admission.binding(pid) == binding, 'CANDIDATE_CHANGED')
        self.validate()
        return binding

    def rollback(self):
        with controller_lock(self.root):
            return self._rollback_locked()

    def recover_reclosed(self, readback):
        with controller_lock(self.root):
            if self.terminal_failure():
                return 'MANUAL_RECONCILIATION_REQUIRED'
            proof = readback()
            reservation = json.loads(admission.read(self.root / 'handoff-reserved.json'))
            require(self.plan.get('handoff') is True and proof.get('result') == 'CLOSED_DRAINED_INVALIDATED' and
                    proof.get('reservation_ticket_sha256') == reservation['ticket_sha256'] and
                    proof.get('plan_sha256') == digest(self.root / 'plan.json') and
                    proof.get('capture_permitted') is False and proof.get('fresh_readback') is True,
                    'MAILBOX_RECLOSURE_REQUIRED')
            self.record('handoff-reclosed', **proof)
            self.record('rollback-intent', reason='AUTHENTICATED_RECLOSURE', data_restore_allowed=False)
            self._fresh_reclosure = proof
            try:
                return self._rollback_locked(reclosure=proof)
            finally:
                del self._fresh_reclosure

    def _rollback_locked(self, reclosure=None):
        require(not self.has('handoff-reserved') or
                reclosure is not None and getattr(self, '_fresh_reclosure', None) is reclosure,
                'MAILBOX_RECLOSURE_REQUIRED')
        if self.terminal_failure():
            return 'MANUAL_RECONCILIATION_REQUIRED'
        state = self.validate()
        if not self.dropin.exists() and state['MainPID'] != '0' and argv(int(state['MainPID'])) == self.plan['old_argv']:
            require(all(state[key] == self.plan['before'][key] for key in CONFIG), 'ORIGINAL_SETTINGS_NOT_RESTORED')
            require(ipc(self.plan['socket']) == {'ok': False, 'error': 'support_unavailable'}, 'ROLLBACK_IPC')
            if not self.has('drain-intent') or self.has('aborted') or self.has('old-exited'):
                self.record('rolled-back', data_restored=False, legacy_uncertainty_preserved=True)
                return 'ROLLED_BACK'
        if not self.has('old-exited'):
            if self.has('drain-intent') and not self.has('aborted'):
                if not self.old_exit(commit=False):
                    return self.old_exit_outcome()
            else:
                self.live(state, self.plan['old_argv'])
                self.record('rolled-back', old_unchanged=True, data_restored=False)
                return 'ROLLED_BACK'
        state = self.validate()
        if state['MainPID'] != '0':
            require(argv(int(state['MainPID'])) == self.plan['new_argv'] and
                    state['ActiveState'] in ('active', 'deactivating'), 'ROLLBACK_COMMAND_MISMATCH')
            require(all(state[key] == value for key, value in SETTINGS.items()), 'ROLLBACK_KILL_POLICY')
            self.record('candidate-stop-intent', data_restore_allowed=False)
            if state['ActiveState'] != 'deactivating':
                self.manager.call('stop', '--no-block', self.manager.unit)
            deadline = time.monotonic() + 3
            while self.manager.state()['MainPID'] != '0' and time.monotonic() < deadline:
                time.sleep(.05)
            state = self.validate()
            if state['MainPID'] != '0':
                return 'WAITING_CANDIDATE_DRAIN'
        if state['ActiveState'] == 'activating' and state['SubState'] == 'auto-restart':
            require(all(state[key] == value for key, value in SETTINGS.items()), 'ROLLBACK_KILL_POLICY')
            self.manager.call('stop', self.manager.unit)
            state = self.validate()
        empty(state, self.plan['before']['ControlGroup'])
        if self.dropin.exists():
            self.dropin.unlink()
            sync(self.dropin.parent)
        self.record('rollback-dropin-removed', data_restored=False)
        self.manager.call('daemon-reload')
        state = self.validate()
        require(all(state[key] == self.plan['before'][key] for key in CONFIG), 'ORIGINAL_SETTINGS_NOT_RESTORED')
        self.manager.call('stop', self.manager.unit)
        self.manager.call('start', self.manager.unit)
        deadline = time.monotonic() + 5
        while True:
            try:
                state = self.validate()
                self.live(state, self.plan['old_argv'])
                require(ipc(self.plan['socket']) == {'ok': False, 'error': 'support_unavailable'}, 'ROLLBACK_IPC')
                break
            except (OSError, ValueError):
                if time.monotonic() >= deadline:
                    raise
                time.sleep(.05)
        self.record('rolled-back', data_restored=False, state=state, legacy_uncertainty_preserved=True)
        return 'ROLLED_BACK'

    def run(self, recover=False):
        with controller_lock(self.root):
            require(not self.has('handoff-reserved') or not (recover or self.has('rollback-intent')),
                    'MAILBOX_RECLOSURE_REQUIRED')
            if self.terminal_failure():
                return 'MANUAL_RECONCILIATION_REQUIRED'
            state = self.validate()
            if recover:
                self.record('rollback-intent', reason='EXPLICIT_RECOVERY', data_restore_allowed=False)
            if self.has('rolled-back'):
                self.live(state, self.plan['old_argv'])
                return 'ROLLED_BACK'
            if self.has('rollback-intent'):
                return self._rollback_locked()
            if self.has('aborted'):
                return 'ABORTED'
            if self.has('accepted'):
                self.verify(state)
                return 'ALREADY_ACCEPTED'
            if not self.old_exit():
                return self.old_exit_outcome()
            try:
                state = self.validate()
                if not self.dropin.exists():
                    empty(state, self.plan['before']['ControlGroup'])
                    self.manager.call('stop', self.manager.unit)
                    self.dropin.parent.mkdir(mode=0o755, exist_ok=True)
                    self.record('install-intent', dropin_sha256=self.plan['dropin_sha256'])
                    put(self.dropin, admission.read(self.root / 'support.conf'))
                    self.dropin.chmod(0o644)
                self.manager.call('daemon-reload')
                state = self.validate()
                require(all(state[key] == value for key, value in SETTINGS.items()), 'PAIRED_SETTINGS')
                if state['MainPID'] == '0' and not self.has('candidate-start-intent'):
                    empty(state, self.plan['before']['ControlGroup'])
                    self.record('candidate-start-intent')
                    self.manager.call('start', self.manager.unit)
                if self.plan.get('handoff'):
                    self.admit_candidate()
                deadline = time.monotonic() + 5
                while True:
                    try:
                        bound = self.verify(self.validate())
                        break
                    except (OSError, ValueError):
                        if time.monotonic() >= deadline:
                            raise
                        time.sleep(.05)
                self.record('accepted', binding=bound, archive_sha256=CANDIDATE,
                            data_restored=False, legacy_uncertainty_preserved=True, capture_permitted=False)
                return 'ACCEPTED'
            except Exception as error:
                self.record('rollback-intent', reason=type(error).__name__, data_restore_allowed=False)
                return self._rollback_locked()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True, type=Path)
    parser.add_argument('--recover', action='store_true')
    args = parser.parse_args()
    try:
        replacement = Replacement(args.run)
        result = replacement.run(recover=args.recover)
        if result == 'MANUAL_RECONCILIATION_REQUIRED':
            print(admission.read(replacement.root / 'terminal-failure.json').decode())
            raise SystemExit(78)
    except Exception as error:
        print(json.dumps(dict(result='MANUAL_RECONCILIATION_REQUIRED', reason=type(error).__name__,
                              code=str(error) if re.fullmatch(r'[A-Z][A-Z0-9_]{1,80}', str(error)) else None,
                              capture_permitted=False)))
        raise SystemExit(78) from None
    print(json.dumps(dict(result=result, capture_permitted=False)))
    if result.startswith('WAITING_'):
        raise SystemExit(75)


if __name__ == '__main__':
    main()
