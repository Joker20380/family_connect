import json
import time
import uuid

import httpx
import pytest

from messenger.local import LocalError
from messenger.tests.announcement_server import AnnouncementServer
from messenger.tests.test_linux_owner import MemoryKeyring
from provisioning.chat_admin import AnnouncementClient, validate_notice
from provisioning.chat_owner import ChatOwner
from provisioning.chat_rpc import invoke
from provisioning.friends import FriendsError
from provisioning.friends_owner import FriendsOwner


def notice(**changes):
    return dict(dict(id=uuid.uuid4().hex, kind='information', title='Public announcement', body='Synthetic service text',
                     platforms=['android', 'windows', 'linux'], days=30), **changes)


@pytest.fixture
def setup(tmp_path, chat_runtime):
    server = AnnouncementServer(tmp_path / 'server')
    friends = FriendsOwner(tmp_path / 'identity', tmp_path / 'anchor', http_factory=server.http)
    friends.activate(server.access.invite())
    owner = ChatOwner(tmp_path / 'chat', friends, keyring=MemoryKeyring(), runtime_factory=lambda _: chat_runtime)
    owner.open(create=True)
    try:
        yield owner, server
    finally:
        owner.close()
        server.close()


def grant(owner, server):
    server.store.grant_device(server.access, owner.device.reference, 'Synthetic operator')


def test_member_denial_does_not_create_roles_or_mutate_history(setup):
    owner, server = setup
    profile = owner.invoke('profile')
    for operation, arguments in [('announcements_list', dict(offset=0)), ('announcements_publish', dict(notice=notice()))]:
        with pytest.raises(LocalError, match='^notice_denied$'):
            owner.invoke(operation, **arguments)
    assert server.store.device_role(owner.device.reference)['role'] == 'member'
    assert server.store.feed()['events'] == []
    assert owner.invoke('profile') == profile


def test_actual_proofs_publication_idempotency_edit_revision_and_revocation(setup):
    owner, server = setup
    grant(owner, server)
    value = notice()
    assert owner.invoke('announcements_list', offset=0) == dict(events=[], next_offset=None)
    expected = dict(id=value['id'], status='published')
    assert owner.invoke('announcements_publish', notice=value) == expected
    assert owner.invoke('announcements_publish', notice=value) == expected
    page = owner.invoke('announcements_list', offset=0)
    assert len(page['events']) == 1 and page['events'][0]['revision'] == 1
    edit = dict(id=value['id'], revision=1, request_id=uuid.uuid4().hex, title='Corrected', body='New public text')
    assert owner.invoke('announcements_edit', notice=edit) == dict(id=value['id'], revision=2, status='updated')
    assert owner.invoke('announcements_edit', notice=edit)['revision'] == 2
    with pytest.raises(LocalError, match='notice_conflict'):
        owner.invoke('announcements_edit', notice=dict(edit, request_id=uuid.uuid4().hex))
    assert server.store.feed()['events'][0]['title'] == value['title']
    assert owner.invoke('announcements_list', offset=0)['events'][0]['title'] == 'Corrected'
    server.after_challenge = lambda: server.store.revoke_device(owner.device.reference)
    with pytest.raises(LocalError, match='notice_denied'):
        owner.invoke('announcements_edit', notice=dict(edit, revision=2, request_id=uuid.uuid4().hex))
    assert server.store.current_event(value['id'])['revision'] == 2


def test_ambiguous_server_reply_keeps_operation_identity_for_explicit_retry(setup):
    owner, server = setup
    grant(owner, server)
    value = notice()
    server.lose_reply = True
    with pytest.raises(LocalError, match='notice_unavailable'):
        owner.invoke('announcements_publish', notice=value)
    assert len(server.store.feed()['events']) == 1
    assert owner.invoke('announcements_publish', notice=value)['id'] == value['id']
    assert len(server.store.feed()['events']) == 1
    request = dict(id=uuid.uuid4().hex, created=int(time.time()), operation='announcements_edit',
                   arguments=dict(notice=dict(id=value['id'], revision=1, request_id=uuid.uuid4().hex, title='Edited', body='Preserved retry')))
    result = invoke(owner, request)
    calls = len(server.requests)
    assert invoke(owner, request) == result and len(server.requests) == calls
    assert server.store.db.execute('SELECT COUNT(*) FROM edit_operations').fetchone()[0] == 1


