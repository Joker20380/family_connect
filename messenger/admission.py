"""Domain-separated proof linking a chat key to an invited device challenge."""
import base64

DOMAIN = b'family-connect/chat-admission/v1\x00'


def message(public_hex, device, challenge):
    if type(public_hex) is not str or len(public_hex) != 128:
        raise ValueError('Invalid chat key')
    public = bytes.fromhex(public_hex)
    if public.hex() != public_hex or len(public) != 64:
        raise ValueError('Invalid chat key')
    if type(device) is not str or len(device) != 32:
        raise ValueError('Invalid device')
    reference = bytes.fromhex(device)
    if reference.hex() != device or len(reference) != 16:
        raise ValueError('Invalid device')
    if type(challenge) is not str or len(challenge) != 44:
        raise ValueError('Invalid challenge')
    nonce = base64.b64decode(challenge, validate=True)
    if len(nonce) != 32 or base64.b64encode(nonce).decode() != challenge:
        raise ValueError('Invalid challenge')
    return DOMAIN + reference + public + nonce
