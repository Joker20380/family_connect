import base64
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import ipaddress
import json
import os
from pathlib import Path
import queue
import socketserver
import ssl
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace

import pytest
import RNS
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat
from cryptography.x509.oid import NameOID

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'clients/linux'))
sys.path.insert(0, str(ROOT / 'tests'))
from mesh_chat_service import ServiceHost, ServiceOwner
import mesh_materials
from mesh_ownership import Ownership
from mesh_ownership import OwnershipError
import mesh_service
from provisioning.chat_bridge import ChatBridge
from provisioning import chat_bridge_protocol as wire
from control.friends.access import Rejected
from control.friends.chat import ChatAccess
from control.friends.restricted import utc
from messenger.admission import message
from test_friends_restricted import proof
from test_native_authority_compat import fixture as authority_fixture

pytestmark = pytest.mark.skipif(os.geteuid() != 0 or not os.environ.get('FC_L021_WORKER'),
                                reason='isolated root process gate with explicitly built fixture worker')


class Events(socketserver.ThreadingTCPServer):
    daemon_threads = False

    def __init__(self):
        self.events = queue.Queue()
        self.cleanup = threading.Event()
        self.bootstrap = threading.Event()
        self.bootstrap.set()
        self.peer = threading.Event()
        self.peer.set()
        self.fail_bootstrap = self.fail_peer = False
        self.history = []
        class Handler(socketserver.StreamRequestHandler):
            def handle(connection):
                kind = json.loads(connection.rfile.readline())['event']
                self.history.append(kind)
                quiet = ((kind == 'bootstrap' and self.bootstrap.is_set()) or
                         (kind == 'peer_control' and self.peer.is_set()) or
                         (kind == 'terminal' and not self.fail_peer) or
                         (kind == 'drained' and not (self.fail_peer or self.fail_bootstrap)))
                if not quiet:
                    self.events.put(kind)
                result = 1
                if kind == 'cleanup_entered':
                    self.cleanup.wait(12)
                if kind == 'bootstrap':
                    self.bootstrap.wait(12)
                    result = 0 if self.fail_bootstrap else 1
                if kind == 'peer_control':
                    self.peer.wait(12)
                    result = 0 if self.fail_peer else 1
                connection.wfile.write(bytes([result]))
        super().__init__(('127.0.0.1', 0), Handler)
        self.thread = threading.Thread(target=self.serve_forever)
        self.thread.start()

    def until(self, kind):
        return self.until_all(kind)

    def until_all(self, *kinds):
        seen = []
        deadline = time.monotonic() + 8
        while not set(kinds).issubset(seen):
            seen.append(self.events.get(timeout=max(.01, deadline - time.monotonic())))
        return seen

    def close(self):
        self.cleanup.set()
        self.bootstrap.set()
        self.peer.set()
        self.shutdown()
        self.server_close()
        self.thread.join(3)


