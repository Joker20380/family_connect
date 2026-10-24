"""Chat-only socket routes. Packed LXMF never leaves the encrypted RNS mailbox.

Factories are supplied by a trusted session owner, not by a contact or wire JSON.
Only transient route failures advance the ordered route set. The same node key,
source identity, queue and signed bytes are used on every path.
"""
from contextlib import contextmanager
import threading
import time
import ssl
import socket

import RNS
from RNS.Interfaces.TCPInterface import TCPClientInterface
from RNS.Interfaces.LocalInterface import LocalClientInterface

from .mailbox import Mailbox, MailboxError


class RoutedMailbox(Mailbox):
    ROUTES = ('DIRECT', 'EXISTING_EXIT', 'SERVICE_ONLY')

    def __init__(self, chat, source, node_public, runtime, routes, session_lock):
        super().__init__(chat, source, node_public)
        order = self.ROUTES
        if (not routes or len(routes) > 3 or any(name not in order or not callable(connect) for name, connect in routes)
                or [order.index(name) for name, _ in routes] != sorted(set(order.index(name) for name, _ in routes))):
            raise ValueError('Invalid chat routes')
        self.runtime, self.routes, self.session_lock = runtime, tuple(routes), session_lock
        self.route = None
        self.attempted = []
        self._route_lock = threading.Lock()
        self._selected = None

    def exchange(self, *, timeout=12, cancel=None):
        if type(timeout) not in (int, float) or not 0 < timeout <= 30:
            raise ValueError('Invalid mailbox timeout')
        cancel = cancel if cancel is not None else threading.Event()
        if not self._route_lock.acquire(blocking=False):
            raise MailboxError('busy')
        deadline = time.monotonic() + timeout
        self.attempted = []
        try:
            for index, route in enumerate(self.routes):
                self._wait(lambda: True, deadline, cancel)
                self._selected = route
                self.attempted.append(route[0])
                try:
                    budget = (deadline - time.monotonic()) / (len(self.routes) - index)
                    return super().exchange(timeout=min(30, budget), cancel=cancel)
                except MailboxError as failure:
                    if str(failure) not in ('unavailable', 'link_failed', 'timeout', 'request_failed'):
                        raise
            raise MailboxError('unavailable')
        finally:
            self._selected = None
            self._route_lock.release()

    @contextmanager
    def _connection(self, timeout, cancel):
        cancel = cancel if cancel is not None else threading.Event()
        deadline = time.monotonic() + timeout
        if self._selected is None:
            raise MailboxError('unavailable')
        name, connect = self._selected
        self._wait(lambda: True, deadline, cancel)
        try:
            sock = connect(deadline, cancel)
        except ssl.SSLError:
            raise MailboxError('access_denied') from None
        except OSError:
            raise MailboxError('unavailable') from None
        interface = reader = None
        if not self.session_lock.acquire(blocking=False):
            sock.close()
            raise MailboxError('busy')
        try:
            self._wait(lambda: True, deadline, cancel)
            sock.settimeout(None)
            if sock.family == socket.AF_UNIX:
                interface = LocalClientInterface(RNS.Transport, 'fc-chat-service', connected_socket=sock)
                interface.epoll_backend = False
                interface.pause_on_client_sleep = False
            else:
                interface = TCPClientInterface(RNS.Transport, {'name': 'fc-chat-route'}, connected_socket=sock)
                interface.target_ip, interface.target_port = sock.getpeername()[:2]
            interface.OUT = interface.online = True
            self.runtime._add_interface(interface)
            reader = threading.Thread(target=interface.read_loop, name='chat-route', daemon=True)
            reader.start()
            destination = RNS.Destination(self.node, RNS.Destination.OUT, RNS.Destination.SINGLE, 'lxmf', 'propagation')
            with RNS.Transport.path_table_lock:
                RNS.Transport.path_table.pop(destination.hash, None)
            with super()._connection(min(30, deadline - time.monotonic()), cancel) as connection:
                self.route = name
                yield connection
        finally:
            if interface is not None:
                interface.detach()
                RNS.Transport.remove_interface(interface)
            else:
                sock.close()
            if reader is not None:
                reader.join(1)
            self.session_lock.release()
