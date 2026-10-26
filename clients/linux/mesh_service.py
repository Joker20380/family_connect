"""Single-owner MESH supervisor with native validation and private atomic cache."""
import copy
import os
import socket
import subprocess
import threading
import time

import mesh_ipc as ipc
from mesh_chat import ChatLane
from mesh_chat_host import Binding
from mesh_materials import MaterialsError, NativeMaterials
from mesh_system import ENV

WORKER = "/usr/local/lib/family-connect-mesh/fc-mesh"
TRANSIENT = frozenset(("DEADLINE", "NETWORK_TIMEOUT", "NETWORK_ERROR", "EOF", "IO_CLOSED", "RELIABLE_CLOSED",
                       "REMOTE_RESET", "RELIABLE_EXHAUSTED", "WORKER_EXITED", "UNDERLAY_UNAVAILABLE", "UNDERLAY_CHANGED",
                       "HEALTH_UNAVAILABLE", "MISSING", "EXPIRED_ON_IMPORT", "CHALLENGE_TIMEOUT", "CHALLENGE_TEMPORARY_SERVER_FAILURE",
                       "FETCH_TEMPORARY_SERVER_FAILURE", "FETCH_NETWORK_FAILURE"))
CLEANUP_REASONS = frozenset(('CHAT_BINDING_CLEANUP_FAILED', 'WORKER_REAP_FAILED', 'WORKER_READER_FAILED',
                             'WORKER_DESCRIPTOR_FAILED', 'WORKER_CLEANUP_FAILED', 'NETWORK_DETACH_FAILED',
                             'NETWORK_CLEANUP_FAILED'))


class NativeWorker:
    def __init__(self, ownership=None):
        parent, child = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
        inherited = (child.fileno(),) if ownership is None else (child.fileno(), ownership.descriptor)
        try:
            self.process = subprocess.Popen([WORKER, "--stdio-chat-fd", str(child.fileno())], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                            stderr=subprocess.DEVNULL, env=ENV, bufsize=0, close_fds=True, pass_fds=inherited)
        except BaseException:
            parent.close()
            raise
        finally:
            child.close()
        self.chat = ChatLane(parent)
        self.identifier = 0
        self.close_lock = threading.Lock()
        self.close_done = False
        self.cleanup_reason = None

    def call(self, action, start=None):
        if self.process.poll() is not None:
            raise EOFError("MESH worker exited")
        self.identifier += 1
        request = {"schema": 1, "id": self.identifier, "action": action}
        if start is not None:
            request["start"] = start
        deadline = time.monotonic() + 4
        ipc.send(self.process.stdin.fileno(), request, ipc.MAX_REQUEST, deadline)
        reply = ipc.receive(self.process.stdout.fileno(), ipc.MAX_REPLY, deadline)
        if reply.get("schema") != 1 or reply.get("id") != self.identifier or type(reply.get("ok")) is not bool:
            raise ipc.ProtocolError()
        if set(reply) - {"schema", "id", "ok", "state", "error", "interface", "mtu", "snapshot"}:
            raise ipc.ProtocolError()
        return reply

    def _reap(self, deadline):
        if self.process.poll() is None:
            try:
                self.call('stop')
            except Exception:
                try:
                    self.process.terminate()
                except OSError:
                    pass
        for action in (None, self.process.terminate, self.process.kill):
            if action is not None:
                try:
                    action()
                except OSError:
                    pass
            try:
                result = self.process.wait(timeout=max(0, min(2, deadline - time.monotonic())))
                if result is None or self.process.returncode is None:
                    raise SessionFailure('CLEANUP_PENDING', 'WORKER_REAP_FAILED')
                return
            except subprocess.TimeoutExpired:
                continue
        raise SessionFailure('CLEANUP_PENDING', 'WORKER_REAP_FAILED')

    def close(self):
        with self.close_lock:
            if not self.close_done:
                deadline = time.monotonic() + 10
                failures = []
                try:
                    self.chat.close()
                except Exception:
                    failures.append('WORKER_READER_FAILED')
                try:
                    self._reap(deadline)
                except Exception:
                    failures.append('WORKER_REAP_FAILED')
                for stream in (self.process.stdin, self.process.stdout):
                    try:
                        stream.close()
                        if not stream.closed:
                            raise SessionFailure('CLEANUP_PENDING')
                    except Exception:
                        failures.append('WORKER_DESCRIPTOR_FAILED')
                try:
                    self.chat.reader.join(max(0, min(2, deadline - time.monotonic())))
                    if self.chat.reader.is_alive() or self.chat.connection.fileno() != -1:
                        raise SessionFailure('CLEANUP_PENDING')
                except Exception:
                    failures.append('WORKER_READER_FAILED')
                if time.monotonic() > deadline:
                    failures.append('WORKER_CLEANUP_FAILED')
                self.cleanup_reason = failures[0] if failures else None
                self.close_done = True
            if self.cleanup_reason is not None:
                raise SessionFailure('CLEANUP_PENDING', self.cleanup_reason)


