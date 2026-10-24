import base64
from contextlib import contextmanager
import copy
import json
import os
from pathlib import Path
import secrets
import socket
import sys
import threading
import time
from types import SimpleNamespace

import httpx
import pytest
import RNS

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'linux'))
import chat_direct_host
from chat_direct_host import Authority, DirectHost
from control.friends.access import Access, Rejected
from control.friends.chat import ChatAccess
from device_identity.device import DeviceIdentity
from provisioning import chat_bridge_protocol as wire
from provisioning.chat_bridge import ChatHTTP
from provisioning.chat_direct import DirectBridge, DirectHTTP, authority_digest, validate
from provisioning.chat_owner import ChatOwner
from provisioning.chat_transport import ProtectedMailbox, _DirectDeadline
from provisioning.friends import FriendsError
from messenger.mailbox import MailboxError


class API:
    def __init__(self, directory):
        self.access = Access(directory / 'access.sqlite')
        self.access.initialize()
        self.chat = ChatAccess(self.access)
        self.chat.initialize()
        self.device = DeviceIdentity.generate()
        challenge = self.access.challenge(public_identity=self.device.public_identity,
            wireguard_public_key=self.device.wireguard_public_key, purpose='activate', invitation=self.access.invite())
        self.access.complete(self.device.prove_transport_key(challenge['challenge']), 'activate')
        self.node = dict(sequence=1, expires_at=int(time.time()) + 100, host='192.0.2.10', port=4242,
                         public_key=RNS.Identity().get_public_key().hex())
        self.pending = False
        self.calls = []

    def request(self, path, raw):
        self.calls.append(path)
        body = json.loads(raw)
        try:
            result = self.chat.challenge(**body) if path == wire.PATHS[0] else self.chat.register(**body)
        except Rejected:
            raise wire.BridgeError('DENIED') from None
        if path == wire.PATHS[1] and not self.pending:
            result.update(status='active', node=self.node)
        return dict(status=200, data=json.dumps(result).encode())


class SyntheticNative:
    def __init__(self, api):
        self.api = api
        self.opens = []
        self.closed = threading.Event()
        self.hold = self.entered = None
        self.request_hold = self.request_entered = None

    @contextmanager
    def operation(self, cancel, deadline, **fields):
        if fields['action'] == 'request':
            reply = self.api.request(fields['path'], base64.b64decode(fields['data']))
            if self.request_entered is not None and fields['path'] == wire.PATHS[1]:
                self.request_entered.set()
                assert self.request_hold.wait(4)
            yield reply, None
            return
        self.opens.append(fields)
        local, remote = socket.socketpair()
        def peer():
            try:
                remote.settimeout(4)
                data = remote.recv(16384)
                remote.sendall(data.upper())
                remote.shutdown(socket.SHUT_WR)
            except OSError:
                pass
            finally:
                remote.close()
        thread = threading.Thread(target=peer)
        thread.start()
        try:
            if self.entered is not None:
                self.entered.set()
                assert self.hold.wait(4)
            yield {}, local
        finally:
            local.close()
            remote.close()
            thread.join(5)
            assert not thread.is_alive()
            self.closed.set()


@pytest.fixture
def integration(tmp_path):
    tmp_path.chmod(0o700)
    api = API(tmp_path)
    native = SyntheticNative(api)
    host = DirectHost(tmp_path / 'direct.sock', os.getuid(), native)
    host.start()
    direct = DirectBridge(api.device.reference, _paths=[host.endpoint], _root_uid=os.getuid())
    fallback = SimpleNamespace(request=lambda *args: pytest.fail('unexpected existing exit'),
                               open_mailbox=lambda *args: pytest.fail('unexpected existing exit'), close=lambda: None)
    key = secrets.token_bytes(32)
    ordinary = httpx.MockTransport(lambda _: pytest.fail('ordinary OS socket used'))
    friends = SimpleNamespace(_device=lambda _: api.device,
        http_factory=lambda: httpx.Client(base_url='https://invalid.example', transport=ordinary))
    owner = ChatOwner(tmp_path / 'store', friends, keyring=SimpleNamespace(key=lambda *args, **kwargs: key),
        runtime_factory=lambda _: SimpleNamespace(), events_fetcher=lambda _: [],
        restricted_factory=lambda _: fallback, direct_factory=lambda _: direct,
        mailbox_factory=lambda *args: SimpleNamespace(route=None, close=lambda: None, exchange=lambda **kwargs: {}))
    yield SimpleNamespace(api=api, host=host, direct=direct, owner=owner, native=native, fallback=fallback)
    owner.close()
    direct.close()
    host.close()
    assert not host.active


