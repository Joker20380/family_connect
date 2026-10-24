"""One real MESH attempt for the shared Auto owner; no local reconnect loop."""
import copy
import threading
import time

from auto_guard import candidate
from auto_policy import Failure, require
import mesh_ipc as ipc
from mesh_materials import MaterialsError, NativeMaterials
from mesh_service import NativeWorker, PacketSession, SessionFailure, TRANSIENT


def rejection(error):
    if isinstance(error, Failure):
        return error
    if isinstance(error, (MaterialsError, SessionFailure)):
        code = error.code
        if code == 'CANCELLED':
            return Failure('CANCELLED')
        if code in ('FAMILY_REJECTED', 'AUTH_OR_STARTUP_FAILED', 'AUTHORIZATION_REJECTED',
                    'NATIVE_VALIDATION_FAILED', 'BOOTSTRAP_VALIDATION_FAILED', 'EXPIRED_ON_IMPORT'):
            return Failure('AUTH')
        if code in ('CHALLENGE_TIMEOUT', 'CHALLENGE_TEMPORARY_SERVER_FAILURE',
                    'FETCH_TEMPORARY_SERVER_FAILURE', 'FETCH_NETWORK_FAILURE', 'MISSING'):
            return Failure('BOOTSTRAP_UNAVAILABLE', temporary=True)
        if code in TRANSIENT:
            return Failure('NETWORK')
    if isinstance(error, (EOFError, BrokenPipeError, TimeoutError)):
        return Failure('NETWORK')
    return Failure('INTERNAL')


class MeshCandidate:
    def __init__(self, network, materials_owner, materials, worker_factory=NativeWorker, ownership=None):
        ipc.validate_request(dict(schema=1, id=1, action='start', materials=materials))
        self.network, self.materials_owner = network, materials_owner
        self.materials = copy.deepcopy(materials)
        self.worker_factory, self.session = worker_factory, None
        self.ownership = ownership
        if ownership is not None:
            self.worker_factory = lambda: worker_factory(ownership)
            self.materials_owner.native = NativeMaterials(ownership)
        self.lock = threading.Lock()
        self.view_lock = threading.Lock()
        self.view = dict(attempt=0, native={}, readiness={})
        self.attempt, self.pending_cleanup, self.released = 0, False, False

    def chat_binding(self):
        if not self.lock.acquire(blocking=False):
            return None
        try:
            return self.session.chat_binding if self.session is not None and not self.released else None
        finally:
            self.lock.release()

    def prepare(self, context):
        context.check()
        require(not self.released and self.session is None and not self.pending_cleanup)
        return candidate('mesh', 'fcmesh0')

    def open(self, context):
        with self.lock:
            context.check()
            require(not self.released and self.session is None and not self.pending_cleanup)
            self.attempt += 1
            self.pending_cleanup = True
            try:
                if self.ownership is not None:
                    self.ownership.acquire(context.cancel, context.deadline)
                self.network.prepare()
                context.check()
                underlying = self.network.underlying()
                self.session = PacketSession(self.network, self.materials_owner, context.cancel,
                                             self.attempt, self.worker_factory)
                self.session.begin(self.materials, underlying, context.deadline, context.deadline)
                while True:
                    context.check()
                    state = self.session.poll()
                    context.check()
                    if state == 'CONNECTED':
                        index = self.network.record['packet_index']
                        require(type(index) is int and 0 < index < 2**31)
                        return index, False
                    context.cancel.wait(min(1, max(0, context.deadline - time.monotonic())))
            except Exception as error:
                raise rejection(error) from None
            finally:
                self._capture()

    def health(self, context):
        with self.lock:
            context.check()
            require(self.session is not None and not self.released)
            try:
                state = self.session.poll()
                context.check()
                if state != 'CONNECTED':
                    raise Failure('NETWORK')
                return True
            except Exception as error:
                raise rejection(error) from None
            finally:
                self._capture()

    def close(self, context):
        if self.session is not None:
            self.session.cancel.set()
        with self.lock:
            context.check()
            if self.session is not None:
                self.session.close()
                self.session = None
            if self.pending_cleanup:
                self.network.cleanup()
                context.check()
                require(not self.network.owns_journal)
                if self.ownership is not None and self.ownership.active:
                    self.ownership.finish()
                self.pending_cleanup = False

    def release(self, context):
        with self.lock:
            context.check()
            require(self.session is None and not self.pending_cleanup)
            self.materials.clear()
            self.released = True

    def _capture(self):
        with self.view_lock:
            self.view = dict(attempt=self.attempt, native=copy.deepcopy(self.session.snapshot) if self.session else {},
                             readiness=copy.deepcopy(self.materials_owner.summary))

    def snapshot(self):
        with self.view_lock:
            return copy.deepcopy(self.view)