class SessionFailure(RuntimeError):
    def __init__(self, code, cleanup_reason=None):
        self.code = code
        self.cleanup_reason = cleanup_reason
        super().__init__(code)


class PacketSession:
    def __init__(self, network, materials_owner, cancel, attempt, worker_factory=NativeWorker):
        self.network, self.materials_owner, self.cancel = network, materials_owner, cancel
        self.attempt, self.worker_factory = attempt, worker_factory
        self.worker, self.reply = None, None
        self.attached, self.started = False, False
        self.snapshot = {}
        self.underlying, self.deadline = 0, 0
        self.chat_binding = None
        self.close_lock = threading.Lock()
        self.close_done = False
        self.cleanup_confirmed = False
        self.cleanup_reason = None

    def begin(self, materials, underlying, startup_deadline, readiness_deadline):
        if self.started:
            raise SessionFailure('WORKER_PROTOCOL_REJECTED')
        self.started = True
        self.underlying, self.deadline = underlying, readiness_deadline
        start = {}
        try:
            if self.cancel.is_set():
                raise SessionFailure('CANCELLED')
            start = self.materials_owner.resolve(materials, underlying, self.cancel, startup_deadline, self.attempt == 1)
            if self.cancel.is_set():
                raise SessionFailure('CANCELLED')
            remaining = int((startup_deadline - time.monotonic()) * 1000)
            if remaining <= 0:
                raise SessionFailure('DEADLINE')
            self.worker = self.worker_factory()
            start.update(attempt=self.attempt, budget_ms=min(200000, remaining),
                         resolver='1.1.1.1:53', underlying_index=underlying)
            self.reply = self.worker.call('start', start)
            if getattr(self.worker, 'chat', None) is not None:
                self.chat_binding = Binding(self.worker.chat, start, self.cancel)
        finally:
            start.clear()

    def poll(self):
        if self.worker is None:
            raise SessionFailure('WORKER_PROTOCOL_REJECTED')
        while not self.cancel.is_set():
            reply = self.reply if self.reply is not None else self.worker.call('status')
            self.reply = None
            if reply.get('ok') is not True:
                raise SessionFailure('WORKER_PROTOCOL_REJECTED')
            self.snapshot = copy.deepcopy(reply.get('snapshot', {}))
            state = reply.get('state')
            if state == 'PACKET_READY':
                if self.attached or reply.get('interface') != 'fcmesh0' or reply.get('mtu') != 1280:
                    raise SessionFailure('WORKER_PROTOCOL_REJECTED')
                self.network.attach()
                self.attached = True
                if self.cancel.is_set():
                    break
                self.reply = self.worker.call('routed')
                continue
            if state == 'CONNECTED':
                if not self.attached:
                    raise SessionFailure('WORKER_PROTOCOL_REJECTED')
            elif state in ('FAILED', 'DISCONNECTED'):
                reason = reply.get('error', 'UNKNOWN')
                allowed = TRANSIENT | {'FAMILY_REJECTED', 'RELIABLE_PROTOCOL', 'MUX_PROTOCOL', 'CANCELLED'}
                raise SessionFailure(reason if reason in allowed else 'AUTH_OR_STARTUP_FAILED')
            elif state not in ('CONNECTING', 'TRANSPORT_READY', 'ROUTE_CONFIRMING'):
                raise SessionFailure('WORKER_PROTOCOL_REJECTED')
            if state != 'CONNECTED' and time.monotonic() >= self.deadline:
                raise SessionFailure('DEADLINE')
            try:
                self.network.verify_guard()
                if self.network.underlying() != self.underlying:
                    raise SessionFailure('UNDERLAY_CHANGED')
            except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
                if isinstance(error, SessionFailure):
                    raise
                raise SessionFailure('UNDERLAY_UNAVAILABLE') from None
            if self.cancel.is_set():
                break
            if self.chat_binding is not None:
                if state == 'CONNECTED':
                    self.chat_binding.ready.set()
                else:
                    self.chat_binding.ready.clear()
            return state
        raise SessionFailure('CANCELLED')

    def close(self):
        with self.close_lock:
            if not self.close_done:
                failures = []
                if self.chat_binding is not None:
                    try:
                        self.chat_binding.close()
                    except Exception:
                        failures.append('CHAT_BINDING_CLEANUP_FAILED')
                self.reply = None
                if self.worker is not None:
                    try:
                        self.worker.close()
                    except Exception as error:
                        reason = getattr(error, 'cleanup_reason', None)
                        failures.append(reason if reason in CLEANUP_REASONS else 'WORKER_CLEANUP_FAILED')
                    else:
                        self.worker = None
                try:
                    self.network.detach()
                except Exception:
                    failures.append('NETWORK_DETACH_FAILED')
                else:
                    self.attached = False
                self.cleanup_reason = failures[0] if failures else None
                self.cleanup_confirmed = not failures
                self.close_done = True
            if not self.cleanup_confirmed:
                raise SessionFailure('CLEANUP_PENDING', self.cleanup_reason)


