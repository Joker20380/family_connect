"""Desktop enrollment speaks the deployed API using disposable identities only."""
import base64
import json
import secrets

import httpx
import RNS
import pytest

from control.friends.access import Access, Rejected
from control.friends.referrals import Referrals
from control.friends.chat import ChatAccess
from messenger.admission import message
from device_identity.device import DeviceIdentity
from provisioning.friends import FriendsClient, FriendsError


@pytest.fixture
def service(tmp_path):
    access = Access(tmp_path / 'access.sqlite', clock=lambda: 1000)
    access.initialize()
    referrals = Referrals(access, secrets.token_bytes(32))
    referrals.initialize()
    chat_access = ChatAccess(access)
    chat_access.initialize()
    seen = []

    def route(request):
        seen.append(request.url.path)
        body = json.loads(request.content)
        try:
            if request.url.path == '/friends/challenge':
                result = access.challenge(**body)
            elif request.url.path == '/friends/activate':
                result = dict(device=access.complete(body, request.url.path.rsplit('/',1)[1])['device'], status='active')
            elif request.url.path == '/friends/referral/claim':
                result = referrals.claim(**body)
            elif request.url.path == '/friends/device/status':
                result = access.status(body)
            elif request.url.path == '/friends/referral/issue':
                result = referrals.issue(body)
            elif request.url.path == '/friends/chat/challenge':
                result = chat_access.challenge(**body)
            elif request.url.path == '/friends/chat/register':
                result = chat_access.register(**body)
            else:
                return httpx.Response(404)
            return httpx.Response(200, json=result)
        except (Rejected, ValueError):
            return httpx.Response(403, json={'detail': 'not for the UI'})

    with httpx.Client(base_url='https://pilot.invalid', transport=httpx.MockTransport(route),
                      timeout=10) as http:
        yield access, FriendsClient(http, DeviceIdentity.generate(), clock=lambda: 1000), seen


def test_existing_api_activation_referral_and_persisted_identity(service):
    access, client, seen = service
    identity = client.device
    original = (identity.reference, identity.public_identity, identity.wireguard_public_key)
    invitation = access.invite()
    result = client.activate(invitation)
    assert result == dict(device=identity.reference, status='active')
    first = client.referral()
    assert client.referral()['url'] == first['url']
    assert first['pool_limit'] == first['remaining'] == 500
    # Repeating activation with the same owner must not create a second device.
    client.activate(invitation)
    with access.db() as db:
        assert db.execute('SELECT COUNT(*) FROM devices').fetchone()[0] == 1
        assert db.execute('SELECT COUNT(*) FROM challenges WHERE used=0').fetchone()[0] == 0
    assert original == (identity.reference, identity.public_identity, identity.wireguard_public_key)
    assert seen.count('/friends/challenge') == 4


def test_device_status_recovery_round_trip(service):
    access, client, _ = service
    # Unknown device: authenticated query returns not-registered without consuming anything.
    status = client.device_status()
    assert status == dict(device=client.device.reference, registered=False, revoked=False, active=False)
    with access.db() as db:
        assert db.execute('SELECT COUNT(*) FROM devices').fetchone()[0] == 0
    # After activation the same local identity reports registered/active.
    invitation = access.invite()
    client.activate(invitation)
    status = client.device_status()
    assert status == dict(device=client.device.reference, registered=True, revoked=False, active=True)


def test_not_activated_and_revoked_owner_cannot_refer(service):
    access, client, _ = service
    with pytest.raises(FriendsError, match='^access_rejected$'):
        client.referral()
    client.activate(access.invite())
    with access.db() as db:
        db.execute('UPDATE devices SET revoked=1')
    with pytest.raises(FriendsError, match='^access_rejected$'):
        client.referral()


@pytest.mark.parametrize('code', ['', 'FC-abcd', 'X' * 129, None, True])
def test_invalid_invitation_never_makes_a_request(service, code):
    _, client, seen = service
    with pytest.raises(FriendsError, match='^invalid_invitation$'):
        client.activate(code)
    assert seen == []


@pytest.mark.parametrize('mutation', [
    lambda c: {**c, 'expires_at': 1000},
    lambda c: {**c, 'expires_at': 1121},
    lambda c: {**c, 'expires_at': True},
    lambda c: {**c, 'audience': 'other'},
    lambda c: {**c, 'challenge': 'bad'},
    lambda c: {**c, 'unexpected': 1},
])
def test_bad_challenge_never_sends_proof(mutation):
    device = DeviceIdentity.generate()
    calls = []
    def route(request):
        calls.append(request.url.path)
        return httpx.Response(200, json=mutation(dict(challenge=base64.b64encode(bytes(32)).decode(),
                            expires_at=1120, audience=FriendsClient.AUDIENCE)))
    with httpx.Client(base_url='https://pilot.invalid', transport=httpx.MockTransport(route)) as http:
        client = FriendsClient(http, device, clock=lambda: 1000)
        with pytest.raises(FriendsError, match='^invalid_response$'):
            client.activate('FC-' + 'A' * 32)
    assert calls == ['/friends/challenge']


@pytest.mark.parametrize('raw', [b'{"a":1,"a":2}', b'NaN', b'[' * 2000, b'x' * 65537])
def test_bad_response_is_bounded_and_sanitized(raw):
    with httpx.Client(base_url='https://pilot.invalid', transport=httpx.MockTransport(
            lambda _: httpx.Response(200, content=raw))) as http:
        with pytest.raises(FriendsError, match='^invalid_response$'):
            FriendsClient(http, DeviceIdentity.generate()).referral()


