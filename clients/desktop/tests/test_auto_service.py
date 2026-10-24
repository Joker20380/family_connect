import base64
import copy
from contextlib import nullcontext
import json
import os
from pathlib import Path
from queue import Queue
import socket
import stat
import sys
import threading
import time
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'linux'))
import auto_ipc
from auto_intent import AutoIntent
import auto_service as service
import mesh_ipc as ipc
import mesh_intent
from mesh_intent import Intent


def encoded(size, value=b'x'):
    return base64.b64encode(value * size).decode()


def selection():
    return dict(preferred='', materials=dict(identity=encoded(64), anchor=encoded(32, b'a'),
                wireguard_private=encoded(32, b's'), wireguard_public=encoded(32, b'w'),
                profile='P1', country='nl', normal_floors=[]))


class Manager:
    def __init__(self):
        self.descriptor = None

    def store(self, descriptor):
        assert self.descriptor is None
        self.descriptor = os.dup(descriptor)

    def remove(self):
        if self.descriptor is not None:
            os.close(self.descriptor)
            self.descriptor = None


@pytest.fixture
def intent(tmp_path):
    manager = Manager()
    owner = AutoIntent(tmp_path / 'intent.json', 1000, manager, expected_owner=os.getuid())
    try:
        yield owner
    finally:
        owner.close()
        manager.remove()


def wait(predicate):
    deadline = time.monotonic() + 3
    while not predicate() and time.monotonic() < deadline:
        time.sleep(.01)
    assert predicate()


class Runtime:
    def __init__(self, record, selection, terminal):
        self.record = copy.deepcopy(record)
        self.material = copy.deepcopy(selection)
        self.terminal = terminal
        self.calls, self.finish = [], threading.Event()
        self.coordinator = SimpleNamespace(failed=False, thread=None, abort=self.abort, close=self.close, status=self.status)

    def start(self):
        self.calls.append('start')
        self.coordinator.thread = threading.Thread(target=self.finish.wait)
        self.coordinator.thread.start()

    def status(self):
        return dict(policy=dict(state='CONNECTED', desired_connected=True))

    def close(self):
        self.calls.append('release')
        self.finish.set()
        self.coordinator.thread.join()

    def abort(self):
        self.calls.append('retain_guard')
        self.finish.set()
        self.coordinator.thread.join()

    def dispose(self):
        self.calls.append('dispose')
        assert self.coordinator.thread is None or not self.coordinator.thread.is_alive()


@pytest.fixture
def owner(intent):
    runtimes, cleanups = [], []
    def factory(*args):
        result = Runtime(*args)
        runtimes.append(result)
        return result
    controller = service.Controller(intent, factory=factory, cleanup=lambda record, keep: cleanups.append((record, keep)), gate=nullcontext)
    try:
        yield controller, runtimes, cleanups
    finally:
        controller.shutdown()


class ControlledRuntime(Runtime):
    def __init__(self, *args):
        super().__init__(*args)
        self.started, self.disposing, self.disposed = (threading.Event() for _ in range(3))
        self.allow_dispose = threading.Event()
        self.allow_dispose.set()
        self.dispose_error = False

    def start(self):
        super().start()
        self.started.set()

    def dispose(self):
        self.disposing.set()
        assert self.allow_dispose.wait(3)
        super().dispose()
        if self.dispose_error:
            raise OSError('synthetic dispose failure')
        self.disposed.set()


@pytest.fixture
def lifecycle(intent):
    runtimes, created, cleanups = [], Queue(), []
    def factory(*args):
        runtime = ControlledRuntime(*args)
        runtimes.append(runtime)
        created.put(runtime)
        return runtime
    controller = service.Controller(intent, factory, lambda record, keep: cleanups.append((record, keep)), gate=nullcontext)
    try:
        yield controller, created, runtimes, cleanups
    finally:
        for runtime in runtimes:
            runtime.allow_dispose.set()
        if controller.fatal:
            with pytest.raises(ValueError):
                controller.shutdown()
        else:
            controller.shutdown()


def started_runtime(controller, created):
    assert controller.start(selection())
    runtime = created.get(timeout=3)
    assert runtime.started.wait(3)
    return runtime


def joined(thread):
    thread.join(timeout=3)
    assert not thread.is_alive()


