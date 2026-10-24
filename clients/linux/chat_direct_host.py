"""Root-owned fixed chat service, independent of VPN ownership and user endpoints."""
import base64
import fcntl
from contextlib import contextmanager
import ipaddress
import json
import os
from pathlib import Path
import signal
import socket
import stat
import subprocess
import sys
import threading
import time
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
if __name__ == '__main__':
    from system_runtime import configure, shared_gate
    RUNTIME_GATE = shared_gate()
    configure()
from auto_platform import Underlying
from auto_policy import Failure
from auto_normal_worker import trusted
from mesh_chat_host import Host, Cancellation
from mesh_ipc import peer_uid
from provisioning import chat_bridge_protocol as wire
from provisioning.chat_direct import authority_digest, validate
from provisioning.friends import FriendsClient, FriendsError


class Context:
    def __init__(self, cancel, deadline):
        self.cancel, self.deadline = cancel, deadline

    def check(self):
        if self.cancel.is_set():
            raise wire.BridgeError('CANCELLED')
        if time.monotonic() >= self.deadline:
            raise wire.BridgeError('DEADLINE')


class Native:
    def __init__(self, worker=Path('/usr/local/lib/family-connect-mesh/fc-mesh'), underlying=None):
        self.worker, self.underlying = Path(worker), underlying or Underlying()

    @contextmanager
    def operation(self, cancel, deadline, **fields):
        context = Context(cancel, deadline)
        context.check()
        path = self.underlying.read(context)
        for parent in (self.worker, *self.worker.parents):
            trusted(parent, parent != self.worker)
        local, remote = socket.socketpair()
        process, monitor = None, None
        failure = None
        done, invalid = threading.Event(), threading.Event()

        def watch():
            checking = Context(Cancellation(cancel, done), deadline)
            while not done.wait(.1):
                try:
                    checking.check()
                    if self.underlying.read(checking) != path:
                        raise wire.BridgeError()
                except (OSError, ValueError, Failure):
                    invalid.set()
                    try:
                        process.terminate()
                        local.shutdown(socket.SHUT_RDWR)
                    except OSError:
                        pass
                    return

        try:
            process = subprocess.Popen([str(self.worker), '--chat-direct-fd', str(remote.fileno())],
                pass_fds=(remote.fileno(),), stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            remote.close()
            monitor = threading.Thread(target=watch, name='fc-chat-direct-cancel', daemon=False)
            monitor.start()
            wire.write(local, dict(index=path['index'], name=path['name'], budget_ms=Host._budget(deadline), **fields))
            reply = wire.read(local, deadline)
            if reply.get('code') != 'OK':
                if set(reply) != {'code'} or reply.get('code') not in wire.ERRORS:
                    raise wire.BridgeError('INVALID_RESPONSE')
                raise wire.BridgeError(reply['code'])
            context.check()
            if invalid.is_set() or path != self.underlying.read(context):
                raise wire.BridgeError()
            expected = {'code', 'status', 'data'} if fields['action'] == 'request' and reply.get('status') == 200 else {'code', 'status'} if fields['action'] == 'request' else {'code'}
            if set(reply) != expected:
                raise wire.BridgeError('INVALID_RESPONSE')
            if fields['action'] == 'request':
                if type(reply['status']) is not int or not 100 <= reply['status'] <= 599:
                    raise wire.BridgeError('INVALID_RESPONSE')
                reply['data'] = wire.payload(reply.get('data', ''), 16384)
            yield reply, local
        except BaseException as error:
            failure = error
            if isinstance(error, OSError) and getattr(error, 'code', None) not in ('DENIED', 'CONFLICT', 'INVALID_RESPONSE'):
                try:
                    context.check()
                except wire.BridgeError as cancelled:
                    failure = cancelled
            raise failure
        finally:
            try:
                done.set()
                if monitor is not None:
                    monitor.join(6)
                local.close()
                remote.close()
                if process is not None:
                    if process.poll() is None:
                        process.terminate()
                    try:
                        process.wait(2)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(2)
                if monitor is not None and monitor.is_alive():
                    raise RuntimeError('DIRECT cleanup pending')
            except (OSError, subprocess.SubprocessError, RuntimeError):
                if failure is not None:
                    raise failure from None
                raise wire.BridgeError('DENIED') from None


class Authority:
    def __init__(self, clock=time.time):
        self.clock = clock
        self.lock = threading.RLock()
        self.device = self.public = None
        self.response = None
        self.sequence = 0
        self.digest = None
        self.revoked = threading.Event()

    def probe(self, device):
        with self.lock:
            if self.device is None:
                self.device = device
            if device != self.device:
                raise wire.BridgeError('DENIED')

    def revoke(self):
        with self.lock:
            self.revoked.set()
            self.response = None

    def registered(self, device, public, raw, context=None):
        try:
            response = json.loads(raw, object_pairs_hook=wire.pairs)
            if type(response) is not dict:
                raise ValueError()
            active = response.get('status') == 'active'
            FriendsClient._fields(response, 'device chat_public status' + (' node' if active else ''))
            if response['device'] != device or response['chat_public'] != public or response['status'] not in ('active', 'pending-node'):
                raise ValueError()
            with self.lock:
                self.probe(device)
                if context is not None:
                    context.check()
                if self.public is not None and self.public != public:
                    raise ValueError()
                self.revoke()
                self.public = public
                if not active:
                    return
                node = response['node']
                FriendsClient._fields(node, 'sequence expires_at host port public_key')
                FriendsClient._integer(node['sequence'], 1)
                FriendsClient._integer(node['expires_at'], 1)
                FriendsClient._integer(node['port'], 1)
                address = ipaddress.IPv4Address(node['host'])
                from messenger.codec import identity
                identity(bytes.fromhex(node['public_key']))
                if (str(address) != node['host'] or address.is_loopback or address.is_multicast or address.is_unspecified or address.is_link_local or
                        node['port'] > 65535 or not self.clock() < node['expires_at'] <= self.clock() + 120 or
                        type(node['public_key']) is not str or len(node['public_key']) != 128 or node['public_key'].lower() != node['public_key']):
                    raise ValueError()
                digest = authority_digest({key: node[key] for key in ('sequence', 'host', 'port', 'public_key')})
                if node['sequence'] < self.sequence or (node['sequence'] == self.sequence and digest != self.digest):
                    raise ValueError()
                self.sequence, self.digest = node['sequence'], digest
                if context is not None:
                    context.check()
                self.revoked = threading.Event()
                self.response = response
        except wire.BridgeError:
            self.revoke()
            raise
        except (ValueError, TypeError, KeyError, FriendsError):
            self.revoke()
            raise wire.BridgeError('INVALID_RESPONSE') from None

    def acquire(self, device, digest):
        with self.lock:
            self.probe(device)
            if self.response is None:
                raise wire.BridgeError('DENIED' if self.revoked.is_set() else 'UNAVAILABLE')
            if self.response['node']['expires_at'] <= self.clock():
                self.revoke()
                raise wire.BridgeError('DENIED')
            if digest != authority_digest(self.response):
                raise wire.BridgeError('DENIED')
            return dict(self.response['node']), self.revoked


class SocketLane:
    def __init__(self, channel):
        self.channel = channel

    def call(self, action, **values):
        if action == 'close':
            self.channel.close()
            return {}
        context = Context(values['cancel'], time.monotonic() + values['budget_ms'] / 1000)
        context.check()
        self.channel.settimeout(.2)
        if action == 'finish':
            self.channel.shutdown(socket.SHUT_WR)
            return {}
        if action == 'write':
            data = wire.payload(values['data'], 16384)
            offset = 0
            while offset < len(data):
                context.check()
                try:
                    count = self.channel.send(data[offset:])
                    if not count:
                        raise wire.BridgeError()
                    offset += count
                except TimeoutError:
                    continue
            return dict(count=offset)
        while True:
            context.check()
            try:
                data = self.channel.recv(values['size'])
                return dict(data=data, eof=not data)
            except TimeoutError:
                continue


class DirectHost(Host):
    def __init__(self, endpoint, uid, native=None, authority=None):
        super().__init__(endpoint, uid, None)
        self.native, self.authority = native or Native(), authority or Authority()
        self.request_lock = threading.Lock()

    def _serve(self, connection):
        request = {}
        lost, monitor_stop = threading.Event(), threading.Event()
        monitor = None
        try:
            if peer_uid(connection) != self.uid:
                return
            request = wire.read(connection, time.monotonic() + 4)
            validate(request)
            self.authority.probe(request['device'])
            if request['action'] == 'probe':
                wire.write(connection, dict(schema=1, id=request['id'], ok=True, route='DIRECT'))
                return
            cancel = Cancellation(self.stop, lost)
            deadline = time.monotonic() + request['budget_ms'] / 1000
            monitor = threading.Thread(target=self._monitor, args=(connection, lost, monitor_stop), name='fc-direct-disconnect', daemon=False)
            monitor.start()
            if request['action'] == 'request':
                if not self.request_lock.acquire(blocking=False):
                    raise wire.BridgeError()
                published = False
                try:
                    with self.native.operation(cancel, deadline, action='request', path=request['path'], data=request['data']) as (reply, _):
                        Context(cancel, deadline).check()
                        if request['path'] == wire.PATHS[1] and reply['status'] == 200:
                            body = json.loads(wire.payload(request['data'], 8192))
                            self.authority.registered(request['device'], body['chat_public'], reply['data'], Context(cancel, deadline))
                            published = True
                            Context(cancel, deadline).check()
                        wire.write(connection, dict(schema=1, id=request['id'], ok=True, route='DIRECT', status=reply['status'], data=base64.b64encode(reply['data']).decode()))
                except OSError as error:
                    if published or getattr(error, 'code', None) in ('DENIED', 'CONFLICT', 'INVALID_RESPONSE'):
                        self.authority.revoke()
                    raise
                finally:
                    self.request_lock.release()
            else:
                node, revoked = self.authority.acquire(request['device'], request['authority'])
                cancel = Cancellation(cancel, revoked)
                deadline = min(deadline, time.monotonic() + node['expires_at'] - self.authority.clock())
                with self.native.operation(cancel, deadline, action='open', host=node['host'], port=node['port']) as (_, channel):
                    Context(cancel, deadline).check()
                    monitor_stop.set()
                    monitor.join(1)
                    self._mailbox(connection, request['id'], SimpleNamespace(lane=SocketLane(channel)), 1, cancel, deadline, route='DIRECT')
        except (OSError, ValueError, Failure, RecursionError) as error:
            if type(request.get('id')) is int:
                try:
                    code = 'DENIED' if isinstance(error, (ValueError, RecursionError)) else getattr(error, 'code', 'UNAVAILABLE')
                    wire.write(connection, dict(schema=1, id=request['id'], ok=False, error=code if code in wire.ERRORS else 'UNAVAILABLE'))
                except (OSError, ValueError):
                    pass
        finally:
            lost.set()
            monitor_stop.set()
            if monitor is not None:
                monitor.join(1)
            request.clear()
            with self.lock:
                connection.close()
                self.active.pop(connection, None)

    def close(self):
        self.authority.revoke()
        super().close()


def prepare_runtime(directory):
    for parent in reversed(directory.parents):
        trusted(parent, True)
    directory.mkdir(mode=0o711, exist_ok=True)
    expected = trusted(directory, True)
    descriptor = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        actual = os.fstat(descriptor)
        if (actual.st_dev, actual.st_ino) != (expected.st_dev, expected.st_ino):
            raise ValueError('Unsafe chat runtime')
        os.fchmod(descriptor, 0o711)
    finally:
        os.close(descriptor)


def main():
    if len(sys.argv) != 2 or os.geteuid() != 0 or not sys.argv[1].isdigit() or not 0 < int(sys.argv[1]) < 2**31:
        raise SystemExit('Root chat service requires one desktop UID')
    uid = int(sys.argv[1])
    directory = Path('/run/family-connect-chat-direct')
    prepare_runtime(directory)
    descriptor = os.open(directory / (str(uid) + '.lock'), os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    expected = trusted(directory / (str(uid) + '.lock'))
    actual = os.fstat(descriptor)
    if ((actual.st_dev, actual.st_ino) != (expected.st_dev, expected.st_ino) or
            stat.S_IMODE(actual.st_mode) != 0o600):
        os.close(descriptor)
        raise ValueError('Unsafe chat lock')
    fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    host = DirectHost(directory / (str(uid) + '.chat.sock'), uid)
    stopping = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stopping.set())
    signal.signal(signal.SIGINT, lambda *_: stopping.set())
    try:
        host.start()
        stopping.wait()
    finally:
        host.close()
        os.close(descriptor)


if __name__ == '__main__':
    main()
