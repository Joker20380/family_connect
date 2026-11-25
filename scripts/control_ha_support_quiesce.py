"""One-use reversible legacy application/RNS idle probe, never stop or capture."""
import argparse
from contextlib import ExitStack, contextmanager
import inspect
import json
import math
import os
from pathlib import Path
import runpy
import sys
import threading
import time


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def remaining(deadline):
    duration = deadline - time.monotonic()
    require(duration > 0, 'PROBE_EXPIRED')
    return duration


class Clock:
    def __init__(self, owner, original, codes):
        self.owner, self.original, self.codes = owner, original, codes

    def __getattr__(self, name):
        return getattr(self.original, name)

    def sleep(self, seconds):
        worker = threading.current_thread()
        if (not self.owner.armed or worker not in self.owner.producers or
                sys._getframe(1).f_code not in self.codes):
            return self.original.sleep(seconds)
        started = time.monotonic()
        try:
            with self.owner.lock:
                self.owner.parked.add(worker)
            self.owner.release.wait(max(0, self.owner.deadline - time.monotonic()))
        finally:
            with self.owner.lock:
                self.owner.parked.discard(worker)
        self.owner.resume(worker)
        self.original.sleep(max(0, seconds - (time.monotonic() - started)))


class RuntimePause:
    def __init__(self, contract, delivery, deadline):
        self.contract, self.delivery, self.deadline = contract, delivery, deadline
        self.lock = threading.RLock()
        self.release, self.failed = threading.Event(), threading.Event()
        self.parked, self.queue_parked = set(), set()
        self.freeze_queue = False
        self.armed = False
        self.restore = ExitStack()

    def patch(self, owner, name, replacement):
        original = inspect.getattr_static(owner, name)
        self.restore.callback(setattr, owner, name, original)
        setattr(owner, name, replacement)

    def resume(self, worker):
        pass

    def expected_exit(self, arguments):
        return False

    @contextmanager
    def queue_lock(self):
        require(self.condition.acquire(timeout=remaining(self.deadline)), 'RNS_QUEUE_BUSY')
        try:
            yield
        finally:
            self.condition.release()

    def __enter__(self):
        modules = self.contract['verify_code']()
        self.rns = self.contract['RNS']
        runtime = self.rns.Reticulum.get_instance()
        transport = self.rns.Transport
        require(runtime is not None and runtime.is_standalone_instance and
                not runtime.is_connected_to_shared_instance and not self.rns.Reticulum.transport_enabled() and
                not self.rns.Reticulum._Reticulum__exit_handler_ran and transport._should_run,
                'RNS_RUNTIME_SHAPE')
        require(transport.USE_INBOUND_QUEUE and not transport.USE_OUTBOUND_QUEUE and
                type(transport.inbound_queues) is modules['RNS.Transport'].InboundQueues,
                'RNS_QUEUE_SHAPE')
        periodic = self.rns.Reticulum._Reticulum__jobs
        functions = (periodic, transport.jobloop, transport.count_traffic_loop, transport.inbound_job)
        found = {function: [] for function in functions}
        for worker in threading.enumerate():
            target = getattr(worker, '_target', None)
            function = getattr(target, '__func__', target)
            if function in found:
                if function is periodic:
                    require(getattr(target, '__self__', None) is runtime, 'RNS_THREAD_OWNER')
                found[function].append(worker)
        require(all(len(workers) == 1 for workers in found.values()), 'RNS_THREAD_SHAPE')
        self.producers = {found[function][0] for function in functions[:3]}
        self.queues = {found[transport.inbound_job][0]}
        self.condition = transport.inbound_queues._cond
        require(type(self.condition) is threading.Condition and 'wait' not in vars(self.condition),
                'RNS_QUEUE_CONDITION')
        original_wait = self.condition.wait
        get_code = modules['RNS.Transport'].InboundQueues.get.__code__

        def wait(timeout=None):
            worker = threading.current_thread()
            if worker not in self.queues or sys._getframe(1).f_code is not get_code:
                return original_wait(timeout)
            started = time.monotonic()
            try:
                while True:
                    with self.lock:
                        freeze = (self.freeze_queue and not self.release.is_set() and
                                  time.monotonic() < self.deadline)
                        if freeze:
                            self.queue_parked.add(worker)
                    if not freeze:
                        self.resume(worker)
                        duration = .05 if timeout is None else max(0, min(.05, timeout))
                        return original_wait(duration)
                    original_wait(.05)
                    if timeout is not None and time.monotonic() - started >= timeout:
                        return False
            finally:
                with self.lock:
                    self.queue_parked.discard(worker)

        try:
            self.condition.wait = wait
            self.restore.callback(delattr, self.condition, 'wait')
            reticulum, transport_module = modules['RNS.Reticulum'], modules['RNS.Transport']
            self.patch(reticulum, 'time', Clock(self, reticulum.time, {periodic.__code__}))
            self.patch(transport_module, 'time', Clock(self, transport_module.time,
                                                     {transport.count_traffic_loop.__code__}))
            self.patch(transport_module, 'sleep', Clock(self, time, {transport.jobloop.__code__}).sleep)
            original_log, original_hook = self.rns.log, threading.excepthook

            def log(message, level=3, *args, **kwargs):
                if level in (self.rns.LOG_CRITICAL, self.rns.LOG_ERROR):
                    self.failed.set()
                return original_log(message, level, *args, **kwargs)

            def thread_error(arguments):
                if self.expected_exit(arguments):
                    return
                self.failed.set()
                original_hook(arguments)

            self.patch(self.rns, 'log', log)
            self.patch(threading, 'excepthook', thread_error)
            with self.queue_lock():
                self.condition.notify_all()
        except BaseException:
            self.__exit__(*sys.exc_info())
            raise
        return self

    def ready(self):
        transport = self.rns.Transport
        expected = {threading.main_thread(), self.delivery._worker, *self.producers, *self.queues}
        with self.queue_lock(), self.lock:
            observed = set(threading.enumerate())
            native = {int(path.name) for path in Path('/proc/self/task').iterdir()}
            require(not self.failed.is_set(), 'RNS_WORK_UNCERTAIN')
            require(self.producers | self.queues <= observed, 'RNS_WORKER_LOST')
            quiet = (observed == expected and native == {worker.native_id for worker in expected} and
                     self.parked == self.producers and not transport.interfaces and
                     not transport.local_client_interfaces and not transport.active_links and
                     not transport.pending_links and transport.inbound_queues.qsize() == 0 and
                     not any(path.joinpath('children').read_text().strip()
                             for path in Path('/proc/self/task').iterdir()))
            self.freeze_queue = quiet
            self.condition.notify_all()
            return quiet and self.queue_parked == self.queues

    def drain(self):
        while not self.ready():
            time.sleep(min(.02, remaining(self.deadline)))

    def __exit__(self, *_):
        self.release.set()
        self.restore.close()
        if self.condition.acquire(timeout=.1):
            try:
                self.condition.notify_all()
            finally:
                self.condition.release()
        deadline = time.monotonic() + 2
        while True:
            with self.lock:
                if not self.parked and not self.queue_parked:
                    break
            time.sleep(min(.01, remaining(deadline)))