def test_disconnected_is_not_published_during_final_dispose(lifecycle):
    controller, created, runtimes, _ = lifecycle
    runtime = started_runtime(controller, created)
    runtime.allow_dispose.clear()
    thread, previous = controller.thread, controller.record['generation']
    assert controller.stop(previous)
    assert runtime.disposing.wait(3)
    assert not controller.desired and not controller.intent.desired()
    assert controller.status()['state'] == 'DISCONNECTING'
    assert controller.thread is thread and thread.is_alive()
    assert not controller.start(selection()) and len(runtimes) == 1
    runtime.allow_dispose.set()
    joined(thread)
    assert runtime.disposed.is_set()
    assert controller.status()['state'] == 'DISCONNECTED'
    current = started_runtime(controller, created)
    assert controller.record['generation'] != previous
    assert not controller.stop(previous)
    assert controller.desired and controller.intent.desired()
    assert current.calls == ['start'] and not current.disposing.is_set()


def test_start_reaps_finished_owner_without_status_or_retry(lifecycle):
    controller, created, runtimes, _ = lifecycle
    runtime = started_runtime(controller, created)
    thread, previous = controller.thread, controller.record['generation']
    assert controller.stop(previous)
    joined(thread)
    assert runtime.disposed.is_set()
    started_runtime(controller, created)
    assert len(runtimes) == 2 and controller.record['generation'] != previous
    assert controller.thread is not thread


def test_repeated_stop_after_owner_exit_is_idempotent_without_status(lifecycle):
    controller, created, runtimes, cleanups = lifecycle
    runtime = started_runtime(controller, created)
    thread, previous = controller.thread, controller.record['generation']
    assert controller.stop(previous)
    joined(thread)
    assert controller.stop(previous)
    assert controller.thread is None and controller.status()['state'] == 'DISCONNECTED'
    assert runtime.calls == ['start', 'release', 'dispose'] and not cleanups
    started_runtime(controller, created)
    assert len(runtimes) == 2


def test_completed_stop_can_retry_failed_revocation_write_without_repeating_cleanup(lifecycle, monkeypatch):
    controller, created, _, cleanups = lifecycle
    runtime = started_runtime(controller, created)
    thread, previous = controller.thread, controller.record['generation']
    original = mesh_intent.private_write
    def rejected(*args):
        raise OSError('synthetic persistence failure')
    monkeypatch.setattr(mesh_intent, 'private_write', rejected)
    with pytest.raises(OSError):
        controller.stop(previous)
    assert not controller.desired and controller.cancel.is_set()
    joined(thread)
    assert controller.intent.desired()
    monkeypatch.setattr(mesh_intent, 'private_write', original)
    assert controller.stop(previous)
    assert not controller.intent.desired()
    assert controller.thread is None and controller.status()['state'] == 'DISCONNECTED'
    assert runtime.calls == ['start', 'release', 'dispose'] and not cleanups
    started_runtime(controller, created)


def test_owner_tail_and_repeated_stop_cannot_strand_disconnecting(lifecycle, monkeypatch):
    controller, created, runtimes, _ = lifecycle
    returned, allow_exit = threading.Event(), threading.Event()
    original = controller.run
    def held_run(value):
        original(value)
        returned.set()
        assert allow_exit.wait(3)
    monkeypatch.setattr(controller, 'run', held_run)
    runtime = started_runtime(controller, created)
    thread, previous = controller.thread, controller.record['generation']
    try:
        assert controller.stop(previous)
        assert returned.wait(3) and runtime.disposed.is_set()
        assert controller.status()['state'] == 'DISCONNECTING'
        assert controller.thread is thread and thread.is_alive()
        assert not controller.start(selection()) and len(runtimes) == 1
        assert controller.stop(previous)
    finally:
        allow_exit.set()
    joined(thread)
    assert controller.stop(previous)
    assert controller.status()['state'] == 'DISCONNECTED'
    assert controller.thread is None
    started_runtime(controller, created)


