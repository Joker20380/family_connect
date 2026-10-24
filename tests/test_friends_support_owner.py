import json

import httpx
import pytest

from control.friends.access import Access, Rejected
from control.friends import support_ids
from provisioning.friends import FriendsError
from provisioning.friends_owner import FriendsOwner


def test_own_support_id_authenticated_cached_bound_to_identity_and_no_key_changes(tmp_path):
    access = Access(tmp_path / 'access.db')
    access.initialize()
    invitation = access.invite()
    requests = []
    fail = False
    def route(request):
        value = json.loads(request.content)
        requests.append(request.url.path)
        try:
            if request.url.path == '/friends/challenge':
                return httpx.Response(200, json=access.challenge(**value))
            if request.url.path == '/friends/activate':
                return httpx.Response(200, json=dict(device=access.complete(value, 'activate')['device'], status='active'))
            if request.url.path == '/friends/device/support':
                if fail:
                    return httpx.Response(503)
                return httpx.Response(200, json=support_ids.request(access, value))
            raise AssertionError('Unexpected request')
        except Rejected:
            return httpx.Response(403)
    factory = lambda: httpx.Client(base_url='https://test.invalid', transport=httpx.MockTransport(route))
    owner = FriendsOwner(tmp_path / 'identity', tmp_path / 'anchor', http_factory=factory)
    assert owner.cached_support_id() is None and not owner.path.exists()
    with pytest.raises((OSError, ValueError)):
        owner.refresh_support_id('linux-0.2.11', 2011)
    owner.activate(invitation)
    with access.db() as database:
        support_ids.create(database)
        expected = support_ids.registered(database, owner._device().reference)
    original = {name: (owner.path / name).read_bytes() for name in ('reticulum.key', 'wireguard.key', 'friends.initialized')}
    assert owner.refresh_support_id('linux-0.2.11', 2011) == expected
    assert owner.cached_support_id() == expected
    assert (owner.path / 'support.json').stat().st_mode & 0o777 == 0o600
    fail = True
    with pytest.raises(FriendsError):
        owner.refresh_support_id('linux-0.2.11', 2011)
    assert owner.cached_support_id() == expected
    assert all((owner.path / name).read_bytes() == raw for name, raw in original.items())
    other = FriendsOwner(tmp_path / 'other', tmp_path / 'anchor', http_factory=factory)
    other._device(True)
    (other.path / 'support.json').write_bytes((owner.path / 'support.json').read_bytes())
    (other.path / 'support.json').chmod(0o600)
    assert other.cached_support_id() is None
    (owner.path / 'support.json').write_text('{"schema":1,"schema":1}')
    assert owner.cached_support_id() is None
    assert all((owner.path / name).read_bytes() == raw for name, raw in original.items())
    assert requests.count('/friends/activate') == 1
