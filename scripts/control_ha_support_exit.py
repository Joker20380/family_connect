"""Two-phase legacy support exit; no deployment, data rollback or capture approval."""
import atexit
import json
import math
import os
from pathlib import Path
import runpy
import stat
import sys
import threading
import time


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def stage(path, raw):
    with path.open('xb') as target:
        os.fchmod(target.fileno(), 0o600)
        target.write(raw)
        target.flush()
        os.fsync(target.fileno())


def prepare(pid, root, output, *, seconds=360):
    from scripts import control_ha_legacy_support as admission
    from scripts import control_ha_support_quiesce as pause

    pause.prepare(pid, root, output, seconds=seconds, hold=0)
    output = Path(output).absolute()
    raw = admission.read(Path(__file__).resolve())
    stage(output / 'exit.py', raw)
    pins = {name: admission.digest(admission.read(output / name))
            for name in ('exit.py', 'request.json', 'probe.py', 'runtime.py', 'admission.py')}
    admission.write(output / 'exit-request.json', dict(schema=1, pins=pins))
    launcher_pins = dict(pins, **{'exit-request.json': admission.digest(admission.read(output / 'exit-request.json'))})
    launcher = ('import hashlib,pathlib,runpy\n'
                f'root=pathlib.Path({str(output)!r})\n'
                f'assert all(hashlib.sha256((root/name).read_bytes()).hexdigest()==digest for name,digest in {launcher_pins!r}.items())\n'
                'runpy.run_path(str(root/"exit.py"))["execute"](root)\n')
    stage(output / 'exit-invoke.py', launcher.encode())
    for path in output.iterdir():
        admission.visible_to(pid, path)
    return output / 'exit-invoke.py'


def authorize(output):
    from scripts import control_ha_legacy_support as admission

    output = Path(output).absolute()
    raw = admission.read(output / 'request.json')
    request = json.loads(raw)
    ready = json.loads(admission.read(output / 'ready.json'))
    require(not (output / 'error.json').exists() and not (output / 'restored.json').exists(), 'EXIT_REFUSED')
    require(ready == dict(binding=request['binding'], request_sha256=admission.digest(raw),
                         capture_permitted=False), 'READY_RECEIPT')
    require(time.monotonic() < request['deadline'] - .1, 'COMMIT_EXPIRED')
    require(admission.binding(request['binding']['pid']) == request['binding'], 'PROCESS_BINDING')
    admission.sources(request['root'], request['baseline'])
    admission.write(output / 'commit.json', ready)


class Retired(SystemExit):
    pass


def terminal_type(base):
    class TerminalPause(base):
        committed = False

        def resume(self, worker):
            if self.committed and worker in self.producers | self.queues:
                raise Retired()

        def expected_exit(self, arguments):
            return (self.committed and arguments.exc_type is Retired and
                    arguments.thread in self.producers | self.queues)

        def commit(self, stopped):
            require(self.ready(), 'QUIESCENCE_LOST')
            with self.queue_lock(), self.lock:
                require(not stopped.is_set() and time.monotonic() < self.deadline - .1 and
                        not self.failed.is_set() and self.parked == self.producers and
                        self.queue_parked == self.queues, 'COMMIT_BOUNDARY_LOST')
                self.committed = True
                self.deadline = float('inf')

        def retire(self):
            require(self.committed, 'COMMIT_REQUIRED')
            self.release.set()
            with self.condition:
                self.condition.notify_all()
            for worker in self.producers | self.queues:
                worker.join()
            require(not self.failed.is_set(), 'RNS_WORK_UNCERTAIN')

    return TerminalPause


def owned(admission, request, content):
    delivery, stopped = admission['context'](request['root'], content)
    frame, owners = sys._getframe(), []
    while frame is not None:
        if frame.f_code.co_name == 'main' and frame.f_locals.get('stopped') is stopped:
            owners.append(frame)
        frame = frame.f_back
    require(len(owners) == 1, 'MAIN_OWNER')
    values = owners[0].f_locals
    server, store, args = (values[name] for name in ('server', 'store', 'args'))
    require(server.owner.store is store and delivery.mailbox.owner.store is store, 'STORE_OWNER')
    admission['code_matches'](store.close, content['messenger/store.py'],
                              str(Path(request['root']) / 'messenger/store.py'))
    require(not store._db.in_transaction, 'STORE_TRANSACTION_OPEN')
    store_root, runtime_root, socket = Path(args.store), Path(args.runtime), Path(args.socket)
    require(store_root.is_absolute() and runtime_root.is_absolute() and socket.is_absolute(), 'STATE_ABSOLUTE')
    require(store._db.execute('PRAGMA database_list').fetchall() ==
            [(0, 'main', str(store_root / 'history.sqlite'))], 'STORE_DATABASE_BINDING')
    info = socket.lstat()
    require(stat.S_ISSOCK(info.st_mode) and info.st_uid == os.getuid(), 'SOCKET_BINDING')
    return delivery, stopped, server, store, store_root, runtime_root, socket, (info.st_dev, info.st_ino)


def only_main():
    require(threading.enumerate() == [threading.main_thread()] and
            {int(path.name) for path in Path('/proc/self/task').iterdir()} ==
            {threading.main_thread().native_id}, 'WORKERS_REMAIN')
    require(not any(path.joinpath('children').read_text().strip()
                    for path in Path('/proc/self/task').iterdir()), 'CHILDREN_REMAIN')


