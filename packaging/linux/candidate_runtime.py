"""Inventory-bound internal desktop candidate and explicit system setup."""
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
REQUIRED = {'launcher.py', 'candidate_setup.py', 'candidate_runtime.py', 'embedded/system.tar.gz',
            'clients/desktop/app.py', 'clients/desktop/backend.py', 'clients/desktop/chat_daemon.py',
            'clients/desktop/chat_ui.py', 'clients/desktop/chat_notifications.py', 'clients/desktop/chat_voice.py',
            'clients/desktop/friends_ui.py', 'clients/desktop/updates.py', 'clients/desktop/update.pub',
            'provisioning/chat_client.py', 'provisioning/chat_rpc.py', 'provisioning/chat_owner.py',
            'provisioning/chat_bridge.py', 'provisioning/chat_direct.py', 'provisioning/chat_events.py',
            'device_identity/device.py', 'messenger/store.py', 'python-runtime.json', 'remove_user_service.py',
            'integration/family-connect-chat.service', 'integration/com.familyconnect.Chat1.service',
            'integration/AppRun', 'integration/postinst', 'integration/prerm'}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read_file(path, maximum):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as source:
        before = os.fstat(source.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size > maximum or before.st_mode & 0o6022:
            raise ValueError('Unsafe candidate member')
        raw = source.read(maximum + 1)
        after = os.fstat(source.fileno())
        if len(raw) != before.st_size or (before.st_ctime_ns, before.st_mtime_ns) != (after.st_ctime_ns, after.st_mtime_ns):
            raise ValueError('Candidate member changed')
        return raw


def verify(root=ROOT):
    record = json.loads(read_file(root / 'candidate.json', 1048576))
    if (record['schema'] != 1 or record['runtime_contract'] != 2 or record.get('authorization_protocol') != 2 or
            record['python'] != list(sys.version_info[:2])):
        raise ValueError('Candidate runtime contract/ABI mismatch')
    identity = digest(json.dumps({key: value for key, value in record.items() if key != 'build_id'},
                                 sort_keys=True, separators=(',', ':')).encode())
    if identity != record['build_id'] or not re.fullmatch('[a-f0-9]{40}', record['source_commit']):
        raise ValueError('Candidate identity mismatch')
    files = record['files']
    if not REQUIRED <= set(files) or len(files) > 8192:
        raise ValueError('Candidate user runtime incomplete')
    actual = set()
    for path in root.rglob('*'):
        if path.is_symlink():
            raise ValueError('Candidate symlink rejected')
        if path.is_file():
            actual.add(str(path.relative_to(root)))
        elif not path.is_dir():
            raise ValueError('Non-regular candidate member')
    if actual != set(files) | {'candidate.json'}:
        raise ValueError('Candidate member inventory mismatch')
    for name, expected in files.items():
        if Path(name).is_absolute() or any(part in ('', '.', '..') for part in name.split('/')):
            raise ValueError('Invalid candidate path')
        raw = read_file(root / name, 80 * 1024 * 1024)
        if len(raw) != expected['size'] or digest(raw) != expected['sha256']:
            raise ValueError('Candidate member hash mismatch: ' + name)
    system = record['system']
    if files['embedded/system.tar.gz'] != {key: system[key] for key in ('sha256', 'size')}:
        raise ValueError('Candidate system binding mismatch')
    if root == Path('/usr/lib/family-connect'):
        for relative in ('usr/lib/systemd/user/family-connect-chat.service',
                         'usr/share/dbus-1/services/com.familyconnect.Chat1.service'):
            if read_file(Path('/') / relative, 65536) != read_file(root / 'integration' / Path(relative).name, 65536):
                raise ValueError('Installed user service differs from candidate')
    return record


def installed_guard(capability):
    try:
        record = verify()
        if capability['build_id'] != record['system']['build_id']:
            return 'CANDIDATE_SYSTEM_BUILD_MISMATCH'
        if capability.get('authorization_protocol') != record['authorization_protocol']:
            return 'CANDIDATE_AUTHORIZATION_PROTOCOL_MISMATCH'
        return 'READY'
    except (OSError, ValueError, KeyError, TypeError):
        return 'CANDIDATE_USER_INTEGRITY_FAILED'


def setup():
    if os.geteuid() == 0:
        raise ValueError('Run candidate setup as your ordinary desktop user')
    record = verify()
    raw = read_file(ROOT / 'embedded/system.tar.gz', 80 * 1024 * 1024)
    from candidate_setup import extract_verified
    with tempfile.TemporaryDirectory(prefix='family-connect-user-setup-') as temporary:
        extract_verified(raw, record['system'], Path(temporary))
        source = read_file(ROOT / 'candidate_setup.py', 65536)
        if digest(source) != record['files']['candidate_setup.py']['sha256']:
            raise ValueError('Setup changed after verification')
        command = source.decode() + '\nroot_main(' + repr(record['system']) + ')\n'
        result = subprocess.run(['/usr/bin/pkexec', '/usr/bin/python3', '-I', '-S', '-c', command],
                                input=raw, capture_output=True,
                                env={key: value for key, value in os.environ.items() if key in
                                     ('DISPLAY', 'WAYLAND_DISPLAY', 'XAUTHORITY', 'XDG_RUNTIME_DIR', 'DBUS_SESSION_BUS_ADDRESS', 'LANG', 'LC_ALL')} |
                                    {'PATH': '/usr/sbin:/usr/bin:/sbin:/bin'})
        if result.returncode:
            raise ValueError('System setup cancelled or refused; no automatic retry. ' + result.stderr.decode(errors='replace')[-1500:])
    return json.loads(result.stdout)


def check_imports():
    import importlib
    import gi
    gi.require_version('Gtk', '4.0')
    gi.require_version('Adw', '1')
    for name in ('backend', 'chat_daemon', 'chat_voice', 'chat_notifications', 'chat_announcements',
                 'support_daemon', 'friends_ui', 'provisioning.chat_client', 'provisioning.chat_direct',
                 'provisioning.chat_bridge', 'provisioning.chat_owner', 'device_identity.device',
                 'messenger.codec', 'RNS', 'LXMF', 'cryptography', 'httpx', 'pydantic'):
        module = importlib.import_module(name)
        if not Path(module.__file__).resolve().is_relative_to(ROOT):
            raise ValueError('User import escaped candidate: ' + name)
    from gi.repository import Gio
    gi.require_version('Gst', '1.0')
    from gi.repository import Gst
    Gst.init(None)
    import ctypes
    ctypes.CDLL('libcodec2.so.1.2')
    return {'user_imports': 'PASS', 'candidate': verify()['build_id']}


def remove_integration():
    verify()
    image = Path(os.environ.get('APPIMAGE', '')).resolve()
    appdir = Path(os.environ.get('APPDIR', '')).resolve()
    if os.geteuid() == 0 or not image.is_file() or not ROOT.is_relative_to(appdir):
        raise ValueError('Run this action from your original AppImage as an ordinary user')
    unit = ['systemctl', '--user']
    command = subprocess.run(unit + ['show', 'family-connect-chat.service', '-p', 'ExecStart', '--value'],
                             check=True, capture_output=True, text=True, timeout=10).stdout
    if 'path=' + str(image) + ' ;' in command:
        subprocess.run(unit + ['stop', 'family-connect-chat.service'], check=True, timeout=50)
    desktop = Path.home() / '.local/share/applications/com.familyconnect.Client.desktop'
    if desktop.exists() and 'Exec="' + str(image) + '" %u\n' in read_file(desktop, 65536).decode():
        desktop.unlink()
    return {'integration_removed': True, 'user_state_changed': False, 'system_runtime_removed': False}
