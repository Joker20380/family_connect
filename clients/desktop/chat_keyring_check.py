"""Check libsecret against an isolated D-Bus/keyring process with synthetic data."""
import base64
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

from provisioning.chat_keyring import ChatKeyring, KeyringUnavailable
from gi.repository import Gio, GLib
import gi
gi.require_version('Secret', '1')
from gi.repository import Secret


def main(root):
    assert os.environ['HOME'] == str(root)
    assert os.environ['XDG_DATA_HOME'] == str(root / 'data')
    assert os.environ['XDG_RUNTIME_DIR'] == str(root / 'run')
    assert os.environ.get('DBUS_SESSION_BUS_ADDRESS')
    diagnostics = (root / 'daemon.log').open('w')
    runtime = tempfile.TemporaryDirectory(prefix='fc-chat-keyring-')
    starts = 0
    def start():
        nonlocal starts
        starts += 1
        child = subprocess.Popen(['gnome-keyring-daemon', '--foreground', '--unlock', '--components=secrets',
                                  '--control-directory=' + str(Path(runtime.name) / ('keyring-' + str(starts)))],
                                 stdin=subprocess.PIPE, stdout=diagnostics, stderr=diagnostics)
        child.stdin.write(b'synthetic-disposable-vault-password\n')
        child.stdin.close()
        return child
    process = start()
    worker = ThreadPoolExecutor(max_workers=1)
    def service_pid():
        connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        return connection.call_sync('org.freedesktop.DBus', '/org/freedesktop/DBus',
                                    'org.freedesktop.DBus', 'GetConnectionUnixProcessID',
                                    GLib.Variant('(s)', ('org.freedesktop.secrets',)),
                                    GLib.VariantType.new('(u)'), Gio.DBusCallFlags.NONE, 1000, None).unpack()[0]
    def request(vault, create):
        future = worker.submit(vault.key, 'synthetic-desktop-fixture', create=create)
        context = GLib.MainContext.default()
        deadline = time.monotonic() + 17
        while not future.done() and time.monotonic() < deadline:
            while context.pending():
                context.iteration(False)
            time.sleep(.01)
        return future.result(timeout=1)
    try:
        vault = ChatKeyring()
        deadline = time.monotonic() + 10
        while True:
            try:
                key = request(vault, True)
                break
            except KeyringUnavailable:
                if time.monotonic() >= deadline:
                    raise
                time.sleep(.1)
        assert len(key) == 32
        assert service_pid() == process.pid
        original_pid = process.pid
        assert vault.key('synthetic-desktop-fixture', create=False) == key
        assert ChatKeyring().key('synthetic-desktop-fixture', create=False) == key
        process.terminate()
        process.wait(timeout=5)
        process = start()
        deadline = time.monotonic() + 10
        while True:
            try:
                if service_pid() == process.pid:
                    break
            except GLib.Error:
                pass
            if time.monotonic() >= deadline:
                raise AssertionError('restarted service did not acquire its bus name')
            context = GLib.MainContext.default()
            while context.pending():
                context.iteration(False)
            time.sleep(.05)
        diagnosed = False
        while True:
            try:
                assert request(ChatKeyring(), False) == key
                assert service_pid() == process.pid and process.pid != original_pid
                break
            except KeyringUnavailable:
                if not diagnosed:
                    service = Secret.Service.open_sync(Secret.Service.__gtype__, 'org.freedesktop.secrets',
                        Secret.ServiceFlags.OPEN_SESSION | Secret.ServiceFlags.LOAD_COLLECTIONS, None)
                    schema = Secret.Schema.new('com.familyconnect.ChatKey.v1', Secret.SchemaFlags.NONE,
                        {'device': Secret.SchemaAttributeType.STRING})
                    value = service.lookup_sync(schema, {'device': 'synthetic-desktop-fixture'}, None)
                    print(json.dumps({'new_service_matches': value is not None and value.get_text() == base64.b64encode(key).decode(),
                        'locked_collections': [collection.get_locked() for collection in service.get_collections()],
                        'owner_is_restarted_process': service_pid() == process.pid}), flush=True)
                    diagnosed = True
                if time.monotonic() >= deadline:
                    raise
                time.sleep(.1)
        try:
            vault.key('missing-fixture', create=False)
            raise AssertionError('missing key was created')
        except KeyringUnavailable:
            pass
        for path in (root / 'data').rglob('*'):
            if path.is_file():
                assert key not in path.read_bytes()
                assert base64.b64encode(key) not in path.read_bytes()
        (root / 'result.json').write_text(json.dumps(dict(result='PASS', actual_secret_service=True,
            key_bytes=32, same_key_on_resume=True, missing_key_not_created=True,
            user_keyring_touched=False, background_thread=True, service_restart=True), indent=2) + '\n')
    finally:
        worker.shutdown(wait=True, cancel_futures=True)
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        diagnostics.close()
        runtime.cleanup()


if __name__ == '__main__':
    main(Path(sys.argv[1]))
