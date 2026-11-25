"""Opt-in lifecycle owner for the pinned standalone support Reticulum runtime."""
from contextlib import ExitStack
import atexit
import hashlib
import importlib
import inspect
import os
from pathlib import Path
from queue import Empty
import stat
import sys
import threading
import time
import types

import RNS

PINS = {
    'RNS': 'ed6cd970da6e19a0fdc34aae74897f876917879eb02cf6aacc86eb9ae13ebbd9',
    'RNS.Reticulum': 'e7c8908081132a6ca26593a833a5a41cb1bedaf45713958a1cac870b758f5fc7',
    'RNS.Transport': '97224d31475741e2d943779ce497853140344f5c9898afcaa9b87ddc937b2340',
    'RNS.Identity': '447d6a8406ab0f824c9c6488de1f14434003d21bdfef65d33d79b20d8a2698e3',
}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def code_tree(code):
    yield code
    for value in code.co_consts:
        if isinstance(value, types.CodeType):
            yield from code_tree(value)


def verify_code():
    require(threading.current_thread() is threading.main_thread() and not sys.flags.optimize,
            'RNS_MAIN_THREAD_REQUIRED')
    modules = {name: importlib.import_module(name) for name in PINS}
    compiled = {}
    for name, module in modules.items():
        path = Path(module.__file__)
        require(path.suffix == '.py' and not path.is_symlink(), 'RNS_SOURCE_SHAPE')
        raw = path.read_bytes()
        require(hashlib.sha256(raw).hexdigest() == PINS[name], 'RNS_SOURCE_PIN')
        compiled[name] = list(code_tree(compile(raw, str(path), 'exec')))
    functions = [RNS.log, RNS._detach_stdout, RNS.Reticulum._Reticulum__jobs, RNS.Reticulum.exit_handler,
                 RNS.Reticulum._Reticulum__persist_data, RNS.Reticulum._Reticulum__clean_caches,
                 RNS.Transport.jobloop, RNS.Transport.count_traffic_loop, RNS.Transport.inbound_job,
                 RNS.Transport.exit_handler, RNS.Transport.persist_data,
                 RNS.Identity.exit_handler, RNS.Identity.persist_data,
                 RNS.Identity.save_known_destinations, modules['RNS.Transport'].InboundQueues.get]
    for function in functions:
        require(isinstance(function, types.FunctionType) and function.__module__ in compiled,
                'RNS_LOADED_CODE')
        candidates = [code for code in compiled[function.__module__]
                      if code.co_qualname == function.__qualname__]
        require(len(candidates) == 1 and function.__code__ == candidates[0] and
                function.__code__.co_filename == modules[function.__module__].__file__, 'RNS_LOADED_CODE')
    return modules


def verify():
    modules = verify_code()
    require(RNS.Reticulum.get_instance() is None and len(threading.enumerate()) == 1,
            'RNS_ALREADY_OWNED')
    require({int(path.name) for path in Path('/proc/self/task').iterdir()} ==
            {threading.main_thread().native_id}, 'RNS_ALREADY_OWNED')
    require(RNS.Transport.USE_INBOUND_QUEUE and not RNS.Transport.USE_OUTBOUND_QUEUE,
            'RNS_QUEUE_SHAPE')
    return modules


def state_paths(root):
    require(not any(path.is_symlink() for path in (root, *root.parents)), 'RNS_STATE_PATH')
    paths = [root, *root.rglob('*')]
    for path in paths:
        info = path.lstat()
        directory = stat.S_ISDIR(info.st_mode)
        require((directory or stat.S_ISREG(info.st_mode) and info.st_nlink == 1) and
                info.st_uid == os.getuid() and not info.st_mode & 0o022, 'RNS_STATE_SHAPE')
    return paths


def sync_tree(root):
    for path in reversed(state_paths(root)):
        info = path.lstat()
        directory = stat.S_ISDIR(info.st_mode)
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK |
                             (os.O_DIRECTORY if directory else 0))
        try:
            opened = os.fstat(descriptor)
            require((opened.st_dev, opened.st_ino) == (info.st_dev, info.st_ino), 'RNS_STATE_CHANGED')
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


