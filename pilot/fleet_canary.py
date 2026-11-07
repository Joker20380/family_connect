"""Disposable native data-plane fixture. Never install on a production gateway."""
import base64
from datetime import datetime, timedelta, timezone
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import ipaddress
import json
import os
from pathlib import Path
import secrets
import socket
import ssl
import struct
import subprocess
import sys
import threading
import time
import uuid

ROOT = Path('/run/fc-canary')
DOMAIN = 'origin.canary.test'
TUNNEL = '10.254.253.2'
NATIVE = {
    'amneziawg-go': 'e7f00e47d6df853ade5dcd2fe79240f01ff897d75088c768316a444c27c87e0f',
    'awg': '906d6795af1dd4adee7b11bf1e7fa133d4795c8a8d6e2099b34a026f810a3278',
    'xray': '4f7a4436f86798bbb5c875014e352021a1673710a45e170ccc507c5f59341940',
}


def require(condition):
    if not condition:
        raise ValueError('isolated canary gate rejected')


def stage(name):
    (ROOT / 'stage').write_text(name)


def private_address(value):
    address = ipaddress.IPv4Address(value)
    require(address.is_private and not address.is_loopback and not address.is_link_local
        and not address.is_unspecified and not address.is_multicast)
    return str(address)


def run(arguments, *, data=None, timeout=15, check=True):
    result = subprocess.run(arguments, input=data, capture_output=True, timeout=timeout)
    if check:
        require(result.returncode == 0)
    return result


def secret(name, raw):
    descriptor = os.open(ROOT / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'wb') as handle:
        handle.write(raw)


def keypair():
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
    from cryptography.hazmat.primitives import serialization
    key = X25519PrivateKey.generate()
    return (key.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption()),
        key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw))


def urlkey(raw):
    return base64.urlsafe_b64encode(raw).decode().rstrip('=')


def material(spec):
    require(set(spec) == {'origin', 'gateway', 'egress', 'certificate'})
    origin, gateway, egress = (private_address(spec[name]) for name in ('origin', 'gateway', 'egress'))
    require(len({origin, gateway, egress}) == 3)
    awg_private, awg_public = keypair()
    client_private, client_public = keypair()
    reality_private, reality_public = keypair()
    padding = base64.b64encode(secrets.token_bytes(32)).decode()
    parameters = ('Jc = 4\nJmin = 40\nJmax = 70\nS1 = 81\nS2 = 93\nS3 = 17\nS4 = 23\n'
        'H1 = 1\nH2 = 2\nH3 = 3\nH4 = 4\nHeaderProtectionKey = ' + padding + '\nContentPaddingAddition = 0-32\n')
    server_awg = ('[Interface]\nPrivateKey = ' + base64.b64encode(awg_private).decode() + '\nListenPort = 51823\n'
        + parameters + '[Peer]\nPublicKey = ' + base64.b64encode(client_public).decode() + '\nAllowedIPs = ' + TUNNEL + '/32\n')
    client_awg = ('[Interface]\nPrivateKey = ' + base64.b64encode(client_private).decode() + '\n' + parameters
        + '[Peer]\nPublicKey = ' + base64.b64encode(awg_public).decode() + '\nEndpoint = ' + gateway
        + ':51823\nAllowedIPs = ' + origin + '/32\n')
    identity, short_id = str(uuid.uuid4()), secrets.token_hex(8)
    server_tcp = dict(log=dict(loglevel='none'), dns=dict(servers=[origin], queryStrategy='UseIPv4'),
        inbounds=[dict(listen='0.0.0.0', port=443, protocol='vless',
            settings=dict(clients=[dict(id=identity, flow='xtls-rprx-vision')], decryption='none'),
            streamSettings=dict(network='tcp', security='reality', realitySettings=dict(
                dest=origin + ':443', serverNames=[DOMAIN], privateKey=urlkey(reality_private), shortIds=[short_id])))],
        outbounds=[dict(protocol='freedom', settings=dict(domainStrategy='UseIPv4'))])
    client_tcp = dict(log=dict(loglevel='none'), inbounds=[dict(listen='127.0.0.1', port=19728,
        protocol='socks', settings=dict(auth='noauth', udp=False))], outbounds=[dict(protocol='vless',
        settings=dict(vnext=[dict(address=gateway, port=443, users=[dict(id=identity, flow='xtls-rprx-vision', encryption='none')])]),
        streamSettings=dict(network='tcp', security='reality', realitySettings=dict(fingerprint='chrome',
            serverName=DOMAIN, password=urlkey(reality_public), shortId=short_id)))])
    return server_awg.encode(), server_tcp, dict(spec, awg=client_awg,
        server_public=base64.b64encode(awg_public).decode(), tcp=client_tcp)


