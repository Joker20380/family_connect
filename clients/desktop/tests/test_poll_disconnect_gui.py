import os
import json
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from queue import Queue
import threading
from types import SimpleNamespace

import pytest

pytest.importorskip('gi')
pytestmark = pytest.mark.skipif(not os.environ.get('DISPLAY'), reason='Real GTK display required')

import app as module
import backend


@pytest.fixture
def reopened_app(normal_owner, monkeypatch):
    module.Adw.init()
    application = module.App(smoke=True)
    application.friends_owner_class = None
    application.ru = False
    monkeypatch.setattr(module, 'backend', lambda: normal_owner.driver)
    initialized = Future()
    initialized.set_result(application.initialize())
    application.complete('initialized', initialized, application.revision, None)
    assert application.active and application.selected() == normal_owner.ident
    application.poll_pool.shutdown()
    application.poll_pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix='fc-poll')
    completions = Queue()
    original_idle = module.GLib.idle_add

    def idle(callback, *arguments):
        if callback == application.complete:
            completions.put(arguments)
            return 0
        return original_idle(callback, *arguments)

    monkeypatch.setattr(module.GLib, 'idle_add', idle)
    yield application, completions
    normal_owner.release.set()
    application.pool.shutdown(wait=True, cancel_futures=True)
    application.poll_pool.shutdown(wait=True, cancel_futures=True)
    application.busy = False
    application.close(True)


@pytest.mark.parametrize('health', [False, True])
def test_reopened_gui_one_disconnect_ignores_slow_poll(normal_owner, reopened_app, health):
    application, completions = reopened_app
    normal_owner.block_at = 'health' if health else 'profiles'
    if health:
        application.recovery.arm(normal_owner.ident)
        application.recovery.next_check = 0
    application.refresh()
    assert normal_owner.entered.wait(5)
    application.toggle_vpn()
    assert application.connection_action == 'STOPPING' and application.busy
    application.toggle_vpn()
    application.refresh()
    foreground = completions.get(timeout=5)
    assert foreground[0] == 'state'
    application.complete(*foreground)
    assert normal_owner.downs == [normal_owner.ident], application.detail_text
    assert not normal_owner.active and application.active is False
    assert 'Operation failed' not in application.detail_text
    normal_owner.release.set()
    late = completions.get(timeout=5)
    application.complete(*late)
    assert application.active is False and not application.busy and not application.polling
    assert normal_owner.downs == [normal_owner.ident]


def test_gui_real_owner_failure_remains_visible(normal_owner, reopened_app):
    application, completions = reopened_app
    with backend.connection_operation(owner='a'*64) as lease:
        lease.reserve()
    application.toggle_vpn()
    application.complete(*completions.get(timeout=5))
    assert normal_owner.active and normal_owner.downs == []
    assert 'Connection recovery is pending' in application.detail_text


def test_gui_prestart_and_unknown_remain_distinct(normal_owner, reopened_app, monkeypatch):
    application, _ = reopened_app
    monkeypatch.setattr(application, 'transport_id', lambda: 'awg' if normal_owner.ident.startswith('fcawg') else 'tcp')
    failure = backend.PreStartRejected('TRANSPORT_BUSY')
    failure.operation_diagnostic = dict(category='TRANSPORT_BUSY', phase='IDLE', outcome='PRE_START_REJECTED',
        cleanup_confirmed=True, generation=2, pending=False)
    future = Future();future.set_exception(failure)
    application.complete('initialized', future, application.revision, normal_owner.ident)
    application.render()
    assert 'TRANSPORT_BUSY' in application.detail_text and not application.active
    assert application.diagnostics.current['first_failure'] == 'TRANSPORT_BUSY'
    unknown = backend.RecoveryRequired('PENDING_OPERATION')
    unknown.operation_diagnostic = dict(category='PENDING_OPERATION', phase='RECOVERY_REQUIRED', outcome='OUTCOME_UNKNOWN',
        cleanup_confirmed=False, generation=3, pending=True)
    future = Future();future.set_exception(unknown)
    application.complete('poll', future, application.revision, application.selected())
    application.render()
    assert 'recovery required' in application.detail_text
    assert 'Waiting for completion' not in application.detail_text
    assert application.diagnostics.current['normal_operation']['pending'] is True


@pytest.mark.parametrize('kind', ['poll', 'health'])
def test_stale_generation_never_becomes_health_failure(normal_owner, reopened_app, kind):
    application, _ = reopened_app
    application.recovery.arm(normal_owner.ident)
    application.polling = True
    stale = Future()
    stale.set_exception(backend.StaleConnection('changed'))
    application.complete(kind, stale, application.revision, normal_owner.ident)
    assert application.active and not application.polling and not application.poll_error
    assert application.recovery.failures == 0 and application.recovery.attempts == 0
    assert normal_owner.downs == []


