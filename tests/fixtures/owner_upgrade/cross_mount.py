"""Disposable OWNER bind-mount rehearsal; never a live-service launcher."""
from contextlib import ExitStack
import fcntl
import hashlib
import json
import os
from pathlib import Path
import resource
import select
import signal
import subprocess
import sys
import time

IMAGES = {
    'console': 'sha256:b62e66930cd672ed5350c1e5b7c19f48f0f77ffcdbe3ce9b2b2b9a85a608e8e0',
    'system_publisher': 'sha256:2162635c93cf7cdf376aa7a0cb6189ff8a4f8105f4c26aea6d28e63ccfb93a79',
}
USERS = {'console': 10001, 'system_publisher': 1000}
RUNTIME = 'python:3.13-slim-trixie@sha256:d98cc29d3266e535dd9da1099688d9cb3ca4753813571e071763d17725460962'
DESTINATION = '/run/family-connect-capture'
NAMESPACES = ('mnt', 'pid', 'user', 'time')


def require(condition):
    if not condition:
        raise RuntimeError('CROSS_MOUNT_REFUSED')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def emit(value):
    print(json.dumps(value, sort_keys=True), flush=True)


def request():
    line = sys.stdin.readline(128)
    require(line.endswith('\n'))
    return line.strip()


def report(gate, source):
    namespaces = {}
    for name in NAMESPACES:
        info = os.stat('/proc/self/ns/' + name)
        namespaces[name] = [info.st_dev, info.st_ino]
    with gate.opened() as descriptors:
        files = {name: [os.fstat(descriptor).st_uid, os.fstat(descriptor).st_gid,
                       os.fstat(descriptor).st_mode & 0o7777] for name, descriptor in descriptors.items()}
    return dict(uid=os.getuid(), gid=os.getgid(), groups=os.getgroups(), namespaces=namespaces,
                maps={name: digest(Path('/proc/self/' + name + '_map').read_bytes()) for name in ('uid', 'gid')},
                pins={name: list(pair) for name, pair in gate.pins.items()}, files=files,
                source_sha256=digest(source), pending=len(list((gate.directory / 'pending').iterdir())))


def match(writer, guardian, uid):
    require(writer['uid'] == writer['gid'] == guardian['uid'] == guardian['gid'] == uid)
    require(writer['groups'] == [uid] and guardian['groups'] == [])
    require(writer['pins'] == guardian['pins'] and len({tuple(pair) for pair in writer['pins'].values()}) == 4)
    require(writer['maps'] == guardian['maps'] and writer['source_sha256'] == guardian['source_sha256'])
    require(all(writer['namespaces'][name] == guardian['namespaces'][name] for name in ('user', 'time')))
    require(all(writer['namespaces'][name] != guardian['namespaces'][name] for name in ('mnt', 'pid')))
    require(writer['files'] == guardian['files'] == {
        '.': [uid, uid, 0o700], 'admission.lock': [uid, uid, 0o600],
        'operations.lock': [uid, uid, 0o600], 'pending': [uid, uid, 0o700]})
    require(writer['pending'] == guardian['pending'] == 0)


def writer():
    sys.path.insert(0, '/app')
    from control.capture_gate import Gate, Busy
    source = Path('/app/control/capture_gate.py').read_bytes()
    gate = Gate(DESTINATION)
    emit(report(gate, source))
    while True:
        command = request()
        require(command in ('write', 'hold', 'crash', 'exit'))
        if command == 'exit':
            return
        try:
            with gate.operation():
                if command == 'crash':
                    os._exit(23)
                if command == 'hold':
                    emit({'status': 'ACTIVE'})
                    require(request() == 'finish')
                emit({'status': 'WRITE'})
        except Busy:
            emit({'status': 'BUSY'})


