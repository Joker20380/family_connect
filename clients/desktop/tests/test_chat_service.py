import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import uuid
import time

import pytest

pytest.importorskip('gi')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import chat_daemon
from messenger.local import LocalError


def bare_service():
    service = object.__new__(chat_daemon.ChatService)
    service.stopping = False
    service.support = None
    service.support_pending = False
    service.pending = 0
    service.clients = {}
    service.state = {'attached': False}
    service.owner = SimpleNamespace(local=None)
    service.idle_since = 0
    service.next_resume = 1000
    service.notifier = SimpleNamespace(withdraw=lambda _: None)
    return service


def request(service, operation, arguments, sender=':1.20', uid=None):
    value = dict(id=uuid.uuid4().hex, created=int(time.time()), operation=operation, arguments=arguments)
    replies = []
    connection = SimpleNamespace(call_sync=lambda *args: SimpleNamespace(unpack=lambda: (os.getuid() if uid is None else uid,)))
    parameters = SimpleNamespace(unpack=lambda: (json.dumps(value),))
    invocation = SimpleNamespace(return_value=lambda response: replies.append(json.loads(response.unpack()[0])))
    service.request(connection, sender, '/', 'ignored', 'Request', parameters, invocation)
    return replies[0]


def test_session_credentials_and_queue_bounds_checked_before_owner_access():
    service = bare_service()
    assert request(service, 'status', {}, uid=os.getuid() + 1)['error'] == 'invalid_input'
    service.pending = 8
    assert request(service, 'status', {})['error'] == 'busy'
    service.pending = 0
    assert request(service, 'execute', {'command': 'not-allowed'})['error'] == 'invalid_input'


def test_clients_have_independent_leases_and_departure_cannot_detach_replacement():
    service = bare_service()
    for index in range(4):
        assert request(service, 'heartbeat', dict(visible=True, peer='service'), sender=':1.' + str(index))['ok']
    assert request(service, 'heartbeat', dict(visible=False, peer=None), sender=':1.extra')['error'] == 'busy'
    assert request(service, 'heartbeat', dict(visible='yes', peer=None))['error'] == 'invalid_input'
    assert request(service, 'heartbeat', dict(visible=True, peer='https://untrusted/'))['error'] == 'invalid_input'
    assert request(service, 'detach', {}, sender=':1.0')['ok']
    assert ':1.0' not in service.clients and len(service.clients) == 3
    parameters = SimpleNamespace(unpack=lambda: (':1.1', ':1.1', ''))
    service.name_changed(None, None, None, None, None, parameters)
    assert set(service.clients) == {':1.2', ':1.3'}


def test_absent_or_locked_store_does_not_leave_idle_daemon_forever(monkeypatch):
    service = bare_service()
    service.loop = SimpleNamespace(quit=lambda: None)
    monkeypatch.setattr(chat_daemon.time, 'monotonic', lambda: 61)
    assert service.poll() is False and service.stopping
    service = bare_service()
    service.clients = {':1.2': (70, False, None)}
    assert service.poll() is True and service.idle_since == 61


def test_language_read_is_bounded_and_rejects_nonregular_files(tmp_path, monkeypatch):
    monkeypatch.setenv('XDG_CONFIG_HOME', str(tmp_path))
    monkeypatch.setenv('LANG', 'en_US.UTF-8')
    directory = tmp_path / 'family-connect'
    directory.mkdir()
    language = directory / 'ui-language'
    language.write_text('ru\n')
    assert chat_daemon.ChatService.russian() is True
    language.unlink()
    os.mkfifo(language)
    assert chat_daemon.ChatService.russian() is False
    language.unlink()
    language.symlink_to('/dev/zero')
    assert chat_daemon.ChatService.russian() is False


def test_notification_activation_launches_separate_fixed_gui_unit(monkeypatch):
    calls = []
    monkeypatch.setattr(chat_daemon, 'entry_command', lambda: ['/usr/bin/python3', '/bundle/clients/desktop/chat_daemon.py'])
    monkeypatch.setattr(chat_daemon, 'session_environment', lambda: ['--setenv=DISPLAY=:99'])
    monkeypatch.setattr(chat_daemon.subprocess, 'Popen', lambda command, **kwargs: calls.append((command, kwargs)))
    for invalid in (None, '../app', 'familyconnect://invite/' + '0' * 64):
        with pytest.raises(LocalError, match='invalid_input'):
            chat_daemon.open_window(invalid)
    assert not calls
    chat_daemon.open_window('service')
    command, options = calls[0]
    assert command[:4] == ['systemd-run', '--user', '--collect', '--quiet']
    assert command[4].startswith('--unit=family-connect-window-')
    assert command[-1] == 'familyconnect://chat/service'
    assert command[-2] == str(Path(chat_daemon.__file__).with_name('app.py'))
    assert options['start_new_session'] and not options.get('shell')


def test_fit_waits_for_frame_and_preserves_outer_window_geometry():
    from app import App
    calls = []
    callbacks = []
    class Clock:
        def connect(self, signal, callback):
            assert signal == 'after-paint'
            callbacks.append(callback)
            return 21

        def request_phase(self, phase):
            calls.append(('phase', phase))

        def disconnect(self, ident):
            calls.append(('disconnect', ident))
    clock = Clock()
    def measure(orientation, width):
        assert width == 360
        return (247, 756, -1, -1)
    window = SimpleNamespace(get_frame_clock=lambda: clock, get_default_size=lambda: (360, 286),
        measure=measure, set_default_size=lambda width, height: calls.append(('size', width, height)))
    app = SimpleNamespace(window=window, closed=False, fit_source=0, fit_clock=None, fitted_height=None, page='status')
    app.fit_height = lambda: App.fit_height(app)
    App.request_fit(app)
    App.request_fit(app)
    assert len(callbacks) == 1 and not any(call[0] == 'size' for call in calls)
    callbacks[0](clock)
    assert calls[-2:] == [('disconnect', 21), ('size', 360, 756)]
    assert app.fit_clock is None and app.fit_source == 0 and app.fitted_height == 756
    calls.clear()
    app.page = 'messenger'
    App.fit_height(app)
    app.page = 'route'
    App.fit_height(app)
    assert not calls
