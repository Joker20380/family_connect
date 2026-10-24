#!/usr/bin/python3 -I
"""Root Auto service: UID-bound socket, memory-only credentials and native policy."""
import copy
from contextlib import contextmanager
import fcntl
import os
from pathlib import Path
import re
import signal
import socket
import stat
import subprocess
import sys
import threading
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
if __name__ == '__main__':
    from system_runtime import configure, shared_gate
    RUNTIME_GATE = shared_gate()
    configure()
import auto_ipc
from auto_configuration import NormalOwner
from auto_guard import DIRECTORY, Guard
from auto_intent import AutoIntent
from auto_mesh import MeshCandidate
from auto_normal import NormalCandidate
from auto_platform import HintStore, Platform
from auto_policy import Context, require
from auto_runtime import Coordinator
import mesh_ipc as ipc
from mesh_intent import Notifier
from mesh_materials import CacheStore, MaterialOwner, MaterialsError
from mesh_system import Network
from mesh_chat_host import Host as ChatHost, remove_endpoint as remove_chat_endpoint

SOCKET_DIRECTORY = Path('/run/family-connect-auto-ipc')
STATE = Path('/var/lib/family-connect-auto')
MESH_STATE = Path('/var/lib/family-connect-mesh')
RUNTIME_LOCK = Path('/run/family-connect-auto-runtime.lock')
COMMAND_LOCK = Path('/run/family-connect-auto-command.lock')


def directory(path, mode):
    try:
        path.mkdir(mode=mode)
        descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            require(os.fstat(descriptor).st_uid == 0)
            os.fchmod(descriptor, mode)
        finally:
            os.close(descriptor)
    except FileExistsError:
        pass
    info = path.lstat()
    if path == SOCKET_DIRECTORY and mode == 0o711 and stat.S_ISDIR(info.st_mode) and info.st_uid == 0 and stat.S_IMODE(info.st_mode) == 0o700:
        for index, entry in enumerate(path.iterdir()):
            require(index < 16)
            item = entry.lstat()
            require(stat.S_ISSOCK(item.st_mode) and 0 < item.st_uid < 2**31 and
                    entry.name == str(item.st_uid)+'.sock' and stat.S_IMODE(item.st_mode) == 0o600)
        descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fchmod(descriptor, mode)
        finally:
            os.close(descriptor)
        info = path.lstat()
    require(stat.S_ISDIR(info.st_mode) and info.st_uid == 0 and stat.S_IMODE(info.st_mode) == mode)


def locked(path):
    descriptor = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    try:
        info = os.fstat(descriptor)
        require(stat.S_ISREG(info.st_mode) and info.st_uid == 0 and info.st_nlink == 1 and stat.S_IMODE(info.st_mode) == 0o600)
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def mesh_network(guard):
    return Network(guard.directory / 'mesh.json', guard.uid, auto_guard=guard)


@contextmanager
def command_gate():
    descriptor = locked(COMMAND_LOCK)
    try:
        yield
    finally:
        os.close(descriptor)


def manage_unit(action, uid):
    require(action in ('start', 'stop') and type(uid) is int and 0 < uid < 2**31)
    subprocess.run(['/usr/bin/systemctl', action, 'family-connect-auto@'+str(uid)+'.service'],
                   check=True, timeout=60, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                   env={'PATH': '/usr/sbin:/usr/bin:/sbin:/bin', 'HOME': '/root', 'LANG': 'C'})


def read_catalog(uid):
    storage = CacheStore(STATE, uid)
    try:
        raw = storage.read()
        return None if raw is None else auto_ipc.catalog(ipc.decode(raw, 16384))
    finally:
        storage.close()


def reconcile(record, keep):
    require(type(keep) is bool)
    if not any(os.path.lexists(DIRECTORY / name) for name in ('guard.json', 'normal.json', 'mesh.json')):
        return
    require(record is not None)
    with Guard(record['uid'], record['generation']) as guard:
        guard.acquire()
        NormalCandidate(guard).close(Context(20000))
        network = mesh_network(guard)
        if os.path.lexists(network.journal):
            network.restore()
            network.cleanup()
            require(not network.owns_journal)
        if not keep:
            guard.release()


