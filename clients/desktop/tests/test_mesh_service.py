import base64
import copy
import importlib.util
import json
import os
from pathlib import Path
import struct
import sys
import threading
import time

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "linux"))
import mesh_ipc as ipc
import mesh_service as service
import mesh_system as system
import backend

SPEC = importlib.util.spec_from_file_location("mesh_helper", Path(system.__file__).with_name("mesh-helper.py"))
helper = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(helper)


def materials():
    return {"identity": base64.b64encode(b"x" * 64).decode(), "anchor": base64.b64encode(b"a" * 32).decode(),
            "wireguard_public": base64.b64encode(b"w" * 32).decode(), "profile": "P1"}


class FakeMaterials:
    summary = {"stage": "SYNTHETIC_TEST_ONLY"}

    def resolve(self, material, underlying, cancel, deadline, required):
        return dict(identity=material["identity"], anchor=material["anchor"], profile=material["profile"],
                    readiness={"synthetic": True})


def request():
    return {"schema": 1, "id": 1, "action": "start", "materials": materials()}


def wait_for(predicate):
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(.005)
    pytest.fail("Supervisor did not reach expected bounded state")


@pytest.mark.parametrize("raw", [b'{"id":1,"id":2}', b'{"nested":{"id":1,"id":2}}', b'{"x":NaN}',
                                b'{"x":Infinity}', b'{"x":1} {}', b'[]', b'\xff', b'{"x":' + b'[' * 18 + b'0' + b']' * 18 + b'}'])
def test_private_ipc_rejects_ambiguous_or_deep_input(raw):
    with pytest.raises(ipc.ProtocolError):
        ipc.decode(raw, ipc.MAX_REQUEST)


@pytest.mark.parametrize("change", [{"schema": True}, {"id": True}, {"id": 0}, {"id": 2**63}, {"action": "exec"},
                                   {"action": "status"}, {"path": "/bin/sh"}])
def test_private_ipc_exact_envelope(change):
    value = request()
    value.update(change)
    with pytest.raises(ipc.ProtocolError):
        ipc.validate_request(value)


@pytest.mark.parametrize("change", [{"profile": "P2"}, {"profile": "Q1"}, {"identity": "private"}, {"identity": 9},
                                   {"anchor": base64.b64encode(b"a" * 31).decode()}, {"readiness": []},
                                   {"resolver": "198.51.100.1:53"}, {"underlying_index": 2}, {"readiness": {"large": "a" * 65536}}])
def test_private_ipc_does_not_accept_commands_or_network_overrides(change):
    value = request()
    value["materials"].update(change)
    with pytest.raises(ipc.ProtocolError):
        ipc.validate_request(value)


def test_private_ipc_roundtrip_bounds_and_eof():
    source, sink = os.pipe()
    try:
        value = request()
        ipc.send(sink, value, ipc.MAX_REQUEST, time.monotonic() + 1)
        assert ipc.validate_request(ipc.receive(source, ipc.MAX_REQUEST, time.monotonic() + 1)) == value
        os.write(sink, struct.pack("!I", ipc.MAX_REQUEST + 1))
        with pytest.raises(ipc.ProtocolError):
            ipc.receive(source, ipc.MAX_REQUEST, time.monotonic() + 1)
        with pytest.raises(TimeoutError):
            ipc.receive(source, ipc.MAX_REQUEST, time.monotonic() - 1)
        os.close(sink)
        sink = None
        with pytest.raises(EOFError):
            ipc.receive(source, ipc.MAX_REQUEST, time.monotonic() + 1)
    finally:
        os.close(source)
        if sink is not None:
            os.close(sink)


def test_authorized_bridge_cannot_expand_service_privileges():
    for action in ("up", "down"):
        arguments, data = backend._session_request(dict(kind="mesh", action=action, ident="fcmesh0", data=None))
        assert arguments == ["/usr/local/lib/family-connect-mesh/helper", action, "fcmesh0"]
        assert data is None
    for action, ident, data in (("import", None, "secret"), ("serve", "1000", None), ("up", "fcmesh00000000", None), ("up", "fcmesh0", "key")):
        with pytest.raises(ValueError):
            backend._session_request(dict(kind="mesh", action=action, ident=ident, data=data))
    for value in ("0", "-1", "01", "١", "1000;id", "2147483648", ""):
        with pytest.raises(ValueError):
            helper.owner(value)
    assert helper.owner("1000") == 1000


