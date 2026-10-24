import subprocess

import pytest

from messenger.local import LocalError
from provisioning import chat_client


@pytest.fixture
def bundle(tmp_path, monkeypatch):
    root = tmp_path / 'bundle'
    (root / 'provisioning').mkdir(parents=True)
    monkeypatch.setattr(chat_client, '__file__', str(root / 'provisioning/chat_client.py'))
    monkeypatch.delenv('APPIMAGE', raising=False)
    monkeypatch.delenv('APPDIR', raising=False)
    return root


def test_source_and_full_bundle_entry_are_fixed(bundle):
    assert chat_client.entry_command() == [chat_client.sys.executable, str(bundle / 'clients/desktop/chat_daemon.py')]
    (bundle / 'launcher.py').touch()
    assert chat_client.entry_command() == [chat_client.sys.executable, str(bundle / 'launcher.py')]


def test_appimage_service_reopens_original_image_not_transient_mount(bundle, monkeypatch, tmp_path):
    image = tmp_path / 'Family Connect.AppImage'
    image.touch()
    monkeypatch.setenv('APPIMAGE', str(image))
    monkeypatch.setenv('APPDIR', str(bundle))
    assert chat_client.entry_command() == [str(image)]
    monkeypatch.setenv('APPDIR', str(tmp_path / 'other-image'))
    assert chat_client.entry_command()[-1] == str(bundle / 'clients/desktop/chat_daemon.py')
    monkeypatch.setenv('APPDIR', str(bundle))
    image.unlink()
    assert chat_client.entry_command()[-1] == str(bundle / 'clients/desktop/chat_daemon.py')


def test_session_environment_forwards_paths_not_credentials(monkeypatch):
    monkeypatch.setenv('XDG_CONFIG_HOME', '/synthetic/config with spaces')
    monkeypatch.setenv('XDG_DATA_HOME', '/synthetic/data')
    monkeypatch.setenv('FC_PRIVATE_TOKEN', 'must-not-be-forwarded')
    monkeypatch.setenv('PYTHONPATH', '/untrusted/library')
    values = chat_client.session_environment()
    assert '--setenv=XDG_CONFIG_HOME=/synthetic/config with spaces' in values
    assert '--setenv=XDG_DATA_HOME=/synthetic/data' in values
    assert all('FC_PRIVATE_TOKEN' not in value and 'PYTHONPATH' not in value for value in values)


def test_start_is_user_session_fixed_dbus_unit_without_shell(bundle, monkeypatch):
    calls = []
    monkeypatch.setattr(subprocess, 'run', lambda command, **kwargs: calls.append((command, kwargs)))
    chat_client.start_service()
    command, options = calls[0]
    assert command[:5] == ['systemd-run', '--user', '--collect', '--quiet', '--unit=family-connect-chat']
    assert '--property=Type=dbus' in command
    assert '--property=BusName=com.familyconnect.Chat1' in command
    assert '--property=Restart=on-failure' in command
    assert '--property=StartLimitBurst=3' in command
    assert '--property=KillMode=control-group' in command
    assert '--property=UMask=0077' in command
    assert command[-3:] == [chat_client.sys.executable, str(bundle / 'clients/desktop/chat_daemon.py'), '--chat-service']
    assert options['timeout'] == 8 and not options.get('shell')


def test_start_failure_is_stable_and_never_uses_local_owner(monkeypatch):
    def unavailable(*args, **kwargs):
        raise OSError('private process failure')
    monkeypatch.setattr(subprocess, 'run', unavailable)
    with pytest.raises(LocalError, match='^service_unavailable$'):
        chat_client.start_service()


def test_client_close_does_not_restart_service_and_releases_connection(monkeypatch):
    client = chat_client.ChatClient(starter=lambda: pytest.fail('close restarted daemon'))
    calls = []
    class Connection:
        def close_sync(self, cancellable):
            calls.append('closed')
    client.connection = Connection()
    def request(operation, arguments, **kwargs):
        calls.append((operation, arguments, kwargs))
        raise LocalError('service_unavailable')
    monkeypatch.setattr(client, 'request', request)
    client.close()
    assert calls == [('detach', {}, {'start': False}), 'closed']
    assert client.closed