class Runtime:
    def __init__(self, record, selection, terminal):
        self.guard, self.stores, self.coordinator = None, [], None
        try:
            self.guard = Guard(record['uid'], record['generation'])
            descriptor = locked('/run/family-connect-transport.lock')
            try:
                existing = os.path.lexists(self.guard.path)
                require(not os.path.lexists('/run/family-connect-mesh/active.json'))
                if not existing:
                    require(not os.path.lexists('/run/family-connect-tcp/active'))
                    require(not os.path.lexists('/run/family-connect-awg/active.json'))
                    require(not any(re.fullmatch(r'fc(?:mesh0|(?:awg|tcp)[a-f0-9]{8})', item.get('ifname', ''))
                                    for item in self.guard.system.links()))
                self.guard.acquire()
            finally:
                os.close(descriptor)
            for path, receipts in ((STATE, False), (MESH_STATE, False), (MESH_STATE, True)):
                self.stores.append(CacheStore(path, record['uid'], receipt=receipts))
            material = selection['materials']
            from mesh_ownership import Ownership
            mesh = MeshCandidate(mesh_network(self.guard), MaterialOwner(self.stores[1], self.stores[2]),
                                 {key: material[key] for key in ('identity', 'wireguard_public', 'anchor', 'profile')},
                                 ownership=Ownership('vpn'))
            self.platform = Platform(self.guard, NormalOwner(self.stores[0]), mesh, material,
                                     hints=HintStore(STATE / (str(record['uid']) + '.hint.json'), record['uid']),
                                     preferred=selection['preferred'])
            self.preferred, self.last = selection['preferred'], self.platform.hints.last(material['country'])
            self.coordinator = Coordinator(self.guard, self.platform, record['recoveries'] + 1,
                                           terminal=terminal, guard_prepared=True)
        except BaseException:
            self.dispose()
            raise

    def start(self):
        self.coordinator.start(self.preferred, self.last)

    def dispose(self):
        if self.coordinator is not None and self.coordinator.thread is not None:
            require(not self.coordinator.thread.is_alive())
        for storage in self.stores:
            storage.close()
        if self.guard is not None:
            self.guard.close()


