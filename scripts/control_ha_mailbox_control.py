"""Root SSH endpoint for this HA-02 mailbox generation; no network listener."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import shlex
import subprocess
import sys
import time

from scripts import control_ha_legacy_support as admission
from scripts.control_ha_mailbox_startup import encoded, fixture_scope, owned, unique


def sha(path):
    return hashlib.sha256(admission.read(path, 64 * 1024 * 1024)).hexdigest()


def wake_control(process, directory, uid):
    path = Path(directory) / (str(process['pid']) + '-' + process['start'] + '.json')
    try:
        ready = json.loads(owned(path, uid), object_pairs_hook=unique)
    except FileNotFoundError:
        raise ValueError('MAILBOX_WAKEUP_NOT_READY') from None
    admission.require(ready == dict(schema=1, process=process, signal=int(signal.SIGUSR1)), 'MAILBOX_WAKEUP_BINDING')
    status = admission.read(Path('/proc') / str(process['pid']) / 'status').decode()
    caught = next(line.split()[1] for line in status.splitlines() if line.startswith('SigCgt:'))
    admission.require(int(caught, 16) & (1 << (signal.SIGUSR1 - 1)), 'MAILBOX_WAKEUP_NOT_CAUGHT')
    descriptor = os.pidfd_open(process['pid'])
    try:
        admission.require(admission.binding(process['pid']) == process, 'MAILBOX_WAKEUP_PROCESS_CHANGED')
        signal.pidfd_send_signal(descriptor, signal.SIGUSR1)
    finally:
        os.close(descriptor)


class MailboxControl:
    actions = ('observe', 'consume', 'reclose')

    def invocation(self, action, request):
        return 'startup.observe()' if action == 'observe' else f'startup.{action}({str(request)!r})'

    def fixture_plan(self, path):
        return (fixture_scope(self.plan['manifest'], self.plan['unit']) and
                Path(path).absolute() == Path(self.plan['manifest']).with_name('control.json'))

    def __init__(self, plan):
        self.owner = os.geteuid()
        self.plan = json.loads(owned(plan, self.owner), object_pairs_hook=unique)
        expected = {'schema', 'unit', 'user', 'manifest', 'argv', 'restart_argv', 'files', 'sources', 'interpreter',
                    'interpreter_sha256', 'runtime', 'uid', 'gid'}
        admission.require(set(self.plan) >= expected and set(self.plan) <= expected | {'response_directory', 'wakeup_directory'} and
                          self.plan['schema'] == 1, 'MAILBOX_CONTROL_PLAN')
        unit = self.plan['unit']
        fixture = self.fixture_plan(plan)
        admission.require((self.plan['user'] is True and self.owner != 0 and
                           re.fullmatch('fc-ha-mailbox-handoff-test-[0-9a-f]{32}\\.service', unit)) or
                          (self.plan['user'] is False and self.owner == 0 and
                           (unit == 'family-connect-mailbox.service' or fixture)), 'MAILBOX_CONTROL_SCOPE')
        self.command = ['systemctl', *(['--user'] if self.plan['user'] else [])]
        self.runtime = Path(self.plan['runtime'])

    def validate(self):
        admission.require(sys.version_info[:2] == (3, 14) and sys._is_gil_enabled(), 'CPYTHON_314_GIL_REQUIRED')
        for path, digest in {**self.plan['sources'], **self.plan['files']}.items():
            admission.require(sha(path) == digest, 'MAILBOX_CONTROL_SOURCE_CHANGED')
        admission.require(sha(self.plan['interpreter']) == self.plan['interpreter_sha256'], 'MAILBOX_INTERPRETER')
        fields = ('MainPID', 'ActiveState', 'SubState', 'ControlPID', 'FragmentPath', 'DropInPaths',
                  'NeedDaemonReload', 'ExecStart')
        raw = subprocess.check_output([*self.command, 'show', self.plan['unit'],
                                       '--property=' + ','.join(fields)], text=True, timeout=10)
        state = dict(line.split('=', 1) for line in raw.splitlines())
        self.observed_state = {key: state.get(key, '')[:128] for key in
                               ('MainPID', 'ControlPID', 'ActiveState', 'SubState', 'NeedDaemonReload')}
        admission.require(set(state) == set(fields) and state['MainPID'] not in ('', '0') and
                          state['ControlPID'] == '0' and state['ActiveState'] == 'active' and
                          state['SubState'] == 'running' and state['NeedDaemonReload'] == 'no', 'MAILBOX_UNIT_NOT_LIVE')
        admission.require({state['FragmentPath'], *shlex.split(state['DropInPaths'])} == set(self.plan['files']),
                          'MAILBOX_UNIT_FILES')
        commands = re.findall(r'argv\[\]=(.*?) ; ignore_errors=', state['ExecStart'])
        admission.require(commands == [' '.join(self.plan['restart_argv'])], 'MAILBOX_RESTART_COMMAND')
        process = admission.binding(int(state['MainPID']))
        admission.require(os.readlink(Path('/proc') / state['MainPID'] / 'exe') == self.plan['interpreter'],
                          'MAILBOX_EXECUTABLE_CHANGED')
        arguments = [os.fsdecode(value) for value in admission.read(
            Path('/proc') / state['MainPID'] / 'cmdline').split(b'\0') if value]
        admission.require(arguments in (self.plan['argv'], self.plan['restart_argv']), 'MAILBOX_GUARDED_COMMAND')
        return process

    def call(self, value):
        admission.require(type(value) is dict and set(value) == {'action', 'nonce', 'payload'} and
                          re.fullmatch('[0-9a-f]{64}', value['nonce']) and value['action'] in
                          self.actions, 'MAILBOX_CONTROL_REQUEST')
        process = self.validate()
        manifest = Path(self.plan['manifest'])
        raw = owned(manifest, self.owner)
        configuration = json.loads(raw, object_pairs_hook=unique)
        nonce, action = value['nonce'], value['action']
        admission.require(self.runtime.is_dir() and not self.runtime.is_symlink() and
                          self.runtime.stat().st_uid == self.owner and not self.runtime.stat().st_mode & 0o022,
                          'MAILBOX_CONTROL_DIRECTORY')
        responses = Path(self.plan.get('response_directory', self.runtime / 'responses'))
        admission.require(responses.is_absolute() and '..' not in responses.parts, 'MAILBOX_RESPONSE_PATH')
        admission.require(responses.is_dir() and not responses.is_symlink() and
                          responses.stat().st_uid == self.plan['uid'] and not responses.stat().st_mode & 0o077,
                          'MAILBOX_RESPONSE_DIRECTORY')
        request, probe = self.runtime / (nonce + '.json'), self.runtime / (nonce + '.py')
        output = responses / (nonce + '.json')
        admission.require(not any(path.exists() or path.is_symlink() for path in (request, probe, output)),
                          'MAILBOX_NONCE_REUSED')
        if action == 'reclose':
            seal = manifest.with_suffix('.reclosed.json')
            expected = dict(schema=1, generation=configuration['generation'],
                            manifest_sha256=hashlib.sha256(raw).hexdigest(), opening_invalidated=True)
            if seal.exists() or seal.is_symlink():
                admission.require(json.loads(owned(seal, self.owner), object_pairs_hook=unique) == expected,
                                  'RECLOSURE_SEAL_CHANGED')
            else:
                admission.write(seal, expected)
                os.chown(seal, self.owner, self.plan['gid'])
                seal.chmod(0o640)
        admission.write(request, value['payload'])
        os.chown(request, self.owner, self.plan['gid'])
        request.chmod(0o640)
        invocation = self.invocation(action, request)
        code = ('import os,time\nfrom scripts import control_ha_mailbox_startup as mailbox\n'
                'from scripts import control_ha_legacy_support as admission\n'
                f'assert time.monotonic() < {time.monotonic() + 5!r}\n'
                f'assert admission.binding(os.getpid()) == {process!r}\n'
                f'assert os.getuid() == {self.plan["uid"]!r}\n'
                'startup=mailbox.ACTIVE\n'
                'try:\n'
                f' admission.require(str(startup.path) == {str(manifest)!r},"MAILBOX_ACTIVE_MANIFEST")\n'
                f' observed={invocation}\n'
                f' result=dict(nonce={nonce!r},observed=observed)\n'
                'except Exception as error:\n'
                ' import re\n'
                ' reason=str(error)\n'
                f' result=dict(nonce={nonce!r},error=reason if re.fullmatch("[A-Z][A-Z0-9_]{{1,80}}",reason) else type(error).__name__)\n'
                f'admission.write(mailbox.Path({str(output)!r}),result)\n')
        with probe.open('x') as destination:
            destination.write(code)
            destination.flush()
            os.fsync(destination.fileno())
        os.chown(probe, self.owner, self.plan['gid'])
        probe.chmod(0o640)
        try:
            sys.remote_exec(process['pid'], str(probe))
        except RuntimeError:
            raise ValueError('MAILBOX_PROBE_UNAVAILABLE') from None
        if 'wakeup_directory' in self.plan:
            wake_control(process, self.plan['wakeup_directory'], self.plan['uid'])
        deadline = time.monotonic() + 5
        while not output.exists():
            admission.require(time.monotonic() < deadline, 'MAILBOX_RESPONSE_UNKNOWN')
            time.sleep(.01)
        result = json.loads(owned(output, self.plan['uid']), object_pairs_hook=unique)
        admission.require(result.get('nonce') == nonce and self.validate() == process, 'MAILBOX_READBACK_CHANGED')
        if 'error' in result:
            raise ValueError(result['error'])
        admission.require(result['observed']['ticket']['process'] == process, 'MAILBOX_PROCESS_CHANGED')
        result.update(unit_verified=True, restart_guard_verified=True, controller_uid=self.owner,
                      unit_files_sha256=hashlib.sha256(encoded(self.plan['files'])).hexdigest(),
                      source_files_sha256=hashlib.sha256(encoded(self.plan['sources'])).hexdigest())
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', required=True, type=Path)
    args = parser.parse_args()
    raw = sys.stdin.buffer.read(65537)
    admission.require(len(raw) <= 65536, 'MAILBOX_REQUEST_TOO_LARGE')
    value = json.loads(raw, object_pairs_hook=unique)
    controller = None
    try:
        controller = MailboxControl(args.plan)
        result = controller.call(value)
    except ValueError as error:
        reason = str(error)
        reason = reason if re.fullmatch('[A-Z][A-Z0-9_]{1,80}', reason) else type(error).__name__
        waiting = reason in ('MAILBOX_PROBE_UNAVAILABLE', 'MAILBOX_RESPONSE_UNKNOWN', 'MAILBOX_READBACK_CHANGED',
                             'MAILBOX_WAKEUP_NOT_READY')
        print(encoded(dict(nonce=value['nonce'], controller_uid=os.geteuid(), result='REFUSED',
                           reason=reason, incomplete=True, retryable=waiting,
                           state=getattr(controller, 'observed_state', {}))).decode())
        raise SystemExit(75 if waiting else 78) from None
    print(encoded(result).decode())


if __name__ == '__main__':
    main()
