import asyncio
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


def invoke(handler, bridge, *, cancelled=None):
    with httpx.Client(base_url='https://185.251.89.19:8443', transport=httpx.MockTransport(handler)) as direct:
        client = FriendsClient(ChatHTTP(direct, bridge), object(), cancelled=cancelled)
        return client._post('/friends/chat/challenge', {'test': 'synthetic'})


class ControlledStream(httpx.SyncByteStream):
    def __init__(self, *, chunks=(b'{"direct":true}',), read_error=None, close_error=None, on_read=None):
        self.chunks, self.read_error, self.close_error = chunks, read_error, close_error
        self.on_read = on_read
        self.close_calls = 0

    def __iter__(self):
        if self.on_read is not None:
            self.on_read()
        yield from self.chunks
        if self.read_error is not None:
            raise self.read_error

    def close(self):
        self.close_calls += 1
        if self.close_error is not None:
            raise self.close_error


def transport_failure(cause):
    failure = httpx.ReadError('synthetic transport')
    failure.__cause__ = cause
    return failure


@pytest.fixture
def streams():
    created = []
    def create(**options):
        options.setdefault('close_error', transport_failure(ValueError('synthetic cleanup cause')))
        stream = ControlledStream(**options)
        created.append(stream)
        return stream
    yield create
    assert created and all(stream.close_calls == 1 for stream in created)


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


@pytest.mark.parametrize('status', [400, 401, 403, 409])
def test_access_rejection_survives_cleanup_failure(status, streams):
    bridge, stream = Bridge(), streams()
    with pytest.raises(FriendsError, match='^access_rejected$'):
        invoke(lambda request: httpx.Response(status, stream=stream), bridge)
    assert not bridge.calls


@pytest.mark.parametrize('chunks,headers', [((b'{}',), {'Content-Encoding': 'deflate'}),
                                          ((b'a' * 8192, b'b' * 8193), {})])
def test_invalid_response_survives_cleanup_failure(chunks, headers, streams):
    bridge, stream = Bridge(), streams(chunks=chunks)
    with pytest.raises(FriendsError, match='^invalid_response$'):
        invoke(lambda request: httpx.Response(200, stream=stream, headers=headers), bridge)
    assert not bridge.calls


def test_read_tls_failure_survives_cleanup_with_its_own_non_tls_cause(streams):
    bridge = Bridge()
    stream = streams(read_error=transport_failure(ssl.SSLCertVerificationError('synthetic TLS')))
    with pytest.raises(FriendsError, match='^access_rejected$'):
        invoke(lambda request: httpx.Response(200, stream=stream), bridge)
    assert not bridge.calls


@pytest.mark.parametrize('cleanup', [transport_failure(ssl.SSLCertVerificationError('synthetic cleanup TLS')),
                                   RuntimeError('synthetic cleanup')])
def test_invalid_response_is_not_replaced_by_cleanup_failure(cleanup, streams):
    bridge = Bridge()
    stream = streams(close_error=cleanup)
    with pytest.raises(FriendsError, match='^invalid_response$'):
        invoke(lambda request: httpx.Response(200, stream=stream, headers={'Content-Encoding': 'deflate'}), bridge)
    assert not bridge.calls


def test_established_deadline_survives_cleanup_failure(monkeypatch, streams):
    clock = [100.0]
    monkeypatch.setattr('provisioning.chat_bridge.time.monotonic', lambda: clock[0])
    def expire():
        clock[0] += 60
    bridge, stream = Bridge(), streams(on_read=expire)
    with pytest.raises(FriendsError, match='^timeout$'):
        invoke(lambda request: httpx.Response(200, stream=stream), bridge)
    assert not bridge.calls


def test_complete_response_is_not_repeated_after_cleanup_transport_failure(streams):
    bridge, stream = Bridge(), streams()
    assert invoke(lambda request: httpx.Response(200, stream=stream), bridge) == {'direct': True}
    assert not bridge.calls


def test_completed_invalid_json_is_still_validated_by_friends_after_cleanup_failure(streams):
    bridge, stream = Bridge(), streams(chunks=(b'not json',))
    with pytest.raises(FriendsError, match='^invalid_response$'):
        invoke(lambda request: httpx.Response(200, stream=stream), bridge)
    assert not bridge.calls


@pytest.mark.parametrize('cleanup', [None, transport_failure(ValueError('synthetic cleanup cause'))])
def test_partial_transient_read_keeps_existing_fallback(cleanup, streams):
    bridge, stream = Bridge(), streams(chunks=(b'{"partial":',), read_error=httpx.ReadTimeout('synthetic read'),
                                      close_error=cleanup)
    assert invoke(lambda request: httpx.Response(200, stream=stream), bridge) == {'fallback': True}
    assert len(bridge.calls) == 1


def test_consumer_transport_error_after_yield_does_not_fall_back(streams):
    bridge, stream = Bridge(), streams(close_error=None)
    failure = httpx.ReadTimeout('synthetic consumer')
    with httpx.Client(base_url='https://185.251.89.19:8443',
                      transport=httpx.MockTransport(lambda request: httpx.Response(200, stream=stream))) as direct:
        with pytest.raises(httpx.ReadTimeout) as raised:
            with ChatHTTP(direct, bridge).stream('POST', '/friends/chat/challenge', json={}) as response:
                assert response.json() == {'direct': True}
                raise failure
    assert raised.value is failure
    assert not bridge.calls


@pytest.mark.parametrize('failure', [FriendsError('cancelled'), asyncio.CancelledError('synthetic cancellation')])
def test_read_cancellation_survives_cleanup_failure(failure, streams):
    bridge, stream = Bridge(), streams(read_error=failure)
    with pytest.raises(type(failure)) as raised:
        invoke(lambda request: httpx.Response(200, stream=stream), bridge)
    assert raised.value is failure
    assert not bridge.calls


def test_friends_cancellation_after_read_is_not_retried_on_cleanup_failure(streams):
    cancelled = []
    bridge, stream = Bridge(), streams(on_read=lambda: cancelled.append(True))
    with pytest.raises(FriendsError, match='^cancelled$'):
        invoke(lambda request: httpx.Response(200, stream=stream), bridge, cancelled=lambda: bool(cancelled))
    assert not bridge.calls


def test_unexpected_cleanup_error_is_not_suppressed_or_retried(streams):
    bridge, stream = Bridge(), streams(close_error=RuntimeError('synthetic cleanup'))
    with pytest.raises(FriendsError, match='^service_unavailable$'):
        invoke(lambda request: httpx.Response(200, stream=stream), bridge)
    assert not bridge.calls
