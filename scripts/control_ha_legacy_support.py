"""Reversible pinned legacy support admission probe; never stops or approves capture."""
import hashlib
import json
import math
import os
from pathlib import Path
import socketserver
import stat
import sys
import tempfile
import threading
import time
import types


BASELINE = 'abe256c570c861a1d5f5f485482652b7c5bcc9740630bc2d049b85753c07edc1'
RNS_JOBS = frozenset(('Reticulum.__jobs', 'Transport.jobloop', 'Transport.count_traffic_loop',
                      'Transport.inbound_job', 'Transport.outbound_job'))


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path, maximum=512 * 1024):
    path = Path(path).absolute()
    require(not any(item.is_symlink() for item in (path, *path.parents)), 'INPUT_SYMLINK')
    descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC)
    with os.fdopen(descriptor, 'rb') as source:
        before = os.fstat(source.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1, 'INPUT_SHAPE')
        raw = source.read(maximum + 1)
        after = os.fstat(source.fileno())
    require(len(raw) <= maximum, 'INPUT_LIMIT')
    require((before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
            (after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns), 'INPUT_CHANGED')
    return raw


def binding(pid):
    require(type(pid) is int and pid > 1, 'PID')
    root = Path('/proc') / str(pid)
    before = (root / 'stat').read_text().rsplit(')', 1)[1].split()[19]
    result = dict(pid=pid, start=before, boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                  command=digest(read(root / 'cmdline', 32768)), cgroup=digest(read(root / 'cgroup', 32768)))
    require((root / 'stat').read_text().rsplit(')', 1)[1].split()[19] == before, 'PID_CHANGED')
    return result


def write(path, value):
    descriptor, temporary = tempfile.mkstemp(prefix='.receipt-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as target:
            target.write(json.dumps(value, sort_keys=True).encode())
            target.flush()
            os.fsync(target.fileno())
        os.link(temporary, path)
    finally:
        os.unlink(temporary)
    descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


COLLECTOR_BASELINE = 'owner-collectors-192343eb'
COLLECTOR_SOURCES = {
    'control/capture_gate.py': 'da28d940e2e17e2dbb1fbbde8cc04c59d29cffc8762ada717135504e2ffa4906',
    'provisioning/owner_capture.py': '1997f1bf5da19ad1a2d11b16d83a71c217d1ea1f5f4cc440ef59db9e07e737cf',
    'provisioning/support_bindings.py': 'afba534e17ec3a57f5431bd611d66b94a56f7e5f969e167ca5afe2834d430bc2',
    'provisioning/subscription_collector.py': '3bb9954c8edfba64f4b2aeb63fb174669fa2fc8e37f71c193c9a18da895193cb',
}
MANDATORY_COLLECTOR_BASELINE = 'owner-collectors-b7f4cbd2'
MANDATORY_COLLECTOR_SOURCES = COLLECTOR_SOURCES | {
    'provisioning/owner_capture.py': 'b7b1fb3ffe69d9428cb419a30d2473a2bb73a6ffb2e7c6390b6878afc953a45d',
}
COLLECTOR_VARIANTS = {
    COLLECTOR_BASELINE: COLLECTOR_SOURCES,
    MANDATORY_COLLECTOR_BASELINE: MANDATORY_COLLECTOR_SOURCES,
}


def sources(root, expected, *, installed_collectors=False, baseline_variant=None):
    require(digest(json.dumps(expected, sort_keys=True, separators=(',', ':')).encode()) == BASELINE,
            'BASELINE_PIN')
    require(type(installed_collectors) is bool, 'COLLECTOR_BASELINE_OPTION')
    require(baseline_variant is None or baseline_variant in COLLECTOR_VARIANTS, 'BASELINE_VARIANT')
    require(not installed_collectors or baseline_variant in (None, COLLECTOR_BASELINE), 'BASELINE_VARIANT_CONFLICT')
    if installed_collectors:
        baseline_variant = COLLECTOR_BASELINE
    if baseline_variant is not None:
        expected = expected | COLLECTOR_VARIANTS[baseline_variant]
    root = Path(root).absolute()
    require(not any(path.is_symlink() for path in (root, *root.parents)), 'SOURCE_SYMLINK')
    require({path.relative_to(root).as_posix() for path in root.rglob('*.py')} == set(expected),
            'SOURCE_CLOSURE')
    content = {name: read(root / name) for name in expected}
    require(all(digest(raw) == expected[name] for name, raw in content.items()), 'SOURCE_PIN')
    return content


def visible_to(pid, path):
    target = Path('/proc') / str(pid) / 'root' / path.relative_to('/')
    try:
        host, remote = path.stat(), target.stat()
    except OSError:
        raise ValueError('OUTPUT_NAMESPACE') from None
    require((host.st_dev, host.st_ino, host.st_mode) ==
            (remote.st_dev, remote.st_ino, remote.st_mode), 'OUTPUT_NAMESPACE')


def prepare(pid, root, output, *, seconds=5, hold=0):
    require(sys.version_info[:2] == (3, 14) and hasattr(sys, 'remote_exec'), 'CPYTHON_314_REQUIRED')
    require(type(seconds) in (int, float) and math.isfinite(seconds) and .2 <= seconds <= 15 and
            type(hold) in (int, float) and math.isfinite(hold) and 0 <= hold < seconds, 'REQUEST_TIME')
    root, output = Path(root).absolute(), Path(output).absolute()
    contract = Path(__file__).resolve().parents[1] / 'deploy/support-chat/support-capture-v1.json'
    expected = json.loads(read(contract))['baseline']
    sources(root, expected)
    observed = binding(pid)
    require(not any(path.is_symlink() for path in (output, *output.parents)), 'OUTPUT_SYMLINK')
    visible_to(pid, output.parent)
    output.mkdir(mode=0o700, exist_ok=False)
    raw = read(Path(__file__).absolute())
    with (output / 'bridge.py').open('xb') as target:
        os.fchmod(target.fileno(), 0o600)
        target.write(raw)
        target.flush()
        os.fsync(target.fileno())
    request = dict(binding=observed, root=str(root), output=str(output), baseline=expected, hold=hold,
                   deadline=time.monotonic() + seconds, source_sha256=digest(raw))
    write(output / 'request.json', request)
    launcher = ('try:\n import hashlib,pathlib\n'
                f' root=pathlib.Path({str(output)!r})\n raw=(root/"bridge.py").read_bytes()\n'
                f' assert hashlib.sha256(raw).hexdigest()=={digest(raw)!r}\n'
                ' namespace={"__file__":str(root/"bridge.py")}\n'
                ' exec(compile(raw,namespace["__file__"],"exec"),namespace)\n'
                ' namespace["execute"](root/"request.json")\nexcept BaseException:\n pass\n')
    with (output / 'invoke.py').open('xb') as target:
        os.fchmod(target.fileno(), 0o600)
        target.write(launcher.encode())
        target.flush()
        os.fsync(target.fileno())
    write(output / 'prepared.json', dict(binding=observed, submitted=False, capture_permitted=False))
    for path in (output, *output.iterdir()):
        visible_to(pid, path)
    require(binding(pid) == observed, 'PID_CHANGED')
    return output / 'invoke.py'


def code_matches(function, raw, filename):
    def codes(code):
        yield code
        for value in code.co_consts:
            if isinstance(value, types.CodeType):
                yield from codes(value)
    require(hasattr(function, '__code__'), 'LOADED_CODE')
    expected = [code for code in codes(compile(raw, filename, 'exec'))
                if code.co_qualname == function.__code__.co_qualname]
    require(len(expected) == 1 and function.__code__ == expected[0] and
            function.__code__.co_filename == filename, 'LOADED_CODE')


def context(root, content):
    require(threading.current_thread() is threading.main_thread() and not sys.flags.optimize,
            'MAIN_THREAD_REQUIRED')
    filename = str(Path(root) / 'provisioning/support_worker.py')
    modules = []
    for module in tuple(sys.modules.values()):
        if getattr(module, '__file__', None) == filename and hasattr(module, 'main'):
            if not any(module is previous for previous in modules):
                modules.append(module)
    frames, frame = [], sys._getframe()
    while frame is not None:
        frames.append(frame)
        frame = frame.f_back
    owners = [(module, frame) for module in modules for frame in frames
              if getattr(module.main, '__code__', None) is frame.f_code and
              module.__dict__ is frame.f_globals and module.main.__globals__ is frame.f_globals]
    require(len(owners) == 1, 'RUNTIME_BINDING')
    runtime, main = owners[0]
    for function in (runtime.main, runtime.SupportHandler.handle, runtime.SupportServer.__init__):
        code_matches(function, content['provisioning/support_worker.py'], filename)
    for function in (runtime.DeliveryController._run, runtime.DeliveryController.close,
                     runtime.DeliveryController.update, runtime.DeliveryController.request_sync):
        code_matches(function, content['messenger/delivery.py'], str(Path(root) / 'messenger/delivery.py'))
    mains = [frame for frame in frames if frame.f_code is runtime.main.__code__]
    loops = [frame for frame in frames if frame.f_code is socketserver.BaseServer.handle_request.__code__]
    require(len(mains) == len(loops) == 1, 'IDLE_MAIN_LOOP_REQUIRED')
    loop = loops[0]
    require(loop.f_back is main, 'SERIAL_LOOP_BINDING')
    require(not any(frame.f_code is socketserver.BaseServer._handle_request_noblock.__code__
                    for frame in frames), 'PARTIAL_ACCEPT_REFUSED')
    server, delivery, stopped = (main.f_locals[name] for name in ('server', 'delivery', 'stopped'))
    require(type(server) is runtime.SupportServer and loop.f_locals['self'] is server and
            server.delivery is delivery and type(delivery) is runtime.DeliveryController and
            delivery._worker.is_alive() and getattr(delivery._worker._target, '__self__', None) is delivery,
            'OWNER_BINDING')
    require(type(stopped) is threading.Event and not stopped.is_set(), 'STOP_ALREADY_REQUESTED')
    return delivery, stopped


def threads(delivery):
    readers, background = [], []
    observed = threading.enumerate()
    for worker in observed:
        if worker in (threading.main_thread(), delivery._worker):
            continue
        target = getattr(worker, '_target', None)
        module, name = getattr(target, '__module__', ''), getattr(target, '__qualname__', '')
        if module in ('RNS.Reticulum', 'RNS.Transport') and name in RNS_JOBS:
            background.append(worker)
        elif worker.name == 'chat-route' and (module, name) in (
                ('RNS.Interfaces.TCPInterface', 'TCPClientInterface.read_loop'),
                ('RNS.Interfaces.LocalInterface', 'LocalClientInterface.read_loop')):
            readers.append(worker)
        else:
            raise ValueError('UNKNOWN_THREAD')
    require({int(path.name) for path in Path('/proc/self/task').iterdir()} ==
            {worker.native_id for worker in observed}, 'NATIVE_THREAD_COVERAGE')
    return readers, background


def execute(path):
    path = Path(path)
    output, delivery, paused = path.parent, None, False
    try:
        require(output.stat().st_uid == os.geteuid() and stat.S_IMODE(output.stat().st_mode) == 0o700,
                'PRIVATE_OUTPUT')
        write(output / 'claimed.json', dict(pid=os.getpid()))
        request = json.loads(read(path, 32768))
        require(set(request) == {'binding', 'root', 'output', 'baseline', 'hold', 'deadline', 'source_sha256'},
                'REQUEST_FIELDS')
        require(request['output'] == str(output) and binding(os.getpid()) == request['binding'], 'PROCESS_BINDING')
        remaining = request['deadline'] - time.monotonic()
        require(0 < remaining <= 15 and type(request['hold']) in (int, float) and
                math.isfinite(request['hold']) and 0 <= request['hold'] < remaining, 'EXPIRED_REQUEST')
        require(digest(read(__file__)) == request['source_sha256'], 'BRIDGE_PIN')
        content = sources(request['root'], request['baseline'])
        delivery, stopped = context(request['root'], content)
        write(output / 'thread-census.json', [dict(native_id=worker.native_id,
              module=getattr(getattr(worker, '_target', None), '__module__', None),
              function=getattr(getattr(worker, '_target', None), '__qualname__', None))
              for worker in threading.enumerate()])
        require(delivery._condition.acquire(timeout=max(0, request['deadline'] - time.monotonic())),
                'CONDITION_BUSY')
        try:
            require(not delivery._closed, 'DELIVERY_CLOSED')
            online = delivery._online
            delivery._online = False
            paused = True
        finally:
            delivery._condition.release()
        write(output / 'entered.json', dict(pid=os.getpid(), main_thread=True,
              application_admission_paused=True, cancellation_requested=False, capture_permitted=False))
        with delivery._condition:
            while delivery._cancel is not None:
                remaining = request['deadline'] - time.monotonic()
                require(remaining > 0, 'DELIVERY_UNFINISHED')
                delivery._condition.wait(remaining)
        readers, background = threads(delivery)
        for reader in readers:
            reader.join(max(0, request['deadline'] - time.monotonic()))
        require(all(not reader.is_alive() for reader in readers), 'READERS_UNFINISHED')
        readers, background = threads(delivery)
        require(not readers, 'READERS_UNFINISHED')
        require(all(not (task / 'children').read_text().strip() for task in Path('/proc/self/task').iterdir()),
                'CHILDREN_UNFINISHED')
        require(time.monotonic() + request['hold'] < request['deadline'], 'EXPIRED_REQUEST')
        write(output / 'drained.json', dict(application_drained=True, runtime_drained=False,
              runtime_threads=len(background), external_settlement_proven=False, capture_permitted=False))
        time.sleep(request['hold'])
        require(not stopped.is_set(), 'STOP_REQUESTED_DURING_PROBE')
    except BaseException as error:
        reason = str(error) if type(error) is ValueError and str(error).isupper() else 'BRIDGE_FAILURE'
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
                      admission_restores_on_return=True, capture_permitted=False))
            except BaseException:
                pass