@pytest.mark.parametrize('close_request', [False, True])
def test_closed_gui_cancels_queued_disconnect(normal_owner, reopened_app, close_request):
    application, completions = reopened_app
    held, release = threading.Event(), threading.Event()

    def occupied():
        held.set()
        assert release.wait(5)

    work = application.pool.submit(occupied)
    try:
        assert held.wait(5)
        application.toggle_vpn()
        assert application.connection_action == 'STOPPING'
        if close_request:
            application.on_close()
            assert application.confirmation is not None
        application.close(True)
        assert application.closed
    finally:
        release.set()
        work.result(timeout=5)
    application.pool.shutdown(wait=True)
    while not completions.empty():
        application.complete(*completions.get_nowait())
    assert normal_owner.active and normal_owner.downs == []


@pytest.fixture
def normal_connect_app(normal_owner, monkeypatch, tmp_path):
    monkeypatch.setattr(Path, 'home', lambda: tmp_path)
    module.Adw.init()
    application = module.App(smoke=True)
    transport = 'awg' if normal_owner.ident.startswith('fcawg') else 'tcp'
    normal_owner.active = False
    control = SimpleNamespace(application=application, transport=transport, calls=[], helpers=[],
                              futures=[], completions=Queue(), entered=threading.Event(),
                              release=threading.Event(), block=False)

    class SyntheticFriends:
        def __init__(self, *_):
            pass

        def connect(self, country, driver, *, transport):
            control.calls.append((country, transport))
            with backend.connection_operation(owner='c'*64) as lease:
                lease.reserve()
                driver.connect(normal_owner.ident)
                lease.finish()

    def helper(action, profile=None, data=None):
        assert action in ('up', 'down') and profile == normal_owner.ident and data is None
        control.helpers.append(action)
        control.entered.set()
        if control.block:
            assert control.release.wait(10), 'Mutation barrier was not released'
        normal_owner.active = action == 'up'

    monkeypatch.setattr(normal_owner.driver, '_'+transport, helper)
    application.friends_owner_class = SyntheticFriends
    application.friends_registered = True
    application.driver = normal_owner.driver
    application.items = normal_owner.driver.profiles()
    application.selected_id = normal_owner.ident
    application.active = False
    application.ru = False
    application.route_options = {'transport': transport}
    application.configure_transports()
    application.render()
    assert application.transport_id() == transport
    original_submit = application.pool.submit

    def submit(*arguments, **keywords):
        future = original_submit(*arguments, **keywords)
        control.futures.append(future)
        return future

    original_idle = module.GLib.idle_add

    def idle(callback, *arguments):
        if callback == application.complete:
            control.completions.put(arguments)
            return 0
        return original_idle(callback, *arguments)

    monkeypatch.setattr(application.pool, 'submit', submit)
    monkeypatch.setattr(module.GLib, 'idle_add', idle)
    with backend.connection_operation() as lease:
        assert lease.record == dict(generation=0, pending=None)
    yield control
    control.release.set()
    for future in control.futures:
        future.cancel()
    application.pool.shutdown(wait=True)
    application.poll_pool.shutdown(wait=True)
    application.busy = False
    application.close(True)


@pytest.fixture
def occupied_worker(normal_connect_app):
    application = normal_connect_app.application
    entered, release = threading.Event(), threading.Event()

    def occupy():
        entered.set()
        assert release.wait(10), 'Queue barrier was not released'

    blocker = application.pool.submit(occupy)
    assert entered.wait(5)
    yield release, blocker
    for future in normal_connect_app.futures:
        future.cancel()
    release.set()
    blocker.result(timeout=5)


def journal():
    return json.loads((backend.operation_directory() / 'state.json').read_text())


def gui_snapshot(application):
    return (application.closed, application.busy, application.connection_action,
            application.active, application.revision, application.initializing,
            application.render_count, application.widget_changes, application.detail_text)


def test_queued_normal_friends_connect_one_close(normal_connect_app, occupied_worker):
    control = normal_connect_app
    application = control.application
    release, blocker = occupied_worker
    baseline = journal()
    application.toggle_vpn()
    future = control.futures[-1]
    assert application.connection_action == 'CONNECTING' and application.busy
    assert not future.running() and not future.done()
    assert control.calls == control.helpers == [] and journal() == baseline
    revision = application.revision
    application.on_close()
    observed = (future.cancelled(), application.closed, application.busy, application.connection_action)
    assert observed == (True, True, False, None), observed
    assert application.connection_future is None and application.revision > revision
    assert not application.initializing
    closed = gui_snapshot(application)
    release.set()
    blocker.result(timeout=5)
    application.pool.shutdown(wait=True)
    application.complete(*control.completions.get(timeout=5))
    assert gui_snapshot(application) == closed
    assert control.calls == control.helpers == [] and journal() == baseline


