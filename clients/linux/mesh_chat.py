"""Private bounded chat lane; a broken lane never terminates the VPN worker."""
import base64
import select
import socket
import threading
import time

import mesh_ipc as ipc

MAX_FRAME = 96 * 1024
MAX_DATA = 16 * 1024
MAX_JOBS = 12
CONTROL = frozenset(('route', 'release', 'close', 'cancel'))
ACTIONS = CONTROL | {'acquire', 'open', 'request', 'read', 'write', 'finish'}
ERRORS = frozenset(('DENIED', 'CONFLICT', 'DEADLINE', 'CANCELLED', 'UNAVAILABLE', 'BUSY_OR_UNAVAILABLE'))
ROUTES = frozenset(('CONNECTING', 'SERVICE_ONLY', 'EXISTING_EXIT', 'UNAVAILABLE'))


class ChatError(RuntimeError):
    def __init__(self, code):
        self.code = code if code in ERRORS else 'UNAVAILABLE'
        super().__init__(self.code)


class Pending:
    def __init__(self, action):
        self.action = action
        self.ready = threading.Event()
        self.reply = None


def checked_reply(reply, identifier, action):
    if (type(reply.get('schema')) is not int or reply['schema'] != 1 or
            type(reply.get('id')) is not int or reply['id'] != identifier or type(reply.get('ok')) is not bool):
        raise ipc.ProtocolError()
    base = {'schema', 'id', 'ok'}
    if not reply['ok']:
        if not isinstance(reply.get('error'), str) or reply['error'] not in ERRORS:
            raise ipc.ProtocolError()
        allowed = base | {'error'}
        if action in ('read', 'write'):
            allowed |= {'count', 'data'}
    else:
        allowed = base | {'acquire': {'lease', 'route'}, 'route': {'route'}, 'open': {'stream'},
                          'request': {'status', 'data'}, 'read': {'count', 'data', 'eof'},
                          'write': {'count'}}.get(action, set())
        if action in ('acquire', 'route') and (not isinstance(reply.get('route'), str) or reply['route'] not in ROUTES):
            raise ipc.ProtocolError()
        if action == 'acquire' and (type(reply.get('lease')) is not int or reply['lease'] != identifier):
            raise ipc.ProtocolError()
        if action == 'open' and (type(reply.get('stream')) is not int or reply['stream'] != identifier):
            raise ipc.ProtocolError()
        if action == 'request' and (type(reply.get('status')) is not int or not 100 <= reply['status'] <= 599):
            raise ipc.ProtocolError()
    if set(reply) - allowed:
        raise ipc.ProtocolError()
    if 'count' in reply and (type(reply['count']) is not int or not 0 <= reply['count'] <= MAX_DATA):
        raise ipc.ProtocolError()
    if 'eof' in reply and type(reply['eof']) is not bool:
        raise ipc.ProtocolError()
    encoded = reply.get('data', '')
    if not isinstance(encoded, str) or len(encoded) > 4 * ((MAX_DATA + 2) // 3):
        raise ipc.ProtocolError()
    try:
        data = base64.b64decode(encoded, validate=True)
    except (ValueError, UnicodeError):
        raise ipc.ProtocolError() from None
    if len(data) > MAX_DATA or base64.b64encode(data).decode() != encoded:
        raise ipc.ProtocolError()
    if action == 'read' and len(data) != reply.get('count', 0):
        raise ipc.ProtocolError()
    return dict(reply, data=data) if 'data' in allowed else reply


class ChatLane:
    def __init__(self, connection):
        if connection.family != socket.AF_UNIX or connection.type & 0xf != socket.SOCK_STREAM:
            raise ValueError('Private stream socket required')
        self.connection = connection
        self.lock = threading.Lock()
        self.writer = threading.Lock()
        self.closed = threading.Event()
        self.pending = {}
        self.identifier = 0
        self.reader = threading.Thread(target=self._read, name='fc-chat-native', daemon=True)
        self.reader.start()

    def _submit(self, action, values):
        if action not in ACTIONS or set(values) & {'schema', 'id', 'action'}:
            raise ValueError('Invalid chat action')
        pending = Pending(action)
        deadline = time.monotonic() + 4
        if not self.writer.acquire(timeout=4):
            self.close()
            raise ChatError('UNAVAILABLE')
        try:
            with self.lock:
                if self.closed.is_set():
                    raise ChatError('UNAVAILABLE')
                jobs = sum(item.action not in CONTROL for item in self.pending.values())
                controls = len(self.pending) - jobs
                if (action in CONTROL and controls >= 4) or (action not in CONTROL and jobs >= MAX_JOBS):
                    raise ChatError('BUSY_OR_UNAVAILABLE')
                self.identifier += 1
                identifier = self.identifier
                self.pending[identifier] = pending
            try:
                ipc.send(self.connection.fileno(), dict(values, schema=1, id=identifier, action=action), MAX_FRAME, deadline)
            except (OSError, ValueError, EOFError, TimeoutError):
                self.close()
                raise ChatError('UNAVAILABLE') from None
        finally:
            self.writer.release()
        return identifier, pending

    def call(self, action, *, cancel=None, **values):
        if cancel is not None and cancel.is_set():
            raise ChatError('CANCELLED')
        budget = values.get('budget_ms', 0)
        if action not in CONTROL and (type(budget) is not int or not 0 < budget <= 30000):
            raise ValueError('Chat operation requires a bounded deadline')
        identifier, pending = self._submit(action, values)
        deadline = time.monotonic() + budget / 1000 + 4
        cancelled = False
        while not pending.ready.wait(.05):
            if cancel is not None and cancel.is_set() and not cancelled:
                self._submit('cancel', {'target': identifier})
                cancelled = True
                deadline = min(deadline, time.monotonic() + 4)
            if time.monotonic() >= deadline:
                self.close()
                raise ChatError('UNAVAILABLE')
        reply = pending.reply
        if reply is None:
            raise ChatError('UNAVAILABLE')
        if cancelled and reply['ok']:
            if action in ('acquire', 'open'):
                self.call('release' if action == 'acquire' else 'close', **{'lease' if action == 'acquire' else 'stream': identifier})
            raise ChatError('CANCELLED')
        if not reply['ok']:
            raise ChatError(reply['error'])
        return reply

    def _read(self):
        try:
            while not self.closed.is_set():
                if not select.select([self.connection], [], [], .2)[0]:
                    continue
                reply = ipc.receive(self.connection.fileno(), MAX_FRAME, time.monotonic() + 4)
                identifier = reply.get('id')
                if type(identifier) is not int:
                    raise ipc.ProtocolError()
                with self.lock:
                    pending = self.pending.get(identifier)
                    if pending is None:
                        raise ipc.ProtocolError()
                    pending.reply = checked_reply(reply, identifier, pending.action)
                    del self.pending[identifier]
                    pending.ready.set()
        except (OSError, ValueError, EOFError, TimeoutError):
            pass
        finally:
            self.close()
            with self.writer:
                self.connection.close()

    def close(self):
        with self.lock:
            if self.closed.is_set():
                return
            self.closed.set()
            for pending in self.pending.values():
                pending.ready.set()
            self.pending.clear()
        try:
            self.connection.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
