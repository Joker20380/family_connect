from contextlib import contextmanager
import json
import sqlite3

import pytest

from control.friends.access import Rejected
from control.friends import gateway_routing as routing, gateway_selection as selection
from control.friends.gateway_routing_postgres import initialize_synthetic_routing
from provisioning.friends_catalog import GATEWAY_CHOICES
from scripts.gateway_routing_postgres_rehearsal import scenario, replacement, activate, signed_catalog
from tests.test_enrollment_repository import access as enrollment_access, parallel, postgres_access


@pytest.fixture
def node(enrollment_access, tmp_path):
    if enrollment_access.path is None:
        initialize_synthetic_routing(enrollment_access.enrollment_repository)
    return scenario(enrollment_access, tmp_path)


@pytest.fixture
def postgres_node(postgres_access, tmp_path):
    initialize_synthetic_routing(postgres_access.enrollment_repository)
    return scenario(postgres_access, tmp_path)


def enable(node):
    return routing.install(node.access, node.policy, node.envelopes[0])


def state(node):
    with node.access.read_enrollment() as transaction:
        adapter = transaction.routing()
        return {table: [dict(row) for row in transaction.database.execute('SELECT * FROM ' + table + ' ORDER BY 1')]
            for table in ('devices', 'invites', 'challenges', 'gateway_routing_state', 'gateway_assignments',
                          'gateway_assignment_events', 'gateway_selection_events') if adapter.exists(table)}


def move(node, **changes):
    arguments = dict(device=node.owner.reference, expected=node.hashes[0], destination=node.hashes[1],
                     operation_id='synthetic-movement-01') | changes
    return routing.move(node.access, node.policy, **arguments)


def test_unconfigured_and_install_preserve_existing_devices(node):
    assert routing.configuration(node.access, node.root, 'nl', node.owner.reference) is None
    assert enable(node)['preserved_devices'] == 1
    assert enable(node)['result'] == 'UNCHANGED'
    for country in ('ru', 'nl'):
        assert routing.configuration(node.access, node.root, country, node.owner.reference)[0] == node.policy.catalogs[node.hashes[0]]
    newcomer = activate(node.access)
    assert routing.configuration(node.access, node.root, 'nl', newcomer.reference)[0] == node.policy.catalogs[node.hashes[1]]


def test_concurrent_install_and_first_assignment(node):
    results = parallel(lambda index: enable(node), 6)
    assert sum(result['result'] == 'INSTALLED' for result in results) == 1
    newcomer = activate(node.access)
    results = parallel(lambda index: routing.configuration(node.access, node.root, 'nl', newcomer.reference), 8)
    assert all(result == results[0] for result in results)
    assert len(state(node)['gateway_assignments']) == 2


def test_move_replay_conflict_and_forward_rollback(node):
    enable(node)
    assert move(node)['result'] == 'ASSIGNED'
    assert move(node)['result'] == 'UNCHANGED'
    before = state(node)
    with pytest.raises(ValueError):
        move(node, destination=node.hashes[2])
    with pytest.raises(ValueError):
        move(node, expected=node.hashes[1], destination=node.hashes[0], operation_id='backward-rejected')
    assert state(node) == before
    assert move(node, expected=node.hashes[1], destination=node.hashes[2], operation_id='forward-rollback')['result'] == 'ASSIGNED'
    assert routing.configuration(node.access, node.root, 'nl', node.owner.reference)[1] == '192.0.2.20'


def test_concurrent_conflicting_moves_have_one_winner(node):
    enable(node)

    def attempt(index):
        try:
            return move(node, destination=node.hashes[1 + index % 2], operation_id='competing-move-' + str(index))
        except ValueError:
            return None

    results = parallel(attempt, 8)
    assert sum(result is not None for result in results) == 1
    assert len(state(node)['gateway_assignment_events']) == 2