class Controller:
    def __init__(self, intent, factory=Runtime, cleanup=reconcile, *, gate=command_gate, catalog=read_catalog):
        self.intent, self.factory, self.cleanup = intent, factory, cleanup
        self.gate, self.catalog = gate, catalog
        self.lock = threading.RLock()
        self.cancel = threading.Event()
        self.thread, self.runtime = None, None
        self.record = intent.read()
        self.state, self.reason, self.requested = 'DISCONNECTED', '', ''
        self.stopping, self.fatal = False, False
        self.desired = self.record is not None and self.record['desired']

    def chat_binding(self):
        with self.lock:
            runtime = self.runtime
            if runtime is None or self.cancel.is_set() or self.stopping:
                return None
        return runtime.platform.mesh.chat_binding()

    def terminal(self):
        with self.lock:
            try:
                self.intent.revoke()
            finally:
                self.desired = False

    def recover(self, selection):
        if not self.desired:
            return
        if selection is None:
            self.state, self.reason = 'FAILED', 'RECOVERY_CREDENTIAL_UNAVAILABLE'
            return
        self.launch(selection, restoring=True)

    def launch(self, selection, restoring=False):
        auto_ipc.selection(selection)
        with self.lock:
            require(self.thread is None and not self.stopping)
            self.state, self.reason = ('RESTORING' if restoring else 'CONNECTING'), ''
            self.requested = selection['materials']['profile']
            self.cancel.clear()
            self.thread = threading.Thread(target=self.run, args=(copy.deepcopy(selection),), name='fc-auto-owner', daemon=False)
            self.thread.start()

    def start(self, selection):
        with self.lock, self.gate():
            self.reap()
            if self.stopping or self.fatal or self.state != 'DISCONNECTED' or self.thread is not None or self.desired:
                return False
            try:
                self.intent.begin(selection)
            except Exception:
                self.state, self.reason, self.fatal = 'FAILED', 'INTENT_PERSISTENCE_FAILED', True
                raise
            self.record, self.desired = self.intent.read(), True
            self.launch(selection)
            return True

    def stop(self, generation):
        with self.lock:
            self.reap()
            if self.record is None or generation != self.record['generation']:
                return False
            if self.state == 'DISCONNECTED' and self.thread is None and not self.desired and not self.fatal:
                self.terminal()
                return True
            try:
                self.terminal()
            finally:
                if not self.fatal:
                    self.state = 'DISCONNECTING'
                self.cancel.set()
                if self.thread is None:
                    self.thread = threading.Thread(target=self.run, args=(None,), name='fc-auto-cleanup', daemon=False)
                    self.thread.start()
            return True

    def run(self, selection):
        runtime = None
        try:
            if selection is not None and not self.cancel.is_set():
                runtime = self.factory(self.record, selection, self.terminal)
                with self.lock:
                    self.runtime = runtime
                if not self.cancel.is_set():
                    runtime.start()
                    while not self.cancel.wait(.25):
                        coordinator = runtime.coordinator
                        if coordinator.failed or (coordinator.thread is not None and not coordinator.thread.is_alive()):
                            raise RuntimeError('Auto controller terminated')
                with self.lock:
                    keep = self.desired
                if runtime.coordinator.thread is not None:
                    (runtime.coordinator.abort if keep else runtime.coordinator.close)()
                else:
                    runtime.dispose()
                    runtime = None
                    self.cleanup(self.record, keep)
            else:
                self.cleanup(self.record, self.desired)
            with self.lock:
                if not self.desired:
                    self.intent.notifier.remove()
                    self.intent.close()
        except Exception:
            with self.lock:
                self.state, self.reason, self.fatal = 'FAILED', 'INTERNAL', True
            if runtime is not None and runtime.coordinator.thread is not None:
                try:
                    runtime.coordinator.abort()
                except Exception:
                    pass
        finally:
            if selection is not None:
                selection['materials'].clear()
                selection.clear()
            if runtime is not None:
                try:
                    runtime.dispose()
                except Exception:
                    with self.lock:
                        self.state, self.reason, self.fatal = 'FAILED', 'INTERNAL', True
            with self.lock:
                self.runtime = None

    def reap(self):
        with self.lock:
            if self.thread is not None and not self.thread.is_alive():
                self.thread.join()
                self.thread = None
                if not self.fatal and not self.desired:
                    self.state, self.reason = 'DISCONNECTED', ''

    def status(self):
        with self.lock:
            self.reap()
            status = dict(state=self.state, reason=self.reason, generation=self.record['generation'] if self.record else '',
                          desired_connected=self.desired, requested_profile=self.requested, controller=None)
            if self.runtime is not None and not self.fatal:
                status['controller'] = self.runtime.coordinator.status()
                if not self.cancel.is_set() and self.runtime.coordinator.thread is not None:
                    status['state'] = status['controller']['policy']['state']
            return status

    def shutdown(self):
        with self.lock:
            self.stopping = True
            self.cancel.set()
            thread = self.thread
        if thread is not None:
            thread.join(timeout=40)
            require(not thread.is_alive())
        require(not self.fatal)


def dispatch(controller, request):
    auto_ipc.validate_request(request)
    action = request['action']
    if action == 'catalog':
        try:
            catalog = controller.catalog(controller.intent.uid)
            if catalog is not None:
                auto_ipc.catalog(catalog)
            return dict(schema=1, id=request['id'], ok=True, catalog=catalog)
        except (OSError, ValueError, MaterialsError):
            return dict(schema=1, id=request['id'], ok=False, catalog=None)
    accepted = controller.start(request['selection']) if action == 'start' else controller.stop(request['generation']) if action == 'stop' else True
    return dict(schema=1, id=request['id'], ok=accepted, **controller.status())


