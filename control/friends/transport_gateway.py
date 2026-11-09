"""Gateway decision cache and bounded application, not a subscription authority."""
import fcntl
from contextlib import contextmanager
from contextvars import ContextVar
import json
import os
from pathlib import Path
import re
import resource
import signal
import socket
import subprocess
import sys
import time

from . import transport_policy as policy

SERVICES = ('family-connect-friends-awg.service', 'family-connect-friends-tcp.service')
OPERATION_SECONDS = 8
CURRENT_OPERATION = ContextVar('transport_operation', default=None)
FAILURE_CODES = frozenset(('TRANSPORT_OPERATION_DEADLINE', 'ENGINE_START_TIMEOUT',
    'ENGINE_READBACK_MISMATCH', 'INVALID_AWG_READBACK', 'INVALID_TCP_READBACK',
    'UNSAFE_GATEWAY_STATE', 'INVALID_GATEWAY_POLICY', 'INVALID_GATEWAY_CACHE',
    'INVALID_MEMBERSHIP_CACHE', 'INVALID_GATEWAY_BINDING', 'TCP_BINDING_CONFLICT',
    'INCOMPLETE_NODE_BINDING', 'APPLICATION_DID_NOT_CONVERGE', 'DUPLICATE_JSON_FIELD'))


def emit(value):
    try:
        print(json.dumps(value, sort_keys=True), file=sys.stderr, flush=True)
    except OSError:
        pass


def process_usage():
    try:
        return resource.getrusage(resource.RUSAGE_SELF)
    except OSError:
        return None


def command_family(arguments):
    executable = Path(arguments[0]).name if arguments else ''
    if executable == 'awg':
        return 'awg-query' if arguments[1:2] == ['show'] else 'awg-actuation'
    if executable == 'xray':
        return 'tcp-query' if arguments[1:2] == ['api'] else 'tcp-engine'
    return executable if executable in ('systemctl', 'ip', 'iptables') else 'other'


def failure_record(error, mode):
    context = getattr(error, 'transport_context', {})
    if isinstance(error, subprocess.TimeoutExpired):
        kind, reason = 'TimeoutExpired', 'COMMAND_TIMEOUT'
    elif isinstance(error, subprocess.CalledProcessError):
        kind, reason = 'CalledProcessError', 'COMMAND_FAILED'
    elif isinstance(error, TimeoutError):
        kind, reason = 'TimeoutError', 'TRANSPORT_OPERATION_DEADLINE'
    elif isinstance(error, OSError):
        kind, reason = 'OSError', 'FILESYSTEM_OR_OS_ERROR'
    elif isinstance(error, ValueError):
        kind, reason = 'ValueError', str(error) if str(error) in FAILURE_CODES else 'INVALID_INPUT_OR_STATE'
    elif isinstance(error, AssertionError):
        kind, reason = 'AssertionError', 'INVARIANT_FAILED'
    else:
        kind, reason = 'Exception', 'UNCLASSIFIED_FAILURE'
    invocation = os.environ.get('INVOCATION_ID', '')
    record = dict(schema=1, mode=mode if mode in ('watch', 'register', 'run', 'paid-preflight') else 'unknown',
        phase=context.get('phase', 'entry'), exception_class=kind, reason=reason,
        pid=os.getpid(), invocation_id=invocation if re.fullmatch('[a-f0-9]{32}', invocation) else None,
        observed_at=time.time(), elapsed=context.get('elapsed'), budget=OPERATION_SECONDS)
    for name in ('boundary', 'calls', 'calls_dropped', 'stage_counts'):
        if name in context:
            record[name] = context[name]
    if isinstance(error, (subprocess.TimeoutExpired, subprocess.CalledProcessError)):
        record.update(command_family=command_family(error.cmd),
            returncode=getattr(error, 'returncode', None), timeout=isinstance(error, subprocess.TimeoutExpired))
    if isinstance(error, OSError):
        record['errno'] = error.errno
    return record