def sealed_import():
    raw = Path('/stand/guardians.pyz').read_bytes()
    descriptor = os.memfd_create('cross-mount-fixture', os.MFD_CLOEXEC | os.MFD_ALLOW_SEALING)
    with os.fdopen(os.dup(descriptor), 'wb') as output:
        output.write(raw)
    os.fchmod(descriptor, 0o444)
    fcntl.fcntl(descriptor, fcntl.F_ADD_SEALS,
                fcntl.F_SEAL_WRITE | fcntl.F_SEAL_GROW | fcntl.F_SEAL_SHRINK | fcntl.F_SEAL_SEAL)
    sys.path.insert(0, '/proc/self/fd/' + str(descriptor))
    from control import capture_launch
    capture_launch.trusted_entrypoint(digest(raw))
    return descriptor, capture_launch, raw


def actor(role, initialize=False):
    descriptor, launcher, raw = sealed_import()
    try:
        from control.capture_gate import Gate, initialize as create
        uid = USERS[role]
        parent = Path('/gates') / role
        if initialize:
            os.chown(parent, uid, uid)
        os.setgroups([])
        os.setgid(uid)
        os.setuid(uid)
        gate = create(parent / 'gate') if initialize else Gate(parent / 'gate')
        import zipfile
        import io
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            source = archive.read('control/capture_gate.py')
        emit(report(gate, source))
    finally:
        os.close(descriptor)


def coordinator(initialize=False):
    descriptor, launcher, raw = sealed_import()
    from control import capture_group as group
    try:
        observed, guardians = {}, []
        for role, uid in USERS.items():
            result = subprocess.check_output([sys.executable, '-I', '-S', '-B', __file__,
                'initialize-actor' if initialize else 'actor', role], timeout=5)
            observed[role] = json.loads(result)
            guardians.append(dict(uid=uid, gid=uid, groups=[], gate='/gates/' + role + '/gate',
                                  pins=observed[role]['pins']))
        if initialize:
            emit(observed)
            return
        binding = dict(schema=1, source_sha256=digest(raw),
            runtime_sha256=digest(Path('/proc/self/exe').read_bytes()), namespaces=launcher.namespaces(),
            mappings=launcher.mappings(), coordinator=[0, 0], guardians=guardians)
        path = Path('/sandbox/binding.json')
        path.write_bytes(json.dumps(binding, sort_keys=True).encode())
        path.chmod(0o600)
        source = Path('/sandbox/guardians.pyz')
        source.write_bytes(raw)
        source.chmod(0o600)
        emit(observed)
        while True:
            command = request()
            require(command in ('begin', 'exit'))
            if command == 'exit':
                return
            try:
                with launcher.launch(str(path), digest(path.read_bytes()), str(source)) as participants:
                    emit({'status': 'DRAINING'})
                    with group.joint(participants) as window:
                        emit({'status': 'HELD'})
                        require(request() == 'release')
                emit(window.receipt)
            except OSError as error:
                print('REHEARSAL_GATE_REFUSAL:' + str(error), file=sys.stderr, flush=True)
                emit({'status': 'REFUSED'})
    finally:
        os.close(descriptor)


def receive(process, timeout=8):
    require(select.select([process.stdout], [], [], timeout)[0])
    line = process.stdout.readline(16384)
    require(line.endswith(b'\n'))
    return json.loads(line)


def send(process, command):
    process.stdin.write((command + '\n').encode())
    process.stdin.flush()


def docker(*arguments, **kwargs):
    environment = {name: value for name, value in os.environ.items() if not name.startswith('DOCKER_')}
    return subprocess.run(['docker', '--host', 'unix:///var/run/docker.sock', *arguments],
                          capture_output=True, env=environment, timeout=30, **kwargs)


