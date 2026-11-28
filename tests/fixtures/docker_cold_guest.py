"""Disposable QEMU guest only: retain old runtime, boot a pinned fresh Engine under AuthZ."""
import argparse
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import threading
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from control.docker_cold import Transition, boot, digest, publish
from control.capture_native import require
from docker_authz_checks import API
from docker_prehook_transition import VolumeHandler, VolumeServer
from run_docker_authz import DOCKER_SHA, IMAGE, wait

ROOT = Path('/var/lib/fc-cold-vm')
SOURCE = Path(__file__).resolve().parents[2]
ENGINE = '/usr/bin/dockerd'
PARENT = 'fccold.slice'


def command(*arguments, seconds=30):
    return subprocess.run(arguments, check=True, capture_output=True, text=True, timeout=seconds).stdout


def safe():
    require(os.geteuid() == 0 and Path('/etc/fc-disposable-vm').read_text() == 'fc-cold-vm-20261128', 'LAB_GUEST_ONLY')
    require(command('systemd-detect-virt').strip() in ('kvm', 'qemu'), 'LAB_VM_ONLY')
    require(digest(ENGINE) == DOCKER_SHA, 'LAB_ENGINE_PIN')


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    path.chmod(0o600)
    with path.open('rb') as stream:
        os.fsync(stream.fileno())


def unit(name, content):
    write(Path('/etc/systemd/system') / name, content)
    command('systemctl', 'daemon-reload')


def legacy():
    require(not ROOT.exists(), 'LAB_PRESTATE_EXISTS')
    ROOT.mkdir(mode=0o700)
    for name in ('protected', 'volume', 'old-data', 'evidence'):
        (ROOT / name).mkdir(mode=0o700)
    config = ROOT / 'old.json'
    write(config, json.dumps(dict(hosts=['unix:///run/fc-old.sock'], **{'data-root': str(ROOT / 'old-data'),
        'exec-root': '/run/fc-old', 'pidfile': '/run/fc-old.pid', 'bridge': 'none', 'iptables': False,
        'ip6tables': False, 'userland-proxy': False, 'storage-driver': 'overlayfs',
        'features': {'containerd-snapshotter': True}, 'live-restore': False,
        'exec-opts': ['native.cgroupdriver=systemd']})))
    unit('fc-cold-old.service', '[Unit]\nDescription=Disposable old Engine\n[Service]\nType=simple\n'
         f'ExecStart={ENGINE} --config-file {config}\nDelegate=yes\nKillMode=control-group\n'
         'TimeoutStopSec=12\n[Install]\nWantedBy=multi-user.target\n')
    command('systemctl', 'enable', '--now', 'fc-cold-old.service')
    engine = API('/run/fc-old.sock')
    wait(lambda: engine.json('GET', '/version')['Version'] == '29.1.3')
    command('docker', '--host=unix:///run/fc-old.sock', 'load', '-i', '/opt/fc-images.tar', seconds=120)
    base = dict(Image=IMAGE, Cmd=['sleep', 'infinity'], HostConfig=dict(NetworkMode='none',
        Binds=[str(ROOT / 'protected') + ':/data'], RestartPolicy=dict(Name='unless-stopped')))
    writer = engine.json('POST', '/containers/create?name=old-protected', base, 201)['Id']
    engine.json('POST', '/containers/' + writer + '/start', expected=204)
    program = '''import os,time,mmap
if os.fork(): os._exit(0)
os.setsid()
descriptor=os.open('/data/old-fd',os.O_CREAT|os.O_WRONLY|os.O_APPEND,0o600)
mapped=os.open('/data/old-mmap',os.O_CREAT|os.O_RDWR,0o600)
os.ftruncate(mapped,4096)
memory=mmap.mmap(mapped,4096)
while True:
 os.write(descriptor,b'x');os.fsync(descriptor)
 memory[0:8]=str(time.monotonic_ns()).encode()[-8:];memory.flush()
 with open('/data/temporary','w') as target: target.write(str(time.monotonic_ns()));target.flush();os.fsync(target.fileno())
 os.replace('/data/temporary','/data/renamed')
 time.sleep(.03)
'''
    execution = engine.json('POST', '/containers/' + writer + '/exec', dict(Cmd=['python', '-c', program]), 201)['Id']
    engine.json('POST', '/exec/' + execution + '/start', dict(Detach=True))
    wait(lambda: (ROOT / 'protected/renamed').exists())
    publish(ROOT / 'evidence/legacy.json', dict(boot=boot(), writer=writer, execution=execution,
            image=engine.json('GET', '/containers/' + writer + '/json')['Image'], old_parent='', restart='unless-stopped'))


