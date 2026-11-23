from copy import deepcopy
import json
import sqlite3
import time
from types import SimpleNamespace

import pytest

from control.friends import paid_beta, transport_membership, transport_policy as policy
from control.friends.enrollment_postgres import PostgresEnrollment
from control.friends.paid_postgres import PostgresPaidTransaction
from control.friends.transport_gateway import Gateway, write
from test_paid_repository import NOW, activate, event, new_store, parallel, rows
from test_transport_enforcement import make_engine


class Fleet:
    def __init__(self, access, root, monkeypatch):
        self.access = access
        self.device, self.support = activate(access)
        self.other, self.other_support = activate(access)
        self.current = [NOW]
        access.clock = lambda: self.current[0]
        self.nodes, self.calls = {}, []
        self.hook = self.prepare
        for node in policy.NODES:
            directory = root / node
            directory.mkdir()
            initial = self.envelope(node)['decisions']
            initial = next(record for record in initial if record['device'] == self.device.reference)
            self.nodes[node] = make_engine(directory, initial, node=node, current=self.current)
        if access.path is None:
            access.enrollment_repository.membership_exchange = self.exchange
        else:
            write(access.path.parent / 'transport-enforcement.json', dict(schema=1, profile=policy.PROFILE,
                enabled=True, hosts={node: node for node in policy.NODES}))
            write(access.path.parent / 'transport-commands.json', {node: ['synthetic-node', node] for node in policy.NODES})

            def call(command, *, input, capture_output, timeout, check):
                assert command[0] == 'synthetic-node' and capture_output and check and timeout == 12
                return SimpleNamespace(stdout=self.exchange(command[1], json.loads(input)))

            monkeypatch.setattr(transport_membership.subprocess, 'run', call)
        self.reconcile()

    def envelope(self, node):
        with self.access.enrollment() as transaction:
            return policy.read_snapshot(transaction.paid(), node, self.current[0])

    def exchange(self, node, request):
        self.calls.append((node, deepcopy(request)))
        assert request['operation'] == 'prepare' and request['paid']['node'] == node
        assert len(request['paid']['decisions']) == 1
        assert request['paid']['decisions'][0]['device'] == self.device.reference
        assert request['paid']['decisions'][0]['cohort'] is False
        return self.hook(node, request)

    def prepare(self, node, request):
        gateway = self.nodes[node][0]
        with gateway.serialized():
            with gateway.lock():
                gateway.prepare(request['paid'], request['token'])
            gateway.apply_serialized()
        self.fenced([node])
        return json.dumps(dict(schema=1, node=node, result='prepared', token=request['token'])).encode()

    def fenced(self, nodes):
        for node in nodes:
            gateway, current, live, initial = self.nodes[node]
            assert gateway.load()['records'][self.device.reference]['prepared']
            assert not gateway.peer_allowed(initial['public_key'])
            assert initial['public_key'] not in live['awg']
            assert initial['tcp_id'] not in {client['id'] for client in live['tcp']}
            assert 'foreign-key' in live['awg']
            assert 'foreign' in {client['id'] for client in live['tcp']}
            other = gateway.load()['records'][self.other.reference]
            assert other['prepared'] is None and gateway.allowed(other)

    def reconcile(self):
        for node, (gateway, current, live, initial) in self.nodes.items():
            gateway.accept(self.envelope(node))
            gateway.apply()

    def restart(self):
        for node, (gateway, current, live, initial) in self.nodes.items():
            replacement = Gateway(gateway.gateway, clock=lambda: self.current[0],
                monotonic=lambda: self.current[0], run=gateway.run)
            replacement.apply()
            self.nodes[node] = replacement, current, live, initial

    def pay(self):
        return event(self.access, self.support, now=self.current[0])


@pytest.fixture(params=['sqlite', 'postgres'])
def fleet(request, tmp_path, monkeypatch):
    return Fleet(new_store(request.param, tmp_path, membership_required=True), tmp_path, monkeypatch)


@pytest.mark.parametrize('failed_node', policy.NODES)
def test_partial_prepare_lost_ack_rolls_back_db_but_retains_node_fences(fleet, failed_node):
    before = rows(fleet.access)

    def lost(node, request):
        reply = fleet.prepare(node, request)
        if node == failed_node:
            raise TimeoutError('synthetic-lost-ack-after-durable-fence')
        return reply

    fleet.hook = lost
    with pytest.raises(paid_beta.PaidBetaError, match='TRANSPORT_PREPARATION_REQUIRED'):
        fleet.pay()
    assert rows(fleet.access) == before
    prepared = policy.NODES[:policy.NODES.index(failed_node) + 1]
    assert [node for node, request in fleet.calls] == list(prepared)
    first_token = fleet.calls[0][1]['token']
    fleet.current[0] += 360
    fleet.restart()
    fleet.reconcile()
    fleet.fenced(prepared)
    fleet.hook = fleet.prepare
    result = fleet.pay()
    assert not result['duplicate']
    assert {request['token'] for node, request in fleet.calls} == {first_token}
    assert len(rows(fleet.access)['paid_beta_events']) == 1
    fleet.reconcile()
    for gateway, current, live, initial in fleet.nodes.values():
        assert gateway.peer_allowed(initial['public_key'])
        assert initial['public_key'] in live['awg']
        assert initial['tcp_id'] in {client['id'] for client in live['tcp']}


