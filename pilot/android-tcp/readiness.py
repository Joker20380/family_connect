"""Linux-only ownership barrier for the disposable REALITY peer, not VPN readiness."""
import contextlib
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import threading
import time


class Receipt:
    def __init__(self, destination):
        self.destination = destination
        self.events = []

    def record(self, event, **fields):
        if len(self.events) >= 64:
            raise RuntimeError('TCP fixture lifecycle receipt overflow')
        self.events.append(dict(event=event, monotonic=time.monotonic(), **fields))
        self.destination.write_text(json.dumps(dict(schema=1, events=self.events), indent=2) + '\n')


def listening_inodes(pid, port, any_address=False):
    found = set()
    for table, address in (('tcp', '00000000'), ('tcp6', '0' * 32)):
        for line in Path(f'/proc/{pid}/net/{table}').read_text().splitlines()[1:]:
            fields = line.split()
            if fields[3] == '0A' and fields[1].endswith(f':{port:04X}'):
                if any_address or fields[1] == f'{address}:{port:04X}':
                    found.add(fields[9])
    return found


def owned_listener(process, port):
    if process.poll() is not None:
        return set()
    try:
        listeners = listening_inodes(process.pid, port)
        descriptors = set()
        for descriptor in Path(f'/proc/{process.pid}/fd').iterdir():
            try:
                target = os.readlink(descriptor)
            except FileNotFoundError:
                continue
            if target.startswith('socket:['):
                descriptors.add(target[8:-1])
        if listening_inodes(process.pid, port, any_address=True) - descriptors:
            return set()
        return listeners & descriptors if process.poll() is None else set()
    except FileNotFoundError:
        return set()


def require_ready(process, port, receipt):
    inodes = owned_listener(process, port)
    if not inodes:
        receipt.record('not_ready', pid=process.pid, returncode=process.poll(), port=port)
        raise RuntimeError(f'REALITY peer does not own LISTEN 0.0.0.0:{port}; '
                           f'pid={process.pid} returncode={process.poll()}; see android-tcp-peer.log')
    try:
        with socket.create_connection(('127.0.0.1', port), timeout=.2):
            if owned_listener(process, port) != inodes:
                raise RuntimeError('REALITY listener ownership changed during IPv4 probe')
    except OSError as error:
        receipt.record('ipv4_probe_failed', pid=process.pid, port=port, errno=error.errno)
        raise RuntimeError('REALITY owned listener does not accept IPv4') from error
    receipt.record('owned_listener', pid=process.pid, port=port, inodes=sorted(inodes))


def wait_ready(process, port, receipt, timeout=15):
    deadline = time.monotonic() + timeout
    wake = threading.Event()
    while True:
        if process.poll() is not None:
            receipt.record('early_exit', pid=process.pid, returncode=process.returncode, port=port)
            raise RuntimeError(f'REALITY peer exited before readiness: pid={process.pid} '
                               f'returncode={process.returncode} endpoint=0.0.0.0:{port}; '
                               'see android-tcp-peer.log')
        if owned_listener(process, port):
            require_ready(process, port, receipt)
            return
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            receipt.record('readiness_timeout', pid=process.pid, port=port,
                           observed_inodes=sorted(listening_inodes('self', port)))
            raise RuntimeError(f'REALITY peer readiness timeout: pid={process.pid} '
                               f'expected owned LISTEN 0.0.0.0:{port}; see android-tcp-peer.log')
        wake.wait(min(.05, remaining))


@contextlib.contextmanager
def reserve_endpoint(port, receipt):
    with socket.socket() as reservation:
        try:
            reservation.bind(('0.0.0.0', port))
        except OSError as error:
            receipt.record('reservation_failed', port=port, errno=error.errno)
            raise RuntimeError(f'TCP fixture endpoint 0.0.0.0:{port} unavailable; '
                               f'errno={error.errno}; no foreign process terminated') from error
        receipt.record('reserved', port=reservation.getsockname()[1])
        yield reservation


@contextlib.contextmanager
def running_server(server, receipt, label):
    thread = threading.Thread(target=server.serve_forever, kwargs={'poll_interval': .05},
                              name=f'fc-tcp-fixture-{label}')
    try:
        thread.start()
        receipt.record('server_started', label=label, port=server.server_address[1])
        yield server
    finally:
        if thread.ident is not None:
            server.shutdown()
            thread.join(timeout=5)
        server.server_close()
        receipt.record('server_closed', label=label, thread_alive=thread.is_alive())
        if thread.is_alive():
            raise RuntimeError(f'TCP fixture {label} thread did not join')


@contextlib.contextmanager
def running_peer(command, config, root, port, receipt):
    with (root / 'android-tcp-peer.log').open('w') as log:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=log,
                                   stderr=subprocess.STDOUT, text=True)
        try:
            receipt.record('spawned', pid=process.pid, port=port,
                           binary_sha256=hashlib.sha256(Path(command[0]).read_bytes()).hexdigest())
            with process.stdin:
                process.stdin.write(json.dumps(config))
            wait_ready(process, port, receipt)
            yield process
        finally:
            if not process.stdin.closed:
                process.stdin.close()
            receipt.record('peer_stopping', pid=process.pid, returncode=process.poll())
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
            process.wait(timeout=10)
            receipt.record('peer_reaped', pid=process.pid, returncode=process.returncode)
