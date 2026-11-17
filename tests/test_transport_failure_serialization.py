import errno
import fcntl
import importlib.util
import io
import json
import os
from pathlib import Path
import socket
import threading

import pytest

from control.friends import transport_gateway as module
from test_transport_enforcement import engine, envelope, registry
from test_transport_observation_mode import candidate, collector


def expire_operation():
    operation = module.CURRENT_OPERATION.get()
    operation.started -= 9
    operation.deadline -= 9


def entrypoint_for(monkeypatch, gateway, registry, initial, operation):
    filename = Path(__file__).resolve().parents[1]/'deploy/friends/awg-gateway.py'
    spec = importlib.util.spec_from_file_location('failure_serialization_entrypoint', filename)
    entrypoint = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(entrypoint)
    monkeypatch.setattr(entrypoint, 'ROOT', gateway.root)
    monkeypatch.setattr(entrypoint, 'paid_engine', lambda: gateway)
    (gateway.root/'settings.json').write_text(json.dumps(dict(network='10.1.0.0/24')))
    request = dict(operation=operation, paid=envelope(registry))
    if operation == 'prepare':
        request['token'] = 'c'*64
    if operation == 'register':
        request = {key: initial[key] for key in ('public_key', 'tcp_id', 'device')}
        request['paid'] = envelope(registry)
    monkeypatch.setattr(entrypoint.sys, 'stdin', io.TextIOWrapper(io.BytesIO(json.dumps(request).encode())))
    return entrypoint