def prepare(pid, root, output, *, seconds=360, hold=.25):
    from scripts import control_ha_legacy_support as admission

    require(sys.version_info[:2] == (3, 14) and hasattr(sys, 'remote_exec'), 'CPYTHON_314_REQUIRED')
    require(type(seconds) in (float, int) and math.isfinite(seconds) and .5 <= seconds <= 360 and
            type(hold) in (float, int) and math.isfinite(hold) and 0 <= hold <= 10 and hold < seconds,
            'REQUEST_TIME')
    root, output = Path(root).absolute(), Path(output).absolute()
    repo = Path(__file__).resolve().parents[1]
    expected = json.loads(admission.read(repo / 'deploy/support-chat/support-capture-v1.json'))['baseline']
    admission.sources(root, expected)
    observed = admission.binding(pid)
    require(not any(path.is_symlink() for path in (output, *output.parents)), 'OUTPUT_SYMLINK')
    admission.visible_to(pid, output.parent)
    output.mkdir(mode=0o700, exist_ok=False)
    files = {'probe.py': Path(__file__), 'admission.py': Path(admission.__file__),
             'runtime.py': repo / 'provisioning/support_runtime.py'}
    hashes = {}
    for name, source in files.items():
        raw = admission.read(source)
        hashes[name] = admission.digest(raw)
        with (output / name).open('xb') as target:
            os.fchmod(target.fileno(), 0o600)
            target.write(raw)
            target.flush()
            os.fsync(target.fileno())
    request = dict(binding=observed, root=str(root), output=str(output), baseline=expected,
                   hashes=hashes, deadline=time.monotonic() + seconds, hold=hold)
    admission.write(output / 'request.json', request)
    launcher = ('import hashlib,pathlib,runpy\n'
                f'root=pathlib.Path({str(output)!r})\n'
                f'assert all(hashlib.sha256((root/name).read_bytes()).hexdigest()==digest for name,digest in {hashes!r}.items())\n'
                'runpy.run_path(str(root/"probe.py"))["execute"](root/"request.json")\n')
    with (output / 'invoke.py').open('xb') as target:
        os.fchmod(target.fileno(), 0o600)
        target.write(launcher.encode())
        target.flush()
        os.fsync(target.fileno())
    admission.write(output / 'prepared.json', dict(binding=observed, submitted=False, capture_permitted=False))
    for path in (output, *output.iterdir()):
        admission.visible_to(pid, path)
    require(admission.binding(pid) == observed, 'PID_CHANGED')
    return output / 'invoke.py'