@pytest.mark.parametrize('failure', ['close', 'dispose', 'cleanup'])
def test_lifecycle_failure_is_not_reset_by_stop_or_reap(lifecycle, monkeypatch, failure):
    controller, created, runtimes, _ = lifecycle
    def rejected(*args):
        raise OSError('synthetic cleanup failure')
    if failure == 'cleanup':
        controller.intent.begin(selection())
        controller.record, controller.desired = controller.intent.read(), True
        controller.recover(None)
        monkeypatch.setattr(controller, 'cleanup', rejected)
    else:
        runtime = started_runtime(controller, created)
        if failure == 'close':
            runtime.coordinator.close = rejected
        else:
            runtime.dispose_error = True
    previous = controller.record['generation']
    assert controller.stop(previous)
    joined(controller.thread)
    assert controller.status()['state'] == 'FAILED' and controller.fatal
    assert not controller.start(selection())
    assert controller.stop(previous)
    if controller.thread is not None:
        joined(controller.thread)
    status = controller.status()
    assert status['state'] == 'FAILED' and status['reason'] == 'INTERNAL' and controller.fatal
    assert not controller.start(selection())
    assert len(runtimes) == (0 if failure == 'cleanup' else 1)


def test_real_coordinator_callback_and_process_close_finish_before_owner_handoff(intent):
    callback_entered, allow_callback, disconnect_sent = (threading.Event() for _ in range(3))
    process_closing, allow_close, disposed = (threading.Event() for _ in range(3))
    created, callbacks, runtimes = Queue(), [], []
    class Process:
        def __init__(self, host):
            self.generation = host.generation
        def submit(self, action, *args, **kwargs):
            if action == 'disconnect':
                disconnect_sent.set()
            value = dict(generation=self.generation, state='DISCONNECTED' if action == 'disconnect' else 'FAILED',
                         desired_connected=False, retry_at_ms=0, events=[], events_dropped=0)
            done = threading.Event()
            done.set()
            return SimpleNamespace(done=done, wait=lambda timeout: dict(ok=True, snapshot=value))
        def close(self):
            process_closing.set()
            assert allow_close.wait(3)
    def factory(record, value, terminal):
        if runtimes:
            runtime = ControlledRuntime(record, value, terminal)
        else:
            def held_terminal():
                callback_entered.set()
                assert allow_callback.wait(3)
                terminal()
                callbacks.append(record['generation'])
            runtime = service.Runtime.__new__(service.Runtime)
            runtime.guard, runtime.stores = SimpleNamespace(close=disposed.set), []
            runtime.preferred = runtime.last = ''
            runtime.platform = SimpleNamespace(underlying=SimpleNamespace(read=lambda context: None),
                cancel_health=lambda: None, snapshot=lambda: {}, mesh=SimpleNamespace(snapshot=lambda: {}))
            runtime.coordinator = service.Coordinator(runtime.guard, runtime.platform, 1,
                process_factory=Process, terminal=held_terminal, guard_prepared=True)
        runtimes.append(runtime)
        created.put(runtime)
        return runtime
    controller = service.Controller(intent, factory, gate=nullcontext)
    try:
        assert controller.start(selection())
        runtime = created.get(timeout=3)
        assert callback_entered.wait(3)
        thread, previous = controller.thread, controller.record['generation']
        assert controller.stop(previous) and disconnect_sent.wait(3)
        assert controller.status()['state'] == 'DISCONNECTING'
        assert not controller.desired and not intent.desired()
        assert not controller.start(selection()) and not disposed.is_set()
        allow_callback.set()
        assert process_closing.wait(3)
        assert runtime.coordinator.thread.is_alive() and not disposed.is_set()
        assert controller.status()['state'] == 'DISCONNECTING'
        assert not controller.start(selection())
        allow_close.set()
        joined(thread)
        assert disposed.is_set() and not runtime.coordinator.thread.is_alive()
        assert callbacks == [previous]
        current = started_runtime(controller, created)
        assert not controller.stop(previous) and controller.desired and intent.desired()
        assert current.calls == ['start'] and callbacks == [previous]
    finally:
        allow_callback.set()
        allow_close.set()
        controller.shutdown()


def request(action, **extra):
    return dict(schema=1, id=1, action=action, **extra)


def test_auto_credentials_survive_restart_only_in_sealed_memory(intent):
    value = selection()
    value['materials']['normal_floors'] = [dict(payload=encoded(8192), signature=encoded(64)) for _ in range(2)]
    intent.begin(value)
    assert set(json.loads(intent.path.read_text())) == {'schema', 'uid', 'generation', 'desired', 'recoveries'}
    assert all(value['materials'][key] not in intent.path.read_text() for key in ('identity', 'wireguard_private', 'anchor'))
    intent.close()
    restored = AutoIntent(intent.path, 1000, intent.notifier, expected_owner=os.getuid())
    try:
        assert restored.recover(os.dup(intent.notifier.descriptor)) == value
        assert restored.read()['recoveries'] == 1
        restored.revoke()
        assert os.pread(intent.notifier.descriptor, 1, 0) == b'\0'
    finally:
        restored.close()