class _Stopped(BaseException):
    pass


class _Clock:
    def __init__(self, owner, original, codes):
        self.owner, self.original, self.codes = owner, original, codes

    def __getattr__(self, name):
        return getattr(self.original, name)

    def sleep(self, seconds):
        if sys._getframe(1).f_code not in self.codes:
            return self.original.sleep(seconds)
        if self.owner.producers_stop.wait(seconds):
            raise _Stopped()


class ManagedRuntime:
    def __init__(self, gate):
        self.gate = gate
        self.condition = threading.RLock()
        self.producers_stop = threading.Event()
        self.queues_stop = False
        self.loops, self.idle = {}, set()
        self.failed = threading.Event()
        self.restore = ExitStack()
        self.root = None
        self.root_pin = None
        self.closed = False

    def patch(self, owner, name, replacement):
        original = inspect.getattr_static(owner, name)
        self.restore.callback(setattr, owner, name, original)
        setattr(owner, name, replacement)

    def loop(self, function, kind):
        def run(*args, **kwargs):
            worker = threading.current_thread()
            with self.condition:
                self.loops[worker] = kind
            try:
                result = function(*args, **kwargs)
                if not self.producers_stop.is_set():
                    self.failed.set()
                return result
            except _Stopped:
                require(self.producers_stop.is_set(), 'RNS_UNEXPECTED_STOP')
            except BaseException:
                self.failed.set()
                raise
            finally:
                with self.condition:
                    self.idle.discard(worker)
        return run

    def __enter__(self):
        modules = verify()
        self.operation = self.gate.operation()
        self.admitted = self.operation.__enter__()
        try:
            periodic = RNS.Reticulum._Reticulum__jobs
            jobs, traffic = RNS.Transport.jobloop, RNS.Transport.count_traffic_loop
            reticulum, transport = modules['RNS.Reticulum'], modules['RNS.Transport']
            self.patch(reticulum, 'time', _Clock(self, reticulum.time, {periodic.__code__}))
            self.patch(transport, 'time', _Clock(self, transport.time, {traffic.__code__}))
            clock = _Clock(self, time, {jobs.__code__})
            self.patch(transport, 'sleep', clock.sleep)
            self.patch(RNS.Reticulum, '_Reticulum__jobs', self.loop(periodic, 'producer'))
            self.patch(RNS.Transport, 'jobloop', staticmethod(self.loop(jobs, 'producer')))
            self.patch(RNS.Transport, 'count_traffic_loop', staticmethod(self.loop(traffic, 'producer')))
            self.patch(RNS.Transport, 'inbound_job', staticmethod(self.loop(RNS.Transport.inbound_job, 'queue')))
            original_get = transport.InboundQueues.get

            def get(queue, block=True, timeout=None):
                worker = threading.current_thread()
                if self.loops.get(worker) != 'queue' or not block or timeout is not None:
                    return original_get(queue, block=block, timeout=timeout)
                while True:
                    with self.condition:
                        try:
                            packet = original_get(queue, block=False)
                        except Empty:
                            self.idle.add(worker)
                            if self.queues_stop:
                                raise _Stopped()
                        else:
                            self.idle.discard(worker)
                            return packet
                    with queue._cond:
                        if queue.qsize() == 0:
                            queue._cond.wait(.1)

            self.patch(transport.InboundQueues, 'get', get)
            original_log = RNS.log

            def log(message, level=3, *args, **kwargs):
                if level in (RNS.LOG_CRITICAL, RNS.LOG_ERROR):
                    self.failed.set()
                return original_log(message, level, *args, **kwargs)

            self.patch(RNS, 'log', log)
            original_hook = threading.excepthook

            def thread_error(arguments):
                self.failed.set()
                original_hook(arguments)

            self.patch(threading, 'excepthook', thread_error)
        except BaseException:
            self.restore.close()
            self.operation.__exit__(*sys.exc_info())
            raise
        return self

    def initialize(self, directory, *, initializer=None):
        if initializer is None:
            from provisioning.chat_transport import initialize as initializer
        require(self.root is None and not self.closed, 'RNS_SINGLE_LIFETIME')
        self.root = Path(directory).absolute()
        require(not any(path.is_symlink() for path in (self.root, *self.root.parents)), 'RNS_STATE_PATH')
        runtime = initializer(self.root)
        info = self.root.stat()
        self.root_pin = (info.st_dev, info.st_ino)
        require(runtime.is_standalone_instance and not runtime.is_connected_to_shared_instance and
                not RNS.Reticulum.transport_enabled(), 'RNS_RUNTIME_SHAPE')
        return runtime

    def workers(self):
        return [worker for worker in threading.enumerate() if worker is not threading.main_thread()]

    def join_worker(self, worker, timeout):
        if worker._started.wait(timeout):
            worker.join(timeout)

    def close(self):
        try:
            return self._close()
        except BaseException:
            self.failed.set()
            self.admitted.uncertain()
            raise

    def _close(self):
        from provisioning.support_lifecycle import stop_requested

        if self.closed:
            require(not self.failed.is_set(), 'RNS_PERSISTENCE_UNCERTAIN')
            return
        with stop_requested():
            atexit.unregister(RNS.Reticulum.exit_handler)
            while (RNS.Transport.interfaces or RNS.Transport.local_client_interfaces or
                   RNS.Transport.active_links or RNS.Transport.pending_links):
                time.sleep(.05)
            self.producers_stop.set()
            while True:
                with self.condition:
                    observed = self.workers()
                    others = [worker for worker in observed if self.loops.get(worker) != 'queue']
                    queues_idle = all(worker in self.idle for worker in observed if worker not in others)
                    native = {int(path.name) for path in Path('/proc/self/task').iterdir()}
                    covered = native == {threading.main_thread().native_id, *(worker.native_id for worker in observed)}
                    if not others and queues_idle and covered:
                        self.queues_stop = True
                        break
                for worker in others:
                    self.join_worker(worker, .05)
                time.sleep(.01)
            while self.workers():
                for worker in self.workers():
                    self.join_worker(worker, .1)
            require(not any(task.joinpath('children').read_text().strip()
                            for task in Path('/proc/self/task').iterdir()), 'RNS_CHILDREN_REMAIN')
            if RNS.Reticulum.get_instance() is not None:
                require(RNS.Transport.inbound_queues.snapshot()[0] == 0, 'RNS_QUEUE_UNFINISHED')
            if self.root is not None:
                state_paths(self.root)
                info = self.root.stat()
                require(self.root_pin is None or (info.st_dev, info.st_ino) == self.root_pin,
                        'RNS_STATE_REPLACED')
            if RNS.Reticulum.get_instance() is not None:
                streams = sys.stdout, sys.stderr
                try:
                    RNS.Reticulum.exit_handler()
                finally:
                    detached = sys.stdout, sys.stderr
                    sys.stdout, sys.stderr = streams
                    for stream in detached:
                        if not any(stream is original for original in streams):
                            stream.close()
            while self.workers():
                for worker in self.workers():
                    self.join_worker(worker, .1)
            require({int(path.name) for path in Path('/proc/self/task').iterdir()} ==
                    {threading.main_thread().native_id}, 'RNS_NATIVE_WORKERS_REMAIN')
            if self.root is not None:
                sync_tree(self.root)
            self.closed = True
            require(not self.failed.is_set(), 'RNS_PERSISTENCE_UNCERTAIN')

    def __exit__(self, kind, error, traceback):
        try:
            self.close()
        except BaseException:
            self.operation.__exit__(*sys.exc_info())
            raise
        else:
            return self.operation.__exit__(kind, error, traceback)
        finally:
            self.restore.close()
