"""Loopback-only XHTTP/TLS acceptance using a supplied Xray binary. No phone/TUN or live keys."""
import argparse
from contextlib import contextmanager
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import threading
import time

from clients.desktop.profile_config import tcp_config
from scripts.xhttp_gateway_config import origin_config

PROFILE = dict(type='vless-xhttp-tls-v1', server='192.0.2.1', port=443,
    id='00000000-0000-4000-8000-000000000001', server_name='edge.example.com',
    path='/fc_test_only_path_1234/', mode='packet-up')


def port():
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0)); return s.getsockname()[1]


def run(*args, env=None):
    p = subprocess.run(args, capture_output=True, env=env, timeout=20)
    if p.returncode: raise RuntimeError('Lab subprocess failed: '+Path(args[0]).name)
    return p.stdout


@contextmanager
def process(binary, config, root, name, env, listen):
    path = root/(name+'.json'); path.write_text(json.dumps(config)); path.chmod(0o600)
    run(str(binary), 'run', '-test', '-config', str(path), env=env)
    p = subprocess.Popen([str(binary), 'run', '-config', str(path)], env=env,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        deadline = time.monotonic()+5
        while True:
            if p.poll() is not None: raise RuntimeError('Xray lab process exited')
            try:
                with socket.create_connection(('127.0.0.1', listen), timeout=.1): break
            except OSError:
                if time.monotonic() >= deadline: raise RuntimeError('Xray lab start timeout')
                time.sleep(.05)
        yield
    finally:
        if p.poll() is None:
            p.terminate()
            try: p.wait(timeout=5)
            except subprocess.TimeoutExpired: p.kill(); p.wait(timeout=5)


def check(binary, client_binary=None):
    class Echo(BaseHTTPRequestHandler):
        def do_POST(self):
            data = self.rfile.read(int(self.headers['Content-Length']))
            response = data
            self.send_response(200); self.send_header('Content-Length', str(len(response)))
            self.end_headers(); self.wfile.write(response)
        def log_message(self, *args): pass
    echo = ThreadingHTTPServer(('127.0.0.1', 0), Echo)
    thread = threading.Thread(target=echo.serve_forever, daemon=True); thread.start()
    results = {}
    try:
        with tempfile.TemporaryDirectory(prefix='fc-xhttp-lab-') as folder:
            root = Path(folder)
            run('openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-days', '1',
                '-subj', '/CN=Family Connect disposable lab', '-keyout', str(root/'key.pem'),
                '-out', str(root/'cert.pem'), '-addext', 'subjectAltName=DNS:edge.example.com')
            (root/'key.pem').chmod(0o600)
            payload = b'Family Connect synthetic XHTTP traffic\n'*32768
            (root/'payload').write_bytes(payload)
            server_port, socks_port = port(), port()
            server = origin_config(PROFILE, server_port)
            # Test-only overrides: TLS directly in core, isolated local echo destination allowed.
            server.pop('routing'); server['outbounds'] = [{'protocol':'freedom'}]
            stream = server['inbounds'][0]['streamSettings']; stream['security'] = 'tls'
            stream['tlsSettings'] = {'alpn':['h2'], 'certificates':[{
                'certificateFile':str(root/'cert.pem'), 'keyFile':str(root/'key.pem')}]}
            env = {**os.environ, 'SSL_CERT_FILE':str(root/'cert.pem')}
            with process(binary, server, root, 'origin', env, server_port):
                for case in ('valid', 'wrong-name', 'untrusted-cert', 'wrong-id', 'wrong-path'):
                    client = tcp_config(PROFILE, 'fctcp12345678')
                    client['inbounds'] = [{'listen':'127.0.0.1','port':socks_port,
                        'protocol':'socks','settings':{'auth':'noauth','udp':False}}]
                    outbound = client['outbounds'][0]
                    target = outbound['settings']['vnext'][0]; target['address']='127.0.0.1'; target['port']=server_port
                    stream = outbound['streamSettings']; stream.pop('sockopt')
                    if case == 'wrong-name': stream['tlsSettings']['serverName']='wrong.example.com'
                    if case == 'wrong-id': target['users'][0]['id']='00000000-0000-4000-8000-000000000002'
                    if case == 'wrong-path': stream['xhttpSettings']['path']='/fc_other_test_path_1234/'
                    client_env = {**env, 'SSL_CERT_FILE':'/dev/null'} if case == 'untrusted-cert' else env
                    with process(client_binary or binary, client, root, case, client_env, socks_port):
                        p = subprocess.run(['curl','--silent','--show-error','--fail','--max-time','4',
                            '--noproxy','', '--proxy',f'socks5h://127.0.0.1:{socks_port}',
                            '--data-binary','@'+str(root/'payload'),f'http://127.0.0.1:{echo.server_port}/echo'],
                            capture_output=True, timeout=8)
                    success = p.returncode == 0 and p.stdout == payload
                    results[case] = success if case == 'valid' else not success
                    if not results[case]: raise RuntimeError('XHTTP acceptance failed: '+case)
            results['payload_bytes_each_direction'] = len(payload)
            results['xray_sha256'] = hashlib.sha256(binary.read_bytes()).hexdigest()
    finally:
        echo.shutdown(); echo.server_close(); thread.join(timeout=2)
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--xray', required=True, type=Path)
    parser.add_argument('--client-binary', type=Path, help='Optional host-built Android bridge test driver')
    args = parser.parse_args()
    print(json.dumps(check(args.xray.resolve(), args.client_binary.resolve() if args.client_binary else None), indent=2))
