"""Public service notices, separate from end-to-end encrypted personal messages.

Only the service operator's authenticated HTTPS origin supplies this feed. No event
may change VPN configuration, execute a command or install an update.
"""
import json
import re
import time

KINDS = {'update', 'maintenance', 'server_change', 'information'}
PLATFORMS = {'android', 'windows', 'linux'}


def validate_feed(feed, *, platform=None, now=None):
    now = int(time.time()) if now is None else now
    if type(feed) is not dict or set(feed) != {'version', 'events'} or type(feed['version']) is not int or feed['version'] not in (1,2):
        raise ValueError('Invalid feed')
    if len(json.dumps(feed,ensure_ascii=False).encode('utf-8')) > 1000000: raise ValueError('Feed too large')
    events = feed['events']
    if type(events) is not list or len(events) > 200:
        raise ValueError('Invalid events')
    result, seen = [], set()
    for event in events:
        if type(event) is not dict or set(event) != ({'id', 'kind', 'title', 'body', 'author', 'created', 'expires', 'platforms'} | ({'revision','updated','editor'} if feed['version']==2 else set())):
            raise ValueError('Invalid event')
        if feed['version']==2:
            if type(event['revision']) is not int or not 1<=event['revision']<=1000000 or type(event['updated']) is not int or type(event['created']) is not int or not event['created']<=event['updated']<=now+300:
                raise ValueError('Invalid revision')
            if type(event['editor']) is not str or not event['editor'].strip() or len(event['editor'])>80: raise ValueError('Invalid editor')
        ident = event['id']
        if type(ident) is not str or re.fullmatch('[a-f0-9]{32}', ident) is None or ident in seen:
            raise ValueError('Invalid event id')
        seen.add(ident)
        if type(event['kind']) is not str or event['kind'] not in KINDS:
            raise ValueError('Invalid kind')
        for field, limit in [('title', 160), ('body', 4000), ('author', 80)]:
            text = event[field]
            if type(text) is not str or not text.strip() or len(text) > limit or any(ord(c) < 32 and c not in '\n\t' for c in text):
                raise ValueError('Invalid text')
        if type(event['created']) is not int or type(event['expires']) is not int or not 0 < event['created'] < event['expires'] or event['created'] > now + 300:
            raise ValueError('Invalid time')
        targets = event['platforms']
        if type(targets) is not list or not targets or any(type(p) is not str for p in targets) or len(targets) != len(set(targets)) or any(p not in PLATFORMS for p in targets):
            raise ValueError('Invalid platforms')
        if event['expires'] > now and (platform is None or platform in targets):
            result.append(dict(event))
    return result
