"""Demand-driven chat MESH generation, never a packet/VPN session."""
import base64
import fcntl
import hashlib
import os
from pathlib import Path
import signal
import stat
import sys
import threading
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from auto_platform import Underlying
from auto_policy import Failure
from mesh_chat_host import Binding, Cancellation, Host
from mesh_materials import CacheStore, MaterialOwner, MaterialsError, NativeMaterials
from mesh_ownership import Ownership, OwnershipError, locked_file, prepare_runtime
from mesh_service import NativeWorker
from provisioning import chat_bridge_protocol as wire


class Context:
    def __init__(self, cancel, deadline):
        self.cancel, self.deadline = cancel, deadline

    def check(self):
        if self.cancel.is_set():
            raise wire.BridgeError('CANCELLED')
        if time.monotonic() >= self.deadline:
            raise wire.BridgeError('DEADLINE')


def packaged_anchor(path):
    for parent in path.parents:
        info = parent.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o022:
            raise ValueError('Unsafe packaged anchor')
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as source:
        info = os.fstat(source.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_nlink != 1 or info.st_mode & 0o022:
            raise ValueError('Unsafe packaged anchor')
        raw = source.read(129)
    if len(raw) > 128 or len(base64.b64decode(raw.strip(), validate=True)) != 32:
        raise ValueError('Invalid packaged anchor')
    return raw.strip().decode('ascii')


class ServiceOwner:
    def __init__(self, materials, anchor, *, underlying=None, ownership_factory=Ownership, worker_factory=NativeWorker):
        self.materials, self.anchor = materials, anchor
        self.underlying = underlying or Underlying()
        self.ownership_factory, self.worker_factory = ownership_factory, worker_factory
        self.lock = threading.Lock()
        self.cancel = threading.Event()
        self.stopped = threading.Event()
        self.gate = self.worker = self.current = None
        self.generation_lease = None
        self.network = None
        self.fingerprint = None
        self.touched = 0
        self.failed = False
        self.watcher = threading.Thread(target=self._watch, name='fc-chat-mesh-generation', daemon=False)
        self.watcher.start()

    def prepare(self, request, cancelled, deadline):
        if not self.lock.acquire(timeout=max(0, min(1, deadline - time.monotonic()))):
            raise wire.BridgeError()
        start, material = {}, {}
        try:
            if self.failed or self.stopped.is_set():
                raise wire.BridgeError()
            if self.current is not None:
                self.current.probe(request['device'])
                fingerprint = hashlib.sha256((request['identity'] + request['wireguard_public']).encode('ascii')).digest()
                if fingerprint != self.fingerprint:
                    raise wire.BridgeError('DENIED')
                if self.current.material['readiness']['expires_at'] > time.time():
                    Context(Cancellation(cancelled, self.cancel, self.stopped), deadline).check()
                    self.touched = time.monotonic()
                    return self.current
                self.cancel.set()
                self._cleanup_locked()
            if self.gate is None:
                self.cancel = threading.Event()
                self.gate = self.ownership_factory('chat')
                self.gate.acquire(Cancellation(cancelled, self.cancel, self.stopped), deadline)
            cancel = Cancellation(cancelled, self.cancel, self.stopped)
            context = Context(cancel, deadline)
            context.check()
            network = self.underlying.read(context)
            if self.network is not None and self.network != network:
                self.cancel.set()
                raise wire.BridgeError('CANCELLED')
            self.network = network
            material = dict(identity=request['identity'], wireguard_public=request['wireguard_public'],
                            anchor=self.anchor, profile='P0')
            self.materials.native = NativeMaterials(self.gate)
            start = self.materials.resolve(material, network['index'], cancel, deadline, True)
            context.check()
            if start['readiness'].get('device') != request['device']:
                raise wire.BridgeError('DENIED')
            start.update(resolver='1.1.1.1:53', underlying_index=network['index'])
            if self.worker is None:
                self.worker = self.worker_factory(self.gate)
            if self.current is not None:
                self.current.close()
            self.current = Binding(self.worker.chat, start, self.cancel, 'SERVICE_ONLY')
            self.fingerprint = hashlib.sha256((request['identity'] + request['wireguard_public']).encode('ascii')).digest()
            self.current.ready.set()
            self.generation_lease = self.current.acquire(request['device'], cancel, Host._budget(deadline))
            self.touched = time.monotonic()
            context.check()
            return self.current
        except MaterialsError as error:
            self.cancel.set()
            code = error.code
            if code not in ('CANCELLED', 'DEADLINE'):
                code = 'UNAVAILABLE' if code in ('FETCH_NETWORK_FAILURE', 'FETCH_TEMPORARY_SERVER_FAILURE',
                    'CHALLENGE_TIMEOUT', 'CHALLENGE_TEMPORARY_SERVER_FAILURE', 'MISSING') else 'DENIED'
            raise wire.BridgeError(code) from None
        except (OwnershipError, BlockingIOError, Failure):
            self.cancel.set()
            raise wire.BridgeError() from None
        except BaseException:
            self.cancel.set()
            raise
        finally:
            start.clear()
            material.clear()
            self.lock.release()

    def binding(self):
        with self.lock:
            if self.failed or self.cancel.is_set() or self.stopped.is_set():
                return None
            self.touched = time.monotonic()
            return self.current

    def _cleanup(self):
        with self.lock:
            self._cleanup_locked()

    def _cleanup_locked(self):
        self.cancel.set()
        if self.current is not None:
            self.current.close()
            if self.generation_lease is not None:
                self.current.release(self.generation_lease)
                self.generation_lease = None
            self.current = None
        if self.worker is not None:
            self.worker.close()
            self.worker = None
        if self.gate is not None:
            if self.gate.active:
                self.gate.finish()
            else:
                self.gate.close()
            self.gate = None
        self.network = self.fingerprint = None
        self.touched = 0

    def _watch(self):
        while not self.stopped.wait(.1):
            gate = self.gate
            cancel, network = self.cancel, self.network
            if gate is None:
                continue
            try:
                if gate.preempted() or (self.touched and time.monotonic() - self.touched > 45):
                    cancel.set()
                with self.lock:
                    if (self.gate is gate and self.cancel is cancel and self.current is not None and
                            self.current.material['readiness']['expires_at'] <= time.time()):
                        cancel.set()
                if network is not None and not cancel.is_set():
                    current = self.underlying.read(Context(cancel, time.monotonic() + 2))
                    if network != current:
                        cancel.set()
            except (OSError, ValueError, Failure):
                cancel.set()
            if cancel.is_set():
                try:
                    with self.lock:
                        if self.gate is gate and self.cancel is cancel:
                            self._cleanup_locked()
                except Exception:
                    self.failed = True
                    return

    def close(self):
        self.stopped.set()
        self.cancel.set()
        self.watcher.join(10)
        if self.watcher.is_alive() or self.failed:
            raise RuntimeError('CLEANUP_UNCONFIRMED')
        self._cleanup()


class ServiceHost(Host):
    validate = staticmethod(wire.validate_service)

    def __init__(self, endpoint, uid, owner):
        super().__init__(endpoint, uid, owner.binding)
        self.owner = owner

    def binding(self, request, cancel, deadline):
        if request['action'] == 'prepare':
            return self.owner.prepare(request, cancel, deadline)
        return super().binding(request, cancel, deadline)


def main():
    if os.geteuid() != 0 or len(sys.argv) != 2 or not sys.argv[1].isascii() or not sys.argv[1].isdigit() or not 0 < int(sys.argv[1]) < 2**31:
        raise SystemExit('Root chat service requires one desktop UID')
    uid = int(sys.argv[1])
    directory = Path('/run/family-connect-chat-mesh')
    prepare_runtime(directory)
    descriptor = locked_file(directory / (str(uid) + '.lock'))
    fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    storage = CacheStore('/var/lib/family-connect-mesh', uid)
    receipts = CacheStore('/var/lib/family-connect-mesh', uid, receipt=True)
    owner = ServiceOwner(MaterialOwner(storage, receipts), packaged_anchor(Path(__file__).with_name('update.pub')))
    host = ServiceHost(directory / (str(uid) + '.chat.sock'), uid, owner)
    stopping = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stopping.set())
    signal.signal(signal.SIGINT, lambda *_: stopping.set())
    try:
        host.start()
        stopping.wait()
    finally:
        owner.cancel.set()
        try:
            host.close()
            owner.close()
        finally:
            storage.close()
            receipts.close()
            os.close(descriptor)


if __name__ == '__main__':
    main()
