"""Authenticated enrollment's support role, never an announcement or contact name."""
import re
import time

def validate(value, device, chat_public, now=None):
    now = time.time() if now is None else now
    fields = {'schema', 'device', 'chat_public', 'sender_public', 'revision', 'expires_at', 'enabled'}
    if (type(value) is not dict or set(value) != fields or type(value['schema']) is not int
            or type(device) is not str or re.fullmatch('[0-9a-f]{32}', device) is None
            or type(chat_public) is not str or re.fullmatch('[0-9a-f]{128}', chat_public) is None
            or value['schema'] != 1 or value['device'] != device or value['chat_public'] != chat_public
            or type(value['enabled']) is not bool or type(value['revision']) is not int
            or not 1 <= value['revision'] <= 2**53 - 1 or type(value['expires_at']) is not int
            or not now < value['expires_at'] <= now + 120
            or type(value['sender_public']) is not str
            or re.fullmatch('[0-9a-f]{128}', value['sender_public']) is None
            or value['sender_public'] == chat_public):
        raise ValueError('Invalid support binding')
    return dict(value)


def accept(store, value, device, chat_public):
    value = validate(value, device, chat_public)
    with store._lock, store._db:
        previous = store._get('support-role')
        if previous is not None:
            if (any(previous[key] != value[key] for key in ('device', 'chat_public', 'sender_public'))
                    or value['revision'] < previous['revision']
                    or (not previous['enabled'] and value['enabled'])
                    or (value['revision'] == previous['revision'] and value['enabled'] != previous['enabled'])
                    or value['expires_at'] < previous['expires_at']):
                raise ValueError('Support binding changed or revoked')
        store._put('support-role', value)


def role(store):
    with store._lock:
        return store._get('support-role')


def active(value):
    return value is not None and value['enabled'] and time.time() < value['expires_at']


def contacts(store, ordinary):
    from . import codec
    result = dict(ordinary)
    value = role(store)
    if value is not None:
        address = codec.address(bytes.fromhex(value['sender_public'])).hex()
        result.pop(address, None)
        if active(value):
            result[address] = value['sender_public']
    return result