def test_concurrent_identical_move_and_old_replay_never_rewind(node):
    enable(node)
    results = parallel(lambda index: move(node), 8)
    assert sum(result['result'] == 'ASSIGNED' for result in results) == 1
    move(node, expected=node.hashes[1], destination=node.hashes[2], operation_id='newer-routing-movement')
    before = state(node)
    assert move(node)['result'] == 'UNCHANGED'
    assert state(node) == before


def test_selection_monotonic_update_and_stale_replay(enrollment_access, tmp_path):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    if enrollment_access.path is None:
        initialize_synthetic_routing(enrollment_access.enrollment_repository)
    signer = Ed25519PrivateKey.generate()
    node = scenario(enrollment_access, tmp_path, signer=signer)
    enable(node)
    selection.install(node.access, node.root, node.request)
    envelope = json.loads((node.directory / (node.request['catalog_sha256'] + '.selection.json')).read_bytes())
    raw = routing.canonical(signed_catalog(envelope, signer, sequence=2))
    catalog = routing.digest(raw)
    target = node.directory / (catalog + '.selection.json')
    target.write_bytes(raw)
    target.chmod(0o600)
    request = node.request | dict(operation_id='newer-selection-catalog', catalog_sha256=catalog,
                                previous_sha256=node.request['catalog_sha256'])
    with pytest.raises(ValueError):
        selection.install(node.access, node.root, request | dict(previous_sha256='0' * 64))
    assert selection.install(node.access, node.root, request)['sequence'] == 2
    before = state(node)
    assert selection.install(node.access, node.root, node.request)['result'] == 'UNCHANGED'
    assert state(node) == before
    assert selection.configuration(node.access, node.root, GATEWAY_CHOICES[0], node.owner.reference)[0] == json.loads(raw)
    with pytest.raises(ValueError):
        selection.install(node.access, node.root, node.request | dict(operation_id='old-catalog-new-operation', previous_sha256=catalog))


def test_selection_is_independent_idempotent_and_no_fallback(node):
    enable(node)
    before = state(node)['gateway_assignments']
    with pytest.raises(ValueError):
        selection.configuration(node.access, node.root, GATEWAY_CHOICES[0], node.owner.reference)
    results = parallel(lambda index: selection.install(node.access, node.root, node.request), 6)
    assert sum(result['result'] == 'SELECTION_CATALOG_INSTALLED' for result in results) == 1
    for target, host in zip(GATEWAY_CHOICES, ('192.0.2.20', '192.0.2.21')):
        assert selection.configuration(node.access, node.root, target, node.owner.reference)[1] == host
    for changes in (dict(previous_sha256='0' * 64), dict(operation_id='same-sequence-rejected',
                   previous_sha256=node.request['catalog_sha256'])):
        with pytest.raises(ValueError):
            selection.install(node.access, node.root, node.request | changes)
    assert state(node)['gateway_assignments'] == before


def test_policy_replacement_preserves_assignments_invalidates_selection(node):
    enable(node)
    selection.install(node.access, node.root, node.request)
    before = state(node)['gateway_assignments']
    updated = replacement(node)
    assert routing.replace_policy(node.access, node.policy, updated)['result'] == 'POLICY_INSTALLED'
    assert routing.replace_policy(node.access, node.policy, updated)['result'] == 'UNCHANGED'
    assert state(node)['gateway_assignments'] == before
    assert routing.configuration(node.access, node.root, 'nl', activate(node.access).reference)[0] == updated.catalogs[node.hashes[2]]
    with pytest.raises(ValueError):
        selection.configuration(node.access, node.root, GATEWAY_CHOICES[0], node.owner.reference)


