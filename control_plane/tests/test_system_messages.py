import http.client
import io
import json
import time
import urllib.error
import uuid

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core import signing
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import transaction
from django.test import Client
from django.urls import reverse
import pytest

from apps.console.models import AuditRecord, SystemMessage
from apps.console.system_messages import payload
from apps.console.system_publisher import PublicationRefused, PublicationUnknown, Publisher, publish_next


def compose(client, **changes):
    token = client.get(reverse('console:system_message_new')).context['token']
    values = dict(token=token, title='Синтетическое объявление', body='Тестовый текст — не production',
                  kind='information', platforms=['android'], days=30)
    values.update(changes)
    return values


def draft(client):
    values = compose(client)
    response = client.post(reverse('console:system_message_preview'), values)
    assert response.status_code == 302
    return SystemMessage.objects.get(pk=signing.loads(values['token'], salt='system-draft')['id'])


def queue(client, message):
    token = client.get(reverse('console:system_message', args=[message.pk])).context['token']
    return client.post(reverse('console:system_message_send', args=[message.pk]), dict(token=token, confirm='public'))


class RecordingPublisher:
    def __init__(self, failure=None):
        self.values = []
        self.failure = failure

    def publish(self, value):
        self.values.append(value)
        if self.failure:
            raise self.failure


@pytest.fixture
def operator(console):
    client = Client()
    client.force_login(console)
    return client


def test_preview_is_not_publication_and_confirmation_is_csrf_protected(console):
    client = Client(enforce_csrf_checks=True)
    client.force_login(console)
    values = compose(client, body='<script>alert("synthetic")</script>')
    preview_url = reverse('console:system_message_preview')
    assert client.get(preview_url).status_code == 405
    assert client.post(preview_url, values).status_code == 403
    values['csrfmiddlewaretoken'] = client.cookies['csrftoken'].value
    for _ in range(2):
        assert client.post(preview_url, values).status_code == 302
    message = SystemMessage.objects.get()
    assert message.status == 'draft'
    publisher = RecordingPublisher()
    assert publish_next(publisher) is None
    response = client.get(reverse('console:system_message', args=[message.pk]))
    assert response['Cache-Control'] == 'no-store'
    assert '&lt;script&gt;' in response.content.decode()
    send_url = reverse('console:system_message_send', args=[message.pk])
    assert client.get(send_url).status_code == 405
    send = dict(token=response.context['token'], confirm='public')
    assert client.post(send_url, send).status_code == 403
    send['csrfmiddlewaretoken'] = values['csrfmiddlewaretoken']
    assert client.post(send_url, dict(send, confirm='')).status_code == 400
    for _ in range(2):
        assert client.post(send_url, send).status_code == 302
    assert publish_next(publisher) == 'published'
    assert publish_next(publisher) is None
    assert len(publisher.values) == 1
    audit = list(AuditRecord.objects.filter(action__startswith='system.').values('action', 'details'))
    assert [item['action'] for item in reversed(audit)] == ['system.preview', 'system.queued', 'system.published']
    assert 'synthetic' not in json.dumps(audit)


def test_same_id_cannot_change_text_or_switch_actor(operator, console):
    values = compose(operator)
    preview_url = reverse('console:system_message_preview')
    assert operator.post(preview_url, values).status_code == 302
    assert operator.post(preview_url, dict(values, body='changed')).status_code == 400
    message = SystemMessage.objects.get()
    token = operator.get(reverse('console:system_message', args=[message.pk])).context['token']
    other = get_user_model().objects.create_superuser(username='another-operator')
    operator.force_login(other)
    assert operator.post(preview_url, values).status_code == 400
    assert operator.post(reverse('console:system_message_send', args=[message.pk]), dict(token=token, confirm='public')).status_code == 400
    assert queue(operator, message).status_code == 400
    message.refresh_from_db()
    assert message.status == 'draft'


def test_reader_cannot_compose_or_send_and_inactive_operator_is_rechecked(operator, console):
    message = draft(operator)
    assert queue(operator, message).status_code == 302
    reader = get_user_model().objects.create_user(username='reader', is_staff=True)
    reader.user_permissions.add(Permission.objects.get(codename='view_system_messages'))
    operator.force_login(reader)
    assert operator.get(reverse('console:system_messages')).status_code == 200
    response = operator.get(reverse('console:system_message', args=[message.pk]))
    assert response.status_code == 200 and 'name="confirm"' not in response.content.decode()
    assert operator.get(reverse('console:system_message_new')).status_code == 403
    assert operator.post(reverse('console:system_message_preview'), {}).status_code == 403
    assert operator.post(reverse('console:system_message_send', args=[message.pk]), {}).status_code == 403
    console.is_active = False
    console.save()
    publisher = RecordingPublisher()
    assert publish_next(publisher) == 'refused' and not publisher.values