def enroll(integration):
    owner = integration.owner
    profile = owner.open(create=True)
    owner.tick(online=True, visible=True)
    assert owner.delivery_error is None and owner.node == integration.api.node
    return profile


def test_owner_proofs_direct_registration_proxy_half_close_and_encrypted_reopen(integration):
    profile = enroll(integration)
    with integration.direct.open_mailbox(time.monotonic() + 4, threading.Event()) as channel:
        assert channel.family == socket.AF_UNIX and not os.get_inheritable(channel.fileno())
        channel.sendall(b'private mailbox bytes')
        channel.shutdown(socket.SHUT_WR)
        assert channel.recv(16384) == b'PRIVATE MAILBOX BYTES'
        assert channel.recv(1) == b''
    assert integration.native.closed.wait(5)
    assert integration.native.opens == [dict(action='open', host='192.0.2.10', port=4242)]
    owner = integration.owner
    owner.close()
    integration.direct = DirectBridge(integration.api.device.reference, _paths=[integration.host.endpoint], _root_uid=os.getuid())
    owner.direct_factory = lambda _: integration.direct
    assert owner.open(create=False) == profile
    with integration.api.access.db() as database:
        assert database.execute('SELECT COUNT(*) FROM chat_challenges WHERE used=1').fetchone()[0] == 1
        assert database.execute('SELECT COUNT(*) FROM chat_bindings').fetchone()[0] == 1
        database.execute('UPDATE devices SET revoked=1')
    owner.next_enrollment = 0
    owner.tick(online=True, visible=True)
    assert owner.node is None
    assert integration.host.authority.revoked.is_set()


@pytest.mark.parametrize('change', ['host', 'port', 'public_key', 'expires_at', 'device', 'chat_public'])
def test_changed_authority_cannot_connect(integration, change):
    profile = enroll(integration)
    response = dict(device=integration.api.device.reference, chat_public=profile['public'], status='active', node=copy.deepcopy(integration.api.node))
    target = response if change in response else response['node']
    target[change] = 'forged'
    integration.direct.bind(response)
    with pytest.raises(wire.BridgeError, match='DENIED'):
        integration.direct.open_mailbox(time.monotonic() + 2, threading.Event())
    assert not integration.native.opens


@pytest.mark.parametrize('condition', ['expired', 'revoked', 'pending', 'replacement'])
def test_authority_lifetime_blocks_old_mailbox(integration, condition):
    profile = enroll(integration)
    authority = integration.host.authority
    if condition == 'expired':
        authority.clock = lambda: integration.api.node['expires_at']
    elif condition == 'revoked':
        authority.revoke()
    else:
        response = dict(device=integration.api.device.reference, chat_public=profile['public'], status='pending-node')
        if condition == 'replacement':
            response.update(status='active', node=dict(integration.api.node, sequence=2, port=4243))
        authority.registered(response['device'], profile['public'], json.dumps(response).encode())
    with pytest.raises(wire.BridgeError, match='DENIED'):
        integration.direct.open_mailbox(time.monotonic() + 2, threading.Event())
    assert not integration.native.opens


@pytest.mark.parametrize('field', ['url', 'host', 'port', 'resolver', 'interface', 'command', 'path_override'])
def test_extra_fields_rejected_before_native(integration, field):
    request = dict(schema=1, id=1, action='probe', device=integration.api.device.reference, budget_ms=1000)
    with socket.socket(socket.AF_UNIX) as channel:
        channel.connect(str(integration.host.endpoint))
        wire.write(channel, dict(request, **{field: 'attacker'}))
        assert not wire.read(channel, time.monotonic() + 2)['ok']
    assert not integration.api.calls and not integration.native.opens


