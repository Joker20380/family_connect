"""Start an explicitly separate containerd and exact Docker Engine for native AuthZ evidence."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import threading
import time
import traceback
import uuid

from docker_authz_checks import API

DOCKER_SHA = '8f1c19d27e182ce6c82ddfd900d596195b0fd9d6740a9ff1ccac584e04355cb0'
IMAGE = 'python:3.12-slim-bookworm'
IMAGE_SHA = 'sha256:935c3c5b12357a7e10caa9c1e6ca5692344d97cf229832ef584be2cec9fc03df'


def wait(test, seconds=15):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            value = test()
            if value:
                return value
        except (OSError, AssertionError, ValueError):
            pass
        time.sleep(.05)
    raise AssertionError('LAB_WAIT_DEADLINE')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--dockerd', default='/usr/bin/dockerd')
    parser.add_argument('--containerd', default='/usr/bin/containerd')
    args = parser.parse_args()
    root = args.root.absolute()
    assert os.geteuid() == 0 and root.name.startswith('fc-owner-executor-') and not root.exists()
    assert hashlib.sha256(Path(args.dockerd).read_bytes()).hexdigest() == DOCKER_SHA
    os.umask(0o077)
    root.mkdir(mode=0o700)
    for name in ('protected', 'neighbor', 'engine2-data'):
        (root / name).mkdir()
    runtime = Path('/run') / ('fc-authz-' + uuid.uuid4().hex)
    runtime.mkdir(mode=0o700)
    config = root / 'daemon.json'
    def configuration(plugins):
        config.write_text(json.dumps({'authorization-plugins': plugins}))
        config.chmod(0o600)
    configuration([])
    (root / 'containerd.toml').write_text('version = 3\nroot = ' + json.dumps(str(root / 'containerd-root')) +
        '\nstate = ' + json.dumps(str(runtime / 'containerd-state')) +
        '\ndisabled_plugins = ["io.containerd.cri.v1.images", "io.containerd.cri.v1.runtime"]\n[grpc]\naddress = ' +
        json.dumps(str(runtime / 'containerd.sock')) + '\n')
    handles, processes, plugins = [], [], []
    results = dict(engine_binary_sha256=DOCKER_SHA, production_modified=False, owner_adapter_installed=False,
                   common_kit=False, runtime=str(runtime))
    sources = ['control/capture_docker.py', 'control/capture_docker_domain.py', 'control/capture_domain.py',
               'control/capture_native.py', 'tests/fixtures/run_docker_authz.py',
               'tests/fixtures/docker_domain_checks.py',
               'tests/fixtures/docker_authz_checks.py', 'tests/fixtures/docker_authz_server.py']
    results['source'] = dict(head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
        files={name: hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in sources})
    installed = json.loads(subprocess.check_output(['docker', 'image', 'inspect', IMAGE], timeout=10))
    assert len(installed) == 1 and any(digest.endswith('@' + IMAGE_SHA)
                                      for digest in installed[0].get('RepoDigests', []))
    results['fixture_image'] = dict(manifest=IMAGE_SHA, local_id=installed[0]['Id'])
    def spawn(command, name):
        output = (root / (name + '.log')).open('wb')
        handles.append(output)
        process = subprocess.Popen(command, stdout=output, stderr=subprocess.STDOUT,
            env={**os.environ, 'PYTHONPATH': str(Path.cwd()), 'PYTHONDONTWRITEBYTECODE': '1'})
        processes.append(process)
        return process
    engine = API(runtime / 'docker.sock')
    daemon = None
    parent = 'fc' + uuid.uuid4().hex + '.slice'
    unit = Path('/run/systemd/system') / parent
    try:
        containerd = spawn([args.containerd, '--config', str(root / 'containerd.toml')], 'containerd')
        wait(lambda: (runtime / 'containerd.sock').exists())
        daemon_args = [args.dockerd, '--host=unix://' + str(runtime / 'docker.sock'),
            '--containerd=' + str(runtime / 'containerd.sock'), '--containerd-namespace=fc-authz-lab',
            '--containerd-plugins-namespace=fc-authz-lab-plugins', '--data-root=' + str(root / 'engine2-data'),
            '--exec-root=' + str(runtime / 'exec'), '--pidfile=' + str(runtime / 'docker.pid'),
            '--config-file=' + str(config), '--storage-driver=vfs', '--bridge=none', '--iptables=false',
            '--ip6tables=false', '--ip-masq=false', '--ip-forward=false']
        daemon = spawn(daemon_args, 'daemon')
        wait(lambda: engine.json('GET', '/version')['Version'] == '29.1.3')
        assert engine.json('GET', '/info')['DockerRootDir'] == str(root / 'engine2-data')
        own = ['docker', '--host=unix://' + str(runtime / 'docker.sock')]
        image = root / 'image.tar'
        subprocess.run(['docker', 'image', 'save', '-o', str(image), IMAGE], check=True, timeout=90)
        subprocess.run([*own, 'load', '-i', str(image)], check=True, stdout=subprocess.DEVNULL, timeout=90)
        image.unlink()
        for name in ('protected', 'neighbor'):
            subprocess.run([*own, 'run', '-d', '--name', 'fc-authz-' + name, '--network=none',
                '-v', str(root / name) + ':/data', IMAGE, 'sleep', 'infinity'], check=True,
                stdout=subprocess.DEVNULL, timeout=20)
        def plugin(number):
            name = 'fc-authz-' + uuid.uuid4().hex
            path = Path('/run/docker/plugins') / (name + '.sock')
            path.parent.mkdir(exist_ok=True)
            journal = root / ('authz-' + str(number))
            process = spawn([sys.executable, 'tests/fixtures/docker_authz_server.py', '--socket', str(path),
                '--engine', str(runtime / 'docker.sock'), '--pidfile', str(runtime / 'docker.pid'),
                '--daemon-config', str(config), '--journal', str(journal), '--protect', str(root / 'protected')],
                'plugin-' + str(number))
            plugins.append(path)
            client = API(path)
            wait(lambda: client.json('POST', '/Plugin.Activate', {})['Implements'] == ['authz'])
            configuration([name])
            daemon.send_signal(signal.SIGHUP)
            wait(lambda: engine.json('GET', '/version')['Version'] == '29.1.3')
            assert daemon.poll() is None
            return process, client, journal, path
        first, client, journal, path = plugin(1)
        native_output = (root / 'native.log').open('wb')
        handles.append(native_output)
        subprocess.run([sys.executable, 'tests/fixtures/docker_authz_checks.py', '--engine', str(runtime / 'docker.sock'),
            '--plugin', str(path), '--root', str(root)], check=True, timeout=90,
            stdout=native_output)
        results['direct_api'] = json.loads((root / 'authz-native.json').read_bytes())
        released = client.json('POST', '/fc-control', dict(command='RELEASE'))
        assert client.json('POST', '/fc-control', dict(command='RELEASE')) == released
        subprocess.run([*own, 'rm', '-f', 'fc-authz-auto', 'fc-authz-paused', 'fc-authz-new-id'],
            check=True, stdout=subprocess.DEVNULL, timeout=20)
        second, client, journal, path = plugin(2)
        original = engine.json('POST', '/containers/fc-authz-protected/exec',
            dict(Cmd=['sh', '-c', 'echo late >/data/delayed-effect']), 201)['Id']
        response = []
        def delayed():
            response.append(engine.call('POST', '/exec/' + original + '/start', dict(Detach=True, Tty=False),
                                        headers={'X-Fc-Native-Delay': '1'}))
        thread = threading.Thread(target=delayed)
        thread.start()
        wait(lambda: (journal / 'delay-permitted').exists(), 5)
        closed = client.json('POST', '/fc-control', dict(command='CLOSE'))
        assert closed['pending'] == 1 and not (root / 'protected/delayed-effect').exists()
        (journal / 'delay-go').touch()
        thread.join(10)
        assert not thread.is_alive() and response[0][0] == 200
        wait(lambda: (root / 'protected/delayed-effect').exists())
        assert client.json('POST', '/fc-control', dict(command='CHECK'))['pending'] == 0
        results['preauthorized_delayed_effect'] = 'EXECUTED_AFTER_CLOSE_NOT_CONTAINED'
        channel = socket.socket(socket.AF_UNIX)
        channel.connect(str(path))
        body = b'{"command":"RELEASE"}'
        channel.sendall(b'POST /fc-control HTTP/1.0\r\nContent-Length: ' + str(len(body)).encode() +
                        b'\r\n\r\n' + body)
        channel.close()
        wait(lambda: (journal / 'released').exists())
        receipt = client.json('POST', '/fc-control', dict(command='RELEASE'))
        assert receipt['phase'] == 'RELEASED' and receipt['lease'] == closed['lease']
        assert client.json('POST', '/fc-control', dict(command='RELEASE')) == receipt
        results['release_response_loss'] = 'SAME_PROCESS_IDEMPOTENT_NO_EFFECT_REPLAY'
        third, client, journal, path = plugin(3)
        closed = client.json('POST', '/fc-control', dict(command='CLOSE'))
        neighbor = engine.json('GET', '/containers/fc-authz-neighbor/json')['State']['Pid']
        third.kill()
        third.wait(5)
        try:
            status, unused = engine.call('POST', '/containers/fc-authz-neighbor/exec', dict(Cmd=['true']))
            assert status >= 500
        except TimeoutError:
            pass
        assert Path(f'/proc/{neighbor}').exists() and daemon.poll() is None
        results['enforcement_death'] = 'NEIGHBOR_API_REFUSED_RUNNING_PROCESS_RETAINED'
        configuration([])
        daemon.send_signal(signal.SIGHUP)
        wait(lambda: engine.json('GET', '/version')['Version'] == '29.1.3')
        fourth, client, journal, path = plugin(4)
        client.json('POST', '/fc-control', dict(command='CLOSE'))
        before = config.read_bytes()
        configuration([])
        daemon.send_signal(signal.SIGHUP)
        wait(lambda: engine.json('POST', '/containers/fc-authz-neighbor/exec', dict(Cmd=['true']), 201))
        config.write_bytes(before)
        daemon.send_signal(signal.SIGHUP)
        status, unused = client.call('POST', '/fc-control', dict(command='CHECK'))
        assert status == 503
        assert json.loads((journal / 'failed').read_bytes())['reason'] == 'DOCKER_HOOK_CONFIGURATION_CHANGED'
        results['hook_remove_restore'] = 'OLD_LEASE_FAILED'
        results['valid_reload_same_daemon_pid'] = daemon.pid
        configuration([])
        daemon.send_signal(signal.SIGHUP)
        wait(lambda: engine.json('GET', '/version')['Version'] == '29.1.3')
        fifth, client, journal, path = plugin(5)
        client.json('POST', '/fc-control', dict(command='CLOSE'))
        old_pid = daemon.pid
        daemon.terminate()
        daemon.wait(35)
        daemon = spawn(daemon_args, 'daemon-new-generation')
        wait(lambda: engine.json('GET', '/version')['Version'] == '29.1.3')
        status, unused = client.call('POST', '/fc-control', dict(command='CHECK'))
        assert status == 503 and daemon.pid != old_pid
        assert json.loads((journal / 'failed').read_bytes())['reason'] == 'DOCKER_DAEMON_GENERATION_CHANGED'
        results['daemon_generation'] = 'OLD_LEASE_FAILED'
        configuration([])
        daemon.send_signal(signal.SIGHUP)
        wait(lambda: engine.json('GET', '/version')['Version'] == '29.1.3')
        for row in engine.json('GET', '/containers/json?all=1'):
            assert all(name.startswith('/fc-authz-') for name in row['Names'])
            engine.call('DELETE', '/containers/' + row['Id'] + '?force=1')
        unit.write_text('[Unit]\nDescription=Disposable FC Docker domain qualification\n[Slice]\n')
        subprocess.run(['systemctl', 'daemon-reload'], check=True, timeout=10)
        subprocess.run(['systemctl', 'start', parent], check=True, timeout=10)
        results['domain'] = {}
        for mode in ('normal', 'enforcer-hang', 'enforcer-death', 'controller-death'):
            name = 'fc-domain-' + uuid.uuid4().hex
            path = Path('/run/docker/plugins') / (name + '.sock')
            plugins.append(path)
            enforcer = spawn([sys.executable, '-m', 'control.capture_docker_domain', '--socket', str(path),
                '--engine', str(runtime / 'docker.sock'), '--pidfile', str(runtime / 'docker.pid'),
                '--daemon-config', str(config), '--journal', str(root / ('domain-plugin-' + mode)),
                '--protect', str(root / 'protected'), '--parent', parent], 'domain-plugin-' + mode)
            domain_client = API(path)
            wait(lambda: domain_client.json('POST', '/Plugin.Activate', {})['Implements'] == ['authz'])
            configuration([name])
            daemon.send_signal(signal.SIGHUP)
            time.sleep(.2)
            subprocess.run([sys.executable, 'tests/fixtures/docker_domain_checks.py', '--engine', str(runtime / 'docker.sock'),
                '--plugin', str(path), '--root', str(root), '--parent', parent, '--mode', mode,
                '--enforcer', str(enforcer.pid)], check=True, timeout=45,
                env={**os.environ, 'PYTHONPATH': str(Path.cwd()), 'PYTHONDONTWRITEBYTECODE': '1'})
            results['domain'][mode] = json.loads((root / ('domain-' + mode + '.json')).read_bytes())
            configuration([])
            daemon.send_signal(signal.SIGHUP)
            wait(lambda: engine.json('GET', '/version')['Version'] == '29.1.3')
        (root / 'qualification.json').write_text(json.dumps(results, sort_keys=True))
        print(json.dumps(results, sort_keys=True))
    finally:
        primary = sys.exception()
        cleanup_errors = []
        try:
            if daemon is not None and daemon.poll() is None:
                configuration([])
                daemon.send_signal(signal.SIGHUP)
                try:
                    wait(lambda: engine.json('GET', '/version')['Version'] == '29.1.3', 5)
                    rows = engine.json('GET', '/containers/json?all=1')
                    assert all(all(name.startswith('/fc-authz-') for name in row['Names']) for row in rows)
                    for row in rows:
                        engine.call('DELETE', '/containers/' + row['Id'] + '?force=1')
                finally:
                    daemon.terminate()
                    daemon.wait(35)
        except BaseException as error:
            traceback.print_exc()
            cleanup_errors.append(type(error).__name__)
        for process in reversed(processes):
            try:
                if process.poll() is None:
                    process.terminate()
                    process.wait(10)
            except BaseException as error:
                traceback.print_exc()
                cleanup_errors.append(type(error).__name__)
        for path in plugins:
            path.unlink(missing_ok=True)
        for handle in handles:
            handle.close()
        try:
            if unit.exists():
                frozen = Path('/sys/fs/cgroup') / parent / 'cgroup.freeze'
                if frozen.exists():
                    frozen.write_text('0')
                subprocess.run(['systemctl', 'stop', parent], check=True, timeout=10)
                unit.unlink()
                subprocess.run(['systemctl', 'daemon-reload'], check=True, timeout=10)
        except BaseException as error:
            traceback.print_exc()
            cleanup_errors.append(type(error).__name__)
        (root / 'cleanup.json').write_text(json.dumps(dict(errors=cleanup_errors,
            primary=type(primary).__name__ if primary is not None else None,
            own_children_exited=all(process.poll() is not None for process in processes))))
        (root / 'readback-observations.json').write_text(json.dumps(engine.observations))
        if cleanup_errors:
            if primary is not None:
                primary.add_note('LAB_CLEANUP_RECONCILIATION_REQUIRED')
            else:
                raise RuntimeError('LAB_CLEANUP_RECONCILIATION_REQUIRED')


if __name__ == '__main__':
    main()
