"""Stock Engine pre-hook handlers, delayed inside a disposable volume driver, not a proxy."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import socketserver
import subprocess
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler

from docker_authz_checks import API
from run_docker_authz import DOCKER_SHA, IMAGE, IMAGE_SHA, wait


class VolumeHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get('Content-Length', '0'))) or b'{}')
        root = self.server.root
        name = body.get('Name', '')
        phase = self.path.rsplit('.', 1)[-1]
        result = {}
        if self.path == '/Plugin.Activate':
            result = dict(Implements=['VolumeDriver'])
        elif phase == 'Capabilities':
            result = dict(Capabilities=dict(Scope='local'))
        elif phase == 'Get':
            result = dict(Err='not found') if name not in self.server.created else dict(Volume=dict(Name=name, Mountpoint=str(root / 'volume')))
        elif phase in ('Create', 'Mount'):
            selected = (phase == 'Create' and name == 'late-create' or phase == 'Mount' and name == 'late-start')
            if selected:
                (root / (phase + '-entered')).write_text('accepted inside Engine volume callback')
                deadline = time.monotonic() + 30
                while not (root / (phase + '-release')).exists():
                    if time.monotonic() >= deadline:
                        result = dict(Err='LAB_DELAY_DEADLINE')
                        break
                    time.sleep(.01)
            if not result:
                self.server.created.add(name)
                if phase == 'Mount':
                    result = dict(Mountpoint=str(root / 'volume'))
        elif phase == 'Path':
            result = dict(Mountpoint=str(root / 'volume'))
        elif phase not in ('Remove', 'Unmount', 'List'):
            result = dict(Err='unsupported laboratory request')
        raw = json.dumps(result).encode()
        self.send_response(200)
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers()
        try:
            self.wfile.write(raw)
        except BrokenPipeError:
            pass


class VolumeServer(socketserver.ThreadingUnixStreamServer):
    daemon_threads = True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--dockerd', default='/usr/bin/dockerd')
    parser.add_argument('--containerd', default='/usr/bin/containerd')
    parser.add_argument('--retire-control-processes', action='store_true')
    args = parser.parse_args()
    root = args.root.absolute()
    assert os.geteuid() == 0 and root.name.startswith('fc-owner-executor-') and not root.exists()
    assert hashlib.sha256(Path(args.dockerd).read_bytes()).hexdigest() == DOCKER_SHA
    os.umask(0o077)
    root.mkdir(mode=0o700)
    for name in ('protected', 'volume', 'engine-data'):
        (root / name).mkdir()
    runtime = Path('/run') / ('fc-prehook-' + uuid.uuid4().hex)
    runtime.mkdir(mode=0o700)
    config = root / 'daemon.json'
    config.write_text('{}')
    volume_name = 'fc-delay-' + uuid.uuid4().hex
    auth_name = 'fc-admit-' + uuid.uuid4().hex
    paths = [Path('/run/docker/plugins') / (name + '.sock') for name in (volume_name, auth_name)]
    paths[0].parent.mkdir(exist_ok=True)
    server = VolumeServer(str(paths[0]), VolumeHandler)
    server.root, server.created = root, set()
    threading.Thread(target=server.serve_forever, daemon=True).start()
    processes, handles, requests = [], [], []
    result = dict(engine_sha256=DOCKER_SHA, production_modified=False, initial_admission_coverage_proven=False)
    sources = ['tests/fixtures/docker_prehook_transition.py', 'tests/fixtures/docker_authz_checks.py',
               'tests/fixtures/run_docker_authz.py', 'control/capture_docker.py', 'control/capture_native.py']
    result['source'] = dict(head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
        files={name: hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in sources})

    def spawn(command, name):
        output = (root / (name + '.log')).open('wb')
        handles.append(output)
        process = subprocess.Popen(command, stdout=output, stderr=subprocess.STDOUT,
            env={**os.environ, 'PYTHONPATH': str(Path.cwd()), 'PYTHONDONTWRITEBYTECODE': '1'})
        processes.append(process)
        return process

    engine = API(runtime / 'docker.sock')
    own = ['docker', '--host=unix://' + str(runtime / 'docker.sock')]
    daemon = None
    try:
        (root / 'containerd.toml').write_text('version = 3\nroot = ' + json.dumps(str(root / 'ctr-root')) +
            '\nstate = ' + json.dumps(str(runtime / 'ctr-state')) +
            '\ndisabled_plugins = ["io.containerd.cri.v1.images", "io.containerd.cri.v1.runtime"]\n[grpc]\naddress = ' +
            json.dumps(str(runtime / 'containerd.sock')) + '\n')
        containerd_command = [args.containerd, '--config', str(root / 'containerd.toml')]
        containerd = spawn(containerd_command, 'containerd')
        wait(lambda: (runtime / 'containerd.sock').exists())
        daemon_command = [args.dockerd, '--host=unix://' + str(runtime / 'docker.sock'),
            '--containerd=' + str(runtime / 'containerd.sock'), '--containerd-namespace=fc-prehook-lab',
            '--containerd-plugins-namespace=fc-prehook-lab-plugins', '--data-root=' + str(root / 'engine-data'),
            '--exec-root=' + str(runtime / 'exec'), '--pidfile=' + str(runtime / 'docker.pid'),
            '--config-file=' + str(config), '--storage-driver=vfs', '--bridge=none', '--iptables=false',
            '--ip6tables=false', '--ip-masq=false', '--ip-forward=false']
        daemon = spawn(daemon_command, 'daemon')
        wait(lambda: engine.json('GET', '/version')['Version'] == '29.1.3')
        assert engine.json('GET', '/info')['DockerRootDir'] == str(root / 'engine-data')
        installed = json.loads(subprocess.check_output(['docker', 'image', 'inspect', IMAGE], timeout=10))[0]
        assert any(digest.endswith('@' + IMAGE_SHA) for digest in installed['RepoDigests'])
        subprocess.run(['docker', 'save', '-o', str(root / 'image.tar'), IMAGE], check=True, timeout=90)
        subprocess.run([*own, 'load', '-i', str(root / 'image.tar')], check=True, timeout=90, stdout=subprocess.DEVNULL)
        (root / 'image.tar').unlink()

        def spec(name):
            return dict(Image=IMAGE, Cmd=['sh', '-c', 'echo effect >> /data/started; exec sleep infinity'],
                HostConfig=dict(NetworkMode='none', RestartPolicy=dict(Name='unless-stopped'),
                    Binds=[str(root / 'protected') + ':/data'],
                    Mounts=[dict(Type='volume', Source=name, Target='/delay',
                        VolumeOptions=dict(DriverConfig=dict(Name=volume_name)))]))

        old = engine.json('POST', '/containers/create?name=old-start', spec('late-start'), 201)['Id']
        old_value = engine.json('GET', '/containers/' + old + '/json')
        assert not old_value['HostConfig']['CgroupParent']
        assert old_value['HostConfig']['RestartPolicy']['Name'] == 'unless-stopped'
        result['old_container'] = old

        if args.retire_control_processes:
            writer = engine.json('POST', '/containers/create?name=prior-writer', dict(Image=IMAGE,
                Cmd=['sleep', 'infinity'], HostConfig=dict(NetworkMode='none',
                    RestartPolicy=dict(Name='unless-stopped'), Binds=[str(root / 'protected') + ':/data'])), 201)['Id']
            engine.call('POST', '/containers/' + writer + '/start')
            program = '''import os,time,mmap
if os.fork(): os._exit(0)
os.setsid()
descriptor=os.open('/data/old-fd',os.O_CREAT|os.O_WRONLY|os.O_APPEND,0o600)
mapped=os.open('/data/old-mmap',os.O_CREAT|os.O_RDWR,0o600)
os.ftruncate(mapped,4096)
memory=mmap.mmap(mapped,4096)
while True:
 os.write(descriptor,b'x');memory[0:8]=str(time.monotonic_ns()).encode()[-8:];memory.flush()
 with open('/data/temporary','w') as target: target.write(str(time.monotonic_ns()))
 os.replace('/data/temporary','/data/renamed')
 time.sleep(.02)
'''
            execution = engine.json('POST', '/containers/' + writer + '/exec',
                dict(Cmd=['python', '-c', program], AttachStdout=False, AttachStderr=False), 201)['Id']
            engine.call('POST', '/exec/' + execution + '/start', dict(Detach=True))
            wait(lambda: (root / 'protected/old-fd').exists())
            result['writer'] = writer

        def request(label, route, value=None):
            try:
                status, raw = engine.call('POST', route, value)
                requests.append(dict(label=label, status=status, response=json.loads(raw) if raw else None))
            except Exception as error:
                requests.append(dict(label=label, failure=type(error).__name__))

        threads = [threading.Thread(target=request, args=('create', '/containers/create?name=pre-hook-create', spec('late-create'))),
                   threading.Thread(target=request, args=('start', '/containers/' + old + '/start'))]
        for thread in threads:
            thread.start()
        wait(lambda: (root / 'Create-entered').exists() and (root / 'Mount-entered').exists())
        assert not (root / 'protected/started').exists()
        if args.retire_control_processes:
            started = time.monotonic()
            try:
                for process in (daemon, containerd):
                    process.kill()
                    process.wait(5)
                result['control_process_retirement_seconds'] = time.monotonic() - started
                before = {name: (root / 'protected' / name).read_bytes() for name in ('old-fd', 'old-mmap', 'renamed')}
                for phase in ('Create', 'Mount'):
                    (root / (phase + '-release')).touch()
                for thread in threads:
                    thread.join(12)
                    assert not thread.is_alive()
                wait(lambda: all((root / 'protected' / name).read_bytes() != raw for name, raw in before.items()))
                result.update(old_fd_mmap_rename_after_daemons_exited=True, requests=requests,
                    conclusion='CONTROL_PROCESS_RETIREMENT_NOT_RUNTIME_FENCE', maintenance_window_qualified=False)
                (root / 'result.json').write_text(json.dumps(result))
            finally:
                recovery_started = time.monotonic()
                containerd = spawn(containerd_command, 'containerd-recovery')
                daemon = spawn(daemon_command, 'daemon-recovery')
                wait(lambda: engine.json('GET', '/version')['Version'] == '29.1.3')
                result['lab_api_recovery_seconds'] = time.monotonic() - recovery_started
                (root / 'result.json').write_text(json.dumps(result))
            return
        spawn([sys.executable, '-m', 'control.capture_docker', '--socket', str(paths[1]),
            '--engine', str(runtime / 'docker.sock'), '--pidfile', str(runtime / 'docker.pid'),
            '--daemon-config', str(config), '--journal', str(root / 'authz'), '--protect', str(root / 'protected')], 'authz')
        plugin = API(paths[1])
        wait(lambda: plugin.json('POST', '/Plugin.Activate', {})['Implements'] == ['authz'])
        config.write_text(json.dumps({'authorization-plugins': [auth_name]}))
        daemon.send_signal(signal.SIGHUP)
        wait(lambda: any('Reloaded configuration' in line
                         for line in (root / 'daemon.log').read_text().splitlines()))
        plugin.json('POST', '/fc-control', dict(command='CLOSE'))
        status, _ = engine.call('POST', '/containers/create?name=post-hook-refused',
            dict(Image=IMAGE, HostConfig=dict(Binds=[str(root / 'protected') + ':/data'])))
        assert status == 403
        result['post_hook_direct_denied'] = True
        for phase in ('Create', 'Mount'):
            (root / (phase + '-release')).touch()
        for thread in threads:
            thread.join(12)
            assert not thread.is_alive()
        wait(lambda: (root / 'protected/started').exists())
        late = engine.json('GET', '/containers/pre-hook-create/json')
        running = engine.json('GET', '/containers/' + old + '/json')
        assert not late['HostConfig']['CgroupParent'] and running['State']['Running']
        result.update(pre_hook_create_after_close=True, pre_hook_start_effect_after_close=True,
            runtime_pid=running['State']['Pid'], requests=requests,
            conclusion='ONLINE_HOOK_ATTACHMENT_NOT_INITIAL_COVERAGE', maintenance_window_qualified=False)
        (root / 'result.json').write_text(json.dumps(result))
    finally:
        for phase in ('Create', 'Mount'):
            (root / (phase + '-release')).touch()
        if daemon is not None and daemon.poll() is None:
            config.write_text('{}')
            daemon.send_signal(signal.SIGHUP)
            wait(lambda: engine.json('GET', '/version')['Version'] == '29.1.3')
            identifiers = subprocess.check_output([*own, 'ps', '-aq'], timeout=10).decode().split()
            if identifiers:
                subprocess.run([*own, 'stop', '-t', '5', *identifiers], check=True, timeout=20, stdout=subprocess.DEVNULL)
                subprocess.run([*own, 'rm', *identifiers], check=True, timeout=15, stdout=subprocess.DEVNULL)
            assert not subprocess.check_output([*own, 'ps', '-q'], timeout=10).strip()
        for process in reversed(processes):
            if process.poll() is None:
                process.terminate()
                process.wait(15)
        server.shutdown()
        server.server_close()
        for path in paths:
            path.unlink(missing_ok=True)
        for output in handles:
            output.close()
        (root / 'cleanup.json').write_text(json.dumps(dict(own_processes_exited=all(p.poll() is not None for p in processes),
            production_modified=False, capture_lease_adopted=False)))


if __name__ == '__main__':
    main()
