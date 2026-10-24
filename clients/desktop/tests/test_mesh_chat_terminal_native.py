from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
import base64
import json
import threading
import time

import pytest

from test_mesh_chat_lifetime_native import authenticated, pytestmark
from mesh_chat import ChatError
from mesh_ownership import Ownership, OwnershipError
from messenger.admission import message
from provisioning import chat_bridge_protocol as wire


def material(fixture):
    return dict(device=fixture.device.reference,
                identity=base64.b64encode(fixture.device._identity.get_private_key()).decode(),
                wireguard_public=fixture.device.wireguard_public_key)


@contextmanager
def held_watcher(fixture, monkeypatch):
    entered, resume = threading.Event(), threading.Event()
    original = fixture.owner.underlying.read
    def read(context):
        if threading.current_thread() is fixture.owner.watcher:
            entered.set()
            assert resume.wait(10)
        return original(context)
    monkeypatch.setattr(fixture.owner.underlying, 'read', read)
    assert entered.wait(3)
    try:
        yield
    finally:
        resume.set()


def exchange(fixture, mailbox=True):
    identity = fixture.chat_identity
    public = identity.get_public_key().hex()
    body = dict(public_identity=fixture.device.public_identity, wireguard_public_key=fixture.device.wireguard_public_key,
                chat_public=public)
    status, raw = fixture.bridge.request(wire.PATHS[0], json.dumps(body).encode(), 5)
    assert status == 200 and fixture.bridge.route == 'SERVICE_ONLY'
    challenge = json.loads(raw)['challenge']
    registration = dict(proof=fixture.device.prove_transport_key(challenge), chat_public=public,
                        chat_signature=identity.sign(message(public, fixture.device.reference, challenge)).hex())
    assert fixture.bridge.request(wire.PATHS[1], json.dumps(registration).encode(), 5)[0] == 200
    if mailbox:
        with fixture.bridge.open_service_mailbox(time.monotonic() + 5, threading.Event()) as channel:
            channel.settimeout(3)
            assert channel.recv(9) == b'from-peer'
            channel.sendall(b'to-peer')
            assert channel.recv(7) == b'to-peer'


@pytest.mark.parametrize('failure', ['peer', 'bootstrap'])
def test_terminal_generation_recovers(authenticated, monkeypatch, failure):
    fixture = authenticated
    fixture.events.peer.clear()
    if failure == 'bootstrap':
        fixture.events.bootstrap.clear()
        fixture.owner.prepare(material(fixture), threading.Event(), time.monotonic() + 5)
        fixture.events.until('bootstrap')
    else:
        exchange(fixture, mailbox=False)
    old = fixture.owner.current
    readiness, network = dict(old.material['readiness']), dict(fixture.owner.network)
    assert readiness['expires_at'] > time.time()
    lease = fixture.owner.generation_lease
    worker = fixture.workers[0]
    assert worker.chat.call('route', lease=lease)['route'] == ('CONNECTING' if failure == 'bootstrap' else 'SERVICE_ONLY')
    with held_watcher(fixture, monkeypatch):
        if failure == 'bootstrap':
            fixture.events.fail_bootstrap = True
            fixture.events.bootstrap.set()
            fixture.events.until('drained')
            fixture.events.fail_bootstrap = False
        else:
            fixture.events.fail_peer = True
            fixture.events.peer.set()
            fixture.events.until_all('peer_closed', 'terminal')
        assert worker.chat.call('route', lease=lease)['route'] == 'UNAVAILABLE'
        touched = fixture.owner.touched
        returned = fixture.owner.binding()
        if returned is old:
            assert fixture.owner.touched > touched
            assert fixture.owner.prepare(material(fixture), threading.Event(), time.monotonic() + 5) is old
            if failure == 'bootstrap':
                fixture.events.fail_peer = False
                identity = fixture.chat_identity
                public = identity.get_public_key().hex()
                body = dict(public_identity=fixture.device.public_identity,
                            wireguard_public_key=fixture.device.wireguard_public_key,
                            chat_public=public)
                status, raw = fixture.bridge.request(wire.PATHS[0], json.dumps(body).encode(), 5)
                assert status == 200
                challenge = json.loads(raw)['challenge']
                registration = dict(proof=fixture.device.prove_transport_key(challenge), chat_public=public,
                    chat_signature=identity.sign(message(public, fixture.device.reference, challenge)).hex())
                fixture.events.until('cleanup_entered')
                assert fixture.owner.generation_lease == lease
                assert worker.chat.call('route', lease=lease)['route'] == 'UNAVAILABLE'
                with pytest.raises(wire.BridgeError, match='UNAVAILABLE') as error:
                    fixture.bridge.request(wire.PATHS[1], json.dumps(registration).encode(), 3)
                print('BEFORE bootstrap: valid register error=', error.value.code)
            print('BEFORE', failure, 'stale_binding=True touched_renewed=True generation_lease_retained=True',
                  'opens=', fixture.events.history.count('open'), 'events=', fixture.events.history)
        assert returned is None
        assert fixture.owner.touched == touched
    fixture.events.cleanup.set()
    worker.process.wait(5)
    with fixture.owner.lock:
        assert fixture.owner.current is None and fixture.owner.gate is None
    fixture.events.fail_peer = False
    exchange(fixture)
    assert fixture.owner.current is not old and len(fixture.workers) == 2
    assert fixture.owner.current.material['readiness'] == readiness and fixture.owner.network == network
    assert fixture.events.history.count('open') == 2
    assert fixture.events.history.count('authenticated') == (1 if failure == 'bootstrap' else 2)
    assert fixture.owner.worker.chat.call('route', lease=fixture.owner.generation_lease)['route'] == 'SERVICE_ONLY'
    print('AFTER', failure, 'fresh_generation=True opens=2 authenticated_exchange=True')


