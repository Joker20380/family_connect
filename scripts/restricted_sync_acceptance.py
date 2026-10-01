"""Bounded RU acceptance, separate from the immutable restricted sync runtime."""
import argparse
import contextlib
from datetime import datetime, timezone
import io
import json
import os
from pathlib import Path
import re
import resource
import runpy
import secrets
import subprocess
import sys
import tempfile
import time

UNIT = 'family-connect-restricted-sync.service'
STEPS = {
    'before': ('python', 'python -I <operator> --snapshot --runtime <archive> --root <root>', 5),
    'unit_before': ('systemctl', 'systemctl show <sync-unit> <fixed-properties>', 2),
    'reload': ('systemctl', 'systemctl daemon-reload', 5),
    'start': ('systemctl', 'systemctl start <sync-unit>', 45),
    'unit_after': ('systemctl', 'systemctl show <sync-unit> <fixed-properties>', 2),
    'after': ('python', 'python -I <operator> --snapshot --runtime <archive> --root <root>', 5),
    'generic_shell': ('ssh', 'ssh <fixed-strict-options> <dedicated-target> id', 15),
    'stale_crl': ('ssh', 'ssh <fixed-strict-options> <dedicated-target> restricted-sync [stdin:redacted]', 15),
    'final': ('python', 'python -I <operator> --snapshot --runtime <archive> --root <root>', 5),
    'journal': ('journalctl', 'journalctl -u <sync-unit> --since <time> -o cat --no-pager', 10),
}
STATE_FIELDS = {'ActiveState': {'active', 'inactive', 'activating', 'deactivating', 'failed'},
                'SubState': {'dead', 'running', 'start', 'stop', 'failed', 'exited'},
                'Result': {'success', 'exit-code', 'timeout', 'signal', 'resources'},
                'Type': {'oneshot'}, 'TimeoutStartUSec': {'25s'}}
STATE_NUMBERS = ('MainPID', 'ExecMainCode', 'ExecMainStatus', 'ExecMainStartTimestampMonotonic')
METADATA = ('crl_sequence', 'database_sequence', 'directory_version', 'directory_issued_ns',
            'directory_expires_ns', 'directory_valid')
LIMIT = 65536
TOTAL_SECONDS = 107


class AcceptanceFailed(RuntimeError):
    pass


def safe_state(raw):
    try:
        values = dict(line.split('=', 1) for line in raw.decode().splitlines() if '=' in line)
    except UnicodeError:
        return {}
    result = {key: value if value in allowed else 'unknown'
              for key, allowed in STATE_FIELDS.items() if (value := values.get(key)) is not None}
    for key in STATE_NUMBERS:
        value = values.get(key, '')
        if value.isascii() and value.isdigit() and len(value) < 22:
            result[key] = int(value)
    return result


def safe_metadata(value):
    return {key: item for key in METADATA if type(item := value.get(key)) in (int, bool) and item >= 0}


def classify(raw):
    if not raw:
        return 'empty'
    if len(raw) > LIMIT:
        return 'oversized'
    for marker, label in ((b'ModuleNotFoundError', 'module-import-error'),
                          (b'directory_validation_failed', 'directory-validation-failed'),
                          (b'Restricted synchronization unavailable', 'sync-unavailable')):
        if marker in raw:
            return label
    return 'nonempty-redacted'


