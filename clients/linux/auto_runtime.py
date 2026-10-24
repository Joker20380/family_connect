"""Service-lifetime driver for the native Auto controller and real platform host."""
import copy
import threading
import time

from auto_policy import Context, Failure, GuardedHost, PolicyProcess, require, snapshot
from backend import RecoveryPolicy


class Coordinator:
    def __init__(self, guard, platform, generation, *, worker=None, process_factory=PolicyProcess,
                 clock=time.monotonic, terminal=None, guard_prepared=False):
        self.guard, self.platform, self.generation = guard, platform, generation
        self.host = GuardedHost(guard, platform, generation, guard_prepared=guard_prepared)
        self.process_factory, self.worker, self.clock, self.terminal = process_factory, worker, clock, terminal
        self.lock = threading.Lock()
        self.wake = threading.Event()
        self.abandon = threading.Event()
        self.process, self.thread, self.operation, self.disconnect = None, None, None, None
        self.stopping, self.failed, self.probe = False, False, None
        self.view = dict(generation=generation, state='DISCONNECTED', desired_connected=False,
                         retry_at_ms=0, events=[], events_dropped=0)
        self.next_health, self.terminal_reported = 0, False

    def start(self, preferred='', last_good=''):
        initial_network = self.network()
        with self.lock:
            require(self.thread is None and not self.stopping)
            arguments = {} if self.worker is None else dict(worker=self.worker)
            self.process = self.process_factory(self.host, **arguments)
            try:
                self.operation = self.process.submit('connect', self.generation, network=initial_network is not None,
                                                     preferred=preferred, last_good=last_good)
                self.view.update(state='CONNECTING', desired_connected=True)
                self.thread = threading.Thread(target=self.run, name='fc-auto-coordinator', daemon=False)
                self.thread.start()
            except Exception:
                self.process.close()
                raise

    def status(self):
        with self.lock:
            value = copy.deepcopy(self.view)
        return dict(policy=value, platform=self.platform.snapshot(), mesh=self.platform.mesh.snapshot())

    def request_disconnect(self):
        self.platform.cancel_health()
        with self.lock:
            if self.stopping:
                return
            self.stopping = True
            if self.probe is not None:
                self.probe.cancel.set()
            if self.process is not None and not self.failed:
                self.view.update(state='DISCONNECTING', desired_connected=False)
                self.disconnect = self.process.submit('disconnect', self.generation)
            self.wake.set()

    def accept(self, ticket):
        reply = ticket.wait(4)
        require(reply['ok'])
        value = snapshot(reply['snapshot'])
        require(value['generation'] in (0, self.generation))
        if value['generation'] == self.generation:
            with self.lock:
                self.view = value
                if self.stopping and value['state'] in ('CONNECTED', 'CONNECTING', 'RESTORING'):
                    self.view = dict(value, state='DISCONNECTING', desired_connected=False)
        return value

    def network(self):
        context = Context(5000)
        with self.lock:
            if self.stopping:
                return None
            self.probe = context
        try:
            return self.platform.underlying.read(context)
        except Failure as failure:
            if failure.category not in ('NETWORK', 'CANCELLED'):
                raise
            return None
        finally:
            with self.lock:
                self.probe = None

    def tick(self):
        with self.lock:
            operation, disconnect = self.operation, self.disconnect
        if operation is not None and operation.done.is_set():
            self.accept(operation)
            with self.lock:
                self.operation = None
        if disconnect is not None and disconnect.done.is_set():
            value = self.accept(disconnect)
            require(value['state'] in ('DISCONNECTED', 'FAILED'))
            return True
        value = self.accept(self.process.submit('status'))
        with self.lock:
            if self.stopping:
                return False
            operation = self.operation
        if value['state'] == 'FAILED' and not value['desired_connected']:
            if not self.terminal_reported and self.terminal is not None:
                self.terminal()
                self.terminal_reported = True
            return False
        path = self.network()
        with self.lock:
            if self.stopping:
                return False
        self.accept(self.process.submit('network', self.generation, network=path is not None))
        if operation is not None:
            return False
        if value['state'] == 'RESTORING':
            with self.lock:
                if not self.stopping:
                    self.operation = self.process.submit('retry', self.generation)
        elif value['state'] == 'CONNECTED':
            failure = None
            changed = path is None or self.platform.network_matches(path) is False
            if changed:
                failure = 'NETWORK'
            elif self.clock() >= self.next_health:
                self.next_health = self.clock() + RecoveryPolicy.interval
                try:
                    self.platform.health(Context(20000))
                except Failure as error:
                    failure = error.category
                with self.lock:
                    if self.stopping:
                        return False
                if failure is None:
                    self.accept(self.process.submit('healthy', self.generation, healthy=True))
            with self.lock:
                if failure is not None and not self.stopping:
                    self.operation = self.process.submit('lost', self.generation, reason=failure)
        return False

    def run(self):
        try:
            while not self.abandon.is_set() and not self.tick():
                self.wake.wait(1)
                self.wake.clear()
        except Exception:
            with self.lock:
                self.failed = True
                self.view.update(state='FAILED', first_reason=self.view.get('first_reason') or 'INTERNAL')
        finally:
            self.platform.cancel_health()
            try:
                self.process.close()
            except Exception:
                with self.lock:
                    self.failed = True
                    self.view.update(state='FAILED', desired_connected=False,
                                     first_reason=self.view.get('first_reason') or 'INTERNAL')

    def close(self):
        self.request_disconnect()
        if self.thread is not None:
            self.thread.join(timeout=35)
            if self.thread.is_alive():
                raise Failure('INTERNAL')
        with self.lock:
            if self.failed or self.view['state'] != 'DISCONNECTED':
                raise Failure('INTERNAL')

    def abort(self):
        self.abandon.set()
        self.platform.cancel_health()
        with self.lock:
            if self.probe is not None:
                self.probe.cancel.set()
        self.wake.set()
        if self.thread is not None:
            self.thread.join(timeout=35)
            if self.thread.is_alive():
                raise Failure('INTERNAL')
        with self.lock:
            if self.failed:
                raise Failure('INTERNAL')