@pytest.mark.parametrize('operation', ['reconcile', 'prepare', 'register'])
def test_slow_application_open_consumes_registration_budget(candidate, registry, monkeypatch, capsys, operation):
    gateway, current, live, initial = candidate
    gateway.accept(envelope(registry))
    gateway.apply()
    authority = gateway.path.read_bytes()
    entrypoint = entrypoint_for(monkeypatch, gateway, registry, initial, operation)
    original_open = Path.open
    lock_path = gateway.root/'application.lock'
    clock, handles, bodies, failures = [1000.0], [], [], []
    original_apply, original_accept, original_prepare = gateway.apply_serialized, gateway.accept, gateway.prepare

    def open_file(path, *args, **kwargs):
        handle = original_open(path, *args, **kwargs)
        if path == lock_path:
            handles.append(handle)
            clock[0] += 9
        return handle

    def apply(*args, **kwargs):
        bodies.append('apply')
        return original_apply(*args, **kwargs)

    def accept(*args, **kwargs):
        bodies.append('accept')
        return original_accept(*args, **kwargs)

    def prepare(*args, **kwargs):
        bodies.append('prepare')
        return original_prepare(*args, **kwargs)

    monkeypatch.setattr(module.time, 'monotonic', lambda: clock[0])
    monkeypatch.setattr(Path, 'open', open_file)
    monkeypatch.setattr(gateway, 'apply_serialized', apply)
    monkeypatch.setattr(gateway, 'accept', accept)
    monkeypatch.setattr(gateway, 'prepare', prepare)
    live['calls'].clear()
    try:
        entrypoint.register()
    except BaseException as error:
        failures.append(error)
    ack = capsys.readouterr().out
    queries = [command for command in live['calls'] if command[0] != 'systemctl']
    receipt = dict(errors=[str(error) for error in failures], bodies=bodies, queries=len(queries),
        ack=bool(ack), elapsed=gateway.metrics['total'])
    print(json.dumps(receipt))
    assert receipt == dict(errors=['TRANSPORT_OPERATION_DEADLINE'], bodies=[], queries=0, ack=False, elapsed=9.0)
    assert isinstance(failures[0], TimeoutError)
    assert failures[0].transport_context['elapsed'] == 9.0
    assert gateway.path.read_bytes() == authority
    assert not gateway.observation_path.exists()
    assert len(handles) == 1 and handles[0].closed
    assert module.CURRENT_OPERATION.get() is None
    with original_open(lock_path, 'a') as probe:
        fcntl.flock(probe, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert live['calls'] == [['systemctl', '--no-block', 'stop', *module.SERVICES]]


@pytest.mark.parametrize('operation', ['reconcile', 'prepare', 'register'])
@pytest.mark.parametrize('fault', ['fsync', 'deadline', 'context_exit'])
def test_failure_receipt_barrier_excludes_real_watch_notify_and_collector(
        candidate, registry, collector, monkeypatch, capsys, tmp_path, operation, fault):
    initial_gateway, current, live, initial = candidate
    initial_gateway.accept(envelope(registry))
    initial_gateway.apply()
    registration = module.Gateway(initial_gateway.gateway, clock=initial_gateway.clock,
        monotonic=initial_gateway.monotonic, run=initial_gateway.run)
    watcher = module.Gateway(initial_gateway.gateway, clock=initial_gateway.clock,
        monotonic=initial_gateway.monotonic, run=initial_gateway.run)
    entrypoint = entrypoint_for(monkeypatch, registration, registry, initial, operation)
    monkeypatch.setattr(module, 'Gateway', lambda *args, **kwargs: watcher)
    receipt_entered, release_receipt = threading.Event(), threading.Event()
    watch_boundary, release_watch = threading.Event(), threading.Event()
    failures, watch_failures, injected = [], [], []
    original_sync, original_flock, original_notify = os.fsync, fcntl.flock, module.notify
    stop_command = ['systemctl', '--no-block', 'stop', *module.SERVICES]
    original_apply = registration.apply_serialized

    def apply():
        original_apply()
        if fault == 'context_exit':
            injected.append(True)
            expire_operation()

    monkeypatch.setattr(registration, 'apply_serialized', apply)

    def sync(descriptor):
        filename = Path(os.readlink(f'/proc/self/fd/{descriptor}')).name
        if fault != 'context_exit' and threading.current_thread().name == 'registration' and filename == 'transport-attempt.pending' and not injected:
            injected.append(True)
            if fault == 'fsync':
                raise OSError(errno.EIO, 'synthetic mandatory sync failure')
            original_sync(descriptor)
            expire_operation()
            return
        if threading.current_thread().name == 'registration' and filename == 'transport-failure.json':
            receipt_entered.set()
            assert release_receipt.wait(5), 'test did not release diagnostic barrier'
        original_sync(descriptor)

    def flock(descriptor, flags):
        try:
            return original_flock(descriptor, flags)
        except BlockingIOError:
            if threading.current_thread().name == 'watcher' and Path(os.readlink(f'/proc/self/fd/{descriptor.fileno()}')).name == 'application.lock':
                watch_boundary.set()
                assert release_watch.wait(5)
                raise InterruptedError('bounded watcher stopped at contended application lock')
            raise

    def notify(value):
        original_notify(value)
        if value == 'WATCHDOG=1':
            watch_boundary.set()
            assert release_watch.wait(5)
            raise InterruptedError('bounded watcher stopped after forbidden heartbeat')

    def register():
        try:
            entrypoint.register()
        except BaseException as error:
            failures.append(error)

    def watch():
        try:
            module.watch(watcher.gateway, run=watcher.run)
        except BaseException as error:
            watch_failures.append(error)

    monkeypatch.setattr(module.os, 'fsync', sync)
    monkeypatch.setattr(module.fcntl, 'flock', flock)
    monkeypatch.setattr(module, 'notify', notify)
    channel = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    channel.bind(str(tmp_path/'notify.sock'))
    channel.setblocking(False)
    monkeypatch.setenv('NOTIFY_SOCKET', str(tmp_path/'notify.sock'))
    registration_thread = threading.Thread(target=register, name='registration')
    watch_thread = threading.Thread(target=watch, name='watcher')
    notices = []
    try:
        registration_thread.start()
        assert receipt_entered.wait(5), 'mandatory failure did not reach diagnostic fsync'
        stops_before_diagnostic_completion = live['calls'].count(stop_command)
        with (registration.root/'application.lock').open('a') as probe:
            try:
                original_flock(probe, fcntl.LOCK_EX | fcntl.LOCK_NB)
                lock_held = False
            except BlockingIOError:
                lock_held = True
        live['calls'].clear()
        watch_thread.start()
        assert watch_boundary.wait(5), 'watcher reached neither contention nor heartbeat'
        while True:
            try:
                notices.append(channel.recv(128).decode())
            except BlockingIOError:
                break
        during = dict(lock_held=lock_held, collector=collector()['status'],
            observation=registration.observation_path.exists(),
            queries=sum('show' in command or 'inbounduser' in command for command in live['calls']),
            heartbeat='WATCHDOG=1' in notices, ack=capsys.readouterr().out)
    finally:
        release_receipt.set()
        registration_thread.join(5)
        release_watch.set()
        if watch_thread.ident is not None:
            watch_thread.join(5)
        channel.close()
    assert not registration_thread.is_alive() and not watch_thread.is_alive()
    assert injected == [True]
    assert len(failures) == 1 and isinstance(failures[0], OSError if fault == 'fsync' else TimeoutError)
    if fault == 'fsync':
        assert failures[0].errno == errno.EIO
    assert len(watch_failures) == 1 and isinstance(watch_failures[0], InterruptedError)
    assert during == dict(lock_held=True, collector='unavailable', observation=False, queries=0, heartbeat=False, ack='')
    assert stops_before_diagnostic_completion == 1
    record = module.read(registration.root/'transport-failure.json')
    assert record['reason'] == ('FILESYSTEM_OR_OS_ERROR' if fault == 'fsync' else 'TRANSPORT_OPERATION_DEADLINE')
    assert record['phase'] == ('operation' if fault == 'context_exit' else 'persist_file')
    assert record['budget'] == 8
    if fault != 'fsync':
        assert record['elapsed'] >= 9
    assert stop_command in live['calls']
    assert capsys.readouterr().out == ''
    with (registration.root/'application.lock').open('a') as probe:
        original_flock(probe, fcntl.LOCK_EX | fcntl.LOCK_NB)


@pytest.mark.parametrize('operation', ['reconcile', 'prepare', 'register'])
def test_success_ack_after_context_exit_without_stop(candidate, registry, collector, monkeypatch, capsys, operation):
    gateway, current, live, initial = candidate
    entrypoint = entrypoint_for(monkeypatch, gateway, registry, initial, operation)
    original_remaining = module.Operation.remaining
    exit_checked = []
    original_apply = gateway.apply_serialized
    applied = []

    def apply():
        original_apply()
        applied.append(True)

    def remaining(operation):
        if applied:
            assert capsys.readouterr().out == ''
            with (gateway.root/'application.lock').open('a') as probe:
                with pytest.raises(BlockingIOError):
                    fcntl.flock(probe, fcntl.LOCK_EX | fcntl.LOCK_NB)
            exit_checked.append(True)
        return original_remaining(operation)

    monkeypatch.setattr(gateway, 'apply_serialized', apply)
    monkeypatch.setattr(module.Operation, 'remaining', remaining)
    entrypoint.register()
    assert exit_checked == [True]
    reply = json.loads(capsys.readouterr().out)
    assert reply.get('result', reply.get('transport')) == {'reconcile': 'applied', 'prepare': 'prepared', 'register': 'amneziawg-3.1'}[operation]
    assert not any('--no-block' in command for command in live['calls'])
    assert collector()['status'] == 'ok'


@pytest.mark.parametrize('boundary', ['open', 'flock', 'contended_deadline'])
@pytest.mark.parametrize('operation', ['reconcile', 'prepare', 'register'])
def test_lock_acquisition_failure_never_enters_body_or_acks(candidate, registry, monkeypatch, capsys, boundary, operation):
    gateway, current, live, initial = candidate
    gateway.accept(envelope(registry))
    gateway.apply()
    authority = gateway.path.read_bytes()
    entrypoint = entrypoint_for(monkeypatch, gateway, registry, initial, operation)
    original_open, original_flock = Path.open, fcntl.flock
    lock_path = gateway.root/'application.lock'
    owner = original_open(lock_path, 'a')
    failure = OSError(errno.EACCES, 'synthetic lock access failure')
    if boundary == 'contended_deadline':
        original_flock(owner, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def open_file(path, *args, **kwargs):
        if path == lock_path and boundary == 'open':
            raise failure
        return original_open(path, *args, **kwargs)

    def flock(handle, flags):
        if Path(os.readlink(f'/proc/self/fd/{handle.fileno()}')) == lock_path:
            if boundary == 'flock':
                raise failure
            try:
                return original_flock(handle, flags)
            except BlockingIOError:
                expire_operation()
                raise
        return original_flock(handle, flags)

    monkeypatch.setattr(Path, 'open', open_file)
    monkeypatch.setattr(module.fcntl, 'flock', flock)
    live['calls'].clear()
    try:
        with pytest.raises(TimeoutError if boundary == 'contended_deadline' else OSError) as caught:
            entrypoint.register()
        if boundary != 'contended_deadline':
            assert caught.value is failure
        else:
            with original_open(lock_path, 'a') as probe:
                with pytest.raises(BlockingIOError):
                    original_flock(probe, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert gateway.path.read_bytes() == authority
        assert live['calls'] == [['systemctl', '--no-block', 'stop', *module.SERVICES]]
        assert not gateway.observation_path.exists()
        assert capsys.readouterr().out == ''
        assert module.CURRENT_OPERATION.get() is None
    finally:
        owner.close()
    with original_open(lock_path, 'a') as probe:
        original_flock(probe, fcntl.LOCK_EX | fcntl.LOCK_NB)


@pytest.mark.parametrize('boundary', ['accept', 'apply', 'exit'])
def test_first_error_survives_cleanup_and_context_close(candidate, registry, monkeypatch, capsys, boundary):
    gateway, current, live, initial = candidate
    gateway.accept(envelope(registry))
    gateway.apply()
    entrypoint = entrypoint_for(monkeypatch, gateway, registry, initial, 'reconcile')
    failure = OSError(errno.EIO, 'synthetic first failure')
    original_open = Path.open
    original_apply = gateway.apply_serialized
    stages = []

    class BrokenClose:
        def __init__(self, handle):
            self.handle = handle

        def __enter__(self):
            return self.handle

        def __exit__(self, *args):
            self.handle.close()
            stages.append('release')
            raise OSError(errno.EBADF, 'synthetic secondary context exit failure')

    def open_file(path, *args, **kwargs):
        handle = original_open(path, *args, **kwargs)
        return BrokenClose(handle) if path.name == 'application.lock' else handle

    def fail(*args):
        raise failure

    def apply():
        original_apply()
        expire_operation()

    def stop():
        assert not gateway.observation_path.exists()
        with original_open(gateway.root/'application.lock', 'a') as probe:
            with pytest.raises(BlockingIOError):
                fcntl.flock(probe, fcntl.LOCK_EX | fcntl.LOCK_NB)
        stages.append('stop')
        raise PermissionError('synthetic stop failure')

    def error_receipt():
        stages.append('error_receipt')
        raise OSError(errno.ENOSPC, 'synthetic secondary receipt failure')

    monkeypatch.setattr(Path, 'open', open_file)
    monkeypatch.setattr(gateway, 'stop_all', stop)
    monkeypatch.setattr(gateway, 'failure', error_receipt)
    monkeypatch.setattr(gateway, 'accept' if boundary == 'accept' else 'apply_serialized', apply if boundary == 'exit' else fail)
    with pytest.raises(TimeoutError if boundary == 'exit' else OSError) as caught:
        entrypoint.register()
    if boundary != 'exit':
        assert caught.value is failure
    record = module.read(gateway.root/'transport-failure.json')
    assert record['errno'] == (None if boundary == 'exit' else errno.EIO)
    assert stages == ['stop', 'error_receipt', 'release']
    assert capsys.readouterr().out == ''
    assert module.CURRENT_OPERATION.get() is None
    with original_open(gateway.root/'application.lock', 'a') as probe:
        fcntl.flock(probe, fcntl.LOCK_EX | fcntl.LOCK_NB)
