"""Root-owned atomic readiness storage and bounded native preparation transactions."""
import base64
import hashlib
import json
import os
import re
import secrets
import signal
import stat
import subprocess
import tempfile
import time

import mesh_ipc as ipc
from mesh_system import ENV

WORKER = "/usr/local/lib/family-connect-mesh/fc-mesh"
MAX_CACHE = 70000
MAX_RECEIPT = 4096
APP_VERSION = "linux-0.2.11"
VERSION_CODE = 2011
CODE = re.compile(r"[A-Z][A-Z0-9_]{0,63}\Z")
RESULTS = {"READY", "MISSING", "NATIVE_VALIDATION_FAILED", "BOOTSTRAP_VALIDATION_FAILED", "ATOMIC_IMPORT_FAILED",
           "PERSISTENCE_FAILED", "EXPIRED_ON_IMPORT", "ORCHESTRATOR_NOT_USABLE", "INTERNAL_ERROR", "STALE_STATE",
           "AUTHORIZATION_REJECTED", "FETCH_FAILED"}


class MaterialsError(RuntimeError):
    def __init__(self, code):
        self.code = code if isinstance(code, str) and CODE.fullmatch(code) else "MATERIALS_FAILED"
        super().__init__(self.code)


class CacheStore:
    def __init__(self, directory, uid, expected_owner=0, receipt=False):
        if type(uid) is not int or not 1 <= uid < 2**31:
            raise MaterialsError("PERSISTENCE_FAILED")
        self.descriptor = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        self.owner = expected_owner
        self.name = str(uid) + (".receipt.json" if receipt else ".json")
        self.maximum = MAX_RECEIPT if receipt else MAX_CACHE
        self.failed = False
        info = os.fstat(self.descriptor)
        if info.st_uid != self.owner or stat.S_IMODE(info.st_mode) != 0o700:
            self.close()
            raise MaterialsError("PERSISTENCE_FAILED")

    def close(self):
        if self.descriptor is not None:
            os.close(self.descriptor)
            self.descriptor = None

    def read(self):
        if self.failed or self.descriptor is None:
            raise MaterialsError("PERSISTENCE_FAILED")
        try:
            try:
                descriptor = os.open(self.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=self.descriptor)
            except FileNotFoundError:
                return None
            with os.fdopen(descriptor, "rb") as source:
                info = os.fstat(source.fileno())
                if (not stat.S_ISREG(info.st_mode) or info.st_uid != self.owner or info.st_nlink != 1 or
                        stat.S_IMODE(info.st_mode) != 0o600 or not 0 < info.st_size <= self.maximum):
                    raise MaterialsError("PERSISTENCE_FAILED")
                raw = source.read(self.maximum + 1)
                ipc.decode(raw, self.maximum)
                return raw
        except (OSError, ValueError):
            raise MaterialsError("PERSISTENCE_FAILED") from None

    def write(self, raw):
        temporary = ".pending-" + secrets.token_hex(16)
        created = False
        try:
            self.read()
            ipc.decode(raw, self.maximum)
            descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=self.descriptor)
            created = True
            with os.fdopen(descriptor, "wb") as output:
                output.write(raw)
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, self.name, src_dir_fd=self.descriptor, dst_dir_fd=self.descriptor)
            created = False
            os.fsync(self.descriptor)
            if self.read() != raw:
                raise MaterialsError("PERSISTENCE_FAILED")
        except (OSError, ValueError, MaterialsError):
            self.failed = True
            raise MaterialsError("PERSISTENCE_FAILED") from None
        finally:
            if created:
                try:
                    os.unlink(temporary, dir_fd=self.descriptor)
                except OSError:
                    pass


