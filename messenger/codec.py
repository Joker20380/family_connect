"""Bounded LXMF text subset; explicit verified contacts, independent chat identity.

The carrier must use encrypted DIRECT delivery. Packed bytes are signed plaintext,
not a transport encryption envelope, and must never be logged or sent over raw TCP.
"""
import hashlib
import math

import LXMF
import RNS
import RNS.vendor.umsgpack as msgpack

MAX_TEXT = 4096
MAX_PACKED = 4608


def identity(public):
    if type(public) is not bytes or len(public) != 64:
        raise ValueError('Invalid contact public key')
    result = RNS.Identity(create_keys=False)
    result.load_public_key(public)
    return result


def address(public):
    return RNS.Destination.hash(identity(public), 'lxmf', 'delivery')


def pack(sender, recipient, text):
    if type(text) is not str or not 0 < len(text.encode('utf-8')) <= MAX_TEXT:
        raise ValueError('Text must contain 1..4096 UTF-8 bytes')
    destination = RNS.Destination(identity(recipient), RNS.Destination.OUT,
                                  RNS.Destination.SINGLE, 'lxmf', 'delivery')
    source = RNS.Destination(sender, RNS.Destination.OUT,
                            RNS.Destination.SINGLE, 'lxmf', 'delivery')
    message = LXMF.LXMessage(destination, source, text, desired_method=LXMF.LXMessage.DIRECT)
    message.pack()
    return message.packed


def unpack(raw, *, recipient, contacts):
    """contacts maps verified delivery-address bytes to their full public keys."""
    if type(raw) is not bytes or not 96 < len(raw) <= MAX_PACKED:
        raise ValueError('Invalid message size')
    target, source, signature, payload = raw[:16], raw[16:32], raw[32:96], raw[96:]
    if target != address(recipient) or source not in contacts:
        raise ValueError('Wrong recipient or unknown contact')
    public = contacts[source]
    if address(public) != source:
        raise ValueError('Contact address mismatch')
    hashed = target + source + payload
    message_id = hashlib.sha256(hashed).digest()
    if not identity(public).validate(signature, hashed + message_id):
        raise ValueError('Invalid message signature')
    try:
        body = msgpack.unpackb(payload)
        if type(body) is not list or len(body) != 4:
            raise ValueError()
        timestamp, title, content, fields = body
        if (type(timestamp) not in (int, float) or not math.isfinite(timestamp) or timestamp < 0
                or title != b'' or type(fields) is not dict or fields
                or type(content) is not bytes or not 0 < len(content) <= MAX_TEXT):
            raise ValueError()
        text = content.decode('utf-8')
    except (ValueError, TypeError, IndexError, RecursionError, msgpack.UnpackException):
        raise ValueError('Unsupported LXMF text payload') from None
    return dict(id=message_id.hex(), peer=source.hex(), text=text, timestamp=timestamp)