def respond(connection, uid, controller):
    request = {}
    try:
        if ipc.peer_uid(connection) != uid:
            return
        request = ipc.receive(connection.fileno(), auto_ipc.MAX_REQUEST, time.monotonic() + 4)
        reply = dispatch(controller, request)
        ipc.send(connection.fileno(), reply, auto_ipc.MAX_REPLY, time.monotonic() + 4)
    finally:
        if isinstance(request.get('selection'), dict):
            if isinstance(request['selection'].get('materials'), dict):
                request['selection']['materials'].clear()
            request['selection'].clear()
        request.clear()


def remove_socket(uid):
    endpoint = SOCKET_DIRECTORY / (str(uid) + '.sock')
    if os.path.lexists(endpoint):
        info = endpoint.lstat()
        require(stat.S_ISSOCK(info.st_mode) and info.st_uid == uid and stat.S_IMODE(info.st_mode) == 0o600)
        endpoint.unlink()


def serve(uid):
    notifier = Notifier('family-connect-auto@' + str(uid) + '.service', name=AutoIntent.name)
    intent = AutoIntent(DIRECTORY / (str(uid) + '.intent.json'), uid, notifier)
    selection = intent.recover()
    descriptor = locked(RUNTIME_LOCK)
    controller, listener = None, None
    chat = None
    try:
        directory(DIRECTORY, 0o700)
        directory(SOCKET_DIRECTORY, 0o711)
        directory(STATE, 0o700)
        directory(MESH_STATE, 0o700)
        reconcile(intent.read(), intent.desired())
        remove_socket(uid)
        listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        endpoint = SOCKET_DIRECTORY / (str(uid) + '.sock')
        listener.bind(str(endpoint))
        os.chmod(endpoint, 0o600)
        os.chown(endpoint, uid, 0)
        listener.listen(4)
        listener.settimeout(1)
        controller = Controller(intent)
        chat = ChatHost(SOCKET_DIRECTORY / (str(uid) + '.chat.sock'), uid, controller.chat_binding)
        chat.start()
        controller.recover(selection)
        if selection is not None:
            selection['materials'].clear()
            selection.clear()
        stopping = threading.Event()
        signal.signal(signal.SIGTERM, lambda *_: stopping.set())
        signal.signal(signal.SIGINT, lambda *_: stopping.set())
        notifier.ready()
        while not stopping.is_set():
            controller.reap()
            require(not controller.fatal)
            try:
                connection, _ = listener.accept()
            except TimeoutError:
                continue
            with connection:
                connection.setblocking(False)
                try:
                    respond(connection, uid, controller)
                except (OSError, EOFError, ValueError, TimeoutError):
                    pass
    finally:
        if listener is not None:
            listener.close()
        try:
            if controller is not None:
                controller.shutdown()
        finally:
            if chat is not None:
                chat.close()
        remove_socket(uid)
        intent.close()
        os.close(descriptor)


def cleanup(uid):
    descriptor = locked(RUNTIME_LOCK)
    try:
        directory(DIRECTORY, 0o700)
        directory(SOCKET_DIRECTORY, 0o711)
        intent = AutoIntent(DIRECTORY / (str(uid) + '.intent.json'), uid)
        reconcile(intent.read(), intent.desired())
        remove_socket(uid)
        remove_chat_endpoint(SOCKET_DIRECTORY / (str(uid) + '.chat.sock'), uid)
    finally:
        os.close(descriptor)


def main():
    require(os.geteuid() == 0 and not os.environ.get('PKEXEC_UID') and len(sys.argv) == 3)
    action, raw_uid = sys.argv[1:]
    require(action in ('serve', 'cleanup') and raw_uid.isascii() and raw_uid.isdecimal())
    uid = int(raw_uid)
    require(str(uid) == raw_uid and 0 < uid < 2**31)
    (serve if action == 'serve' else cleanup)(uid)


if __name__ == '__main__':
    try:
        main()
    except Exception:
        print('Auto service failed; use the bounded application diagnostic export.', file=sys.stderr, flush=True)
        os._exit(1)
