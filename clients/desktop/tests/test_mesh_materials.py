import base64
import hashlib
import json
import os
from pathlib import Path
import sys
import threading
import time

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "linux"))
import mesh_ipc as ipc
import mesh_materials as materials
from test_mesh_service import FakeNetwork, FakeWorker, materials as inputs, wait_for
import mesh_service as service

PUBLIC = base64.b64encode(b"p" * 64).decode()
CACHE = {"response": {"synthetic_test_only": "тест"}, "denied": False, "next_attempt": 123}


def packed(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()


def reply(identifier=1, code="READY", proposal=None):
    value = dict(schema=1, id=identifier, ok=code == "READY", code=code, validated=code == "READY", durable=False,
                 storage_required=proposal is not None, relay_available=False, public=PUBLIC,
                 device=hashlib.sha256(b"p" * 64).hexdigest()[:32], source="FRESH" if code == "READY" else "")
    if proposal is not None:
        value.update(cache_proposal=base64.b64encode(proposal).decode(), candidate_sha256=hashlib.sha256(proposal).hexdigest())
    return value


@pytest.fixture
def storage(tmp_path):
    tmp_path.chmod(0o700)
    owner = materials.CacheStore(tmp_path, 1000, expected_owner=os.getuid())
    yield owner
    owner.close()


def test_atomic_private_cache_roundtrip_and_restart(storage, tmp_path):
    assert storage.read() is None
    raw = packed(CACHE)
    storage.write(raw)
    assert storage.read() == raw
    assert (tmp_path / "1000.json").stat().st_mode & 0o777 == 0o600
    restarted = materials.CacheStore(tmp_path, 1000, expected_owner=os.getuid())
    try:
        assert restarted.read() == raw
        assert list(tmp_path.iterdir()) == [tmp_path / "1000.json"]
    finally:
        restarted.close()


@pytest.mark.parametrize("kind", ["symlink", "hardlink", "fifo", "directory", "mode", "oversize", "duplicate", "empty"])
def test_cache_never_adopts_unsafe_files(storage, tmp_path, kind):
    target = tmp_path / "1000.json"
    if kind in ("symlink", "hardlink"):
        other = tmp_path / "other"
        other.write_bytes(packed(CACHE))
        other.chmod(0o600)
        if kind == "symlink":
            target.symlink_to(other)
        else:
            os.link(other, target)
    elif kind == "fifo":
        os.mkfifo(target, 0o600)
    elif kind == "directory":
        target.mkdir(mode=0o600)
    else:
        target.write_bytes(b"" if kind == "empty" else b"x" * 70001 if kind == "oversize" else
                           b'{"denied":false,"denied":true}' if kind == "duplicate" else packed(CACHE))
        target.chmod(0o644 if kind == "mode" else 0o600)
    with pytest.raises(materials.MaterialsError, match="PERSISTENCE_FAILED"):
        storage.read()
    with pytest.raises(materials.MaterialsError, match="PERSISTENCE_FAILED"):
        storage.write(packed(CACHE))


def test_cache_directory_not_symlink_or_shared(tmp_path):
    tmp_path.chmod(0o755)
    with pytest.raises(materials.MaterialsError):
        materials.CacheStore(tmp_path, 1000, expected_owner=os.getuid())
    tmp_path.chmod(0o700)
    alias = tmp_path / "alias"
    alias.symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(OSError):
        materials.CacheStore(alias, 1000, expected_owner=os.getuid())


def test_failed_replace_keeps_previous_and_poisoned_owner(storage, tmp_path, monkeypatch):
    original = packed(CACHE)
    storage.write(original)
    def fail(*args, **kwargs):
        raise OSError("synthetic disk failure")
    monkeypatch.setattr(os, "replace", fail)
    with pytest.raises(materials.MaterialsError):
        storage.write(packed(dict(CACHE, denied=True)))
    assert (tmp_path / "1000.json").read_bytes() == original
    assert not list(tmp_path.glob(".pending-*"))
    with pytest.raises(materials.MaterialsError):
        storage.read()


def test_cache_directory_sync_failure_never_claims_durable(storage, monkeypatch):
    original = os.fsync
    def fail(descriptor):
        if descriptor == storage.descriptor:
            raise OSError("synthetic directory sync failure")
        original(descriptor)
    monkeypatch.setattr(os, "fsync", fail)
    with pytest.raises(materials.MaterialsError):
        storage.write(packed(CACHE))
    assert storage.failed


def test_prepare_persists_exact_native_bytes_and_revalidates_disk(storage):
    owner = materials.MaterialOwner(storage)
    calls = []
    def native(request, cancel, deadline):
        calls.append(request["action"])
        if request["action"] == "refresh":
            assert request["cached"] is None and request["required"]
            assert request["underlying_index"] == 2 and 0 < request["budget_ms"] <= 200000
            return reply(proposal=packed(CACHE))
        assert storage.read() == packed(CACHE)
        assert request["cached"] == CACHE
        assert "identity" not in request
        return reply(identifier=2)
    owner.native = native
    result = owner.resolve(inputs(), 2, threading.Event(), time.monotonic() + 200, True)
    assert calls == ["refresh", "inspect"]
    assert result["readiness"] == CACHE["response"]
    assert result["identity"] == inputs()["identity"]
    assert owner.summary["durable"] and owner.summary["stage"] == "VERIFIED_READBACK"
    assert "synthetic_test_only" not in json.dumps(owner.summary)


def test_denial_is_persisted_even_when_preparation_failed(storage):
    storage.write(packed(CACHE))
    denied = packed(dict(CACHE, denied=True))
    owner = materials.MaterialOwner(storage)
    owner.native = lambda *args: reply(code="AUTHORIZATION_REJECTED", proposal=denied)
    with pytest.raises(materials.MaterialsError, match="AUTHORIZATION_REJECTED"):
        owner.resolve(inputs(), 2, threading.Event(), time.monotonic() + 200, True)
    assert storage.read() == denied
    assert not owner.summary["durable"]


@pytest.mark.parametrize("change", [{"durable": True}, {"id": True}, {"validated": 1}, {"schema": True},
                                    {"device": "a" * 32}, {"public": "invalid"}, {"source": "NONE"},
                                    {"candidate_sha256": "0" * 64}, {"code": "secret URL"}, {"command": "exec"}])
def test_native_materials_response_cannot_bypass_owner_readback(storage, change):
    owner = materials.MaterialOwner(storage)
    value = reply(proposal=packed(CACHE))
    value.update(change)
    owner.native = lambda *args: value
    with pytest.raises(materials.MaterialsError, match="MATERIALS_PROTOCOL_REJECTED"):
        owner.resolve(inputs(), 2, threading.Event(), time.monotonic() + 200, True)
    assert storage.read() is None


def test_validated_but_unstored_proposal_cannot_start(storage):
    owner = materials.MaterialOwner(storage)
    owner.native = lambda *args: reply()
    with pytest.raises(materials.MaterialsError, match="PERSISTENCE_FAILED"):
        owner.resolve(inputs(), 2, threading.Event(), time.monotonic() + 200, True)


def test_invalid_disk_readback_never_reaches_session(storage):
    owner = materials.MaterialOwner(storage)
    owner.native = lambda request, *args: reply(proposal=packed(CACHE)) if request["action"] == "refresh" else reply(identifier=2, code="EXPIRED_ON_IMPORT")
    with pytest.raises(materials.MaterialsError, match="PERSISTENCE_FAILED"):
        owner.resolve(inputs(), 2, threading.Event(), time.monotonic() + 200, True)


def test_cancel_after_denial_persists_latch_without_connect(storage):
    owner = materials.MaterialOwner(storage)
    cancel = threading.Event()
    denied = packed(dict(CACHE, denied=True))
    def native(*args):
        cancel.set()
        return reply(code="AUTHORIZATION_REJECTED", proposal=denied)
    owner.native = native
    with pytest.raises(materials.MaterialsError, match="CANCELLED"):
        owner.resolve(inputs(), 2, cancel, time.monotonic() + 200, True)
    assert storage.read() == denied


def test_ipc_partial_response_is_interruptible():
    reader, writer = os.pipe()
    cancel = threading.Event()
    timer = threading.Timer(.05, cancel.set)
    try:
        os.write(writer, b"\0\0")
        timer.start()
        started = time.monotonic()
        with pytest.raises(InterruptedError):
            ipc.receive(reader, ipc.MAX_REPLY, started + 30, cancel)
        assert time.monotonic() - started < 1
    finally:
        timer.join()
        os.close(reader)
        os.close(writer)


def test_service_never_spawns_packet_worker_without_durable_materials(storage):
    owner = materials.MaterialOwner(storage)
    owner.native = lambda *args: reply(code="AUTHORIZATION_REJECTED", proposal=packed(dict(CACHE, denied=True)))
    network = FakeNetwork()
    supervisor = service.Supervisor(network, owner)
    created = []
    supervisor.worker_factory = lambda: created.append(True)
    assert supervisor.start(inputs())
    try:
        wait_for(lambda: supervisor.status()["state"] == "FAILED")
        assert supervisor.status()["reason"] == "AUTHORIZATION_REJECTED"
        assert not created and "cleanup" not in network.operations
        assert supervisor.status()["readiness"]["stage"] == "FAILED"
    finally:
        assert supervisor.stop()


def test_service_readiness_then_packet_then_routes(storage):
    owner = materials.MaterialOwner(storage)
    owner.native = lambda request, *args: reply(proposal=packed(CACHE)) if request["action"] == "refresh" else reply(identifier=2)
    network = FakeNetwork()
    worker = FakeWorker(network)
    supervisor = service.Supervisor(network, owner)
    supervisor.worker_factory = lambda: worker
    assert supervisor.start(inputs())
    try:
        wait_for(lambda: supervisor.status()["state"] == "CONNECTED")
        assert supervisor.status()["readiness"]["durable"]
        assert worker.calls[:2] == ["start", "routed"]
    finally:
        assert supervisor.stop()
