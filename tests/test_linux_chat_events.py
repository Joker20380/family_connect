import json
import time

import httpx
import pytest

from provisioning.chat_events import fetch_events, notification_batches, MAX_BYTES, MAX_BATCHES


def event(**changes):
    now = int(time.time())
    value = dict(id='a' * 32, kind='information', title='Public title', body='Public body', author='Operator',
                 created=now - 10, expires=now + 100, platforms=['linux'], revision=1, updated=now - 10, editor='Operator')
    return dict(value, **changes)


def test_feed_is_linux_filtered_without_permission_or_configuration_actions():
    requests = []
    def respond(request):
        requests.append(request)
        body = json.dumps({'version': 2, 'events': [event(), event(id='b' * 32, platforms=['android'])]}).encode()
        return httpx.Response(200, stream=httpx.ByteStream(body))
    result = fetch_events(lambda: httpx.Client(base_url='https://example.invalid', transport=httpx.MockTransport(respond)))
    assert [item['id'] for item in result] == ['a' * 32]
    assert requests[0].method == 'GET'
    assert requests[0].url.path == '/downloads/family-connect-events-v2.json'
    assert 'authorization' not in requests[0].headers
    assert requests[0].headers['accept-encoding'] == 'identity'


@pytest.mark.parametrize('status,body', [(302, b'{}'), (403, b'{}'), (200, b'{"version":1,"version":2,"events":[]}'),
                                      (200, b'\xff'), (200, b'x' * (MAX_BYTES + 1)),
                                      (200, json.dumps({'version': 2, 'events': [event(kind='execute')]}).encode())])
def test_feed_fail_closed_for_redirect_denial_duplicate_encoding_size_schema(status, body):
    def respond(request):
        return httpx.Response(status, stream=httpx.ByteStream(body), headers={'location': 'https://other.invalid/'})
    with pytest.raises(Exception):
        fetch_events(lambda: httpx.Client(base_url='https://example.invalid', transport=httpx.MockTransport(respond)))


def test_grouping_content_free_privacy_bounds_and_old_notice_suppression():
    messages = [dict(id=str(index), peer=format(index, '032x'), text='SECRET', read=False, notified=False)
                for index in range(25)]
    events = [dict(id='old', text='PRIVATE', read=False, notified=False, notification_suppressed=True)]
    snapshot = notification_batches(messages, events)
    assert snapshot['unread'] == 26
    assert len(snapshot['batches']) == MAX_BATCHES
    assert 'service' in snapshot['peers']
    assert 'SECRET' not in json.dumps(snapshot) and 'PRIVATE' not in json.dumps(snapshot)
    group = notification_batches([dict(item, peer='a' * 32) for item in messages], events)['batches'][0]
    assert group['unread'] == 25 and len(group['receipts']) == 25
    assert notification_batches([dict(item, read=True) for item in messages], events)['batches'] == []


def test_posted_groups_do_not_repeat_and_ack_batch_is_bounded():
    messages = [dict(id=str(index), peer='a' * 32, read=False, notified=False) for index in range(1100)]
    result = notification_batches(messages, [])
    assert result['batches'][0]['unread'] == 1100
    assert len(result['batches'][0]['receipts']) == 1000
    assert notification_batches([dict(item, notified=True) for item in messages], [])['batches'] == []


def test_unrequested_content_encoding_is_rejected_before_expansion():
    import gzip
    def respond(request):
        return httpx.Response(200, stream=httpx.ByteStream(gzip.compress(b' ' * (MAX_BYTES + 1))), headers={'content-encoding': 'gzip'})
    with pytest.raises(ValueError, match='events_unavailable'):
        fetch_events(lambda: httpx.Client(base_url='https://example.invalid', transport=httpx.MockTransport(respond)))