def test_manual_mesh_cannot_consume_auto_memory_contract(intent):
    intent.begin(selection())
    manual = Intent(intent.path, 1000, intent.notifier, expected_owner=os.getuid())
    try:
        with pytest.raises(ValueError):
            manual.recover(os.dup(intent.notifier.descriptor))
    finally:
        manual.close()


@pytest.mark.parametrize('field,value', [('profile', 'P2'), ('country', 'us'), ('wireguard_private', encoded(31)),
    ('identity', encoded(32)), ('normal_floors', [{}]), ('normal_floors', [dict(payload=encoded(8193), signature=encoded(64))]),
    ('normal_floors', [dict(payload=encoded(1), signature=encoded(64))] * 3)])
def test_invalid_material_is_rejected_before_intent_persistence(intent, field, value):
    body = selection()
    body['materials'][field] = value
    with pytest.raises(ValueError):
        intent.begin(body)
    assert intent.descriptor is None and not intent.path.exists()


@pytest.mark.parametrize('bad', [request('shell', command='whoami'), request('stop'), request('stop', generation='A'*32),
    request('status', generation='a'*32), request('start', selection={'materials':'private','preferred':''}),
    request('start', selection={'materials':{},'preferred':'mesh'}), dict(schema=True,id=1,action='status'),
    dict(schema=1,id=True,action='status'), request('status', path='/etc/passwd')])
def test_only_exact_bounded_commands_are_accepted(bad):
    with pytest.raises(ValueError):
        auto_ipc.validate_request(bad)


def test_start_replies_with_durable_intent_and_never_echoes_material(owner):
    controller, runtimes, _ = owner
    reply = service.dispatch(controller, request('start', selection=selection()))
    assert reply['ok'] and reply['desired_connected']
    assert reply['generation'] == controller.intent.read()['generation']
    assert controller.intent.notifier.descriptor is not None
    assert encoded(64) not in json.dumps(reply) and 'materials' not in json.dumps(reply)
    wait(lambda: bool(runtimes) and runtimes[0].coordinator.thread is not None)
    assert not service.dispatch(controller, request('start', selection=selection()))['ok']


def test_stop_revokes_before_async_cleanup_and_old_generation_cannot_stop_new_session(owner):
    controller, runtimes, _ = owner
    controller.start(selection())
    wait(lambda: bool(runtimes) and runtimes[0].coordinator.thread is not None)
    previous = controller.record['generation']
    assert controller.stop(previous)
    assert not controller.intent.desired() and not controller.desired
    wait(lambda: controller.status()['state'] == 'DISCONNECTED')
    assert runtimes[0].calls == ['start', 'release', 'dispose']
    assert controller.intent.notifier.descriptor is None
    assert controller.start(selection())
    assert controller.record['generation'] != previous
    assert not controller.stop(previous)
    assert controller.desired


def test_service_shutdown_keeps_intent_and_guard_for_manager_restart(owner):
    controller, runtimes, _ = owner
    controller.start(selection())
    wait(lambda: bool(runtimes) and runtimes[0].coordinator.thread is not None)
    controller.shutdown()
    assert controller.intent.desired() and controller.intent.notifier.descriptor is not None
    assert runtimes[0].calls == ['start', 'retain_guard', 'dispose']


def test_stop_still_cancels_policy_if_revocation_journal_write_fails(owner, monkeypatch):
    controller, runtimes, _ = owner
    controller.start(selection())
    wait(lambda: bool(runtimes) and runtimes[0].coordinator.thread is not None)
    def rejected(*args):
        raise OSError('synthetic persistence failure')
    monkeypatch.setattr(mesh_intent, 'private_write', rejected)
    descriptor = os.dup(controller.intent.notifier.descriptor)
    try:
        with pytest.raises(OSError):
            controller.stop(controller.record['generation'])
        assert not controller.desired and os.pread(descriptor, 1, 0) == b'\0'
        wait(lambda: controller.status()['state'] == 'DISCONNECTED')
        assert runtimes[0].calls == ['start', 'release', 'dispose']
    finally:
        os.close(descriptor)


