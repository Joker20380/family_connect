import base64
import json
import ssl

import pytest

from provisioning.readiness_relay import MAX_RESPONSE, PATHS, ReadinessRelay


class Connection:
    status = 200
    body = b'{"fixture":true}'
    encoding = 'identity'
    closed = False

    def request(self, method, path, **kwargs):
        self.sent = method, path, kwargs

    def getresponse(self):
        return self

    def getheader(self, name, default):
        return self.encoding

    def read(self, maximum):
        return self.body[:maximum]

    def close(self):
        self.closed = True


@pytest.mark.parametrize('path', sorted(PATHS))
def test_exact_proof_forwarded_without_entitlement_override(path):
    connection = Connection()
    raw = b'{"proof":"synthetic-existing-identity-proof"}'
    result = json.loads(ReadinessRelay(lambda: connection).respond(path, raw))
    assert result['status'] == 200
    assert base64.b64decode(result['body']) == connection.body
    assert connection.sent == ('POST', path, {'body': raw, 'headers': {
        'Content-Type': 'application/json', 'Cache-Control': 'no-store'}})
    assert connection.closed


@pytest.mark.parametrize('status', [301, 400, 401, 403, 409, 429, 503])
def test_denials_not_retried_redirected_or_cached(status):
    connection = Connection()
    connection.status = status
    result = json.loads(ReadinessRelay(lambda: connection).respond(next(iter(PATHS)), b'{}'))
    assert result == {'status': status, 'body': ''}
    assert connection.closed


@pytest.mark.parametrize('path,data', [('/friends/activate', b'{}'),
    ('https://elsewhere/', b'{}'), (next(iter(PATHS)), b'x' * 8193),
    (next(iter(PATHS)), ''), (next(iter(PATHS)), b'')])
def test_invalid_requests_never_open_backend(path, data):
    def forbidden():
        pytest.fail('backend called')
    assert json.loads(ReadinessRelay(forbidden).respond(path, data))['status'] == 400


def test_bounded_slots_failure_and_response():
    connection = Connection()
    relay = ReadinessRelay(lambda: connection)
    for _ in range(4):
        assert relay.slots.acquire(False)
    assert json.loads(relay.respond(next(iter(PATHS)), b'{}'))['status'] == 503
    relay.slots.release()
    connection.body = b'x' * (MAX_RESPONSE + 1)
    assert json.loads(relay.respond(next(iter(PATHS)), b'{}'))['status'] == 502
    connection.body = b'{}'
    connection.encoding = 'gzip'
    assert json.loads(relay.respond(next(iter(PATHS)), b'{}'))['status'] == 502


def test_tls_error_fails_closed():
    def rejected():
        raise ssl.SSLCertVerificationError('synthetic')
    relay = ReadinessRelay(rejected)
    assert json.loads(relay.respond(next(iter(PATHS)), b'{}')) == {'status': 503, 'body': ''}
    assert relay.slots.acquire(False)
