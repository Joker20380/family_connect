"""Resumable paired legacy HTTP replacement; never restores data or force-stops writers."""
import argparse
import fcntl
import hashlib
import http.client
import json
import os
from pathlib import Path
import re
import select
import shlex
import signal
import subprocess
import sys
import tempfile
import time

try:
    from scripts import control_ha_legacy_http as bridge
except ModuleNotFoundError:
    import control_ha_legacy_http as bridge

require = bridge.require
CANDIDATE = '58c5fde9b91a8997a2ebe2c881c43d8032eb82899d1d3c510390dd61efdab627'
UNIT = 'family-connect-friends-http-candidate.service'
DROPIN = 'zzzzzzzzzzzzzzzz-ha02-receiver-capture.conf'
SETTINGS = dict(KillMode='mixed', KillSignal='15', SendSIGKILL='no', TimeoutStopUSec='infinity')
CONFIG = ('Type', 'Restart', 'User', 'Group', 'Environment', 'EnvironmentFiles',
          'KillMode', 'KillSignal', 'SendSIGKILL', 'TimeoutStopUSec')
FIELDS = (*CONFIG, 'MainPID', 'ActiveState', 'SubState', 'ControlGroup', 'FragmentPath',
          'DropInPaths', 'NeedDaemonReload', 'ExecMainCode', 'ExecMainStatus', 'NRestarts')


def digest(path):
    return hashlib.sha256(bridge.read(path)).hexdigest()


