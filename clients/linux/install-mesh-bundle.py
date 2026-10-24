#!/usr/bin/python3 -I
"""Offline system-component installation, with own-file rollback and no activation."""
import fcntl
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile

ROOT = Path('/usr/local/lib/family-connect-mesh')
BACKUPS = Path('/var/backups/family-connect')
CONFIG_DIRECTORIES = (Path('/etc/family-connect/awg'), Path('/etc/family-connect/tcp'))
MODULES = ('backend.py', 'profile_config.py', 'system_runtime.py', 'chat_direct_host.py', 'mesh_chat_service.py', 'mesh_ipc.py', 'mesh_chat.py', 'mesh_chat_host.py', 'mesh_materials.py', 'mesh_network.py', 'mesh_intent.py', 'mesh_service.py', 'mesh_system.py', 'mesh_ownership.py',
           'auto_guard.py', 'auto_policy.py', 'auto_mesh.py', 'auto_configuration.py', 'auto_normal.py', 'auto_normal_worker.py',
           'auto_platform.py', 'auto_runtime.py', 'auto_ipc.py', 'auto_intent.py', 'auto_service.py', 'awg_lifecycle.py')
COMMON = ('provisioning/__init__.py', 'provisioning/friends_catalog.py', 'provisioning/chat_bridge_protocol.py', 'clients/desktop/profile_config.py',
          'provisioning/chat_bridge.py', 'provisioning/chat_direct.py', 'provisioning/friends.py', 'provisioning/support.py',
          'device_identity/__init__.py', 'device_identity/device.py', 'device_identity/friends.py',
          'messenger/__init__.py', 'messenger/admission.py', 'messenger/codec.py')
UNITS = ('mesh', 'auto', 'chat-direct', 'chat-mesh')
NORMAL_FILES = {'awg': ('awg', 'amneziawg-go', 'awg-quick', 'awg31.json', 'LICENSE-go', 'LICENSE-tools'),
                'tcp': ('xray', 'LICENSE')}
FILES = {'bin/fc-mesh': (ROOT / 'fc-mesh', 0o755), 'lib/helper': (ROOT / 'helper', 0o755),
         **{'normal/' + kind + '/' + name: (Path('/usr/local/lib/family-connect-' + kind) / name,
             0o755 if name in ('awg', 'amneziawg-go', 'awg-quick', 'xray') else 0o644)
            for kind, names in NORMAL_FILES.items() for name in names},
         'normal/build.json': (ROOT / 'normal-build.json', 0o644),
         'systemd/family-connect-tcp@.service': (Path('/etc/systemd/system/family-connect-tcp@.service'), 0o644),
         'lib/update.pub': (ROOT / 'update.pub', 0o644),
         'python-runtime.json': (ROOT / 'python-runtime.json', 0o644),
         **{'native/' + name: (ROOT / 'native' / name, 0o644)
            for name in ('build.json', 'source-inventory.json', 'dependencies.json')},
         'rns/fc-rns.pyz': (ROOT / 'rns/fc-rns.pyz', 0o644),
         'rns/build.json': (ROOT / 'rns/build.json', 0o644),
         **{'lib/' + name: (ROOT / name, 0o644) for name in MODULES},
         **{'lib/' + name: (ROOT / name, 0o644) for name in COMMON},
         **{'systemd/family-connect-' + name + '@.service': (Path('/etc/systemd/system/family-connect-' + name + '@.service'), 0o644)
            for name in UNITS}}
CAPABILITY = ROOT / 'capabilities.json'
AUTO_CAPABILITY = ROOT / 'auto-capabilities.json'
LOCKS = ('family-connect-system-install.lock', 'family-connect-transport.lock', 'family-connect-awg.lock', 'family-connect-tcp.lock',
         'family-connect-tcp-runtime.lock', 'family-connect-mesh-runtime.lock', 'family-connect-auto-runtime.lock',
         'family-connect-auto-command.lock')


def command(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True, timeout=30,
                          env={'PATH': '/usr/sbin:/usr/bin:/sbin:/bin', 'LC_ALL': 'C'})


def trusted(path, directory=False):
    info = path.lstat()
    if (info.st_uid != 0 or info.st_mode & 0o022 or
            not (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)) or
            (not directory and info.st_nlink != 1)):
        raise ValueError('Unsafe system-component destination')
    return info