def arm():
    operation = secrets.token_hex(16)
    root = ROOT / ('operation-' + operation)
    root.mkdir(mode=0o700)
    publish(root / 'prepare-intent.json', dict(operation=operation, boot=boot(), capture_lease=None))
    interlocks = []
    for name in ('docker.service', 'docker.socket', 'containerd.service', 'fc-cold-old.service'):
        directory = Path('/etc/systemd/system') / (name + '.d')
        path = directory / '00-fc-cold-interlock.conf'
        write(path, '[Unit]\nConditionPathExists=/run/fc-never-legacy-authorized\n')
        interlocks.append(path)
    command('systemctl', 'daemon-reload')
    os.sync()
    config = root / 'daemon.json'
    plugin = 'fc-cold-' + operation
    write(config, json.dumps(dict(hosts=['unix:///run/fc-new.sock'], **{'data-root': str(root / 'data'),
        'exec-root': '/run/fc-new', 'pidfile': '/run/fc-new.pid', 'bridge': 'none', 'iptables': False,
        'ip6tables': False, 'userland-proxy': False, 'storage-driver': 'overlayfs',
        'features': {'containerd-snapshotter': True}, 'live-restore': False,
        'exec-opts': ['native.cgroupdriver=systemd'], 'authorization-plugins': [plugin]})))
    sources = ['control/docker_cold.py', 'control/docker_cold_plugin.py', 'control/capture_docker.py',
               'control/capture_docker_domain.py', 'control/capture_domain.py', 'control/capture_native.py']
    plan = dict(schema=1, operation=operation, old_boot=boot(), old_root=str(ROOT / 'old-data'),
        new_root=str(root / 'data'), engine=ENGINE, engine_sha256=DOCKER_SHA, configuration=str(config),
        configuration_sha256=digest(config), plugin=plugin, parent=PARENT, socket='/run/fc-new.sock',
        plugin_socket='/run/docker/plugins/' + plugin + '.sock', pidfile='/run/fc-new.pid',
        protected=[str(ROOT / 'protected')], sources={str(SOURCE / name): digest(SOURCE / name) for name in sources})
    base = '[Service]\nType=simple\nWorkingDirectory=' + str(SOURCE) + '\nEnvironment=PYTHONDONTWRITEBYTECODE=1\n'
    unit(PARENT, '[Unit]\nDescription=Disposable FC mandatory domain\n[Slice]\n')
    unit('fc-cold-policy.service', '[Unit]\nDescription=Disposable cold mandatory policy\nBefore=fc-cold-runtime.service\n' + base +
         'ExecStartPre=/usr/bin/mkdir -p /run/docker/plugins\n' +
         f'ExecStart=/usr/bin/python3 -m control.docker_cold_plugin --root {root}\nRestart=no\n')
    unit('fc-cold-runtime.service', '[Unit]\nDescription=Disposable cold pinned runtime\nRequires=fc-cold-policy.service\n'
         'After=fc-cold-policy.service\n' + base +
         f'ExecStartPre=/usr/bin/mkdir -p /sys/fs/cgroup/{PARENT}\n' +
         f'ExecStart=/usr/bin/python3 -m control.docker_cold --root {root} --exec-engine\n'
         'Delegate=yes\nKillMode=control-group\nTimeoutStopSec=12\nRestart=no\n[Install]\nWantedBy=multi-user.target\n')
    command('systemctl', 'enable', 'fc-cold-runtime.service')
    for path in interlocks + [Path('/etc/systemd/system') / name for name in (PARENT, 'fc-cold-policy.service', 'fc-cold-runtime.service')]:
        plan['sources'][str(path)] = digest(path)
    publish(root / 'plan.json', plan)
    publish(ROOT / 'current.json', dict(root=str(root)))
    require(command('systemctl', 'is-active', 'fc-cold-old.service').strip() == 'active', 'LAB_OLD_WRITER_MISSING')
    try:
        Transition(root).guard()
    except ValueError as error:
        require(str(error) == 'COLD_NEW_KERNEL_REQUIRED', 'LAB_INTERLOCK_WRONG_REFUSAL')
    else:
        raise AssertionError('LAB_OLD_KERNEL_ADMITTED')
    publish(root / 'armed.json', dict(boot=boot(), old_runtime_still_running=True, initial_coverage=False))
    os.sync()
    return root


