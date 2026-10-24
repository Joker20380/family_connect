import base64
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import threading
import time

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "linux"))
import mesh_materials as materials


@pytest.fixture
def native(monkeypatch):
    path = os.environ.get("FC_TEST_MESH_WORKER")
    if not path:
        pytest.skip("Set FC_TEST_MESH_WORKER to the exact locally built native artifact")
    executable = Path(path).resolve(strict=True)
    monkeypatch.setattr(materials, "WORKER", str(executable))
    return executable


@pytest.mark.parametrize("cached,code", [(None, "MISSING"),
    ({"response": None, "denied": True, "next_attempt": 0}, "AUTHORIZATION_REJECTED"),
    ({"response": {"synthetic_invalid": True}, "denied": False, "next_attempt": 0}, "NATIVE_VALIDATION_FAILED"),
    ({"unexpected": True}, "PERSISTENCE_FAILED")])
def test_actual_native_offline_inspection_never_claims_durable(native, cached, code, tmp_path, monkeypatch):
    monkeypatch.setattr(materials.tempfile, "tempdir", str(tmp_path))
    command = dict(schema=1, id=1, action="inspect", public=base64.b64encode(b"p" * 64).decode(),
                   anchor=base64.b64encode(b"a" * 32).decode(), cached=cached)
    reply = materials.NativeMaterials()(command, threading.Event(), time.monotonic() + 5)
    assert reply["code"] == code
    assert materials._reply(reply, 1) is None
    assert not reply["validated"] and not reply["durable"] and not reply["relay_available"]
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("raw", [b'{"schema":1,"id":1,"id":2,"action":"inspect"}',
                                 b'{"schema":1,"id":1,"action":"inspect","path":"/etc/shadow"}'])
def test_actual_native_rejects_ambiguous_or_executable_command(native, raw):
    result = subprocess.run([str(native), "--materials-stdio"], input=struct.pack("!I", len(raw)) + raw,
                            capture_output=True, timeout=5)
    assert result.returncode != 0 and not result.stdout
    assert raw not in result.stderr


def test_actual_native_reports_both_protocol_versions(native):
    result = subprocess.run([str(native), "--version"], capture_output=True, check=True, timeout=5)
    report = json.loads(result.stdout)
    assert report["materials_protocol"] == 1
    assert report["bridge_protocol"] == 1


@pytest.mark.parametrize("cached,phase,result", [(None, "restart", "MISSING"),
    ({"response": None, "denied": True, "next_attempt": 0}, "restart", "AUTHORIZATION_REJECTED"),
    ({"response": {"synthetic_invalid": True}, "denied": False, "next_attempt": 0}, "restart", "NATIVE_VALIDATION_FAILED"),
    (None, "import", "FETCH_FAILED")])
def test_actual_native_receipt_is_bounded_typed_offline_and_not_durable(native, cached, phase, result):
    command = dict(schema=1, id=3, action="receipt", identity=base64.b64encode(b"\0" * 64).decode(),
                   wireguard_public=base64.b64encode(b"w" * 32).decode(), anchor=base64.b64encode(b"a" * 32).decode(),
                   cached=cached, attempt={"challenge_id": "a" * 32, "fetch_id": "b" * 32}, phase=phase,
                   app_version=materials.APP_VERSION, version_code=materials.VERSION_CODE)
    if phase == "import":
        command["import_result"] = result
    response = materials.NativeMaterials()(command, threading.Event(), time.monotonic() + 5)
    assert materials._reply(response, 3) is None
    assert response["ok"] and response["code"] == "RECEIPT_READY"
    payload = response["receipt"]
    assert payload["result"] == result and len(payload) == 17 and not payload["orchestrator_usable"]
    assert not response["durable"] and not response["validated"]
    assert len(json.dumps(payload).encode()) < 4096
    assert command["identity"] not in json.dumps(payload)