@pytest.fixture
def authenticated(tmp_path, monkeypatch, request):
    binary = os.environ['FC_L021_WORKER']
    service, device, now, gateway = authority_fixture(tmp_path, crl_number=1)
    response = service.fetch(proof(service, device))
    chat = ChatAccess(service.access)
    chat.initialize()
    api_calls = []
    class API(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            api_calls.append(self.path)
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            try:
                result = chat.challenge(**body) if self.path == wire.PATHS[0] else chat.register(**body)
                status = 200
            except Rejected:
                result, status = {}, 403
            encoded = json.dumps(result).encode()
            self.send_response(status)
            self.send_header('Content-Length', str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)
    class Mailbox(socketserver.BaseRequestHandler):
        def handle(self):
            self.request.settimeout(5)
            self.request.sendall(b'from-peer')
            while data := self.request.recv(16384):
                self.request.sendall(data)
    api = ThreadingHTTPServer(('127.0.0.1', 0), API)
    mailbox = socketserver.ThreadingTCPServer(('127.0.0.1', 0), Mailbox)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'isolated L021 API')])
    certificate = (x509.CertificateBuilder().subject_name(subject).issuer_name(subject).public_key(key.public_key())
                   .serial_number(1).not_valid_before(utc(now - 60)).not_valid_after(utc(now + 3600))
                   .add_extension(x509.BasicConstraints(ca=True, path_length=None), True)
                   .add_extension(x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address('185.251.89.19'))]), False)
                   .sign(key, hashes.SHA256()))
    cert_path, key_path = tmp_path / 'api.pem', tmp_path / 'api.key'
    cert_path.write_bytes(certificate.public_bytes(Encoding.PEM))
    key_path.write_bytes(key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()))
    key_path.chmod(0o600)
    tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    tls.load_cert_chain(cert_path, key_path)
    api.socket = tls.wrap_socket(api.socket, server_side=True)
    threads = [threading.Thread(target=server.serve_forever) for server in (api, mailbox)]
    for thread in threads:
        thread.start()
    events = Events()
    def stop_servers():
        events.cleanup.set()
        for server in (api, mailbox):
            server.shutdown()
            server.server_close()
        for thread in threads:
            thread.join(3)
        events.close()
    request.addfinalizer(stop_servers)
    settings = tmp_path / 'fixture.json'
    settings.write_text(json.dumps(dict(gateway=gateway, api='%s:%s' % api.server_address,
                                        mailbox='%s:%s' % mailbox.server_address)))
    settings.chmod(0o600)
    monkeypatch.setattr(mesh_service, 'WORKER', binary)
    monkeypatch.setattr(mesh_materials, 'WORKER', binary)
    monkeypatch.setattr(mesh_service, 'ENV', dict(mesh_service.ENV, FC_L021_FIXTURE=str(settings),
                         FC_L021_EVENTS='%s:%s' % events.server_address, SSL_CERT_FILE=str(cert_path)))
    cache = tmp_path / 'cache'
    cache.mkdir(mode=0o700)
    storage = mesh_materials.CacheStore(cache, 1000)
    storage.write(json.dumps(dict(response=response, denied=False, next_attempt=now + 300)).encode())
    class CachedMaterials(mesh_materials.MaterialOwner):
        def resolve(self, supplied, underlying, cancel, deadline, required):
            assert required
            return super().resolve(supplied, underlying, cancel, deadline, False)
    materials = CachedMaterials(storage)
    workers = []
    def worker(gate):
        value = mesh_service.NativeWorker(gate)
        workers.append(value)
        return value
    directory = Path('/run') / ('fc-l021-' + tmp_path.name)
    selected_owner = ServiceOwner
    if os.environ.get('FC_L021_SERVICE_SOURCE'):
        spec = importlib.util.spec_from_file_location('l021_before', os.environ['FC_L021_SERVICE_SOURCE'])
        before = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(before)
        selected_owner = before.ServiceOwner
    owner = selected_owner(materials, base64.b64encode(service.anchor).decode(),
                           ownership_factory=lambda role: Ownership(role, directory), worker_factory=worker)
    host = ServiceHost(tmp_path / 'service.sock', 0, owner)
    host.start()
    bridge = ChatBridge(device.reference, _paths=[], _root_uid=0)
    bridge.service_path = host.endpoint
    bridge.configure(lambda: dict(identity=base64.b64encode(device._identity.get_private_key()).decode(),
                                  wireguard_public=device.wireguard_public_key))
    try:
        yield SimpleNamespace(owner=owner, host=host, bridge=bridge, events=events, workers=workers,
                              device=device, access=service.access, directory=directory,
                              chat_identity=RNS.Identity(), api_calls=api_calls, authority=service, settings=settings)
    finally:
        events.cleanup.set()
        events.bootstrap.set()
        events.peer.set()
        bridge.close()
        host.close()
        if owner.failed:
            with pytest.raises(RuntimeError, match='CLEANUP_UNCONFIRMED'):
                owner.close()
        else:
            owner.close()
        storage.close()


