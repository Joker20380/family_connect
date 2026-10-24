import base64
import json
import os
from pathlib import Path
import secrets
import sys
import threading
from types import SimpleNamespace

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'linux'))
from mesh_chat_host import Binding, Host
from control.friends.access import Access, Rejected
from control.friends.chat import ChatAccess
from device_identity.device import DeviceIdentity
from provisioning.chat_bridge import ChatBridge
from provisioning.chat_owner import ChatOwner


class RegistrationLane:
    def __init__(self, access):
        self.access, self.chat = access, ChatAccess(access)
        self.chat.initialize()
        self.calls, self.leases = [], set()

    def call(self, action, **values):
        self.calls.append(action)
        if action == 'acquire':
            self.leases.add(1)
            return dict(lease=1, route='EXISTING_EXIT')
        if action == 'release':
            self.leases.remove(values['lease'])
            return {}
        assert action == 'request' and values['lease'] in self.leases
        body = json.loads(base64.b64decode(values['data']))
        try:
            result = (self.chat.challenge(**body) if values['path'].endswith('/challenge')
                      else self.chat.register(**body))
            return dict(status=200, data=json.dumps(result).encode())
        except Rejected:
            return dict(status=403, data=b'')


@pytest.mark.parametrize('revoke', [False, True])
def test_real_owner_proofs_cross_uid_endpoint_and_preserve_chat_identity(tmp_path, revoke):
    tmp_path.chmod(0o700)
    device = DeviceIdentity.generate()
    access = Access(tmp_path / 'local-access.sqlite')
    access.initialize()
    invitation = access.invite()
    challenge = access.challenge(public_identity=device.public_identity, wireguard_public_key=device.wireguard_public_key,
                                 purpose='activate', invitation=invitation)
    access.complete(device.prove_transport_key(challenge['challenge']), 'activate')
    lane = RegistrationLane(access)
    binding = Binding(lane, dict(readiness={'device': device.reference}, identity='private-synthetic-key',
                                anchor='synthetic-anchor', resolver='1.1.1.1:53', underlying_index=2), threading.Event())
    binding.ready.set()
    host = Host(tmp_path / 'chat.sock', os.getuid(), lambda: binding)
    host.start()
    loaded, clients, direct = [], [], []
    def existing_device(create):
        loaded.append(create)
        assert create is False
        return device
    def unavailable(request):
        direct.append(request.url.path)
        raise httpx.ConnectError('synthetic offline direct route')
    def bridge(reference):
        assert reference == device.reference
        client = ChatBridge(reference, _paths=[host.endpoint], _root_uid=os.getuid())
        clients.append(client)
        return client
    friends = SimpleNamespace(_device=existing_device, http_factory=lambda: httpx.Client(
        base_url='https://example.invalid', transport=httpx.MockTransport(unavailable)))
    key = secrets.token_bytes(32)
    owner = ChatOwner(tmp_path / 'chat', friends, keyring=SimpleNamespace(key=lambda *args, **kwargs: key),
                      runtime_factory=lambda _: None, events_fetcher=lambda _: [], restricted_factory=bridge)
    original_device = device.reference, device.public_identity, device.wireguard_public_key
    try:
        profile = owner.open(create=True)
        state = owner.tick(online=True, visible=True)
        assert state['registration_error'] == 'delivery_unavailable'
        assert owner.node is None and owner.carrier is None
        with access.db() as database:
            row = database.execute('SELECT device,public FROM chat_bindings').fetchone()
            assert tuple(row) == (device.reference, profile['public'])
            assert database.execute('SELECT COUNT(*) FROM chat_challenges WHERE used=1').fetchone()[0] == 1
            if revoke:
                database.execute('UPDATE devices SET revoked=1 WHERE device=?', (device.reference,))
        owner.close()
        assert clients[0].closed
        assert owner.open(create=False) == profile
        owner.next_enrollment = 0
        owner.tick(online=True, visible=True)
        with access.db() as database:
            assert database.execute('SELECT COUNT(*) FROM devices').fetchone()[0] == 1
            assert database.execute('SELECT COUNT(*) FROM chat_bindings').fetchone()[0] == 1
            assert database.execute('SELECT COUNT(*) FROM chat_challenges WHERE used=1').fetchone()[0] == (1 if revoke else 2)
        assert len(direct) == (3 if revoke else 4)
        assert lane.calls.count('request') == len(direct)
        assert loaded == [False, False]
        assert original_device == (device.reference, device.public_identity, device.wireguard_public_key)
    finally:
        owner.close()
        binding.close()
        host.close()
    assert not lane.leases and all(client.closed for client in clients)