class NativeMaterials:
    OPTION = '--materials-stdio'
    MAX_REQUEST = ipc.MAX_REQUEST

    def __call__(self, request, cancel, deadline):
        if cancel.is_set():
            raise MaterialsError("CANCELLED")
        with tempfile.TemporaryDirectory(prefix="fc-mesh-materials-") as scratch:
            return self._exchange(request, cancel, deadline, scratch)

    def _exchange(self, request, cancel, deadline, scratch):
        process = subprocess.Popen([WORKER, self.OPTION], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.DEVNULL, env={**ENV, "TMPDIR": scratch}, bufsize=0, close_fds=True, start_new_session=True)
        try:
            ipc.send(process.stdin.fileno(), request, self.MAX_REQUEST, min(deadline, time.monotonic() + 4), cancel)
            process.stdin.close()
            reply = ipc.receive(process.stdout.fileno(), ipc.MAX_REPLY, deadline, cancel)
            if process.wait(timeout=2) != 0:
                raise MaterialsError("MATERIALS_WORKER_FAILED")
            return reply
        except InterruptedError:
            raise MaterialsError("CANCELLED") from None
        except TimeoutError:
            raise MaterialsError("DEADLINE") from None
        except (OSError, ValueError, EOFError, subprocess.SubprocessError):
            raise MaterialsError("MATERIALS_WORKER_FAILED") from None
        finally:
            if process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
            process.wait(timeout=2)
            process.stdin.close()
            process.stdout.close()


def _bytes(value, size=None, maximum=None):
    try:
        raw = base64.b64decode(value, validate=True)
        if (base64.b64encode(raw).decode() != value or (size is not None and len(raw) != size) or
                (maximum is not None and not 0 < len(raw) <= maximum)):
            raise ValueError()
        return raw
    except (ValueError, TypeError):
        raise MaterialsError("MATERIALS_PROTOCOL_REJECTED") from None


def _reply(reply, identifier):
    allowed = {"schema", "id", "ok", "code", "source", "device", "public", "validated", "durable",
               "storage_required", "candidate_sha256", "cache_proposal", "relay_available", "import_result", "receipt"}
    if (not isinstance(reply, dict) or set(reply) - allowed or type(reply.get("schema")) is not int or reply["schema"] != 1 or
            type(reply.get("id")) is not int or reply["id"] != identifier or not isinstance(reply.get("code"), str) or
            not CODE.fullmatch(reply["code"])):
        raise MaterialsError("MATERIALS_PROTOCOL_REJECTED")
    for field in ("ok", "validated", "durable", "storage_required", "relay_available"):
        if type(reply.get(field)) is not bool:
            raise MaterialsError("MATERIALS_PROTOCOL_REJECTED")
    if reply["durable"] or (reply["validated"] and (not reply["ok"] or reply["code"] != "READY")):
        raise MaterialsError("MATERIALS_PROTOCOL_REJECTED")
    public = _bytes(reply.get("public"), size=64)
    if hashlib.sha256(public).hexdigest()[:32] != reply.get("device"):
        raise MaterialsError("MATERIALS_PROTOCOL_REJECTED")
    if reply.get("source", "") not in ("", "FRESH", "VALIDATED_CACHE"):
        raise MaterialsError("MATERIALS_PROTOCOL_REJECTED")
    if "import_result" in reply and (not isinstance(reply["import_result"], str) or reply["import_result"] not in RESULTS):
        raise MaterialsError("MATERIALS_PROTOCOL_REJECTED")
    if "receipt" in reply:
        _receipt(reply["receipt"])
    if reply["storage_required"]:
        proposal = _bytes(reply.get("cache_proposal"), maximum=MAX_CACHE)
        if hashlib.sha256(proposal).hexdigest() != reply.get("candidate_sha256"):
            raise MaterialsError("MATERIALS_PROTOCOL_REJECTED")
        ipc.decode(proposal, MAX_CACHE)
        return proposal
    if "cache_proposal" in reply or "candidate_sha256" in reply:
        raise MaterialsError("MATERIALS_PROTOCOL_REJECTED")
    return None


