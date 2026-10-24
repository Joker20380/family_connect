"""Strict user-session IPC and encrypted, crash-safe mutation replay fences."""
import hashlib
import json
import re
import time

from messenger.local import LocalError


BUS_NAME = 'com.familyconnect.Chat1'
OBJECT_PATH = '/com/familyconnect/Chat1'
PROTOCOL = 1
MAX_REQUEST = 262144
MAX_RESPONSE = 1048576
MAX_TICKETS = 64
REQUEST_AGE = 120
READS = frozenset(('profile', 'contacts', 'inbox_summary', 'preview_contact', 'history', 'audio',
                  'voice_settings', 'delivery_settings', 'event_counts', 'service_events_page', 'announcements_list'))
WRITES = frozenset(('trust_contact', 'rename_contact', 'queue', 'edit_message', 'queue_audio', 'queue_radio',
                   'voice_mode', 'voice_confirm', 'background_delivery', 'notification_settings', 'visible_read',
                   'announcements_publish', 'announcements_edit'))
SUPPORT = frozenset(('support_status', 'support_consent'))
ERRORS = frozenset(('closed', 'invalid_input', 'not_created', 'identity_unavailable', 'identity_mismatch',
    'keyring_unavailable', 'store_unavailable', 'own_contact', 'fingerprint_mismatch', 'unverified_contact',
    'message_not_saved', 'invalid_audio', 'audio_unavailable', 'operation_outcome_unknown', 'busy',
    'service_unavailable', 'response_too_large', 'request_expired', 'notice_denied', 'notice_conflict', 'notice_unavailable',
    'support_unavailable', 'support_conflict'))


def object_pairs(pairs):
    result = {}
    for name, value in pairs:
        if name in result:
            raise ValueError('duplicate_field')
        result[name] = value
    return result


def parse_request(raw, now=None):
    now = time.time() if now is None else now
    try:
        if type(raw) is not str or len(raw.encode('utf-8')) > MAX_REQUEST:
            raise ValueError()
        value = json.loads(raw, object_pairs_hook=object_pairs)
        if (type(value) is not dict or set(value) != {'id', 'created', 'operation', 'arguments'} or
                type(value['id']) is not str or not re.fullmatch('[a-f0-9]{32}', value['id']) or
                type(value['created']) is not int or type(value['operation']) is not str or
                value['operation'] not in READS | WRITES | SUPPORT | {'open', 'heartbeat', 'detach', 'status'} or
                type(value['arguments']) is not dict):
            raise ValueError()
        if not now - REQUEST_AGE <= value['created'] <= now + 5:
            raise LocalError('request_expired')
        return value
    except (ValueError, TypeError, RecursionError, UnicodeError):
        raise LocalError('invalid_input') from None


def encode_response(value=None, error=None):
    result = {'protocol': PROTOCOL, 'ok': error is None}
    result['value' if error is None else 'error'] = value if error is None else error if error in ERRORS else 'store_unavailable'
    try:
        raw = json.dumps(result, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
        if len(raw.encode()) > MAX_RESPONSE:
            return encode_response(error='response_too_large')
        return raw
    except (ValueError, TypeError, RecursionError, UnicodeError):
        return encode_response(error='store_unavailable')


def invoke(owner, request):
    operation, arguments = request['operation'], request['arguments']
    if operation in READS:
        return owner.invoke(operation, **arguments)
    if operation not in WRITES or owner.local is None:
        raise LocalError('invalid_input')
    store = owner.local._store
    digest = hashlib.sha256(json.dumps(request, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
    with owner.local._lock, store._lock:
        tickets = store._get('desktop-rpc-v1')
        if tickets is None:
            tickets = {}
        if type(tickets) is not dict or len(tickets) > MAX_TICKETS:
            raise LocalError('store_unavailable')
        previous = tickets.get(request['id'])
        if previous is not None:
            if previous.get('digest') != digest:
                raise LocalError('invalid_input')
            if previous.get('state') != 'complete':
                raise LocalError('operation_outcome_unknown')
            if 'error' in previous:
                raise LocalError(previous['error'])
            return previous['value']
        now = time.time()
        tickets = {ident: item for ident, item in tickets.items() if item['expires'] >= now}
        if len(tickets) >= MAX_TICKETS:
            raise LocalError('busy')
        ticket = dict(digest=digest, expires=request['created'] + REQUEST_AGE, state='pending')
        tickets[request['id']] = ticket
        with store._db:
            store._put('desktop-rpc-v1', tickets)
        try:
            result = owner.invoke(operation, **arguments)
        except LocalError as failure:
            code = str(failure) if str(failure) in ERRORS else 'store_unavailable'
            ticket.update(state='complete', error=code)
            with store._db:
                store._put('desktop-rpc-v1', tickets)
            raise LocalError(code) from None
        ticket.update(state='complete', value=result)
        with store._db:
            store._put('desktop-rpc-v1', tickets)
        return result
