"""Authenticated mailbox on OS routing; no privileged bypass or service-only claim."""
import importlib
import ipaddress
import os
from pathlib import Path
import signal
import socket
import stat
import threading
import time

import RNS

from messenger.codec import identity
from messenger.mailbox import MailboxError
from messenger.routed import RoutedMailbox

_runtime_lock = threading.Lock()
_session_lock = threading.Lock()
_runtime = None


class _ApplicationSignals:
    SIGINT = signal.SIGINT
    SIGTERM = signal.SIGTERM

    @staticmethod
    def signal(*args):
        return None


def initialize(directory):
    global _runtime
    with _runtime_lock:
        if _runtime is not None:
            return _runtime
        if RNS.Reticulum.get_instance() is not None:
            raise ValueError('runtime_already_owned')
        root = Path(directory)
        root.mkdir(mode=0o700, exist_ok=True)
        info = root.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
            raise ValueError('unsafe_runtime')
        descriptor = os.open(root / 'config', os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
        with os.fdopen(descriptor, 'w') as target:
            info = os.fstat(target.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_uid != os.getuid():
                raise ValueError('unsafe_runtime')
            target.truncate(0)
            target.write('[reticulum]\nshare_instance = No\nenable_transport = No\n'
                         '[logging]\nloglevel = -1\n[interfaces]\n')
        module = importlib.import_module('RNS.Reticulum')
        original = module.signal
        try:
            module.signal = _ApplicationSignals
            _runtime = RNS.Reticulum(configdir=str(root), loglevel=-1)
        finally:
            module.signal = original
        return _runtime


class SystemMailbox(RoutedMailbox):
    ROUTES = ('SYSTEM',)

    def __init__(self, chat, node, runtime, *, _routes=None):
        self.host = str(ipaddress.IPv4Address(node['host']))
        self.port, self.expires = node['port'], node['expires_at']
        if (type(self.port) is not int or not 1 <= self.port <= 65535 or
                type(self.expires) is not int or not time.time() < self.expires <= time.time() + 120):
            raise ValueError('invalid_node')
        public = bytes.fromhex(node['public_key'])
        identity(public)
        self.closed = False
        source = RNS.Destination(chat.identity, RNS.Destination.IN, RNS.Destination.SINGLE, 'lxmf', 'delivery')
        source.accepts_links(False)
        try:
            super().__init__(chat, source, public, runtime, _routes or [('SYSTEM', self._connect)], _session_lock)
        except BaseException:
            RNS.Transport.deregister_destination(source)
            raise

    def _connect(self, deadline, cancel):
        self._wait(lambda: True, deadline, cancel)
        connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            connection.settimeout(min(2, max(.001, deadline - time.monotonic())))
            connection.connect((self.host, self.port))
            self._wait(lambda: True, deadline, cancel)
            return connection
        except BaseException:
            connection.close()
            raise

    def exchange(self, *, timeout=12, cancel=None):
        remaining = self.expires - time.time()
        if self.closed or remaining <= 0:
            raise MailboxError('access_denied')
        return super().exchange(timeout=min(timeout, remaining), cancel=cancel)

    def close(self):
        if not self.closed:
            RNS.Transport.deregister_destination(self.source)
            self.closed = True


class ExistingExitMailbox(SystemMailbox):
    ROUTES = ('SYSTEM', 'EXISTING_EXIT')

    def __init__(self, chat, node, runtime, bridge):
        super().__init__(chat, node, runtime)
        self.bridge = bridge
        self.routes = (*self.routes, ('EXISTING_EXIT', self._existing))

    def _existing(self, deadline, cancel):
        from .chat_bridge_protocol import BridgeError
        try:
            return self.bridge.open_mailbox(deadline, cancel)
        except BridgeError as error:
            if error.code in ('DENIED', 'CONFLICT', 'INVALID_RESPONSE'):
                raise MailboxError('access_denied') from None
            if error.code == 'CANCELLED':
                raise MailboxError('cancelled') from None
            raise MailboxError('unavailable') from None


class _DirectDeadline(Exception):
    pass


class ProtectedMailbox(ExistingExitMailbox):
    ROUTES = ('DIRECT', 'EXISTING_EXIT', 'SERVICE_ONLY')

    def __init__(self, chat, node, runtime, direct, bridge, *, registration_route='DIRECT'):
        if registration_route not in self.ROUTES:
            raise ValueError('invalid_registration_route')
        self.direct, self.bridge = direct, bridge
        routes = (('EXISTING_EXIT', self._existing),)
        if hasattr(bridge, 'open_service_mailbox'):
            routes = (*routes, ('SERVICE_ONLY', self._service))
        if registration_route == 'DIRECT':
            routes = (('DIRECT', self._direct), *routes)
        SystemMailbox.__init__(self, chat, node, runtime, _routes=routes)

    def _existing(self, deadline, cancel):
        from .chat_bridge_protocol import BridgeError
        try:
            return self.bridge.open_mailbox(deadline, cancel)
        except BridgeError as error:
            if error.code in ('DENIED', 'CONFLICT', 'INVALID_RESPONSE'):
                raise MailboxError('access_denied') from None
            if error.code == 'DEADLINE':
                raise _DirectDeadline() from None
            if error.code == 'CANCELLED':
                raise MailboxError('cancelled') from None
            raise MailboxError('unavailable') from None

    def _service(self, deadline, cancel):
        from .chat_bridge_protocol import BridgeError
        try:
            return self.bridge.open_service_mailbox(deadline, cancel)
        except BridgeError as error:
            if error.code in ('DENIED', 'CONFLICT', 'INVALID_RESPONSE'):
                raise MailboxError('access_denied') from None
            if error.code == 'DEADLINE':
                raise _DirectDeadline() from None
            if error.code == 'CANCELLED':
                raise MailboxError('cancelled') from None
            raise MailboxError('unavailable') from None

    def exchange(self, *, timeout=12, cancel=None):
        try:
            return super().exchange(timeout=timeout, cancel=cancel)
        except _DirectDeadline:
            raise MailboxError('timeout') from None

    def _direct(self, deadline, cancel):
        from .chat_bridge_protocol import BridgeError
        try:
            return self.direct.open_mailbox(deadline, cancel)
        except BridgeError as error:
            if error.code in ('DENIED', 'CONFLICT', 'INVALID_RESPONSE'):
                raise MailboxError('access_denied') from None
            if error.code == 'CANCELLED':
                raise MailboxError('cancelled') from None
            if error.code == 'DEADLINE':
                raise _DirectDeadline() from None
            raise MailboxError('unavailable') from None