@pytest.mark.parametrize('failure', ['before-fence', 'readback', 'after-all-acks'])
def test_preparation_or_commit_failure_cannot_create_partial_payment(fleet, monkeypatch, failure):
    before = rows(fleet.access)

    def fail(node, request):
        if failure == 'before-fence':
            raise OSError('synthetic-unavailable')
        fleet.prepare(node, request)
        raise OSError('synthetic-readback-failed')

    def fail_after_append(transaction, record):
        assert transaction.event(record['event_id']) is not None
        raise OSError('synthetic-commit-failed')

    with monkeypatch.context() as patch:
        if failure == 'after-all-acks':
            patch.setattr(paid_beta.PaidTransaction, 'save_subscription', fail_after_append)
        else:
            fleet.hook = fail
        with pytest.raises((paid_beta.PaidBetaError, OSError)):
            fleet.pay()
    assert rows(fleet.access) == before
    if failure != 'before-fence':
        fleet.restart()
        fleet.reconcile()
        fleet.fenced(policy.NODES if failure == 'after-all-acks' else policy.NODES[:1])
    fleet.hook = fleet.prepare
    assert not fleet.pay()['duplicate']


@pytest.mark.parametrize('invalid', ['wrong-node', 'wrong-token', 'extra-field', 'schema-bool',
    'schema-float', 'duplicate-field', 'non-utf8', 'oversize', 'not-bytes', 'empty'])
def test_invalid_ack_fails_closed_after_durable_node_preparation(fleet, invalid):
    before = rows(fleet.access)

    def malformed(node, request):
        raw = fleet.prepare(node, request)
        acknowledgement = json.loads(raw)
        if invalid == 'wrong-node':
            acknowledgement['node'] = 'other-node'
        elif invalid == 'wrong-token':
            acknowledgement['token'] = '0' * 64
        elif invalid == 'extra-field':
            acknowledgement['allowed'] = True
        elif invalid == 'schema-bool':
            acknowledgement['schema'] = True
        elif invalid == 'schema-float':
            acknowledgement['schema'] = 1.0
        elif invalid == 'duplicate-field':
            return b'{"schema":1,' + raw[1:]
        elif invalid == 'non-utf8':
            return b'\xff'
        elif invalid == 'oversize':
            return raw + b' ' * 1025
        elif invalid == 'not-bytes':
            return raw.decode()
        elif invalid == 'empty':
            return b''
        return json.dumps(acknowledgement).encode()

    fleet.hook = malformed
    with pytest.raises(paid_beta.PaidBetaError, match='TRANSPORT_PREPARATION_REQUIRED'):
        fleet.pay()
    assert rows(fleet.access) == before and len(fleet.calls) == 1
    fleet.fenced(policy.NODES[:1])


def test_no_payment_visible_before_all_acks_and_retry_after_commit_never_prepares(fleet):
    def inspect(node, request):
        if fleet.access.path is None:
            repository = fleet.access.enrollment_repository
            with repository.connect() as database:
                repository.configure(database)
                assert database.execute('SELECT count(*) AS total FROM paid_beta_events').fetchone()['total'] == 0
        else:
            with sqlite3.connect(fleet.access.path) as database:
                assert database.execute('SELECT count(*) FROM paid_beta_events').fetchone()[0] == 0
        return fleet.prepare(node, request)

    fleet.hook = inspect
    result = fleet.pay()
    assert [node for node, request in fleet.calls] == list(policy.NODES)
    before = rows(fleet.access)
    fleet.hook = lambda *args: pytest.fail('Committed payment replay must not contact nodes')
    duplicate = fleet.pay()
    assert duplicate['duplicate'] and duplicate['event'] == result['event']
    assert rows(fleet.access) == before and len(fleet.calls) == 3


def test_concurrent_payment_prepares_only_once(fleet):
    results = parallel(lambda index: fleet.pay(), 4)
    assert all(isinstance(result, dict) for result in results)
    assert sum(not result['duplicate'] for result in results) == 1
    assert [node for node, request in fleet.calls] == list(policy.NODES)
    assert len(rows(fleet.access)['paid_beta_events']) == 1


