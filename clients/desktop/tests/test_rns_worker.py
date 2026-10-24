import base64
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import socket
import struct
import threading
import time

import pytest

ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location("fc_desktop_rns_worker", ROOT / "clients/rns/worker.py")
relay = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(relay)


def command(identifier=1):
    return dict(schema=1, id=identifier, underlying_index=2, budget_ms=1000,
                path="/friends/restricted-readiness/challenge", body=base64.b64encode(b"{}").decode())


def frame(value):
    raw = json.dumps(value).encode()
    return struct.pack("!I", len(raw)) + raw


def test_rns_worker_matches_exact_accepted_provider_and_transport_source():
    capsule = ROOT / "state-client-build/owner-diagnostic106-20261022/android-source/clients/android/app/src/main"
    expected = json.loads((capsule / "assets/rns-relay.json").read_text())
    assert dict(host=relay.HOST, port=relay.PORT, provider_public=relay.PROVIDER) == expected
    assert len(base64.b64decode(relay.PROVIDER, validate=True)) == 64
    actual = (ROOT / "clients/rns/fc_rns_transport.py").read_bytes()
    assert hashlib.sha256(actual).hexdigest() == "70593713d1d915904d10cf0cac0eb21ca41b11b4dedcdb7973d0da236579ada0"


@pytest.mark.parametrize("change", [{"schema": True}, {"id": 2}, {"underlying_index": 0}, {"budget_ms": 200001},
    {"path": "/exec"}, {"provider": "other"}, {"identity": "private"}, {"body": "e30=\n"}, {"body": ""}])
def test_rns_worker_rejects_non_byte_transport_commands(change):
    value = command()
    value.update(change)
    with pytest.raises(ValueError):
        relay.request(value, 1)


def test_rns_worker_rejects_duplicate_and_oversized_frames():
    with pytest.raises(ValueError):
        relay.decode(b'{"id":1,"id":2}', 32768)
    with pytest.raises(ValueError):
        relay.decode(b"x" * 32769, 32768)
    with pytest.raises(ValueError):
        relay.serve(io.BytesIO(struct.pack("!I", 32769)), io.BytesIO(), None, threading.Event())


class FakeTransport:
    class TransportUnavailable(OSError):
        pass

    calls = []
    closed = 0

    class Channel:
        def __init__(self, directory, host, port, provider, callbacks):
            self.callbacks = callbacks
            assert (host, port, provider) == (relay.HOST, relay.PORT, relay.PROVIDER)
            FakeTransport.calls.append("open")

        def readiness_request(self, path, body):
            FakeTransport.calls.append(path)
            return ["AVAILABLE", base64.b64encode(b'{"status":200,"body":"e30="}').decode()]

        def close(self):
            FakeTransport.closed += 1


def test_rns_worker_one_link_and_fixed_provider_for_both_messages(monkeypatch):
    monkeypatch.setattr(socket, "if_indextoname", lambda _: "synthetic")
    FakeTransport.calls, FakeTransport.closed = [], 0
    first, second = command(), command(2)
    second["path"] = "/friends/restricted-readiness"
    source, sink = io.BytesIO(frame(first) + frame(second)), io.BytesIO()
    relay.serve(source, sink, FakeTransport, threading.Event())
    result = io.BytesIO(sink.getvalue())
    for identifier in (1, 2):
        size = struct.unpack("!I", relay.read_exact(result, 4))[0]
        value = relay.decode(relay.read_exact(result, size), 131072)
        assert value["code"] == "OK" and value["id"] == identifier
    assert FakeTransport.calls == ["open", first["path"], second["path"]]
    assert FakeTransport.closed == 1


class FakeSocket:
    family = socket.AF_INET

    def __init__(self):
        self.options = {}
        self.detached = False

    def setsockopt(self, level, option, value):
        self.options[level, option] = value

    def getsockopt(self, level, option, *args):
        return self.options[level, option]

    def detach(self):
        self.detached = True


@pytest.mark.parametrize("platform", ["linux", "win32"])
def test_rns_socket_binding_uses_exact_underlay_not_android_stub(monkeypatch, platform):
    monkeypatch.setattr(socket, "if_indextoname", lambda _: "synthetic")
    monkeypatch.setattr(relay.sys, "platform", platform)
    descriptor = FakeSocket()
    monkeypatch.setattr(socket, "socket", lambda **_: descriptor)
    callbacks = relay.Callbacks(2, time.monotonic() + 5, threading.Event())
    assert callbacks.bindSocket(123)
    assert descriptor.detached
    if platform == "linux":
        assert descriptor.options[socket.SOL_SOCKET, socket.SO_BINDTODEVICE] == b"synthetic\0"
        assert descriptor.options[socket.SOL_SOCKET, socket.SO_MARK] == 64640
    else:
        assert descriptor.options[socket.IPPROTO_IP, 31] == b"\0\0\0\2"


def test_rns_binding_denied_or_replaced_interface_never_falls_back(monkeypatch):
    monkeypatch.setattr(socket, "if_indextoname", lambda _: "synthetic")
    callbacks = relay.Callbacks(2, time.monotonic() + 5, threading.Event())
    descriptor = FakeSocket()
    def denied(*args):
        raise PermissionError()
    descriptor.setsockopt = denied
    monkeypatch.setattr(socket, "socket", lambda **_: descriptor)
    assert not callbacks.bindSocket(123) and descriptor.detached
    monkeypatch.setattr(socket, "if_indextoname", lambda _: "changed")
    assert not callbacks.bindSocket(123)
    callbacks.stop.set()
    assert callbacks.stopReason() == "CANCELLED"


@pytest.mark.parametrize("name", ["lo", "lo0", "fcmesh0"])
def test_rns_rejects_recursive_and_loopback_underlay(monkeypatch, name):
    monkeypatch.setattr(socket, "if_indextoname", lambda _: name)
    with pytest.raises(ValueError):
        relay.Callbacks(2, time.monotonic() + 5, threading.Event())
