"""Root-internal adapter to the shared Go policy; no unprivileged command server."""
import copy
import os
import queue
import re
import subprocess
import threading
import time

import mesh_ipc as ipc
from mesh_system import ENV

WORKER = '/usr/local/lib/family-connect-mesh/fc-mesh'
MAX_FRAME = 32768
MAX_ID = 2**53 - 1
CANDIDATES = frozenset(('wg', 'awg', 'tcp', 'restricted'))
FAILURES = frozenset(('CANCELLED', 'AUTH', 'CONFIGURATION', 'NETWORK', 'TRANSPORT_UNAVAILABLE',
                      'BOOTSTRAP_UNAVAILABLE', 'INTERNAL'))
STATES = frozenset(('DISCONNECTED', 'CONNECTING', 'CONNECTED', 'RESTORING', 'FAILED', 'DISCONNECTING'))


class Failure(RuntimeError):
    def __init__(self, category='INTERNAL', temporary=False):
        if category not in FAILURES or type(temporary) is not bool or (temporary and category != 'BOOTSTRAP_UNAVAILABLE'):
            category, temporary = 'INTERNAL', False
        self.category, self.temporary = category, temporary
        super().__init__(category)


def require(condition):
    if not condition:
        raise ipc.ProtocolError()


def number(value, minimum=0, maximum=MAX_ID):
    return type(value) is int and minimum <= value <= maximum


def snapshot(value):
    require(isinstance(value, dict) and {'generation', 'state', 'desired_connected', 'retry_at_ms', 'events', 'events_dropped'} <= set(value))
    require(not set(value) - {'generation', 'state', 'selected', 'desired_connected', 'first_reason', 'retry_at_ms', 'events', 'events_dropped'})
    require(number(value['generation']) and value['state'] in STATES and type(value['desired_connected']) is bool)
    require(value.get('selected', '') in CANDIDATES | {''} and value.get('first_reason', '') in FAILURES | {''})
    require(number(value['retry_at_ms'], maximum=2**63-1) and number(value['events_dropped'], maximum=2**64-1))
    events = value['events']
    require(events is None or isinstance(events, list) and len(events) <= 128)
    for event in events or []:
        require(isinstance(event, dict) and {'event', 'state', 'elapsed_ms'} <= set(event))
        require(not set(event) - {'event', 'state', 'elapsed_ms', 'candidate', 'category'})
        require(isinstance(event['event'], str) and re.fullmatch('[a-z_]{1,48}', event['event']) is not None)
        require(event['state'] in STATES and number(event['elapsed_ms'], maximum=2**63-1))
        require(event.get('candidate', '') in CANDIDATES | {''} and event.get('category', '') in FAILURES | {''})
    return copy.deepcopy(value)


def validate_frame(frame):
    require(isinstance(frame, dict) and len(frame) == 1)
    kind, value = next(iter(frame.items()))
    require(isinstance(value, dict) and value.get('schema') == 1 and type(value['schema']) is int and number(value.get('id'), 1))
    if kind == 'reply':
        require({'schema', 'id', 'ok', 'snapshot'} <= set(value) and not set(value) - {'schema', 'id', 'ok', 'error', 'snapshot'})
        require(type(value['ok']) is bool and value.get('error', '') in ('', 'BUSY', 'STALE', 'INVALID', 'INTERNAL'))
        require(value['ok'] == (value.get('error', '') == ''))
        snapshot(value['snapshot'])
    elif kind == 'host_cancel':
        require(set(value) == {'schema', 'id'})
    elif kind == 'host_call':
        require({'schema', 'id', 'generation', 'operation', 'budget_ms'} <= set(value))
        require(not set(value) - {'schema', 'id', 'generation', 'operation', 'budget_ms', 'candidate'})
        require(number(value['generation'], 1))
        operation = value['operation']
        require(operation in ('configure', 'open', 'close', 'release', 'remember'))
        if operation in ('open', 'remember'):
            require(value.get('candidate') in CANDIDATES)
            require(operation != 'remember' or value['candidate'] != 'restricted')
        else:
            require('candidate' not in value)
        limit = 30000 if operation == 'configure' else 20000
        if operation == 'open' and value['candidate'] == 'restricted':
            limit = 200000
        require(number(value['budget_ms'], 1, limit))
    else:
        raise ipc.ProtocolError()
    return kind, value


