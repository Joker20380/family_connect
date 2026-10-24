"""Bounded public chat-only socket protocol shared by the user and root services."""
import array
import base64
import hashlib
import json
import math
import os
import re
import socket
import struct
import time

MAX_FRAME = 32 * 1024
PATHS = ('/friends/chat/challenge', '/friends/chat/register')
ERRORS = ('DENIED', 'CONFLICT', 'UNAVAILABLE', 'DEADLINE', 'CANCELLED')


class BridgeError(OSError):
    def __init__(self, code='UNAVAILABLE'):
        self.code = code if code in ERRORS else 'UNAVAILABLE'
        super().__init__(self.code)


def pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError('Invalid chat message')
        result[key] = value
    return result


def bounded(value, depth=0):
    if depth > 16 or (isinstance(value, float) and not math.isfinite(value)):
        raise ValueError('Invalid chat message')
    if isinstance(value, dict):
        for item in value.values():
            bounded(item, depth + 1)
    elif isinstance(value, list):
        for item in value:
            bounded(item, depth + 1)


def encode(value):
    bounded(value)
    raw = json.dumps(value, separators=(',', ':'), allow_nan=False).encode()
    if not 0 < len(raw) <= MAX_FRAME:
        raise ValueError('Invalid chat message')
    return struct.pack('!I', len(raw)) + raw


def read(connection, deadline):
    def exact(size):
        result = bytearray()
        while len(result) < size:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise BridgeError('DEADLINE')
            connection.settimeout(remaining)
            part = connection.recv(size - len(result))
            if not part:
                raise BridgeError()
            result.extend(part)
        return result
    size = struct.unpack('!I', exact(4))[0]
    if not 0 < size <= MAX_FRAME:
        raise ValueError('Invalid chat message')
    raw = exact(size)
    try:
        value = json.loads(raw, object_pairs_hook=pairs)
        bounded(value)
        if type(value) is not dict:
            raise ValueError('Invalid chat message')
        return value
    finally:
        raw[:] = b'\0' * len(raw)


def write(connection, value):
    connection.settimeout(4)
    connection.sendall(encode(value))


def payload(value, maximum):
    if type(value) is not str or len(value) > 4 * ((maximum + 2) // 3):
        raise ValueError('Invalid chat payload')
    raw = base64.b64decode(value, validate=True)
    if len(raw) > maximum or base64.b64encode(raw).decode() != value:
        raise ValueError('Invalid chat payload')
    return raw


def validate(request):
    if (type(request.get('schema')) is not int or request['schema'] != 1 or
            type(request.get('id')) is not int or not 0 < request['id'] < 2**63 or
            type(request.get('device')) is not str or not re.fullmatch('[0-9a-f]{32}', request['device']) or
            type(request.get('budget_ms')) is not int or not 0 < request['budget_ms'] <= 30000):
        raise ValueError('Invalid chat request')
    expected = {'schema', 'id', 'action', 'device', 'budget_ms'}
    if request.get('action') == 'request':
        expected |= {'path', 'data'}
        if request.get('path') not in PATHS:
            raise ValueError('Invalid chat request')
        raw = payload(request.get('data'), 8192)
        body = json.loads(raw, object_pairs_hook=pairs)
        bounded(body)
        if type(body) is not dict:
            raise ValueError('Invalid chat request')
        binding = body if request['path'] == PATHS[0] else body.get('proof')
        if type(binding) is not dict:
            raise BridgeError('DENIED')
        public = payload(binding.get('public_identity'), 64)
        if len(public) != 64 or hashlib.sha256(public).hexdigest()[:32] != request['device']:
            raise BridgeError('DENIED')
    elif request.get('action') not in ('open', 'probe'):
        raise ValueError('Invalid chat request')
    if set(request) != expected:
        raise ValueError('Invalid chat request')
    return request


def send_socket(connection, channel):
    descriptors = array.array('i', [channel.fileno()])
    if connection.sendmsg([b'F'], [(socket.SOL_SOCKET, socket.SCM_RIGHTS, descriptors)]) != 1:
        raise BridgeError()


def receive_socket(connection):
    descriptors = []
    try:
        data, controls, flags, _ = connection.recvmsg(1, socket.CMSG_SPACE(8 * array.array('i').itemsize), socket.MSG_CMSG_CLOEXEC)
        valid = True
        for level, kind, raw in controls:
            if level != socket.SOL_SOCKET or kind != socket.SCM_RIGHTS:
                valid = False
                continue
            values = array.array('i')
            values.frombytes(raw[:len(raw) - len(raw) % values.itemsize])
            descriptors.extend(values)
        if not valid or data != b'F' or flags & (socket.MSG_CTRUNC | socket.MSG_TRUNC) or len(descriptors) != 1:
            raise BridgeError()
        channel = socket.socket(fileno=descriptors[0])
        descriptors.pop()
        try:
            if channel.family != socket.AF_UNIX or channel.type & 0xf != socket.SOCK_STREAM:
                raise BridgeError()
            os.set_inheritable(channel.fileno(), False)
            return channel
        except BaseException:
            channel.close()
            raise
    finally:
        for descriptor in descriptors:
            os.close(descriptor)
