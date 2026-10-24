"""UID and device-bound chat access to an existing authenticated MESH session."""
import base64
import copy
import os
from pathlib import Path
import select
import socket
import stat
import threading
import time

from mesh_chat import ChatError
import mesh_ipc
from provisioning import chat_bridge_protocol as wire


class Cancellation:
    def __init__(self, *events):
        self.events = events

    def is_set(self):
        return any(event.is_set() for event in self.events)


class Binding:
    def __init__(self, lane, start, cancelled, route='EXISTING_EXIT'):
        if route not in ('EXISTING_EXIT', 'SERVICE_ONLY'):
            raise ValueError('Invalid chat route')
        self.route = route
        self.lane = lane
        self.lock = threading.Lock()
        self.closed, self.ready = threading.Event(), threading.Event()
        self.cancelled = cancelled
        self.device = start['readiness'].get('device', '')
        self.material = copy.deepcopy({key: start[key] for key in ('identity', 'anchor', 'readiness', 'resolver', 'underlying_index')})

    def close(self):
        self.closed.set()
        self.ready.clear()
        with self.lock:
            self.material.clear()

    def acquire(self, device, cancel, budget):
        with self.lock:
            if device != self.device:
                raise wire.BridgeError('DENIED')
            if not self.ready.is_set() or self.closed.is_set() or self.cancelled.is_set():
                raise wire.BridgeError()
            material = copy.deepcopy(self.material)
        try:
            result = self.lane.call('acquire', acquire=material, budget_ms=budget, cancel=cancel)
        finally:
            material.clear()
        allowed = ('SERVICE_ONLY', 'CONNECTING') if self.route == 'SERVICE_ONLY' else ('EXISTING_EXIT',)
        if result.get('route') not in allowed or cancel.is_set():
            self.release(result['lease'])
            raise wire.BridgeError()
        return result['lease']

    def probe(self, device):
        if device != self.device:
            raise wire.BridgeError('DENIED')
        if not self.ready.is_set() or self.closed.is_set() or self.cancelled.is_set():
            raise wire.BridgeError()

    def release(self, lease):
        try:
            self.lane.call('release', lease=lease)
        except (OSError, ValueError, ChatError):
            pass


def remove_endpoint(endpoint, uid):
    if os.path.lexists(endpoint):
        info = endpoint.lstat()
        if not stat.S_ISSOCK(info.st_mode) or info.st_uid != uid or stat.S_IMODE(info.st_mode) != 0o600:
            raise ValueError('Unsafe chat endpoint')
        endpoint.unlink()


