"""Bounded public service feed and content-free desktop notification selection."""
import json
import time

from messenger.service_events import validate_feed
from .friends import FriendsClient


EVENTS_PATH = '/downloads/family-connect-events-v2.json'
MAX_BYTES = 1000000
MAX_BATCHES = 8


def fetch_events(http_factory):
    deadline = time.monotonic() + 16
    with http_factory() as http, http.stream('GET', EVENTS_PATH, timeout=8, follow_redirects=False,
                                           headers={'Accept-Encoding': 'identity'}) as response:
        if response.status_code != 200 or response.headers.get('content-encoding', 'identity').lower() != 'identity':
            raise ValueError('events_unavailable')
        data = bytearray()
        for chunk in response.iter_raw(8192):
            if len(data) + len(chunk) > MAX_BYTES or time.monotonic() > deadline:
                raise ValueError('events_unavailable')
            data.extend(chunk)
        return validate_feed(json.loads(data.decode('utf-8'), object_pairs_hook=FriendsClient._object), platform='linux')


def notification_batches(inbox, events):
    groups = {}
    for service, messages in ((False, inbox), (True, events)):
        for message in messages:
            if message['read']:
                continue
            peer = 'service' if service else message['peer']
            group = groups.setdefault(peer, {'peer': peer, 'unread': 0, 'fresh': False, 'receipts': []})
            group['unread'] += 1
            fresh = not message['notified'] and not message.get('notification_suppressed', False)
            group['fresh'] |= fresh
            if fresh and len(group['receipts']) < 1000:
                group['receipts'].append({'id': message['id'], 'revision': message.get('revision', 1 if service else 0)})
    return {'unread': sum(group['unread'] for group in groups.values()),
            'peers': list(groups), 'batches': [group for group in groups.values() if group['fresh']][:MAX_BATCHES]}