def report_failure(error, mode, root):
    if getattr(error, 'transport_reported', False):
        return
    error.transport_reported = True
    record = failure_record(error, mode)
    emit(dict(transport_failure=record))
    diagnostic_started = time.monotonic()
    outcome = 'unavailable'
    try:
        descriptor = os.open(root/'transport-failure.json', os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(descriptor, 'w') as output:
            json.dump(record, output, sort_keys=True)
            output.flush()
            sync_started = time.monotonic()
            emit(dict(transport_diagnostic_call=dict(role='failure_record', kind='file_fsync',
                boundary='before', remaining=None)))
            os.fsync(output.fileno())
            emit(dict(transport_diagnostic_call=dict(role='failure_record', kind='file_fsync',
                boundary='after', duration=time.monotonic()-sync_started, completed=True)))
            outcome = 'created'
    except FileExistsError:
        outcome = 'retained'
    except Exception:
        emit(dict(transport_diagnostic_persistence='unavailable'))
    finally:
        emit(dict(transport_diagnostic_write=dict(role='failure_record', result=outcome,
            duration=time.monotonic()-diagnostic_started)))


class Operation:
    def __init__(self, seconds=OPERATION_SECONDS):
        self.started = time.monotonic()
        self.deadline = self.started + seconds
        self.stages = {}
        self.stage_counts = {}
        self.calls = []
        self.calls_dropped = 0

    def context(self, phase, boundary):
        return dict(phase=phase, boundary=boundary, elapsed=time.monotonic()-self.started,
            calls=self.calls.copy(), calls_dropped=self.calls_dropped, stage_counts=self.stage_counts.copy())

    def remaining(self):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError('TRANSPORT_OPERATION_DEADLINE')
        return remaining

    @contextmanager
    def stage(self, name):
        started = time.monotonic()
        self.stage_counts[name] = self.stage_counts.get(name, 0) + 1
        boundary = 'before'
        try:
            self.remaining()
            boundary = 'body'
            yield
            boundary = 'after'
            self.remaining()
        except BaseException as error:
            if not hasattr(error, 'transport_context'):
                error.transport_context = self.context(name, boundary)
            raise
        finally:
            self.stages[name] = self.stages.get(name, 0) + time.monotonic() - started

    @contextmanager
    def call(self, kind, *, role=None, replacement=None, phase=None):
        entry = dict(kind=kind, role=role, entered=time.monotonic()-self.started,
            remaining=self.deadline-time.monotonic(), started=None, finished=None,
            duration=None, completed=False, replace_completed=replacement, boundary='before')
        if len(self.calls) == 24:
            self.calls.pop(0)
            self.calls_dropped += 1
        self.calls.append(entry)
        usage = None
        boundary = 'before'
        if phase:
            self.stage_counts[phase] = self.stage_counts.get(phase, 0) + 1
        try:
            self.remaining()
            usage = process_usage()
            entry['started'] = time.monotonic()-self.started
            boundary = 'body'
            entry['boundary'] = boundary
            yield entry
            entry['completed'] = True
            entry['finished'] = time.monotonic()-self.started
            boundary = 'after'
            entry['boundary'] = boundary
            self.remaining()
        except BaseException as error:
            if phase and not hasattr(error, 'transport_context'):
                error.transport_context = self.context(phase, boundary)
            raise
        finally:
            if entry['started'] is not None:
                if entry['finished'] is None:
                    entry['finished'] = time.monotonic()-self.started
                entry['duration'] = entry['finished']-entry['started']
                latest = process_usage()
                if usage is not None and latest is not None:
                    entry['self_cpu_seconds'] = latest.ru_utime+latest.ru_stime-usage.ru_utime-usage.ru_stime
                    entry['major_faults'] = latest.ru_majflt-usage.ru_majflt
                    entry['voluntary_switches'] = latest.ru_nvcsw-usage.ru_nvcsw
                    entry['involuntary_switches'] = latest.ru_nivcsw-usage.ru_nivcsw
            if phase:
                self.stages[phase] = self.stages.get(phase, 0) + time.monotonic()-self.started-entry['entered']


@contextmanager
def measured_call(kind, *, role=None, replacement=None, phase=None):
    operation = CURRENT_OPERATION.get()
    if operation is None:
        yield {}
    else:
        with operation.call(kind, role=role, replacement=replacement, phase=phase) as entry:
            yield entry


def remaining():
    operation = CURRENT_OPERATION.get()
    return operation.remaining() if operation else OPERATION_SECONDS


def unique(pairs):
    result = {}
    for name, value in pairs:
        if name in result:
            raise ValueError('DUPLICATE_JSON_FIELD')
        result[name] = value
    return result


def read(path):
    info = path.lstat()
    if path.is_symlink() or not path.is_file() or info.st_uid != os.geteuid() or info.st_mode & 0o077 or info.st_size > 8_000_000:
        raise ValueError('UNSAFE_GATEWAY_STATE')
    return json.loads(path.read_text(), object_pairs_hook=unique)


def write(path, value, mode=0o600):
    role = {'transport-state.json': 'decision_state', 'transport-attempt.json': 'attempt_result',
        'server.json': 'engine_config'}.get(path.name, 'unknown')
    temporary = path.with_suffix('.pending')
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, mode)
    os.fchmod(descriptor, mode)
    with os.fdopen(descriptor, 'w') as handle:
        json.dump(value, handle, sort_keys=True)
        handle.flush()
        with measured_call('file_fsync', role=role, replacement=False, phase='persist_file'):
            os.fsync(handle.fileno())
    with measured_call('replace', role=role, replacement=False, phase='persist_replace') as entry:
        os.replace(temporary, path)
        entry['replace_completed'] = True
    directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        with measured_call('directory_fsync', role=role, replacement=True, phase='persist_directory'):
            os.fsync(directory)
    finally:
        os.close(directory)