@pytest.mark.parametrize('changes', [dict(title=''), dict(body=' '), dict(title='😀' * 81),
    dict(body='x' * 4001), dict(body='bad\x01'), dict(platforms=[]), dict(platforms=['ios']),
    dict(kind='execute'), dict(days=0), dict(days=366), dict(platforms=['android', 'android'])])
def test_invalid_content_never_queues(operator, changes):
    response = operator.post(reverse('console:system_message_preview'), compose(operator, **changes))
    assert response.status_code == 400
    assert not SystemMessage.objects.exists()


def test_forged_and_expired_form_tokens(operator, monkeypatch):
    values = compose(operator)
    url = reverse('console:system_message_preview')
    assert operator.post(url, dict(values, token=values['token']+'tampered')).status_code == 400
    monkeypatch.setattr(signing.TimestampSigner, 'timestamp', lambda self: signing.b62_encode(1))
    expired = signing.dumps(dict(id=uuid.uuid4().hex, actor=1), salt='system-draft')
    assert operator.post(url, dict(values, token=expired)).status_code == 400
    assert not SystemMessage.objects.exists()


def test_unknown_result_requires_explicit_same_id_retry(operator):
    message = draft(operator)
    queue(operator, message)
    publisher = RecordingPublisher(PublicationUnknown())
    assert publish_next(publisher) == 'unknown'
    assert publish_next(publisher) is None
    assert queue(operator, message).status_code == 302
    publisher.failure = None
    assert publish_next(publisher) == 'published'
    assert publisher.values[0] == publisher.values[1]
    assert queue(operator, message).status_code == 302
    assert publish_next(publisher) is None


def test_process_crash_rolls_back_queue_without_changing_id(operator):
    message = draft(operator)
    queue(operator, message)
    publisher = RecordingPublisher(RuntimeError('synthetic process death'))
    with pytest.raises(RuntimeError), transaction.atomic():
        publish_next(publisher)
    message.refresh_from_db()
    assert message.status == 'queued'
    publisher.failure = None
    assert publish_next(publisher) == 'published'
    assert publisher.values[0] == publisher.values[1]


@pytest.fixture
def publisher(tmp_path):
    token = tmp_path / 'publisher.token'
    token.write_text('a' * 64)
    token.chmod(0o600)
    return Publisher('https://notices.test.invalid', token)


class Reply(io.BytesIO):
    def __init__(self, value):
        super().__init__(value if isinstance(value, bytes) else json.dumps(value).encode())
        self.status = 200
        self.headers = {}


class Responses:
    def __init__(self, *responses):
        self.responses = iter(responses)
        self.requests = []

    def open(self, request, timeout):
        assert timeout == 10
        self.requests.append(request)
        response = next(self.responses)
        if isinstance(response, Exception):
            raise response
        return Reply(response)


def test_https_receipt_and_exact_public_readback(publisher, operator):
    value = payload(draft(operator))
    now = int(time.time())
    event = dict(value, created=now, expires=now+30*86400)
    publisher.opener = Responses(dict(id=value['id'], status='published'), dict(version=2, events=[event]))
    publisher.publish(value)
    requests = publisher.opener.requests
    assert requests[0].get_header('Authorization') == 'Bearer ' + 'a'*64
    assert requests[1].get_header('Authorization') is None
    assert requests[0].full_url == 'https://notices.test.invalid/friends/notices/publish'
    assert requests[1].full_url == 'https://notices.test.invalid/downloads/family-connect-events-v2.json'


@pytest.mark.parametrize('raw', [b'not-json', b'{"id":1,"id":2}', b'x'*1000001, [], {}])
def test_bad_response_is_unknown_not_success(publisher, raw):
    publisher.opener = Responses(raw)
    with pytest.raises(PublicationUnknown):
        publisher.publish(dict(id='b'*32))


@pytest.mark.parametrize('code,expected', [(403, PublicationRefused), (400, PublicationRefused),
    (500, PublicationUnknown), (302, PublicationUnknown), (429, PublicationUnknown)])
def test_http_failure_is_sanitized(publisher, code, expected):
    publisher.opener = Responses(urllib.error.HTTPError(publisher.origin, code, 'private upstream text', {}, None))
    with pytest.raises(expected) as error:
        publisher.publish(dict(id='b'*32))
    assert 'private' not in str(error.value)


def test_missing_or_mismatched_feed_is_not_delivered(publisher, operator):
    value = payload(draft(operator))
    publisher.opener = Responses(dict(id=value['id'], status='published'), dict(version=2, events=[]))
    with pytest.raises(PublicationUnknown):
        publisher.publish(value)