def attack():
    path = Path('/run/docker/plugins/fc-cold-delay.sock')
    path.parent.mkdir(exist_ok=True, parents=True)
    server = VolumeServer(str(path), VolumeHandler)
    server.root, server.created = ROOT, set()
    threading.Thread(target=server.serve_forever, daemon=True).start()
    engine = API('/run/fc-old.sock')
    def spec(name):
        return dict(Image=IMAGE, Cmd=['sh', '-c', 'echo late >> /data/late-write'], HostConfig=dict(NetworkMode='none',
            Binds=[str(ROOT / 'protected') + ':/data'], RestartPolicy=dict(Name='unless-stopped'),
            Mounts=[dict(Type='volume', Source=name, Target='/delay', VolumeOptions=dict(DriverConfig=dict(Name='fc-cold-delay')))]))
    old = engine.json('POST', '/containers/create?name=pre-hook-start', spec('late-start'), 201)['Id']
    def request(route, value):
        try:
            engine.call('POST', route, value)
        except Exception:
            pass
    threading.Thread(target=request, args=('/containers/create?name=pre-hook-unknown', spec('late-create')), daemon=True).start()
    threading.Thread(target=request, args=('/containers/' + old + '/start', None), daemon=True).start()
    wait(lambda: (ROOT / 'Create-entered').exists() and (ROOT / 'Mount-entered').exists())
    publish(ROOT / 'evidence/attack.json', dict(boot=boot(), old_start=old, unknown_create_response=False,
            effect_before_boot=(ROOT / 'protected/late-write').exists()))
    os.sync()
    time.sleep(120)


def recover():
    root = Path(json.loads((ROOT / 'current.json').read_bytes())['root'])
    started = time.monotonic()
    engine = API('/run/fc-new.sock')
    with Transition(root) as transition:
        transition.guard()
        wait(lambda: engine.json('GET', '/version')['Version'] == '29.1.3', 30)
        require(engine.json('GET', '/info')['DockerRootDir'] == transition.plan['new_root'], 'LAB_OLD_ROOT_OPENED')
        require(not Path('/run/fc-old.sock').exists(), 'LAB_OLD_ENGINE_RESTARTED')
        before = {name: digest(ROOT / 'protected' / name) for name in ('old-fd', 'old-mmap', 'renamed')}
        time.sleep(1)
        require(before == {name: digest(ROOT / 'protected' / name) for name in before}, 'LAB_OLD_WRITER_SURVIVED')
        require(not (ROOT / 'protected/late-write').exists(), 'LAB_PREHOOK_EFFECT_AFTER_BOOT')
        command('docker', '--host=unix:///run/fc-new.sock', 'load', '-i', '/opt/fc-images.tar', seconds=120)
        spec = dict(Image=IMAGE, Cmd=['sleep', 'infinity'], HostConfig=dict(NetworkMode='none',
            Binds=[str(ROOT / 'protected') + ':/data'], CgroupParent=PARENT, RestartPolicy=dict(Name='no')))
        require(engine.call('POST', '/containers/create?name=outside', {**spec, 'HostConfig': {
            **spec['HostConfig'], 'CgroupParent': '', 'RestartPolicy': dict(Name='unless-stopped')}})[0] == 403, 'LAB_BYPASS')
        def observe():
            status, raw = engine.call('GET', '/containers/enrolled/json')
            if status == 404:
                return None
            require(status == 200, 'LAB_CONTAINER_READBACK')
            value = json.loads(raw)
            require(value['HostConfig']['CgroupParent'] == PARENT and
                    value['HostConfig']['RestartPolicy']['Name'] == 'no', 'LAB_ENROLLMENT_CHANGED')
            return dict(id=value['Id'], image=value['Image'], parent=PARENT, restart='no')
        created = transition.step('create', observe,
            lambda: engine.json('POST', '/containers/create?name=enrolled', spec, 201))
        container = created['observed']['id']
        def running():
            value = engine.json('GET', '/containers/' + container + '/json')
            if not value['State']['Running']:
                return None
            require(Path('/proc/' + str(value['State']['Pid']) + '/cgroup').read_text().strip().startswith('0::/' + PARENT + '/'), 'LAB_PHYSICAL_PARENT')
            return dict(id=container, boot=boot(), parent=PARENT)
        transition.step('start', running, lambda: engine.json('POST', '/containers/' + container + '/start', expected=204))
        receipt = dict(operation=transition.plan['operation'], boot=boot(), old_boot=transition.plan['old_boot'],
            old_bytes=before, initial_runtime_coverage=True, application_recovery=False, capture_lease=None,
            recovery_seconds=time.monotonic() - started)
        output = root / 'runtime-observations'
        output.mkdir(exist_ok=True)
        publish(output / (secrets.token_hex(16) + '.json'), receipt)
        print(json.dumps(receipt))


if __name__ == '__main__':
    safe()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['legacy', 'arm', 'attack', 'recover'])
    options = parser.parse_args()
    globals()[options.action]()