def test_wrong_uid_and_device_fail_before_network(integration, monkeypatch):
    integration.host.authority.probe(integration.api.device.reference)
    other = DirectBridge('a'*32, _paths=[integration.host.endpoint], _root_uid=os.getuid())
    with pytest.raises(wire.BridgeError, match='DENIED'):
        other._select(time.monotonic() + 2)
    monkeypatch.setattr(chat_direct_host, 'peer_uid', lambda _: os.getuid() + 1)
    with pytest.raises((OSError, wire.BridgeError)):
        integration.direct._select(time.monotonic() + 2)
    assert not integration.api.calls


@pytest.mark.parametrize('field', ['host', 'url', 'command', 'interface', 'resolver'])
def test_body_overrides_are_rejected_at_root_not_only_in_client(integration, field):
    body = dict(public_identity=integration.api.device.public_identity,
                wireguard_public_key=integration.api.device.wireguard_public_key,
                chat_public=RNS.Identity().get_public_key().hex(), **{field: 'untrusted'})
    request = dict(schema=1, id=1, action='request', device=integration.api.device.reference, budget_ms=1000,
                   path=wire.PATHS[0], data=base64.b64encode(json.dumps(body).encode()).decode())
    with socket.socket(socket.AF_UNIX) as channel:
        channel.connect(str(integration.host.endpoint))
        wire.write(channel, request)
        assert wire.read(channel, time.monotonic()+2)['error'] == 'DENIED'
    assert not integration.api.calls and not integration.native.opens


@pytest.mark.parametrize('code', ['DENIED', 'CONFLICT', 'CANCELLED', 'DEADLINE', 'INVALID_RESPONSE'])
def test_direct_terminal_error_cannot_fall_back(code):
    def rejected(*args):
        raise wire.BridgeError(code)
    direct = SimpleNamespace(request=rejected, open_mailbox=rejected)
    fallback = SimpleNamespace(request=lambda *args: pytest.fail('terminal fallback'))
    with pytest.raises(FriendsError):
        with ChatHTTP(DirectHTTP(direct), fallback).stream('POST', wire.PATHS[0], json={}):
            pytest.fail('terminal reply')
    mailbox = object.__new__(ProtectedMailbox)
    mailbox.direct = direct
    with pytest.raises(_DirectDeadline if code == 'DEADLINE' else MailboxError) as failure:
        mailbox._direct(time.monotonic() + 1, threading.Event())
    assert str(failure.value) not in ('unavailable', 'timeout')
    if code in ('DENIED', 'CONFLICT', 'CANCELLED'):
        mailbox.bridge = direct
        with pytest.raises(MailboxError) as failure:
            mailbox._existing(time.monotonic()+1, threading.Event())
        assert str(failure.value) not in ('unavailable', 'timeout')


def test_established_direct_mailbox_deadline_is_timeout_without_next_route(monkeypatch):
    from messenger.mailbox import Mailbox
    mailbox = object.__new__(ProtectedMailbox)
    mailbox.closed, mailbox.expires = False, time.time()+30
    mailbox._route_lock = threading.Lock()
    def denied(*args):
        raise wire.BridgeError('DEADLINE')
    mailbox.direct = SimpleNamespace(open_mailbox=denied)
    mailbox.routes = (('DIRECT', mailbox._direct), ('EXISTING_EXIT', lambda *args: pytest.fail('deadline fallback')))
    monkeypatch.setattr(Mailbox, 'exchange', lambda self, *, timeout, cancel: self._selected[1](time.monotonic()+timeout, cancel))
    with pytest.raises(MailboxError, match='^timeout$'):
        mailbox.exchange()
    assert mailbox.attempted == ['DIRECT']


def test_direct_unavailable_preserves_existing_exit_not_system():
    def unavailable(*args):
        raise wire.BridgeError()
    used = []
    fallback = SimpleNamespace(request=lambda *args: (used.append('EXISTING_EXIT') or (200, b'{}')))
    with ChatHTTP(DirectHTTP(SimpleNamespace(request=unavailable)), fallback).stream('POST', wire.PATHS[0], json={}) as response:
        assert response.json() == {}
    assert used == ['EXISTING_EXIT'] and ProtectedMailbox.ROUTES == ('DIRECT', 'EXISTING_EXIT')