def _receipt(value):
    fields = set("version type correlation_id challenge_id fetch_id result provisioning bootstrap orchestrator_usable revision minimum_crl expires_at observed_at phase app_version version_code failure_reason".split())
    if not isinstance(value, dict) or set(value) != fields or not isinstance(value.get("result"), str) or value["result"] not in RESULTS:
        raise MaterialsError("MATERIALS_PROTOCOL_REJECTED")
    ready = value["result"] == "READY"
    for name in ("version", "revision", "minimum_crl", "expires_at", "observed_at", "version_code"):
        minimum = 1 if ready or name in ("version", "observed_at", "version_code") else 0
        if type(value[name]) is not int or not minimum <= value[name] <= 9007199254740991:
            raise MaterialsError("MATERIALS_PROTOCOL_REJECTED")
    for name in ("correlation_id", "challenge_id", "fetch_id"):
        if not isinstance(value[name], str) or re.fullmatch("[a-f0-9]{32}", value[name]) is None:
            raise MaterialsError("MATERIALS_PROTOCOL_REJECTED")
    if (value["version"] != 1 or value["type"] != "READINESS_IMPORT_RESULT" or
            value["correlation_id"] != value["challenge_id"] or value["challenge_id"] == value["fetch_id"] or
            value["orchestrator_usable"] is not ready or value["phase"] not in ("import", "restart") or
            not isinstance(value["app_version"], str) or re.fullmatch("[A-Za-z0-9._-]{1,64}", value["app_version"]) is None or
            value["provisioning"] != ("PRESENT_VALID" if ready else "NOT_READY") or value["bootstrap"] != value["provisioning"] or
            value["failure_reason"] != ("NONE" if ready else value["result"]) or (ready and value["expires_at"] <= value["observed_at"])):
        raise MaterialsError("MATERIALS_PROTOCOL_REJECTED")


