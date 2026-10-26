import base64
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import select
import socketserver
import struct
import subprocess
import sys
import threading
import time

import pytest

from test_mesh_chat_lifetime_native import authenticated
from mesh_chat_host import Host
from mesh_chat_service import ServiceHost
from mesh_ownership import Ownership
from mesh_service import Supervisor
from mesh_system import Network
import mesh_service
from auto_configuration import NormalOwner
from auto_guard import Guard
from auto_mesh import MeshCandidate
from auto_platform import Platform
from auto_runtime import Coordinator
from mesh_materials import CacheStore
from mesh_chat import ChatError
from provisioning import chat_bridge_protocol as wire
from control.friends.restricted_admin import grant, publish_crl
from test_friends_restricted import proof

pytestmark = pytest.mark.skipif(os.geteuid() != 0 or os.environ.get('FC_L022_ISOLATED') != 'yes',
                                reason='disposable container with private D-Bus/resolved and network required')


def wait_until(check, timeout=15):
    deadline = time.monotonic() + timeout
    while not check():
        assert time.monotonic() < deadline, 'bounded state observation deadline'
        threading.Event().wait(.02)


class User:
    def __init__(self, fixture, service, vpn):
        script = Path(__file__).resolve().parents[3] / 'tests/fixtures/mesh_combined/user_peer.py'
        self.process = subprocess.Popen([sys.executable, str(script)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, text=True, user=1000, group=1000, extra_groups=())
        config = dict(identity=base64.b64encode(fixture.device._identity.get_private_key()).decode(),
                      wireguard_private=base64.b64encode(fixture.device._wireguard_key.private_bytes_raw()).decode(),
                      service=str(service), vpn=str(vpn))
        self.process.stdin.write(json.dumps(config) + '\n')
        self.process.stdin.flush()

    def call(self, action, **fields):
        self.process.stdin.write(json.dumps(dict(action=action, **fields)) + '\n')
        self.process.stdin.flush()
        assert select.select([self.process.stdout], [], [], 18)[0], 'user IPC deadline'
        response = self.process.stdout.readline()
        assert response, self.process.stderr.read()
        return json.loads(response)

    def close(self):
        self.process.stdin.close()
        self.process.wait(5)
        assert self.process.returncode == 0, self.process.stderr.read()


@pytest.fixture
def combined(authenticated, monkeypatch):
    fixture = authenticated
    race_path = fixture.settings.parent / 'native-race'
    monkeypatch.setitem(mesh_service.ENV, 'GORACE', 'log_path=' + str(race_path))
    original_worker = mesh_service.NativeWorker
    class ObservedWorker(original_worker):
        def call(self, action, start=None):
            result = super().call(action, start)
            if action == 'stop':
                print('NATIVE STOP:', result.get('ok'), result.get('state'), result.get('error'))
            return result
        def close(self):
            try:
                return super().close()
            except Exception:
                print('NATIVE CLOSE FAILED:', self.process.returncode)
                if self.process.returncode == 66:
                    print(race_path.with_name(race_path.name + '.' + str(self.process.pid)).read_text())
                raise
    monkeypatch.setattr(mesh_service, 'NativeWorker', ObservedWorker)
    queries = []
    class DNS(socketserver.StreamRequestHandler):
        def handle(self):
            length = struct.unpack('!H', self.rfile.read(2))[0]
            query = self.rfile.read(length)
            queries.append(query)
            reply = query[:2] + b'\x81\x83' + query[4:]
            self.wfile.write(struct.pack('!H', len(reply)) + reply)
    class DNSServer(socketserver.ThreadingTCPServer):
        allow_reuse_address = True
    dns = DNSServer(('127.0.0.2', 53), DNS)
    dns_thread = threading.Thread(target=dns.serve_forever)
    dns_thread.start()
    settings = json.loads(fixture.settings.read_text())
    gateway = fixture.settings.with_name('gateway.json')
    gateway.write_text(json.dumps(settings['gateway']))
    gateway.chmod(0o600)
    settings['gateway_path'] = str(gateway)
    fixture.settings.write_text(json.dumps(settings))
    fixture.host.close()
    endpoints = Path('/run') / ('fc-l022-ipc-' + fixture.settings.parent.name)
    endpoints.mkdir(mode=0o711)
    service = ServiceHost(endpoints / 'service.sock', 1000, fixture.owner)
    service.start()
    fixture.user = User(fixture, service.endpoint, endpoints / 'vpn.sock')
    fixture.endpoints, fixture.queries, fixture.gateway = endpoints, queries, gateway
    try:
        yield fixture
    finally:
        fixture.events.cleanup.set()
        fixture.user.close()
        service.close()
        dns.shutdown()
        dns.server_close()
        dns_thread.join(3)


def vpn_material(fixture):
    return dict(identity=base64.b64encode(fixture.device._identity.get_private_key()).decode(),
                wireguard_public=fixture.device.wireguard_public_key, anchor=fixture.owner.anchor, profile='P0')


def leases(fixture, expected):
    wait_until(lambda: next((value for value in reversed(fixture.events.history) if value.startswith('leases:')), None) == 'leases:' + str(expected), 3)


def kernel_resources():
    return [subprocess.check_output(command, timeout=3) for command in (
        ['ip', '-j', 'route', 'show', 'table', 'all'], ['ip', '-j', 'rule', 'show'], ['resolvectl', 'dns'])]


def late_acquire(fixture, monkeypatch, executor):
    binding = fixture.owner.current
    entered, resume = threading.Event(), threading.Event()
    original = binding.lane.call
    def call(action, **values):
        result = original(action, **values)
        if action == 'acquire' and not entered.is_set():
            entered.set()
            assert resume.wait(60)
        return result
    monkeypatch.setattr(binding.lane, 'call', call)
    result = executor.submit(binding.acquire, fixture.device.reference, threading.Event(), 3000)
    assert entered.wait(3)
    return resume, result


def denied_demand(fixture):
    calls, opens = len(fixture.api_calls), fixture.events.history.count('open')
    result = fixture.user.call('exchange', route='SERVICE_ONLY')
    assert result.get('error') in ('UNAVAILABLE', 'CANCELLED', 'BUSY_OR_UNAVAILABLE'), result
    assert len(fixture.api_calls) == calls and fixture.events.history.count('open') == opens


def profile_mismatch(fixture, binding):
    previous = binding.material['readiness']
    gateway = json.loads(fixture.gateway.read_text())
    grant(fixture.authority.access, fixture.device.reference, gateway['family'], previous['expires_at'], 3)
    different = fixture.authority.fetch(proof(fixture.authority, fixture.device))
    assert different != previous
    assert different['device'] == previous['device'] and different['issuer'] == previous['issuer']
    calls, opens = len(fixture.api_calls), fixture.events.history.count('open')
    with pytest.raises(ChatError, match='UNAVAILABLE'):
        binding.lane.call('acquire', acquire=dict(binding.material, readiness=different), budget_ms=3000)
    assert len(fixture.api_calls) == calls and fixture.events.history.count('open') == opens
    lease = binding.acquire(fixture.device.reference, threading.Event(), 3000)
    assert binding.lane.call('route', lease=lease)['route'] == 'EXISTING_EXIT'
    binding.release(lease)


def finish_late(fixture, resume, result, binding):
    resume.set()
    with pytest.raises((ChatError, wire.BridgeError)) as failure:
        result.result(3)
    assert failure.value.code in ('UNAVAILABLE', 'CANCELLED')
    assert binding.ready.is_set() and not binding.closed.is_set()
    assert fixture.events.history.count('open') == 2


def stopped_with_held_cleanup(fixture, stop, gate, executor):
    count = fixture.events.history.count('cleanup_entered')
    fixture.events.cleanup.clear()
    stopping = executor.submit(stop)
    try:
        wait_until(lambda: fixture.events.history.count('cleanup_entered') > count, 5)
        assert fixture.user.call('eof')['ok']
        assert gate.active and (fixture.directory / 'transport.lock').read_bytes() == b'vpn'
        denied_demand(fixture)
        assert fixture.owner.current is None and not stopping.done()
    finally:
        fixture.events.cleanup.set()
    stopping.result(15)


def short_readiness(fixture):
    gateway = json.loads(fixture.gateway.read_text())
    grant(fixture.authority.access, fixture.device.reference, gateway['family'], int(time.time()) + 12, 4)
    response = fixture.authority.fetch(proof(fixture.authority, fixture.device))
    fixture.owner.materials.storage.write(json.dumps(dict(response=response, denied=False, next_attempt=int(time.time()) + 300)).encode())
    return response['expires_at']


def terminal_mailbox(fixture, reason, expiry=None):
    calls = len(fixture.api_calls)
    assert fixture.user.call('denied') == dict(ok=False, error='DENIED')
    assert len(fixture.api_calls) == calls + 1
    binding, worker, gate = fixture.owner.current, fixture.workers[-1], fixture.owner.gate
    terminal = fixture.events.history.count('terminal')
    assert fixture.user.call('open')['ok']
    if reason == 'revocation':
        with fixture.authority.access.db() as database:
            database.execute('UPDATE restricted_grants SET revoked=1 WHERE device=?', (fixture.device.reference,))
        publish_crl(fixture.authority, fixture.settings.parent / 'revocations.pem')
        gateway = json.loads(fixture.gateway.read_text())
        gateway['revocations'] = fixture.authority.crl_source().decode()
        pending = fixture.gateway.with_suffix('.pending')
        pending.write_text(json.dumps(gateway))
        pending.chmod(0o600)
        pending.replace(fixture.gateway)
    assert fixture.user.call('drain')['ok']
    wait_until(lambda: fixture.owner.current is None and not gate.active, 8)
    assert binding.closed.is_set() and worker.process.returncode == 0
    assert fixture.events.history.count('terminal') > terminal
    assert fixture.events.history.count('open') == 3 and len(fixture.api_calls) == calls + 1
    assert fixture.events.history.count('broker_drained') == 3
    assert fixture.events.history.count('cleaned') == 3
    leases(fixture, 0)
    if expiry is not None:
        assert time.time() >= expiry
    print('TERMINAL', reason, ': active mailbox cancelled; three owners drained; no HTTP replay')


def test_manual_authenticated_off_on_off(combined, monkeypatch):
    fixture = combined
    assert fixture.user.call('exchange', route='SERVICE_ONLY')['ok']
    leases(fixture, 1)
    resources = kernel_resources()
    old, old_worker, old_gate = fixture.owner.current, fixture.workers[0], fixture.owner.gate
    assert fixture.owner.generation_lease is not None and fixture.events.history.count('open') == 1
    assert not Path('/sys/class/net/fcmesh0').exists()
    network = Network(fixture.settings.parent / 'manual.json', 1000)
    gate = Ownership('vpn', fixture.directory)
    supervisor = Supervisor(network, fixture.owner.materials, gate)
    host = Host(fixture.endpoints / 'vpn.sock', 1000, supervisor.chat_binding)
    host.start()
    executor = ThreadPoolExecutor(2)
    resume, late = late_acquire(fixture, monkeypatch, executor)
    try:
        assert supervisor.start(vpn_material(fixture))
        fixture.events.until_all('leases:0', 'cleanup_entered')
        assert old.closed.is_set() and old_gate.active and not gate.active
        assert (fixture.directory / 'transport.lock').read_bytes() == b'chat'
        assert fixture.events.history.count('open') == 1 and supervisor.session is None
        denied_demand(fixture)
        fixture.events.cleanup.set()
        old_worker.process.wait(5)
        wait_until(lambda: supervisor.status()['state'] in ('CONNECTED', 'FAILED'), 30)
        assert supervisor.status()['state'] == 'CONNECTED', supervisor.status()
        assert gate.active and not old_gate.active
        assert old_worker.process.returncode == 0
        assert network.record['packet_index'] > 0 and fixture.queries
        assert supervisor.status()['native']['health']['probe_ok']
        assert supervisor.session.chat_binding.ready.is_set()
        finish_late(fixture, resume, late, supervisor.session.chat_binding)
        profile_mismatch(fixture, supervisor.session.chat_binding)
        response = fixture.user.call('exchange', route='EXISTING_EXIT')
        assert response['ok'], response
        assert fixture.owner.current is None and fixture.events.history.count('open') == 2
        leases(fixture, 0)
        fixture.events.until('broker_extended')
        assert fixture.user.call('open')['ok']
        worker = supervisor.session.worker
        stopped_with_held_cleanup(fixture, supervisor.stop, gate, executor)
        assert supervisor.status()['state'] == 'DISCONNECTED', (supervisor.status(), fixture.events.history)
        assert worker.process.returncode == 0 and not gate.active and not network.owns_journal
        assert not Path('/sys/class/net/fcmesh0').exists()
        assert kernel_resources() == resources
        assert fixture.user.call('exchange', route='SERVICE_ONLY')['ok']
        leases(fixture, 1)
        assert fixture.events.history.count('open') == 3
        assert fixture.owner.current is not old and fixture.owner.generation_lease is not None
        print('MANUAL OFF/ON/OFF: SERVICE_ONLY -> CONNECTED/EXISTING_EXIT -> SERVICE_ONLY; opens=3; DNS=', len(fixture.queries))
        terminal_mailbox(fixture, 'revocation')
    finally:
        resume.set()
        fixture.events.cleanup.set()
        supervisor.stop()
        host.close()
        executor.shutdown()


def test_auto_authenticated_off_on_off(combined, monkeypatch):
    fixture = combined
    assert fixture.user.call('exchange', route='SERVICE_ONLY')['ok']
    leases(fixture, 1)
    resources = kernel_resources()
    old, old_worker, old_gate = fixture.owner.current, fixture.workers[0], fixture.owner.gate
    assert fixture.owner.generation_lease is not None and fixture.events.history.count('open') == 1
    guard = Guard(1000, '1234567890abcdef1234567890abcdef')
    cache = fixture.settings.parent / 'normal'
    cache.mkdir(mode=0o700)
    storage = CacheStore(cache, 1000)
    network = Network(guard.directory / 'mesh.json', 1000, auto_guard=guard)
    gate = Ownership('vpn', fixture.directory)
    mesh = MeshCandidate(network, fixture.owner.materials, vpn_material(fixture), ownership=gate)
    material = dict(vpn_material(fixture), wireguard_private=base64.b64encode(fixture.device._wireguard_key.private_bytes_raw()).decode(),
                    country='nl', normal_floors=[])
    platform = Platform(guard, NormalOwner(storage), mesh, material)
    runtime = Coordinator(guard, platform, 1, worker=os.environ['FC_L021_WORKER'])
    host = Host(fixture.endpoints / 'vpn.sock', 1000, mesh.chat_binding)
    host.start()
    executor = ThreadPoolExecutor(2)
    resume, late = late_acquire(fixture, monkeypatch, executor)
    try:
        runtime.start(preferred='restricted')
        wait_until(lambda: 'cleanup_entered' in fixture.events.history or runtime.status()['policy']['state'] == 'FAILED', 40)
        assert 'cleanup_entered' in fixture.events.history, runtime.status()
        fixture.events.until_all('leases:0', 'cleanup_entered')
        assert old.closed.is_set() and old_gate.active and not gate.active
        assert fixture.events.history.count('open') == 1 and mesh.session is None
        denied_demand(fixture)
        fixture.events.cleanup.set()
        old_worker.process.wait(5)
        wait_until(lambda: runtime.status()['policy']['state'] in ('CONNECTED', 'FAILED'), 35)
        assert runtime.status()['policy']['state'] == 'CONNECTED', runtime.status()
        assert gate.active and not old_gate.active and old_worker.process.returncode == 0
        assert network.record['packet_index'] > 0 and fixture.queries
        assert mesh.snapshot()['native']['health']['probe_ok']
        assert platform.selection_snapshot()['applied']['transport'] == 'restricted'
        with mesh.lock:
            binding = mesh.session.chat_binding
        finish_late(fixture, resume, late, binding)
        profile_mismatch(fixture, binding)
        response = fixture.user.call('exchange', route='EXISTING_EXIT')
        assert response['ok'], response
        assert fixture.owner.current is None and fixture.events.history.count('open') == 2
        leases(fixture, 0)
        fixture.events.until('broker_extended')
        assert fixture.user.call('open')['ok']
        worker = mesh.session.worker
        stopped_with_held_cleanup(fixture, runtime.close, gate, executor)
        assert runtime.status()['policy']['state'] == 'DISCONNECTED'
        assert worker.process.returncode == 0 and not gate.active and not network.owns_journal
        assert guard.record is None and guard.system.read() is None
        assert not Path('/sys/class/net/fcmesh0').exists()
        assert kernel_resources() == resources
        expiry = short_readiness(fixture)
        assert fixture.user.call('exchange', route='SERVICE_ONLY')['ok']
        leases(fixture, 1)
        assert fixture.events.history.count('open') == 3
        assert fixture.owner.current is not old and fixture.owner.generation_lease is not None
        print('AUTO OFF/ON/OFF: SERVICE_ONLY -> CONNECTED/EXISTING_EXIT -> SERVICE_ONLY; opens=3; DNS=', len(fixture.queries))
        terminal_mailbox(fixture, 'expiry', expiry)
    finally:
        resume.set()
        fixture.events.cleanup.set()
        runtime.close()
        host.close()
        guard.close()
        storage.close()
        executor.shutdown()