class FakeNetwork:
    def __init__(self):
        self.operations = []
        self.index = 2
        self.fail_attach = False

    def prepare(self):
        self.operations.append("guard")

    def underlying(self):
        return self.index

    def attach(self):
        self.operations.append("routes_and_dns")
        if self.fail_attach:
            raise RuntimeError("Synthetic route failure")

    def detach(self):
        self.operations.append("detach")

    def verify_guard(self):
        pass

    def cleanup(self):
        self.operations.append("cleanup")


class FakeWorker:
    def __init__(self, network, state="PACKET_READY", error=None):
        self.network = network
        self.calls = []
        self.state = state
        self.error = error

    def call(self, action, start=None):
        self.calls.append(action)
        if start is not None:
            assert start["underlying_index"] == 2
            assert start["profile"] == "P1"
            assert start["resolver"] == "1.1.1.1:53"
        if action == "routed":
            assert "routes_and_dns" in self.network.operations
            self.state = "CONNECTED"
        return {"ok": True, "state": self.state, "interface": "fcmesh0", "mtu": 1280, "error": self.error,
                "snapshot": {"count": 1}}

    def close(self):
        self.calls.append("close")


def test_connected_only_after_verified_routes_and_disconnect_cancels():
    network = FakeNetwork()
    supervisor = service.Supervisor(network, FakeMaterials())
    worker = FakeWorker(network)
    supervisor.worker_factory = lambda: worker
    value = materials()
    assert supervisor.start(value)
    try:
        wait_for(lambda: supervisor.status()["state"] == "CONNECTED")
        assert worker.calls[:2] == ["start", "routed"]
        assert not supervisor.start(materials())
        snapshot = supervisor.status()
        snapshot["native"]["count"] = 7
        assert supervisor.status()["native"]["count"] == 1
        assert "identity" not in json.dumps(supervisor.status())
    finally:
        assert supervisor.stop()
    assert value == {}
    assert not supervisor.status()["desired_connected"]
    assert supervisor.status()["state"] == "DISCONNECTED"
    assert network.operations[-2:] == ["detach", "cleanup"]
    assert worker.calls[-1] == "close"


def test_chat_admission_tracks_verified_packet_session_and_teardown():
    network = FakeNetwork()
    worker = FakeWorker(network)
    worker.chat = object()
    class ChatMaterials(FakeMaterials):
        def resolve(self, *args):
            result = super().resolve(*args)
            result['readiness']['device'] = 'a' * 32
            return result
    supervisor = service.Supervisor(network, ChatMaterials())
    supervisor.worker_factory = lambda: worker
    assert supervisor.chat_binding() is None
    assert supervisor.start(materials())
    try:
        wait_for(lambda: supervisor.chat_binding() is not None)
        binding = supervisor.chat_binding()
        assert binding.device == 'a' * 32 and binding.ready.is_set()
        assert 'routes_and_dns' in network.operations
        assert binding.lane is worker.chat
        assert 'private' not in supervisor.status()
    finally:
        assert supervisor.stop()
    assert supervisor.chat_binding() is None
    assert binding.closed.is_set() and not binding.ready.is_set() and not binding.material


def test_chat_admission_is_not_published_after_route_failure():
    network = FakeNetwork()
    network.fail_attach = True
    worker = FakeWorker(network)
    worker.chat = object()
    supervisor = service.Supervisor(network, FakeMaterials())
    supervisor.worker_factory = lambda: worker
    assert supervisor.start(materials())
    try:
        wait_for(lambda: supervisor.status()['state'] == 'FAILED')
        assert supervisor.chat_binding() is None
    finally:
        assert supervisor.stop()


def test_no_connected_on_failed_routing_guard_retained_until_disconnect():
    network = FakeNetwork()
    network.fail_attach = True
    supervisor = service.Supervisor(network, FakeMaterials())
    worker = FakeWorker(network)
    supervisor.worker_factory = lambda: worker
    assert supervisor.start(materials())
    try:
        wait_for(lambda: supervisor.status()["state"] == "FAILED")
        assert "routed" not in worker.calls
        assert "cleanup" not in network.operations
        assert supervisor.status()["desired_connected"]
        assert supervisor.status()["first_reason"] == "PACKET_OR_IPC_FAILED"
    finally:
        assert supervisor.stop()