@pytest.mark.parametrize('table', ['devices', 'invites'])
@pytest.mark.parametrize('newcomer', [False, True])
def test_revocation_checked_before_read_or_assignment(node, table, newcomer):
    enable(node)
    selection.install(node.access, node.root, node.request)
    device = activate(node.access) if newcomer else node.owner
    with node.access.enrollment() as transaction:
        transaction.database.execute('UPDATE ' + table + ' SET revoked=1 WHERE device=' + transaction.placeholder,
                                     (device.reference,))
    before = state(node)
    with pytest.raises(Rejected):
        routing.configuration(node.access, node.root, 'nl', device.reference)
    with pytest.raises(Rejected):
        selection.configuration(node.access, node.root, GATEWAY_CHOICES[0], device.reference)
    with pytest.raises(Rejected):
        move(node, device=device.reference)
    assert state(node) == before


@pytest.mark.parametrize('phase', ['install', 'move', 'replace', 'assign', 'selection'])
def test_failure_rolls_back_schema_projection_and_journal(node, monkeypatch, phase):
    if phase != 'install':
        enable(node)
    if phase == 'install':
        method, attempt = 'event', lambda: enable(node)
    elif phase == 'move':
        method, attempt = 'event', lambda: move(node)
    elif phase == 'replace':
        updated = replacement(node)
        method, attempt = 'event', lambda: routing.replace_policy(node.access, node.policy, updated)
    elif phase == 'assign':
        device = activate(node.access)
        method, attempt = 'set_assignment', lambda: routing.configuration(node.access, node.root, 'nl', device.reference)
    else:
        method, attempt = 'selection_event', lambda: selection.install(node.access, node.root, node.request)
    before = state(node)
    original = getattr(routing.RoutingTransaction, method)

    def fail_after(self, *args, **kwargs):
        original(self, *args, **kwargs)
        raise RuntimeError('synthetic transaction failure')

    with monkeypatch.context() as patch:
        patch.setattr(routing.RoutingTransaction, method, fail_after)
        with pytest.raises(RuntimeError, match='synthetic transaction failure'):
            attempt()
    assert state(node) == before
    attempt()


@pytest.mark.parametrize('phase', ['install', 'move', 'replace', 'assign', 'selection'])
def test_lost_commit_ack_retry_does_not_duplicate(node, monkeypatch, phase):
    if phase != 'install':
        enable(node)
    updated = replacement(node)
    newcomer = activate(node.access)
    attempts = dict(install=lambda: enable(node), move=lambda: move(node),
        replace=lambda: routing.replace_policy(node.access, node.policy, updated),
        assign=lambda: routing.configuration(node.access, node.root, 'nl', newcomer.reference),
        selection=lambda: selection.install(node.access, node.root, node.request))
    original = node.access.enrollment

    @contextmanager
    def lost_ack():
        with original() as transaction:
            yield transaction
        raise RuntimeError('synthetic lost commit acknowledgement')

    with monkeypatch.context() as patch:
        patch.setattr(node.access, 'enrollment', lost_ack)
        with pytest.raises(RuntimeError, match='synthetic lost commit acknowledgement'):
            attempts[phase]()
    committed = state(node)
    attempts[phase]()
    assert state(node) == committed


@pytest.mark.parametrize('table', ['gateway_assignment_events', 'gateway_selection_events'])
@pytest.mark.parametrize('action', ['UPDATE', 'DELETE'])
def test_event_history_is_append_only(node, table, action):
    import psycopg
    enable(node)
    selection.install(node.access, node.root, node.request)
    before = state(node)
    query = ('UPDATE ' + table + " SET operation_id='tampered'" if action == 'UPDATE' else 'DELETE FROM ' + table)
    with pytest.raises((sqlite3.IntegrityError, psycopg.errors.CheckViolation)):
        with node.access.enrollment() as transaction:
            transaction.database.execute(query)
    assert state(node) == before


def test_status_and_selection_use_readonly_snapshot(node, monkeypatch):
    enable(node)
    selection.install(node.access, node.root, node.request)
    before = state(node)

    def no_writer():
        raise AssertionError('read-only operation acquired writer')

    monkeypatch.setattr(node.access, 'enrollment', no_writer)
    assert routing.administer(node.access, node.root, dict(schema=1, action='status'))['mutations'] == 0
    selection.configuration(node.access, node.root, GATEWAY_CHOICES[0], node.owner.reference)
    assert state(node) == before