def directory(path):
    if path.exists() or path.is_symlink():
        for parent in (path, *path.parents):
            trusted(parent, directory=True)
    else:
        directory(path.parent)
        path.mkdir(mode=0o755)
        path.chmod(0o755)
        sync_directory(path.parent)


def atomic(path, data, mode):
    directory(path.parent)
    if path.exists() or path.is_symlink():
        trusted(path)
    descriptor, temporary = tempfile.mkstemp(prefix='.fc-mesh-install-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as output:
            output.write(data)
            output.flush()
            os.fchmod(output.fileno(), mode)
            os.fsync(output.fileno())
        os.replace(temporary, path)
        parent = os.open(path.parent, os.O_DIRECTORY | os.O_RDONLY | os.O_NOFOLLOW)
        try:
            os.fsync(parent)
        finally:
            os.close(parent)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def target(name):
    if name in FILES:
        return FILES[name]
    if re.fullmatch(r'licenses/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*', name) and not any(part in ('.', '..') for part in name.split('/')):
        return ROOT / name, 0o644
    if name in ('compat/awg-helper.py', 'compat/tcp-helper.py'):
        kind = name.split('/')[1].split('-')[0]
        return Path('/usr/local/lib/family-connect-' + kind + '/helper'), 0o755
    if (name.startswith('vendor/') and re.fullmatch(r'vendor/[A-Za-z0-9_.+/-]+', name) and
            not any(part in ('', '.', '..', '__pycache__') for part in name.split('/')) and
            not name.endswith(('.pth', '.pyc', '.pyo'))):
        return ROOT / name, 0o644
    raise ValueError('Unexpected bundle member')


def read_member(path, maximum):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as source:
        before = os.fstat(source.fileno())
        if (not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size > maximum or
                before.st_mode & 0o6022):
            raise ValueError('Unsafe or oversized bundle member')
        raw = source.read(maximum + 1)
        after = os.fstat(source.fileno())
        if len(raw) != before.st_size or (before.st_mtime_ns, before.st_ctime_ns) != (after.st_mtime_ns, after.st_ctime_ns):
            raise ValueError('Bundle member changed while reading')
        return raw


def verify(bundle):
    if bundle.is_symlink() or not bundle.is_dir():
        raise ValueError('Unsafe bundle directory')
    raw = read_member(bundle / 'manifest.json', 1048576)
    manifest = json.loads(raw)
    if (set(manifest) != {'schema', 'architecture', 'source_digest', 'sha256', 'sizes', 'signing', 'build_id'} or manifest['schema'] != 2 or
            manifest['architecture'] != 'amd64' or not re.fullmatch('[a-f0-9]{64}', manifest['source_digest']) or
            manifest['signing'] != 'unsigned-private-component'):
        raise ValueError('Unsupported system-component bundle')
    hashes = manifest['sha256']
    required = set(FILES) | {'compat/awg-helper.py', 'compat/tcp-helper.py', 'install.py', 'README.txt'}
    if (not isinstance(hashes, dict) or not required <= set(hashes) or len(hashes) > 8192 or
            set(manifest['sizes']) != set(hashes)):
        raise ValueError('Incomplete system-component bundle')
    expected_id = hashlib.sha256(json.dumps({key: value for key, value in manifest.items() if key != 'build_id'},
                                           sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    if manifest['build_id'] != expected_id:
        raise ValueError('Component build ID mismatch')
    members = set()
    for path in bundle.rglob('*'):
        info = path.lstat()
        if stat.S_ISDIR(info.st_mode):
            continue
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise ValueError('Unsafe bundle member or symlink')
        members.add(str(path.relative_to(bundle)))
    if members != set(hashes) | {'manifest.json'}:
        raise ValueError('Unexpected bundle members')
    payload = {}
    total = 0
    for name, digest in hashes.items():
        if name not in ('install.py', 'README.txt'):
            target(name)
        path = bundle / name
        for parent in (path, *path.parents):
            if parent == bundle:
                break
            if parent.is_symlink():
                raise ValueError('Bundle symlinks are not accepted')
        info = path.lstat()
        maximum = (64 if name == 'normal/tcp/xray' else 40) * 1024 * 1024
        if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size > maximum or
                type(manifest['sizes'][name]) is not int or info.st_size != manifest['sizes'][name]):
            raise ValueError('Invalid bundle member')
        raw = read_member(path, maximum)
        total += len(raw)
        if total > 128 * 1024 * 1024:
            raise ValueError('Oversized component bundle')
        if hashlib.sha256(raw).hexdigest() != digest:
            raise ValueError('Bundle checksum mismatch')
        payload[name] = raw
    runtime = json.loads(payload['python-runtime.json'])
    if runtime['files'] != {name: checksum for name, checksum in hashes.items() if name.startswith('vendor/')}:
        raise ValueError('Python runtime inventory mismatch')
    return manifest, payload


def acquire():
    descriptors = []
    try:
        for name in LOCKS:
            descriptor = os.open('/run/' + name, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
            descriptors.append(descriptor)
            info = os.fstat(descriptor)
            if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_nlink != 1 or stat.S_IMODE(info.st_mode) != 0o600:
                raise ValueError('Unsafe component lock')
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        for name in ('/run/family-connect-mesh/active.json', '/run/family-connect-tcp/active', '/run/family-connect-awg/active.json',
                     '/run/family-connect-auto/guard.json', '/run/family-connect-auto/normal.json', '/run/family-connect-auto/mesh.json'):
            if Path(name).exists() or Path(name).is_symlink():
                raise ValueError('Finish VPN cleanup before system-component installation')
        owner = Path('/run/family-connect-mesh-owner')
        directory(owner)
        for name in ('vpn.lock', 'transport.lock'):
            path = owner / name
            descriptor = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
            descriptors.append(descriptor)
            info = os.fstat(descriptor)
            if (not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_nlink != 1 or
                    stat.S_IMODE(info.st_mode) != 0o600):
                raise ValueError('Unsafe MESH ownership lock')
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            if name == 'transport.lock' and os.fstat(descriptor).st_size:
                raise ValueError('MESH cleanup is unconfirmed; retain the sticky marker')
        for kind in ('direct', 'mesh'):
            runtime = Path('/run/family-connect-chat-' + kind)
            if not (runtime.exists() or runtime.is_symlink()):
                continue
            directory(runtime)
            for path in runtime.glob('*.lock'):
                trusted(path)
                descriptor = os.open(path, os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK)
                descriptors.append(descriptor)
                actual = os.fstat(descriptor)
                expected = trusted(path)
                if (actual.st_dev, actual.st_ino) != (expected.st_dev, expected.st_ino) or stat.S_IMODE(actual.st_mode) != 0o600:
                    raise ValueError('Unsafe chat lifecycle lock')
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        for name in ('/run/family-connect-mesh/active.json', '/run/family-connect-tcp/active', '/run/family-connect-awg/active.json',
                     '/run/family-connect-auto/guard.json', '/run/family-connect-auto/normal.json', '/run/family-connect-auto/mesh.json'):
            if Path(name).exists() or Path(name).is_symlink():
                raise ValueError('Finish VPN cleanup before system-component installation')
        idle_services()
        for link in json.loads(command('ip', '-j', 'link', 'show').stdout):
            if re.fullmatch(r'fc(?:mesh0|(?:awg|tcp)[a-f0-9]{8})', link.get('ifname', '')):
                raise ValueError('Disconnect Family Connect before installation')
        return descriptors
    except Exception:
        for descriptor in descriptors:
            os.close(descriptor)
        raise


def idle_services():
    units = command('systemctl', 'list-units', *('family-connect-' + name + '@*.service' for name in (*UNITS, 'tcp')),
                    '--state=active,activating,deactivating', '--no-legend', '--plain').stdout
    if units.strip():
        raise ValueError('Live Family Connect service owner; installation refused')


@contextmanager
def service_barrier():
    originals = {}
    try:
        idle_services()
        for name in (*UNITS, 'tcp'):
            unit = 'family-connect-' + name + '@.service'
            for base in ('/etc/systemd/system', '/run/systemd/system', '/usr/lib/systemd/system'):
                folder = Path(base)
                if any(path.name != unit for path in folder.glob('family-connect-' + name + '@*.service')) or any(folder.glob('family-connect-' + name + '@*.service.d')):
                    raise ValueError('Custom service override requires separate review')
            path = Path('/etc/systemd/system') / unit
            directory(path.parent)
            original = None
            if path.exists() or path.is_symlink():
                info = trusted(path)
                original = (path.read_bytes(), stat.S_IMODE(info.st_mode))
            originals[path] = original
        directory(BACKUPS)
        saved = Path(tempfile.mkdtemp(prefix='service-barrier-', dir=BACKUPS))
        for path, original in originals.items():
            if original is not None:
                atomic(saved / path.name, original[0], 0o600)
        atomic(saved / 'restore.json', json.dumps({str(path): None if value is None else
            dict(file=path.name, mode=value[1], sha256=hashlib.sha256(value[0]).hexdigest())
            for path, value in originals.items()}).encode(), 0o600)
        for path in originals:
            temporary = path.with_name('.fc-install-mask-' + path.name)
            os.symlink('/dev/null', temporary)
            os.replace(temporary, path)
            sync_directory(path.parent)
        command('systemctl', 'daemon-reload')
        idle_services()
        yield originals
    finally:
        for path, original in originals.items():
            if path.is_symlink() and os.readlink(path) == '/dev/null':
                path.unlink()
                if original is not None:
                    atomic(path, *original)
                sync_directory(path.parent)
        if originals:
            command('systemctl', 'daemon-reload')


def sync_directory(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def apply(payload, source_digest, build_id=None, masked=None):
    version = command('systemctl', '--version').stdout
    match = re.match(r'systemd ([0-9]+)\b', version)
    if match is None or int(match[1]) < 254:
        raise ValueError('MESH recovery requires systemd254 or newer')
    vendor = ROOT / 'vendor'
    if vendor.exists() or vendor.is_symlink():
        directory(vendor)
        for path in vendor.rglob('*'):
            if path.is_dir() and not path.is_symlink():
                directory(path)
            elif str(path.relative_to(ROOT)) not in payload:
                raise ValueError('Unowned Python runtime member; preserve it for separate review')
    destinations = {}
    for name, data in payload.items():
        if name in ('install.py', 'README.txt'):
            continue
        path, mode = target(name)
        destinations[path] = (data, mode)
        if name.startswith('compat/'):
            destinations[path.parent / 'authorization-session-v1'] = (b'', 0o644)
            for module in ('backend.py', 'profile_config.py'):
                destinations[path.parent / module] = (payload['lib/' + module], 0o644)
            if name == 'compat/awg-helper.py':
                destinations[path.parent / 'awg_lifecycle.py'] = (payload['lib/awg_lifecycle.py'], 0o644)
    inventory = dict(schema=2, build_id=build_id, source_digest=source_digest,
                     files={str(path): dict(sha256=hashlib.sha256(raw).hexdigest(), size=len(raw), mode=mode)
                            for path, (raw, mode) in destinations.items()})
    installed_raw = json.dumps(inventory, sort_keys=True, separators=(',', ':')).encode()
    destinations[ROOT / 'installed.json'] = (installed_raw, 0o644)
    capability = dict(schema=2, runtime_contract=2, chat_setup_protocol=1, bridge_protocol=1, materials_protocol=1, intent_protocol=1, core_reference='android106-native105',
                      build_id=build_id, installed_sha256=hashlib.sha256(installed_raw).hexdigest(),
                      source_digest=source_digest, profiles=['P0', 'P1'])
    destinations[ROOT / 'authorization-session-v1'] = (b'', 0o644)
    destinations[CAPABILITY] = (json.dumps(capability, separators=(',', ':')).encode(), 0o644)
    destinations[AUTO_CAPABILITY] = (json.dumps(dict(schema=2, service_protocol=1, catalog_protocol=1,
        source_digest=source_digest, build_id=build_id), separators=(',', ':')).encode(), 0o644)
    previous = {}
    for path in CONFIG_DIRECTORIES:
        directory(path)
        if stat.S_IMODE(path.lstat().st_mode) != 0o755:
            raise ValueError('Normal transport configuration directory must remain mode0755')
    for path in destinations:
        directory(path.parent)
        if masked is not None and path in masked:
            if masked[path] is not None:
                previous[path] = masked[path]
            continue
        if path.exists() or path.is_symlink():
            info = trusted(path)
            if info.st_size > (64 if path == Path('/usr/local/lib/family-connect-tcp/xray') else 40) * 1024 * 1024:
                raise ValueError('Oversized installed component')
            previous[path] = (path.read_bytes(), stat.S_IMODE(info.st_mode))
    directory(BACKUPS)
    backup = Path(tempfile.mkdtemp(prefix='mesh-bundle-', dir=BACKUPS))
    records = []
    for index, (path, value) in enumerate(previous.items()):
        raw, mode = value
        saved = backup / str(index)
        atomic(saved, raw, 0o600)
        records.append(dict(path=str(path), file=str(index), mode=mode, sha256=hashlib.sha256(raw).hexdigest()))
    atomic(backup / 'restore.json', json.dumps(dict(previous=records, new_files=[str(path) for path in destinations if path not in previous])).encode(), 0o600)
    changed = []
    try:
        for marker in (CAPABILITY, AUTO_CAPABILITY):
            if marker in previous:
                marker.unlink()
                sync_directory(marker.parent)
                changed.append(marker)
        for path, (raw, mode) in destinations.items():
            if path in (CAPABILITY, AUTO_CAPABILITY):
                continue
            if path not in changed:
                changed.append(path)
            if masked is not None and path in masked and path.is_symlink() and os.readlink(path) == '/dev/null':
                path.unlink()
            atomic(path, raw, mode)
        for path, (raw, mode) in destinations.items():
            if path in (CAPABILITY, AUTO_CAPABILITY):
                continue
            info = trusted(path)
            if stat.S_IMODE(info.st_mode) != mode or path.read_bytes() != raw:
                raise ValueError('Installed system file readback mismatch')
        actual = json.loads(command(str(ROOT / 'fc-mesh'), '--version').stdout)
        if (actual.get('source_manifest') != source_digest or actual.get('core_reference') != 'android106-native105' or
                actual.get('bridge_protocol') != 1 or actual.get('materials_protocol') != 1 or actual.get('os') != 'linux' or
                actual.get('auto_policy_protocol') != 1 or actual.get('normal_configuration_protocol') != 1 or
                actual.get('chat_ipc_protocol') != 1 or actual.get('private_chat_endpoint') != 'inherited-unix-stream' or
                actual.get('arch') != 'amd64' or actual.get('profiles') != ['P0', 'P1']):
            raise ValueError('Installed native worker does not match the verified component')
        relay = json.loads(command('/usr/bin/python3', '-I', '-S', str(ROOT / 'rns/fc-rns.pyz'), '--version').stdout)
        if relay != dict(rns_protocol=1, rns='1.5.1', pyserial='3.5', crypto_provider='internal'):
            raise ValueError('Installed RNS runtime does not match the verified component')
        runtime = json.loads(command('/usr/bin/python3', '-I', '-S', str(ROOT / 'system_runtime.py'), '--check').stdout)
        if runtime.get('runtime') != 2 or runtime.get('imports') != 'PASS':
            raise ValueError('Installed Python runtime readback failed')
        command('systemctl', 'daemon-reload')
        if CAPABILITY not in changed:
            changed.append(CAPABILITY)
        atomic(CAPABILITY, *destinations[CAPABILITY])
        if AUTO_CAPABILITY not in changed:
            changed.append(AUTO_CAPABILITY)
        atomic(AUTO_CAPABILITY, *destinations[AUTO_CAPABILITY])
        return backup
    except Exception:
        for path in reversed(changed):
            if path in previous:
                atomic(path, *previous[path])
            elif path.exists():
                trusted(path)
                path.unlink()
                sync_directory(path.parent)
        command('systemctl', 'daemon-reload')
        raise


def main():
    if len(sys.argv) != 1 or os.geteuid() != 0 or os.uname().machine != 'x86_64':
        raise ValueError('Authorize this offline amd64 installer explicitly; the GUI stays unprivileged')
    for program in ('ip', 'resolvectl', 'resolvconf', 'systemctl', 'pkexec', 'nft', 'curl', 'sysctl', 'bash'):
        if not shutil.which(program):
            raise ValueError('Required platform component is missing')
    if not stat.S_ISCHR(Path('/dev/net/tun').stat().st_mode):
        raise ValueError('System TUN is unavailable')
    manifest, payload = verify(Path(__file__).resolve().parent)
    descriptors = acquire()
    try:
        with service_barrier() as masked:
            backup = apply(payload, manifest['source_digest'], manifest['build_id'], masked)
        print(json.dumps(dict(installed=True, backup=str(backup), service_started=False, user_state_changed=False)))
    finally:
        for descriptor in descriptors:
            os.close(descriptor)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        reason = str(error) if isinstance(error, ValueError) else type(error).__name__
        print('System component installation refused/failed; no activation requested: ' + reason, file=sys.stderr)
        raise SystemExit(1)