def test_authorization_failure_never_retries_or_falls_back():
    network = FakeNetwork()
    supervisor = service.Supervisor(network, FakeMaterials())
    worker = FakeWorker(network, "FAILED", "FAMILY_REJECTED")
    supervisor.worker_factory = lambda: worker
    assert supervisor.start(materials())
    try:
        wait_for(lambda: supervisor.status()["state"] == "FAILED")
        assert supervisor.status()["reason"] == "FAMILY_REJECTED"
        assert worker.calls == ["start", "close"]
        assert "cleanup" not in network.operations
    finally:
        assert supervisor.stop()


def test_disconnect_during_restoring_cancels_backoff_without_second_worker():
    network = FakeNetwork()
    supervisor = service.Supervisor(network, FakeMaterials())
    worker = FakeWorker(network, "FAILED", "NETWORK_ERROR")
    supervisor.worker_factory = lambda: worker
    assert supervisor.start(materials())
    try:
        wait_for(lambda: supervisor.status()["state"] == "RESTORING")
        assert supervisor.status()["attempt"] == 1
        assert "cleanup" not in network.operations
    finally:
        assert supervisor.stop()
    assert worker.calls == ["start", "close"]


def test_bounded_history_preserves_first_and_latest_events():
    supervisor = service.Supervisor(FakeNetwork(), FakeMaterials())
    for number in range(80):
        supervisor.attempt = number
        supervisor.transition("RESTORING", "NETWORK_ERROR")
    snapshot = supervisor.status()
    assert len(snapshot["events"]) == 32
    assert snapshot["events"][0]["attempt"] == 0
    assert snapshot["events"][-1]["attempt"] == 79
    assert snapshot["events_dropped"] == 48


def test_cancel_rejects_late_positive_state_callback():
    supervisor = service.Supervisor(FakeNetwork(), FakeMaterials())
    supervisor.cancel.set()
    for state in ("CONNECTING", "RESTORING", "CONNECTED"):
        supervisor.transition(state)
    assert supervisor.status()["state"] == "DISCONNECTED"
    assert supervisor.status()["events"] == []


def test_unexpected_setup_failure_stays_guarded_until_stop():
    network = FakeNetwork()
    def broken():
        network.operations.append("guard")
        raise KeyError("synthetic malformed system readback")
    network.prepare = broken
    supervisor = service.Supervisor(network, FakeMaterials())
    assert supervisor.start(materials())
    try:
        wait_for(lambda: supervisor.status()["state"] == "FAILED")
        assert "cleanup" not in network.operations
    finally:
        assert supervisor.stop()


def test_foreign_or_unowned_journal_never_drives_cleanup(tmp_path, monkeypatch):
    journal = tmp_path / "active.json"
    journal.write_text("{}")
    network = system.Network(journal, 1000)
    monkeypatch.setattr(system, "command", lambda *args, **kwargs: pytest.fail("Must not mutate networking"))
    network.cleanup()
    assert journal.exists()
    with pytest.raises(ValueError):
        network._prepare()
    foreign = dict(network.record, uid=1001)
    monkeypatch.setattr(system, "private_read", lambda path: foreign)
    with pytest.raises(ValueError):
        network.restore()
    assert not network.owns_journal


def test_partial_guard_cleanup_uses_only_the_recorded_prefix(tmp_path, monkeypatch):
    journal = tmp_path / "active.json"
    journal.write_text("{}")
    network = system.Network(journal, 1000)
    record = dict(network.record, guard_count=2)
    monkeypatch.setattr(system, "private_read", lambda path: record)
    commands = []
    monkeypatch.setattr(system, "command", lambda *args, **kwargs: commands.append(args))
    network.restore()
    network.query = lambda *arguments: []
    network.cleanup()
    assert len(commands) == 2
    assert all(arguments[:4] in (("ip", "-6", "route", "del"), ("ip", "-4", "route", "del")) for arguments in commands)
    assert not journal.exists()


def test_cleanup_never_reverts_reused_interface_name(tmp_path, monkeypatch):
    network = system.Network(tmp_path / "active.json", 1000)
    network.record["packet_index"] = 7
    network.query = lambda *args: [{"ifname": "fcmesh0", "ifindex": 8}]
    monkeypatch.setattr(system, "command", lambda *args, **kwargs: pytest.fail("Must not remove a foreign interface"))
    with pytest.raises(ValueError, match="ownership"):
        network.detach()


