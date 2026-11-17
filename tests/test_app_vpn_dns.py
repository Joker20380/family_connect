import contextlib
import importlib.util
import json
import os
from pathlib import Path
import socket
import socketserver
import struct
import subprocess
import threading

import pytest


ROOT = Path(__file__).resolve().parents[1]


def load(relative):
    spec = importlib.util.spec_from_file_location('routing_fixture', ROOT/relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


FIXTURE = load('pilot/android-app-vpn/fixture.py')


def query(kind):
    return b'\x12\x34\x01\x00\x00\x01'+bytes(6)+b'\x07example\x03com\x00'+struct.pack('!HH', kind, 1)


def read_exact(connection, length):
    result = b''
    while len(result) < length:
        chunk = connection.recv(length-len(result))
        if not chunk:
            break
        result += chunk
    return result


@contextlib.contextmanager
def server(server_type, handler):
    instance = server_type(('127.0.0.1', 0), handler)
    instance.record_dns = lambda *args: None
    worker = threading.Thread(target=instance.serve_forever, kwargs={'poll_interval': .02})
    worker.start()
    try:
        yield instance
    finally:
        instance.shutdown()
        instance.server_close()
        worker.join(timeout=3)
        assert not worker.is_alive()


@pytest.mark.parametrize('kind', [1, 28])
def test_udp_and_fragmented_tcp_dns_return_same_answer(kind):
    question = query(kind)
    expected = FIXTURE.dns_answer(question)[1]
    assert expected[:2] == b'\x12\x34'
    address = socket.inet_aton('198.19.1.1') if kind == 1 else socket.inet_pton(socket.AF_INET6, 'fd79:fc::1')
    assert expected.endswith(address)
    with server(socketserver.ThreadingUDPServer, FIXTURE.DNSDatagram) as udp:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as connection:
            connection.settimeout(2)
            connection.sendto(question, udp.server_address)
            assert connection.recv(4096) == expected
    with server(FIXTURE.DNSStreamServer, FIXTURE.DNSStream) as tcp:
        with socket.create_connection(tcp.server_address, timeout=3) as connection:
            frame = struct.pack('!H', len(question))+question
            connection.sendall(frame[:1])
            connection.sendall(frame[1:])
            assert read_exact(connection, 2+len(expected)) == struct.pack('!H', len(expected))+expected
            connection.sendall(frame)
            assert read_exact(connection, 2+len(expected)) == struct.pack('!H', len(expected))+expected


@pytest.mark.parametrize('question', [b'', query(15), query(1)[:-1], query(1)[:12]+b'\xc0\x0c', bytes(4097)])
def test_invalid_questions_are_not_synthetic_success(question):
    assert FIXTURE.dns_answer(question) is None


@pytest.mark.parametrize('frame', [b'\xff\xff', b'\x00', b'\x00\x20partial'])
def test_bad_or_stalled_tcp_client_is_closed_and_joined(frame):
    with server(FIXTURE.DNSStreamServer, FIXTURE.DNSStream) as tcp:
        with socket.create_connection(tcp.server_address, timeout=3) as connection:
            connection.sendall(frame)
            assert connection.recv(1) == b''


def test_real_pinned_xray_routes_dns_not_https(tmp_path):
    binary = os.environ.get('FC_APP_VPN_XRAY')
    if not binary:
        pytest.skip('Explicit pinned Xray executable required; mandatory in Client builds')
    assert Path(binary).is_file()
    readiness = load('pilot/android-tcp/readiness.py')

    class NotDNS(socketserver.BaseRequestHandler):
        def handle(self):
            self.request.sendall(b'NOT_DNS')

    with server(FIXTURE.DNSStreamServer, FIXTURE.DNSStream) as dns, server(socketserver.ThreadingTCPServer, NotDNS) as tls:
        for repaired in (False, True):
            with socket.socket() as reserved:
                reserved.bind(('0.0.0.0', 0))
                port = reserved.getsockname()[1]
            config = dict(log=dict(loglevel='warning'),
                          inbounds=[dict(listen='0.0.0.0', port=port, protocol='socks', settings=dict(auth='noauth'))],
                          outbounds=[dict(tag='tls', protocol='freedom', settings=dict(redirect='127.0.0.1:'+str(tls.server_address[1]))),
                                     dict(tag='dns', protocol='freedom', settings=dict(redirect='127.0.0.1:'+str(dns.server_address[1]))),
                                     dict(tag='unsupported-dot', protocol='blackhole')],
                          routing=dict(rules=FIXTURE.dns_routes() if repaired else [dict(type='field', network='udp', outboundTag='dns')]))
            with (tmp_path/f'xray-{repaired}.log').open('wb') as log:
                child = subprocess.Popen([binary, 'run', '-config', 'stdin:'], stdin=subprocess.PIPE, stdout=log, stderr=log)
                try:
                    child.stdin.write(json.dumps(config).encode())
                    child.stdin.close()
                    readiness.wait_ready(child, port, readiness.Receipt(tmp_path/f'ownership-{repaired}.json'), timeout=5)
                    for destination in (53, 853, 51904):
                        with socket.create_connection(('127.0.0.1', port), timeout=3) as connection:
                            connection.sendall(b'\x05\x01\x00')
                            assert read_exact(connection, 2) == b'\x05\x00'
                            connection.sendall(b'\x05\x01\x00\x01'+socket.inet_aton('1.1.1.1')+struct.pack('!H', destination))
                            reply = read_exact(connection, 10)
                            assert reply[:4] == b'\x05\x00\x00\x01'
                            if repaired and destination == 53:
                                question = query(1)
                                answer = FIXTURE.dns_answer(question)[1]
                                connection.sendall(struct.pack('!H', len(question))+question)
                                assert read_exact(connection, 2+len(answer)) == struct.pack('!H', len(answer))+answer
                            elif repaired and destination == 853:
                                assert connection.recv(1) == b''
                            else:
                                assert read_exact(connection, 7) == b'NOT_DNS'
                finally:
                    if child.poll() is None:
                        child.terminate()
                    child.wait(timeout=5)
                assert not readiness.listening_inodes('self', port)


def test_client_ci_requires_real_xray_fixture_regression():
    from scripts.client_ci_scope import platforms
    workflow = (ROOT/'.github/workflows/clients.yml').read_text()
    for name in ('tests/test_app_vpn_dns.py', 'tests/test_app_vpn_fixture.py'):
        assert platforms([name])['android']
        assert workflow.count("'"+name+"'") == 2
    assert 'FC_APP_VPN_XRAY: ${{ github.workspace }}/clients/android/awg-generated/xray-peer' in workflow
    assert 'tests/test_app_vpn_fixture.py tests/test_app_vpn_dns.py' in workflow
