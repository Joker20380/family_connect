"""CPython 3.14 main-thread bridge for the pinned legacy HTTP receiver, not capture acceptance."""
import hashlib
import json
import os
from pathlib import Path
import socketserver
import stat
import sys
import tempfile
import threading
import time

BASELINE = '4e2df679761ba9e7af74128984ef2e19e8e7b228f1cc85b36d50be2b0bc24ce8'
RETENTION = {'support-retention': 'control.friends.diagnostics',
             'technical-metadata-retention': 'control.friends.technical_metadata'}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def read(path, maximum=2 * 1024 * 1024):
    path = Path(path).absolute()
    require(not any(item.is_symlink() for item in (path, *path.parents)), 'SYMLINK_INPUT')
    descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC)
    with os.fdopen(descriptor, 'rb') as source:
        require(stat.S_ISREG(os.fstat(source.fileno()).st_mode), 'REGULAR_INPUT_REQUIRED')
        raw = source.read(maximum + 1)
    require(len(raw) <= maximum, 'INPUT_LIMIT')
    return raw


def binding(pid):
    require(type(pid) is int and pid > 1, 'PID')
    root = Path('/proc') / str(pid)
    before = (root / 'stat').read_text().rsplit(')', 1)[1].split()[19]
    result = dict(pid=pid, start=before, boot=(Path('/proc/sys/kernel/random/boot_id').read_text().strip()),
                  command=hashlib.sha256(read(root / 'cmdline', 32768)).hexdigest(),
                  cgroup=hashlib.sha256(read(root / 'cgroup', 32768)).hexdigest())
    require((root / 'stat').read_text().rsplit(')', 1)[1].split()[19] == before, 'PID_CHANGED')
    return result


