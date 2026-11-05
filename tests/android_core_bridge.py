import argparse
import json
import os
from pathlib import Path
import signal
import socket
import socketserver
import subprocess
import threading


BRIDGE = '''import os,socket,sys,threading
connection=socket.create_connection(('127.0.0.1',int(sys.argv[1])),10)
connection.settimeout(None)
def send():
 try:
  while True:
   data=os.read(0,65536)
   if not data:break
   connection.sendall(data)
 finally:
  try:connection.shutdown(socket.SHUT_WR)
  except OSError:pass
threading.Thread(target=send,daemon=True).start()
try:
 while True:
  data=connection.recv(65536)
  if not data:break
  sys.stdout.buffer.write(data);sys.stdout.buffer.flush()
finally:connection.close()
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--container', required=True)
    parser.add_argument('--server', required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--seconds', type=int, default=14400)
    args = parser.parse_args()
    assert args.container.startswith('fc-mesh-android-') and 0 < args.seconds <= 14400
    inspection = json.loads(subprocess.check_output(['docker', 'inspect', args.container]))[0]
    assert inspection['State']['Running']
    if inspection['HostConfig']['NetworkMode'] != 'none':
        networks = inspection['NetworkSettings']['Networks']
        assert len(networks) == 1
        isolated = json.loads(subprocess.check_output(['docker', 'network', 'inspect', next(iter(networks))]))[0]
        assert isolated['Internal'] and isolated['Labels'].get('family_connect.qualification') == 'android-core'
    state = json.loads(subprocess.check_output(['docker', 'exec', args.container, 'cat', args.server]))
    assert state['state'] == 'HTTP_READY'
    stopped = threading.Event()
    children = set()
    lock = threading.Lock()

    def forward(connection, target):
        assert target.startswith('127.0.0.1:')
        process = subprocess.Popen(['docker', 'exec', '-i', args.container, 'python', '-u', '-c', BRIDGE,
            target.split(':')[1]], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        with lock:
            children.add(process)
        def receive():
            try:
                while True:
                    data = process.stdout.read1(65536)
                    if not data:
                        break
                    connection.sendall(data)
            except OSError:
                pass
            finally:
                try:
                    connection.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
        thread = threading.Thread(target=receive, daemon=True)
        thread.start()
        try:
            while not stopped.is_set():
                data = connection.recv(65536)
                if not data:
                    break
                process.stdin.write(data)
                process.stdin.flush()
        except OSError:
            pass
        finally:
            try:
                process.stdin.close()
            except OSError:
                pass
            if process.poll() is None:
                process.terminate()
            process.wait(timeout=10)
            thread.join(10)
            with lock:
                children.discard(process)

    class Relay(socketserver.BaseRequestHandler):
        def handle(self):
            forward(self.request, state['relay'])

    class HTTPS(socketserver.BaseRequestHandler):
        def handle(self):
            self.request.settimeout(10)
            header = bytearray()
            while not header.endswith(b'\r\n\r\n'):
                data = self.request.recv(1)
                if not data or len(header) > 8192:
                    return
                header.extend(data)
            if bytes(header).split(b'\r\n')[0] not in (b'CONNECT 185.251.89.19:8443 HTTP/1.1', b'CONNECT 185.251.89.19:8443 HTTP/1.0'):
                self.request.sendall(b'HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\n\r\n')
                return
            self.request.sendall(b'HTTP/1.1 200 Connection established\r\n\r\n')
            self.request.settimeout(None)
            forward(self.request, state['https'])

    class Server(socketserver.ThreadingTCPServer):
        daemon_threads = True

    servers = [Server(('127.0.0.1', 0), handler) for handler in (Relay, HTTPS)]
    threads = [threading.Thread(target=server.serve_forever, daemon=True) for server in servers]
    for thread in threads:
        thread.start()
    args.receipt.write_text(json.dumps(dict(container=args.container, relay=servers[0].server_address[1],
        https_proxy=servers[1].server_address[1], source=state['source'], pid=os.getpid(),
        actual_remote='network-none container loopback only'))+'\n')
    for event in (signal.SIGTERM, signal.SIGINT):
        signal.signal(event, lambda *_: stopped.set())
    try:
        stopped.wait(args.seconds)
    finally:
        stopped.set()
        for server in servers:
            server.shutdown()
            server.server_close()
        with lock:
            for process in children:
                process.terminate()
        for thread in threads:
            thread.join(10)


if __name__ == '__main__':
    main()
