"""Synthetic TLS/proofs and real DIRECT sockets in an empty disposable netns only."""
import argparse
from contextlib import ExitStack
from datetime import datetime, timedelta, timezone
import ipaddress
import json
import os
from pathlib import Path
import secrets
import socket
import ssl
import subprocess
import sys
import tempfile
import threading
import time
from types import SimpleNamespace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'clients/linux'), str(ROOT / 'clients/desktop/tests')]


def peer(directory):
    from control.friends.access import Access, Rejected
    from control.friends.chat import ChatAccess
    from provisioning import chat_bridge_protocol as wire
    chat = ChatAccess(Access(directory / 'access.sqlite'))
    node = json.loads((directory / 'node.json').read_text())
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            try:
                assert self.headers['Accept-Encoding'] == 'identity'
                body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                if self.path == wire.PATHS[0]:
                    result = chat.challenge(**body)
                else:
                    assert self.path == wire.PATHS[1]
                    result = chat.register(**body)
                    result.update(status='active', node=node)
                raw = json.dumps(result).encode()
                self.send_response(200)
            except Rejected:
                raw = b''
                self.send_response(403)
            self.send_header('Content-Length', str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
    server = ThreadingHTTPServer(('185.251.89.19', 8443), Handler)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(directory / 'cert.pem', directory / 'key.pem')
    server.socket = context.wrap_socket(server.socket, server_side=True)
    mailbox = socket.socket()
    mailbox.bind(('192.0.2.1', 4242))
    mailbox.listen(4)
    def accept():
        while True:
            channel, _ = mailbox.accept()
            def exchange(channel):
                with channel:
                    channel.settimeout(3)
                    try:
                        data = channel.recv(16384)
                        channel.sendall(data.upper())
                        channel.shutdown(socket.SHUT_WR)
                    except OSError:
                        pass
            threading.Thread(target=exchange, args=(channel,), daemon=True).start()
    threading.Thread(target=accept, daemon=True).start()
    (directory / 'ready').touch()
    server.serve_forever()


def run(worker, host_netns):
    if os.geteuid() != 0 or os.stat('/proc/self/ns/net').st_ino in (host_netns, os.stat('/proc/1/ns/net').st_ino):
        raise SystemExit('Separate root network namespace required')
    def command(*args):
        return subprocess.check_output(['ip', *args], text=True, timeout=5)
    if [entry['ifname'] for entry in json.loads(command('-j', 'link', 'show'))] != ['lo']:
        raise SystemExit('Empty network namespace required')
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from chat_direct_host import DirectHost, Native
    from provisioning.chat_direct import DirectBridge
    from provisioning.chat_owner import ChatOwner
    from provisioning.chat_transport import ProtectedMailbox, initialize
    from provisioning import chat_bridge_protocol as wire
    from test_chat_direct import API
    import httpx
    import mesh_network
    command('netns', 'add', 'fc-l01-peer')
    with ExitStack() as cleanup:
        cleanup.callback(command, 'netns', 'del', 'fc-l01-peer')
        command('link', 'add', 'eth0', 'type', 'veth', 'peer', 'name', 'peer0')
        command('link', 'set', 'peer0', 'netns', 'fc-l01-peer')
        command('addr', 'add', '192.0.2.2/24', 'dev', 'eth0')
        command('link', 'set', 'eth0', 'up')
        for interface in ('all', 'default', 'eth0'):
            Path('/proc/sys/net/ipv4/conf/' + interface + '/rp_filter').write_text('0')
        command('-n', 'fc-l01-peer', 'addr', 'add', '192.0.2.1/24', 'dev', 'peer0')
        command('-n', 'fc-l01-peer', 'addr', 'add', '185.251.89.19/32', 'dev', 'peer0')
        command('-n', 'fc-l01-peer', 'link', 'set', 'peer0', 'up')
        command('route', 'add', 'default', 'via', '192.0.2.1', 'dev', 'eth0')
        directory = Path(cleanup.enter_context(tempfile.TemporaryDirectory(prefix='fc-chat-kernel-')))
        api = API(directory)
        api.node.update(host='192.0.2.1')
        (directory / 'node.json').write_text(json.dumps(api.node))
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        name = x509.Name([x509.NameAttribute(x509.NameOID.COMMON_NAME, 'disposable chat peer')])
        now = datetime.now(timezone.utc)
        cert = x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key()).serial_number(1).not_valid_before(now-timedelta(minutes=1)).not_valid_after(now+timedelta(minutes=10)).add_extension(x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address('185.251.89.19'))]), critical=False).add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True).sign(key, hashes.SHA256())
        (directory / 'cert.pem').write_bytes(cert.public_bytes(serialization.Encoding.PEM))
        (directory / 'key.pem').write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
        os.environ['SSL_CERT_FILE'] = str(directory / 'cert.pem')
        process = subprocess.Popen(['ip', 'netns', 'exec', 'fc-l01-peer', sys.executable, __file__, '--peer', str(directory)], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        cleanup.callback(process.wait, 5)
        cleanup.callback(process.terminate)
        deadline = time.monotonic() + 10
        while not (directory / 'ready').exists():
            if process.poll() is not None or time.monotonic() > deadline:
                raise RuntimeError('Synthetic peer not ready')
            threading.Event().wait(.05)
        host = DirectHost(directory / 'chat.sock', os.getuid(), Native(worker))
        host.start()
        cleanup.callback(host.close)
        direct = DirectBridge(api.device.reference, _paths=[host.endpoint])
        fallback = SimpleNamespace(request=lambda *args: (_ for _ in ()).throw(AssertionError('fallback used')), close=lambda: None,
                                   open_mailbox=lambda *args: (_ for _ in ()).throw(AssertionError('fallback used')))
        storage_key = secrets.token_bytes(32)
        friends = SimpleNamespace(_device=lambda _: api.device, http_factory=lambda: httpx.Client(base_url='https://unused.invalid', transport=httpx.MockTransport(lambda _: (_ for _ in ()).throw(AssertionError('OS route used')))))
        owner = ChatOwner(directory / 'store', friends, keyring=SimpleNamespace(key=lambda *args, **kwargs: storage_key),
            runtime_factory=initialize, restricted_factory=lambda _: fallback, direct_factory=lambda _: direct, events_fetcher=lambda _: [])
        cleanup.callback(owner.close)
        profile = owner.open(create=True)
        for guarded in (False, True):
            if guarded:
                for arguments in mesh_network.guard_commands('add'):
                    command(*arguments[1:])
                route = json.loads(command('-j', '-4', 'route', 'get', '185.251.89.19', 'mark', str(mesh_network.MARK)))
                assert route[0]['dev'] == 'eth0'
                assert subprocess.run(['ip', '-4', 'route', 'get', '185.251.89.19'], capture_output=True).returncode != 0
            owner.node = None
            owner.next_enrollment = 0
            owner.tick(online=True, visible=True)
            assert owner.delivery_error is None and isinstance(owner.carrier, ProtectedMailbox), ('registration', guarded)
            owner.local.delivery_update(online=False, foreground=False)
            owner.local.detach_carrier()
            with owner.carrier._direct(time.monotonic()+5, threading.Event()) as channel:
                assert channel.family == socket.AF_UNIX and not os.get_inheritable(channel.fileno())
                channel.sendall(b'protected bytes')
                channel.shutdown(socket.SHUT_WR)
                assert channel.recv(16384) == b'PROTECTED BYTES'
                assert channel.recv(1) == b''
            owner.carrier.close()
            owner.carrier = None
        with direct.open_mailbox(time.monotonic()+5, threading.Event()) as channel:
            channel.settimeout(2)
            command('link', 'set', 'eth0', 'name', 'eth-new')
            assert channel.recv(1) == b''
            command('link', 'set', 'eth-new', 'name', 'eth0')
        with api.access.db() as database:
            assert database.execute('SELECT COUNT(*) FROM chat_challenges WHERE used=1').fetchone()[0] == 2
            database.execute('UPDATE devices SET revoked=1')
        owner.close()
        owner.direct_factory = lambda _: DirectBridge(api.device.reference, _paths=[host.endpoint])
        assert owner.open(create=False) == profile
        owner.tick(online=True, visible=True)
        assert owner.node is None and host.authority.revoked.is_set()
        assert not Path('/run/family-connect-auto/guard.json').exists()
    print(json.dumps(dict(result='PASS', scope='isolated-kernel-synthetic-TLS-peer', protected_api=True, protected_mailbox=True,
        vpn_off=True, guarded_underlying=True, unmarked_route='UNREACHABLE', real_owner_proofs=True,
        encrypted_reopen=True, revocation=True, interface_change_closed=True, vpn_owner_created=False,
        fixture_rpf='disabled only inside disposable test netns', host_network_changed=False, live=False)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--peer', type=Path)
    parser.add_argument('--worker', type=Path)
    parser.add_argument('--host-netns', type=int)
    arguments = parser.parse_args()
    if arguments.peer:
        peer(arguments.peer)
    else:
        run(arguments.worker, arguments.host_netns)