def test_late_reply_cannot_report_connected_after_stop_even_if_cleanup_is_waiting(owner):
    controller, runtimes, _ = owner
    controller.start(selection())
    wait(lambda: bool(runtimes) and runtimes[0].coordinator.thread is not None)
    runtime = runtimes[0]
    entered, finish = threading.Event(), threading.Event()
    def close():
        entered.set()
        assert finish.wait(3)
        runtime.close()
    runtime.coordinator.close = close
    try:
        assert controller.stop(controller.record['generation'])
        assert entered.wait(3)
        status = controller.status()
        assert status['state'] == 'DISCONNECTING' and not status['desired_connected']
    finally:
        finish.set()
    wait(lambda: controller.status()['state'] == 'DISCONNECTED')


def test_terminal_authorization_revokes_restart_but_cleanup_still_requires_disconnect(owner):
    controller, runtimes, _ = owner
    controller.start(selection())
    wait(lambda: bool(runtimes) and runtimes[0].coordinator.thread is not None)
    runtimes[0].terminal()
    assert not controller.intent.desired() and 'release' not in runtimes[0].calls
    assert controller.stop(controller.record['generation'])
    wait(lambda: controller.status()['state'] == 'DISCONNECTED')


def test_stop_during_factory_initialization_never_starts_policy(intent):
    entered, finish = threading.Event(), threading.Event()
    runtimes, cleanups = [], []
    def factory(*args):
        entered.set()
        assert finish.wait(3)
        runtime = Runtime(*args)
        runtimes.append(runtime)
        return runtime
    controller = service.Controller(intent, factory, lambda record, keep: cleanups.append(keep), gate=nullcontext)
    try:
        controller.start(selection())
        assert entered.wait(3)
        assert controller.stop(controller.record['generation'])
        assert not intent.desired()
        finish.set()
        wait(lambda: controller.status()['state'] == 'DISCONNECTED')
        assert runtimes[0].calls == ['dispose'] and cleanups == [False]
    finally:
        finish.set()
        controller.shutdown()


def test_missing_restart_material_is_failed_not_connected_and_explicit_stop_cleans(owner):
    controller, runtimes, cleanups = owner
    controller.intent.begin(selection())
    controller.record, controller.desired = controller.intent.read(), True
    controller.recover(None)
    assert controller.status()['reason'] == 'RECOVERY_CREDENTIAL_UNAVAILABLE'
    assert not runtimes and not cleanups
    assert controller.stop(controller.record['generation'])
    wait(lambda: controller.status()['state'] == 'DISCONNECTED')
    assert cleanups == [(controller.record, False)]


def test_unexpected_native_exit_is_fatal_but_does_not_revoke_restart(intent):
    controller = service.Controller(intent, Runtime, gate=nullcontext)
    controller.start(selection())
    wait(lambda: controller.runtime is not None and controller.runtime.coordinator.thread is not None)
    controller.runtime.finish.set()
    wait(lambda: controller.fatal)
    with pytest.raises(ValueError):
        controller.shutdown()
    assert intent.desired()


def exchange(controller, value, uid=None):
    client, server = socket.socketpair()
    errors = []
    def respond():
        with server:
            try:
                service.respond(server, os.getuid() if uid is None else uid, controller)
            except Exception as error:
                errors.append(error)
    thread = threading.Thread(target=respond)
    thread.start()
    try:
        try:
            ipc.send(client.fileno(), value, auto_ipc.MAX_REQUEST, time.monotonic()+2)
            reply = ipc.receive(client.fileno(), auto_ipc.MAX_REPLY, time.monotonic()+2)
        except (EOFError, ConnectionResetError, BrokenPipeError):
            reply = None
    finally:
        client.close()
        thread.join(timeout=3)
    assert not thread.is_alive()
    return reply, errors


def test_real_unix_peer_credentials_reject_another_uid_before_dispatch(owner):
    controller, runtimes, _ = owner
    reply, errors = exchange(controller, request('start', selection=selection()), uid=os.getuid()+1)
    assert reply is None and errors == [] and not runtimes and not controller.intent.path.exists()


def test_real_unix_frames_start_query_and_stop_exact_generation(owner):
    controller, _, _ = owner
    reply, errors = exchange(controller, request('start', selection=selection()))
    assert reply['ok'] and not errors
    status, errors = exchange(controller, request('status'))
    assert not errors and status['generation'] == reply['generation']
    stopped, errors = exchange(controller, request('stop', generation=reply['generation']))
    assert not errors and stopped['ok'] and not stopped['desired_connected']
    wait(lambda: controller.status()['state'] == 'DISCONNECTED')