class Context:
    def __init__(self, budget_ms):
        self.deadline = time.monotonic() + budget_ms / 1000
        self.cancel = threading.Event()

    def check(self):
        if self.cancel.is_set():
            raise Failure('CANCELLED')
        if time.monotonic() >= self.deadline:
            raise Failure('NETWORK')


class GuardedHost:
    def __init__(self, guard, platform, generation, *, guard_prepared=False):
        require(number(generation, 1))
        self.guard, self.platform, self.generation = guard, platform, generation
        self.released = False
        self.guard_prepared, self.configured = guard_prepared, False

    def call(self, request, context):
        require(request['generation'] == self.generation and not self.released)
        context.check()
        action = request['operation']
        if action == 'configure':
            require(not self.configured)
            self.configured = True
            if self.guard_prepared:
                self.guard.block()
            else:
                self.guard.acquire()
            result = self.platform.configure(context)
            require(isinstance(result, list) and len(result) <= 3 and len(set(result)) == len(result))
            require(all(candidate in ('wg', 'awg', 'tcp') for candidate in result))
            context.check()
            return result
        if action == 'open':
            selected = request['candidate']
            try:
                plan = self.platform.prepare(context, selected)
                context.check()
                require(isinstance(plan, dict) and plan.get('kind') == {'restricted': 'mesh', 'wg': 'wg', 'awg': 'awg', 'tcp': 'tcp'}.get(selected))
                self.guard.prepare(plan)
                index, ipv6 = self.platform.open(context, selected)
                context.check()
                self.guard.ready(index, ipv6)
                context.check()
                applied = getattr(self.platform, 'applied', None)
                if applied is not None:
                    applied(context, selected)
                context.check()
                return []
            except Exception:
                cancel_health = getattr(self.platform, 'cancel_health', None)
                if cancel_health is not None:
                    cancel_health()
                raise
        elif action == 'close':
            if self.guard.record is not None:
                self.guard.block()
                self.platform.close(context)
        elif action == 'release':
            if self.guard.record is not None:
                self.platform.release(context)
                context.check()
                self.guard.release()
            self.released = True
        elif action == 'remember':
            self.platform.remember(context, request['candidate'])
        else:
            raise ipc.ProtocolError()
        context.check()
        return []

    def abort(self):
        if not self.released and self.guard.record is not None:
            self.guard.block()
            self.platform.close(Context(20000))


class Ticket:
    def __init__(self, identifier):
        self.identifier = identifier
        self.done = threading.Event()
        self.reply = None
        self.failed = False

    def wait(self, timeout):
        if not self.done.wait(timeout):
            raise TimeoutError('Auto reply pending; do not replay the operation')
        if self.failed:
            raise Failure()
        return copy.deepcopy(self.reply)


