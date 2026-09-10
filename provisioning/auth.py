"""Purpose-separated proof for one authenticated provisioning fetch."""
import json

import RNS

from device_identity.device import _b64, _decode

AUDIENCE = 'family-connect/provisioning-fetch/v1'
DOMAIN = b'family-connect/provisioning-fetch/v1\x00'


def _binding(public_identity, wireguard_public_key, challenge):
    _decode(public_identity, 64)
    _decode(wireguard_public_key, 32)
    _decode(challenge, 32)
    return dict(schema_version=1, audience=AUDIENCE, public_identity=public_identity,
                wireguard_public_key=wireguard_public_key, challenge=challenge)


def _message(binding):
    return DOMAIN + json.dumps(binding, sort_keys=True, separators=(',', ':')).encode()


def prove(device, challenge):
    binding = _binding(device.public_identity, device.wireguard_public_key, challenge)
    return {**binding, 'signature': _b64(device._identity.sign(_message(binding)))}


def verify(proof):
    fields = {'schema_version', 'audience', 'public_identity', 'wireguard_public_key',
              'challenge', 'signature'}
    if (type(proof) is not dict or set(proof) != fields or
            type(proof['schema_version']) is not int or proof['schema_version'] != 1 or
            proof['audience'] != AUDIENCE):
        raise ValueError('invalid fetch proof')
    binding = _binding(proof['public_identity'], proof['wireguard_public_key'], proof['challenge'])
    identity = RNS.Identity(create_keys=False)
    identity.load_public_key(_decode(proof['public_identity'], 64))
    if not identity.validate(_decode(proof['signature'], 64), _message(binding)):
        raise ValueError('invalid fetch proof')
    return identity.hash.hex()
