"""Bounded NL bootstrap acceptance; journal diagnostics never decide runtime success."""
import argparse
import contextlib
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import resource
import runpy
import secrets
import signal
import subprocess
import sys
import tempfile
import time

UNIT = 'family-connect-restricted-bootstrap.service'
LIMIT = 65536
TOTAL_SECONDS = 165
READY_SECONDS = 120
JOURNAL_SECONDS = 5
STATE_FIELDS = ('ActiveState', 'SubState', 'Result', 'MainPID', 'NRestarts',
                'ExecMainStatus', 'ExecMainStartTimestampMonotonic')
MATERIAL_FIELDS = ('published', 'directory_valid', 'canonical_utc', 'seed_count',
                   'issued_ns', 'expires_ns', 'crl_expires_ns', 'gateway_expires_ns')


class AcceptanceFailed(RuntimeError):
    pass


class Receipts:
    def __init__(self, path, generation):
        if not re.fullmatch(r'[A-Za-z0-9_.-]{1,64}', generation):
            raise ValueError('Invalid generation')
        self.path, self.generation = Path(path), generation
        self.path.mkdir(mode=0o700)
        self.descriptor = os.open(self.path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        parent = os.open(self.path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(parent)
        finally:
            os.close(parent)

    def close(self):
        os.close(self.descriptor)

    def persist(self, kind, record):
        if kind not in ('authoritative', 'diagnostic'):
            raise ValueError('Invalid receipt kind')
        record = dict(record, kind=kind, generation=self.generation,
                      timestamp=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'))
        name = kind + '-' + str(time.monotonic_ns()) + '-' + secrets.token_hex(8)
        descriptor = os.open(name + '.pending', os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                             0o600, dir_fd=self.descriptor)
        with os.fdopen(descriptor, 'w') as stream:
            json.dump(record, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.rename(name + '.pending', name + '.json', src_dir_fd=self.descriptor, dst_dir_fd=self.descriptor)
        os.fsync(self.descriptor)


def execute(argv, timeout):
    with tempfile.TemporaryFile() as output, tempfile.TemporaryFile() as errors:
        try:
            process = subprocess.run(argv, stdout=output, stderr=errors, timeout=timeout,
                                     preexec_fn=lambda: resource.setrlimit(resource.RLIMIT_FSIZE, (LIMIT, LIMIT)))
            status, timed_out = process.returncode, False
        except subprocess.TimeoutExpired:
            status, timed_out = None, True
        except OSError:
            status, timed_out = None, False
        output.seek(0)
        errors.seek(0)
        return status, output.read(LIMIT + 1), errors.read(LIMIT + 1), timed_out


def classify(raw):
    return 'oversized' if len(raw) > LIMIT else 'nonempty-redacted' if raw else 'empty'


def safe_state(raw):
    values = dict(line.split('=', 1) for line in raw.decode().splitlines() if '=' in line)
    result = {}
    choices = {'ActiveState': ('inactive', 'active', 'failed', 'activating', 'deactivating'),
               'SubState': ('dead', 'running', 'failed', 'start', 'auto-restart'),
               'Result': ('success', 'exit-code', 'signal', 'timeout', 'start-limit-hit')}
    for key in STATE_FIELDS:
        value = values.get(key, '')
        if key in choices:
            result[key] = value if value in choices[key] else 'unknown'
        else:
            result[key] = int(value) if value.isascii() and value.isdigit() and len(value) < 22 else -1
    return result


class Runner:
    def __init__(self, receipts, commands, *, execute_command=execute, clock=time.monotonic,
                 wall_clock=time.time_ns, sleep=time.sleep):
        self.receipts, self.commands, self.execute = receipts, commands, execute_command
        self.clock, self.wall_clock, self.sleep = clock, wall_clock, sleep
        self.deadline = clock() + TOTAL_SECONDS
        self.decided = False

    def require(self, condition, reason):
        if not condition:
            raise AcceptanceFailed(reason)

    def command(self, step, cap, deadline=None):
        started = self.clock()
        timeout = min(cap, (self.deadline if deadline is None else min(deadline, self.deadline)) - started)
        self.require(timeout > 0, 'authoritative_deadline')
        status, output, errors, timed_out = self.execute(self.commands[step], timeout)
        elapsed = self.clock() - started
        self.receipts.persist('authoritative', dict(event='command', step=step, timeout=timeout,
                              elapsed=elapsed, exit_status=status, timeout_expired=timed_out,
                              stdout_class=classify(output), stderr_class=classify(errors)))
        self.require(not timed_out and elapsed <= timeout, step + '_timeout')
        self.require(status == 0 and len(output) <= LIMIT and len(errors) <= LIMIT, step + '_command_failed')
        return output

    def state(self, deadline=None):
        state = safe_state(self.command('state', 2, deadline))
        self.receipts.persist('authoritative', dict(event='service_state', state=state))
        return state

    def material(self, deadline=None):
        value = json.loads(self.command('snapshot', 5, deadline))
        self.require(type(value) is dict, 'snapshot_schema')
        for key in MATERIAL_FIELDS:
            expected_type = bool if key in ('published', 'directory_valid', 'canonical_utc') else int
            self.require(type(value.get(key)) is expected_type and value[key] >= 0, 'snapshot_schema')
        self.require(type(value.get('binding')) is str and re.fullmatch(r'[0-9a-f]{64}', value['binding']), 'snapshot_binding')
        self.receipts.persist('authoritative', dict(event='material', **{key: value[key] for key in MATERIAL_FIELDS}))
        return value

    def healthy(self, state, previous, active=None):
        self.require(state['ActiveState'] == 'active' and state['SubState'] == 'running'
                     and state['Result'] == 'success' and state['ExecMainStatus'] == 0
                     and state['MainPID'] > 0 and state['NRestarts'] == 0
                     and state['ExecMainStartTimestampMonotonic'] > previous['ExecMainStartTimestampMonotonic'],
                     'service_unhealthy')
        if active is not None:
            self.require(all(state[key] == active[key] for key in ('MainPID', 'ExecMainStartTimestampMonotonic')),
                         'service_restarted')

    def accept(self):
        if self.decided:
            raise AcceptanceFailed('authoritative_verdict_already_written')
        failure = None
        try:
            previous = self.state()
            self.require(previous['ActiveState'] == 'inactive' and previous['MainPID'] == 0
                         and previous['ExecMainStartTimestampMonotonic'] >= 0, 'service_not_inactive')
            before = self.material()
            self.require(not before['published'], 'preexisting_directory')
            started_ns = self.wall_clock()
            self.require(min(before['crl_expires_ns'], before['gateway_expires_ns']) - started_ns > 600_000_000_000,
                         'material_expiring')
            self.command('start', 30)
            wait_until = min(self.clock() + READY_SECONDS, self.deadline - 7)
            active = None
            ready = None
            for attempt in range(60):
                self.require(self.clock() < wait_until, 'ready_deadline')
                state = self.state(wait_until)
                self.healthy(state, previous, active)
                active = state
                current = self.material(wait_until)
                self.require(current['binding'] == before['binding'], 'gateway_binding_changed')
                if current['published']:
                    self.require(current['directory_valid'] and current['canonical_utc'] and current['seed_count'] == 1,
                                 'directory_invalid')
                    self.require(current['issued_ns'] >= started_ns, 'directory_not_fresh')
                    ready = current
                    break
                self.sleep(min(2, max(0, wait_until - self.clock())))
            self.require(ready is not None, 'ready_deadline')
            self.healthy(self.state(), previous, active)
            final = self.material()
            self.require(final == ready and final['expires_ns'] > self.wall_clock()
                         and min(final['crl_expires_ns'], final['gateway_expires_ns']) > self.wall_clock(),
                         'final_material_changed_or_expired')
            self.require(self.clock() <= self.deadline, 'authoritative_deadline')
            self.receipts.persist('authoritative', dict(event='ready', observed=True, seed_published=True,
                                  directory_valid=True, gateway_binding_unchanged=True, restarts=0,
                                  signal='fresh_validated_post_connect_export', issued_ns=final['issued_ns'],
                                  expires_ns=final['expires_ns']))
        except BaseException as error:
            failure = str(error) if isinstance(error, AcceptanceFailed) else 'operator_interrupted' if isinstance(error, (KeyboardInterrupt, InterruptedError)) else 'operator_error'
        self.receipts.persist('authoritative', dict(event='verdict', passed=failure is None, failure=failure))
        self.decided = True
        return failure is None

    def diagnose(self, enabled):
        if not self.decided:
            raise AcceptanceFailed('authoritative_verdict_missing')
        record = dict(event='journal', available=False, timeout=False, classification='diagnostic_not_requested')
        if enabled:
            started = self.clock()
            try:
                status, output, errors, timed_out = self.execute(self.commands['journal'], JOURNAL_SECONDS)
                timed_out = timed_out or self.clock() - started > JOURNAL_SECONDS
                available = status == 0 and not timed_out and len(output) <= LIMIT and len(errors) <= LIMIT
                record.update(available=available, timeout=timed_out, exit_status=status,
                              classification='diagnostic_available' if available else 'diagnostic_timeout' if timed_out else 'diagnostic_unavailable',
                              stdout_class=classify(output), stderr_class=classify(errors))
            except subprocess.TimeoutExpired:
                record.update(timeout=True, classification='diagnostic_timeout')
            except (OSError, subprocess.SubprocessError):
                record['classification'] = 'diagnostic_unavailable'
            record.update(timeout_configured=JOURNAL_SECONDS, elapsed=self.clock() - started)
        self.receipts.persist('diagnostic', record)
        return record


def snapshot(root, runtime):
    sys.argv = [str(runtime), '--help']
    with contextlib.redirect_stdout(io.StringIO()):
        try:
            runpy.run_path(str(runtime), run_name='__main__')
        except SystemExit as error:
            if error.code != 0:
                raise AcceptanceFailed('runtime_import') from None
    from cryptography import x509
    from control.friends.restricted import DirectoryValidationError, bounded_file, directory, timestamp_ns
    from provisioning.friends_catalog import parse
    material = root / 'friends-restricted'
    profile = parse(bounded_file(material / 'gateway.json', 49152, True))
    binding = {key: profile[key] for key in ('family', 'gateway', 'authority', 'certificate', 'minimum_revision')}
    certificate = x509.load_pem_x509_certificate(profile['certificate'].encode())
    crl = x509.load_pem_x509_crl(profile['revocations'].encode())
    result = dict(binding=hashlib.sha256(json.dumps(binding, sort_keys=True).encode()).hexdigest(),
                  published=False, directory_valid=False, canonical_utc=False, seed_count=0, issued_ns=0, expires_ns=0,
                  crl_expires_ns=int(crl.next_update_utc.timestamp()) * 1_000_000_000,
                  gateway_expires_ns=int(certificate.not_valid_after_utc.timestamp()) * 1_000_000_000)
    try:
        raw = bounded_file(material / 'directory.json', 8192, True)
    except FileNotFoundError:
        return result
    result['published'] = True
    try:
        value = directory(raw, profile['family'], profile['gateway'])
        original = parse(raw)
        result.update(directory_valid=True, canonical_utc=all(original[key].endswith('Z') for key in ('issued_at', 'expires_at')),
                      seed_count=len(value['seeds']), issued_ns=timestamp_ns(value['issued_at']),
                      expires_ns=timestamp_ns(value['expires_at']))
    except DirectoryValidationError:
        pass
    return result


def commands(root, runtime):
    return dict(state=['/usr/bin/systemctl', 'show', UNIT, '-p', ','.join(STATE_FIELDS)],
                start=['/usr/bin/systemctl', 'start', UNIT],
                snapshot=[sys.executable, '-I', str(Path(__file__).resolve()), '--snapshot', '--root', str(root), '--runtime', str(runtime)],
                journal=['/usr/bin/journalctl', '-u', UNIT, '--since', '@' + str(int(time.time())), '-n', '100', '-o', 'json', '--no-pager'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--execute', action='store_true', help='Authorized deployment only: starts NL bootstrap once')
    mode.add_argument('--snapshot', action='store_true', help='Read-only material snapshot; internal binding digest is not a receipt')
    parser.add_argument('--root', type=Path, default=Path('/opt/apps/family_connect'))
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--evidence', type=Path)
    parser.add_argument('--generation')
    parser.add_argument('--journal', action='store_true', help='Optional non-gating diagnostic, at most five seconds')
    args = parser.parse_args()
    if args.snapshot:
        print(json.dumps(snapshot(args.root, args.runtime)))
        return 0
    if args.evidence is None or args.generation is None:
        parser.error('--execute requires --evidence and --generation')
    root, evidence = args.root.resolve(), args.evidence.resolve()
    if root.is_relative_to(evidence) or any(evidence.is_relative_to(root / name) for name in ('friends-restricted', 'friends-access')):
        parser.error('Evidence must be outside the runtime/rollback replacement tree')
    receipts = Receipts(args.evidence, args.generation)
    try:
        runner = Runner(receipts, commands(args.root, args.runtime))
        passed = runner.accept()
        diagnostic = runner.diagnose(args.journal)
    finally:
        receipts.close()
    print(json.dumps(dict(authoritative='PASS' if passed else 'FAIL', journal=diagnostic['classification'])))
    return 0 if passed else 1


if __name__ == '__main__':
    def interrupted(number, frame):
        raise InterruptedError('operator interrupted')
    for number in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(number, interrupted)
    try:
        status = main()
    except Exception:
        raise SystemExit('NL acceptance/evidence unavailable; inspect protected receipts') from None
    raise SystemExit(status)
