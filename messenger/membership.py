"""Expiring operator snapshots. No device credentials or public membership API."""
import json
import time
from pathlib import Path


def validate(value, now=None):
    now = time.time() if now is None else now
    if type(value) is not dict or set(value) != {'sequence','expires_at','public_keys'}:
        raise ValueError('Invalid membership snapshot')
    if type(value['sequence']) is not int or not 1 <= value['sequence'] < 2**63:
        raise ValueError('Invalid membership sequence')
    if type(value['expires_at']) is not int or not now < value['expires_at'] <= now+120:
        raise ValueError('Expired membership')
    keys = value['public_keys']
    if type(keys) is not list or len(keys) > 550: raise ValueError('Membership quota exceeded')
    if any(type(k) is not str or len(k)!=128 or bytes.fromhex(k).hex()!=k for k in keys):
        raise ValueError('Invalid membership keys')
    if len(set(keys)) != len(keys): raise ValueError('Duplicate member')
    return value


class Membership:
    def __init__(self, path, read, clock=time.time):
        self.path, self.read, self.clock = Path(path), read, clock

    def keys(self):
        try:
            value = validate(json.loads(self.read(self.path, 131072)), self.clock())
            return [bytes.fromhex(key) for key in value['public_keys']]
        except (OSError, ValueError, TypeError):
            return []  # Missing/corrupt/expired snapshot never grants dynamic access.
