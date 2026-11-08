"""Isolated real AWG/REALITY peers and distinct direct/VPN TLS endpoints."""
import argparse
import datetime
import http.server
import ipaddress
import json
import os
from pathlib import Path
import queue
import signal
import socketserver
import ssl
import struct
import subprocess
import threading

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


class RoutingHTTPServer(http.server.ThreadingHTTPServer):
    def __init__(self, address, handler, tls):
        self.tls = tls
        super().__init__(address, handler)

    def get_request(self):
        connection, address = super().get_request()
        connection.settimeout(5)
        return self.tls.wrap_socket(connection, server_side=True, do_handshake_on_connect=False), address


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--awg-peer', type=Path, required=True)
    parser.add_argument('--xray', type=Path, required=True)
    args = parser.parse_args()
    os.umask(0o077)
    args.out.mkdir(mode=0o700, parents=True, exist_ok=False)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'synthetic-app-vpn')])
    now = datetime.datetime.now(datetime.timezone.utc)
    certificate = x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key()).serial_number(x509.random_serial_number()).not_valid_before(now-datetime.timedelta(minutes=5)).not_valid_after(now+datetime.timedelta(days=1)).add_extension(x509.SubjectAlternativeName([x509.DNSName('android.test'), x509.IPAddress(ipaddress.ip_address('10.0.2.2')), x509.IPAddress(ipaddress.ip_address('fd79:fc::1'))]), False).sign(key, hashes.SHA256())
    cert_path = args.out/'routing-ca.pem'
    key_path = args.out/'fixture-key.pem'
    cert_path.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    (args.out/'probe-assets').mkdir()
    (args.out/'probe-assets'/'routing-ca.pem').write_bytes(cert_path.read_bytes())
    key_path.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    tls.minimum_version = ssl.TLSVersion.TLSv1_2
    tls.load_cert_chain(cert_path, key_path)
    records = []
    records_lock = threading.Lock()
    servers = []
    started_servers = []
    children = []
    streams = []
    stop = threading.Event()

    def handler(route):
        class HTTP(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                data = (route+self.path).encode()
                self.send_response(200)
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                with records_lock:
                    records.append(dict(route=route, path=self.path, at=datetime.datetime.now(datetime.timezone.utc).isoformat()))

            def log_message(self, *args):
                pass
        return HTTP

    class DNS(socketserver.BaseRequestHandler):
        def handle(self):
            data, sock = self.request
            try:
                end = 12
                while data[end]:
                    end += data[end]+1
                end += 1
                kind = struct.unpack('!H', data[end:end+2])[0]
                end += 4
                if kind not in (1, 28):
                    return
                value = ipaddress.ip_address(self.server.ipv4 if kind == 1 else 'fd79:fc::1').packed
                answer = data[:2]+b'\x81\x80'+struct.pack('!HHHH', 1, 1, 0, 0)+data[12:end]+b'\xc0\x0c'+struct.pack('!HHIH', kind, 1, 0, len(value))+value
                sock.sendto(answer, self.client_address)
            except (IndexError, struct.error):
                pass

    try:
        for port, route in [(51904, 'DIRECT'), (51905, 'VPN_TCP')]:
            server = RoutingHTTPServer(('127.0.0.1', port), handler(route), tls)
            servers.append(server)
        for address, port, answer in [('127.0.0.1', 51906, '198.19.1.1')]:
            server = socketserver.ThreadingUDPServer((address, port), DNS)
            server.ipv4 = answer
            servers.append(server)
        for server in servers:
            threading.Thread(target=server.serve_forever, daemon=True).start()
            started_servers.append(server)
        profile = 'private_key='+'02'*32+'\nlisten_port=51821\njc=3\njmin=40\njmax=80\ns1=16\ns2=16\ns3=16\ns4=16\nh1=1\nh2=2\nh3=3\nh4=4\nheader_protection_key='+'03'*32+'\ncontent_padding_addition=0-32\nrandom_trailers=true\ndisable_cookies=false\ni1=<b 0x11223344><r 16>\npublic_key=a4e09292b651c278b9772c569f5fa9bb13d906b46ab68c9df9dc2b4409f8a209\nallowed_ip=10.78.0.4/32\nallowed_ip=fd78:92::4/128\n\n'
        error = (args.out/'awg.log').open('wb')
        streams.append(error)
        awg = subprocess.Popen([str(args.awg_peer)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=error, text=True)
        children.append(awg)
        awg.stdin.write(json.dumps(dict(Config=profile, Certificate=str(cert_path), Key=str(key_path))))
        awg.stdin.close()
        ready = queue.Queue()
        threading.Thread(target=lambda: ready.put(awg.stdout.readline()), daemon=True).start()
        assert ready.get(timeout=30).strip() == 'ready'
        config = dict(log=dict(loglevel='warning'), inbounds=[dict(listen='0.0.0.0', port=51900, protocol='vless', settings=dict(clients=[dict(id='11111111-2222-4333-8444-555555555555', flow='xtls-rprx-vision')], decryption='none'), streamSettings=dict(network='raw', security='reality', realitySettings=dict(show=False, target='127.0.0.1:51904', xver=0, serverNames=['android.test'], privateKey='AgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgI', shortIds=['0102030405060708'])))], outbounds=[dict(tag='tls', protocol='freedom', settings=dict(redirect='127.0.0.1:51905')), dict(tag='dns', protocol='freedom', settings=dict(redirect='127.0.0.1:51906'))], routing=dict(rules=[dict(type='field', network='udp', outboundTag='dns')]))
        output = (args.out/'xray.log').open('wb')
        streams.append(output)
        xray = subprocess.Popen([str(args.xray), 'run', '-config', 'stdin:'], stdin=subprocess.PIPE, stdout=output, stderr=subprocess.STDOUT, text=True)
        children.append(xray)
        xray.stdin.write(json.dumps(config))
        xray.stdin.close()
        (args.out/'ready.json').write_text(json.dumps(dict(awg_pid=awg.pid, xray_pid=xray.pid, direct=51904, vpn=51905)))
        signal.signal(signal.SIGTERM, lambda *_: stop.set())
        signal.signal(signal.SIGINT, lambda *_: stop.set())
        while not stop.wait(1):
            assert all(child.poll() is None for child in children), 'FIXTURE_CHILD_EXITED'
    finally:
        for child in children:
            if child.poll() is None:
                child.terminate()
                try:
                    child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait(timeout=5)
        for server in servers:
            if server in started_servers:
                server.shutdown()
            server.server_close()
        for stream in streams:
            stream.close()
        (args.out/'traffic.json').write_text(json.dumps(records, indent=2))


if __name__ == '__main__':
    main()