class Supervisor:
    def __init__(self, network, materials_owner, ownership=None):
        self.network = network
        self.materials_owner = materials_owner
        self.lock = threading.Lock()
        self.cancel = threading.Event()
        self.thread = None
        self.state = "DISCONNECTED"
        self.reason = "NONE"
        self.first_reason = "NONE"
        self.intent = False
        self.attempt = 0
        self.events = []
        self.dropped = 0
        self.snapshot = {}
        self.started_at = time.monotonic()
        self.worker_factory = NativeWorker
        self.ownership = ownership
        if ownership is not None:
            self.worker_factory = lambda: NativeWorker(ownership)
            self.materials_owner.native = NativeMaterials(ownership)
        self.restarted = False
        self.session = None
        self.cleanup_pending = False

    def chat_binding(self):
        with self.lock:
            return self.session.chat_binding if self.session is not None and self.state == 'CONNECTED' and not self.cancel.is_set() else None

    def transition(self, state, reason="NONE"):
        with self.lock:
            if self.cancel.is_set() and state in ("CONNECTING", "RESTORING", "CONNECTED"):
                return
            self.state, self.reason = state, reason
            if reason != "NONE" and reason != "CANCELLED" and self.first_reason == "NONE":
                self.first_reason = reason
            event = {"state": state, "reason": reason, "attempt": self.attempt,
                     "elapsed_ms": int((time.monotonic() - self.started_at) * 1000)}
            if len(self.events) == 32:
                del self.events[1]
                self.dropped += 1
            self.events.append(event)

    def status(self):
        with self.lock:
            return {"state": self.state, "reason": self.reason, "first_reason": self.first_reason,
                    "desired_connected": self.intent, "attempt": self.attempt,
                    "events": list(self.events), "events_dropped": self.dropped, "native": copy.deepcopy(self.snapshot),
                    "readiness": dict(self.materials_owner.summary)}

    def start(self, materials, restoring=False):
        with self.lock:
            if self.thread is not None or self.intent or self.state != "DISCONNECTED":
                return False
            self.intent = True
            self.restarted = restoring
            self.state = "RESTORING" if restoring else "CONNECTING"
            if restoring:
                self.reason = 'SERVICE_RESTARTED'
                self.events.append(dict(state='RESTORING', reason='SERVICE_RESTARTED', attempt=0,
                                        elapsed_ms=int((time.monotonic() - self.started_at) * 1000)))
            self.thread = threading.Thread(target=self.run, args=(materials,), name="fc-mesh-supervisor", daemon=False)
            self.thread.start()
        return True

    def stop(self):
        with self.lock:
            self.intent = False
            self.cancel.set()
            thread = self.thread
            if thread is not None and thread.is_alive():
                self.state = "STOPPING"
        if thread is not None:
            thread.join(timeout=20)
            if thread.is_alive():
                self.transition("FAILED", "CLEANUP_PENDING")
                return False
        return self.state == "DISCONNECTED"

    def run(self, materials):
        failure = "NONE"
        retries = 0
        try:
            if self.cancel.is_set():
                return
            try:
                if self.ownership is not None:
                    self.ownership.acquire(self.cancel, time.monotonic() + 30)
                self.network.prepare()
            except Exception:
                self.transition('FAILED', 'NETWORK_SETUP_FAILED')
                self.cancel.wait()
                return
            while not self.cancel.is_set():
                try:
                    underlying = self.network.underlying()
                except (OSError, ValueError, RuntimeError, subprocess.SubprocessError):
                    failure = "UNDERLAY_UNAVAILABLE"
                else:
                    with self.lock:
                        self.attempt += 1
                    failure = self.connect(materials, underlying)
                if self.cancel.is_set():
                    break
                if failure not in TRANSIENT:
                    self.transition("FAILED", failure)
                    self.cancel.wait()
                    break
                self.transition("RESTORING", failure)
                retries += 1
                self.cancel.wait(min(30, 2 ** min(retries, 5)))
        except Exception:
            failure = "PACKET_OR_IPC_FAILED"
            self.transition("FAILED", failure)
            self.cancel.wait()
        finally:
            materials.clear()
            try:
                if self.cleanup_pending:
                    raise SessionFailure('CLEANUP_PENDING')
                self.network.cleanup()
                if self.ownership is not None and self.ownership.active:
                    if self.session is not None:
                        raise SessionFailure('CLEANUP_PENDING')
                    self.ownership.finish()
            except Exception:
                if not self.cleanup_pending:
                    self.transition('FAILED', 'NETWORK_CLEANUP_FAILED')
                self.transition("FAILED", "CLEANUP_PENDING")
            else:
                if self.cancel.is_set():
                    self.transition("DISCONNECTED", "CANCELLED")

    def connect(self, materials, underlying):
        session = None
        failure = 'CANCELLED'
        try:
            session = PacketSession(self.network, self.materials_owner, self.cancel, self.attempt, self.worker_factory)
            with self.lock:
                self.session = session
            self.transition("CONNECTING" if self.attempt == 1 and not self.restarted else "RESTORING")
            startup_deadline = time.monotonic() + 200
            session.begin(materials, underlying, startup_deadline, startup_deadline + 35)
            while not self.cancel.is_set():
                try:
                    state = session.poll()
                finally:
                    with self.lock:
                        self.snapshot = copy.deepcopy(session.snapshot)
                if state == 'CONNECTED' and self.state != 'CONNECTED':
                    self.transition('CONNECTED')
                if self.cancel.wait(1):
                    break
        except (MaterialsError, SessionFailure) as error:
            failure = error.code
        except (EOFError, BrokenPipeError, TimeoutError):
            failure = 'WORKER_EXITED'
        except Exception:
            failure = 'PACKET_OR_IPC_FAILED'
        finally:
            if failure != 'CANCELLED':
                self.transition('STOPPING', failure)
            try:
                if session is not None:
                    session.close()
            except Exception as error:
                reason = getattr(error, 'cleanup_reason', None)
                self.transition('STOPPING', reason if reason in CLEANUP_REASONS else 'CLEANUP_FAILED')
                self.cleanup_pending = True
            finally:
                with self.lock:
                    if self.session is session:
                        self.session = None
        return 'CLEANUP_PENDING' if self.cleanup_pending else failure