@pytest.mark.parametrize('teardown', ['shutdown', 'cancel', 'idle', 'expiry', 'preempt'])
def test_authenticated_requests_retain_actual_native_generation(authenticated, teardown):
    fixture = authenticated
    identity = RNS.Identity()
    public = identity.get_public_key().hex()
    body = dict(public_identity=fixture.device.public_identity, wireguard_public_key=fixture.device.wireguard_public_key,
                chat_public=public)
    status, raw = fixture.bridge.request(wire.PATHS[0], json.dumps(body).encode(), 10)
    assert status == 200 and fixture.bridge.route == 'SERVICE_ONLY'
    challenge = json.loads(raw)['challenge']
    registration = dict(proof=fixture.device.prove_transport_key(challenge), chat_public=public,
                        chat_signature=identity.sign(message(public, fixture.device.reference, challenge)).hex())
    observed = []
    while observed.count('leases:1') < 2 and 'leases:0' not in observed:
        observed.append(fixture.events.events.get(timeout=5))
    if 'leases:0' in observed:
        if 'cleanup_entered' not in observed:
            fixture.events.until('cleanup_entered')
        print('BEFORE: challenge=200; active_native_leases=0; opens=1; cleanup=held; next=register')
        try:
            fixture.bridge.request(wire.PATHS[1], json.dumps(registration).encode(), 5)
        finally:
            fixture.events.cleanup.set()
        pytest.fail('old implementation unexpectedly survived held native cleanup')
    assert observed.count('open') == 1
    assert observed.count('authenticated') == 1 and observed.count('leases:2') == 1
    status, raw = fixture.bridge.request(wire.PATHS[1], json.dumps(registration).encode(), 10)
    assert status == 200 and json.loads(raw)['status'] == 'pending-node'
    assert fixture.events.until('leases:1') == ['leases:2', 'leases:1']
    with fixture.access.db() as database:
        database.execute('UPDATE devices SET revoked=1')
    with pytest.raises(wire.BridgeError, match='DENIED'):
        fixture.bridge.request(wire.PATHS[0], json.dumps(body).encode(), 5)
    assert fixture.events.until('leases:1') == ['leases:2', 'leases:1']
    with fixture.access.db() as database:
        database.execute('UPDATE devices SET revoked=0')
    with fixture.bridge.open_service_mailbox(time.monotonic() + 5, threading.Event()) as channel:
        channel.settimeout(3)
        assert channel.recv(9) == b'from-peer'
        channel.sendall(b'to-peer')
        assert channel.recv(7) == b'to-peer'
    assert fixture.events.until('leases:1') == ['leases:2', 'leases:1']
    generation = fixture.owner.generation_lease
    assert fixture.workers[0].chat.call('route', lease=generation)['route'] == 'SERVICE_ONLY'
    assert len(fixture.workers) == 1 and fixture.owner.materials.summary['durable']
    binding = fixture.owner.current
    gate = fixture.owner.gate
    with ThreadPoolExecutor(1) as executor:
        pending = None
        vpn = None
        if teardown == 'shutdown':
            pending = executor.submit(fixture.owner.close)
        elif teardown == 'cancel':
            fixture.owner.cancel.set()
        elif teardown == 'idle':
            fixture.owner.touched = time.monotonic() - 46
        elif teardown == 'expiry':
            with fixture.owner.lock:
                binding.material['readiness']['expires_at'] = 1
        else:
            vpn = Ownership('vpn', fixture.directory)
            pending = executor.submit(vpn.acquire, threading.Event(), time.monotonic() + 10)
        try:
            assert set(fixture.events.until_all('leases:0', 'cleanup_entered')) == {'leases:0', 'cleanup_entered'}
            assert (pending is None or not pending.done()) and gate.active
            assert (fixture.directory / 'transport.lock').read_bytes() == b'chat'
            with pytest.raises(wire.BridgeError):
                binding.probe(fixture.device.reference)
        finally:
            fixture.events.cleanup.set()
        assert fixture.events.until('cleaned') == ['cleaned']
        fixture.workers[0].process.wait(5)
        if pending is not None:
            pending.result(5)
        if vpn is not None:
            assert vpn.active and not gate.active
            with pytest.raises(OwnershipError, match='VPN_RESERVED'):
                Ownership('chat', fixture.directory).acquire(threading.Event(), time.monotonic() + 1)
            vpn.finish()
    assert fixture.workers[0].process.returncode == 0
    if teardown != 'shutdown':
        with fixture.owner.lock:
            assert not gate.active and fixture.owner.current is None
        status, _ = fixture.bridge.request(wire.PATHS[0], json.dumps(dict(public_identity=fixture.device.public_identity,
                                 wireguard_public_key=fixture.device.wireguard_public_key, chat_public=public)).encode(), 10)
        assert status == 200 and len(fixture.workers) == 2
        observed = fixture.events.until('authenticated')
        assert observed.count('open') == 1
    else:
        assert not (fixture.directory / 'transport.lock').read_bytes()


@pytest.mark.parametrize('failure', ['cancel', 'peer'])
def test_unconfirmed_authenticated_cleanup_retains_admission(authenticated, failure):
    fixture = authenticated
    if failure == 'peer':
        fixture.events.peer.clear()
    identity = RNS.Identity()
    body = dict(public_identity=fixture.device.public_identity, wireguard_public_key=fixture.device.wireguard_public_key,
                chat_public=identity.get_public_key().hex())
    assert fixture.bridge.request(wire.PATHS[0], json.dumps(body).encode(), 10)[0] == 200
    fixture.events.until('authenticated')
    if failure == 'peer':
        fixture.events.fail_peer = True
        fixture.events.peer.set()
    else:
        fixture.owner.cancel.set()
    fixture.events.until('cleanup_entered')
    fixture.owner.watcher.join(8)
    assert fixture.owner.failed and fixture.owner.gate.active
    assert (fixture.directory / 'transport.lock').read_bytes() == b'chat'
    with pytest.raises(OwnershipError, match='OWNER_BUSY'):
        Ownership('chat', fixture.directory).acquire(threading.Event(), time.monotonic() + 1)
    assert fixture.owner.binding() is None and len(fixture.workers) == 1


def test_active_authenticated_mailbox_cancelled_before_native_drain(authenticated):
    fixture = authenticated
    with fixture.bridge.open_service_mailbox(time.monotonic() + 10, threading.Event()) as channel:
        channel.settimeout(3)
        assert channel.recv(9) == b'from-peer'
        fixture.events.until('authenticated')
        fixture.owner.cancel.set()
        observed = fixture.events.until_all('cleanup_entered', 'leases:0')
        assert 'leases:0' in observed and fixture.owner.gate.active
        assert channel.recv(1) == b''
        fixture.events.cleanup.set()
        fixture.events.until('cleaned')
    fixture.workers[0].process.wait(5)
    with fixture.owner.lock:
        assert fixture.owner.current is None and fixture.owner.generation_lease is None
        assert not fixture.owner.failed
    assert not (fixture.directory / 'transport.lock').read_bytes()
