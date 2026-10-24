import json
import ssl

import httpx
import pytest

from provisioning.chat_bridge import ChatHTTP
from provisioning.chat_bridge_protocol import BridgeError
from provisioning.friends import FriendsClient, FriendsError


class Bridge:
    def __init__(self, error=None):
        self.calls = []
        self.error = error

    def request(self, path, body, timeout):
        self.calls.append((path, json.loads(body), timeout))
        if self.error is not None:
            raise self.error
        return 200, b'{"fallback":true}'


def invoke(handler, bridge):
    with httpx.Client(base_url='https://185.251.89.19:8443', transport=httpx.MockTransport(handler)) as direct:
        client = FriendsClient(ChatHTTP(direct, bridge), object())
        return client._post('/friends/chat/challenge', {'test': 'synthetic'})


def test_direct_success_does_not_acquire_restricted_transport():
    bridge = Bridge()
    assert invoke(lambda request: httpx.Response(200, json={'direct': True}), bridge) == {'direct': True}
    assert not bridge.calls


@pytest.mark.parametrize('status', [400, 401, 403, 409])
def test_direct_authorization_and_conflict_never_fall_back(status):
    bridge = Bridge()
    with pytest.raises(FriendsError, match='access_rejected'):
        invoke(lambda request: httpx.Response(status), bridge)
    assert not bridge.calls


def test_wrapped_tls_failure_does_not_fall_back():
    def handler(request):
        try:
            raise ssl.SSLCertVerificationError('synthetic')
        except ssl.SSLError as cause:
            raise httpx.ConnectError('TLS failed') from cause
    bridge = Bridge()
    with pytest.raises(FriendsError, match='access_rejected'):
        invoke(handler, bridge)
    assert not bridge.calls


@pytest.mark.parametrize('failure', [httpx.ConnectError('synthetic'), httpx.ReadTimeout('synthetic'), 503])
def test_only_transient_direct_failure_uses_existing_exit(failure):
    def handler(request):
        if isinstance(failure, Exception):
            raise failure
        return httpx.Response(failure)
    bridge = Bridge()
    assert invoke(handler, bridge) == {'fallback': True}
    assert len(bridge.calls) == 1 and bridge.calls[0][0] == '/friends/chat/challenge'
    assert 0 < bridge.calls[0][2] <= 60


@pytest.mark.parametrize('code', ['DENIED', 'CONFLICT'])
def test_restricted_denial_stays_terminal(code):
    bridge = Bridge(BridgeError(code))
    with pytest.raises(FriendsError, match='access_rejected'):
        invoke(lambda request: httpx.Response(503), bridge)
    assert len(bridge.calls) == 1


@pytest.mark.parametrize('content,headers', [(b'{' + b'a' * 16384, {}), (b'not json', {}),
                                         (b'{}', {'Content-Encoding': 'deflate'})])
def test_bad_or_oversized_direct_response_does_not_fall_back(content, headers):
    bridge = Bridge()
    def handler(request):
        response = httpx.Response(200, content=content)
        response.headers.update(headers)
        return response
    with pytest.raises(FriendsError, match='invalid_response'):
        invoke(handler, bridge)
    assert not bridge.calls