class PolicyProcess:
    def __init__(self, host, worker=WORKER):
        if os.geteuid() != 0:
            raise PermissionError('Root Auto coordinator required')
        self.host = host
        self.lock, self.write_lock = threading.Lock(), threading.Lock()
        self.stopping = threading.Event()
        self.identifier, self.last_call, self.completed_call = 0, 0, 0
        self.pending, self.active = {}, None
        self.work = queue.Queue(maxsize=1)
        self.abort_failed = False
        self.process = subprocess.Popen([worker, '--auto-stdio'], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.DEVNULL, env=ENV, bufsize=0, close_fds=True)
        self.reader = threading.Thread(target=self._read, name='fc-auto-policy-reader', daemon=False)
        self.operator = threading.Thread(target=self._operate, name='fc-auto-host', daemon=False)
        self.reader.start()
        self.operator.start()

    def submit(self, action, generation=0, **arguments):
        require(action in ('connect', 'status', 'network', 'disconnect', 'retry', 'lost', 'healthy'))
        require(number(generation) and (action == 'status') == (generation == 0))
        fields = {'connect': {'network', 'preferred', 'last_good'}, 'network': {'network'},
                  'lost': {'reason'}, 'healthy': {'healthy'}}.get(action, set())
        require(not set(arguments) - fields)
        if action in ('connect', 'network'):
            require(type(arguments.get('network')) is bool)
        if action == 'healthy':
            require(type(arguments.get('healthy')) is bool)
        if action == 'lost':
            require(arguments.get('reason') in FAILURES)
        for key in ('preferred', 'last_good'):
            require(arguments.get(key, '') in CANDIDATES | {''})
        with self.write_lock:
            with self.lock:
                if self.stopping.is_set() or self.identifier >= MAX_ID or len(self.pending) >= 4:
                    raise Failure()
                self.identifier += 1
                ticket = Ticket(self.identifier)
                self.pending[ticket.identifier] = ticket
            command = dict(schema=1, id=ticket.identifier, action=action, **arguments)
            if generation:
                command['generation'] = generation
            try:
                self._send(dict(command=command))
            except Exception:
                self._fail()
                raise Failure() from None
        return ticket

    def _send(self, frame):
        ipc.send(self.process.stdin.fileno(), frame, MAX_FRAME, time.monotonic() + 4, self.stopping)

    def _fail(self):
        self.stopping.set()
        with self.lock:
            if self.active is not None:
                self.active[1].cancel.set()
            for ticket in self.pending.values():
                ticket.failed = True
                ticket.done.set()
            self.pending.clear()

    def _read(self):
        try:
            while not self.stopping.is_set():
                try:
                    frame = ipc.receive(self.process.stdout.fileno(), MAX_FRAME, time.monotonic() + 3600, self.stopping)
                except TimeoutError:
                    continue
                kind, value = validate_frame(frame)
                with self.lock:
                    if kind == 'reply':
                        require(value['id'] in self.pending)
                        ticket = self.pending.pop(value['id'])
                        ticket.reply = value
                        ticket.done.set()
                    elif kind == 'host_cancel':
                        if self.active is not None and self.active[0]['id'] == value['id']:
                            self.active[1].cancel.set()
                        else:
                            require(value['id'] == self.completed_call)
                    else:
                        require(self.active is None and value['id'] > self.last_call)
                        self.last_call = value['id']
                        self.active = (value, Context(value['budget_ms']))
                        self.work.put_nowait(self.active)
        except Exception:
            pass
        finally:
            self._fail()

    def _operate(self):
        try:
            while not self.stopping.is_set():
                try:
                    request, context = self.work.get(timeout=.1)
                except queue.Empty:
                    continue
                reply = dict(schema=1, id=request['id'], ok=False, failure='INTERNAL')
                try:
                    result = self.host.call(request, context)
                    context.check()
                    require(isinstance(result, list) and len(result) <= 3)
                    require(not result or request['operation'] == 'configure')
                    require(all(candidate in ('wg', 'awg', 'tcp') for candidate in result) and len(set(result)) == len(result))
                    reply = dict(schema=1, id=request['id'], ok=True)
                    if result:
                        reply['candidates'] = result
                except Failure as failure:
                    reply = dict(schema=1, id=request['id'], ok=False, failure=failure.category)
                    if failure.temporary:
                        reply['temporary_bootstrap'] = True
                except Exception:
                    pass
                with self.lock:
                    self.completed_call = request['id']
                    self.active = None
                if self.stopping.is_set():
                    break
                with self.write_lock:
                    self._send(dict(host_reply=reply))
        except Exception:
            self._fail()
        finally:
            try:
                self.host.abort()
            except Exception:
                self.abort_failed = True

    def close(self):
        self._fail()
        if self.process.poll() is None:
            self.process.terminate()
        try:
            self.process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=2)
        self.reader.join(timeout=2)
        self.operator.join(timeout=22)
        self.process.stdin.close()
        self.process.stdout.close()
        if self.reader.is_alive() or self.operator.is_alive() or self.abort_failed:
            raise Failure()
