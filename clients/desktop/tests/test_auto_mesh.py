import base64
import json
from pathlib import Path
import sys
import threading
import time

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'linux'))
from auto_mesh import MeshCandidate, rejection
from auto_policy import Context, Failure
from mesh_materials import MaterialsError
from mesh_service import SessionFailure


def materials():
    return dict(identity=base64.b64encode(b'x' * 64).decode(), anchor=base64.b64encode(b'a' * 32).decode(),
                wireguard_public=base64.b64encode(b'w' * 32).decode(), profile='P1')


class Network:
    def __init__(self):
        self.actions = []
        self.record = dict(packet_index=0)
        self.owns_journal = False
        self.index, self.cleanup_fails = 2, False

    def prepare(self):
        self.actions.append('prepare')
        self.owns_journal = True

    def underlying(self):
        return self.index

    def attach(self):
        self.actions.append('attach-routes-dns')
        self.record['packet_index'] = 7

    def detach(self):
        self.actions.append('detach')
        self.record['packet_index'] = 0

    def verify_guard(self):
        self.actions.append('verify-guard')

    def cleanup(self):
        self.actions.append('cleanup')
        if self.cleanup_fails:
            raise RuntimeError('Synthetic cleanup failure')
        self.owns_journal = False


class Materials:
    summary = dict(stage='SYNTHETIC_UNIT_TEST_ONLY')

    def __init__(self):
        self.required, self.resolve_hook = [], lambda: None

    def resolve(self, value, underlying, cancel, deadline, required):
        assert underlying == 2 and time.monotonic() < deadline
        self.required.append(required)
        self.resolve_hook()
        return dict(identity=value['identity'], anchor=value['anchor'], profile=value['profile'], readiness={})


class Worker:
    def __init__(self, network):
        self.network, self.calls = network, []
        self.state, self.error = 'PACKET_READY', None
        self.routed_state, self.on_routed = 'CONNECTED', lambda: None

    def call(self, action, start=None):
        self.calls.append(action)
        if action == 'start':
            assert start['profile'] == 'P1' and start['underlying_index'] == 2
            assert 0 < start['budget_ms'] <= 200000
        if action == 'routed':
            assert self.network.record['packet_index'] == 7
            self.on_routed()
            self.state = self.routed_state
        return dict(ok=True, state=self.state, error=self.error, interface='fcmesh0', mtu=1280,
                    snapshot=dict(effective_profile='P1'))

    def close(self):
        self.calls.append('close')


@pytest.fixture
def setup():
    network, owner = Network(), Materials()
    workers = []

    def factory():
        worker = Worker(network)
        workers.append(worker)
        return worker

    current = MeshCandidate(network, owner, materials(), factory)
    return current, network, owner, workers


def test_same_packet_session_requires_routes_and_native_health(setup):
    current, network, owner, workers = setup
    assert current.prepare(Context(1000)) == dict(kind='mesh', interface='fcmesh0', endpoint=None, port=None)
    assert current.open(Context(2000)) == (7, False)
    assert workers[0].calls == ['start', 'routed']
    assert network.actions == ['prepare', 'attach-routes-dns', 'verify-guard']
    assert current.health(Context(1000)) is True
    view = current.snapshot()
    view['native']['effective_profile'] = 'Q1'
    assert current.snapshot()['native']['effective_profile'] == 'P1'
    assert 'identity' not in json.dumps(current.snapshot())
    current.close(Context(1000))
    assert workers[0].calls[-1] == 'close' and network.actions[-2:] == ['detach', 'cleanup']
    assert current.session is None and not network.owns_journal
    current.release(Context(1000))
    assert not current.materials
    with pytest.raises(ValueError):
        current.prepare(Context(1000))


@pytest.mark.parametrize('cleanup_fails', [False, True])
def test_process_reservation_spans_native_drain_and_network_cleanup(cleanup_fails):
    network, owner = Network(), Materials()
    class Gate:
        active = False
        def acquire(self, cancel, deadline):
            assert not network.actions
            self.active = True
            network.actions.append('reserve')
        def finish(self):
            assert self.active and not network.owns_journal and network.actions[-1] == 'cleanup'
            self.active = False
            network.actions.append('release')
    gate = Gate()
    class OwnedWorker(Worker):
        def close(self):
            assert gate.active
            network.actions.append('native-drained')
            super().close()
    current = MeshCandidate(network, owner, materials(), lambda passed: OwnedWorker(network), ownership=gate)
    assert current.open(Context(2000)) == (7, False)
    network.cleanup_fails = cleanup_fails
    if cleanup_fails:
        with pytest.raises(RuntimeError):
            current.close(Context(2000))
        assert gate.active and current.pending_cleanup
        network.cleanup_fails = False
    current.close(Context(2000))
    assert network.actions.index('native-drained') < network.actions.index('detach') < network.actions.index('cleanup')
    assert network.actions[-1] == 'release' and not gate.active