@pytest.mark.parametrize('change', ['body', 'expired', 'duplicate', 'created'])
def test_feed_readback_must_match_live_original(publisher, operator, change):
    value = payload(draft(operator))
    now = int(time.time())
    event = dict(value, created=now, expires=now+30*86400)
    if change == 'body':
        event['body'] = 'another message'
    elif change == 'expired':
        event.update(created=now-31*86400, expires=now-86400)
    elif change == 'created':
        event['created'] = True
    events = [event, event] if change == 'duplicate' else [event]
    publisher.opener = Responses(dict(id=value['id'], status='published'), dict(version=2, events=events))
    with pytest.raises(PublicationUnknown):
        publisher.publish(value)


def test_signed_preview_binds_the_immutable_payload(operator):
    message = draft(operator)
    token = operator.get(reverse('console:system_message', args=[message.pk])).context['token']
    SystemMessage.objects.filter(pk=message.pk).update(body='changed outside the form')
    response = operator.post(reverse('console:system_message_send', args=[message.pk]), dict(token=token, confirm='public'))
    assert response.status_code == 400
    message.refresh_from_db()
    assert message.status == 'draft'


def test_readback_timeout_and_no_redirect(publisher):
    from apps.console.system_publisher import NoRedirect
    assert NoRedirect().redirect_request(None, None, 302, '', {}, 'https://other.invalid') is None
    publisher.opener = Responses(TimeoutError('private details'))
    with pytest.raises(PublicationUnknown):
        publisher.publish(dict(id='b'*32))


def test_truncated_http_reply_is_unknown_and_not_an_automatic_retry(publisher):
    publisher.opener = Responses(http.client.IncompleteRead(b'private truncated body'))
    with pytest.raises(PublicationUnknown) as error:
        publisher.publish(dict(id='b'*32))
    assert 'private' not in str(error.value)


def test_real_canonical_service_lost_reply_retry_and_client_ingestion(publisher, operator, tmp_path):
    pytest.importorskip('messenger')
    from control.friends.notices import publish
    from messenger.service_events import validate_feed
    from scripts.service_notices import Notices

    registry = tmp_path / 'notices.sqlite'
    token = tmp_path / 'canonical.token'
    store = Notices(registry)
    store.grant('Synthetic operator', token)
    publisher = Publisher(publisher.origin, token)
    feed = tmp_path / 'family-connect-events.json'
    message = draft(operator)
    queue(operator, message)

    class CanonicalAPI:
        lost = False

        def open(self, request, timeout):
            if request.data:
                result = publish(registry, feed, request.get_header('Authorization'), json.loads(request.data))
                if not self.lost:
                    self.lost = True
                    raise urllib.error.URLError('Synthetic lost reply after commit')
                return Reply(result)
            return Reply(feed.with_name('family-connect-events-v2.json').read_bytes())

    try:
        publisher.opener = CanonicalAPI()
        assert publish_next(publisher) == 'unknown'
        assert store.db.execute('SELECT COUNT(*) FROM events').fetchone()[0] == 1
        queue(operator, message)
        assert publish_next(publisher) == 'published'
        assert store.db.execute('SELECT COUNT(*) FROM events').fetchone()[0] == 1
        received = validate_feed(json.loads(feed.with_name('family-connect-events-v2.json').read_bytes()), platform='android')
        assert len(received) == 1 and received[0]['id'] == message.pk.hex
        assert received[0]['body'] == message.body
        assert validate_feed(store.feed(version=2), platform='windows') == []
        store.revoke('Synthetic operator')
        second = draft(operator)
        queue(operator, second)
        from control.friends.notices import NoticeDenied
        with pytest.raises(NoticeDenied):
            publisher.publish(payload(second))
    finally:
        store.db.close()


@pytest.mark.parametrize('origin', ['http://example.com', 'https://user:secret@example.com',
    'https://example.com/path', 'https://example.com/?query=1', 'https://example.com/#fragment'])
def test_unsafe_origin_rejected(origin, tmp_path):
    with pytest.raises(ValueError):
        Publisher(origin, tmp_path / 'missing')


def test_token_permissions_and_symlink_rejected(tmp_path):
    token = tmp_path / 'token'
    token.write_text('a' * 64)
    token.chmod(0o644)
    with pytest.raises(ValueError):
        Publisher('https://example.com', token)
    token.chmod(0o600)
    link = tmp_path / 'link'
    link.symlink_to(token)
    with pytest.raises(OSError):
        Publisher('https://example.com', link)


def test_command_rejects_bad_config_without_exposing_credentials(console, tmp_path):
    for options in [dict(limit=0), dict(limit=21), dict(limit=1)]:
        with pytest.raises(CommandError) as error:
            call_command('publish_system_messages', origin='https://example.com', token_file=str(tmp_path / 'missing'), **options)
        assert str(tmp_path) not in str(error.value)
