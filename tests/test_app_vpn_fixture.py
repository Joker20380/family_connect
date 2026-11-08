import datetime
import http.server
import importlib.util
import json
from pathlib import Path
import socket
import ssl
import subprocess
import threading

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT/'pilot/android-app-vpn'/f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def request_during_incomplete_handshake(tmp_path, server_type):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'localhost')])
    now = datetime.datetime.now(datetime.timezone.utc)
    certificate = (x509.CertificateBuilder().subject_name(subject).issuer_name(subject).public_key(key.public_key())
                   .serial_number(x509.random_serial_number()).not_valid_before(now-datetime.timedelta(minutes=1))
                   .not_valid_after(now+datetime.timedelta(hours=1))
                   .add_extension(x509.SubjectAlternativeName([x509.DNSName('localhost')]), False).sign(key, hashes.SHA256()))
    cert_path, key_path = tmp_path/'certificate.pem', tmp_path/'key.pem'
    cert_path.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    key_path.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(cert_path, key_path)

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'DIRECT')

        def log_message(self, *args):
            pass

    server = server_type(('127.0.0.1', 0), Handler, context)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    blocked = socket.create_connection(server.server_address, timeout=1)
    try:
        client = ssl.create_default_context(cafile=str(cert_path))
        with socket.create_connection(server.server_address, timeout=1) as connection:
            with client.wrap_socket(connection, server_hostname='localhost') as secure:
                secure.sendall(b'GET / HTTP/1.0\r\nHost: localhost\r\n\r\n')
                with secure.makefile('rb') as response:
                    assert b'DIRECT' in response.read()
    finally:
        blocked.close()
        server.shutdown()
        server.server_close()
        worker.join(timeout=2)
    assert not worker.is_alive()


def test_incomplete_tls_handshake_does_not_block_other_probes(tmp_path):
    request_during_incomplete_handshake(tmp_path, load('fixture').RoutingHTTPServer)


def test_collect_retains_failed_probe_and_other_receipts(tmp_path, monkeypatch):
    module = load('run')
    results = iter([subprocess.CompletedProcess([], 0, '[{"ipv4_error":"SocketTimeoutException"}]', ''),
                    subprocess.CompletedProcess([], 1, '', 'missing'),
                    subprocess.CompletedProcess([], 0, '{"ok":true}', '')])
    monkeypatch.setattr(module.subprocess, 'run', lambda *args, **kwargs: next(results))
    assert module.collect_receipts(['adb'], tmp_path, ['routing', 'absent', 'catalog']) == ['absent']
    assert json.loads((tmp_path/'routing.json').read_text())[0]['ipv4_error'] == 'SocketTimeoutException'
    assert json.loads((tmp_path/'catalog.json').read_text()) == {'ok': True}
