"""Bounded Android mailbox carrier; shares the control runtime/session lease.

Mailbox-only destination: no direct LXMF receiver, announce or router job loop.
The native owner supplies an authenticated bootstrap, never arbitrary UI JSON.
"""
from contextlib import contextmanager
import ipaddress
import socket
import threading
import time

import RNS
from RNS.Interfaces.TCPInterface import TCPClientInterface
from messenger.mailbox import Mailbox, MailboxError
import fc_rns_transport as transport


class CarrierMailbox(Mailbox):
    def __init__(self, chat, host, port, node_public, callbacks):
        self.host = ipaddress.ip_address(host)
        if type(port) is not int or not 1 <= port <= 65535:
            raise ValueError('Invalid mailbox port')
        self.port, self.callbacks = port, callbacks
        self.source = None
        self._closed = False
        # Validate the trust anchor before registering a destination.
        from messenger.codec import identity
        identity(node_public)
        source = RNS.Destination(chat.identity, RNS.Destination.IN,
                                 RNS.Destination.SINGLE, 'lxmf', 'delivery')
        source.accepts_links(False)
        try:
            super().__init__(chat, source, node_public)
        except BaseException:
            RNS.Transport.deregister_destination(source)
            raise

    @contextmanager
    def _connection(self, timeout, cancel):
        if type(timeout) not in (int, float) or not 0 < timeout <= 30:
            raise ValueError('Invalid mailbox timeout')
        cancel = cancel if cancel is not None else threading.Event()
        deadline = time.monotonic() + timeout
        if self._closed:
            raise MailboxError('unavailable')
        if not transport._session_lock.acquire(blocking=False):
            raise MailboxError('busy')
        sock = interface = reader = None
        try:
            self._wait(lambda: True, deadline, cancel)
            if transport._runtime is None:
                raise MailboxError('unavailable')
            sock = socket.socket(socket.AF_INET6 if self.host.version == 6 else socket.AF_INET,
                                 socket.SOCK_STREAM)
            if not self.callbacks.bindSocket(sock.fileno()):
                raise MailboxError('unavailable')
            self._wait(lambda: True, deadline, cancel)
            sock.settimeout(min(5, max(.001, deadline - time.monotonic())))
            try:
                sock.connect((str(self.host), self.port))
            except OSError:
                raise MailboxError('link_failed') from None
            self._wait(lambda: True, deadline, cancel)
            sock.settimeout(None)
            # connected_socket is a non-initiator: RNS cannot reconnect on an
            # unbound replacement socket behind Android's network owner.
            interface = TCPClientInterface(RNS.Transport, {'name': 'fc-android-chat'},
                                           connected_socket=sock)
            interface.OUT = interface.online = True
            interface.target_ip = str(self.host)
            interface.target_port = self.port
            transport._runtime._add_interface(interface)
            reader = threading.Thread(target=interface.read_loop, name='chat-carrier', daemon=True)
            reader.start()
            destination = RNS.Destination(self.node, RNS.Destination.OUT, RNS.Destination.SINGLE,
                                          'lxmf', 'propagation')
            with RNS.Transport.path_table_lock:
                RNS.Transport.path_table.pop(destination.hash, None)
            self._wait(lambda: True, deadline, cancel)
            with super()._connection(deadline - time.monotonic(), cancel) as connection:
                yield connection
        finally:
            try:
                if interface is not None:
                    interface.detach()
                    RNS.Transport.remove_interface(interface)
                elif sock is not None:
                    sock.close()
                if reader is not None:
                    reader.join(1)
            finally:
                transport._session_lock.release()

    def close(self):
        # The session must stop/join DeliveryController before this call.
        if not self._closed:
            RNS.Transport.deregister_destination(self.source)
            self._closed = True
