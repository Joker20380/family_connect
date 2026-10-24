"""Exact archive/systemd gate. Only run inside the disposable no-network system."""
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import pwd
import shutil
import socket
import stat
import struct
import subprocess
import sys
import tarfile
import time

sys.dont_write_bytecode = True

ROOT = Path('/usr/local/lib/family-connect-mesh')
UNITS = ['family-connect-chat-' + kind + '@1000.service' for kind in ('direct', 'mesh')]
ENV = {'PATH': '/usr/sbin:/usr/bin:/sbin:/bin', 'LC_ALL': 'C'}
RESULTS = {}


def run(*args, ok=True, **options):
    result = subprocess.run(args, capture_output=True, text=True, timeout=60, env=ENV, **options)
    if ok and result.returncode:
        raise AssertionError((args, result.returncode, result.stdout[-2000:], result.stderr[-2000:]))
    return result


def record(name, value=True):
    RESULTS[name] = value
    print(json.dumps({name: value}), flush=True)


def network():
    return [run('ip', '-j', *arguments).stdout for arguments in
            (('link', 'show'), ('route', 'show', 'table', 'all'), ('rule', 'show'))] + [Path('/etc/resolv.conf').read_text()]


def python(code):
    return run('/usr/bin/python3', '-I', '-S', '-c',
               'import sys;sys.path.insert(0,' + repr(str(ROOT)) + ');from system_runtime import configure;configure();' + code).stdout.strip()


def probe(uid, kind):
    code = '''import json,socket,struct,sys,time
connection=socket.socket(socket.AF_UNIX);connection.settimeout(4)
connection.connect('/run/family-connect-chat-'+sys.argv[1]+'/1000.chat.sock')
raw=json.dumps(dict(schema=1,id=1,action='probe',device='a'*32,budget_ms=2000)).encode()
connection.sendall(struct.pack('!I',len(raw))+raw)
try:
    header=connection.recv(4)
except ConnectionResetError:
    header=b''
if not header:
    print('UID_DENIED');sys.exit(0)
size=struct.unpack('!I',header)[0];response=b''
while len(response)<size: response+=connection.recv(size-len(response))
print(response.decode())
'''
    return run('setpriv', '--reuid', str(uid), '--regid', str(uid), '--clear-groups',
               '/usr/bin/python3', '-I', '-S', '-c', code, kind).stdout.strip()


def reseal(directory):
    manifest = json.loads((directory / 'manifest.json').read_text())
    for name in manifest['sha256']:
        raw = (directory / name).read_bytes()
        manifest['sha256'][name] = hashlib.sha256(raw).hexdigest()
        manifest['sizes'][name] = len(raw)
    manifest.pop('build_id')
    manifest['build_id'] = hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    (directory / 'manifest.json').write_text(json.dumps(manifest))