def execute(path):
    output = Path(path).parent
    admission = runpy.run_path(str(output / 'admission.py'))
    read, write = admission['read'], admission['write']
    delivery, paused, runtime_restored = None, False, False
    try:
        require(output.stat().st_uid == os.geteuid() and output.stat().st_mode & 0o777 == 0o700,
                'PRIVATE_OUTPUT')
        write(output / 'claimed.json', dict(pid=os.getpid()))
        request = json.loads(read(path, 32768))
        require(set(request) == {'binding', 'root', 'output', 'baseline', 'hashes', 'deadline', 'hold'},
                'REQUEST_FIELDS')
        require(request['output'] == str(output) and admission['binding'](os.getpid()) == request['binding'],
                'PROCESS_BINDING')
        require(type(request['deadline']) in (int, float) and math.isfinite(request['deadline']) and
                0 < remaining(request['deadline']) <= 360 and type(request['hold']) in (int, float) and
                math.isfinite(request['hold']) and 0 <= request['hold'] <= 10, 'REQUEST_TIME')
        require(set(request['hashes']) == {'probe.py', 'admission.py', 'runtime.py'} and
                all(admission['digest'](read(output / name)) == digest
                    for name, digest in request['hashes'].items()), 'PROBE_PIN')
        contract = runpy.run_path(str(output / 'runtime.py'))
        content = admission['sources'](request['root'], request['baseline'])
        delivery, stopped = admission['context'](request['root'], content)
        require(delivery._condition.acquire(timeout=remaining(request['deadline'])), 'CONDITION_BUSY')
        try:
            require(not delivery._closed, 'DELIVERY_CLOSED')
            online = delivery._online
            delivery._online = False
            paused = True
        finally:
            delivery._condition.release()
        with RuntimePause(contract, delivery, request['deadline']) as runtime:
            write(output / 'entered.json', dict(application_paused=True, cancellation_requested=False,
                                                capture_permitted=False))
            with delivery._condition:
                while delivery._cancel is not None:
                    delivery._condition.wait(remaining(request['deadline']))
            runtime.armed = True
            runtime.drain()
            require(not stopped.is_set() and remaining(request['deadline']) > request['hold'],
                    'STOP_OR_EXPIRY')
            write(output / 'quiesced.json', dict(application_drained=True, rns_idle_paused=True,
                  producers=len(runtime.producers), queues=len(runtime.queues), exit_persisted=False,
                  external_settlement_proven=False, capture_permitted=False))
            deadline = time.monotonic() + request['hold']
            while time.monotonic() < deadline:
                require(runtime.ready() and not stopped.is_set(), 'QUIESCENCE_LOST')
                time.sleep(min(.02, remaining(request['deadline'])))
        runtime_restored = True
    except BaseException as error:
        reason = str(error) if type(error) is ValueError and str(error).isupper() else 'PROBE_FAILURE'
        try:
            write(output / 'error.json', dict(reason=reason, capture_permitted=False))
        except BaseException:
            pass
    finally:
        if paused:
            with delivery._condition:
                delivery._online = online
                delivery._condition.notify_all()
            try:
                write(output / 'restored.json', dict(pid=os.getpid(), delivery_online=online,
                      runtime_probe_completed=runtime_restored, capture_permitted=False))
            except BaseException:
                pass


def main():
    from scripts import control_ha_legacy_support as admission

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pid', required=True, type=int)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--seconds', type=float, default=360)
    parser.add_argument('--hold', type=float, default=.25)
    args = parser.parse_args()
    launcher = prepare(args.pid, args.root, args.output, seconds=args.seconds, hold=args.hold)
    sys.remote_exec(args.pid, str(launcher))
    deadline = time.monotonic() + args.seconds + 5
    while not (args.output / 'restored.json').exists():
        if (args.output / 'error.json').exists() and not (args.output / 'entered.json').exists():
            raise SystemExit('PROBE_REFUSED')
        if time.monotonic() >= deadline:
            raise SystemExit('PROBE_OUTCOME_UNKNOWN_NO_RETRY')
        time.sleep(.05)
    if (args.output / 'error.json').exists() or not (args.output / 'quiesced.json').exists():
        raise SystemExit('PROBE_NOT_QUALIFIED')
    request = json.loads(admission.read(args.output / 'request.json'))
    restored = json.loads(admission.read(args.output / 'restored.json'))
    require(restored == dict(pid=args.pid, delivery_online=True, runtime_probe_completed=True,
                            capture_permitted=False), 'RESTORATION_NOT_QUALIFIED')
    require(admission.binding(args.pid) == request['binding'], 'PID_CHANGED')
    admission.sources(args.root, request['baseline'])
    admission.write(args.output / 'completed.json', dict(binding=request['binding'],
                    same_process_and_sources=True, capture_permitted=False))
    print('REVERSIBLE_RNS_IDLE_PROBE_PASS_NO_CAPTURE')


if __name__ == '__main__':
    main()
