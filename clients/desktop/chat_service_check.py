"""Private D-Bus + real Secret Service + user-systemd restart + loopback RNS."""
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import tempfile
import time
import uuid

from gi.repository import Gio, GLib
from app import App, Adw, Gtk
from chat_notifications_check import Daemon, wait
from chat_ui_check import settled
from mesh_ui_check import capture, pump, Driver, done
from device_identity.friends import load_friends_identity
from messenger.local import LocalChat, LocalError
from messenger.tests.test_offline import Peer
from provisioning.chat_client import ChatClient
from provisioning.chat_rpc import BUS_NAME, OBJECT_PATH
from provisioning.chat_transport import initialize, SystemMailbox


def main(root):
    root.mkdir(mode=0o700, parents=True, exist_ok=False)
    errors = []
    def failed(kind, value, traceback):
        errors.append(kind.__name__)
        sys.__excepthook__(kind, value, traceback)
    sys.excepthook = failed
    parent_unit = os.environ['FC_TEST_PARENT_UNIT']
    assert parent_unit.startswith('fc-parity-chat-service-') and parent_unit.endswith('.service')
    unit = 'fc-chat-fixture-' + str(os.getpid())
    unit_started = False
    for name in ('home', 'config', 'data', 'run'):
        (root / name).mkdir(mode=0o700)
    os.environ.update(HOME=str(root / 'home'), XDG_CONFIG_HOME=str(root / 'config'), XDG_DATA_HOME=str(root / 'data'))
    vault_log = (root / 'keyring.log').open('w')
    vault_runtime = tempfile.TemporaryDirectory(prefix='fc-chat-service-keyring-')
    keyring = subprocess.Popen(['gnome-keyring-daemon', '--foreground', '--unlock', '--components=secrets',
        '--control-directory=' + vault_runtime.name], stdin=subprocess.PIPE, stdout=vault_log, stderr=vault_log)
    keyring.stdin.write(b'synthetic-isolated-vault-password\n')
    keyring.stdin.close()
    def interrupted(*_):
        raise SystemExit('fixture interrupted')
    signal.signal(signal.SIGTERM, interrupted)
    daemon = Daemon()
    app = node = sender = bob = None
    def ctl(*arguments):
        return subprocess.run(['systemctl', '--user', *arguments], capture_output=True, text=True, timeout=15)
    connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    def owner_pid(name=BUS_NAME):
        try:
            return connection.call_sync('org.freedesktop.DBus', '/org/freedesktop/DBus', 'org.freedesktop.DBus',
                'GetConnectionUnixProcessID', GLib.Variant('(s)', (name,)), GLib.VariantType.new('(u)'),
                Gio.DBusCallFlags.NONE, 1000, None).unpack()[0]
        except GLib.Error:
            return None
    def client():
        return ChatClient(starter=lambda: None)
    try:
        wait(lambda: owner_pid('org.freedesktop.secrets') == keyring.pid)
        device = load_friends_identity(root / 'device', create=True)
        runtime = initialize(root / 'bob-runtime')
        bob = LocalChat(root / 'bob', os.urandom(32), create=True, platform='android', version=118)
        environment = ['--setenv=' + name + '=' + os.environ[name] for name in
            ('DBUS_SESSION_BUS_ADDRESS', 'HOME', 'XDG_CONFIG_HOME', 'XDG_DATA_HOME', 'PYTHONPATH', 'DISPLAY', 'XDG_RUNTIME_DIR') if name in os.environ]
        command = ['systemd-run', '--user', '--collect', '--quiet', '--unit=' + unit,
            '--property=Type=exec', '--property=Restart=on-failure',
            '--property=RestartSec=1s', '--property=StartLimitIntervalSec=300s', '--property=StartLimitBurst=3',
            '--property=RuntimeMaxSec=150s', '--property=TimeoutStopSec=15s', '--property=KillMode=control-group',
            '--property=CPUQuota=25%', '--property=BindsTo=' + parent_unit, '--property=After=' + parent_unit] + environment
        command += [sys.executable, str(Path(__file__).parent / 'tests/chat_service_peer.py'), str(root)]
        unit_started = True
        subprocess.run(command, check=True, capture_output=True, timeout=15)
        wait(lambda: owner_pid() is not None)
        first_pid = owner_pid()
        controller = client()
        profile = controller.open(create=True)
        controller.invoke('trust_contact', public=bob.profile()['public'], fingerprint=bob.profile()['fingerprint'])
        bob.trust_contact(profile['public'], profile['fingerprint'])
        controller.invoke('inbox_summary')
        allowed = root / 'allowed.json'
        allowed.write_text(json.dumps([profile['public'], bob.profile()['public']]))
        with socket.socket() as probe:
            probe.bind(('127.0.0.1', 0))
            port = probe.getsockname()[1]
        node = Peer('budget-node', root / 'node', port, script='closed_peer.py', extra=[str(allowed)])
        lease = dict(host='127.0.0.1', port=port, public_key=node.info['public'], expires_at=int(time.time()) + 120)
        (root / 'node.json').write_text(json.dumps(lease))
        sender = SystemMailbox(bob._chat, lease, runtime)
        controller.close()
        Adw.init()
        Gtk.Settings.get_default().set_property('gtk-enable-animations', False)
        def window():
            result = App(smoke=True)
            driver = Driver()
            result.complete('initialized', done((driver, driver.profiles(), False)), result.revision, None)
            result.chat_pane.owner_factory = client
            result.chat_smoke = False
            result.ru = True
            result.present()
            result.select_page('messenger')
            settled(result.chat_pane)
            assert result.chat_pane.opened
            return result
        app = window()
        pane = app.chat_pane
        assert pane.owner.owns_notifications and pane.notifications.closed
        pane.notification_settings()
        settled(pane)
        capture(app, root / 'ru-independent-background-settings.png')
        app.close(True)
        wait(lambda: app.closed)
        assert owner_pid() == first_pid
        message = bob.queue(profile['address'], 'Synthetic delivery after GUI close')
        assert sender.exchange(timeout=20).relayed == 1
        monitor = client()
        deadline = time.monotonic() + 25
        while time.monotonic() < deadline:
            pump(.15)
            inbox = monitor.invoke('inbox_summary')
            if inbox and inbox[0]['notified']:
                break
        assert inbox[0]['id'] == message and inbox[0]['notified'] and not inbox[0]['read']
        assert daemon.posts and 'Synthetic delivery' not in str(daemon.posts)
        daemon.action(daemon.posts[-1][0])
        wait(lambda: (root / 'opened-peer').exists())
        assert (root / 'opened-peer').read_text() == bob.profile()['address']
        os.kill(first_pid, signal.SIGKILL)
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline and owner_pid() in (None, first_pid):
            pump(.1)
        second_pid = owner_pid()
        assert second_pid not in (None, first_pid)
        assert monitor.open() == profile
        assert monitor.invoke('inbox_summary')[0]['notified']
        assert monitor.invoke('history', address=bob.profile()['address'], offset=0, limit=50)['messages'][0]['text'] == 'Synthetic delivery after GUI close'
        request = dict(id=uuid.uuid4().hex, created=int(time.time()), operation='queue',
            arguments=dict(address=bob.profile()['address'], text='synthetic-crash-after-commit'))
        raw = json.dumps(request)
        def call():
            return json.loads(connection.call_sync(BUS_NAME, OBJECT_PATH, BUS_NAME, 'Request', GLib.Variant('(s)', (raw,)),
                GLib.VariantType.new('(s)'), Gio.DBusCallFlags.NO_AUTO_START, 5000, None).unpack()[0])
        try:
            call()
            raise AssertionError('fixture crash did not interrupt the reply')
        except GLib.Error:
            pass
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline and owner_pid() in (None, second_pid):
            pump(.1)
        third_pid = owner_pid()
        assert third_pid not in (None, second_pid)
        assert monitor.open() == profile
        assert call()['error'] == 'operation_outcome_unknown'
        history = monitor.invoke('history', address=bob.profile()['address'], offset=0, limit=50)['messages']
        assert sum(item['text'] == 'synthetic-crash-after-commit' for item in history) == 1
        app = window()
        app.open_chat(bob.profile()['address'])
        wait(lambda: app.chat_pane.screen == 'conversation' and not app.chat_pane.busy)
        capture(app, root / 'ru-reopened-preserved-chat.png')
        monitor.invoke('background_delivery', enabled=False)
        app.close(True)
        wait(lambda: app.closed)
        monitor.close()
        deadline = time.monotonic() + 40
        while owner_pid() is not None and time.monotonic() < deadline:
            pump(.1)
        assert owner_pid() is None, 'disabled background delivery did not release the service'
        assert ctl('show', unit, '-p', 'MainPID', '--value').stdout.strip() == '0'
        assert load_friends_identity(root / 'device', create=False).public_identity == device.public_identity
        assert not errors, errors
        (root / 'result.json').write_text(json.dumps(dict(result='PASS', actual_session_dbus=True,
            actual_secret_service=True, actual_user_systemd=True, gui_detach_survives=True,
            hidden_mailbox_notification=True, sigkill_recovered_same_identity=True,
            crash_after_commit_replay_blocked=True, resumed_history=True, user_state_touched=False,
            disabled_background_stops_service=True,
            activation_scope='isolated peer callback + real reopened GTK; packaged fresh-window launch NOT_RUN',
            external_network=False, installed_upgrade='NOT_RUN',
            supervisor='real user systemd; Type=exec on isolated session bus; production Type=dbus NOT_RUN'), indent=2) + '\n')
    finally:
        if app is not None and not app.closed:
            app.close(True)
            wait(lambda: app.closed)
        if unit_started:
            ctl('stop', unit)
        if sender:
            sender.close()
        if bob:
            bob.close()
        if node:
            node.close()
        daemon.close()
        keyring.terminate()
        try:
            keyring.wait(timeout=5)
        except subprocess.TimeoutExpired:
            keyring.kill()
            keyring.wait(timeout=5)
        vault_log.close()
        vault_runtime.cleanup()
        state = ctl('show', unit, '-p', 'ActiveState', '-p', 'MainPID')
        (root / 'unit-after-stop.txt').write_text(state.stdout)


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