def execute(arguments):
    with measured_call(command_family(arguments)):
        return execute_command(arguments)


def execute_command(arguments):
    timeout = remaining()
    with subprocess.Popen(arguments, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True) as process:
        try:
            output, errors = process.communicate(timeout=timeout)
        except BaseException:
            os.killpg(process.pid, signal.SIGKILL)
            process.communicate()
            raise
        if process.returncode:
            raise subprocess.CalledProcessError(process.returncode, arguments)
    return output


def boot_id():
    return Path('/proc/sys/kernel/random/boot_id').read_text().strip()


class Gateway:
    def __init__(self, gateway, *, clock=time.time, monotonic=time.monotonic, run=execute):
        self.gateway, self.root, self.clock, self.monotonic, self.run = gateway, gateway.ROOT, clock, monotonic, run
        self.path = self.root / 'transport-state.json'
        config = read(self.root / 'transport-enforcement.json')
        if (set(config) != {'schema', 'profile', 'node', 'enabled'} or config['schema'] != 1
                or config['profile'] != policy.PROFILE or config['node'] not in policy.NODES or config['enabled'] is not True):
            raise ValueError('INVALID_GATEWAY_POLICY')
        self.node = config['node']
        self.metrics = None

    @contextmanager
    def operation(self):
        if CURRENT_OPERATION.get() is not None:
            yield
            return
        operation = Operation()
        token = CURRENT_OPERATION.set(operation)
        result = 'error'
        try:
            yield
            operation.remaining()
            result = 'complete'
        except BaseException as error:
            if not hasattr(error, 'transport_context'):
                error.transport_context = operation.context('operation', 'body')
            raise
        finally:
            self.metrics = dict(result=result, total=time.monotonic()-operation.started, stages=operation.stages,
                stage_counts=operation.stage_counts, calls=operation.calls, calls_dropped=operation.calls_dropped)
            CURRENT_OPERATION.reset(token)
            emit(dict(transport_progress=self.metrics))

    @contextmanager
    def stage(self, name):
        operation = CURRENT_OPERATION.get()
        if operation is None:
            raise RuntimeError('TRANSPORT_OPERATION_REQUIRED')
        with operation.stage(name):
            yield

    @contextmanager
    def lock(self, name='registration.lock'):
        with self.operation(), (self.root/name).open('a') as handle:
            with self.stage('lock'):
                while True:
                    try:
                        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                        break
                    except BlockingIOError:
                        time.sleep(min(.02, remaining()))
            yield

    def serialized(self):
        return self.lock('application.lock')

    def load(self):
        value = read(self.path)
        if (set(value) != {'schema', 'node', 'records', 'observed_at'} or value['schema'] != 1
                or value['node'] != self.node or type(value['records']) is not dict
                or len(value['records']) > 10000 or self.clock() + policy.CLOCK_SKEW_SECONDS < value['observed_at']):
            raise ValueError('INVALID_GATEWAY_CACHE')
        for device, cached in value['records'].items():
            if (set(cached) != {'decision', 'boot', 'deadline', 'applied', 'prepared'}
                    or cached['prepared'] is not None and
                    (type(cached['prepared']) is not str or not re.fullmatch('[a-f0-9]{64}', cached['prepared']))):
                raise ValueError('INVALID_MEMBERSHIP_CACHE')
            decision = cached['decision']
            if device != decision['device']:
                raise ValueError('INVALID_GATEWAY_BINDING')
            policy.validate(dict(schema=1, profile=policy.PROFILE, node=self.node,
                observed_at=decision['observed_at'], decisions=[decision]), self.node, decision['observed_at'])
        return value

    def allowed(self, cached):
        decision = cached['decision']
        if not decision['allowed']:
            return False
        if not decision['cohort']:
            return not cached.get('prepared')
        return (cached['boot'] == boot_id() and self.clock() < decision['valid_until']
                and self.monotonic() < cached['deadline'])

    def accept(self, envelope):
        policy.validate(envelope, self.node, self.clock())
        state = self.load()
        for decision in envelope['decisions']:
            remaining()
            old = state['records'].get(decision['device'])
            policy.successor(old['decision'] if old else None, decision)
            for device, cached in state['records'].items():
                if device != decision['device'] and any(cached['decision'][name] == decision[name] for name in ('public_key', 'tcp_id')):
                    raise ValueError('DUPLICATE_GATEWAY_BINDING')
            if old and decision == old['decision']:
                continue
            state['records'][decision['device']] = dict(decision=decision, boot=boot_id(),
                deadline=self.monotonic() + min(policy.LEASE_SECONDS, max(0, decision['valid_until'] - self.clock())),
                applied=old.get('applied') if old else None, prepared=old.get('prepared') if old else None)
        state['observed_at'] = max(state['observed_at'], int(self.clock()))
        write(self.path, state)
        return state

    def prepare(self, envelope, token):
        if not isinstance(token, str) or not re.fullmatch('[a-f0-9]{64}', token) or len(envelope['decisions']) != 1:
            raise ValueError('INVALID_MEMBERSHIP_PREPARATION')
        state = self.accept(envelope)
        cached = state['records'][envelope['decisions'][0]['device']]
        if cached['decision']['cohort']:
            raise ValueError('MEMBERSHIP_OPERATION_CONFLICT')
        cached['prepared'] = token
        write(self.path, state)

    def peer_allowed(self, public):
        state = self.load()
        found = [cached for cached in state['records'].values() if cached['decision']['public_key'] == public]
        return not found or self.allowed(found[0])

    def stop_all(self):
        token = CURRENT_OPERATION.set(None)
        try:
            self.run(['systemctl', '--no-block', 'stop', *SERVICES])
        finally:
            CURRENT_OPERATION.reset(token)

    def failure(self):
        write(self.root/'transport-attempt.json', dict(schema=1, node=self.node,
            observed_at=int(self.clock()), result='error'))

    def fail_closed(self, error, mode):
        report_failure(error, mode, self.root)
        token = CURRENT_OPERATION.set(None)
        try:
            for action in (self.stop_all, self.failure):
                try:
                    action()
                except BaseException as cleanup:
                    emit(dict(transport_cleanup_failure=failure_record(cleanup, mode)))
        finally:
            CURRENT_OPERATION.reset(token)

    def apply(self, *, starting=False):
        if starting:
            with self.lock():
                self.plan()
            return
        with self.serialized():
            self.apply_serialized()

    def apply_serialized(self):
        for attempt in range(12):
            with self.lock():
                with self.stage('plan'):
                    state, peers, observations, changed = self.plan()
            if changed:
                with self.stage('restart_preflight'):
                    self.run(['systemctl', 'restart', SERVICES[1]])
            with self.lock():
                with self.stage('readback'):
                    if self.readback(state, peers, observations):
                        return
        raise ValueError('APPLICATION_DID_NOT_CONVERGE')

    def plan(self):
        state = self.load()
        tcp_path = self.root.parent / 'friends-tcp/server.json'
        info = tcp_path.stat()
        config = json.loads(tcp_path.read_text(), object_pairs_hook=unique)
        inbound = next(item for item in config['inbounds'] if item.get('tag') == 'friends')
        clients = inbound['settings']['clients']
        with self.gateway.database() as database:
            peers = {public: self.gateway.address(index) for index, public in database.execute('SELECT id,public FROM peers')}
        changed, observations = False, {}
        for device, cached in state['records'].items():
            remaining()
            decision = cached['decision']
            email = device + '@family.test'
            matching = [client for client in clients if client.get('email') == email or client.get('id') == decision['tcp_id']]
            expected = dict(id=decision['tcp_id'], email=email, flow='xtls-rprx-vision')
            if matching and matching != [expected]:
                raise ValueError('TCP_BINDING_CONFLICT')
            registered = decision['public_key'] in peers
            if not registered and matching:
                raise ValueError('INCOMPLETE_NODE_BINDING')
            allowed = self.allowed(cached)
            if not allowed and matching:
                clients.remove(matching[0])
                changed = True
            if allowed and registered and not matching:
                clients.append(expected)
                changed = True
            observations[device] = dict(expected_revision=decision['revision'], applied_revision=None,
                observed_at=int(self.clock()), registered=registered, allowed=registered and allowed, result='pending',
                reason='membership-pending' if cached.get('prepared') and not decision['cohort'] else
                    'canonical' if not decision['allowed'] else 'noncohort' if not decision['cohort'] else
                    'lease-expired' if not allowed else 'lease-valid')
        if changed:
            write(tcp_path, config, info.st_mode & 0o777)
            os.chown(tcp_path, info.st_uid, info.st_gid)
        return state, peers, observations, changed

    def readback(self, state, peers, observations):
        live = self.awg_snapshot()
        for device, cached in state['records'].items():
            decision, observation = cached['decision'], observations[device]
            public, allowed = decision['public_key'], observation['allowed']
            if public in peers:
                if allowed and live.get(public) != peers[public]:
                    with self.stage('actuation'):
                        self.gateway.add_peer(public, peers[public])
                elif not allowed and public in live:
                    with self.stage('actuation'):
                        self.run([str(self.root / 'awg'), 'set', self.gateway.IFACE, 'peer', public, 'remove'])
        tcp_by_email, tcp_by_id = self.tcp_snapshot()
        live = self.awg_snapshot()
        for device, cached in state['records'].items():
            decision, observation = cached['decision'], observations[device]
            public = decision['public_key']
            email = device+'@family.test'
            user = tcp_by_email.get(email)
            tcp_present = user is not None and user['account']['id'] == decision['tcp_id']
            if (user is not None or decision['tcp_id'] in tcp_by_id) and (
                    not tcp_present or user['account'].get('flow') != 'xtls-rprx-vision'):
                raise ValueError('ENGINE_READBACK_MISMATCH')
            awg_present = public in live
            expected = observation['allowed']
            if tcp_present != expected or awg_present != expected or expected and live[public] != peers[public]:
                if any(observations[key]['allowed'] != (observations[key]['registered'] and self.allowed(value))
                       for key, value in state['records'].items()):
                    return False
                raise ValueError('ENGINE_READBACK_MISMATCH')
            observation.update(applied_revision=decision['revision'], allowed=expected, result='applied')
            cached['applied'] = observation
        if any(observations[key]['allowed'] != (observations[key]['registered'] and self.allowed(value))
               for key, value in state['records'].items()):
            return False
        state['observed_at'] = int(self.clock())
        write(self.path, state)
        write(self.root/'transport-attempt.json', dict(schema=1, node=self.node,
            observed_at=int(self.clock()), result='applied'))
        return True

    def awg_snapshot(self):
        live = {}
        with self.stage('engine_query'):
            output = self.run([str(self.root / 'awg'), 'show', self.gateway.IFACE, 'allowed-ips']).decode()
        for line in output.splitlines():
            fields = line.split()
            if len(fields) != 2 or fields[0] in live:
                raise ValueError('INVALID_AWG_READBACK')
            live[fields[0]] = fields[1]
        return live

    def tcp_snapshot(self):
        with self.stage('engine_query'):
            runtime = json.loads(self.run([str(self.root.parent / 'friends-tcp/xray'), 'api', 'inbounduser',
                '--server=127.0.0.1:18085', '-tag=friends']), object_pairs_hook=unique)
        if type(runtime) is not dict or set(runtime) - {'users'} or type(runtime.get('users', [])) is not list:
            raise ValueError('INVALID_TCP_READBACK')
        users = runtime.get('users', [])
        emails, identities = {}, {}
        for user in users:
            if (type(user) is not dict or type(user.get('email')) is not str or not user['email']
                    or type(user.get('account')) is not dict or type(user['account'].get('id')) is not str
                    or not user['account']['id'] or user['email'] in emails or user['account']['id'] in identities):
                raise ValueError('INVALID_TCP_READBACK')
            emails[user['email']] = user
            identities[user['account']['id']] = user
        return emails, identities


def notify(value):
    address = os.environ.get('NOTIFY_SOCKET')
    if address:
        with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as channel:
            channel.connect('\0'+address[1:] if address.startswith('@') else address)
            channel.sendall(value.encode())


def watch(gateway, *, run=execute):
    engine = Gateway(gateway, run=run)
    try:
        engine.apply(starting=True)
        notify('READY=1')
        for attempt in range(15):
            try:
                with engine.operation():
                    for service in SERVICES:
                        engine.run(['systemctl', 'is-active', '--quiet', service])
                break
            except subprocess.SubprocessError:
                notify('WATCHDOG=1')
                time.sleep(policy.TICK_SECONDS)
        else:
            raise ValueError('ENGINE_START_TIMEOUT')
        previous = time.monotonic()
        while True:
            engine.apply()
            notify('WATCHDOG=1')
            current = time.monotonic()
            print(json.dumps(dict(transport_progress_gap=current-previous)), file=sys.stderr, flush=True)
            previous = current
            time.sleep(policy.TICK_SECONDS)
    except BaseException as error:
        engine.fail_closed(error, 'watch')
        raise