class Receipts:
    def __init__(self, path, generation):
        if not re.fullmatch(r'[A-Za-z0-9_.-]{1,64}', generation):
            raise ValueError('Invalid generation')
        self.path, self.generation = Path(path), generation
        self.path.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.descriptor = os.open(self.path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        metadata = os.fstat(self.descriptor)
        if metadata.st_uid != os.geteuid() or metadata.st_mode & 0o077:
            self.close()
            raise ValueError('Receipt directory must be owner-only')

    def close(self):
        os.close(self.descriptor)

    def persist(self, record):
        record = dict(record, generation=self.generation,
                      timestamp=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'))
        name = str(time.monotonic_ns()) + '-' + secrets.token_hex(8)
        descriptor = os.open(name + '.pending', os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                             0o600, dir_fd=self.descriptor)
        with os.fdopen(descriptor, 'w') as stream:
            json.dump(record, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.rename(name + '.pending', name + '.json', src_dir_fd=self.descriptor, dst_dir_fd=self.descriptor)
        os.fsync(self.descriptor)


def execute(argv, timeout, payload=None):
    with tempfile.TemporaryFile() as output, tempfile.TemporaryFile() as errors:
        try:
            process = subprocess.run(argv, input=payload, stdout=output, stderr=errors, timeout=timeout,
                                     preexec_fn=lambda: resource.setrlimit(resource.RLIMIT_FSIZE, (LIMIT, LIMIT)))
            status, timed_out, failure = process.returncode, False, None
        except subprocess.TimeoutExpired:
            status, timed_out, failure = None, True, 'timeout'
        except OSError:
            status, timed_out, failure = None, False, 'spawn-failed'
        output.seek(0)
        errors.seek(0)
        return status, output.read(LIMIT + 1), errors.read(LIMIT + 1), timed_out, failure


class Runner:
    def __init__(self, receipts, state_command, *, snapshot_command=None, execute_command=execute, clock=time.monotonic):
        self.receipts, self.state_command = receipts, state_command
        self.snapshot_command = snapshot_command
        self.execute, self.clock = execute_command, clock
        self.deadline = clock() + TOTAL_SECONDS
        self.metadata = {}
        self.after = None

    def run(self, step, argv, payload=None):
        program, shape, configured = STEPS[step]
        started = self.clock()
        timeout = min(configured, max(0, self.deadline - started - 7))
        record = dict(event='subprocess', step=step, program_class=program, argv_shape=shape,
                      timeout_configured=configured, timeout_effective=timeout, monotonic_start=started,
                      observed_before=dict(self.metadata), observed_after=None,
                      unit_state_at_timeout=None, directory_revision=None)
        if timeout:
            try:
                status, output, errors, timed_out, failure = self.execute(argv, timeout, payload)
            except BaseException:
                status, output, errors, timed_out, failure = None, b'', b'', False, 'operator-interrupted'
        else:
            status, output, errors, timed_out, failure = None, b'', b'', False, 'total-deadline'
        ended = self.clock()
        record.update(monotonic_end=ended, elapsed=ended-started, exit_status=status,
                      timeout_expired=timed_out, failure=failure, stdout_class=classify(output),
                      stderr_class=classify(errors), total_deadline_exceeded=ended > self.deadline)
        self.receipts.persist(record)
        if timed_out:
            remaining = min(2, max(0, self.deadline - self.clock()))
            state = dict(available=False)
            diagnostic = dict(step='timeout_state', program_class='systemctl',
                              argv_shape=STEPS['unit_after'][1], timeout_configured=2,
                              timeout_effective=remaining, monotonic_start=self.clock())
            if remaining:
                state_status, raw, state_errors, state_timeout, _ = self.execute(self.state_command, remaining, None)
                state.update(available=state_status == 0, timeout_expired=state_timeout)
                diagnostic.update(exit_status=state_status, timeout_expired=state_timeout,
                                  stdout_class=classify(raw), stderr_class=classify(state_errors))
                if state_status == 0:
                    state.update(safe_state(raw))
            diagnostic.update(monotonic_end=self.clock(), elapsed=self.clock()-diagnostic['monotonic_start'])
            self.receipts.persist(dict(record, event='timeout-state', unit_state_at_timeout=state,
                                       state_observed_monotonic=self.clock(), diagnostic=diagnostic))
            remaining = min(5, max(0, self.deadline - self.clock()))
            if remaining and self.snapshot_command:
                diagnostic = dict(step='timeout_readback', program_class='python',
                                  argv_shape=STEPS['after'][1], timeout_configured=5,
                                  timeout_effective=remaining, monotonic_start=self.clock())
                snapshot_status, raw, snapshot_errors, snapshot_timeout, _ = self.execute(self.snapshot_command, remaining, None)
                diagnostic.update(exit_status=snapshot_status, timeout_expired=snapshot_timeout,
                                  monotonic_end=self.clock(), elapsed=self.clock()-diagnostic['monotonic_start'],
                                  stdout_class=classify(raw), stderr_class=classify(snapshot_errors))
                observed = None
                if snapshot_status == 0:
                    try:
                        observed = safe_metadata(json.loads(raw))
                    except (ValueError, TypeError, AttributeError):
                        pass
                self.after = observed
                self.receipts.persist(dict(record, event='timeout-readback', observed_after=observed,
                                           unit_state_at_timeout=state, readback_timeout=snapshot_timeout,
                                           readback_observed_monotonic=self.clock(), diagnostic=diagnostic))
        if failure or ended > self.deadline:
            raise AcceptanceFailed(step) from None
        return subprocess.CompletedProcess(argv, status, output, errors)

    def check(self, step, condition):
        self.receipts.persist(dict(event='predicate', step=step, passed=bool(condition),
                                   observed_after=dict(self.metadata)))
        if not condition:
            raise AcceptanceFailed(step)


def decoded_snapshot(runner, step, command):
    result = runner.run(step, command)
    runner.check(step + '_exit', result.returncode == 0 and not result.stderr)
    try:
        value = json.loads(result.stdout)
        metadata = safe_metadata(value)
    except (ValueError, TypeError, AttributeError):
        metadata = {}
    runner.metadata = metadata
    if step != 'before':
        runner.after = metadata
    runner.check(step + '_schema', set(metadata) == set(METADATA)
                 and type(metadata['directory_valid']) is bool
                 and all(type(metadata[key]) is int for key in METADATA if key != 'directory_valid'))
    runner.check(step + '_authority', metadata['crl_sequence'] > 0
                 and metadata['crl_sequence'] == metadata['database_sequence'])
    return metadata


def accept(runner, commands, stale):
    completed = []
    try:
        before = decoded_snapshot(runner, 'before', commands['snapshot'])
        result = runner.run('unit_before', commands['state'])
        state = safe_state(result.stdout)
        runner.check('unit_before_state', result.returncode == 0 and state.get('Type') == 'oneshot'
                     and state.get('ActiveState') == 'inactive' and state.get('MainPID') == 0
                     and state.get('TimeoutStartUSec') == '25s')
        result = runner.run('reload', commands['reload'])
        runner.check('reload_exit', result.returncode == 0)
        result = runner.run('start', commands['start'])
        runner.check('start_exit', result.returncode == 0)
        result = runner.run('unit_after', commands['state'])
        state = safe_state(result.stdout)
        runner.check('unit_completed', result.returncode == 0 and state.get('Type') == 'oneshot'
                     and state.get('ActiveState') == 'inactive' and state.get('SubState') == 'dead'
                     and state.get('Result') == 'success' and state.get('MainPID') == 0
                     and state.get('ExecMainCode') in (0, 1) and state.get('ExecMainStatus') == 0)
        after = decoded_snapshot(runner, 'after', commands['snapshot'])
        runner.check('fresh_readback', after['crl_sequence'] == before['crl_sequence'] + 1
                     and after['directory_valid'] and after['directory_version'] == 1
                     and after['directory_issued_ns'] >= before['directory_issued_ns'])
        completed.extend(('unit', 'fresh_readback'))
        result = runner.run('generic_shell', commands['generic_shell'])
        runner.check('generic_shell_rejected', result.returncode == 126 and not result.stdout)
        completed.append('generic_shell')
        result = runner.run('stale_crl', commands['stale_crl'], stale)
        runner.check('stale_crl_rejected', result.returncode == 1 and not result.stdout)
        completed.append('stale_crl')
        final = decoded_snapshot(runner, 'final', commands['snapshot'])
        runner.check('no_rollback', final == after)
        runner.check('total_deadline', runner.clock() <= runner.deadline)
    except BaseException:
        runner.receipts.persist(dict(event='verdict', passed=False, completed=completed,
                                     observed_after=runner.after, last_observed=dict(runner.metadata)))
        raise
    runner.receipts.persist(dict(event='verdict', passed=True, completed=completed,
                                 observed_after=dict(runner.metadata)))


def commands(root, runtime):
    state = ['/usr/bin/systemctl', 'show', UNIT, '-p', ','.join((*STATE_FIELDS, *STATE_NUMBERS))]
    snapshot = [sys.executable, '-I', str(Path(__file__).resolve()), '--snapshot',
                '--root', str(root), '--runtime', str(runtime)]
    material = root / 'friends-restricted'
    ssh = ['/usr/bin/ssh', '-i', str(material / 'sync.key'), '-o', 'IdentitiesOnly=yes',
           '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
           '-o', 'UserKnownHostsFile=' + str(material / 'known_hosts'), '-o', 'ConnectTimeout=5',
           'family-restricted@186.246.45.246']
    return dict(snapshot=snapshot, state=state, reload=['/usr/bin/systemctl', 'daemon-reload'],
                start=['/usr/bin/systemctl', 'start', UNIT], generic_shell=ssh + ['id'],
                stale_crl=ssh + ['restricted-sync'])


def load_runtime(runtime):
    sys.argv = [str(runtime), '--help']
    with contextlib.redirect_stdout(io.StringIO()):
        try:
            runpy.run_path(str(runtime), run_name='__main__')
        except SystemExit as error:
            if error.code != 0:
                raise AcceptanceFailed('runtime-import') from None


def snapshot(root, runtime):
    import sqlite3
    load_runtime(runtime)
    from control.friends.access import Access
    from control.friends.restricted import DirectoryValidationError, directory, from_env, timestamp_ns
    material = root / 'friends-restricted'
    os.environ['FC_FRIENDS_RESTRICTED_DIR'] = str(material)
    service = from_env(Access(root / 'friends-access/access.db'))
    trust, _, _, _, number = service._trust(int(time.time()))
    database = sqlite3.connect(service.access.path.resolve().as_uri() + '?mode=ro', uri=True, timeout=1)
    try:
        sequence = database.execute('SELECT sequence FROM restricted_crl_sequence WHERE singleton=1').fetchone()[0]
    finally:
        database.close()
    result = dict(crl_sequence=number, database_sequence=sequence, directory_valid=False,
                  directory_version=0, directory_issued_ns=0, directory_expires_ns=0)
    try:
        value = directory(service.seed_source(), trust['family'], trust['gateway'])
    except (OSError, DirectoryValidationError):
        return result
    result.update(directory_valid=True, directory_version=value['version'],
                  directory_issued_ns=timestamp_ns(value['issued_at']), directory_expires_ns=timestamp_ns(value['expires_at']))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--snapshot', action='store_true')
    mode.add_argument('--execute', action='store_true', help='Authorized deployment only: starts restricted sync once')
    parser.add_argument('--root', type=Path, default=Path('/opt/apps/family_connect'))
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--evidence', type=Path)
    parser.add_argument('--generation')
    args = parser.parse_args()
    if args.snapshot:
        print(json.dumps(snapshot(args.root, args.runtime)))
        return
    if args.evidence is None or args.generation is None:
        parser.error('--execute requires --evidence and --generation')
    receipts = Receipts(args.evidence, args.generation)
    try:
        load_runtime(args.runtime)
        from control.friends.restricted import bounded_file
        stale = bounded_file(args.root / 'friends-restricted/revocations.pem', 16384, True)
        configured = commands(args.root, args.runtime)
        accept(Runner(receipts, configured['state'], snapshot_command=configured['snapshot']),
               configured, json.dumps(dict(revocations=stale.decode())).encode())
    finally:
        receipts.close()
    print('Restricted sync acceptance passed; receipts persisted')


if __name__ == '__main__':
    try:
        main()
    except Exception:
        raise SystemExit('Restricted sync acceptance failed; inspect protected receipts') from None
