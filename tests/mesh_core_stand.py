import base64
import contextlib
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import socket
import socketserver
import ssl
import struct
import subprocess
import sys
import threading
import time

from cryptography import x509
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
from cryptography.x509.oid import NameOID
from control.friends.restricted import utc
from fixtures.mesh_supervisor import SOCKET, request
from online_package_stand import PackageStand, private_file
from scripts import package_online_renewal as package


class SupervisedProcess:
    def __init__(self, unit, state):
        self.unit, self.pid = unit, int(state['MainPID'])

    def poll(self):
        return request(dict(command='show', unit=self.unit))['returncode']

    def terminate(self):
        request(dict(command='stop', unit=self.unit))

    def wait(self, timeout):
        deadline = time.monotonic()+timeout
        while self.poll() is None and time.monotonic() < deadline:
            time.sleep(.05)
        assert self.poll() is not None
        return self.poll()


class CoreStand(PackageStand):
    def __init__(self, root, extracted, driver, *, age=12000):
        super().__init__(root, extracted, age=age)
        self.driver = driver
        self.binding = private_file(root/'isolated-runtime.json', package.encode(dict(schema=1,
            scope='isolated-core-not-production', source_commit=self.manifest['source_commit'],
            native_sources=self.manifest['native_sources'], entrypoint='carrier/internal/qualification/cmd/mesh-runtime',
            executable_sha256=package.digest(driver.read_bytes()))))
        self.stack = contextlib.ExitStack()
        self.accepted = []

    def online_settings(self):
        return dict(super().online_settings(), isolated_runtime=str(self.binding))

    def gateway_binary(self):
        return self.driver

    def launch(self, unit, command, environment):
        request(dict(command='register', unit=unit, specification=dict(command=command, environment=environment)))
        state = request(dict(command='start', unit=unit))['state']
        return SupervisedProcess(unit, state)

    def launch_gateway(self, unit, profile, observer, directory):
        directory.unlink()
        return self.launch(unit, [str(self.driver), '-mode', 'gateway', '-relay', self.relay,
            '-family-config', str(profile), '-publication-observer', str(observer), '-directory-export', str(directory),
            '-duration', '1h', '-echo', self.echo, '-https', self.https], dict(os.environ, FC_LOCAL_CORE='1'))

    def origins(self):
        stand = self
        key = Ed25519PrivateKey.generate()
        name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'isolated localhost')])
        certificate = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
            .serial_number(x509.random_serial_number()).not_valid_before(utc(time.time()-60))
            .not_valid_after(utc(time.time()+28800)).add_extension(x509.BasicConstraints(ca=True, path_length=None), True)
            .add_extension(x509.SubjectAlternativeName([x509.DNSName('localhost')]), False).sign(key, None))
        self.ca = private_file(self.root/'local-ca.pem', certificate.public_bytes(Encoding.PEM))
        secret = private_file(self.root/'local-origin.key', key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()))

        class HTTP(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def do_GET(self):
                self.send_response(200)
                self.send_header('Content-Length', '24')
                self.end_headers()
                self.wfile.write(b'verified-isolated-origin')

            def do_POST(self):
                body = self.rfile.read(int(self.headers['Content-Length']))
                connection = http.client.HTTPConnection('127.0.0.1', stand.http_port, timeout=10)
                try:
                    connection.request('POST', self.path, body, {'Content-Type': 'application/json'})
                    response = connection.getresponse()
                    raw = response.read()
                    self.send_response(response.status)
                    self.send_header('Content-Length', str(len(raw)))
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(raw)
                finally:
                    connection.close()

        class Echo(socketserver.BaseRequestHandler):
            def handle(self):
                receipt = dict(peer=self.client_address, accepted=time.time(), received=0, closed=False)
                stand.accepted.append(receipt)
                try:
                    while raw := self.request.recv(65536):
                        receipt['received'] += len(raw)
                        self.request.sendall(raw)
                finally:
                    receipt['closed'] = True

        class DNS(socketserver.StreamRequestHandler):
            def handle(self):
                header = self.rfile.read(2)
                if len(header) != 2:
                    return
                query = self.rfile.read(struct.unpack('!H', header)[0])
                answer = query[:2]+b'\x81\x80\x00\x01\x00\x01\x00\x00\x00\x00'+query[12:]+b'\xc0\x0c\x00\x01\x00\x01\x00\x00\x00\x1e\x00\x04\xcb\x00\x71\x07'
                self.wfile.write(struct.pack('!H', len(answer))+answer)

        class TCP(socketserver.ThreadingTCPServer):
            allow_reuse_address = True
            daemon_threads = True

        echo, dns = TCP(('127.0.0.1', 0), Echo), TCP(('127.0.0.1', 53), DNS)
        https = ThreadingHTTPServer(('127.0.0.1', 0), HTTP)
        configuration = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        configuration.load_cert_chain(self.ca, secret)
        https.socket = configuration.wrap_socket(https.socket, server_side=True)
        for server in (echo, dns, https):
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            self.stack.callback(server.server_close)
            self.stack.callback(thread.join, 5)
            self.stack.callback(server.shutdown)
        self.echo, self.https = ('127.0.0.1:'+str(server.server_address[1]) for server in (echo, https))
        self.endpoint = 'https://localhost:'+str(https.server_address[1])
        resolver = Path('/etc/resolv.conf')
        previous = resolver.read_bytes()
        self.stack.callback(resolver.write_bytes, previous)
        resolver.write_text('nameserver 127.0.0.1\n')

    def start(self):
        self.origins()
        self.supervisor = subprocess.Popen([sys.executable, str(package.ROOT/'tests/fixtures/mesh_supervisor.py'),
            'serve', str(self.root)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.stack.callback(self.supervisor.wait, 15)
        self.stack.callback(self.supervisor.terminate)
        deadline = time.monotonic()+5
        while not Path(SOCKET).exists():
            assert self.supervisor.poll() is None and time.monotonic() < deadline
            time.sleep(.02)
        relay = subprocess.Popen([str(self.driver), '-mode', 'relay'], env=dict(os.environ, FC_LOCAL_CORE='1'),
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        self.processes.append(relay)
        self.relay = json.loads(relay.stdout.readline())['address']
        super().start()
        self.systemctl.write_bytes(b'#!/usr/local/bin/python\n'+(package.ROOT/'tests/fixtures/mesh_supervisor.py').read_bytes())
        self.systemctl.chmod(0o755)
        controller = json.loads(self.controller.read_bytes())
        controller['isolated_runtime'] = str(self.binding)
        private_file(self.controller, package.encode(controller))
        for slot in ('NL', 'NL2'):
            deadline = time.monotonic()+5
            while not (self.fleet.nodes[slot].live/'directory.json').exists():
                assert time.monotonic() < deadline, 'real SeedManager publication unavailable'
                time.sleep(.02)

    def client(self, slot, seconds):
        config = private_file(self.root/(slot+'-client.json'), package.encode(dict(
            Endpoint=self.endpoint, Gateway='nl-amsterdam-'+('1' if slot == 'NL' else '2'),
            Identity=base64.b64encode(self.fleet.device._identity.get_private_key()).decode(),
            Wireguard=self.fleet.device.wireguard_public_key, Anchor=base64.b64encode(self.fleet.service.anchor).decode(),
            Roots=str(self.ca), OriginRoot=str(self.ca), DurationSeconds=seconds)))
        output = self.stack.enter_context((self.root/(slot+'-client.log')).open('wb'))
        process = subprocess.Popen([str(self.driver), '-mode', 'client', '-relay', self.relay, '-client-config', str(config)],
            env=dict(os.environ, FC_LOCAL_CORE='1'), stdout=output, stderr=output)
        self.processes.append(process)
        return process

    def run(self, mode, approval=None):
        command = self.command(mode)
        if approval is not None:
            command += ['--outage-approval', str(approval)]
        result = subprocess.run(command, cwd=self.root, capture_output=True, timeout=180)
        return result.returncode, json.loads(result.stdout)

    def close(self):
        try:
            super().close()
        finally:
            self.stack.close()
