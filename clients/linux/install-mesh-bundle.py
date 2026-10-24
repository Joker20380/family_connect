#!/usr/bin/python3 -I
"""Offline system-component installation, with own-file rollback and no activation."""
import fcntl
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
MODULES = ('backend.py', 'profile_config.py', 'mesh_ipc.py', 'mesh_chat.py', 'mesh_chat_host.py', 'mesh_materials.py', 'mesh_network.py', 'mesh_intent.py', 'mesh_service.py', 'mesh_system.py',
           'auto_guard.py', 'auto_policy.py', 'auto_mesh.py', 'auto_configuration.py', 'auto_normal.py', 'auto_normal_worker.py',
           'auto_platform.py', 'auto_runtime.py', 'auto_ipc.py', 'auto_intent.py', 'auto_service.py', 'awg_lifecycle.py')
COMMON = ('provisioning/__init__.py', 'provisioning/friends_catalog.py', 'provisioning/chat_bridge_protocol.py', 'clients/desktop/profile_config.py')
FILES = {'bin/fc-mesh': (ROOT / 'fc-mesh', 0o755), 'lib/helper': (ROOT / 'helper', 0o755),
         'rns/fc-rns.pyz': (ROOT / 'rns/fc-rns.pyz', 0o644),
         'rns/build.json': (ROOT / 'rns/build.json', 0o644),
         **{'lib/' + name: (ROOT / name, 0o644) for name in MODULES},
         **{'lib/' + name: (ROOT / name, 0o644) for name in COMMON},
         **{'systemd/family-connect-' + name + '@.service': (Path('/etc/systemd/system/family-connect-' + name + '@.service'), 0o644)
            for name in ('mesh', 'auto')}}
CAPABILITY = ROOT / 'capabilities.json'
AUTO_CAPABILITY = ROOT / 'auto-capabilities.json'
LOCKS = ('family-connect-transport.lock', 'family-connect-awg.lock', 'family-connect-tcp.lock',
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
    raise ValueError('Unexpected bundle member')


def verify(bundle):
    with (bundle / 'manifest.json').open('rb') as source:
        raw = source.read(65537)
    if len(raw) > 65536:
        raise ValueError('Oversized bundle manifest')
    manifest = json.loads(raw)
    if (set(manifest) != {'schema', 'architecture', 'source_digest', 'sha256', 'signing'} or manifest['schema'] != 1 or
            manifest['architecture'] != 'amd64' or not re.fullmatch('[a-f0-9]{64}', manifest['source_digest']) or
            manifest['signing'] != 'unsigned-private-component'):
        raise ValueError('Unsupported system-component bundle')
    hashes = manifest['sha256']
    required = set(FILES) | {'compat/awg-helper.py', 'compat/tcp-helper.py', 'install.py', 'README.txt'}
    if not isinstance(hashes, dict) or not required <= set(hashes) or len(hashes) > 256:
        raise ValueError('Incomplete system-component bundle')
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
        if not path.is_file() or path.stat().st_size > 40 * 1024 * 1024:
            raise ValueError('Invalid bundle member')
        raw = path.read_bytes()
        total += len(raw)
        if total > 128 * 1024 * 1024:
            raise ValueError('Oversized component bundle')
        if hashlib.sha256(raw).hexdigest() != digest:
            raise ValueError('Bundle checksum mismatch')
        payload[name] = raw
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
        units = command('systemctl', 'list-units', 'family-connect-mesh@*.service', 'family-connect-tcp@*.service', 'family-connect-auto@*.service',
                        '--state=active,activating,deactivating', '--no-legend', '--plain').stdout
        if units.strip():
            raise ValueError('Stop Family Connect services before installation')
        for link in json.loads(command('ip', '-j', 'link', 'show').stdout):
            if re.fullmatch(r'fc(?:mesh0|(?:awg|tcp)[a-f0-9]{8})', link.get('ifname', '')):
                raise ValueError('Disconnect Family Connect before installation')
        return descriptors
    except Exception:
        for descriptor in descriptors:
            os.close(descriptor)
        raise


def apply(payload, source_digest):
    version = command('systemctl', '--version').stdout
    match = re.match(r'systemd ([0-9]+)\b', version)
    if match is None or int(match[1]) < 254:
        raise ValueError('MESH recovery requires systemd254 or newer')
    destinations = {}
    for name, data in payload.items():
        if name in ('install.py', 'README.txt'):
            continue
        path, mode = target(name)
        if name.startswith('compat/') and not (path.exists() or path.is_symlink()):
            continue
        destinations[path] = (data, mode)
        if name.startswith('compat/'):
            for module in ('backend.py', 'profile_config.py'):
                destinations[path.parent / module] = (payload['lib/' + module], 0o644)
            if name == 'compat/awg-helper.py':
                destinations[path.parent / 'awg_lifecycle.py'] = (payload['lib/awg_lifecycle.py'], 0o644)
    capability = dict(schema=1, bridge_protocol=1, materials_protocol=1, intent_protocol=1, core_reference='android106-native105',
                      source_digest=source_digest, profiles=['P0', 'P1'])
    destinations[ROOT / 'authorization-session-v1'] = (b'', 0o644)
    destinations[CAPABILITY] = (json.dumps(capability, separators=(',', ':')).encode(), 0o644)
    destinations[AUTO_CAPABILITY] = (json.dumps(dict(schema=1, service_protocol=1, catalog_protocol=1,
        source_digest=source_digest), separators=(',', ':')).encode(), 0o644)
    previous = {}
    for path in destinations:
        directory(path.parent)
        if path.exists() or path.is_symlink():
            info = trusted(path)
            if info.st_size > 40 * 1024 * 1024:
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
                changed.append(marker)
        for path, (raw, mode) in destinations.items():
            if path in (CAPABILITY, AUTO_CAPABILITY):
                continue
            if path not in changed:
                changed.append(path)
            atomic(path, raw, mode)
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
        command('systemctl', 'daemon-reload')
        raise


def main():
    if len(sys.argv) != 1 or os.geteuid() != 0 or os.uname().machine != 'x86_64':
        raise ValueError('Authorize this offline amd64 installer explicitly; the GUI stays unprivileged')
    for program in ('ip', 'resolvectl', 'systemctl', 'pkexec'):
        if not shutil.which(program):
            raise ValueError('Required platform component is missing')
    if not stat.S_ISCHR(Path('/dev/net/tun').stat().st_mode):
        raise ValueError('System TUN is unavailable')
    manifest, payload = verify(Path(__file__).resolve().parent)
    descriptors = acquire()
    try:
        backup = apply(payload, manifest['source_digest'])
        print(json.dumps(dict(installed=True, backup=str(backup), service_started=False, user_state_changed=False)))
    finally:
        for descriptor in descriptors:
            os.close(descriptor)


if __name__ == '__main__':
    try:
        main()
    except Exception:
        print('MESH component installation failed; no activation was requested.', file=sys.stderr)
        raise SystemExit(1)