def test_cancelled_late_open_is_closed_without_descriptor(integration):
    enroll(integration)
    native = integration.native
    native.entered, native.hold = threading.Event(), threading.Event()
    cancel, finished = threading.Event(), threading.Event()
    failures = []
    def opening():
        try:
            integration.direct.open_mailbox(time.monotonic() + 4, cancel)
        except wire.BridgeError as error:
            failures.append(error.code)
        finally:
            finished.set()
    thread = threading.Thread(target=opening)
    thread.start()
    assert native.entered.wait(3)
    cancel.set()
    assert finished.wait(3)
    native.hold.set()
    thread.join(3)
    assert native.closed.wait(5) and failures == ['CANCELLED']


@pytest.mark.parametrize('cause', ['shutdown', 'replaced', 'disconnect'])
def test_live_proxy_cleanup_does_not_touch_vpn_owner(integration, cause):
    profile = enroll(integration)
    channel = integration.direct.open_mailbox(time.monotonic() + 4, threading.Event())
    try:
        if cause == 'shutdown':
            integration.host.close()
        elif cause == 'replaced':
            response = dict(device=integration.api.device.reference, chat_public=profile['public'], status='active',
                            node=dict(integration.api.node, sequence=2, port=4243))
            integration.host.authority.registered(response['device'], profile['public'], json.dumps(response).encode())
        else:
            channel.close()
        assert integration.native.closed.wait(5)
    finally:
        channel.close()


def test_pending_registration_never_constructs_mailbox(integration):
    integration.api.pending = True
    integration.owner.open(create=True)
    integration.owner.tick(online=True, visible=True)
    assert integration.owner.node is None and integration.owner.carrier is None
    assert not integration.native.opens


def test_direct_requires_explicit_existing_exit_boundary(tmp_path):
    with pytest.raises(ValueError, match='explicit existing-exit'):
        ChatOwner(tmp_path, None, direct_factory=DirectBridge)


@pytest.mark.parametrize('raw', [b'null', b'[]', b'1', b'{"status":"active"}', b'{"status":"active","status":"pending-node"}'])
def test_malformed_authenticated_registration_remains_terminal(integration, raw):
    with pytest.raises(wire.BridgeError, match='INVALID_RESPONSE'):
        integration.host.authority.registered(integration.api.device.reference, 'a'*128, raw)
    assert integration.host.authority.revoked.is_set()


def test_disconnected_registration_cannot_publish_late_authority(integration):
    integration.owner.open(create=True)
    native = integration.native
    native.request_entered, native.request_hold = threading.Event(), threading.Event()
    finished = threading.Event()
    def registering():
        try:
            integration.owner.tick(online=True, visible=True)
        finally:
            finished.set()
    thread = threading.Thread(target=registering)
    thread.start()
    assert native.request_entered.wait(3)
    integration.direct.close()
    assert finished.wait(3)
    native.request_hold.set()
    thread.join(3)
    integration.host.close()
    assert integration.host.authority.response is None and integration.owner.node is None


@pytest.mark.parametrize('change', ['sequence', 'equivocation', 'expiry', 'fields'])
def test_verified_server_response_still_checks_node_bounds_and_floor(integration, change):
    profile = enroll(integration)
    response = dict(device=integration.api.device.reference, chat_public=profile['public'], status='active', node=copy.deepcopy(integration.api.node))
    if change == 'sequence':
        response['node']['sequence'] = 0
    elif change == 'equivocation':
        response['node']['port'] += 1
    elif change == 'expiry':
        response['node']['expires_at'] = int(time.time()) + 3600
    else:
        response['node']['command'] = 'forbidden'
    with pytest.raises(wire.BridgeError, match='INVALID_RESPONSE'):
        integration.host.authority.registered(response['device'], profile['public'], json.dumps(response).encode())
    assert integration.host.authority.revoked.is_set()