def test_operation_pin_at_bootstrap_failure_boundary(authenticated, monkeypatch):
    fixture = authenticated
    fixture.events.bootstrap.clear()
    fixture.owner.prepare(material(fixture), threading.Event(), time.monotonic() + 5)
    fixture.events.until('bootstrap')
    binding, lease = fixture.owner.current, fixture.owner.generation_lease
    entered, resume = threading.Event(), threading.Event()
    original = binding.lane.call
    def call(action, **values):
        if action == 'acquire':
            assert values['generation'] == lease
            entered.set()
            assert resume.wait(8)
        return original(action, **values)
    monkeypatch.setattr(binding.lane, 'call', call)
    with ThreadPoolExecutor(1) as executor, held_watcher(fixture, monkeypatch):
        binding.probe(fixture.device.reference)
        operation = executor.submit(binding.acquire, fixture.device.reference, threading.Event(), 5000)
        try:
            assert entered.wait(3)
            fixture.events.fail_bootstrap = True
            fixture.events.bootstrap.set()
            fixture.events.until('drained')
            assert original('route', lease=lease)['route'] == 'UNAVAILABLE'
            fixture.events.fail_bootstrap = False
            resume.set()
            with pytest.raises(ChatError, match='UNAVAILABLE'):
                operation.result(3)
            assert fixture.events.history.count('open') == 1
            assert fixture.events.history.count('leases:2') == 0
            assert binding.closed.is_set() and fixture.owner.gate.active
            assert not fixture.api_calls
        finally:
            resume.set()
    fixture.workers[0].process.wait(5)
    with fixture.owner.lock:
        assert fixture.owner.current is None
    fixture.events.cleanup.set()
    exchange(fixture)
    assert fixture.events.history.count('open') == 2


@pytest.mark.parametrize('phase', ['acquire', 'request'])
def test_late_result_cannot_touch_replacement_or_replay(authenticated, monkeypatch, phase):
    fixture = authenticated
    fixture.events.peer.clear()
    exchange(fixture, mailbox=False)
    binding, gate, worker = fixture.owner.current, fixture.owner.gate, fixture.workers[0]
    original = binding.lane.call
    entered, resume = threading.Event(), threading.Event()
    def call(action, **values):
        result = original(action, **values)
        if action == phase:
            entered.set()
            assert resume.wait(10)
        return result
    monkeypatch.setattr(binding.lane, 'call', call)
    body = dict(public_identity=fixture.device.public_identity, wireguard_public_key=fixture.device.wireguard_public_key,
                chat_public=fixture.chat_identity.get_public_key().hex())
    before = len(fixture.api_calls)
    with ThreadPoolExecutor(2) as executor:
        pending = executor.submit(fixture.bridge.request, wire.PATHS[0], json.dumps(body).encode(), 15)
        try:
            assert entered.wait(3)
            fixture.events.fail_peer = True
            fixture.events.peer.set()
            fixture.events.until_all('peer_closed', 'terminal', 'cleanup_entered')
            assert gate.active and (fixture.directory / 'transport.lock').read_bytes() == b'chat'
            assert binding.closed.is_set()
            with pytest.raises(wire.BridgeError):
                fixture.owner.prepare(material(fixture), threading.Event(), time.monotonic() + .2)
            vpn = Ownership('vpn', fixture.directory)
            reserved = threading.Event()
            class ReservationSignal(threading.Event):
                def wait(self, timeout=None):
                    reserved.set()
                    return super().wait(timeout)
            reservation = executor.submit(vpn.acquire, ReservationSignal(), time.monotonic() + 5)
            try:
                assert reserved.wait(2)
                assert not reservation.done() and fixture.events.history.count('open') == 1
                with pytest.raises(OwnershipError, match='VPN_RESERVED|OWNER_BUSY'):
                    Ownership('chat', fixture.directory).acquire(threading.Event(), time.monotonic() + .2)
                fixture.events.cleanup.set()
                worker.process.wait(5)
                reservation.result(3)
                assert vpn.active and not gate.active
            finally:
                if vpn.active:
                    vpn.finish()
            with fixture.owner.lock:
                assert fixture.owner.current is None
            fixture.events.fail_peer = False
            assert len(fixture.api_calls) == before + (phase == 'request')
            exchange(fixture)
            fresh, fresh_lease = fixture.owner.current, fixture.owner.generation_lease
            touched = fixture.owner.touched
            resume.set()
            with pytest.raises(wire.BridgeError, match='CANCELLED|UNAVAILABLE'):
                pending.result(3)
            assert fixture.owner.current is fresh and not fresh.cancelled.is_set()
            assert fixture.owner.touched == touched and fixture.owner.generation_lease == fresh_lease
            assert fresh.lane.call('route', lease=fresh_lease)['route'] == 'SERVICE_ONLY'
            assert len(fixture.api_calls) == before + (phase == 'request') + 2
            assert fixture.events.history.count('open') == 2
        finally:
            fixture.events.cleanup.set()
            resume.set()