def test_restored_service_never_reports_a_new_manual_connect():
    network = FakeNetwork()
    supervisor = service.Supervisor(network, FakeMaterials())
    supervisor.worker_factory = lambda: FakeWorker(network)
    assert supervisor.start(materials(), restoring=True)
    try:
        wait_for(lambda: supervisor.status()['state'] == 'CONNECTED')
        snapshot = supervisor.status()
        assert snapshot['events'][0]['reason'] == 'SERVICE_RESTARTED'
        assert not any(event['state'] == 'CONNECTING' for event in snapshot['events'])
        assert snapshot['first_reason'] == 'NONE'
    finally:
        assert supervisor.stop()


def test_disconnect_revokes_before_stopping_and_still_cancels_on_write_failure():
    operations = []
    supervisor = service.Supervisor(FakeNetwork(), FakeMaterials())
    stopping = threading.Event()
    class Intent:
        def revoke(self):
            operations.append('revoke')
            assert not supervisor.cancel.is_set()
    assert helper.dispatch(supervisor, Intent(), dict(action='stop'), stopping)
    assert operations == ['revoke'] and supervisor.cancel.is_set() and stopping.is_set()
    supervisor.cancel.clear()
    stopping.clear()
    class FailedIntent:
        def revoke(self):
            raise OSError('synthetic fence failure')
    with pytest.raises(OSError):
        helper.dispatch(supervisor, FailedIntent(), dict(action='stop'), stopping)
    assert supervisor.cancel.is_set() and stopping.is_set()


def test_start_is_not_executed_before_intent_store_and_stop_wins_during_store():
    supervisor = service.Supervisor(FakeNetwork(), FakeMaterials())
    stopping = threading.Event()
    operations = []
    class Intent:
        def begin(self, material):
            assert supervisor.thread is None
            operations.append('store')
            stopping.set()
        def revoke(self):
            operations.append('revoke')
    assert not helper.dispatch(supervisor, Intent(), dict(action='start', materials=materials()), stopping)
    assert operations == ['store', 'revoke'] and supervisor.thread is None


def test_recovery_retains_guard_until_explicit_revoke(tmp_path, monkeypatch):
    from test_mesh_network import snapshots
    rules4, rules6, routes4, routes6 = snapshots()
    journal = tmp_path / 'active.json'
    journal.write_text('{}')
    current = system.Network(journal, 1000, retain=lambda: True)
    current.owns_journal = True
    current.record['guard_count'] = 6
    operations = []
    def query(*arguments):
        family = arguments[0]
        if arguments[:2] == ('-d', 'link'):
            return []
        if arguments[1] == 'rule':
            return rules4 if family == '-4' else rules6
        if arguments[-1] == 'all':
            return [dict(route, table=64640) for route in (routes4 if family == '-4' else routes6)]
        return routes4 if family == '-4' else routes6
    def command(*arguments, **kwargs):
        operations.append(arguments)
        assert arguments[3] == 'del'
        target = (routes4 if arguments[1] == '-4' else routes6) if arguments[2] == 'route' else (rules4 if arguments[1] == '-4' else rules6)
        if arguments[2] == 'route':
            target.clear()
        else:
            priority = int(arguments[arguments.index('priority') + 1])
            target[:] = [rule for rule in target if rule['priority'] != priority]
    current.query = query
    monkeypatch.setattr(system, 'command', command)
    current.cleanup()
    assert journal.exists() and operations == []
    current.retain = lambda: False
    current.cleanup()
    assert not journal.exists() and len(operations) == 6


def test_resume_without_owned_journal_never_adopts_foreign_resources(tmp_path, monkeypatch):
    journal = tmp_path / 'active.json'
    journal.write_text('{}')
    current = system.Network(journal, 1000, resuming=True)
    monkeypatch.setattr(system, 'private_read', lambda path: dict(current.record, uid=1001))
    monkeypatch.setattr(system, 'command', lambda *args, **kwargs: pytest.fail('foreign network mutation'))
    with pytest.raises(ValueError, match='owner mismatch'):
        current._prepare()