def launch(name, arguments):
    require(not (ROOT / (name + '.pid')).exists())
    process = subprocess.Popen(arguments, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    secret(name + '.pid', str(process.pid).encode())
    time.sleep(.3)
    require(process.poll() is None)


def stop(name):
    path = ROOT / (name + '.pid')
    if path.exists():
        process = int(path.read_text())
        try:
            os.kill(process, 15)
        except ProcessLookupError:
            pass
        for attempt in range(30):
            status = Path('/proc', str(process), 'stat')
            if not status.exists() or status.read_text().split()[2] == 'Z':
                break
            time.sleep(.1)
        else:
            os.kill(process, 9)
        path.unlink()


def wait_for(arguments):
    for attempt in range(50):
        if run(arguments, check=False).returncode == 0:
            return
        time.sleep(.1)
    require(False)


def origin_setup(address):
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    private_address(address)
    key = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, DOMAIN)])
    now = datetime.now(timezone.utc)
    certificate = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
        .serial_number(x509.random_serial_number()).not_valid_before(now - timedelta(minutes=1))
        .not_valid_after(now + timedelta(days=1)).add_extension(x509.SubjectAlternativeName([x509.DNSName(DOMAIN)]), critical=False)
        .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True).sign(key, hashes.SHA256()))
    secret('tls.key', key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    secret('tls.crt', certificate.public_bytes(serialization.Encoding.PEM))
    secret('origin-address', address.encode())
    launch('origin', [sys.executable, __file__, 'serve-origin'])
    return certificate.public_bytes(serialization.Encoding.PEM).decode()


def dns_response(packet, address):
    require(len(packet) >= 17 and struct.unpack('!H', packet[4:6])[0] == 1)
    offset, labels = 12, []
    while packet[offset]:
        length = packet[offset]
        require(0 < length <= 63 and offset + length + 1 < len(packet))
        labels.append(packet[offset + 1:offset + 1 + length].decode('ascii').lower())
        offset += length + 1
    end = offset + 5
    require(len(packet) >= end)
    kind, group = struct.unpack('!HH', packet[offset + 1:end])
    matched = '.'.join(labels) == DOMAIN and kind == 1 and group == 1
    header = packet[:2] + struct.pack('!HHHHH', 0x8180, 1, int(matched), 0, 0)
    answer = b'\xc0\x0c' + struct.pack('!HHIH', 1, 1, 1, 4) + socket.inet_aton(address) if matched else b''
    return header + packet[12:end] + answer


def serve_origin():
    address = (ROOT / 'origin-address').read_text()
    counts = dict(dns=0, https=0)
    lock = threading.Lock()

    def persist():
        (ROOT / 'counts.json').write_text(json.dumps(counts))

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            with lock:
                counts['https'] += 1
                persist()
            raw = json.dumps(dict(path=self.path, peer=self.client_address[0])).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def log_message(self, *arguments):
            pass

    def dns():
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as listener:
            listener.bind(('0.0.0.0', 53))
            while True:
                packet, peer = listener.recvfrom(4096)
                try:
                    answer = dns_response(packet, address)
                except (ValueError, IndexError, UnicodeError, struct.error):
                    continue
                with lock:
                    counts['dns'] += 1
                    persist()
                listener.sendto(answer, peer)

    server = ThreadingHTTPServer(('0.0.0.0', 443), Handler)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = context.maximum_version = ssl.TLSVersion.TLSv1_3
    context.load_cert_chain(ROOT / 'tls.crt', ROOT / 'tls.key')
    server.socket = context.wrap_socket(server.socket, server_side=True, do_handshake_on_connect=False)
    persist()
    threading.Thread(target=dns, daemon=True).start()
    server.serve_forever()


def prepare_gateway(spec):
    stage('gateway-material')
    awg, tcp, client = material(spec)
    secret('server.awg', awg)
    secret('server.json', json.dumps(tcp).encode())
    stage('gateway-tcp-config')
    run(['/native/xray', 'run', '-test', '-config', str(ROOT / 'server.json')])
    stage('gateway-tcp-start')
    launch('server-tcp', ['/native/xray', 'run', '-config', str(ROOT / 'server.json')])
    stage('gateway-awg-start')
    launch('server-awg', ['/native/amneziawg-go', '-f', 'fcprobe0'])
    stage('gateway-awg-ready')
    wait_for(['ip', 'link', 'show', 'fcprobe0'])
    stage('gateway-awg-config')
    run(['/native/awg', 'setconf', 'fcprobe0', str(ROOT / 'server.awg')])
    stage('gateway-interface')
    run(['ip', 'address', 'add', '10.254.253.1/30', 'dev', 'fcprobe0'])
    run(['ip', 'link', 'set', 'fcprobe0', 'mtu', '1280', 'up'])
    rules = ('table ip fc_canary {\n chain postrouting {\n type nat hook postrouting priority srcnat;\n '
        'ip saddr 10.254.253.0/30 ip daddr ' + client['origin'] + ' masquerade\n }\n}\n')
    stage('gateway-nat')
    run(['nft', '-f', '-'], data=rules.encode())
    return client


def curl(options, nonce, success, expected_peer):
    result = run(['curl', '--silent', '--show-error', '--fail', '--max-time', '6', '--connect-timeout', '3',
        '--cacert', str(ROOT / 'origin.crt'), '--proxy', '', '--noproxy', '', *options,
        'https://' + DOMAIN + '/canary/' + nonce], check=False, timeout=10)
    if success:
        require(result.returncode == 0)
        require(json.loads(result.stdout) == dict(path='/canary/' + nonce, peer=expected_peer))
    else:
        require(result.returncode != 0)


def exercise(client):
    origin, gateway, egress = (private_address(client[name]) for name in ('origin', 'gateway', 'egress'))
    secret('origin.crt', client['certificate'].encode())
    nonce = secrets.token_hex(16)
    stage('direct-bypass')
    run(['ip', 'route', 'add', 'unreachable', origin + '/32'])
    curl(['--resolve', DOMAIN + ':443:' + origin], nonce, False, egress)
    results = dict(direct_bypass='REJECTED')
    for name, modify in [('wrong-identity', 'id'), ('wrong-server-key', 'password'), ('valid', None)]:
        stage('tcp-' + name)
        config = json.loads(json.dumps(client['tcp']))
        if modify == 'id':
            config['outbounds'][0]['settings']['vnext'][0]['users'][0]['id'] = str(uuid.uuid4())
        elif modify == 'password':
            config['outbounds'][0]['streamSettings']['realitySettings']['password'] = urlkey(keypair()[1])
        path = name + '.json'
        secret(path, json.dumps(config).encode())
        run(['/native/xray', 'run', '-test', '-config', str(ROOT / path)])
        launch('client-tcp', ['/native/xray', 'run', '-config', str(ROOT / path)])
        try:
            curl(['--socks5-hostname', '127.0.0.1:19728'], nonce, name == 'valid', egress)
            results['tcp_' + name] = 'DNS_TLS_HTTPS_EGRESS_PASS' if name == 'valid' else 'REJECTED'
        finally:
            stop('client-tcp')
    results['tcp_cleanup'] = 'PASS'
    stage('awg-start')
    launch('client-awg', ['/native/amneziawg-go', '-f', 'fcprobe0'])
    try:
        wait_for(['ip', 'link', 'show', 'fcprobe0'])
        run(['ip', 'address', 'add', TUNNEL + '/30', 'dev', 'fcprobe0'])
        run(['ip', 'link', 'set', 'fcprobe0', 'mtu', '1280', 'up'])
        run(['ip', 'route', 'replace', origin + '/32', 'dev', 'fcprobe0'])
        wrong_public = base64.b64encode(keypair()[1]).decode()
        secret('wrong.awg', client['awg'].replace(client['server_public'], wrong_public).encode())
        run(['/native/awg', 'setconf', 'fcprobe0', str(ROOT / 'wrong.awg')])
        stage('awg-wrong-server-key')
        curl(['--interface', TUNNEL, '--resolve', DOMAIN + ':443:' + origin], nonce, False, egress)
        results['awg_wrong-server-key'] = 'REJECTED'
        run(['/native/awg', 'set', 'fcprobe0', 'peer', wrong_public, 'remove'])
        secret('valid.awg', client['awg'].encode())
        started = int(time.time())
        run(['/native/awg', 'setconf', 'fcprobe0', str(ROOT / 'valid.awg')])
        stage('awg-dns')
        answer = run(['dig', '+short', '+tries=1', '+time=3', '-b', TUNNEL, '@' + origin, DOMAIN, 'A']).stdout.decode().strip()
        require(answer == origin)
        stage('awg-https-handshake')
        curl(['--interface', TUNNEL, '--resolve', DOMAIN + ':443:' + answer], nonce, True, egress)
        handshake = run(['/native/awg', 'show', 'fcprobe0', 'latest-handshakes']).stdout.decode().split()
        require(len(handshake) == 2 and handshake[0] == client['server_public'] and started <= int(handshake[1]) <= time.time())
        transfer = run(['/native/awg', 'show', 'fcprobe0', 'transfer']).stdout.decode().split()
        require(len(transfer) == 3 and transfer[0] == client['server_public'] and all(int(value) > 0 for value in transfer[1:]))
        results['awg_valid'] = 'HANDSHAKE_DNS_TLS_HTTPS_NAT_PASS'
    finally:
        stop('client-awg')
        if run(['ip', 'link', 'show', 'fcprobe0'], check=False).returncode == 0:
            run(['ip', 'link', 'delete', 'fcprobe0'])
    stage('operator-cleanup')
    run(['ip', 'route', 'replace', 'unreachable', origin + '/32'])
    curl(['--resolve', DOMAIN + ':443:' + origin], nonce, False, egress)
    results['post_cleanup_bypass'] = 'REJECTED'
    require(run(['ip', 'link', 'show', 'fcprobe0'], check=False).returncode != 0)
    require(run(['ss', '-H', '-ltn', 'sport = :19728']).stdout == b'')
    results['operator_cleanup'] = 'PASS'
    return results


def main():
    os.umask(0o077)
    require(Path('/.dockerenv').is_file() and os.geteuid() == 0)
    require(all(hashlib.sha256(Path('/native', name).read_bytes()).hexdigest() == digest for name, digest in NATIVE.items()))
    ROOT.mkdir(mode=0o700, exist_ok=True)
    action = sys.argv[1:]
    if action == ['serve-origin']:
        serve_origin()
        return
    if action == ['metadata']:
        result = dict(native=NATIVE, python=sys.version.split()[0])
    else:
        value = json.loads(sys.stdin.buffer.read(65537))
        if action == ['origin']:
            result = origin_setup(value['address'])
        elif action == ['gateway']:
            result = prepare_gateway(value)
        elif action == ['client']:
            result = exercise(value)
        else:
            raise ValueError('unknown action')
    print(json.dumps(result))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        print(json.dumps(dict(result='ISOLATED_CANARY_FAILED', stage=(ROOT / 'stage').read_text()
            if (ROOT / 'stage').exists() else 'setup')))
        sys.exit(1)