def test_malformed_selection_cannot_crash_server_during_request_erasure(owner):
    reply, errors = exchange(owner[0], request('start', selection=dict(materials='private', preferred='')))
    assert reply is None and len(errors) == 1 and isinstance(errors[0], ipc.ProtocolError)


def test_service_unit_preserves_privilege_and_memory_contract():
    unit = (Path(service.__file__).parent / 'family-connect-auto@.service').read_text()
    for required in ('FileDescriptorStoreMax=1', 'FileDescriptorStorePreserve=restart', 'ProtectSystem=strict',
                     'ProtectHome=yes', 'NoNewPrivileges=yes', 'LimitCORE=0', 'KillMode=control-group',
                     'ReadWritePaths=/run -/etc/family-connect/awg -/etc/family-connect/tcp'):
        assert required in unit
    assert 'Environment=' not in unit and 'PrivateNetwork=' not in unit


def test_mismatched_fd_store_name_is_rejected(tmp_path):
    with pytest.raises(ValueError):
        AutoIntent(tmp_path / 'intent.json', 1000, SimpleNamespace(name=Intent.name))


def test_uncertain_intent_commit_is_fatal_not_an_unstoppable_disconnected_owner(intent, monkeypatch):
    original = mesh_intent.private_write
    def uncertain(*args):
        original(*args)
        raise OSError('synthetic failure after rename')
    controller = service.Controller(intent, Runtime, gate=nullcontext)
    monkeypatch.setattr(mesh_intent, 'private_write', uncertain)
    with pytest.raises(OSError):
        controller.start(selection())
    assert controller.fatal and controller.state == 'FAILED'
    assert controller.thread is None and controller.runtime is None
    assert controller.intent.descriptor is None and controller.intent.notifier.descriptor is None
    assert controller.intent.read()['desired']
    with pytest.raises(ValueError):
        controller.shutdown()
    restarted = service.Controller(intent, Runtime, gate=nullcontext)
    restarted.recover(None)
    assert restarted.status()['state'] == 'FAILED' and restarted.status()['generation']
    assert restarted.status()['reason'] == 'RECOVERY_CREDENTIAL_UNAVAILABLE'


@pytest.mark.parametrize('conflict', ['', 'mesh', 'tcp', 'awg', 'awg-journal', 'store-failure'])
def test_runtime_reserves_before_real_adapters_and_refuses_existing_manual_vpn(tmp_path, monkeypatch, conflict):
    events = []
    record = dict(uid=1000, generation='a'*32, recoveries=3)
    class Guard:
        def __init__(self, uid, generation):
            self.uid, self.generation, self.directory, self.path = uid, generation, tmp_path, tmp_path/'guard.json'
            self.record = None
            self.system = SimpleNamespace(links=lambda: [dict(ifname='fcawg12345678')] if conflict == 'awg' else [])
        def acquire(self):
            events.append('reserve-guard')
            self.record = dict(current=dict(mode='blocked'))
        def close(self):
            events.append('close-guard-fd')
    class Store:
        def __init__(self, path, uid, receipt=False):
            events.append(('store', path, uid, receipt))
            if conflict == 'store-failure' and path == service.MESH_STATE:
                raise OSError('synthetic unsafe store')
        def close(self):
            events.append('close-store-fd')
    gate = os.open(tmp_path/'gate', os.O_CREAT | os.O_RDWR, 0o600)
    original = os.path.lexists
    monkeypatch.setattr(service, 'locked', lambda path: os.dup(gate))
    monkeypatch.setattr(service, 'Guard', Guard)
    monkeypatch.setattr(service, 'CacheStore', Store)
    monkeypatch.setattr(service, 'HintStore', lambda path, uid: SimpleNamespace(last=lambda country: 'tcp'))
    monkeypatch.setattr(service.os.path, 'lexists', lambda path: (
        True if str(path) == ('/run/family-connect-awg/active.json' if conflict == 'awg-journal' else
            '/run/family-connect-'+conflict+('/active.json' if conflict == 'mesh' else '/active'))
        else False if str(path).startswith('/run/family-connect-') else original(path)))
    try:
        if conflict:
            with pytest.raises((OSError, ValueError)):
                service.Runtime(record, selection(), lambda: None)
            assert events[-1] == 'close-guard-fd'
            if conflict != 'store-failure':
                assert events == ['close-guard-fd']
            else:
                assert 'close-store-fd' in events
        else:
            runtime = service.Runtime(record, selection(), lambda: None)
            try:
                assert events[0] == 'reserve-guard'
                assert runtime.coordinator.host.guard_prepared and runtime.coordinator.generation == 4
                assert runtime.platform.mesh.network.auto_guard is runtime.guard
                assert runtime.platform.mesh.network.journal == tmp_path/'mesh.json'
                assert runtime.last == 'tcp' and runtime.platform.material == selection()['materials']
            finally:
                runtime.dispose()
            assert events.count('close-store-fd') == 3
    finally:
        os.close(gate)


