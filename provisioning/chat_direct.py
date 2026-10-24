"""Fixed chat-only DIRECT admission; endpoint selection never comes from the GUI."""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re

import httpx

from . import chat_bridge_protocol as wire
from .chat_bridge import ChatBridge
from .friends import FriendsError


def authority_digest(response):
    return hashlib.sha256(json.dumps(response, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def validate(request):
    fields = dict(request)
    if fields.get('action') == 'open':
        authority = fields.pop('authority', None)
        if type(authority) is not str or not re.fullmatch('[0-9a-f]{64}', authority):
            raise wire.BridgeError('DENIED')
    wire.validate(fields)
    if fields['action'] == 'request':
        body = json.loads(wire.payload(fields['data'], 8192), object_pairs_hook=wire.pairs)
        challenge = fields['path'] == wire.PATHS[0]
        expected = {'public_identity', 'wireguard_public_key', 'chat_public'} if challenge else {'proof', 'chat_public', 'chat_signature'}
        if set(body) != expected or type(body['chat_public']) is not str or not re.fullmatch('[0-9a-f]{128}', body['chat_public']):
            raise wire.BridgeError('DENIED')
        if challenge:
            if len(wire.payload(body['wireguard_public_key'], 32)) != 32:
                raise wire.BridgeError('DENIED')
        else:
            from device_identity.device import verify_transport_key_proof
            from messenger.admission import message
            from messenger.codec import identity
            proof = body['proof']
            if verify_transport_key_proof(proof, expected_challenge=proof.get('challenge')) != fields['device']:
                raise wire.BridgeError('DENIED')
            signature = body['chat_signature']
            if (type(signature) is not str or not re.fullmatch('[0-9a-f]{128}', signature) or
                    not identity(bytes.fromhex(body['chat_public'])).validate(bytes.fromhex(signature),
                        message(body['chat_public'], fields['device'], proof['challenge']))):
                raise wire.BridgeError('DENIED')
    return request


class DirectBridge(ChatBridge):
    ROUTE = 'DIRECT'
    validate = staticmethod(validate)

    def __init__(self, device, **options):
        options.setdefault('_paths', [Path('/run/family-connect-chat-direct') / (str(os.getuid()) + '.chat.sock')])
        super().__init__(device, **options)
        self.authority = None

    def bind(self, response):
        self.authority = authority_digest(response)

    def open_mailbox(self, deadline, cancel):
        if self.authority is None:
            raise wire.BridgeError()
        selected = self._select(deadline, cancel)
        with self._connection(selected, deadline, cancel) as connection:
            self._request(connection, 'open', deadline, authority=self.authority)
            channel = wire.receive_socket(connection)
        if cancel.is_set() or self.closed:
            channel.close()
            raise wire.BridgeError('CANCELLED')
        return channel


class DirectHTTP:
    base_url = httpx.URL('https://185.251.89.19:8443')

    def __init__(self, bridge):
        self.bridge = bridge

    @contextmanager
    def stream(self, method, path, *, content, timeout, **options):
        if method != 'POST' or path not in wire.PATHS:
            raise FriendsError('invalid_input')
        try:
            status, body = self.bridge.request(path, content, timeout)
        except wire.BridgeError as error:
            terminal = {'DENIED': 'access_rejected', 'CONFLICT': 'access_rejected',
                        'CANCELLED': 'cancelled', 'DEADLINE': 'timeout', 'INVALID_RESPONSE': 'invalid_response'}
            if error.code in terminal:
                raise FriendsError(terminal[error.code]) from None
            raise httpx.ConnectError('Protected chat route unavailable') from None
        yield httpx.Response(status, content=body, request=httpx.Request('POST', self.base_url.join(path)))
