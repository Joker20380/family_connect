import os
from pathlib import Path
import select
import subprocess
import sys
from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.db import connection, transaction
from django.http import HttpResponse, StreamingHttpResponse
from django.test import Client, RequestFactory
from django.urls import path
import pytest

from control.capture_gate import Busy, CURRENT, GateError, initialize
from fc_control_plane.capture import operation
from fc_control_plane.middleware import CaptureAdmission
from apps.console import backend, support
from apps.console.models import SystemMessage
from apps.console.system_publisher import PublicationUnknown, publish_next
import manage


@pytest.fixture
def gate(tmp_path, monkeypatch):
    gate = initialize(tmp_path / 'capture')
    monkeypatch.setenv('FC_CONTROL_CAPTURE_GATE', str(gate.directory))
    return gate


def pending(gate):
    return {entry.name: entry.read_bytes() for entry in (gate.directory / 'pending').iterdir()}


def test_busy_precedes_any_request_work(gate):
    calls = []
    middleware = CaptureAdmission(lambda request: calls.append(request))
    with gate.drain(.2):
        response = middleware(RequestFactory().get('/'))
    assert response.status_code == 503 and response['Cache-Control'] == 'no-store'
    assert not calls and not pending(gate)


def test_request_success_holds_one_gate_and_settles(gate):
    def respond(request):
        assert CURRENT.get() is not None and len(pending(gate)) == 1
        with operation():
            assert len(pending(gate)) == 1
        return HttpResponse('synthetic')
    assert CaptureAdmission(respond)(RequestFactory().get('/')).status_code == 200
    assert not pending(gate)


@pytest.mark.parametrize('failure', ['response', 'exception', 'io'])
def test_failed_request_retains_uncertainty(gate, failure):
    def respond(request):
        if failure == 'response':
            return HttpResponse(status=500)
        if failure == 'io':
            raise OSError('synthetic private detail')
        raise RuntimeError('synthetic private detail')
    middleware = CaptureAdmission(respond)
    if failure == 'exception':
        with pytest.raises(RuntimeError):
            middleware(RequestFactory().get('/'))
    else:
        response = middleware(RequestFactory().get('/'))
        assert response.status_code in (500, 503) and b'private detail' not in response.content
    assert len(pending(gate)) == 1


def test_streaming_is_refused_without_consuming_body(gate):
    calls = []
    def body():
        calls.append('body')
        yield b'not admitted for streaming'
    response = StreamingHttpResponse(body())
    def close():
        assert CURRENT.get() is not None
        calls.append('closed')
    response._resource_closers.append(close)
    assert CaptureAdmission(lambda request: response)(RequestFactory().get('/')).status_code == 503
    assert calls == ['closed'] and len(pending(gate)) == 1


def test_disabled_middleware_preserves_streaming(monkeypatch):
    monkeypatch.delenv('FC_CONTROL_CAPTURE_GATE', raising=False)
    response = StreamingHttpResponse([b'synthetic'])
    assert CaptureAdmission(lambda request: response)(RequestFactory().get('/')) is response
    response.close()


def test_replaced_gate_is_not_silently_rebound(gate):
    middleware = CaptureAdmission(lambda request: HttpResponse('not called'))
    old = gate.directory / 'operations.lock'
    old.rename(gate.directory / 'previous.lock')
    old.touch(mode=0o600)
    assert CaptureAdmission(lambda request: None).gate is middleware.gate
    assert middleware(RequestFactory().get('/')).status_code == 503


def test_missing_gate_fails_startup_without_initialization(tmp_path, monkeypatch):
    missing = tmp_path / 'missing'
    monkeypatch.setenv('FC_CONTROL_CAPTURE_GATE', str(missing))
    with pytest.raises(GateError, match='CAPTURE_UNAVAILABLE'):
        CaptureAdmission(lambda request: None)
    assert not missing.exists()


@pytest.mark.parametrize('outcome', ['success', 'help', 'failure'])
def test_management_scope_includes_django_dispatch(gate, monkeypatch, outcome):
    def execute(arguments):
        assert CURRENT.get() is not None and len(pending(gate)) == 1
        if outcome == 'help':
            raise SystemExit(0)
        if outcome == 'failure':
            raise SystemExit(1)
    monkeypatch.setattr('django.core.management.execute_from_command_line', execute)
    if outcome == 'failure':
        with pytest.raises(SystemExit):
            manage.main(['manage.py', 'synthetic'])
    else:
        assert manage.main(['manage.py', 'synthetic']) == 0
    assert bool(pending(gate)) == (outcome == 'failure')


def test_management_busy_and_runserver_refuse_before_dispatch(gate, monkeypatch, capsys):
    def execute(arguments):
        pytest.fail('unexpected dispatch')
    monkeypatch.setattr('django.core.management.execute_from_command_line', execute)
    with gate.drain(.2):
        assert manage.main(['manage.py', 'migrate']) == 75
    assert manage.main(['manage.py', 'runserver']) == 1
    assert capsys.readouterr().err.splitlines() == ['CAPTURE_BUSY', 'CAPTURE_UNAVAILABLE']
    assert not pending(gate)


def test_real_management_busy_needs_no_settings_or_database(gate, tmp_path):
    environment = dict(os.environ, CONTROL_PLANE_MODE='not-configured', DJANGO_SECRET_KEY='', POSTGRES_PASSWORD='')
    with gate.drain(.2):
        result = subprocess.run([sys.executable, '-B', str(Path(manage.__file__)), 'migrate', '--noinput'],
                                cwd=tmp_path, env=environment, capture_output=True, timeout=10)
    assert result.returncode == 75 and result.stderr == b'CAPTURE_BUSY\n'
    assert not pending(gate)


