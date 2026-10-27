"""Closed operator configuration, delivered only to its authenticated device."""
import json
import stat

from provisioning.chat_publishers import validate


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate publisher field')
        result[key] = value
    return result


def configured(path, device, chat_public, expires, now):
    try:
        info = path.lstat()
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= 8192:
        raise ValueError('Unsafe publisher configuration')
    document = json.loads(path.read_bytes(), object_pairs_hook=unique)
    if (type(document) is not dict or set(document) != {'schema', 'devices'}
            or type(document['schema']) is not int or document['schema'] != 1
            or type(document['devices']) is not dict):
        raise ValueError('Invalid publisher configuration')
    entry = document['devices'].get(device)
    if entry is None:
        return None
    if type(entry) is not dict or set(entry) != {'revision', 'publishers'}:
        raise ValueError('Invalid publisher configuration')
    return validate(dict(schema=1, device=device, chat_public=chat_public,
                         expires_at=expires, **entry), device, chat_public, now)
