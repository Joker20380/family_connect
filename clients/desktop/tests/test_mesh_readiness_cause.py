import json
import os
from pathlib import Path
import sys
import threading
import time

import pytest

from test_mesh_materials import inputs, materials, packed, storage
from test_mesh_service import FakeNetwork, service, wait_for
import backend


CODES = (
    "CHALLENGE_TIMEOUT", "CHALLENGE_TEMPORARY_SERVER_FAILURE", "FETCH_NETWORK_FAILURE",
    "FETCH_TEMPORARY_SERVER_FAILURE", "RNS_UNAVAILABLE", "RNS_WORKER_UNAVAILABLE",
    "RNS_PROTOCOL_REJECTED", "TLS_TRUST_REJECTED", "FETCH_INCOMPATIBLE_RESPONSE",
)


class RetryClock(threading.Event):
    def __init__(self):
        super().__init__()
        self.paused = threading.Event()
        self.backoffs = []

    def wait(self, timeout=None):
        if timeout is not None:
            self.backoffs.append(timeout)
            if len(self.backoffs) == 1:
                return self.is_set()
        self.paused.set()
        return super().wait()


@pytest.fixture
def receipt_storage(tmp_path):
    directory = tmp_path / "receipts"
    directory.mkdir(mode=0o700)
    owner = materials.CacheStore(directory, 1000, expected_owner=os.getuid(), receipt=True)
    yield owner
    owner.close()


@pytest.fixture
def native_transport(tmp_path, monkeypatch):
    model = tmp_path / "model.json"
    worker = tmp_path / "native-fixture"
    worker.write_text(f"""#!{sys.executable}
import json
import sys
import time
from pathlib import Path
sys.path.insert(0, {str(Path(__file__).parent)!r})
sys.path.insert(0, {str(Path(__file__).parents[1])!r})
sys.path.insert(0, {str(Path(__file__).parents[3])!r})
from test_mesh_materials import materials, packed, reply
from test_mesh_receipts import ReceiptNative, ReceiptStorage
request = materials.ipc.receive(sys.stdin.fileno(), materials.NativeMaterials.MAX_REQUEST, time.monotonic() + 5)
model = json.loads(Path({str(model)!r}).read_text())
if request['action'] == 'refresh':
    cached = request.get('cached') or {{'response': None, 'denied': False, 'next_attempt': 0}}
    if request['required'] or cached['next_attempt'] <= model['now']:
        cached['next_attempt'] = model['now'] + 300
        response = reply(code=model['code'], proposal=packed(cached))
        response['import_result'] = 'FETCH_FAILED'
    else:
        response = reply(code=model['unusable'])
else:
    receipts = ReceiptStorage()
    if request['action'] == 'ack':
        receipts.write(packed({{'payload': request['receipt'], 'ack_state': 'ACK_PENDING'}}))
    response = ReceiptNative(receipts)(request, __import__('threading').Event(), time.monotonic() + 5)
materials.ipc.send(sys.stdout.fileno(), response, materials.ipc.MAX_REPLY, time.monotonic() + 5)
""")
    worker.chmod(0o500)
    monkeypatch.setattr(materials, "WORKER", str(worker))
    def configure(code, unusable="MISSING", now=1000):
        model.write_text(json.dumps(dict(code=code, unusable=unusable, now=now)))
    return configure


@pytest.mark.parametrize("code", CODES)
def test_native_material_owner_preserves_cause_and_durable_import(storage, receipt_storage, native_transport, code):
    native_transport(code)
    receipts = receipt_storage
    owner = materials.MaterialOwner(storage, receipts)
    supervisor = service.Supervisor(FakeNetwork(), owner)
    assert supervisor.start(inputs())
    try:
        wait_for(lambda: supervisor.first_reason != "NONE")
        status = supervisor.status()
        assert status["first_reason"] == code
        assert status["attempt"] == 1
    finally:
        assert supervisor.stop()
    assert owner.summary["code"] == code
    assert json.loads(storage.read())["next_attempt"] == 1300
    assert json.loads(receipts.read())["payload"]["result"] == "FETCH_FAILED"
    assert owner.receipt_summary["durable"]
    assert owner.receipt_summary["result"] == "FETCH_FAILED"
    collector = backend.DesktopDiagnostics("test")
    collector.sample(status["state"], "mesh", service=status)
    record = json.loads(collector.export())["ring"]
    assert record["first_failure"] == code
    assert record["events"][-1]["reason_code"] == code


@pytest.mark.parametrize("unusable", ["MISSING", "EXPIRED_ON_IMPORT"])
def test_supervisor_cooldown_terminal_after_two_attempts(storage, receipt_storage, native_transport, unusable):
    native_transport("CHALLENGE_TIMEOUT", unusable)
    if unusable == "EXPIRED_ON_IMPORT":
        storage.write(packed(dict(response={"expires_at": 900}, denied=False, next_attempt=0)))
    network = FakeNetwork()
    owner = materials.MaterialOwner(storage, receipt_storage)
    supervisor = service.Supervisor(network, owner)
    supervisor.cancel = RetryClock()
    calls = []
    native = owner.native
    def exchange(request, cancel, deadline):
        if request["action"] == "refresh":
            calls.append(request["required"])
            assert supervisor.session is not None
            assert network.operations.count("detach") == len(calls) - 1
        return native(request, cancel, deadline)
    owner.native = exchange
    assert supervisor.start(inputs())
    try:
        assert supervisor.cancel.paused.wait(10)
        status = supervisor.status()
        assert status["state"] == "FAILED"
        assert status["reason"] == unusable
        assert status["first_reason"] == "CHALLENGE_TIMEOUT"
        assert status["attempt"] == 2
        assert supervisor.cancel.backoffs == [2]
        assert calls == [True, False]
        assert supervisor.session is None
        assert network.operations == ["guard", "detach", "detach"]
        assert json.loads(storage.read())["next_attempt"] == 1300
    finally:
        assert supervisor.stop()
    assert supervisor.session is None and not supervisor.thread.is_alive()
    assert network.operations[-1] == "cleanup"
    native_transport("FETCH_TEMPORARY_SERVER_FAILURE", unusable, now=1300)
    owner.native = native
    later = service.Supervisor(FakeNetwork(), owner)
    assert later.start(inputs())
    try:
        wait_for(lambda: later.first_reason != "NONE")
        assert later.first_reason == "FETCH_TEMPORARY_SERVER_FAILURE"
        assert later.attempt == 1
    finally:
        assert later.stop()
    assert json.loads(storage.read())["next_attempt"] == 1600