def persist(runtime, contract, store, store_root, runtime_root):
    rns = contract['RNS']
    atexit.unregister(rns.Reticulum.exit_handler)
    streams = sys.stdout, sys.stderr
    try:
        rns.Reticulum.exit_handler()
    finally:
        detached = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = streams
        for stream in detached:
            if not any(stream is original for original in streams):
                stream.close()
    while True:
        workers = [worker for worker in threading.enumerate() if worker is not threading.main_thread()]
        if not workers:
            break
        for worker in workers:
            worker.join(.1)
    only_main()
    require(not runtime.failed.is_set(), 'FINAL_PERSISTENCE_UNCERTAIN')
    contract['sync_tree'](runtime_root)
    store.close()
    require(store._db is None and store._owner is None, 'STORE_NOT_CLOSED')
    contract['sync_tree'](store_root)


def execute(output):
    output = Path(output)
    admission = runpy.run_path(str(output / 'admission.py'))
    read, write = admission['read'], admission['write']
    runtime, delivery, online, entered = None, None, None, False
    require(output.stat().st_uid == os.getuid() and output.stat().st_mode & 0o777 == 0o700,
            'PRIVATE_OUTPUT')
    try:
        write(output / 'claimed-exit.json', dict(pid=os.getpid(), capture_permitted=False))
    except FileExistsError:
        return
    try:
        terminal = json.loads(read(output / 'exit-request.json'))
        require(set(terminal) == {'schema', 'pins'} and terminal['schema'] == 1 and
                set(terminal['pins']) == {'exit.py', 'request.json', 'probe.py', 'runtime.py', 'admission.py'} and
                all(admission['digest'](read(output / name)) == digest
                    for name, digest in terminal['pins'].items()), 'EXIT_PINS')
        request_raw = read(output / 'request.json')
        request = json.loads(request_raw)
        require(request['binding'] == admission['binding'](os.getpid()) and
                request['output'] == str(output), 'PROCESS_BINDING')
        require(type(request['deadline']) in (int, float) and math.isfinite(request['deadline']) and
                0 < request['deadline'] - time.monotonic() <= 360, 'REQUEST_TIME')
        contract = runpy.run_path(str(output / 'runtime.py'))
        pause = runpy.run_path(str(output / 'probe.py'))
        content = admission['sources'](request['root'], request['baseline'])
        delivery, stopped, server, store, store_root, runtime_root, socket, socket_pin = owned(admission, request, content)
        require(str(runtime_root) == contract['RNS'].Reticulum.configdir, 'RNS_ROOT_BINDING')
        roots = [store_root, runtime_root]
        for path in roots:
            contract['state_paths'](path)
        root_pins = [(path.stat().st_dev, path.stat().st_ino) for path in roots]
        require(delivery._condition.acquire(timeout=pause['remaining'](request['deadline'])), 'CONDITION_BUSY')
        try:
            require(not delivery._closed, 'DELIVERY_CLOSED')
            online = delivery._online
            delivery._online = False
        finally:
            delivery._condition.release()
        runtime = terminal_type(pause['RuntimePause'])(contract, delivery, request['deadline'])
        runtime.__enter__()
        entered = True
        write(output / 'entered.json', dict(application_paused=True, capture_permitted=False))
        with delivery._condition:
            while delivery._cancel is not None:
                delivery._condition.wait(pause['remaining'](request['deadline']))
        runtime.armed = True
        runtime.drain()
        receipt = dict(binding=request['binding'], request_sha256=admission['digest'](request_raw),
                       capture_permitted=False)
        write(output / 'ready.json', receipt)
        while not (output / 'commit.json').exists():
            require(runtime.ready() and not stopped.is_set(), 'QUIESCENCE_LOST')
            time.sleep(min(.02, pause['remaining'](request['deadline'])))
        require(json.loads(read(output / 'commit.json')) == receipt, 'COMMIT_BINDING')
        write(output / 'uncertainty.json', dict(legacy_external_outcomes_proven=False, capture_permitted=False))
        runtime.commit(stopped)
        write(output / 'committed.json', dict(binding=request['binding'], irreversible=True, capture_permitted=False))
        runtime.retire()
        require(delivery._cancel is None, 'DELIVERY_NOT_IDLE')
        delivery.close(timeout=0)
        delivery._worker.join()
        only_main()
        require([(path.stat().st_dev, path.stat().st_ino) for path in roots] == root_pins, 'STATE_REPLACED')
        persist(runtime, contract, store, store_root, runtime_root)
        server.server_close()
        info = socket.lstat()
        require((info.st_dev, info.st_ino) == socket_pin and stat.S_ISSOCK(info.st_mode), 'SOCKET_REPLACED')
        socket.unlink()
        descriptor = os.open(socket.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        only_main()
        write(output / 'exited.json', dict(binding=request['binding'], final_persistence=True,
              stores_closed=True, workers=0, exit_code=0, capture_permitted=False))
        os._exit(0)
    except BaseException as error:
        reason = str(error) if type(error) is ValueError and str(error).isupper() else 'EXIT_FAILURE'
        committed = runtime is not None and runtime.committed
        try:
            write(output / 'error.json', dict(reason=reason, irreversible=committed, capture_permitted=False))
        except BaseException:
            pass
        if committed:
            while True:
                try:
                    time.sleep(1)
                except BaseException:
                    pass
    finally:
        if entered and not runtime.committed:
            runtime.__exit__()
        if delivery is not None and online is not None and not (runtime and runtime.committed):
            with delivery._condition:
                delivery._online = online
                delivery._condition.notify_all()
            write(output / 'restored.json', dict(pid=os.getpid(), capture_permitted=False))
