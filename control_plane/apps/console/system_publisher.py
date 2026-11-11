import http.client
import json
import os
import re
import stat
import time
import urllib.error
import urllib.parse
import urllib.request

from django.core.exceptions import PermissionDenied
from django.db import transaction

from .models import SystemMessage
from .system_messages import MessageForm, audit, payload
from .workflow import authorize


class PublicationUnknown(Exception):
    pass


class PublicationRefused(Exception):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def unique_object(pairs):
    result = {}
    for name, value in pairs:
        if name in result:
            raise ValueError('Duplicate response field')
        result[name] = value
    return result


class Publisher:
    def __init__(self, origin, token_file):
        parsed = urllib.parse.urlsplit(origin)
        if (parsed.scheme != 'https' or not parsed.hostname or parsed.username is not None
                or parsed.password is not None or parsed.path not in ('', '/') or parsed.query or parsed.fragment):
            raise ValueError('Publisher requires a fixed HTTPS origin')
        self.origin = origin.rstrip('/')
        descriptor = os.open(token_file, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(descriptor, 'r', encoding='ascii') as stream:
            info = os.fstat(stream.fileno())
            if (not stat.S_ISREG(info.st_mode) or info.st_mode & 0o077 or info.st_uid != os.geteuid()
                    or info.st_size not in (64, 65)):
                raise ValueError('Publisher token must be an owner-only regular file')
            self.token = stream.read(66).strip()
        if re.fullmatch('[a-f0-9]{64}', self.token) is None:
            raise ValueError('Invalid publisher credential')
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect)

    def request(self, path, value=None):
        headers = {'Accept': 'application/json', 'Accept-Encoding': 'identity', 'Cache-Control': 'no-cache'}
        data = None
        if value is not None:
            headers.update({'Authorization': 'Bearer ' + self.token, 'Content-Type': 'application/json'})
            data = json.dumps(value, ensure_ascii=False).encode()
        request = urllib.request.Request(self.origin + path, data=data, headers=headers)
        deadline = time.monotonic() + 20
        try:
            with self.opener.open(request, timeout=10) as response:
                if response.status != 200 or response.headers.get('Content-Encoding', 'identity') != 'identity':
                    raise PublicationUnknown
                raw = bytearray()
                while True:
                    chunk = response.read1(8192)
                    if len(raw) + len(chunk) > 1000000 or time.monotonic() > deadline:
                        raise PublicationUnknown
                    raw.extend(chunk)
                    if not chunk:
                        break
            return json.loads(raw, object_pairs_hook=unique_object)
        except urllib.error.HTTPError as failure:
            code = failure.code
            failure.close()
            if value is not None and code in (400, 401, 403, 409, 422):
                raise PublicationRefused from None
            raise PublicationUnknown from None
        except (OSError, ValueError, urllib.error.URLError, http.client.HTTPException, RecursionError):
            raise PublicationUnknown from None

    def publish(self, value):
        if self.request('/friends/notices/publish', value) != dict(id=value['id'], status='published'):
            raise PublicationUnknown
        feed = self.request('/downloads/family-connect-events-v2.json')
        if (type(feed) is not dict or set(feed) != {'version', 'events'}
                or type(feed['version']) is not int or feed['version'] != 2
                or type(feed['events']) is not list or len(feed['events']) > 200):
            raise PublicationUnknown
        matches = [event for event in feed['events'] if type(event) is dict and event.get('id') == value['id']]
        if len(matches) != 1:
            raise PublicationUnknown
        event = matches[0]
        if (any(event.get(field) != value[field] for field in ('kind', 'title', 'body', 'platforms'))
                or type(event.get('created')) is not int or type(event.get('expires')) is not int
                or not 0 < event['created'] <= int(time.time()) + 300 or event['expires'] <= time.time()
                or event['expires'] - event['created'] != value['days'] * 86400):
            raise PublicationUnknown


def publish_next(publisher):
    with transaction.atomic():
        message = SystemMessage.objects.select_for_update(skip_locked=True).filter(status='queued').order_by('created_at').first()
        if message is None:
            return None
        try:
            authorize(message.created_by, 'view_system_messages')
            authorize(message.created_by, 'send_system_message')
            value = payload(message)
            form = MessageForm(value)
            if not form.is_valid() or any(value[field] != content for field, content in form.cleaned_data.items()):
                raise PublicationRefused
            publisher.publish(value)
            message.status = 'published'
        except (PermissionDenied, PublicationRefused):
            message.status = 'refused'
        except PublicationUnknown:
            message.status = 'unknown'
        message.save(update_fields=['status', 'updated_at'])
        audit(message, message.status)
        return message.status
