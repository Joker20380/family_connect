import base64
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

from scripts import package_online_renewal as package
from cryptography import x509
from control.friends.profile_store import metadata
from control.friends.restricted import iso
from test_multi_gateway_renewal import make_fleet, profiles, change_leaf


def private_file(path, raw):
    path.write_bytes(raw)
    path.chmod(0o600)
    return path


class PackageStand:
    def __init__(self, root, extracted, *, age=0):
        assert os.geteuid() == 0 and Path('/.dockerenv').exists() and root.is_relative_to('/run')
        self.root, self.extracted = root, extracted
        self.manifest = json.loads((extracted/'source-manifest.json').read_bytes())
        self.fleet = make_fleet(root, now=int(time.time())-age)
        for slot, profile in profiles(self.fleet).items():
            leaf = x509.load_pem_x509_certificate(profile['certificate'].encode())
            extensions = []
            for extension in leaf.extensions:
                if isinstance(extension.value, x509.SubjectAlternativeName):
                    extension = x509.Extension(extension.oid, extension.critical,
                        x509.SubjectAlternativeName(list(extension.value)+[x509.DNSName('gateway.family-connect.test')]))
                extensions.append(extension)
            change_leaf(self.fleet, slot, extensions=extensions)
        self.processes, self.proxies, self.configs, self.states = [], [], {}, {}
        self.systemctl = Path('/usr/bin/systemctl')
        self.prior = self.systemctl.read_bytes() if self.systemctl.exists() else None
        self.prior_mode = self.systemctl.stat().st_mode & 0o777 if self.prior is not None else None
        self.service_state = Path('/run/fc-online-service-state.json')
        assert not self.service_state.exists()

    def configure(self, slot):
        node = self.fleet.nodes[slot]
        private = self.root/(slot+'-config')
        private.mkdir(mode=0o700)
        anchor = private_file(private/'anchor', base64.b64encode(self.fleet.service.anchor))
        config = dict(schema=1, role=node.role, live=str(node.live), state=str(node.state),
            database=str(self.root/'access.db') if slot == 'RU' else None, anchor=str(anchor),
            anchor_sha256=package.digest(self.fleet.service.anchor), api_archive=str(self.extracted/'api.pyz'),
            api_sha256=self.manifest['api_sha256'], source_files=self.manifest['source_files'],
            source_sha256=self.manifest['source_sha256'], admission_mode='all_activated',
            gateway_ids=self.fleet.identities, gateway_slot=slot, online=dict(contract=package.CONTRACT))
        if slot == 'RU':
            private_file(node.live/'admission.json', package.encode(dict(version=2, eligibility='all_activated')))
            private_file(node.live/'anchor.pub', base64.b64encode(self.fleet.service.anchor))
            config['service_units'] = ['test-http.service', 'test-renewal.timer', 'test-renewal.service',
                                       'test-sync.timer', 'test-sync.service']
            with socket.socket() as port:
                port.bind(('127.0.0.1', 0))
                self.http_port = port.getsockname()[1]
            environment = dict(os.environ, FC_FRIENDS_RESTRICTED_DIR=str(node.live),
                               FC_FRIENDS_RESTRICTED_DELIVERY_LIFETIME='14400')
            process = subprocess.Popen([sys.executable, '-I', '-B', str(self.extracted/'http.pyz'),
                '--root', str(self.root), '--port', str(self.http_port)], env=environment,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.processes.append(process)
            deadline = time.monotonic()+5
            while True:
                try:
                    with socket.create_connection(('127.0.0.1', self.http_port), timeout=.1):
                        break
                except OSError:
                    assert process.poll() is None and time.monotonic() < deadline, 'packaged HTTP unavailable'
                    time.sleep(.02)
            for unit in config['service_units']:
                self.states[unit] = dict(ActiveState='inactive', SubState='dead', MainPID='0',
                                        InvocationID='', NRestarts='0', Result='success')
            self.states['test-http.service'].update(ActiveState='active', SubState='running', MainPID=str(process.pid))
        else:
            config['service_units'] = ['test-'+slot+'.service']
            profile_root = self.root/(slot+'-profile')
            profile_root.mkdir(mode=0o750)
            os.chown(profile_root, 0, 41003)
            profile = private_file(profile_root/'gateway.json', (node.live/'gateway.json').read_bytes())
            os.chown(profile, 0, 41003)
            profile.chmod(0o640)
            lock = private_file(private/'profile.lock', b'')
            operations = private/'operations'
            operations.mkdir(mode=0o700)
            directory = json.loads((node.live/'directory.json').read_bytes())
            directory.update(issued_at=iso(int(time.time())-1), expires_at=iso(int(time.time())+3599))
            private_file(node.live/'directory.json', package.encode(directory))
            private_file(self.fleet.nodes['RU'].directory_destination(slot), package.encode(directory))
            publisher = node.live.stat()
            gateway = self.extracted/'gateway'
            locator = dict(schema=1, lock_version=1, profile=str(profile), lock=str(lock), operations=str(operations),
                reader_gid=41003, directory=dict(path=str(node.live/'directory.json'),
                    metadata=metadata((node.live/'directory.json').stat()), publisher_parent=dict(path=str(node.live),
                        **metadata(publisher), device=publisher.st_dev, inode=publisher.st_ino),
                    publisher_contract=[[str(gateway), self.manifest['gateway_sha256'], metadata(gateway.stat())]]))
            locator_path = private_file(private/'locator.json', package.encode(locator))
            config.update(profile_locator=str(locator_path), profile_locator_sha256=package.digest(locator_path.read_bytes()))
            observer = private/'reader.sock'
            config['online'].update(reader_socket=str(observer), reader_uid=0,
                                    reader_executable_sha256=self.manifest['gateway_sha256'])
            proxy = socket.socket()
            proxy.bind(('127.0.0.1', 0))
            proxy.listen(1)
            self.proxies.append(proxy)
            environment = dict(os.environ, YANDEX_TELEMOST_OAUTH_TOKEN='synthetic-isolated-unused',
                HTTPS_PROXY='http://127.0.0.1:'+str(proxy.getsockname()[1]), NO_PROXY='')
            process = subprocess.Popen([str(gateway), '-family-config', str(profile), '-listen', '127.0.0.1:0',
                '-publication-observer', str(observer)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=environment)
            self.processes.append(process)
            deadline = time.monotonic()+5
            while not observer.exists():
                assert process.poll() is None and time.monotonic() < deadline, 'gateway observer unavailable'
                time.sleep(.02)
            self.states[config['service_units'][0]] = dict(ActiveState='active', SubState='running', MainPID=str(process.pid),
                InvocationID='synthetic', NRestarts='0', Result='success')
        self.configs[slot] = private_file(private/'node.json', package.encode(config))

    def start(self):
        ssh = self.root/'ssh'
        ssh.mkdir(mode=0o700)
        for name in ('host', 'client'):
            subprocess.run(['ssh-keygen', '-q', '-t', 'ed25519', '-N', '', '-f', str(ssh/name)], check=True)
        known = private_file(ssh/'known_hosts', b'127.0.0.1 '+(ssh/'host.pub').read_bytes())
        configuration = private_file(ssh/'sshd_config', ('ListenAddress 127.0.0.1\nPort 22\n'
            'HostKey '+str(ssh/'host')+'\nAuthorizedKeysFile '+str(ssh/'client.pub')+
            '\nPidFile '+str(ssh/'pid')+'\nPermitRootLogin prohibit-password\nPasswordAuthentication no\n'
            'KbdInteractiveAuthentication no\nUsePAM no\nLogLevel ERROR\n').encode())
        Path('/run/sshd').mkdir(mode=0o755, exist_ok=True)
        daemon = subprocess.Popen(['/usr/sbin/sshd', '-D', '-e', '-f', str(configuration)],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.processes.append(daemon)
        deadline = time.monotonic()+5
        while True:
            try:
                with socket.create_connection(('127.0.0.1', 22), timeout=.1):
                    break
            except OSError:
                assert daemon.poll() is None and time.monotonic() < deadline, 'isolated ssh unavailable'
                time.sleep(.02)
        for slot in ('RU', 'NL', 'NL2'):
            self.configure(slot)
        private_file(self.service_state, package.encode(self.states))
        self.systemctl.write_bytes(b'#!/usr/local/bin/python\n'+(package.ROOT/'tests/fixtures/online_systemctl.py').read_bytes())
        self.systemctl.chmod(0o755)
        routes = {slot: dict(key=str(ssh/'client'), known_hosts=str(known), target='root@127.0.0.1',
            command=[sys.executable, '-E', '-s', '-B', str(self.extracted/'renewal/node.py'), '--config', str(config)])
            for slot, config in self.configs.items()}
        self.controller = private_file(self.root/'controller.json', package.encode(dict(schema=1, online=package.CONTRACT,
            state=str(self.root/'coordinator'), anchor=base64.b64encode(self.fleet.service.anchor).decode(),
            gateway_ids=self.fleet.identities, schedule_seconds=0, ssh_routes=routes)))

    def command(self, mode):
        return [sys.executable, '-E', '-s', '-B', str(self.extracted/'renewal/online_cli.py'),
            '--config', str(self.controller), '--operation', 'test-packaged-ssh-controller', '--mode', mode]

    def rpc_fault(self, slot, command, kind):
        wrapper = private_file(self.root/'fault-python', b'#!/usr/local/bin/python\n'+
            (package.ROOT/'tests/fixtures/online_rpc_fault.py').read_bytes())
        wrapper.chmod(0o700)
        private_file(self.configs[slot].parent/'rpc-fault.json', package.encode(dict(command=command, kind=kind)))
        configuration = json.loads(self.controller.read_bytes())
        configuration['ssh_routes'][slot]['command'][0] = str(wrapper)
        private_file(self.controller, package.encode(configuration))

    def run(self, mode):
        result = subprocess.run(self.command(mode),
            cwd=self.root, capture_output=True, timeout=30)
        return result.returncode, json.loads(result.stdout)

    def close(self):
        for process in reversed(self.processes):
            process.terminate()
            process.wait(timeout=10)
        for proxy in self.proxies:
            proxy.close()
        self.service_state.unlink(missing_ok=True)
        if self.prior is None:
            self.systemctl.unlink(missing_ok=True)
        else:
            self.systemctl.write_bytes(self.prior)
            self.systemctl.chmod(self.prior_mode)