def test_new_attempt_only_after_owner_closes_previous_no_local_retries(setup):
    current, network, owner, workers = setup
    current.open(Context(2000))
    with pytest.raises(ValueError):
        current.open(Context(2000))
    workers[0].state, workers[0].error = 'FAILED', 'REMOTE_RESET'
    with pytest.raises(Failure, match='NETWORK'):
        current.health(Context(1000))
    assert current.attempt == 1 and len(workers) == 1
    current.close(Context(1000))
    current.open(Context(2000))
    assert current.attempt == 2 and owner.required == [True, False] and len(workers) == 2
    current.close(Context(1000))


def test_cancel_after_resolve_never_launches_native_packet_worker(setup):
    current, network, owner, workers = setup
    context = Context(2000)
    owner.resolve_hook = context.cancel.set
    with pytest.raises(Failure, match='CANCELLED'):
        current.open(context)
    assert not workers and current.pending_cleanup
    current.close(Context(1000))
    assert not network.owns_journal


def test_outer_deadline_applies_before_native_start(setup, monkeypatch):
    current, network, owner, workers = setup
    context = Context(2000)
    expired = context.deadline + 1
    owner.resolve_hook = lambda: monkeypatch.setattr(time, 'monotonic', lambda: expired)
    with pytest.raises(Failure, match='NETWORK'):
        current.open(context)
    assert not workers
    current.close(Context(1000))


@pytest.mark.parametrize('failure', ['FAMILY_REJECTED', 'RELIABLE_PROTOCOL', 'private-token-and-url'])
def test_terminal_packet_failure_does_not_reconnect_or_leak_details(setup, failure):
    current, network, owner, workers = setup
    worker = Worker(network)
    worker.state, worker.error = 'FAILED', failure
    current.worker_factory = lambda: worker
    expected = 'INTERNAL' if failure == 'RELIABLE_PROTOCOL' else 'AUTH'
    with pytest.raises(Failure, match=expected):
        current.open(Context(2000))
    assert worker.calls == ['start'] and current.attempt == 1
    assert current.pending_cleanup and 'cleanup' not in network.actions
    current.close(Context(1000))


def test_packet_ready_is_not_connected_and_cancelled_routed_cannot_publish_ready(setup):
    current, network, owner, workers = setup
    context = Context(2000)
    worker = Worker(network)
    worker.on_routed = context.cancel.set
    current.worker_factory = lambda: worker
    with pytest.raises(Failure, match='CANCELLED'):
        current.open(context)
    assert 'routed' in worker.calls and network.record['packet_index'] == 7
    current.close(Context(1000))


def test_underlying_change_is_a_single_attempt_loss(setup):
    current, network, owner, workers = setup
    current.open(Context(2000))
    network.index = 3
    with pytest.raises(Failure, match='NETWORK'):
        current.health(Context(1000))
    assert current.attempt == 1
    current.close(Context(1000))


def test_failed_cleanup_prevents_new_attempt_or_secret_release(setup):
    current, network, owner, workers = setup
    current.open(Context(2000))
    network.cleanup_fails = True
    with pytest.raises(RuntimeError):
        current.close(Context(1000))
    with pytest.raises(ValueError):
        current.prepare(Context(1000))
    with pytest.raises(ValueError):
        current.release(Context(1000))
    assert current.pending_cleanup and current.materials and len(workers) == 1
    network.cleanup_fails = False
    current.close(Context(1000))
    current.release(Context(1000))


@pytest.mark.parametrize('code,category,temporary', [
    ('AUTHORIZATION_REJECTED', 'AUTH', False), ('NATIVE_VALIDATION_FAILED', 'AUTH', False),
    ('EXPIRED_ON_IMPORT', 'AUTH', False), ('BOOTSTRAP_VALIDATION_FAILED', 'AUTH', False),
    ('FETCH_NETWORK_FAILURE', 'BOOTSTRAP_UNAVAILABLE', True),
    ('CHALLENGE_TEMPORARY_SERVER_FAILURE', 'BOOTSTRAP_UNAVAILABLE', True),
    ('CANCELLED', 'CANCELLED', False), ('PERSISTENCE_FAILED', 'INTERNAL', False),
    ('INVALID_MATERIALS_COMMAND', 'INTERNAL', False), ('SECRET_TOKEN', 'INTERNAL', False)])
def test_material_failures_are_bounded_and_authorization_never_temporary(code, category, temporary):
    observed = rejection(MaterialsError(code))
    assert observed.category == category and observed.temporary == temporary
    assert str(observed) == category


def test_private_material_is_copied_not_cloned_or_mutated(setup):
    current, network, owner, workers = setup
    original = materials()
    second = MeshCandidate(network, owner, original)
    second.release(Context(1000))
    assert original == materials()
    with pytest.raises(ValueError):
        MeshCandidate(network, owner, dict(original, profile='Q1'))


def test_diagnostic_read_does_not_wait_for_connecting_candidate(setup):
    current, network, owner, workers = setup
    finished = threading.Event()
    with current.lock:
        reader = threading.Thread(target=lambda: (current.snapshot(), finished.set()))
        reader.start()
        assert finished.wait(.5)
    reader.join(timeout=.5)
    assert not reader.is_alive()