def test_real_management_process_death_retains_marker(gate, tmp_path):
    arguments = [sys.executable, '-B', str(Path(manage.__file__)), 'shell', '--no-imports', '-c',
                 'print("OWNER_ADMITTED", flush=True); input()']
    process = subprocess.Popen(arguments, cwd=tmp_path, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True)
    try:
        assert select.select([process.stdout], [], [], 10)[0]
        assert process.stdout.readline().strip() == 'OWNER_ADMITTED'
        with pytest.raises(Busy, match='DRAIN_TIMEOUT'):
            with gate.drain(.1):
                pytest.fail('running management command admitted capture')
        assert process.poll() is None
        process.kill()
        process.communicate(timeout=5)
        assert len(pending(gate)) == 1
        with pytest.raises(GateError, match='UNSETTLED_OPERATION'):
            with gate.drain(.2):
                pytest.fail('dead management command admitted capture')
    finally:
        if process.poll() is None:
            process.kill()
        process.communicate(timeout=5)


def session_view(request):
    assert CURRENT.get() is not None
    with transaction.atomic():
        get_user_model().objects.create(username='capture-synthetic')
        transaction.on_commit(lambda: request.session.__setitem__('committed', CURRENT.get() is not None))
    return HttpResponse('synthetic')


def failing_view(request):
    get_user_model().objects.create(username='capture-before-failure')
    raise RuntimeError('synthetic view failure')


urlpatterns = [path('write/', session_view), path('failure/', failing_view)]


@pytest.mark.django_db(transaction=True)
def test_real_request_commit_and_response_session_write_share_gate(gate, settings):
    settings.ROOT_URLCONF = __name__
    settings.ALLOWED_HOSTS = ['testserver']
    settings.MIDDLEWARE = ['fc_control_plane.middleware.CaptureAdmission',
                           'django.contrib.sessions.middleware.SessionMiddleware']
    writes = []
    def check(execute, sql, parameters, many, context):
        if sql.startswith(('INSERT', 'UPDATE')):
            assert CURRENT.get() is not None and len(pending(gate)) == 1
            writes.append(sql.split()[0])
        return execute(sql, parameters, many, context)
    with connection.execute_wrapper(check):
        assert Client().get('/write/').status_code == 200
    assert writes and get_user_model().objects.filter(username='capture-synthetic').exists()
    assert Session.objects.get().get_decoded()['committed'] is True and not pending(gate)
    with gate.drain(.2):
        assert Client().get('/write/').status_code == 503
    assert get_user_model().objects.filter(username='capture-synthetic').count() == 1


@pytest.mark.django_db(transaction=True)
def test_django_converted_exception_keeps_pending_marker(gate, settings):
    settings.ROOT_URLCONF = __name__
    settings.ALLOWED_HOSTS = ['testserver']
    settings.MIDDLEWARE = ['fc_control_plane.middleware.CaptureAdmission']
    response = Client(raise_request_exception=False).get('/failure/')
    assert response.status_code == 500 and len(pending(gate)) == 1
    assert get_user_model().objects.filter(username='capture-before-failure').exists()


def test_synthetic_writer_busy_precedes_directory_and_caught_failure(gate, tmp_path, monkeypatch):
    root = tmp_path / 'synthetic'
    monkeypatch.setattr(backend, 'ROOT', root)
    with gate.drain(.2):
        with pytest.raises(Busy):
            backend.seed_fixture()
    assert not root.exists() and not pending(gate)
    with operation():
        with pytest.raises(backend.BackendError):
            with backend.registry(write=True):
                pytest.fail('missing synthetic registry accepted')
    assert len(pending(gate)) == 1


def test_caught_support_ipc_failure_preserves_uncertainty(gate, settings, tmp_path):
    settings.SUPPORT_SOCKET = str(tmp_path / 'absent.sock')
    with operation():
        with pytest.raises(support.SupportUnavailable):
            support.invoke('send', text='synthetic not sent')
    assert len(pending(gate)) == 1


@pytest.mark.django_db(transaction=True)
def test_publisher_remote_ack_and_queue_commit_remain_inside_gate(gate):
    actor = get_user_model().objects.create_superuser(username='publisher-synthetic')
    message = SystemMessage.objects.create(created_by=actor, title='Synthetic', body='Not production',
                                          kind='information', platforms=['android'], days=1, status='queued')
    calls = []
    def publish(value):
        calls.append(value['id'])
        assert CURRENT.get() is not None and connection.in_atomic_block and len(pending(gate)) == 1
        raise PublicationUnknown
    sender = SimpleNamespace(publish=publish)
    with gate.drain(.2):
        with pytest.raises(Busy):
            publish_next(sender)
    assert not calls and not pending(gate)
    assert publish_next(sender) == 'unknown'
    retained = pending(gate)
    assert len(retained) == 1
    message.refresh_from_db()
    assert message.status == 'unknown'
    message.status = 'queued'
    message.save(update_fields=['status'])
    def successful(value):
        assert CURRENT.get() is not None and len(pending(gate)) == 2
        transaction.on_commit(lambda: calls.append('committed' if CURRENT.get() is not None else 'outside'))
    sender.publish = successful
    assert publish_next(sender) == 'published' and calls[-1] == 'committed'
    assert pending(gate) == retained
    with pytest.raises(GateError, match='UNSETTLED_OPERATION'):
        with gate.drain(.2):
            pytest.fail('unknown remote publication permitted capture')
