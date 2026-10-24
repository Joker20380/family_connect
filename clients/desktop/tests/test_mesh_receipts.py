import json
import os
import threading
import time

import pytest

from test_mesh_materials import CACHE, inputs, materials, packed, reply


class ReceiptStorage:
    def __init__(self):
        self.raw = None
        self.history = []
        self.fail = False

    def read(self):
        return self.raw

    def write(self, raw):
        if self.fail:
            raise materials.MaterialsError("PERSISTENCE_FAILED")
        self.raw = raw
        self.history.append(json.loads(raw))


class ReceiptNative:
    def __init__(self, receipts):
        self.receipts = receipts
        self.calls = []
        self.ack_failure = False
        self.cancel_on_ack = False
        self.import_result = "READY"

    def __call__(self, request, cancel, deadline):
        action = request["action"]
        self.calls.append((action, request.get("phase")))
        if action == "refresh":
            value = reply(proposal=packed(CACHE))
            value["import_result"] = self.import_result
            return value
        if action == "inspect":
            return reply(identifier=2)
        if action == "receipt":
            cached = request.get("cached") or {}
            result = request.get("import_result") or ("READY" if cached.get("response") else "MISSING")
            attempt = cached.get("receipt_context", request["attempt"]) if request["phase"] == "restart" else request["attempt"]
            ready = result == "READY"
            observed = int(time.time())
            payload = dict(version=1, type="READINESS_IMPORT_RESULT", correlation_id=attempt["challenge_id"],
                           challenge_id=attempt["challenge_id"], fetch_id=attempt["fetch_id"], result=result,
                           provisioning="PRESENT_VALID" if ready else "NOT_READY", bootstrap="PRESENT_VALID" if ready else "NOT_READY",
                           orchestrator_usable=ready, revision=int(ready), minimum_crl=int(ready),
                           expires_at=observed + 100 if ready else 0, observed_at=observed, phase=request["phase"],
                           app_version=request["app_version"], version_code=request["version_code"],
                           failure_reason="NONE" if ready else result)
            value = reply(identifier=3, code="RECEIPT_READY")
            value.update(ok=True, receipt=payload)
            return value
        assert action == "ack"
        if not self.receipts.fail:
            record = json.loads(self.receipts.read())
            assert record["ack_state"] == "ACK_PENDING"
            assert record["payload"] == request["receipt"]
        assert request["underlying_index"] == 2 and 0 < request["budget_ms"] <= 15000
        assert deadline <= time.monotonic() + 15.1
        if self.cancel_on_ack:
            cancel.set()
            raise materials.MaterialsError("CANCELLED")
        if self.ack_failure:
            raise materials.MaterialsError("DEADLINE")
        value = reply(identifier=4, code="ACK_RECEIVED")
        value["ok"] = True
        return value


@pytest.fixture
def owner(tmp_path):
    tmp_path.chmod(0o700)
    cache = materials.CacheStore(tmp_path, 1000, expected_owner=os.getuid())
    receipts = ReceiptStorage()
    result = materials.MaterialOwner(cache, receipts)
    result.native = ReceiptNative(receipts)
    yield result
    cache.close()


def resolve(owner, cancel=None):
    return owner.resolve(inputs(), 2, cancel or threading.Event(), time.monotonic() + 200, True)


def test_durable_ack_follows_saved_material_readback(owner):
    assert resolve(owner)["readiness"] == CACHE["response"]
    assert owner.native.calls == [("receipt", "restart"), ("refresh", None), ("inspect", None), ("receipt", "import"), ("ack", None)]
    assert [record["ack_state"] for record in owner.receipts.history] == ["UNKNOWN", "ACK_PENDING", "ACK_RECEIVED"]
    assert owner.summary["receipt"] == dict(ack_state="ACK_RECEIVED", durable=True, result="READY", phase="import")
    assert len(owner.receipts.raw) <= 4096
    text = owner.receipts.raw.decode()
    assert "synthetic_test_only" not in text and "identity" not in text and "wireguard_public" not in text
    assert inputs()["identity"] not in text


def test_transient_ack_failure_retains_pending_without_rejecting_valid_material(owner):
    owner.native.ack_failure = True
    assert resolve(owner)["readiness"] == CACHE["response"]
    assert owner.summary["durable"]
    assert owner.summary["receipt"]["ack_state"] == "ACK_PENDING"
    assert owner.summary["receipt"]["durable"]


def test_receipt_persistence_failure_never_claims_durable_ack_or_invalidates_material(owner):
    owner.receipts.fail = True
    assert resolve(owner)["readiness"] == CACHE["response"]
    assert owner.summary["durable"]
    assert owner.summary["receipt"]["ack_state"] == "ACK_RECEIVED"
    assert not owner.summary["receipt"]["durable"]


