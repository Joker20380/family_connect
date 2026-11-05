import argparse
import ipaddress
import json
import os
from pathlib import Path
import signal
import socket
import socketserver
import subprocess
import threading
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--role', choices=('gateway', 'origin'), required=True)
    parser.add_argument('--address', required=True)
    parser.add_argument('--peer', required=True)
    parser.add_argument('--origin-port', type=int, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--seconds', type=int, default=14400)
    args = parser.parse_args()
    assert os.geteuid() == 0 and Path('/.dockerenv').exists()
    assert 0 < args.origin_port < 65536 and 0 < args.seconds <= 32400
    assert ipaddress.ip_address(args.address).is_private and ipaddress.ip_address(args.peer).is_private
    assert args.address != args.peer
    routes = Path('/proc/net/route').read_text().splitlines()[1:]
    assert all(line.split()[1] != '00000000' for line in routes)
    assert {name for _, name in socket.if_nameindex()} == {'lo', 'eth0'}
    public = '185.251.89.19'
    if args.role == 'gateway':
        setup = ['route', 'add', public+'/32', 'via', args.peer]
        cleanup = ['route', 'del', public+'/32', 'via', args.peer]
        listen, target = (args.address, 18443), ('127.0.0.1', args.origin_port)
    else:
        setup = ['addr', 'add', public+'/32', 'dev', 'lo']
        cleanup = ['addr', 'del', public+'/32', 'dev', 'lo']
        listen, target = (public, 8443), (args.peer, 18443)
    subprocess.run(['/busybox', 'ip', *setup], check=True)
    stopped = threading.Event()
    connections = set()
    lock = threading.Lock()
    receipt = dict(scope='internal-Docker-no-external-route-TCP-adapter', role=args.role,
                   started=time.time(), pid=os.getpid(), listen=listen, upstream=target, accepted=0, bytes=0)
    def save():
        args.receipt.write_text(json.dumps(receipt)+'\n')

    class Handler(socketserver.BaseRequestHandler):
        def handle(self):
            with socket.create_connection(target, timeout=5) as upstream:
                upstream.settimeout(None)
                with lock:
                    connections.update((self.request, upstream))
                    receipt['accepted'] += 1
                    save()
                def copy(source, destination):
                    try:
                        while data := source.recv(65536):
                            destination.sendall(data)
                            with lock:
                                receipt['bytes'] += len(data)
                    except OSError:
                        pass
                    finally:
                        try:
                            destination.shutdown(socket.SHUT_WR)
                        except OSError:
                            pass
                receiver = threading.Thread(target=copy, args=(upstream, self.request), daemon=True)
                receiver.start()
                try:
                    copy(self.request, upstream)
                finally:
                    try:
                        upstream.shutdown(socket.SHUT_RDWR)
                    except OSError:
                        pass
                    receiver.join(5)
                    with lock:
                        connections.difference_update((self.request, upstream))
                        save()

    class Server(socketserver.ThreadingTCPServer):
        daemon_threads = True

    try:
        with Server(listen, Handler) as server:
            signal.signal(signal.SIGTERM, lambda *_: stopped.set())
            signal.signal(signal.SIGINT, lambda *_: stopped.set())
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            save()
            try:
                stopped.wait(args.seconds)
            finally:
                server.shutdown()
                with lock:
                    for connection in connections:
                        try:
                            connection.shutdown(socket.SHUT_RDWR)
                        except OSError:
                            pass
                worker.join(5)
    finally:
        subprocess.run(['/busybox', 'ip', *cleanup], check=True)
        receipt['stopped'] = time.time()
        save()


if __name__ == '__main__':
    main()
