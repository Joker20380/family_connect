import json
import time
import uuid

import pytest

from messenger.local import LocalError
from messenger.tests.test_linux_owner import owner_factory
from provisioning.chat_rpc import parse_request, encode_response, invoke, MAX_REQUEST, MAX_RESPONSE, MAX_TICKETS


def request(operation, **arguments):
    return dict(id=uuid.uuid4().hex, created=int(time.time()), operation=operation, arguments=arguments)


@pytest.mark.parametrize('raw', ['{}', '[]', '{"id":1,"id":2}', 'x' * (MAX_REQUEST + 1),
                               json.dumps(request('exec', command='not-allowed'))])
def test_strict_rpc_request_rejects_unknown_fields_and_commands(raw):
    with pytest.raises(LocalError, match='invalid_input'):
        parse_request(raw)


def test_request_freshness_and_bounded_sanitized_response():
    value = request('profile')
    assert parse_request(json.dumps(value)) == value
    with pytest.raises(LocalError, match='request_expired'):
        parse_request(json.dumps(value), now=value['created'] + 121)
    value['created'] = True
    with pytest.raises(LocalError, match='invalid_input'):
        parse_request(json.dumps(value))
    assert json.loads(encode_response(error='PRIVATE-error-text'))['error'] == 'store_unavailable'
    assert json.loads(encode_response('x' * (MAX_RESPONSE + 1)))['error'] == 'response_too_large'


@pytest.mark.parametrize('corrupt', [[], False, '', 0])
def test_invalid_replay_fence_is_not_treated_as_empty(owner_factory, corrupt):
    owner = owner_factory()
    owner.open(create=True)
    with owner.local._store._db:
        owner.local._store._put('desktop-rpc-v1', corrupt)
    with pytest.raises(LocalError, match='store_unavailable'):
        invoke(owner, request('background_delivery', enabled=False))
    assert owner.invoke('delivery_settings')['background'] is True


def test_encrypted_rpc_replay_survives_restart_without_duplicate_message(owner_factory):
    alice, bob = owner_factory('rpc-alice'), owner_factory('rpc-bob')
    first, second = alice.open(create=True), bob.open(create=True)
    alice.invoke('trust_contact', public=second['public'], fingerprint=second['fingerprint'])
    value = request('queue', address=second['address'], text='PRIVATE-replayed-payload')
    message = invoke(alice, value)
    assert invoke(alice, value) == message
    alice.close()
    assert alice.open() == first
    assert invoke(alice, value) == message
    assert alice.invoke('history', address=second['address'], offset=0, limit=50)['total'] == 1
    for path in alice.directory.rglob('*'):
        if path.is_file():
            assert b'PRIVATE-replayed-payload' not in path.read_bytes()
    value['arguments']['text'] = 'Different payload under same request ID'
    with pytest.raises(LocalError, match='invalid_input'):
        invoke(alice, value)


def test_pending_crash_fence_never_reexecutes_and_live_tickets_are_not_evicted(owner_factory, monkeypatch):
    owner = owner_factory()
    owner.open(create=True)
    value = request('background_delivery', enabled=False)
    original = owner.invoke
    def failed(*args, **kwargs):
        raise RuntimeError('simulate abrupt loss after durable intent')
    owner.invoke = failed
    with pytest.raises(RuntimeError):
        invoke(owner, value)
    owner.invoke = original
    owner.close()
    owner.open()
    with pytest.raises(LocalError, match='operation_outcome_unknown'):
        invoke(owner, value)
    assert owner.invoke('delivery_settings')['background']
    for index in range(MAX_TICKETS - 1):
        invoke(owner, request('background_delivery', enabled=True))
    with pytest.raises(LocalError, match='busy'):
        invoke(owner, request('background_delivery', enabled=False))
    now = time.time()
    monkeypatch.setattr('provisioning.chat_rpc.time.time', lambda: now + 125)
    invoke(owner, request('background_delivery', enabled=False))
    assert owner.invoke('delivery_settings')['background'] is False


def test_compact_reads_and_paged_notices_do_not_truncate_content(owner_factory):
    owner = owner_factory()
    owner.open(create=True)
    now = int(time.time())
    events = [dict(id=format(index, '032x'), kind='information', title='Заголовок', body='Ж' * 4000,
                   author='Operator', created=now - 1, expires=now + 100, platforms=['linux']) for index in range(55)]
    owner.local._store.service_events(events)
    first = invoke(owner, request('service_events_page', offset=0, limit=50))
    second = invoke(owner, request('service_events_page', offset=first['next_offset'], limit=50))
    assert first['total'] == 55 and len(first['events']) == 50 and len(second['events']) == 5
    assert second['next_offset'] is None
    assert first['events'][0]['id'] == format(54, '032x')
    assert all(len(item['body']) == 4000 for item in first['events'] + second['events'])
    assert len(encode_response(first).encode()) < MAX_RESPONSE
    assert invoke(owner, request('event_counts')) == dict(total=55, unread=55)
    with pytest.raises(LocalError):
        invoke(owner, request('service_events_page', offset=0, limit=51))
