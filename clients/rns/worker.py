"""Fixed-provider RNS byte worker; no product identity, proof generation or VPN policy."""
import base64
import importlib.metadata
import json
import signal
import socket
import struct
import sys
import tempfile
import threading
import time

SCHEMA = 1
MAX_REQUEST = 32768
MAX_REPLY = 131072
HOST = "186.246.45.246"
PORT = 4242
PROVIDER = "vKri/FwEyJe/AoepLwYxN/T64cqzwVft+HxMCMDcmV8DcTOoLqnoHVjpThpwhvU2eSO+OoMTEg90lUs3VCOV8A=="
PATHS = frozenset("/friends/restricted-readiness" + suffix for suffix in ("", "/challenge", "/ack-challenge", "/ack"))


def unique(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("DUPLICATE_FIELD")
        result[key] = value
    return result


def decode(raw, maximum):
    if not 0 < len(raw) <= maximum:
        raise ValueError("FRAME_LIMIT")
    value = json.loads(raw.decode("utf-8"), object_pairs_hook=unique,
                       parse_constant=lambda _: (_ for _ in ()).throw(ValueError("NONFINITE")))
    if not isinstance(value, dict):
        raise ValueError("INVALID_OBJECT")
    return value


def request(value, expected):
    if set(value) != {"schema", "id", "underlying_index", "budget_ms", "path", "body"}:
        raise ValueError("COMMAND_FIELDS")
    for name, lower, upper in (("schema", 1, 1), ("id", expected, expected), ("underlying_index", 1, 2147483647), ("budget_ms", 1, 200000)):
        if type(value[name]) is not int or not lower <= value[name] <= upper:
            raise ValueError("COMMAND_VALUE")
    if not isinstance(value["path"], str) or value["path"] not in PATHS or not isinstance(value["body"], str):
        raise ValueError("COMMAND_VALUE")
    raw = base64.b64decode(value["body"], validate=True)
    if not 0 < len(raw) <= 8192 or base64.b64encode(raw).decode() != value["body"]:
        raise ValueError("COMMAND_BODY")
    return raw


class Callbacks:
    def __init__(self, index, deadline, stop):
        self.index, self.deadline, self.stop = index, deadline, stop
        self.name = socket.if_indextoname(index)
        if self.name in ("lo", "lo0", "fcmesh0"):
            raise ValueError("UNDERLAY_REJECTED")

    def stopReason(self):
        return "CANCELLED" if self.stop.is_set() else "TIMEOUT" if time.monotonic() >= self.deadline else "NONE"

    def cancelled(self):
        return self.stopReason() != "NONE"

    def bindSocket(self, descriptor):
        if self.cancelled():
            return False
        try:
            if socket.if_indextoname(self.index) != self.name:
                return False
        except OSError:
            return False
        wrapped = socket.socket(fileno=descriptor)
        try:
            if wrapped.family != socket.AF_INET:
                return False
            if sys.platform == "linux":
                wrapped.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, self.name.encode() + b"\0")
                wrapped.setsockopt(socket.SOL_SOCKET, socket.SO_MARK, 64640)
                valid = wrapped.getsockopt(socket.SOL_SOCKET, socket.SO_MARK) == 64640
                valid = valid and wrapped.getsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, 256).rstrip(b"\0") == self.name.encode()
            elif sys.platform == "win32":
                interface = struct.pack("!I", self.index)
                wrapped.setsockopt(socket.IPPROTO_IP, 31, interface)
                valid = wrapped.getsockopt(socket.IPPROTO_IP, 31, 4) == interface
            else:
                return False
            return valid and not self.cancelled() and socket.if_indextoname(self.index) == self.name
        except OSError:
            return False
        finally:
            wrapped.detach()


def read_exact(stream, count):
    raw = bytearray()
    while len(raw) < count:
        part = stream.read(count - len(raw))
        if not part:
            raise EOFError()
        raw.extend(part)
    return bytes(raw)


def serve(source, sink, transport, stop):
    channel = None
    callbacks = None
    with tempfile.TemporaryDirectory(prefix="fc-rns-") as directory:
        try:
            for identifier in range(1, 5):
                size = struct.unpack("!I", read_exact(source, 4))[0]
                if not 0 < size <= MAX_REQUEST:
                    raise ValueError("FRAME_LIMIT")
                command = decode(read_exact(source, size), MAX_REQUEST)
                request(command, identifier)
                reply = dict(schema=SCHEMA, id=identifier, code="REJECTED")
                try:
                    deadline = time.monotonic() + command["budget_ms"] / 1000
                    if callbacks is None:
                        callbacks = Callbacks(command["underlying_index"], deadline, stop)
                        channel = transport.Channel(directory, HOST, PORT, PROVIDER, callbacks)
                    elif command["underlying_index"] != callbacks.index:
                        raise ValueError("UNDERLAY_CHANGED")
                    else:
                        callbacks.deadline = min(callbacks.deadline, deadline)
                    callbacks_state = callbacks.stopReason()
                    if callbacks_state != "NONE":
                        reply["code"] = "CANCELLED" if callbacks_state == "CANCELLED" else "UNAVAILABLE"
                    else:
                        result = channel.readiness_request(command["path"], command["body"])
                        if result[0] == "UNAVAILABLE":
                            reply["code"] = "UNAVAILABLE"
                        elif result[0] == "AVAILABLE":
                            body = base64.b64decode(result[1], validate=True)
                            if not 0 < len(body) <= 90000 or base64.b64encode(body).decode() != result[1]:
                                raise ValueError("RESPONSE_LIMIT")
                            reply.update(code="OK", body=result[1])
                except transport.TransportUnavailable:
                    reply["code"] = "UNAVAILABLE"
                except (OSError, ValueError, TypeError, IndexError):
                    reply["code"] = "CANCELLED" if stop.is_set() else "REJECTED"
                finally:
                    command.clear()
                if stop.is_set():
                    reply = dict(schema=SCHEMA, id=identifier, code="CANCELLED")
                raw = json.dumps(reply, separators=(",", ":")).encode()
                if len(raw) > MAX_REPLY:
                    raise ValueError("FRAME_LIMIT")
                sink.write(struct.pack("!I", len(raw)) + raw)
                sink.flush()
                if reply["code"] != "OK":
                    return
        except EOFError:
            return
        finally:
            stop.set()
            if channel is not None:
                channel.close()


def main():
    if sys.argv[1:] not in (["--stdio"], ["--version"]):
        return 64
    if importlib.metadata.version("rns") != "1.5.1":
        return 65
    if sys.argv[1:] == ["--version"]:
        import RNS
        if not hasattr(importlib.import_module("RNS.Reticulum"), "BackboneInterface"):
            return 65
        print(json.dumps(dict(rns_protocol=SCHEMA, rns="1.5.1", pyserial=importlib.metadata.version("pyserial"),
                             crypto_provider=RNS.Cryptography.Provider.backend())))
        return 0
    source, sink = sys.stdin.buffer, sys.stdout.buffer
    sys.stdout = sys.stderr
    import fc_rns_transport as transport
    stop = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    try:
        serve(source, sink, transport, stop)
    except (OSError, ValueError, TypeError, RecursionError):
        return 65
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(65)
