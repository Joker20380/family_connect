"""Publisher roles received through authenticated chat registration, not announcements."""
import re


def publishers(value, chat_public):
    if type(value) is not list or len(value) > 4:
        raise ValueError('Invalid publisher configuration')
    seen = set()
    for item in value:
        if type(item) is not dict or set(item) != {'role', 'public_key'}:
            raise ValueError('Invalid publisher configuration')
        public = item['public_key']
        if (item['role'] != 'service_publisher' or type(public) is not str
                or re.fullmatch('[0-9a-f]{128}', public) is None
                or public == chat_public or public in seen):
            raise ValueError('Invalid publisher role or key')
        seen.add(public)
    return value


def validate(value, device, chat_public, now):
    if type(value) is not dict or set(value) != {'schema', 'device', 'chat_public', 'revision', 'expires_at', 'publishers'}:
        raise ValueError('Invalid publisher configuration')
    if (type(value['schema']) is not int or value['schema'] != 1
            or value['device'] != device or value['chat_public'] != chat_public
            or type(value['revision']) is not int or not 1 <= value['revision'] <= 2**53 - 1
            or type(value['expires_at']) is not int or not now < value['expires_at'] <= now + 120):
        raise ValueError('Invalid publisher binding or lease')
    publishers(value['publishers'], chat_public)
    return value
