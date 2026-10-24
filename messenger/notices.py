"""Signed LXMF fields; authority comes from a separately pinned public key."""
import re
import time

from .service_events import KINDS, PLATFORMS


def validate_notice(event):
    required = {'event_id', 'revision', 'kind', 'title', 'body', 'created', 'expires',
                'platforms', 'min_version', 'max_version'}
    if type(event) is not dict or set(event) != required:
        raise ValueError('Invalid service fields')
    if type(event['event_id']) is not str or not re.fullmatch('[a-f0-9]{32}', event['event_id']):
        raise ValueError('Invalid service ID')
    if type(event['revision']) is not int or not 1 <= event['revision'] <= 1000000:
        raise ValueError('Invalid service revision')
    if type(event['kind']) is not str or event['kind'] not in KINDS:
        raise ValueError('Invalid service kind')
    for name, limit in (('title', 160), ('body', 4000)):
        value = event[name]
        if (type(value) is not str or not value.strip() or len(value.encode()) > limit
                or any(ord(char) < 32 and char not in '\n\t' for char in value)):
            raise ValueError('Invalid service text')
    if (type(event['created']) is not int or type(event['expires']) is not int
            or not 0 < event['created'] < event['expires'] <= event['created'] + 30 * 86400):
        raise ValueError('Invalid service lifetime')
    platforms = event['platforms']
    if (type(platforms) is not list or not platforms or len(platforms) > 3
            or any(type(value) is not str or value not in PLATFORMS for value in platforms)
            or len(platforms) != len(set(platforms))):
        raise ValueError('Invalid service platforms')
    for name in ('min_version', 'max_version'):
        if type(event[name]) is not int or not 0 <= event[name] <= 2147483647:
            raise ValueError('Invalid service version')
    if event['min_version'] > event['max_version']:
        raise ValueError('Invalid service version range')
    return dict(event)


def applicable(event, platform, version, now=None):
    now = time.time() if now is None else now
    return (event['created'] <= now + 300
            and event['expires'] > now and platform in event['platforms']
            and event['min_version'] <= version <= event['max_version'])