def test_corrupted_generation_rejects_both_configuration_paths(node):
    enable(node)
    selection.install(node.access, node.root, node.request)
    with node.access.enrollment() as transaction:
        transaction.database.execute('UPDATE gateway_routing_state SET generation=99')
    for attempt in (lambda: routing.configuration(node.access, node.root, 'nl', node.owner.reference),
                    lambda: selection.configuration(node.access, node.root, GATEWAY_CHOICES[0], node.owner.reference),
                    lambda: selection.install(node.access, node.root, node.request)):
        with pytest.raises(ValueError, match='Gateway routing rejected'):
            attempt()


@pytest.mark.parametrize('file_kind', ['policy', 'catalog', 'anchor', 'selection'])
def test_unavailable_verified_files_refuse_without_db_mutation(node, file_kind):
    enable(node)
    selection.install(node.access, node.root, node.request)
    newcomer = activate(node.access)
    names = dict(policy=node.policy.sha256 + '.policy.json', catalog=node.hashes[0] + '.catalog.json',
                 anchor='anchor.pub', selection=node.request['catalog_sha256'] + '.selection.json')
    (node.directory / names[file_kind]).unlink()
    before = state(node)
    with pytest.raises(FileNotFoundError):
        selection.configuration(node.access, node.root, GATEWAY_CHOICES[0], newcomer.reference)
    if file_kind != 'selection':
        with pytest.raises(FileNotFoundError):
            routing.configuration(node.access, node.root, 'nl', newcomer.reference)
    assert state(node) == before


@pytest.mark.parametrize('damage', ['missing', 'wrong'])
def test_postgres_marker_is_required(postgres_access, damage):
    import psycopg
    if damage == 'wrong':
        initialize_synthetic_routing(postgres_access.enrollment_repository)
        with postgres_access.enrollment() as transaction:
            transaction.database.execute("UPDATE ha_routing_schema SET purpose='wrong'")
    with pytest.raises(psycopg.errors.UndefinedTable if damage == 'missing' else RuntimeError):
        with postgres_access.enrollment() as transaction:
            transaction.routing()


@pytest.mark.parametrize('table', ['gateway_assignment_events', 'gateway_selection_events'])
def test_postgres_truncate_cannot_erase_evidence(postgres_node, table):
    import psycopg
    enable(postgres_node)
    selection.install(postgres_node.access, postgres_node.root, postgres_node.request)
    before = state(postgres_node)
    with pytest.raises(psycopg.errors.CheckViolation):
        with postgres_node.access.enrollment() as transaction:
            transaction.database.execute('TRUNCATE ' + table)
    assert state(postgres_node) == before


@pytest.mark.parametrize('phase', ['install', 'move', 'selection'])
def test_postgres_backend_loss_is_atomic(postgres_node, monkeypatch, phase):
    import psycopg
    node = postgres_node
    if phase != 'install':
        enable(node)
    method = 'selection_event' if phase == 'selection' else 'event'
    original = getattr(routing.RoutingTransaction, method)
    before = state(node)

    def terminate_after(self, *args):
        original(self, *args)
        with node.access.enrollment_repository.connect() as killer:
            pid = self.database.execute('SELECT pg_backend_pid() AS pid').fetchone()['pid']
            assert killer.execute('SELECT pg_terminate_backend(%s,1000) AS stopped', (pid,)).fetchone()['stopped']
        self.database.execute('SELECT 1')

    attempt = dict(install=lambda: enable(node), move=lambda: move(node),
                   selection=lambda: selection.install(node.access, node.root, node.request))[phase]
    with monkeypatch.context() as patch:
        patch.setattr(routing.RoutingTransaction, method, terminate_after)
        with pytest.raises(psycopg.OperationalError):
            attempt()
    assert state(node) == before
    attempt()
