import os
from concurrent.futures import Future, ThreadPoolExecutor
from queue import Queue
import threading

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