def test_ack_received_but_final_disk_failure_keeps_pending_record(owner):
    write = owner.receipts.write
    def fail_received(raw):
        if json.loads(raw)["ack_state"] == "ACK_RECEIVED":
            raise materials.MaterialsError("PERSISTENCE_FAILED")
        write(raw)
    owner.receipts.write = fail_received
    assert resolve(owner)["readiness"] == CACHE["response"]
    assert json.loads(owner.receipts.read())["ack_state"] == "ACK_PENDING"
    assert owner.summary["receipt"]["ack_state"] == "ACK_RECEIVED"
    assert not owner.summary["receipt"]["durable"]


@pytest.mark.parametrize("change", [{"ok": False}, {"validated": True}, {"id": 5}, {"durable": True}])
def test_malformed_ack_reply_never_promotes_pending(owner, change):
    original = owner.native
    def malformed(request, cancel, deadline):
        response = original(request, cancel, deadline)
        if request["action"] == "ack":
            response.update(change)
        return response
    owner.native = malformed
    assert resolve(owner)["readiness"] == CACHE["response"]
    assert json.loads(owner.receipts.read())["ack_state"] == "ACK_PENDING"
    assert owner.summary["receipt"]["ack_state"] == "ACK_PENDING"


def test_restart_uses_cache_context_and_runs_once_per_service_owner(owner):
    context = dict(challenge_id="c" * 32, fetch_id="d" * 32)
    owner.storage.write(packed(dict(CACHE, receipt_context=context)))
    resolve(owner)
    first = owner.receipts.history[0]
    assert first["ack_state"] == "ACK_PENDING"
    assert first["payload"]["phase"] == "restart"
    assert first["payload"]["correlation_id"] == context["challenge_id"]
    resolve(owner)
    assert owner.native.calls.count(("receipt", "restart")) == 1


def test_cached_refresh_failure_is_not_reported_as_import_ready(owner):
    owner.native.import_result = "FETCH_FAILED"
    assert resolve(owner)["readiness"] == CACHE["response"]
    assert owner.summary["receipt"]["result"] == "FETCH_FAILED"
    assert not json.loads(owner.receipts.raw)["payload"]["orchestrator_usable"]


def test_cancel_during_ack_keeps_pending_and_never_returns_start_material(owner):
    owner.native.cancel_on_ack = True
    with pytest.raises(materials.MaterialsError, match="CANCELLED"):
        resolve(owner)
    assert owner.summary["receipt"]["ack_state"] == "ACK_PENDING"
    assert not owner.summary["durable"]


def test_denial_and_failure_receipt_are_separate_and_persistent(owner):
    original = owner.native
    def denied(request, cancel, deadline):
        if request["action"] == "refresh":
            value = reply(code="AUTHORIZATION_REJECTED", proposal=packed(dict(CACHE, denied=True)))
            value["import_result"] = "AUTHORIZATION_REJECTED"
            return value
        return original(request, cancel, deadline)
    owner.native = denied
    with pytest.raises(materials.MaterialsError, match="AUTHORIZATION_REJECTED"):
        resolve(owner)
    assert json.loads(owner.storage.read())["denied"] is True
    assert json.loads(owner.receipts.read())["payload"]["result"] == "AUTHORIZATION_REJECTED"
    assert owner.summary["receipt"]["ack_state"] == "ACK_RECEIVED"


def test_receipt_store_is_separate_bounded_private_and_restart_safe(tmp_path):
    tmp_path.chmod(0o700)
    storage = materials.CacheStore(tmp_path, 1000, expected_owner=os.getuid(), receipt=True)
    try:
        raw = packed({"payload": {}, "ack_state": "UNKNOWN"})
        storage.write(raw)
        assert not (tmp_path / "1000.json").exists()
        target = tmp_path / "1000.receipt.json"
        assert target.stat().st_mode & 0o777 == 0o600
        restarted = materials.CacheStore(tmp_path, 1000, expected_owner=os.getuid(), receipt=True)
        try:
            assert restarted.read() == raw
        finally:
            restarted.close()
        with pytest.raises(materials.MaterialsError, match="PERSISTENCE_FAILED"):
            storage.write(packed({"oversize": "x" * 4096}))
        assert target.read_bytes() == raw
    finally:
        storage.close()


@pytest.mark.parametrize("field,value", [("result", []), ("orchestrator_usable", 1), ("revision", True),
                                         ("version_code", 0), ("fetch_id", "bad"), ("app_version", "private token")])
def test_bad_native_receipt_never_saved_or_acknowledged(owner, field, value):
    original = owner.native
    def malformed(request, cancel, deadline):
        response = original(request, cancel, deadline)
        if request["action"] == "receipt":
            response["receipt"][field] = value
        return response
    owner.native = malformed
    assert resolve(owner)["readiness"] == CACHE["response"]
    assert not owner.receipts.history
    assert not owner.summary["receipt"]["durable"]
    assert ("ack", None) not in original.calls