@pytest.mark.parametrize('keep', [True, False])
def test_crash_reconciliation_closes_only_owned_attempts_before_optional_release(tmp_path, monkeypatch, keep):
    events = []
    (tmp_path/'guard.json').touch()
    (tmp_path/'mesh.json').touch()
    class Guard:
        directory = tmp_path
        def __init__(self, uid, generation):
            assert uid == 1000 and generation == 'a'*32
        def __enter__(self):
            return self
        def __exit__(self, *args):
            events.append('close-lock')
        def acquire(self):
            events.append('block')
        def release(self):
            events.append('release')
    class Network:
        journal, owns_journal = tmp_path/'mesh.json', True
        def restore(self):
            events.append('restore-mesh')
        def cleanup(self):
            events.append('close-mesh')
            self.owns_journal = False
    monkeypatch.setattr(service, 'DIRECTORY', tmp_path)
    monkeypatch.setattr(service, 'Guard', Guard)
    monkeypatch.setattr(service, 'NormalCandidate', lambda guard: SimpleNamespace(close=lambda context: events.append('close-normal')))
    monkeypatch.setattr(service, 'mesh_network', lambda guard: Network())
    service.reconcile(dict(uid=1000, generation='a'*32), keep)
    assert events == ['block', 'close-normal', 'restore-mesh', 'close-mesh'] + ([] if keep else ['release']) + ['close-lock']


@pytest.mark.parametrize('failure',[False,True])
def test_catalog_command_returns_public_floor_only_and_never_starts_runtime(intent,failure):
    events=[]
    envelope=dict(payload=encoded(128),signature=encoded(64))
    def catalog(uid):
        assert uid==1000
        events.append('read')
        if failure:raise ValueError('Damaged floor')
        return envelope
    controller=service.Controller(intent,lambda *_:pytest.fail('Read command started runtime'),gate=nullcontext,catalog=catalog)
    reply=service.dispatch(controller,dict(schema=1,id=4,action='catalog'))
    assert reply==dict(schema=1,id=4,ok=not failure,catalog=None if failure else envelope)
    assert events==['read'] and controller.record is None


@pytest.mark.parametrize('existing',[False,True])
def test_socket_directory_explicit_mode_survives_restrictive_unit_umask(tmp_path,monkeypatch,existing):
    path=tmp_path/'ipc'
    monkeypatch.setattr(service,'SOCKET_DIRECTORY',path)
    original_stat=Path.lstat;original_fstat=os.fstat
    def root_info(info):
        values=list(info);values[4]=0
        return os.stat_result(values)
    monkeypatch.setattr(Path,'lstat',lambda self:root_info(original_stat(self)))
    monkeypatch.setattr(os,'fstat',lambda descriptor:root_info(original_fstat(descriptor)))
    if existing:path.mkdir(mode=0o700)
    previous=os.umask(0o077)
    try:service.directory(path,0o711)
    finally:os.umask(previous)
    assert stat.S_IMODE(original_stat(path).st_mode)==0o711


def test_old_socket_directory_with_foreign_entry_is_not_made_traversable(tmp_path,monkeypatch):
    path=tmp_path/'ipc';path.mkdir(mode=0o700);(path/'foreign').touch()
    monkeypatch.setattr(service,'SOCKET_DIRECTORY',path)
    original=Path.lstat
    def root_info(self):
        values=list(original(self));values[4]=0
        return os.stat_result(values)
    monkeypatch.setattr(Path,'lstat',root_info)
    with pytest.raises(ValueError):service.directory(path,0o711)
    assert stat.S_IMODE(original(path).st_mode)==0o700