class Host:
    validate = staticmethod(wire.validate)

    def binding(self, request, cancel, deadline):
        return self.provider()

    def __init__(self, endpoint, uid, provider):
        self.endpoint, self.uid, self.provider = Path(endpoint), uid, provider
        self.stop = threading.Event()
        self.lock = threading.Lock()
        self.active = {}
        self.listener = None
        self.thread = None

    def start(self):
        remove_endpoint(self.endpoint, self.uid)
        listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            listener.bind(str(self.endpoint))
            os.chmod(self.endpoint, 0o600)
            os.chown(self.endpoint, self.uid, -1)
            listener.listen(4)
            listener.settimeout(.2)
            self.listener = listener
            self.thread = threading.Thread(target=self._accept, name='fc-chat-admission', daemon=False)
            self.thread.start()
        except BaseException:
            listener.close()
            raise

    def _accept(self):
        while not self.stop.is_set():
            try:
                connection, _ = self.listener.accept()
            except TimeoutError:
                continue
            except OSError:
                break
            with self.lock:
                if self.stop.is_set() or len(self.active) >= 4:
                    connection.close()
                    continue
                thread = threading.Thread(target=self._serve, args=(connection,), name='fc-chat-operation', daemon=False)
                self.active[connection] = thread
                thread.start()

    def _serve(self, connection):
        lost, monitor_stop = threading.Event(), threading.Event()
        monitor = None
        request, binding, lease = {}, None, None
        try:
            if mesh_ipc.peer_uid(connection) != self.uid:
                return
            request = wire.read(connection, time.monotonic() + 4)
            self.validate(request)
            deadline = time.monotonic() + request['budget_ms'] / 1000
            cancel = Cancellation(self.stop, lost)
            monitor = threading.Thread(target=self._monitor, args=(connection, lost, monitor_stop), name='fc-chat-disconnect', daemon=False)
            monitor.start()
            binding = self.binding(request, cancel, deadline)
            if binding is None:
                raise wire.BridgeError()
            binding.probe(request['device'])
            if request['action'] in ('probe', 'prepare'):
                wire.write(connection, dict(schema=1, id=request['id'], ok=True, route=binding.route))
                return
            cancel = Cancellation(self.stop, lost, binding.closed, binding.cancelled)
            lease = binding.acquire(request['device'], cancel, self._budget(deadline))
            if request['action'] == 'request':
                result = binding.lane.call('request', lease=lease, path=request['path'], data=request['data'],
                                           budget_ms=self._budget(deadline), cancel=cancel)
                if cancel.is_set():
                    raise wire.BridgeError('CANCELLED')
                wire.write(connection, dict(schema=1, id=request['id'], ok=True, route=binding.route,
                                           status=result['status'], data=base64.b64encode(result.get('data', b'')).decode()))
            else:
                opened = binding.lane.call('open', lease=lease, budget_ms=self._budget(deadline), cancel=cancel)
                monitor_stop.set()
                monitor.join(1)
                self._mailbox(connection, request['id'], binding, opened['stream'], cancel, deadline, route=binding.route)
        except (OSError, ValueError, ChatError, RecursionError) as error:
            code = getattr(error, 'code', 'UNAVAILABLE')
            if type(request.get('id')) is int:
                try:
                    wire.write(connection, dict(schema=1, id=request['id'], ok=False, error=code if code in wire.ERRORS else 'UNAVAILABLE'))
                except (OSError, ValueError):
                    pass
        finally:
            lost.set()
            monitor_stop.set()
            if monitor is not None:
                monitor.join(1)
            if lease is not None:
                binding.release(lease)
            request.clear()
            connection.close()
            with self.lock:
                self.active.pop(connection, None)

    @staticmethod
    def _budget(deadline):
        remaining = int((deadline - time.monotonic()) * 1000)
        if remaining <= 0:
            raise wire.BridgeError('DEADLINE')
        return min(30000, remaining)

    @staticmethod
    def _monitor(connection, lost, stop):
        while not stop.wait(.1):
            try:
                if select.select([connection], [], [], 0)[0]:
                    lost.set()
                    return
            except (OSError, ValueError):
                lost.set()
                return

    def _mailbox(self, control, identifier, binding, stream, cancel, deadline, route='EXISTING_EXIT'):
        local, remote = socket.socketpair()
        stopped = threading.Event()
        cancelled = Cancellation(cancel, stopped)
        writer = None
        local.settimeout(.2)

        def upload():
            finished_write = False
            try:
                while not cancelled.is_set():
                    try:
                        data = local.recv(16384)
                    except TimeoutError:
                        self._budget(deadline)
                        continue
                    if not data:
                        binding.lane.call('finish', stream=stream, budget_ms=self._budget(deadline), cancel=cancelled)
                        finished_write = True
                        break
                    result = binding.lane.call('write', stream=stream, data=base64.b64encode(data).decode(),
                                               budget_ms=self._budget(deadline), cancel=cancelled)
                    if result.get('count', 0) != len(data):
                        raise wire.BridgeError()
            except (OSError, ValueError, ChatError):
                pass
            finally:
                if not finished_write:
                    stopped.set()

        try:
            wire.write(control, dict(schema=1, id=identifier, ok=True, route=route))
            wire.send_socket(control, remote)
            remote.close()
            writer = threading.Thread(target=upload, name='fc-chat-mailbox-write', daemon=False)
            writer.start()
            while not cancelled.is_set():
                result = binding.lane.call('read', stream=stream, size=16384, budget_ms=self._budget(deadline), cancel=cancelled)
                data = result.get('data', b'')
                offset = 0
                while offset < len(data) and not cancelled.is_set():
                    self._budget(deadline)
                    try:
                        count = local.send(data[offset:])
                        if count == 0:
                            raise wire.BridgeError()
                        offset += count
                    except TimeoutError:
                        continue
                if result.get('eof'):
                    break
        finally:
            stopped.set()
            try:
                local.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                binding.lane.call('close', stream=stream)
            except (OSError, ValueError, ChatError):
                pass
            finally:
                if writer is not None:
                    writer.join(9)
                local.close()
                remote.close()
            if writer is not None and writer.is_alive():
                raise RuntimeError('Chat mailbox cleanup pending')

    def close(self):
        self.stop.set()
        if self.listener is not None:
            self.listener.close()
        if self.thread is not None:
            self.thread.join(2)
        with self.lock:
            active = list(self.active.items())
        for connection, _ in active:
            try:
                connection.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
        deadline = time.monotonic() + 20
        for _, thread in active:
            thread.join(max(0, deadline - time.monotonic()))
        if any(thread.is_alive() for _, thread in active):
            raise RuntimeError('Chat cleanup pending')
        remove_endpoint(self.endpoint, self.uid)
