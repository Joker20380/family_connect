"""Ordinary-user client for chat-only access to this computer's active MESH owner."""
import base64
from contextlib import contextmanager
import json as json_module
import os
from pathlib import Path
import re
import socket
import ssl
import stat
import struct
import threading
import time

import httpx

from . import chat_bridge_protocol as wire
from .friends import FriendsError


class ChatBridge:
    ROUTE = 'EXISTING_EXIT'
    validate = staticmethod(wire.validate)
    def __init__(self, device, *, _paths=None, _root_uid=0):
        if type(device) is not str or not re.fullmatch('[0-9a-f]{32}', device):
            raise ValueError('Invalid device reference')
        self.device, self.root_uid = device, _root_uid
        self.paths = tuple(_paths) if _paths is not None else tuple(Path(root) / (str(os.getuid()) + '.chat.sock')
            for root in ('/run/family-connect-auto-ipc', '/run/family-connect-mesh'))
        self.lock = threading.Lock()
        self.closed = False
        self.connections = set()

    @contextmanager
    def _connection(self, path, deadline, cancel=None):
        if cancel is not None and cancel.is_set():
            raise wire.BridgeError('CANCELLED')
        try:
            parent, endpoint = path.parent.lstat(), path.lstat()
        except FileNotFoundError:
            raise wire.BridgeError() from None
        if (not stat.S_ISDIR(parent.st_mode) or parent.st_uid != self.root_uid or parent.st_mode & 0o022 or
                not stat.S_ISSOCK(endpoint.st_mode) or endpoint.st_uid != os.getuid() or stat.S_IMODE(endpoint.st_mode) != 0o600):
            raise wire.BridgeError('DENIED')
        connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        done, monitor = threading.Event(), None
        def watch_cancel():
            while not done.wait(.05):
                if cancel.is_set():
                    try:
                        connection.shutdown(socket.SHUT_RDWR)
                    except OSError:
                        pass
                    return
        try:
            with self.lock:
                if self.closed:
                    raise wire.BridgeError('CANCELLED')
                if len(self.connections) >= 4:
                    raise wire.BridgeError()
                self.connections.add(connection)
            connection.settimeout(max(.001, min(4, deadline - time.monotonic())))
            connection.connect(str(path))
            _, uid, _ = struct.unpack('3i', connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
            if uid != self.root_uid:
                raise wire.BridgeError('DENIED')
            if cancel is not None:
                monitor = threading.Thread(target=watch_cancel, name='fc-chat-request-cancel', daemon=False)
                monitor.start()
            yield connection
        except OSError as error:
            if (self.closed or (cancel is not None and cancel.is_set())) and getattr(error, 'code', None) not in ('DENIED', 'CONFLICT'):
                raise wire.BridgeError('CANCELLED') from None
            raise
        finally:
            done.set()
            if monitor is not None:
                monitor.join(1)
            with self.lock:
                self.connections.discard(connection)
            connection.close()

    def _request(self, connection, action, deadline, **fields):
        remaining = min(30000, int((deadline - time.monotonic()) * 1000))
        if remaining <= 0:
            raise wire.BridgeError('DEADLINE')
        request = dict(schema=1, id=1, action=action, device=self.device, budget_ms=remaining, **fields)
        self.validate(request)
        wire.write(connection, request)
        reply = wire.read(connection, deadline + 4)
        if (type(reply.get('schema')) is not int or reply['schema'] != 1 or type(reply.get('id')) is not int or
                reply['id'] != 1 or type(reply.get('ok')) is not bool):
            raise wire.BridgeError('DENIED')
        if not reply['ok']:
            if set(reply) != {'schema', 'id', 'ok', 'error'} or type(reply.get('error')) is not str or reply['error'] not in wire.ERRORS:
                raise wire.BridgeError('DENIED')
            raise wire.BridgeError(reply['error'])
        expected = {'schema', 'id', 'ok', 'route'} | ({'status', 'data'} if action == 'request' else set())
        if set(reply) != expected or reply['route'] != self.ROUTE:
            raise wire.BridgeError('DENIED')
        return reply

    def _select(self, deadline, cancel=None):
        selected = None
        for path in self.paths:
            try:
                with self._connection(path, deadline, cancel) as connection:
                    self._request(connection, 'probe', deadline)
                if selected is not None:
                    raise wire.BridgeError('DENIED')
                selected = path
            except wire.BridgeError as error:
                if error.code != 'UNAVAILABLE':
                    raise
            except (ConnectionError, TimeoutError, FileNotFoundError):
                continue
        if selected is None:
            raise wire.BridgeError()
        return selected

    def request(self, path, body, timeout):
        deadline = time.monotonic() + min(30, timeout)
        selected = self._select(deadline)
        with self._connection(selected, deadline) as connection:
            reply = self._request(connection, 'request', deadline, path=path, data=base64.b64encode(body).decode())
        if type(reply.get('status')) is not int or not 100 <= reply['status'] <= 599:
            raise wire.BridgeError('DENIED')
        return reply['status'], wire.payload(reply['data'], 16384)

    def open_mailbox(self, deadline, cancel):
        if cancel.is_set():
            raise wire.BridgeError('CANCELLED')
        selected = self._select(deadline, cancel)
        with self._connection(selected, deadline, cancel) as connection:
            self._request(connection, 'open', deadline)
            channel = wire.receive_socket(connection)
        if cancel.is_set():
            channel.close()
            raise wire.BridgeError('CANCELLED')
        return channel

    def close(self):
        with self.lock:
            self.closed = True
            connections = list(self.connections)
        for connection in connections:
            try:
                connection.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass


def tls_failure(error):
    seen = set()
    while error is not None and id(error) not in seen:
        if isinstance(error, ssl.SSLError):
            return True
        seen.add(id(error))
        error = error.__cause__ or error.__context__
    return False


class ChatHTTP:
    def __init__(self, direct, bridge):
        self.direct, self.bridge = direct, bridge
        self.base_url = direct.base_url
        self.deadline = time.monotonic() + 60

    @contextmanager
    def stream(self, method, path, *, json, **options):
        if method != 'POST' or path not in wire.PATHS:
            raise FriendsError('invalid_input')
        raw = json_module.dumps(json, separators=(',', ':'), allow_nan=False).encode()
        if len(raw) > 8192:
            raise FriendsError('invalid_input')
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise FriendsError('timeout')
        status, body = None, bytearray()
        terminal_error, complete = None, False
        try:
            with self.direct.stream('POST', path, content=raw, headers={'Content-Type': 'application/json', 'Accept-Encoding': 'identity'},
                                    timeout=min(12, remaining), follow_redirects=False) as response:
                try:
                    status = response.status_code
                    if status in (400, 401, 403, 409):
                        raise FriendsError('access_rejected')
                    if status == 200:
                        if response.headers.get('Content-Encoding', '').strip().lower() not in ('', 'identity'):
                            raise FriendsError('invalid_response')
                        for chunk in response.stream:
                            if len(body) + len(chunk) > 16384:
                                raise FriendsError('invalid_response')
                            if time.monotonic() >= self.deadline:
                                raise FriendsError('timeout')
                            body.extend(chunk)
                        complete = True
                except BaseException as error:
                    if not isinstance(error, (httpx.TransportError, ssl.SSLError)):
                        terminal_error = error
                    elif tls_failure(error):
                        terminal_error = FriendsError('access_rejected')
                    raise
        except BaseException as error:
            if terminal_error is not None:
                raise terminal_error from None
            if not isinstance(error, (httpx.TransportError, ssl.SSLError)):
                raise
            if tls_failure(error):
                raise FriendsError('access_rejected') from None
            if not complete:
                status = None
        if status != 200:
            try:
                status, data = self.bridge.request(path, raw, self.deadline - time.monotonic())
                body = bytearray(data)
            except wire.BridgeError as error:
                raise FriendsError('access_rejected' if error.code in ('DENIED', 'CONFLICT') else
                                   'cancelled' if error.code == 'CANCELLED' else 'service_unavailable') from None
        if status in (400, 401, 403, 409):
            raise FriendsError('access_rejected')
        yield httpx.Response(status, content=bytes(body), request=httpx.Request('POST', self.base_url.join(path)))