def test_stale_snapshot_expiry_and_revocation_cannot_undo_membership(fleet, monkeypatch):
    old = {node: fleet.envelope(node) for node in policy.NODES}
    fleet.pay()
    fleet.reconcile()
    fleet.current[0] += 121
    fleet.restart()
    for gateway, current, live, initial in fleet.nodes.values():
        assert not gateway.peer_allowed(initial['public_key'])
    fleet.reconcile()
    for node, (gateway, current, live, initial) in fleet.nodes.items():
        assert gateway.peer_allowed(initial['public_key'])
        late = deepcopy(old[node])
        late['observed_at'] = fleet.current[0] + 1
        for decision in late['decisions']:
            decision.update(observed_at=fleet.current[0] + 1, valid_until=fleet.current[0] + 121)
        with pytest.raises(ValueError, match='TERMINAL'):
            gateway.accept(late)
    event(fleet.access, fleet.support, 'revoke', 'synthetic-terminal-revoke', now=fleet.current[0])
    fleet.reconcile()
    fleet.current[0] += 1000
    monkeypatch.setattr('control.friends.transport_gateway.boot_id', lambda: 'synthetic-new-boot')
    fleet.restart()
    fleet.reconcile()
    fleet.fenced(policy.NODES)
    with pytest.raises(paid_beta.PaidBetaError, match='REVOCATION_TERMINAL'):
        event(fleet.access, fleet.support, event_id='synthetic-new-payment', now=fleet.current[0])


def test_postgres_required_mode_never_falls_back_to_no_transport(tmp_path):
    access = new_store('postgres', tmp_path, membership_required=True)
    device, support = activate(access)
    with pytest.raises(paid_beta.PaidBetaError, match='TRANSPORT_PREPARATION_REQUIRED'):
        event(access, support)
    assert not rows(access)['paid_beta_events']
    original = access.enrollment_repository
    reopened = PostgresEnrollment(port=original.port, schema=original.schema, password=original.password)
    with reopened.transaction() as transaction:
        with pytest.raises(paid_beta.PaidBetaError, match='TRANSPORT_PREPARATION_REQUIRED'):
            transaction.paid().prepare_membership(device.reference, '0' * 64, NOW)


def test_postgres_no_transport_mode_cannot_claim_configured_preparation(tmp_path):
    access = new_store('postgres', tmp_path)
    device, support = activate(access)
    access.enrollment_repository.membership_exchange = lambda *args: pytest.fail('Wrong mode must fail first')
    with pytest.raises(paid_beta.PaidBetaError, match='PAID_REHEARSAL_MODE_CONFLICT'):
        event(access, support)
    assert not rows(access)['paid_beta_events']


def test_postgres_backend_loss_after_all_acks_leaves_durable_denies(tmp_path, monkeypatch):
    fleet = Fleet(new_store('postgres', tmp_path, membership_required=True), tmp_path, monkeypatch)
    from psycopg import OperationalError
    repository = fleet.access.enrollment_repository
    original = paid_beta.PaidTransaction.save_subscription

    def terminate(transaction, record):
        original(transaction, record)
        with repository.connect() as control:
            assert control.execute('SELECT pg_terminate_backend(%s,1000) AS terminated',
                (transaction.database.info.backend_pid,)).fetchone()['terminated'] is True

    with monkeypatch.context() as patch:
        patch.setattr(PostgresPaidTransaction, 'save_subscription', terminate)
        with pytest.raises(OperationalError):
            fleet.pay()
    assert not rows(fleet.access)['paid_beta_events']
    assert not rows(fleet.access)['paid_beta_subscriptions']
    fleet.restart()
    fleet.reconcile()
    fleet.fenced(policy.NODES)
    assert not fleet.pay()['duplicate']
    assert len({request['token'] for node, request in fleet.calls}) == 1
    fleet.reconcile()
    for gateway, current, live, initial in fleet.nodes.values():
        assert gateway.peer_allowed(initial['public_key'])


def test_postgres_idle_timeout_during_prepare_never_becomes_payment(tmp_path, monkeypatch):
    fleet = Fleet(new_store('postgres', tmp_path, membership_required=True), tmp_path, monkeypatch)
    from psycopg.errors import IdleInTransactionSessionTimeout

    def delayed(node, request):
        reply = fleet.prepare(node, request)
        time.sleep(5.5)
        return reply

    fleet.hook = delayed
    with pytest.raises(IdleInTransactionSessionTimeout):
        fleet.pay()
    assert not rows(fleet.access)['paid_beta_events']
    assert len(fleet.calls) == 1
    fleet.restart()
    fleet.reconcile()
    fleet.fenced(policy.NODES[:1])
    fleet.hook = fleet.prepare
    assert not fleet.pay()['duplicate']