def put(path, raw):
    path = Path(path)
    descriptor, temporary = tempfile.mkstemp(prefix='.replacement-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as output:
            output.write(raw)
            output.flush()
            os.fsync(output.fileno())
        os.link(temporary, path)
    finally:
        os.unlink(temporary)
    sync(path.parent)


def sync(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


class Manager:
    def __init__(self, unit, user=False):
        require(unit == UNIT if not user else re.fullmatch(r'fc-ha-replace-test-[0-9a-f]{32}\.service', unit),
                'UNIT_SCOPE')
        self.unit, self.user = unit, user
        self.command = ['systemctl', *(['--user'] if user else [])]

    def call(self, *arguments):
        return subprocess.run([*self.command, *arguments], capture_output=True, check=True, timeout=10)

    def state(self):
        raw = self.call('show', self.unit, '--all', '--property=' + ','.join(FIELDS)).stdout.decode()
        result = dict(line.split('=', 1) for line in raw.splitlines())
        result.setdefault('EnvironmentFiles', '')
        require(set(result) == set(FIELDS), 'UNIT_PROPERTIES')
        return result


def files(state):
    paths = [state['FragmentPath'], *shlex.split(state['DropInPaths'])]
    require(all(Path(path).is_absolute() for path in paths), 'UNIT_PATHS')
    return {path: digest(path) for path in paths}


def argv(pid):
    return [os.fsdecode(value) for value in bridge.read(Path('/proc') / str(pid) / 'cmdline', 32768).split(b'\0') if value]


def empty(state, original_group):
    require(state['MainPID'] == '0' and state['ActiveState'] in ('inactive', 'failed'), 'SERVICE_NOT_STOPPED')
    for name in {state['ControlGroup'], original_group} - {''}:
        group = Path('/sys/fs/cgroup') / name.lstrip('/')
        if group.exists():
            require(not any(path.read_text().strip() for path in group.rglob('cgroup.procs')), 'CGROUP_NOT_EMPTY')


def request(port):
    connection = http.client.HTTPConnection('127.0.0.1', port, timeout=2)
    try:
        connection.request('POST', '/friends/challenge', '{}', {'Content-Type': 'text/plain'})
        response = connection.getresponse()
        return response.status, json.loads(response.read(1024))
    finally:
        connection.close()


def prepare(manager, baseline, candidate, output):
    baseline, candidate, output = Path(baseline).absolute(), Path(candidate).absolute(), Path(output).absolute()
    require(digest(baseline) == bridge.BASELINE and digest(candidate) == CANDIDATE, 'ARCHIVE_PINS')
    before = manager.state()
    require(before['ActiveState'] == 'active' and before['SubState'] == 'running' and before['Type'] == 'simple'
            and before['Restart'] == 'no' and before['NeedDaemonReload'] == 'no'
            and before['EnvironmentFiles'] == '', 'LEGACY_UNIT_STATE')
    pid = int(before['MainPID'])
    arguments = argv(pid)
    require(arguments.count(str(baseline)) == 1 and '--capture-gate' not in arguments and
            all(re.fullmatch(r'[a-zA-Z0-9_./:-]+', part) for part in arguments), 'LEGACY_COMMAND')
    require(arguments.count('--port') == 1, 'PORT_REQUIRED')
    port = int(arguments[arguments.index('--port') + 1])
    require(0 < port < 65536 and (manager.user or port == 18086), 'PORT_SCOPE')
    require(request(port) == (400, {'error': 'invalid-request'}), 'LEGACY_HTTP_NOT_READY')
    original_files = files(before)
    target = Path(before['FragmentPath'] + '.d') / DROPIN
    require(not target.exists() and not target.is_symlink() and
            all(Path(path).name < DROPIN for path in shlex.split(before['DropInPaths'])), 'DROPIN_PRESTATE')
    require(not any(path.is_symlink() for path in (output, *output.parents, target.parent)), 'OUTPUT_SYMLINK')
    output.mkdir(mode=0o700)
    for path in original_files:
        put(output / ('unit-' + hashlib.sha256(path.encode()).hexdigest()), bridge.read(path))
    put(output / 'friends-http.pyz', bridge.read(candidate))
    put(output / 'control_ha_legacy_http.py', bridge.read(Path(bridge.__file__).absolute()))
    put(output / 'controller.py', bridge.read(Path(__file__).absolute()))
    gate = output / 'gate'
    initialize = ('import json,sys;sys.path.insert(0,sys.argv[1]);from control.capture_gate import initialize;'
                  'gate=initialize(sys.argv[2]);\nwith gate.operation() as operation:operation.uncertain()\n'
                  'print(json.dumps({"pending":sorted(path.name for path in (gate.directory/"pending").iterdir())}))')
    initialized = subprocess.run([arguments[0], '-I', '-c', initialize, str(output / 'friends-http.pyz'), str(gate)],
                                 capture_output=True, check=True, timeout=10)
    pending = json.loads(initialized.stdout)['pending']
    require(len(pending) == 1, 'LEGACY_UNCERTAINTY_REQUIRED')
    newer = [str(output / 'friends-http.pyz') if part == str(baseline) else part for part in arguments]
    newer += ['--capture-gate', str(gate)]
    content = ('[Service]\nExecStart=\nExecStart=' + ' '.join(newer) + '\nKillMode=mixed\n'
               'KillSignal=SIGTERM\nSendSIGKILL=no\nTimeoutStopSec=infinity\n').encode()
    put(output / 'receiver.conf', content)
    plan = dict(schema=1, unit=manager.unit, user=manager.user, root=str(output), baseline=str(baseline),
                candidate=str(output / 'friends-http.pyz'), gate=str(gate), pending=pending, port=port,
                before=before, files=original_files, old_binding=bridge.binding(pid), old_argv=arguments,
                new_argv=newer, dropin=str(target), dropin_sha256=hashlib.sha256(content).hexdigest(),
                bridge_sha256=digest(output / 'control_ha_legacy_http.py'), controller_sha256=digest(output / 'controller.py'))
    require(manager.state() == before and files(before) == original_files, 'PRESTATE_CHANGED')
    bridge.write(output / 'plan.json', plan)
    return plan


class Replacement:
    def __init__(self, root):
        self.root = Path(root).absolute()
        self.plan = json.loads(bridge.read(self.root / 'plan.json'))
        require(self.plan['schema'] == 1 and self.plan['root'] == str(self.root) and
                self.root.stat().st_uid == os.geteuid() and self.root.stat().st_mode & 0o777 == 0o700, 'PRIVATE_PLAN')
        self.manager = Manager(self.plan['unit'], self.plan['user'])
        self.dropin = Path(self.plan['dropin'])

    def has(self, name):
        return (self.root / (name + '.json')).exists()

    def record(self, name, **value):
        if not self.has(name):
            bridge.write(self.root / (name + '.json'), dict(at=time.time(), **value))

    def validate(self):
        require(digest(self.plan['baseline']) == bridge.BASELINE and digest(self.plan['candidate']) == CANDIDATE,
                'ARCHIVE_PINS')
        require(digest(self.root / 'receiver.conf') == self.plan['dropin_sha256'] and
                digest(self.root / 'control_ha_legacy_http.py') == self.plan['bridge_sha256'] and
                digest(self.root / 'controller.py') == self.plan['controller_sha256'], 'SOURCE_PINS')
        require(all(digest(path) == expected for path, expected in self.plan['files'].items()), 'PRESTATE_FILES_CHANGED')
        for name in self.plan['pending']:
            require(bridge.read(Path(self.plan['gate']) / 'pending' / name) == b'family-connect/capture-operation/v1\n',
                    'LEGACY_UNCERTAINTY_LOST')
        state = self.manager.state()
        if self.dropin.exists():
            require(digest(self.dropin) == self.plan['dropin_sha256'], 'DROPIN_CHANGED')
        disk_dropins = {str(path) for path in self.dropin.parent.glob('*.conf')}
        require(disk_dropins <= set(self.plan['files']) | {str(self.dropin)}, 'UNEXPECTED_DISK_DROPIN')
        observed = {state['FragmentPath'], *shlex.split(state['DropInPaths'])}
        require(observed in (set(self.plan['files']), set(self.plan['files']) | {str(self.dropin)}),
                'UNEXPECTED_UNIT_FILES')
        return state

    def live(self, state, expected):
        pid = int(state['MainPID'])
        require(pid > 1 and state['ActiveState'] == 'active' and state['SubState'] == 'running' and
                argv(pid) == expected, 'LIVE_COMMAND_MISMATCH')
        return pid

    def old_exit(self, state):
        if self.has('old-exited'):
            return True
        if not self.has('drain-intent'):
            pid = self.live(state, self.plan['old_argv'])
            require(bridge.binding(pid) == self.plan['old_binding'], 'OLD_RUNTIME_CHANGED')
            launcher = bridge.prepare(pid, self.plan['baseline'], self.root / 'drain', mode='stop', seconds=5)
            self.record('drain-intent', launcher=str(launcher))
            sys.remote_exec(pid, str(launcher))
        deadline = time.monotonic() + 7
        while time.monotonic() < deadline:
            state = self.manager.state()
            if state['MainPID'] == '0':
                if state['ActiveState'] not in ('inactive', 'failed'):
                    time.sleep(.05)
                    continue
                empty(state, self.plan['before']['ControlGroup'])
                result = json.loads(bridge.read(self.root / 'drain/result.json'))
                quiescent = json.loads(bridge.read(self.root / 'drain/quiescent.json'))
                require(result['result'] == 'RETURN_TO_EXIT' and quiescent['handlers'] == quiescent['children'] ==
                        quiescent['retention'] == 0 and state['ExecMainStatus'] == '0', 'OLD_EXIT_NOT_ATTESTED')
                self.record('old-exited', external_settlement_proven=False, state=state)
                return True
            require(int(state['MainPID']) == self.plan['old_binding']['pid'], 'OLD_RUNTIME_CHANGED')
            try:
                descriptor = os.pidfd_open(int(state['MainPID']))
                try:
                    if select.select([descriptor], [], [], 0)[0]:
                        continue
                    observed = bridge.binding(int(state['MainPID']))
                    if select.select([descriptor], [], [], 0)[0]:
                        continue
                    if observed['command'] == hashlib.sha256(b'').hexdigest():
                        require(all(observed[key] == self.plan['old_binding'][key]
                                    for key in ('pid', 'start', 'boot', 'cgroup')), 'OLD_RUNTIME_CHANGED')
                        continue
                    require(observed == self.plan['old_binding'], 'OLD_RUNTIME_CHANGED')
                finally:
                    os.close(descriptor)
            except (FileNotFoundError, ProcessLookupError):
                continue
            if (self.root / 'drain/error.json').exists():
                error = json.loads(bridge.read(self.root / 'drain/error.json'))
                if not error['irreversible']:
                    self.record('aborted', reason=error['reason'], old_running=True)
                    return False
            time.sleep(.05)
        if not (self.root / 'drain/claimed.json').exists():
            request = json.loads(bridge.read(self.root / 'drain/request.json'))
            if request['deadline'] < time.monotonic():
                self.record('aborted', reason='UNCLAIMED_EXPIRED_SUBMISSION', old_running=True)
                return False
        self.record('waiting-old-exit', forced_stop_allowed=False)
        return False

    def verify(self, state):
        pid = self.live(state, self.plan['new_argv'])
        require(all(state[key] == value for key, value in SETTINGS.items()) and state['Restart'] == 'no',
                'PAIRED_SETTINGS')
        require(request(self.plan['port']) == (400, {'error': 'invalid-request'}), 'HTTP_PREFLIGHT')
        descriptor = os.open(Path(self.plan['gate']) / 'admission.lock', os.O_RDONLY | os.O_NOFOLLOW)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            require(request(self.plan['port']) == (503, {'error': 'capture-busy'}), 'GATE_NOT_EFFECTIVE')
        finally:
            os.close(descriptor)
        require(request(self.plan['port']) == (400, {'error': 'invalid-request'}), 'HTTP_RESTORE')
        self.validate()
        return bridge.binding(pid)

    def rollback(self):
        state = self.validate()
        if self.has('drain-intent') and not self.has('old-exited') and not self.has('aborted'):
            if not self.old_exit(state) and not self.has('aborted'):
                return 'WAITING_OLD_EXIT'
            state = self.validate()
        if state['MainPID'] != '0':
            if not self.dropin.exists():
                self.live(state, self.plan['old_argv'])
                self.record('rolled-back', data_restored=False, state=state)
                return 'ROLLED_BACK'
            pid = int(state['MainPID'])
            require(pid > 1 and state['ActiveState'] in ('active', 'deactivating') and
                    argv(pid) == self.plan['new_argv'], 'ROLLBACK_COMMAND')
            require(all(state[key] == value for key, value in SETTINGS.items()), 'ROLLBACK_KILL_POLICY')
            descriptor = os.pidfd_open(pid)
            try:
                require(argv(pid) == self.plan['new_argv'], 'ROLLBACK_PID_CHANGED')
                signal.pidfd_send_signal(descriptor, signal.SIGTERM)
                if not select.select([descriptor], [], [], 10)[0]:
                    return 'WAITING_CANDIDATE_DRAIN'
            finally:
                os.close(descriptor)
        deadline = time.monotonic() + 3
        while self.manager.state()['MainPID'] != '0' and time.monotonic() < deadline:
            time.sleep(.05)
        state = self.validate()
        empty(state, self.plan['before']['ControlGroup'])
        if self.dropin.exists():
            self.dropin.unlink()
            sync(self.dropin.parent)
        self.record('rollback-dropin-removed', data_restored=False)
        self.manager.call('daemon-reload')
        restored = self.manager.state()
        require(all(restored[key] == self.plan['before'][key] for key in CONFIG), 'ORIGINAL_SETTINGS_NOT_RESTORED')
        self.manager.call('start', self.manager.unit)
        deadline = time.monotonic() + 5
        while True:
            try:
                restored = self.manager.state()
                self.live(restored, self.plan['old_argv'])
                require(request(self.plan['port']) == (400, {'error': 'invalid-request'}), 'ROLLBACK_HTTP')
                break
            except (OSError, ValueError, http.client.HTTPException):
                if time.monotonic() >= deadline:
                    raise
                time.sleep(.1)
        self.record('rolled-back', data_restored=False, state=restored)
        return 'ROLLED_BACK'

    def run(self, recover=False):
        descriptor = os.open(self.root / 'controller.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            state = self.validate()
            if recover:
                self.record('rollback-intent', reason='EXPLICIT_RECOVERY', data_restore_allowed=False)
            if self.has('aborted'):
                return 'ABORTED'
            if self.has('rollback-intent'):
                return self.rollback()
            if self.has('accepted'):
                self.verify(state)
                return 'ALREADY_ACCEPTED'
            if not self.old_exit(state):
                return 'ABORTED' if self.has('aborted') else 'WAITING_OLD_EXIT'
            try:
                state = self.validate()
                if not self.dropin.exists():
                    empty(state, self.plan['before']['ControlGroup'])
                    self.dropin.parent.mkdir(mode=0o755, exist_ok=True)
                    self.record('install-intent', dropin_sha256=self.plan['dropin_sha256'])
                    put(self.dropin, bridge.read(self.root / 'receiver.conf'))
                self.manager.call('daemon-reload')
                state = self.validate()
                if state['MainPID'] == '0':
                    empty(state, self.plan['before']['ControlGroup'])
                    require(all(state[key] == value for key, value in SETTINGS.items()), 'PAIRED_SETTINGS')
                    self.record('candidate-start-intent')
                    self.manager.call('start', self.manager.unit)
                deadline = time.monotonic() + 5
                while True:
                    try:
                        bound = self.verify(self.validate())
                        break
                    except (OSError, ValueError, http.client.HTTPException):
                        if time.monotonic() >= deadline:
                            raise
                        time.sleep(.1)
                self.record('accepted', binding=bound, archive_sha256=CANDIDATE, old_archive_retained=True,
                            data_restored=False, legacy_uncertainty_preserved=True, capture_permitted=False)
                return 'ACCEPTED'
            except Exception as error:
                self.record('rollback-intent', reason=type(error).__name__, data_restore_allowed=False)
                return self.rollback()
        finally:
            os.close(descriptor)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--recover', action='store_true')
    args = parser.parse_args()
    try:
        result = Replacement(args.run).run(recover=args.recover)
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