def main():
    assert os.geteuid() == 0 and Path('/.dockerenv').exists()
    assert Path('/proc/1/comm').read_text().strip() == 'systemd'
    assert os.environ['FC_L031_HOST_NETNS'] != str(Path('/proc/self/ns/net').stat().st_ino)
    assert [entry['ifname'] for entry in json.loads(run('ip', '-j', 'link').stdout)] == ['lo']
    assert run('systemctl', '--version').stdout.startswith('systemd 255 ')
    for unit in ('dbus', 'systemd-resolved'):
        assert run('systemctl', 'is-active', unit).stdout.strip() == 'active'
    Path('/etc/resolv.conf').write_text('nameserver 127.0.0.53\n')
    before = network()
    archive = Path(sys.argv[1])
    destination = Path('/opt/fc-l031-archive')
    destination.mkdir()
    with tarfile.open(archive) as source:
        members = source.getmembers()
        assert len({member.name for member in members}) == len(members)
        assert all(member.isfile() and not Path(member.name).is_absolute() and '..' not in Path(member.name).parts for member in members)
        source.extractall(destination, filter='data')
    bundle = destination / 'FamilyConnect-MESH-system-amd64'
    spec = importlib.util.spec_from_file_location('exact_installer', bundle / 'install.py')
    installer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(installer)
    manifest, payload = installer.verify(bundle)
    record('archive', dict(sha256=hashlib.sha256(archive.read_bytes()).hexdigest(), build_id=manifest['build_id'], members=len(members)))
    extracted = Path('/opt/fc-l031-extracted-runtime')
    for name, raw in payload.items():
        if name in ('install.py', 'README.txt'):
            continue
        target, mode = installer.target(name)
        if target.is_relative_to(ROOT):
            path = extracted / target.relative_to(ROOT)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
            path.chmod(mode)
    record('extracted_isolated_imports', json.loads(run('/usr/bin/python3', '-I', '-S', str(extracted / 'system_runtime.py'), '--check', cwd='/').stdout))
    try:
        account = pwd.getpwuid(1000)
    except KeyError:
        run('useradd', '--uid', '1000', '--create-home', 'fc-smoke')
        account = pwd.getpwuid(1000)
    state = Path(account.pw_dir) / '.local/share/family-connect/l031-synthetic'
    state.mkdir(parents=True)
    saved = {}
    for name in ('identity', 'history.db', 'settings.json'):
        path = state / name
        path.write_bytes(('synthetic ' + name).encode())
        os.chown(path, 1000, 1000)
        path.chmod(0o600)
        saved[path] = path.read_bytes()
    ROOT.mkdir(parents=True)
    safe = ROOT / 'unrelated-safe-file'
    safe.write_bytes(b'existing safe content')
    saved[safe] = safe.read_bytes()
    install_command = ('/usr/bin/python3', '-I', '-S', str(bundle / 'install.py'))
    previous_umask = os.umask(0o077)
    try:
        record('installation', json.loads(run(*install_command).stdout))
    finally:
        os.umask(previous_umask)
    for kind in ('awg', 'tcp'):
        info = (Path('/etc/family-connect') / kind).lstat()
        assert info.st_uid == 0 and stat.S_ISDIR(info.st_mode) and not info.st_mode & 0o022
    record('installed_normal_binaries', dict(awg=run('/usr/local/lib/family-connect-awg/awg', '--version').stdout.strip(),
           xray=run('/usr/local/lib/family-connect-tcp/xray', 'version').stdout.splitlines()[0]))
    assert python("import backend;print(backend.system_component_status(), backend.auto_component_available())") == 'READY True'
    record('installed_imports', json.loads(run('/usr/bin/python3', '-I', '-S', str(ROOT / 'system_runtime.py'), '--check', cwd='/').stdout))
    rule = Path('/etc/polkit-1/rules.d/10-fc-l031-fixture.rules')
    rule.write_text('polkit.addRule(function(action, subject) { if (action.id == "org.freedesktop.policykit.exec" && subject.user == ' +
                    json.dumps(account.pw_name) + ' && action.lookup("program") == "/usr/local/lib/family-connect-mesh/helper") return polkit.Result.YES; });\n')
    run('systemctl', 'restart', 'polkit')
    setup_code = 'import sys;sys.path.insert(0,' + repr(str(ROOT)) + ');import backend;backend.prepare_chat_services();print("UID_SETUP_OK")'
    setup = ('runuser', '-u', account.pw_name, '--', '/usr/bin/python3', '-I', '-S', '-c', setup_code)
    assert run(*setup).stdout.strip() == 'UID_SETUP_OK'
    for unit in UNITS:
        assert run('systemctl', 'is-active', unit).stdout.strip() == 'active'
        hardening = run('systemctl', 'show', unit, '-p', 'NoNewPrivileges', '-p', 'ProtectSystem', '-p', 'UMask').stdout
        assert all(value in hardening for value in ('NoNewPrivileges=yes', 'ProtectSystem=strict', 'UMask=0077'))
    for kind in ('direct', 'mesh'):
        path = Path('/run/family-connect-chat-' + kind) / '1000.chat.sock'
        for attempt in range(100):
            if path.exists():
                break
            time.sleep(.05)
        info = path.lstat()
        assert stat.S_ISSOCK(info.st_mode) and info.st_uid == 1000 and stat.S_IMODE(info.st_mode) == 0o600
        reply = probe(1000, kind)
        if kind == 'direct':
            assert json.loads(reply)['route'] == 'DIRECT'
        else:
            assert json.loads(reply)['ok'] is False
        assert probe(0, kind) == 'UID_DENIED'
    record('real_polkit_uid_setup_and_ipc_no_vpn')
    pids = [run('systemctl', 'show', unit, '-p', 'MainPID', '--value').stdout for unit in UNITS]
    assert run(*install_command, ok=False).returncode != 0
    assert pids == [run('systemctl', 'show', unit, '-p', 'MainPID', '--value').stdout for unit in UNITS]
    record('live_owner_refused_without_stopping')
    run('systemctl', 'stop', *UNITS)
    for kind in ('mesh', 'auto'):
        unit = 'family-connect-' + kind + '@1000.service'
        run('systemctl', 'start', unit)
        assert run('systemctl', 'is-active', unit).stdout.strip() == 'active'
        assert network() == before
        run('systemctl', 'stop', unit)
    record('manual_auto_units_idle_without_vpn')
    owner = Path('/run/family-connect-mesh-owner')
    owner.mkdir(mode=0o711, exist_ok=True)
    marker = owner / 'transport.lock'
    marker.write_bytes(b'chat')
    marker.chmod(0o600)
    assert run(*install_command, ok=False).returncode != 0 and marker.read_bytes() == b'chat'
    record('sticky_cleanup_preserved')
    marker.write_bytes(b'')
    descriptor = os.open(marker, os.O_RDWR)
    fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert run(*install_command, ok=False).returncode != 0
    os.close(descriptor)
    record('mesh_owner_lock_refused')
    wrapper = '''import importlib.util,sys,os
sys.dont_write_bytecode=True
from pathlib import Path
spec=importlib.util.spec_from_file_location('installer',sys.argv[1]);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
manifest,payload=module.verify(Path(sys.argv[1]).parent)
locks=module.acquire()
try:
    with module.service_barrier() as masks:
        print('BARRIER_HELD',flush=True);sys.stdin.readline()
        module.apply(payload,manifest['source_digest'],manifest['build_id'],masks)
finally:
    for descriptor in locks:os.close(descriptor)
'''
    process = subprocess.Popen(['/usr/bin/python3', '-I', '-S', '-c', wrapper, str(bundle / 'install.py')],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=ENV)
    assert process.stdout.readline().strip() == 'BARRIER_HELD'
    assert run('systemctl', 'start', UNITS[0], ok=False).returncode != 0
    assert run('/usr/bin/python3', '-I', '-S', str(ROOT / 'chat_direct_host.py'), '1000', ok=False).returncode != 0
    output, error = process.communicate('\n', timeout=90)
    assert process.returncode == 0, (output, error)
    record('concurrent_unit_and_direct_exec_excluded')
    snapshot = {path: path.read_bytes() for path in (ROOT / 'capabilities.json', ROOT / 'auto-capabilities.json', ROOT / 'installed.json', ROOT / 'mesh_chat_service.py')}
    negative = Path('/opt/fc-l031-negative')
    shutil.copytree(bundle, negative)
    (negative / 'lib/mesh_chat_service.py').write_bytes(b'def invalid syntax\n')
    reseal(negative)
    assert run('/usr/bin/python3', '-I', '-S', str(negative / 'install.py'), ok=False).returncode != 0
    assert all(path.read_bytes() == raw for path, raw in snapshot.items())
    assert python('import backend;print(backend.system_component_status())') == 'READY'
    record('actual_failed_import_readback_rollback')
    module = ROOT / 'provisioning/chat_direct.py'
    original = module.read_bytes()
    module.write_bytes(original + b'\n')
    assert python('import backend;print(backend.system_component_status())') == 'INSTALLED_FILE_METADATA_MISMATCH'
    module.write_bytes(original)
    assert python('import backend;print(backend.system_component_status())') == 'READY'
    module.write_bytes(b'x' + original[1:])
    assert python('import backend;print(backend.system_component_status())') == 'INSTALLED_FILE_HASH_MISMATCH'
    module.unlink()
    assert python('import backend;print(backend.system_component_status())') == 'RUNTIME_INCOMPLETE'
    module.write_bytes(original)
    module.chmod(0o644)
    legacy = ROOT / 'capabilities.json'
    current = legacy.read_bytes()
    value = json.loads(current)
    value['schema'] = 1
    legacy.write_text(json.dumps(value))
    assert python('import backend;print(backend.system_component_status())') == 'RUNTIME_CONTRACT_MISMATCH'
    legacy.write_bytes(current)
    extra = ROOT / 'vendor/unlisted'
    extra.symlink_to('/usr/lib/python3.12')
    assert python('import backend;print(backend.system_component_status())') == 'PYTHON_RUNTIME_MEMBERS_MISMATCH'
    extra.unlink()
    assert python('import backend;print(backend.system_component_status())') == 'READY'
    record('capability_rejects_changed_runtime')
    assert all(path.read_bytes() == raw for path, raw in saved.items())
    assert network() == before
    for path in ('/run/family-connect-mesh/active.json', '/run/family-connect-auto/guard.json', '/run/family-connect-tcp/active', '/run/family-connect-awg/active.json'):
        assert not Path(path).exists()
    assert run('systemctl', 'list-units', 'family-connect-mesh@*.service', 'family-connect-auto@*.service', 'family-connect-tcp@*.service', '--state=active,activating', '--no-legend').stdout.strip() == ''
    rule.unlink()
    record('identity_history_settings_safe_files_network_vpn_intent_preserved')
    print(json.dumps(dict(result='PASS', checks=RESULTS), sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