class MaterialOwner:
    def __init__(self, storage, receipts=None):
        self.storage = storage
        self.receipts = receipts
        self.native = NativeMaterials()
        self.summary = {"stage": "NOT_STARTED", "code": "MISSING", "durable": False}
        self.receipt_summary = {"ack_state": "UNKNOWN", "durable": False}
        self.reconciled = False

    def _persist_receipt(self, payload, state):
        self.receipt_summary = {"ack_state": state, "durable": False, "result": payload["result"], "phase": payload["phase"]}
        raw = json.dumps({"payload": payload, "ack_state": state}, separators=(",", ":")).encode()
        try:
            self.receipts.write(raw)
            if self.receipts.read() == raw:
                self.receipt_summary["durable"] = True
        except (MaterialsError, OSError, ValueError):
            pass

    def _publish(self, materials, cached, underlying, cancel, deadline, attempt, phase, result="", send=True):
        if self.receipts is None or cancel.is_set() or time.monotonic() >= deadline:
            return
        self.receipt_summary = {"ack_state": "UNKNOWN", "durable": False, "phase": phase}
        request = dict(schema=1, id=3, action="receipt", identity=materials["identity"], anchor=materials["anchor"],
                       wireguard_public=materials["wireguard_public"], cached=cached, attempt=attempt,
                       phase=phase, app_version=APP_VERSION, version_code=VERSION_CODE)
        if result and result != "READY":
            request["import_result"] = result
        try:
            reply = self.native(request, cancel, min(deadline, time.monotonic() + 5))
            request.clear()
            if _reply(reply, 3) is not None or reply["ok"] is not True or reply["code"] != "RECEIPT_READY" or "receipt" not in reply:
                raise MaterialsError("MATERIALS_PROTOCOL_REJECTED")
            payload = reply["receipt"]
            self._persist_receipt(payload, "ACK_PENDING" if send else "UNKNOWN")
            if not send or cancel.is_set() or time.monotonic() >= deadline:
                return
            request = dict(schema=1, id=4, action="ack", identity=materials["identity"], anchor=materials["anchor"],
                           wireguard_public=materials["wireguard_public"], receipt=payload, underlying_index=underlying,
                           budget_ms=min(15000, max(1, int((deadline - time.monotonic()) * 1000))))
            reply = self.native(request, cancel, min(deadline, time.monotonic() + 15))
            if _reply(reply, 4) is not None or reply["ok"] is not True or reply["code"] != "ACK_RECEIVED":
                return
            self._persist_receipt(payload, "ACK_RECEIVED")
        except (MaterialsError, OSError, ValueError):
            pass
        finally:
            request.clear()

    def resolve(self, materials, underlying, cancel, deadline, required):
        self.summary = {"stage": "PREPARING", "code": "MISSING", "durable": False}
        request, reply, saved = {}, {}, None
        result = ""
        attempt = {"challenge_id": secrets.token_hex(16), "fetch_id": secrets.token_hex(16)}
        try:
            raw = self.storage.read()
            cached = ipc.decode(raw, MAX_CACHE) if raw is not None else None
            if not self.reconciled:
                self.reconciled = True
                self._publish(materials, cached, underlying, cancel, deadline, attempt, "restart",
                              send=isinstance(cached, dict) and "receipt_context" in cached)
            request = dict(schema=1, id=1, action="refresh", identity=materials["identity"], anchor=materials["anchor"],
                           wireguard_public=materials["wireguard_public"], cached=cached, underlying_index=underlying,
                           budget_ms=min(200000, max(1, int((deadline - time.monotonic()) * 1000))), required=required,
                           attempt=attempt)
            reply = self.native(request, cancel, deadline)
            request.clear()
            proposal = _reply(reply, 1)
            result = reply.get("import_result", "")
            if proposal is not None:
                self.storage.write(proposal)
            if cancel.is_set():
                raise MaterialsError("CANCELLED")
            if not reply["ok"] or not reply["validated"]:
                raise MaterialsError(reply["code"])
            raw = self.storage.read()
            if raw is None:
                raise MaterialsError("PERSISTENCE_FAILED")
            saved = ipc.decode(raw, MAX_CACHE)
            request = dict(schema=1, id=2, action="inspect", public=reply["public"], anchor=materials["anchor"], cached=saved)
            inspected = self.native(request, cancel, deadline)
            request.clear()
            if (_reply(inspected, 2) is not None or inspected["public"] != reply["public"] or
                    not inspected["ok"] or not inspected["validated"]):
                raise MaterialsError("PERSISTENCE_FAILED")
            if cancel.is_set():
                raise MaterialsError("CANCELLED")
            if time.monotonic() >= deadline:
                raise MaterialsError("DEADLINE")
            if saved.get("denied") is not False or not isinstance(saved.get("response"), dict):
                raise MaterialsError("PERSISTENCE_FAILED")
            if result:
                self._publish(materials, saved, underlying, cancel, deadline, attempt, "import", result)
            if cancel.is_set():
                raise MaterialsError("CANCELLED")
            self.summary = {"stage": "VERIFIED_READBACK", "code": "READY", "durable": True,
                            "source": reply.get("source", ""), "relay_available": reply["relay_available"],
                            "receipt": dict(self.receipt_summary)}
            return {"identity": materials["identity"], "anchor": materials["anchor"], "profile": materials["profile"],
                    "readiness": saved["response"]}
        except MaterialsError as error:
            if result and error.code != "CANCELLED":
                failure = "PERSISTENCE_FAILED" if error.code == "PERSISTENCE_FAILED" else result
                if failure == "READY":
                    failure = "INTERNAL_ERROR"
                self._publish(materials, None, underlying, cancel, deadline, attempt, "import", failure)
            self.summary = {"stage": "FAILED", "code": error.code, "durable": False, "receipt": dict(self.receipt_summary)}
            raise
        finally:
            request.clear()
            reply.clear()
            if saved is not None:
                saved.clear()
