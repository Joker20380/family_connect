"""Unprivileged GTK adapter to the single session chat owner."""
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import uuid

from messenger.local import LocalError
from .chat_rpc import BUS_NAME, OBJECT_PATH, PROTOCOL, MAX_REQUEST, MAX_RESPONSE, ERRORS, object_pairs


def entry_command():
    root = Path(__file__).resolve().parents[1]
    image, appdir = os.environ.get('APPIMAGE'), os.environ.get('APPDIR')
    if image and appdir and root.is_relative_to(Path(appdir).resolve()) and Path(image).is_file():
        return [str(Path(image).resolve())] + (['--appimage-extract-and-run'] if os.environ.get('APPIMAGE_EXTRACT_AND_RUN') == '1' else [])
    if (root / 'launcher.py').is_file():
        return [sys.executable, str(root / 'launcher.py')]
    return [sys.executable, str(root / 'clients/desktop/chat_daemon.py')]


def session_environment():
    names = ('DISPLAY', 'WAYLAND_DISPLAY', 'XAUTHORITY', 'DBUS_SESSION_BUS_ADDRESS', 'XDG_RUNTIME_DIR',
             'XDG_SESSION_TYPE', 'XDG_CURRENT_DESKTOP', 'XDG_CONFIG_HOME', 'XDG_DATA_HOME', 'XDG_STATE_HOME', 'XDG_CACHE_HOME', 'LANG', 'LC_ALL', 'HOME')
    return ['--setenv=' + name + '=' + os.environ[name] for name in names if name in os.environ]


def start_service():
    root = Path(__file__).resolve().parents[1]
    if root == Path('/usr/lib/family-connect') and (root / 'candidate.json').is_file():
        try:
            names = [entry.split('=', 2)[1] for entry in session_environment()]
            subprocess.run(['systemctl', '--user', 'import-environment', *names], check=True,
                           stdin=subprocess.DEVNULL, capture_output=True, timeout=8)
            subprocess.run(['systemctl', '--user', 'start', 'family-connect-chat.service'], check=True,
                           stdin=subprocess.DEVNULL, capture_output=True, timeout=8)
            return
        except (OSError, subprocess.SubprocessError):
            raise LocalError('service_unavailable') from None
    command = ['systemd-run', '--user', '--collect', '--quiet', '--unit=family-connect-chat',
        '--property=Type=dbus', '--property=BusName=' + BUS_NAME,
        '--property=Restart=on-failure', '--property=RestartSec=5s',
        '--property=StartLimitIntervalSec=120s', '--property=StartLimitBurst=3',
        '--property=TimeoutStopSec=40s', '--property=KillMode=control-group', '--property=UMask=0077',
        '--property=StandardOutput=null', '--property=StandardError=null', '--property=Nice=5']
    try:
        subprocess.run(command + session_environment() + entry_command() + ['--chat-service'],
                       stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=8)
    except (OSError, subprocess.TimeoutExpired):
        raise LocalError('service_unavailable') from None


class ChatClient:
    owns_notifications = True

    def __init__(self, *, starter=start_service):
        self.starter = starter
        self.connection = None
        self.lock = threading.Lock()
        self.closed = False
        self.peer = None

    def _connect(self, start=True):
        from gi.repository import Gio, GLib
        with self.lock:
            if self.closed:
                raise LocalError('closed')
            if self.connection is None or self.connection.is_closed():
                address = Gio.dbus_address_get_for_bus_sync(Gio.BusType.SESSION, None)
                self.connection = Gio.DBusConnection.new_for_address_sync(address,
                    Gio.DBusConnectionFlags.AUTHENTICATION_CLIENT | Gio.DBusConnectionFlags.MESSAGE_BUS_CONNECTION, None, None)
            def available():
                return self.connection.call_sync('org.freedesktop.DBus', '/org/freedesktop/DBus',
                    'org.freedesktop.DBus', 'NameHasOwner', GLib.Variant('(s)', (BUS_NAME,)),
                    GLib.VariantType.new('(b)'), Gio.DBusCallFlags.NO_AUTO_START, 3000, None).unpack()[0]
            if not available():
                if not start:
                    raise LocalError('service_unavailable')
                self.starter()
                deadline = time.monotonic() + 5
                while not available():
                    if self.closed:
                        raise LocalError('closed')
                    if time.monotonic() >= deadline:
                        raise LocalError('service_unavailable')
                    time.sleep(.05)
            return self.connection

    def request(self, operation, arguments, *, start=True):
        from gi.repository import Gio, GLib
        if self.closed:
            raise LocalError('closed')
        request = dict(id=uuid.uuid4().hex, created=int(time.time()), operation=operation, arguments=arguments)
        raw = json.dumps(request, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
        if len(raw.encode()) > MAX_REQUEST:
            raise LocalError('invalid_input')
        try:
            connection = self._connect(start)
        except (GLib.Error, OSError):
            raise LocalError('service_unavailable') from None
        if self.closed:
            try:connection.close(None, None)
            except Exception:pass
            raise LocalError('closed')
        try:
            response = connection.call_sync(BUS_NAME, OBJECT_PATH, BUS_NAME, 'Request', GLib.Variant('(s)', (raw,)),
                GLib.VariantType.new('(s)'), Gio.DBusCallFlags.NO_AUTO_START, 25000, None).unpack()[0]
        except GLib.Error:
            raise LocalError('operation_outcome_unknown') from None
        try:
            if len(response.encode()) > MAX_RESPONSE:
                raise ValueError()
            value = json.loads(response, object_pairs_hook=object_pairs)
            if (type(value) is not dict or type(value.get('protocol')) is not int or value['protocol'] != PROTOCOL or type(value.get('ok')) is not bool or
                    set(value) != {'protocol', 'ok', 'value' if value['ok'] else 'error'}):
                raise ValueError()
            if not value['ok']:
                raise LocalError(value['error'] if value['error'] in ERRORS else 'service_unavailable')
            return value['value']
        except (ValueError, TypeError, RecursionError, UnicodeError):
            raise LocalError('service_unavailable') from None

    def open(self, *, create=False):
        return self.request('open', {'create': create})

    def invoke(self, operation, **arguments):
        return self.request(operation, arguments)

    def foreground(self, peer):
        self.peer = peer

    def tick(self, *, online, visible, background=False):
        return self.request('heartbeat', {'visible': visible, 'peer': self.peer if visible else None})

    def close(self):
        try:
            if self.connection is not None and not self.closed:
                self.request('detach', {}, start=False)
        except LocalError:
            pass
        finally:
            self.closed = True
            if self.connection is not None:
                try:
                    self.connection.close_sync(None)
                except Exception:
                    pass