def container_binding(item, role, label, source, directory):
    require(item['Config']['Labels']['family-connect.cross-mount'] == label and
            item['State']['Running'] is True and item['State']['Pid'] > 0)
    host_config = item['HostConfig']
    require(host_config['ReadonlyRootfs'] is True and host_config['NetworkMode'] == 'none' and
            host_config['PidsLimit'] == 48 and host_config['Memory'] == 192 * 1024 * 1024)
    require(host_config['CapDrop'] == ['ALL'] and 'no-new-privileges' in host_config['SecurityOpt'])
    uid = 0 if role == 'coordinator' else USERS[role]
    require(item['Config']['User'] == str(uid) + ':' + str(uid))
    if role != 'coordinator':
        require(item['Image'] == IMAGES[role] and not host_config['CapAdd'])
    expected = {'/stand': (str(source), False)}
    if role == 'coordinator':
        expected.update({'/gates/' + target: (str(directory / target), True) for target in USERS})
    else:
        expected[DESTINATION] = (str(directory / role / 'gate'), True)
    observed = {}
    for mount in item['Mounts']:
        if mount['Type'] == 'tmpfs':
            require(mount['Destination'] == '/sandbox')
            continue
        require(mount['Type'] == 'bind' and mount['Propagation'] == 'rprivate' and
                mount['Destination'] not in observed)
        observed[mount['Destination']] = (mount['Source'], mount['RW'])
    require(observed == expected)
    return dict(id=item['Id'], image=item['Image'], pid=item['State']['Pid'],
                user_namespace_mode=host_config['UsernsMode'],
                mounts_sha256=digest(json.dumps(observed, sort_keys=True).encode()))