def test_two_closes_do_not_add_mutation(normal_connect_app, occupied_worker):
    control = normal_connect_app
    application = control.application
    application.toggle_vpn()
    application.on_close()
    closed = gui_snapshot(application)
    application.on_close()
    application.toggle_vpn()
    assert application.closed and gui_snapshot(application) == closed
    assert len(control.futures) == 2 and control.calls == control.helpers == []
    assert journal() == dict(generation=0, pending=None)


@pytest.mark.parametrize('active', [False, True])
def test_running_normal_mutation_blocks_close_until_completion(normal_connect_app, normal_owner, active):
    control = normal_connect_app
    application = control.application
    application.active = normal_owner.active = active
    control.block = True
    application.toggle_vpn()
    assert control.entered.wait(5)
    future = control.futures[-1]
    assert future.running() and not future.cancel()
    running = journal()
    assert running == dict(generation=1, pending=None if active else 'c'*64)
    application.on_close()
    application.on_close()
    application.toggle_vpn()
    assert not application.closed and application.busy and application.confirmation is None
    assert application.connection_action == ('STOPPING' if active else 'CONNECTING')
    assert len(control.futures) == 1 and control.helpers == ['down' if active else 'up']
    assert journal() == running
    control.release.set()
    completion = control.completions.get(timeout=5)
    assert future.done() and not future.cancelled()
    application.on_close()
    assert not application.closed and application.busy and application.confirmation is None
    application.complete(*completion)
    assert not application.busy and application.connection_action is None
    assert application.connection_future is None and application.active is not active
    assert journal() == dict(generation=1 if active else 2, pending=None)
    application.on_close()
    if not active:
        assert not application.closed and application.confirmation is not None
        application.close(True)
        assert normal_owner.active
    assert application.closed and control.helpers == ['down' if active else 'up']


@pytest.mark.parametrize('kind', ['initialized', 'profiles', 'ip', 'updates', 'tcp_installed',
                                 'system_installed', 'update_installed', 'recovered',
                                 'mesh-started', 'auto-started'])
def test_non_connection_submit_is_not_cancelled(normal_connect_app, occupied_worker, kind):
    control = normal_connect_app
    application = control.application
    application.submit(application.initialize if kind == 'initialized' else lambda: None, kind)
    future = control.futures[-1]
    application.on_close()
    assert not future.done() and not future.running()
    assert application.busy and not application.closed
    assert application.connection_future is None
    assert control.calls == control.helpers == [] and journal() == dict(generation=0, pending=None)


def test_old_connect_completion_cannot_replace_new_disconnect(normal_connect_app, normal_owner):
    control = normal_connect_app
    application = control.application
    application.toggle_vpn()
    connected = control.completions.get(timeout=5)
    application.complete(*connected)
    assert application.active and normal_owner.active
    control.entered.clear()
    control.block = True
    application.toggle_vpn()
    assert control.entered.wait(5)
    stopping = gui_snapshot(application)
    application.complete(*connected)
    assert gui_snapshot(application) == stopping
    control.release.set()
    application.complete(*control.completions.get(timeout=5))
    disconnected = gui_snapshot(application)
    application.complete(*connected)
    assert gui_snapshot(application) == disconnected
    assert not application.active and not normal_owner.active
    assert control.calls == [('nl', control.transport)] and control.helpers == ['up', 'down']
    assert journal() == dict(generation=3, pending=None)


def test_cancelled_callback_is_fenced_while_gui_open(normal_connect_app, occupied_worker):
    control = normal_connect_app
    application = control.application
    application.toggle_vpn()
    assert application.cancel_queued_connection()
    assert not application.closed and not application.busy and application.connection_action is None
    cancelled = control.completions.get(timeout=5)
    application.toggle_vpn()
    connecting = gui_snapshot(application)
    current = application.connection_future
    application.complete(*cancelled)
    assert gui_snapshot(application) == connecting and application.connection_future is current
    application.on_close()
    assert application.closed and control.calls == control.helpers == []
    assert journal() == dict(generation=0, pending=None)


def test_queued_manual_connect_uses_same_ownership(normal_connect_app, occupied_worker):
    control = normal_connect_app
    application = control.application
    application.friends_registered = False
    application.toggle_vpn()
    future = control.futures[-1]
    assert application.connection_future is future and application.connection_action == 'CONNECTING'
    application.on_close()
    assert future.cancelled() and application.closed and control.helpers == []
    assert journal() == dict(generation=0, pending=None)