def test_listing_keeps_archived_announcements_and_bounded_pages(setup):
    owner, server = setup
    grant(owner, server)
    now = int(time.time())
    for index in range(51):
        server.store.publish('', device=owner.device.reference, ident=format(index, '032x'), kind='information',
            title='Archived ' + str(index), body='Past event', platforms=['linux'], now=now-10000+index, lifetime=100)
    page = owner.invoke('announcements_list', offset=0)
    assert len(page['events']) == 50 and page['next_offset'] == 50
    assert all(event['expires'] < now for event in page['events'])
    older = owner.invoke('announcements_list', offset=50)
    assert len(older['events']) == 1 and older['next_offset'] is None


@pytest.mark.parametrize('changes', [dict(title=''), dict(body='\x00'), dict(title='😀' * 81), dict(body='x' * 4001),
    dict(platforms=['linux']), dict(days=True), dict(days=31), dict(id='../request'), dict(extra='field')])
def test_invalid_publication_is_rejected_before_device_proof(setup, changes):
    owner, server = setup
    before = len(server.requests)
    with pytest.raises(LocalError, match='invalid_input'):
        owner.invoke('announcements_publish', notice=notice(**changes))
    assert len(server.requests) == before


@pytest.mark.parametrize('value', [dict(id='a'*32, revision=True, request_id='b'*32, title='Title', body='Body'),
    dict(id='a'*32, revision=1, request_id='b'*32, title='Title', body='Body', platforms=['android'])])
def test_edit_cannot_change_audience_or_use_boolean_revision(value):
    with pytest.raises(FriendsError, match='invalid_input'):
        validate_notice(value, edit=True)


@pytest.mark.parametrize('status,raw', [(302, b'{}'), (200, b'{"events":[],"events":[],"next_offset":null}'),
    (200, b'x' * 1048577), (200, b'{"events":[],"next_offset":50}'),
    (200, b'{"events":[],"next_offset":false}')])
def test_listing_response_fails_closed_without_leaking_raw_body(setup, status, raw):
    owner, server = setup
    def route(request):
        if request.url.path == '/friends/challenge':
            return server.route(request)
        return httpx.Response(status, stream=httpx.ByteStream(raw), headers={'location': 'https://other.invalid/'})
    with httpx.Client(base_url='https://announcement.test.invalid', transport=httpx.MockTransport(route)) as http:
        with pytest.raises(FriendsError, match='^(invalid_response|service_unavailable)$'):
            AnnouncementClient(http, owner.device).list(0)


@pytest.mark.parametrize('path', ['/friends/challenge', '/friends/notices/device/list'])
@pytest.mark.parametrize('encoding', ['gzip', 'br', 'deflate', 'identity, gzip'])
def test_encoded_notice_response_rejected_before_reading_or_decompressing(setup, path, encoding):
    owner, server = setup
    consumed = []

    class UnreadBody(httpx.SyncByteStream):
        def __iter__(self):
            consumed.append(True)
            yield b'untrusted encoded body'

    def route(request):
        assert request.headers['Accept-Encoding'] == 'identity'
        if request.url.path == path:
            return httpx.Response(200, stream=UnreadBody(), headers={'Content-Encoding': encoding})
        return server.route(request)

    with httpx.Client(base_url='https://announcement.test.invalid', transport=httpx.MockTransport(route)) as http:
        with pytest.raises(FriendsError, match='^invalid_response$'):
            AnnouncementClient(http, owner.device).list(0)
    assert not consumed


def test_notice_request_requires_uncompressed_response_without_changing_proof(setup):
    owner, server = setup
    grant(owner, server)
    paths = []

    def route(request):
        assert request.headers['Accept-Encoding'] == 'identity'
        paths.append(request.url.path)
        return server.route(request)

    with httpx.Client(base_url='https://announcement.test.invalid', transport=httpx.MockTransport(route)) as http:
        assert AnnouncementClient(http, owner.device).list(0) == dict(events=[], next_offset=None)
    assert paths == ['/friends/challenge', '/friends/notices/device/list']


def test_announcement_challenge_keeps_android_16k_response_bound(setup):
    owner, server = setup

    def route(request):
        assert request.url.path == '/friends/challenge'
        response = server.route(request)
        return httpx.Response(200, stream=httpx.ByteStream(response.content + b' ' * 16384))

    with httpx.Client(base_url='https://announcement.test.invalid', transport=httpx.MockTransport(route)) as http:
        with pytest.raises(FriendsError, match='^invalid_response$'):
            AnnouncementClient(http, owner.device).list(0)