def host(directory):
    require(directory.is_absolute() and not directory.exists() and directory.parent.is_dir())
    require(not any(path.is_symlink() for path in (directory, *directory.parents)))
    directory.mkdir(mode=0o700)
    source = directory / 'source'
    source.mkdir(mode=0o755)
    source.chmod(0o755)
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    from scripts.package_capture_guardians import build
    from scripts import control_ha_owner_admission_preflight as preflight
    before = preflight.collect()
    source_sha = build(source / 'guardians.pyz')
    (source / 'guardians.pyz').chmod(0o644)
    (source / 'cross_mount.py').write_bytes(Path(__file__).read_bytes())
    (source / 'cross_mount.py').chmod(0o644)
    for role in USERS:
        (directory / role).mkdir(mode=0o700)
    label = 'fc-owner-cross-mount-' + os.urandom(8).hex()
    names, processes = [], []
    receipts = {'source_sha256': source_sha, 'started_ns': time.time_ns(), 'images': IMAGES,
                'production_changed': False, 'capture_permitted': False, 'independent_approval': False}
    (directory / 'installed-before.json').write_text(json.dumps(before, sort_keys=True) + '\n')
    with ExitStack() as stack:
        def start(role, command):
            name = label + '-' + str(len(names))
            names.append(name)
            args = ['docker', '--host', 'unix:///var/run/docker.sock', 'run', '--rm', '-i', '--pull=never',
                '--name', name, '--label', 'family-connect.cross-mount=' + label, '--network=none',
                '--read-only', '--cap-drop=ALL', '--security-opt=no-new-privileges', '--memory=192m',
                '--cpus=1', '--pids-limit=48', '--tmpfs', '/sandbox:rw,nosuid,nodev,size=16m,mode=0700',
                '--mount', 'type=bind,src=' + str(source) + ',dst=/stand,readonly']
            if role == 'coordinator':
                args += ['--user=0:0', '--cap-add=CHOWN', '--cap-add=SETUID', '--cap-add=SETGID', '--cap-add=KILL']
                for target in USERS:
                    args += ['--mount', 'type=bind,src=' + str(directory / target) + ',dst=/gates/' + target]
                image = RUNTIME
            else:
                uid = USERS[role]
                args += ['--user=' + str(uid) + ':' + str(uid), '--mount', 'type=bind,src=' +
                    str(directory / role / 'gate') + ',dst=' + DESTINATION]
                image = IMAGES[role]
            args += ['--entrypoint=python', image, '-I', '-S', '-B', '/stand/cross_mount.py', command]
            stderr = stack.enter_context((directory / (name + '.stderr')).open('xb'))
            process = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr,
                env={key: value for key, value in os.environ.items() if not key.startswith('DOCKER_')})
            processes.append(process)
            return process

        try:
            initializer = start('coordinator', 'initialize')
            receipts['initialized'] = receive(initializer)
            require(initializer.wait(timeout=8) == 0)
            controller = start('coordinator', 'coordinator')
            guardians = receive(controller)
            writers = {role: start(role, 'writer') for role in USERS}
            receipts['writers'] = {role: receive(process) for role, process in writers.items()}
            receipts['guardians'] = guardians
            receipts['containers'] = {}
            for role, name in zip(('coordinator', *USERS), names[1:]):
                result = docker('inspect', name)
                require(result.returncode == 0)
                receipts['containers'][role] = container_binding(json.loads(result.stdout)[0], role, label, source, directory)
            (directory / 'observations.json').write_text(json.dumps(receipts, sort_keys=True, indent=2) + '\n')
            for role, uid in USERS.items():
                match(receipts['writers'][role], guardians[role], uid)
            require(receipts['writers']['console']['namespaces']['mnt'] !=
                    receipts['writers']['system_publisher']['namespaces']['mnt'])
            active = writers['console']
            send(active, 'hold')
            require(receive(active) == {'status': 'ACTIVE'})
            send(controller, 'begin')
            require(receive(controller) == {'status': 'DRAINING'})
            require(not select.select([controller.stdout], [], [], 0.2)[0])
            send(active, 'finish')
            require(receive(active) == {'status': 'WRITE'})
            require(receive(controller) == {'status': 'HELD'})
            for process in writers.values():
                send(process, 'write')
                require(receive(process) == {'status': 'BUSY'})
            send(controller, 'release')
            receipts['interval'] = receive(controller)
            require(receipts['interval']['status'] == 'LOCAL_INTERVAL_CONFIRMED' and
                    receipts['interval']['capture_permitted'] is False)
            for process in writers.values():
                send(process, 'write')
                require(receive(process) == {'status': 'WRITE'})
            send(active, 'crash')
            require(active.wait(timeout=8) == 23)
            replacement = start('console', 'writer')
            retained = receive(replacement)
            require(retained['pins'] == receipts['writers']['console']['pins'] and retained['pending'] == 1)
            send(replacement, 'write')
            require(receive(replacement) == {'status': 'WRITE'})
            send(controller, 'begin')
            require(receive(controller) == {'status': 'DRAINING'})
            require(receive(controller) == {'status': 'REFUSED'})
            receipts['restart_pending_retained'] = True
            for process in (replacement, writers['system_publisher'], controller):
                send(process, 'exit')
                require(process.wait(timeout=8) == 0)
        finally:
            for name in names:
                result = docker('inspect', '--format', '{{index .Config.Labels "family-connect.cross-mount"}}', name)
                if result.returncode == 0:
                    require(result.stdout.decode().strip() == label)
                    require(docker('rm', '-f', name).returncode == 0)
            for process in processes:
                process.wait(timeout=8)
            result = docker('ps', '-aq', '--filter', 'label=family-connect.cross-mount=' + label)
            require(result.returncode == 0 and not result.stdout.strip())
    after = preflight.collect()
    (directory / 'installed-after.json').write_text(json.dumps(after, sort_keys=True) + '\n')
    require([item['binding'] for item in before['containers']] ==
            [item['binding'] for item in after['containers']])
    require([item['processes']['host_uid_gid'] for item in before['containers']] ==
            [item['processes']['host_uid_gid'] for item in after['containers']] == [[(10001, 10001)], [(1000, 1000)]])
    receipts['installed_before_sha256'] = before['observation_sha256']
    receipts['installed_after_sha256'] = after['observation_sha256']
    receipts['installed_bindings_unchanged'] = True
    receipts['finished_ns'] = time.time_ns()
    receipts['owned_containers_removed'] = True
    (directory / 'receipt.json').write_text(json.dumps(receipts, sort_keys=True, indent=2) + '\n')
    emit({'status': 'ISOLATED_CROSS_MOUNT_PASS', 'receipt_sha256': digest((directory / 'receipt.json').read_bytes()),
          'capture_permitted': False, 'production_changed': False})


if __name__ == '__main__':
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    os.umask(0o077)
    if sys.argv[1] == 'host':
        host(Path(sys.argv[2]))
    else:
        require(Path('/.dockerenv').exists())
        signal.alarm(90)
        if sys.argv[1] == 'writer':
            writer()
        elif sys.argv[1] in ('actor', 'initialize-actor'):
            actor(sys.argv[2], sys.argv[1] == 'initialize-actor')
        else:
            require(sys.argv[1] in ('coordinator', 'initialize'))
            coordinator(sys.argv[1] == 'initialize')
