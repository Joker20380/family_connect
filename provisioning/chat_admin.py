"""Accepted device-proof announcement API; never enrolls or grants a role."""
import json
import re

from messenger.service_events import validate_feed
from .friends import FriendsClient, FriendsError


def identifier(value):
    if type(value) is not str or re.fullmatch('[a-f0-9]{32}', value) is None:
        raise FriendsError('invalid_input')


def validate_notice(value, *, edit=False):
    fields = {'id', 'title', 'body'} | ({'revision', 'request_id'} if edit else {'kind', 'platforms', 'days'})
    if type(value) is not dict or set(value) != fields:
        raise FriendsError('invalid_input')
    identifier(value['id'])
    for field, limit in (('title', 160), ('body', 4000)):
        text = value[field]
        if type(text) is not str or not text.strip() or len(text) > limit or any(ord(char) < 32 and char not in '\n\t' for char in text):
            raise FriendsError('invalid_input')
        try:
            if len(text.encode('utf-16-le')) // 2 > limit:
                raise FriendsError('invalid_input')
        except UnicodeError:
            raise FriendsError('invalid_input') from None
    if edit:
        identifier(value['request_id'])
        if type(value['revision']) is not int or not 1 <= value['revision'] < 1000000:
            raise FriendsError('invalid_input')
    elif (value['kind'] != 'information' or value['platforms'] != ['android', 'windows', 'linux'] or
          type(value['days']) is not int or value['days'] != 30):
        raise FriendsError('invalid_input')
    return dict(value)


class AnnouncementClient(FriendsClient):
    def _post(self, path, body, *, limit=None, notice_conflict=False):
        return super()._post(path, body, limit=16384 if limit is None else limit,
                             notice_conflict=notice_conflict, identity_encoding=True)

    def _notice(self, action, fields):
        request = dict(proof=self._proof('notices-' + action), **fields)
        if len(json.dumps(request, ensure_ascii=False, separators=(',', ':')).encode()) > 32768:
            raise FriendsError('invalid_input')
        return self._post('/friends/notices/device/' + action, request,
                          limit=1048576 if action == 'list' else 16384, notice_conflict=action == 'edit')

    def list(self, offset):
        if type(offset) is not int or not 0 <= offset <= 2000000000:
            raise FriendsError('invalid_input')
        result = self._notice('list', {'offset': offset})
        self._fields(result, 'events next_offset')
        events, next_offset = result['events'], result['next_offset']
        if type(events) is not list or len(events) > 50:
            raise FriendsError('invalid_response')
        if next_offset is not None and (type(next_offset) is not int or next_offset != offset + 50 or len(events) != 50):
            raise FriendsError('invalid_response')
        try:
            validate_feed(dict(version=2, events=events), now=int(self.clock()))
        except (ValueError, TypeError, UnicodeError):
            raise FriendsError('invalid_response') from None
        return result

    def publish(self, value):
        value = validate_notice(value)
        result = self._notice('publish', {'notice': value})
        self._fields(result, 'id status')
        if result != dict(id=value['id'], status='published'):
            raise FriendsError('invalid_response')
        return result

    def edit(self, value):
        value = validate_notice(value, edit=True)
        result = self._notice('edit', {'notice': value})
        self._fields(result, 'id revision status')
        if (type(result['revision']) is not int or result['revision'] != value['revision'] + 1 or
                result['id'] != value['id'] or result['status'] != 'updated'):
            raise FriendsError('invalid_response')
        return result