def test_redirect_is_not_followed_and_http_is_refused():
    calls = []
    def route(request):
        calls.append(str(request.url))
        return httpx.Response(307, headers={'Location': 'https://other.invalid/steal'})
    with httpx.Client(base_url='https://pilot.invalid', transport=httpx.MockTransport(route),
                      follow_redirects=True) as http:
        with pytest.raises(FriendsError, match='^service_unavailable$'):
            FriendsClient(http, DeviceIdentity.generate()).referral()
    assert len(calls) == 1
    with httpx.Client(base_url='http://pilot.invalid') as http:
        with pytest.raises(ValueError, match='requires HTTPS'):
            FriendsClient(http, DeviceIdentity.generate())


class ChatOwner:
    def __init__(self):
        self.identity = RNS.Identity()
        self.public = self.identity.get_public_key().hex()

    def profile(self):
        return {'public': self.public}

    def enrollment_proof(self, device, nonce):
        return dict(chat_public=self.public,
                    chat_signature=self.identity.sign(message(self.public, device, nonce)).hex())


def test_chat_enrollment_keeps_server_pending_status_and_checks_ownership(service):
    access, client, _ = service
    client.activate(access.invite())
    chat = ChatOwner()
    result = client.register_chat(chat)
    assert result == dict(device=client.device.reference, chat_public=chat.public, status='pending-node')
    assert client.register_chat(chat) == result
    with pytest.raises(FriendsError, match='^access_rejected$'):
        client.register_chat(ChatOwner())


@pytest.mark.parametrize('mutation', [
    lambda node: {**node, 'expires_at': 1000},
    lambda node: {**node, 'expires_at': 1121},
    lambda node: {**node, 'sequence': True},
    lambda node: {**node, 'host': 'example.com'},
    lambda node: {**node, 'port': 65536},
    lambda node: {**node, 'public_key': 'bad'},
])
def test_invalid_chat_node_not_exposed_to_carrier(mutation):
    device, chat = DeviceIdentity.generate(), ChatOwner()
    node = dict(sequence=1, expires_at=1120, host='192.0.2.1', port=4242, public_key='ab' * 64)
    def route(request):
        if request.url.path.endswith('/challenge'):
            return httpx.Response(200, json=dict(challenge=base64.b64encode(bytes(32)).decode(),
                expires_at=1120, audience=FriendsClient.AUDIENCE, device=device.reference, chat_public=chat.public))
        return httpx.Response(200, json=dict(device=device.reference, chat_public=chat.public,
                                            status='active', node=mutation(node)))
    with httpx.Client(base_url='https://pilot.invalid', transport=httpx.MockTransport(route)) as http:
        with pytest.raises(FriendsError, match='^invalid_response$'):
            FriendsClient(http, device, clock=lambda: 1000).register_chat(chat)


def test_linux_owner_persists_before_enrollment_and_resumes_without_new_invite(service, tmp_path):
    access, reference_client, seen = service
    path = tmp_path / 'linux-device'
    with pytest.raises(FileNotFoundError):
        FriendsClient.from_linux_store(reference_client.http, path)
    assert not seen and not path.exists()
    owner = FriendsClient.from_linux_store(reference_client.http, path, create=True, clock=lambda: 1000)
    assert not seen
    original = {p.name: p.read_bytes() for p in path.iterdir()}
    assert 'friends.initialized' in original
    owner.activate(access.invite())
    first = owner.referral()['url']
    resumed = FriendsClient.from_linux_store(reference_client.http, path, clock=lambda: 1000)
    assert resumed.device.reference == owner.device.reference
    assert resumed.referral()['url'] == first
    assert original == {p.name: p.read_bytes() for p in path.iterdir()}
    (path / 'wireguard.key').unlink()
    before = list(seen)
    with pytest.raises(ValueError, match='recovery'):
        FriendsClient.from_linux_store(reference_client.http, path, create=True)
    assert seen == before and not (path / 'wireguard.key').exists()


def test_link_activation_requires_invitation_and_reuses_device(service):
    access, sponsor, seen = service
    sponsor.activate(access.invite())
    token = sponsor.referral()['url'].split('#')[1]
    child = FriendsClient(sponsor.http, DeviceIdentity.generate(), clock=lambda:1000)
    with pytest.raises(FriendsError, match='access_rejected'):child.register()
    with pytest.raises(FriendsError, match='access_rejected'):child.register('0'*64)
    result=child.register(token)
    assert result['device']==child.device.reference
    assert child.register(token)==result
    assert child.register()==result
    with access.db() as db:
        assert db.execute('SELECT COUNT(*) FROM devices').fetchone()[0]==2
        assert db.execute('SELECT COUNT(*) FROM referral_claims').fetchone()[0]==1
        db.execute('UPDATE devices SET revoked=1 WHERE device=?',(child.device.reference,))
    with pytest.raises(FriendsError, match='access_rejected'):child.register(token)
    assert '/friends/register' not in seen


@pytest.mark.parametrize('lag', [1, 20])
def test_challenge_allows_small_client_clock_lag(service, lag):
    access, client, _ = service
    client.clock = lambda: 1000 - lag
    assert client.activate(access.invite())['status'] == 'active'


def test_challenge_still_rejects_excessive_clock_lag(service):
    access, client, _ = service
    client.clock = lambda: 979
    with pytest.raises(FriendsError):client.activate(access.invite())
