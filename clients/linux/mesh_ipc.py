"""Bounded desktop-to-service and service-to-native private IPC."""
import base64
import json
import math
import os
import select
import socket
import struct
import time

MAX_REQUEST = 96 * 1024
MAX_REPLY = 512 * 1024


class ProtocolError(ValueError):
    def __init__(self):
        super().__init__("Invalid MESH IPC")


def _object(pairs):
    result = {}
    for name, value in pairs:
        if name in result:
            raise ProtocolError()
        result[name] = value
    return result


def _bounded(value, depth=0):
    if depth > 16 or (isinstance(value, float) and not math.isfinite(value)):
        raise ProtocolError()
    if isinstance(value, dict):
        for item in value.values():
            _bounded(item, depth + 1)
    elif isinstance(value, list):
        for item in value:
            _bounded(item, depth + 1)


def decode(raw, maximum):
    if not 0 < len(raw) <= maximum:
        raise ProtocolError()
    try:
        value = json.loads(raw, object_pairs_hook=_object)
        _bounded(value)
        if not isinstance(value, dict):
            raise ProtocolError()
        return value
    except (ValueError, UnicodeError, RecursionError):
        raise ProtocolError() from None


def encode(value, maximum):
    try:
        _bounded(value)
        raw = json.dumps(value, separators=(",", ":"), allow_nan=False).encode()
        if not 0 < len(raw) <= maximum:
            raise ProtocolError()
        return struct.pack("!I", len(raw)) + raw
    except (TypeError, ValueError, RecursionError):
        raise ProtocolError() from None


def _read(descriptor, count, deadline, cancel=None):
    data = bytearray()
    while len(data) < count:
        if cancel is not None and cancel.is_set():
            raise InterruptedError("MESH IPC cancelled")
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("MESH IPC deadline")
        if not select.select([descriptor], [], [], min(remaining, .2) if cancel is not None else remaining)[0]:
            continue
        part = os.read(descriptor, count - len(data))
        if not part:
            raise EOFError("MESH IPC closed")
        data.extend(part)
    return data


def receive(descriptor, maximum, deadline, cancel=None):
    size = struct.unpack("!I", _read(descriptor, 4, deadline, cancel))[0]
    if not 0 < size <= maximum:
        raise ProtocolError()
    raw = _read(descriptor, size, deadline, cancel)
    try:
        return decode(raw, maximum)
    finally:
        raw[:] = b"\0" * len(raw)


def send(descriptor, value, maximum, deadline, cancel=None):
    payload = memoryview(encode(value, maximum))
    while payload:
        if cancel is not None and cancel.is_set():
            raise InterruptedError("MESH IPC cancelled")
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("MESH IPC deadline")
        if not select.select([], [descriptor], [], min(remaining, .2) if cancel is not None else remaining)[1]:
            continue
        count = os.write(descriptor, payload[:4096])
        if not count:
            raise EOFError("MESH IPC closed")
        payload = payload[count:]


def peer_uid(connection):
    return struct.unpack("3i", connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))[1]


def validate_request(value):
    if not isinstance(value, dict) or value.get("schema") != 1 or type(value.get("schema")) is not int:
        raise ProtocolError()
    if type(value.get("id")) is not int or not 0 < value["id"] < 2**63:
        raise ProtocolError()
    action = value.get("action")
    expected = {"schema", "id", "action", "materials"} if action == "start" else {"schema", "id", "action"}
    if set(value) != expected or action not in ("start", "status", "stop"):
        raise ProtocolError()
    if action == "start":
        material = value["materials"]
        if not isinstance(material, dict) or set(material) != {"wireguard_public", "identity", "anchor", "profile"}:
            raise ProtocolError()
        if material["profile"] not in ("P0", "P1"):
            raise ProtocolError()
        for field, size in (("identity", 64), ("anchor", 32), ("wireguard_public", 32)):
            try:
                decoded = base64.b64decode(material[field], validate=True)
                if len(decoded) != size or base64.b64encode(decoded).decode() != material[field]:
                    raise ProtocolError()
            except (TypeError, ValueError):
                raise ProtocolError() from None
    return value