def write(path, value):
    path = Path(path)
    descriptor, temporary = tempfile.mkstemp(prefix='.receipt-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as output:
            output.write(json.dumps(value, sort_keys=True).encode())
            output.flush()
            os.fsync(output.fileno())
        os.link(temporary, path)
    finally:
        os.unlink(temporary)
    directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def prepare(pid, archive, output, *, mode='probe', seconds=5):
    require(sys.version_info[:2] == (3, 14) and hasattr(sys, 'remote_exec'), 'CPYTHON_314_REQUIRED')
    require(mode in ('probe', 'stop') and type(seconds) in (int, float) and 0.2 <= seconds <= 15,
            'REQUEST_SCOPE')
    archive, output = Path(archive).absolute(), Path(output).absolute()
    require(hashlib.sha256(read(archive)).hexdigest() == BASELINE, 'ARCHIVE_PIN')
    require(not any(path.is_symlink() for path in (output, *output.parents)), 'OUTPUT_SYMLINK')
    observed = binding(pid)
    output.mkdir(mode=0o700)
    source = read(Path(__file__).absolute())
    with (output / 'bridge.py').open('xb') as target:
        os.chmod(target.fileno(), 0o600)
        target.write(source)
        target.flush()
        os.fsync(target.fileno())
    request = dict(binding=observed, archive=str(archive), output=str(output), mode=mode,
                   deadline=time.monotonic() + seconds, source_sha256=hashlib.sha256(source).hexdigest())
    write(output / 'request.json', request)
    launcher = ('try:\n'
                ' import hashlib, pathlib\n'
                f' root=pathlib.Path({str(output)!r})\n'
                ' raw=(root/"bridge.py").read_bytes()\n'
                f' assert hashlib.sha256(raw).hexdigest()=={request["source_sha256"]!r}\n'
                ' namespace={"__file__":str(root/"bridge.py")}\n'
                ' exec(compile(raw,namespace["__file__"],"exec"),namespace)\n'
                ' namespace["execute"](root/"request.json")\n'
                'except BaseException:\n pass\n')
    with (output / 'invoke.py').open('xb') as target:
        os.chmod(target.fileno(), 0o600)
        target.write(launcher.encode())
        target.flush()
        os.fsync(target.fileno())
    write(output / 'prepared.json', dict(binding=observed, mode=mode, submitted=False))
    return output / 'invoke.py'


def context(archive):
    require(threading.current_thread() is threading.main_thread(), 'MAIN_THREAD_REQUIRED')
    runtime = sys.modules.get('friends_http')
    require(runtime is not None and runtime.__file__ == archive + '/friends_http.py', 'RUNTIME_BINDING')
    entry = getattr(runtime, 'main', None)
    require(entry is not None and hasattr(entry, '__code__'), 'LEGACY_MAIN_NOT_READY')
    frame = sys._getframe()
    frames = []
    while frame is not None:
        frames.append(frame)
        frame = frame.f_back
    loops = [frame for frame in frames if frame.f_code is socketserver.BaseServer.serve_forever.__code__]
    mains = [frame for frame in frames if frame.f_code is entry.__code__]
    require(len(loops) == len(mains) == 1, 'LEGACY_LOOP_REQUIRED')
    loop, main = loops[0], mains[0]
    server = loop.f_locals['self']
    require(type(server) is runtime.ThreadingHTTPServer and server.RequestHandlerClass is runtime.Handler
            and server.server_address[0] == '127.0.0.1' and not server._BaseServer__shutdown_request,
            'SERVER_BINDING')
    inner = frames[frames.index(loop) - 1]
    require(inner.f_globals.get('__name__') in ('selectors', 'runpy') or inner.f_code.co_filename.endswith('/invoke.py'),
            'PARTIAL_ACCEPT_REFUSED')
    events = [main.f_locals['retention'], main.f_locals['metadata_retention']]
    require(all(type(event) is threading.Event and not event.is_set() for event in events), 'RETENTION_EVENTS')
    workers, handlers = [], []
    for worker in threading.enumerate():
        if worker is threading.main_thread():
            continue
        target = getattr(worker, '_target', None)
        if worker.name in RETENTION:
            require(target is not None and target.__module__ == RETENTION[worker.name]
                    and target.__qualname__ == 'start_retention.<locals>.run', 'RETENTION_BINDING')
            closure = dict(zip(target.__code__.co_freevars, (cell.cell_contents for cell in target.__closure__)))
            require(closure.get('stopped') is events[list(RETENTION).index(worker.name)], 'RETENTION_EVENT_BINDING')
            workers.append(worker)
        else:
            require(getattr(target, '__self__', None) is server and
                    getattr(target, '__func__', None) is socketserver.ThreadingMixIn.process_request_thread,
                    'UNKNOWN_THREAD')
            handlers.append(worker)
    require(len(workers) == 2 and {worker.name for worker in workers} == set(RETENTION), 'RETENTION_COVERAGE')
    require({int(task.name) for task in Path('/proc/self/task').iterdir()} ==
            {worker.native_id for worker in threading.enumerate()}, 'NATIVE_THREAD_COVERAGE')
    return server, workers, handlers, events


def no_children():
    return all(not (task / 'children').read_text().strip() for task in Path('/proc/self/task').iterdir())


def execute(request_path):
    request_path = Path(request_path)
    output = request_path.parent
    require(output.stat().st_uid == os.geteuid() and stat.S_IMODE(output.stat().st_mode) == 0o700,
            'PRIVATE_OUTPUT')
    claimed = output / 'claimed.json'
    write(claimed, dict(pid=os.getpid(), monotonic=time.monotonic()))
    irreversible = False
    try:
        request = json.loads(read(request_path, 32768))
        require(set(request) == {'binding', 'archive', 'output', 'mode', 'deadline', 'source_sha256'}, 'REQUEST_FIELDS')
        require(str(output) == request['output'] and request['mode'] in ('probe', 'stop'), 'REQUEST_SCOPE')
        require(binding(os.getpid()) == request['binding'], 'PROCESS_BINDING')
        require(0 < request['deadline'] - time.monotonic() <= 15, 'EXPIRED_REQUEST')
        require(hashlib.sha256(read(__file__)).hexdigest() == request['source_sha256'], 'BRIDGE_PIN')
        require(hashlib.sha256(read(request['archive'])).hexdigest() == BASELINE, 'ARCHIVE_PIN')
        server, workers, handlers, events = context(request['archive'])
        write(output / 'entered.json', dict(mode=request['mode'], pid=os.getpid(),
              handlers=len(handlers), retention=len(workers), main_thread=True, application_admission_paused=True))
        for handler in handlers:
            handler.join(max(0, request['deadline'] - time.monotonic()))
        require(all(not handler.is_alive() for handler in handlers), 'HANDLERS_UNFINISHED')
        require(no_children(), 'CHILDREN_UNFINISHED')
        require(time.monotonic() < request['deadline'], 'EXPIRED_REQUEST')
        if request['mode'] == 'probe':
            write(output / 'result.json', dict(result='PROBE_RETURNING', pid=os.getpid(),
                  admission_restores_on_return=True, retention_unchanged=True,
                  external_settlement_proven=False, capture_permitted=False))
            return
        write(output / 'legacy-uncertainty.json', dict(reason='OLD_EXTERNAL_OUTCOMES_NOT_ATTESTED',
              pid=os.getpid(), binding=request['binding'], capture_permitted=False))
        write(output / 'draining-retention.json', dict(forced_termination_allowed=False))
        irreversible = True
        for event in events:
            event.set()
        for worker in workers:
            worker.join()
        require(no_children() and threading.active_count() == 1, 'EXIT_CENSUS')
        write(output / 'quiescent.json', dict(pid=os.getpid(), handlers=0, retention=0, children=0,
              external_settlement_proven=False, capture_permitted=False))
        server._BaseServer__shutdown_request = True
        server.socket.close()
        write(output / 'result.json', dict(result='RETURN_TO_EXIT', pid=os.getpid(),
              exit_must_be_observed=True, capture_permitted=False))
    except BaseException as error:
        reason = str(error) if type(error) is ValueError and str(error).isupper() else 'BRIDGE_FAILURE'
        trace = error.__traceback__
        while trace.tb_next is not None:
            trace = trace.tb_next
        try:
            write(output / 'error.json', dict(reason=reason, exception_type=type(error).__name__,
                  failure_site=dict(function=trace.tb_frame.f_code.co_name, line=trace.tb_lineno),
                  irreversible=irreversible, capture_permitted=False))
        except BaseException:
            pass
        if irreversible:
            while True:
                try:
                    time.sleep(60)
                except BaseException:
                    pass
