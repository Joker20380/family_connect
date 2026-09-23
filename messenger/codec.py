"""Bounded LXMF text subset; explicit verified contacts, independent chat identity.

The carrier must use encrypted DIRECT delivery. Packed bytes are signed plaintext,
not a transport encryption envelope, and must never be logged or sent over raw TCP.
"""
import hashlib
import math
import base64
import struct

import LXMF
import RNS
import RNS.vendor.umsgpack as msgpack

MAX_TEXT = 4096
MAX_PACKED = 131584
MAX_AUDIO = 131072
# Shared closed-ingress path: native clients do not import the server's spool.
PUT_PATH = '/family_connect/chat/v1/put'


def identity(public):
    if type(public) is not bytes or len(public) != 64:
        raise ValueError('Invalid contact public key')
    result = RNS.Identity(create_keys=False)
    result.load_public_key(public)
    return result


def address(public):
    return RNS.Destination.hash(identity(public), 'lxmf', 'delivery')


def pack(sender, recipient, text, fields=None):
    if type(text) is not str or len(text.encode('utf-8')) > MAX_TEXT or (not text and not fields):
        raise ValueError('Text must contain 1..4096 UTF-8 bytes')
    destination = RNS.Destination(identity(recipient), RNS.Destination.OUT,
                                  RNS.Destination.SINGLE, 'lxmf', 'delivery')
    source = RNS.Destination(sender, RNS.Destination.OUT,
                            RNS.Destination.SINGLE, 'lxmf', 'delivery')
    message = LXMF.LXMessage(destination, source, text, fields=fields or {}, desired_method=LXMF.LXMessage.DIRECT)
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
                or title != b'' or type(fields) is not dict
                or type(content) is not bytes or len(content) > MAX_TEXT or (not content and not fields)):
            raise ValueError()
        text = content.decode('utf-8')
        extra=parse_fields(fields,text)
    except (ValueError, TypeError, IndexError, RecursionError, msgpack.UnpackException):
        raise ValueError('Unsupported LXMF text payload') from None
    return dict(id=message_id.hex(), peer=source.hex(), text=text, timestamp=timestamp,**extra)


def _ogg_crc(page):
    crc = 0
    for byte in page:
        crc ^= byte << 24
        for _ in range(8):
            crc = ((crc << 1) ^ 0x04c11db7 if crc & 0x80000000 else crc << 1) & 0xffffffff
    return crc


def finalize_recorded_opus(raw):
    """Finalize complete Android OggWriter pages before signing for delivery.

    MediaRecorder can stop without emitting EOS. Never repair missing bytes or
    incomplete packets; verify page checksums before changing the last flag.
    Receivers continue to require the ordinary bounded, finalized envelope.
    """
    if type(raw) is not bytes or not 64 <= len(raw) <= MAX_AUDIO:
        raise ValueError('Invalid audio size')
    offset = 0
    last_offset = None
    while offset < len(raw):
        if offset + 27 > len(raw) or raw[offset:offset+5] != b'OggS\x00':
            raise ValueError('Invalid Ogg page')
        count = raw[offset+26]
        header = offset + 27 + count
        if not count or header > len(raw):
            raise ValueError('Invalid Ogg segments')
        end = header + sum(raw[offset+27:header])
        if end > len(raw):
            raise ValueError('Truncated audio')
        page = bytearray(raw[offset:end])
        expected = struct.unpack_from('<I', page, 22)[0]
        page[22:26] = bytes(4)
        if _ogg_crc(page) != expected:
            raise ValueError('Invalid Ogg checksum')
        if raw[offset+5] & 4 and end != len(raw):
            raise ValueError('Chained audio not supported')
        last_offset = offset
        offset = end
    if raw[header-1] == 255:
        raise ValueError('Incomplete Opus packet')
    if not raw[last_offset+5] & 4:
        page = bytearray(raw[last_offset:])
        page[5] |= 4
        page[22:26] = bytes(4)
        struct.pack_into('<I', page, 22, _ogg_crc(page))
        raw = raw[:last_offset] + bytes(page)
    opus_duration(raw)
    return raw


def opus_duration(raw):
    """Bounded mono Ogg/Opus envelope. Decoder performs codec-level validation."""
    if type(raw) is not bytes or not 64<=len(raw)<=MAX_AUDIO:raise ValueError('Invalid audio size')
    offset=0;sequence=0;serial=None;last=0;skip=None;eos=False
    while offset<len(raw):
        if offset+27>len(raw) or raw[offset:offset+5]!=b'OggS\x00':raise ValueError('Invalid Ogg page')
        count=raw[offset+26];header=offset+27+count
        if header>len(raw):raise ValueError('Invalid Ogg segments')
        end=header+sum(raw[offset+27:header])
        if end>len(raw):raise ValueError('Truncated audio')
        page_serial,number=struct.unpack_from('<II',raw,offset+14)
        if serial is None:serial=page_serial
        if page_serial!=serial or number!=sequence:raise ValueError('Invalid Ogg sequence')
        if sequence==0:
            packet=raw[header:end]
            if not packet.startswith(b'OpusHead') or len(packet)!=19 or packet[8]!=1 or packet[9]!=1 or packet[18]!=0:raise ValueError('Mono Opus required')
            skip=struct.unpack_from('<H',packet,10)[0]
        granule=struct.unpack_from('<Q',raw,offset+6)[0]
        if granule!=2**64-1:
            if granule<last:raise ValueError('Invalid audio duration')
            last=granule
        eos=bool(raw[offset+5]&4);offset=end;sequence+=1
        if eos and offset!=len(raw):raise ValueError('Chained audio not supported')
    duration=(last-skip)/48000
    if not eos or not 0<duration<=61:raise ValueError('Voice limit is 60 seconds')
    return round(duration*1000)


def parse_fields(fields,text):
    if not fields:return {}
    if set(fields)=={LXMF.FIELD_CUSTOM_DATA}:
        edit=fields[LXMF.FIELD_CUSTOM_DATA]
        if type(edit) is not dict or set(edit)!={'fc','type','target','revision'} or type(edit['fc']) is not int or edit['fc']!=1 or edit['type']!='edit':raise ValueError('Unsupported operation')
        target=edit['target']
        if type(target) is not str or len(target)!=64 or bytes.fromhex(target).hex()!=target or type(edit['revision']) is not int or not 1<=edit['revision']<=1000000 or not text:raise ValueError('Invalid edit')
        return dict(kind='edit',target=target,revision=edit['revision'])
    if set(fields)=={LXMF.FIELD_AUDIO}:
        audio=fields[LXMF.FIELD_AUDIO]
        if type(audio) is not list or len(audio)!=2 or audio[0]!=LXMF.AM_OPUS_OGG or text:raise ValueError('Unsupported audio')
        duration=opus_duration(audio[1]);return dict(kind='audio',audio=base64.b64encode(audio[1]).decode(),duration_ms=duration)
    raise ValueError('Unsupported fields')


def fields_for(message):
    if message.get('kind')=='edit':return {LXMF.FIELD_CUSTOM_DATA:dict(fc=1,type='edit',target=message['target'],revision=message['revision'])}
    if message.get('kind')=='audio':return {LXMF.FIELD_AUDIO:[LXMF.AM_OPUS_OGG,base64.b64decode(message['audio'],validate=True)]}
    return {}
