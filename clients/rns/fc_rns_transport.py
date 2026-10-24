"""RNS 1.5.1 byte transport for Android. No device secrets, proofs or VPN policy here."""
import base64
import importlib
import ipaddress
import pathlib
import signal
import socket
import threading
import time

import RNS
from RNS.Interfaces.TCPInterface import TCPClientInterface

_runtime = None
_runtime_lock = threading.Lock()
_session_lock = threading.Lock()
_readiness_paths = frozenset('/friends/restricted-readiness' + suffix for suffix in
                             ('', '/challenge', '/ack-challenge', '/ack'))


class TransportUnavailable(OSError):
    pass


def readiness_open(*args):
    try:
        return ['AVAILABLE', Channel(*args)]
    except TransportUnavailable:
        return ['UNAVAILABLE', None]


def initialize(directory):
    global _runtime
    with _runtime_lock:
        if _runtime is not None:
            return
        root = pathlib.Path(directory)
        root.mkdir(mode=0o700, parents=True, exist_ok=True)
        # App-owned config: no shared instance, discovery, listener or caller-supplied config.
        (root / 'config').write_text('[reticulum]\nshare_instance = No\nenable_transport = No\n'
                                   '[logging]\nloglevel = -1\n[interfaces]\n')
        module = importlib.import_module('RNS.Reticulum')
        original = module.signal
        class AppSignals:
            SIGINT = signal.SIGINT
            SIGTERM = signal.SIGTERM
            @staticmethod
            def signal(*args):
                pass  # Android process lifecycle belongs to Java, not RNS signal handlers.
        try:
            module.signal = AppSignals
            _runtime = RNS.Reticulum(configdir=str(root), loglevel=-1)
        finally:
            module.signal = original


class Channel:
    def __init__(self, directory, host, port, provider_b64, callbacks):
        self.callbacks = callbacks
        self.interface = self.link = self.sock = None
        self.locked = False
        address = ipaddress.ip_address(str(host))  # No DNS via an accidental VPN resolver.
        port = int(port)
        public = base64.b64decode(str(provider_b64), validate=True)
        if len(public) != 64 or not 1 <= port <= 65535:
            raise ValueError('Invalid relay bootstrap')
        if not _session_lock.acquire(blocking=False):
            raise OSError('RNS session already active')
        self.locked = True
        try:
            initialize(str(directory))
            self.provider = RNS.Identity(create_keys=False)
            self.provider.load_public_key(public)
            self.sock = socket.socket(socket.AF_INET6 if address.version == 6 else socket.AF_INET, socket.SOCK_STREAM)
            if not callbacks.bindSocket(self.sock.fileno()):
                self._check_cancelled()
                raise TransportUnavailable('Underlying network unavailable')
            self.sock.settimeout(5)
            try:
                self.sock.connect((str(address), port))
            except OSError as failure:
                raise TransportUnavailable('Relay socket unavailable') from failure
            self.sock.settimeout(None)
            self.interface = TCPClientInterface(RNS.Transport, {'name': 'fc-android-control'}, connected_socket=self.sock)
            self.interface.OUT = True
            self.interface.online = True
            self.interface.target_ip = str(address)
            self.interface.target_port = port
            _runtime._add_interface(self.interface)
            threading.Thread(target=self.interface.read_loop, daemon=True).start()
            destination = RNS.Destination(self.provider, RNS.Destination.OUT, RNS.Destination.SINGLE,
                                          'family_connect', 'control', 'v1')
            # RNS 1.5.1 has_path ignores expired timestamps until its next sweep.
            # Remove only this destination before replacing the detached interface.
            with RNS.Transport.path_table_lock:
                RNS.Transport.path_table.pop(destination.hash, None)
            deadline = time.monotonic() + 25
            RNS.Transport.request_path(destination.hash)
            self._wait(lambda: RNS.Transport.has_path(destination.hash), deadline)
            established = threading.Event()
            self.link = RNS.Link(destination, established_callback=lambda _: established.set())
            self._wait(lambda: established.is_set() or self.link.status == RNS.Link.CLOSED, deadline)
            if not established.is_set() or self.link.status != RNS.Link.ACTIVE:
                raise OSError('RNS link unavailable')
        except BaseException:
            self.close()
            raise

    def _check_cancelled(self):
        classify = getattr(self.callbacks, 'stopReason', None)
        if classify is None:
            if self.callbacks.cancelled():
                raise OSError('RNS cancelled')
            return
        reason = str(classify())
        if reason == 'CANCELLED':
            raise OSError('RNS cancelled')
        if reason == 'TIMEOUT':
            raise TransportUnavailable('RNS shared deadline')
        if reason != 'NONE':
            raise ValueError('Invalid RNS stop reason')

    def _wait(self, predicate, deadline):
        while True:
            self._check_cancelled()
            if time.monotonic() >= deadline:
                raise TransportUnavailable('RNS timeout')
            if predicate():
                return
            time.sleep(.02)

    def readiness_request(self, path, encoded):
        if str(path) not in _readiness_paths:
            raise ValueError('Invalid readiness request')
        try:
            return ['AVAILABLE', self.request(path, encoded)]
        except TransportUnavailable:
            return ['UNAVAILABLE', None]

    def request(self, path, encoded):
        path = str(path)
        raw = base64.b64decode(str(encoded), validate=True)
        readiness = path in _readiness_paths
        if (path not in ('/control/v1/challenge', '/control/v1/fetch', '/control/v1/ack') and not readiness
                or len(raw) > (8192 if readiness else 4096)):
            raise ValueError('Invalid RNS request')
        result = []
        done = threading.Event()
        def received(receipt):
            result.append(receipt.response)
            done.set()
        self._check_cancelled()
        receipt = self.link.request(path, data=raw, response_callback=received,
                                    failed_callback=lambda _: done.set(), timeout=20,
                                    max_response_size=90000 if readiness else 65536)
        if receipt is None or receipt is False:
            raise OSError('RNS request unavailable')
        self._wait(lambda: done.is_set() or self.link.status == RNS.Link.CLOSED, time.monotonic()+20)
        if not result or type(result[0]) is not bytes or not 0 < len(result[0]) <= (90000 if readiness else 65536):
            raise OSError('Invalid RNS response')
        if result[0] in (b'{"code":"PROVISIONING_REJECTED"}', b'{"code":"PROVISIONING_UNAVAILABLE"}'):
            raise OSError('Relay refused request')
        return base64.b64encode(result[0]).decode('ascii')

    def close(self):
        try:
            if self.link is not None:
                self.link.teardown()
            if self.interface is not None:
                self.interface.detach()
                RNS.Transport.remove_interface(self.interface)
            elif self.sock is not None:
                self.sock.close()
        finally:
            self.link = self.interface = self.sock = None
            if self.locked:
                self.locked = False
                _session_lock.release()
