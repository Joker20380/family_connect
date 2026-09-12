"""Non-secret, device-signed ACKs. Receipt IDs make retries byte-identical."""
import base64
import hashlib
import json

import RNS

from .envelope import _unique_fields, ProvisioningRejected

DOMAIN = b'family-connect/control-ack/v1\x00'
STATUSES = {'RECEIVED', 'REJECTED', 'APPLIED', 'COMMITTED', 'ROLLED_BACK', 'FAILED'}
ERRORS = {'NONE', 'SIZE', 'CLOCK', 'SIGNATURE', 'MALFORMED', 'SCHEMA', 'TARGET', 'SIGNER',
    'STRUCTURE', 'LEASE', 'CLIENT_VERSION', 'UNSUPPORTED_TRANSPORT_VERSION', 'REPLAY',
    'PREVIOUS_HASH', 'APPLY', 'HEALTH', 'RECOVERY', 'ROLLBACK'}
MAX_ACK_BYTES = 4096


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def create(device, *, digest, config_id, sequence, status, error, now):
    body = dict(schema_version=1, device=device.reference, public_identity=device.public_identity,
        envelope_hash=digest, config_id=config_id, sequence=sequence, status=status,
        error=error, timestamp=now)
    body['ack_id'] = hashlib.sha256(encode(body)).hexdigest()
    return encode(dict(body=body, signature=base64.b64encode(device._identity.sign(DOMAIN + encode(body))).decode()))


def verify(raw):
    import re
    try:
        if type(raw) is not bytes or len(raw) > MAX_ACK_BYTES:
            raise ValueError()
        outer = json.loads(raw, object_pairs_hook=_unique_fields)
        if type(outer) is not dict or set(outer) != {'body', 'signature'}:
            raise ValueError()
        body = outer['body']
        if type(body) is not dict or set(body) != {'schema_version', 'device', 'public_identity',
                'envelope_hash', 'config_id', 'sequence', 'status', 'error', 'timestamp', 'ack_id'}:
            raise ValueError()
        if (type(body['schema_version']) is not int or body['schema_version'] != 1 or
                body['status'] not in STATUSES or body['error'] not in ERRORS or
                type(body['timestamp']) is not int or body['timestamp'] < 0 or
                type(body['sequence']) is not int or not 0 <= body['sequence'] < 2**63 or
                not re.fullmatch('[0-9a-f]{64}', body['envelope_hash']) or
                (body['config_id'] is not None and not re.fullmatch('[a-zA-Z0-9_-]{1,64}', body['config_id']))):
            raise ValueError()
        identity = RNS.Identity(create_keys=False)
        key = base64.b64decode(body['public_identity'], validate=True)
        if len(key) != 64 or base64.b64encode(key).decode() != body['public_identity']:
            raise ValueError()
        identity.load_public_key(key)
        if identity.hash.hex() != body['device'] or not identity.validate(
                base64.b64decode(outer['signature'], validate=True), DOMAIN + encode(body)):
            raise ValueError()
        if body['ack_id'] != hashlib.sha256(encode({k:v for k,v in body.items() if k != 'ack_id'})).hexdigest():
            raise ValueError()
        return body
    except (ValueError, TypeError, KeyError, UnicodeError, RecursionError):
        raise ProvisioningRejected('invalid control ACK') from None
