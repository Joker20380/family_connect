from contextlib import contextmanager
import hashlib
import json
import secrets
import sqlite3
from types import SimpleNamespace

import pytest

from control.friends.access import Access, Rejected
from control.friends import notices
from device_identity.device import DeviceIdentity
from scripts.notices_postgres_rehearsal import initialize, notice, edit, request_value
from scripts.referral_postgres_rehearsal import NOW, proof
from scripts.service_notices import Notices, NoticeTransaction
from tests.test_enrollment_repository import access as enrollment_access, parallel, postgres_access


def enroll(access):
    device = DeviceIdentity.generate()
    access.complete(proof(access, device, 'activate', access.invite()), 'activate')
    return SimpleNamespace(access=access, device=device)


def setup(access):
    access.clock = lambda: NOW
    initialize(access)
    return enroll(access)


@pytest.fixture
def node(enrollment_access):
    return setup(enrollment_access)


@pytest.fixture
def postgres_node(postgres_access):
    return setup(postgres_access)


def grant(node, name='Synthetic operator'):
    notices.grant_device_repository(node.access, node.device.reference, name)


def submit(node, action='publish', **values):
    if action == 'publish' and not values:
        values = dict(notice=notice())
    return notices.device_request_repository(node.access, action, request_value(node.access, node.device, action, **values))


def state(node):
    with node.access.read_enrollment() as enrollment:
        transaction = NoticeTransaction(enrollment.database, enrollment.placeholder)
        return {table: transaction.rows('SELECT * FROM ' + table + ' ORDER BY 1') for table in
                ('admins', 'device_admins', 'events', 'revisions', 'edit_operations', 'challenges', 'devices', 'invites')}


def test_operator_grant_revoke_explicit_regrant_and_member_cannot_delegate(node):
    assert submit(node, 'role')['role'] == 'member'
    pending = request_value(node.access, node.device, 'publish', notice=notice())
    before = state(node)
    with pytest.raises(notices.NoticeDenied):
        notices.device_request_repository(node.access, 'publish', pending)
    assert state(node) == before
    grant(node)
    assert submit(node, 'role')['name'] == 'Synthetic operator'
    assert notices.device_request_repository(node.access, 'publish', pending)['status'] == 'stored'
    with node.access.enrollment() as enrollment:
        enrollment.notices().revoke_device(node.device.reference)
    with pytest.raises(notices.NoticeDenied):
        submit(node)
    grant(node, 'Reassigned operator')
    assert submit(node, 'role')['name'] == 'Reassigned operator'
    with pytest.raises(ValueError):
        submit(node, 'grant', name='No delegation')


def test_proof_is_action_bound_single_use_and_publish_id_binds_payload(node):
    grant(node)
    value = request_value(node.access, node.device, 'role')
    before = state(node)
    with pytest.raises(Rejected):
        notices.device_request_repository(node.access, 'publish', value | dict(notice=notice()))
    assert state(node) == before
    notices.device_request_repository(node.access, 'role', value)
    with pytest.raises(Rejected):
        notices.device_request_repository(node.access, 'role', value)
    assert submit(node) == submit(node)
    value = request_value(node.access, node.device, 'publish', notice=notice(body='Changed'))
    before = state(node)
    with pytest.raises(ValueError, match='Conflicting notice id'):
        notices.device_request_repository(node.access, 'publish', value)
    assert state(node) == before


def test_edit_atomic_revision_immutable_v1_and_device_bound_retry(node):
    grant(node)
    submit(node)
    response = submit(node, 'edit', notice=edit())
    assert response['revision'] == 2 and submit(node, 'edit', notice=edit()) == response
    assert notices.feed_repository(node.access)['events'][0]['title'] == notice()['title']
    assert notices.feed_repository(node.access, 2)['events'][0]['title'] == edit()['title']
    assert len(state(node)['edit_operations']) == 1
    for candidate, reason in [(edit(body='Changed'), 'Conflicting edit'), (edit(sequence=2), 'Stale notice revision')]:
        value = request_value(node.access, node.device, 'edit', notice=candidate)
        before = state(node)
        with pytest.raises((ValueError, notices.NoticeConflict)) as error:
            notices.device_request_repository(node.access, 'edit', value)
        assert isinstance(error.value, notices.NoticeConflict) if reason.startswith('Stale') else str(error.value) == reason
        assert state(node) == before
    other = enroll(node.access)
    grant(other)
    with pytest.raises(ValueError, match='Conflicting edit'):
        submit(other, 'edit', notice=edit())


@pytest.mark.parametrize('mode', ['one_proof', 'same_operation', 'competing_revision'])
def test_concurrent_edits_serialize_and_bind_request_id(node, mode):
    grant(node)
    submit(node)
    values = [request_value(node.access, node.device, 'edit', notice=edit(sequence=index + 1 if mode == 'competing_revision' else 1))
              for index in range(6)]
    if mode == 'one_proof':
        values = [values[0]] * 6

    def attempt(index):
        try:
            return notices.device_request_repository(node.access, 'edit', values[index])
        except notices.NoticeConflict:
            return None

    results = parallel(attempt, 6)
    assert sum(result is not None for result in results) == (6 if mode == 'same_operation' else 1)
    assert len(state(node)['edit_operations']) == 1
    assert notices.feed_repository(node.access, 2)['events'][0]['revision'] == 2


def test_concurrent_publish_order_and_pagination_are_stable_after_reopen(node):
    grant(node)
    values = [request_value(node.access, node.device, 'publish', notice=notice(index + 1)) for index in range(6)]
    parallel(lambda index: notices.device_request_repository(node.access, 'publish', values[index]), 6)
    with node.access.enrollment() as enrollment:
        publisher = enrollment.notices()
        for index in range(7, 53):
            notices.publish_value(publisher, '', notice(index), device=node.device.reference, now=NOW)
    first = submit(node, 'list', offset=0)
    second = submit(node, 'list', offset=first['next_offset'])
    assert len(first['events']) == 50 and len(second['events']) == 2 and second['next_offset'] is None
    assert [event['id'] for event in first['events'] + second['events']] == list(reversed(
        [event['id'] for event in notices.feed_repository(node.access)['events']]))
    node.access = Access(node.access.path, clock=lambda: NOW, enrollment_repository=node.access.enrollment_repository)
    assert submit(node, 'list', offset=0) == first
    assert sorted(row[2] for row in state(node)['events']) == list(range(1, 53))


def test_active_quota_expiry_and_read_only_feed(node, monkeypatch):
    grant(node)
    with node.access.enrollment() as enrollment:
        for index in range(1, 201):
            notices.publish_value(enrollment.notices(), '', notice(index), device=node.device.reference, now=NOW)
    value = request_value(node.access, node.device, 'publish', notice=notice(201))
    before = state(node)
    with pytest.raises(ValueError, match='Active notice quota reached'):
        notices.device_request_repository(node.access, 'publish', value)
    assert state(node) == before
    with monkeypatch.context() as patch:
        patch.setattr(node.access, 'enrollment', lambda: pytest.fail('Feed must not take writer lock'))
        node.access.clock = lambda: NOW + 86399
        assert len(notices.feed_repository(node.access, 2)['events']) == 200
        node.access.clock = lambda: NOW + 86400
        assert notices.feed_repository(node.access, 2)['events'] == []
    assert state(node) == before
    submit(node, notice=notice(201))
    assert len(state(node)['events']) == 201


@pytest.mark.parametrize('revocation', ['publisher', 'device', 'invite'])
def test_revoke_after_challenge_rolls_back_proof(node, revocation):
    grant(node)
    value = request_value(node.access, node.device, 'publish', notice=notice())
    with node.access.enrollment() as enrollment:
        if revocation == 'publisher':
            enrollment.notices().revoke_device(node.device.reference)
        else:
            enrollment.database.execute('UPDATE ' + ('devices' if revocation == 'device' else 'invites') + ' SET revoked=1')
    before = state(node)
    with pytest.raises((Rejected, notices.NoticeDenied)):
        notices.device_request_repository(node.access, 'publish', value)
    assert state(node) == before
    if revocation != 'publisher':
        with pytest.raises(ValueError, match='Device not active'):
            grant(node)


def test_concurrent_publisher_revoke_cannot_be_undone_by_retry(node):
    grant(node)
    value = request_value(node.access, node.device, 'publish', notice=notice())

    def attempt(index):
        if index:
            with node.access.enrollment() as enrollment:
                enrollment.notices().revoke_device(node.device.reference)
        else:
            try:
                return notices.device_request_repository(node.access, 'publish', value)
            except notices.NoticeDenied:
                return None

    parallel(attempt, 2)
    with pytest.raises(notices.NoticeDenied):
        submit(node)


def test_token_digest_authorization_revocation_and_no_delegation(node):
    token = secrets.token_hex(32)
    with node.access.enrollment() as enrollment:
        enrollment.notices().grant_digest('Synthetic token', hashlib.sha256(token.encode()).hexdigest())
    authorization = 'Bearer ' + token
    assert notices.publish_repository(node.access, authorization, notice())['status'] == 'stored'
    assert token not in repr(state(node))
    with node.access.enrollment() as enrollment:
        enrollment.notices().revoke('Synthetic token')
    before = state(node)
    for header in (authorization, 'Bearer invalid', '', None):
        with pytest.raises(notices.NoticeDenied):
            notices.publish_repository(node.access, header, notice())
    assert state(node) == before
    with pytest.raises(notices.NoticeDenied):
        submit(node)


@pytest.mark.parametrize('operation', ['assign_device', 'grant_digest', 'revoke_device', 'revoke'])
def test_operator_writes_do_not_commit_outside_outer_transaction(node, operation):
    grant(node)
    digest = hashlib.sha256(secrets.token_bytes(32)).hexdigest()
    with node.access.enrollment() as enrollment:
        enrollment.notices().grant_digest('Existing token', digest)
    before = state(node)
    values = {'assign_device': (node.device.reference, 'Changed operator'),
              'grant_digest': ('New token', digest), 'revoke_device': (node.device.reference,), 'revoke': ('Existing token',)}
    with pytest.raises(RuntimeError, match='synthetic operator rollback'):
        with node.access.enrollment() as enrollment:
            getattr(enrollment.notices(), operation)(*values[operation])
            raise RuntimeError('synthetic operator rollback')
    assert state(node) == before


def test_expired_notice_duplicate_does_not_resurrect_or_refresh_lifetime(node):
    grant(node)
    response = submit(node)
    original = state(node)['events']
    node.access.clock = lambda: NOW + 86400
    assert submit(node) == response
    assert state(node)['events'] == original
    assert notices.feed_repository(node.access, 2)['events'] == []
    assert len(submit(node, 'list', offset=0)['events']) == 1


@pytest.mark.parametrize('method', ['save_event', 'save_edit'])
def test_failure_after_durable_writes_rolls_back_proof_history_and_revision(node, monkeypatch, method):
    grant(node)
    if method == 'save_edit':
        submit(node)
    action = 'edit' if method == 'save_edit' else 'publish'
    value = request_value(node.access, node.device, action, notice=edit() if action == 'edit' else notice())
    before = state(node)
    original = getattr(NoticeTransaction, method)

    def broken(self, *args):
        original(self, *args)
        raise RuntimeError('synthetic notice write failure')

    with monkeypatch.context() as patch:
        patch.setattr(NoticeTransaction, method, broken)
        with pytest.raises(RuntimeError, match='synthetic notice write failure'):
            notices.device_request_repository(node.access, action, value)
    assert state(node) == before
    notices.device_request_repository(node.access, action, value)


@pytest.mark.parametrize('committed', [False, True])
def test_commit_failure_and_ack_loss_preserve_edit_idempotency(node, monkeypatch, committed):
    grant(node)
    submit(node)
    value = request_value(node.access, node.device, 'edit', notice=edit())
    before = state(node)
    original = node.access.enrollment

    @contextmanager
    def broken():
        with original() as enrollment:
            yield enrollment
            if not committed:
                raise RuntimeError('synthetic before commit')
        raise RuntimeError('synthetic lost ACK')

    with monkeypatch.context() as patch:
        patch.setattr(node.access, 'enrollment', broken)
        with pytest.raises(RuntimeError, match='synthetic'):
            notices.device_request_repository(node.access, 'edit', value)
    if committed:
        with pytest.raises(Rejected):
            notices.device_request_repository(node.access, 'edit', value)
        assert submit(node, 'edit', notice=edit())['revision'] == 2
    else:
        assert state(node) == before
        notices.device_request_repository(node.access, 'edit', value)
    assert len(state(node)['edit_operations']) == 1


@pytest.mark.parametrize('delay', [60, 101])
def test_time_and_proof_checked_after_writer_wait(node, monkeypatch, delay):
    grant(node)
    value = request_value(node.access, node.device, 'publish', notice=notice())
    before = state(node)
    original = node.access.enrollment

    @contextmanager
    def delayed():
        with original() as enrollment:
            node.access.clock = lambda: NOW + delay
            yield enrollment

    monkeypatch.setattr(node.access, 'enrollment', delayed)
    if delay == 60:
        notices.device_request_repository(node.access, 'publish', value)
        assert notices.feed_repository(node.access)['events'][0]['created'] == NOW + delay
    else:
        with pytest.raises(Rejected):
            notices.device_request_repository(node.access, 'publish', value)
        assert state(node) == before


@pytest.mark.parametrize('mutation', ['days', 'id', 'title', 'platforms', 'unknown'])
def test_invalid_notice_does_not_consume_canonical_proof(node, mutation):
    grant(node)
    candidate = notice()
    candidate[mutation] = {'days': True, 'id': 'bad', 'title': '', 'platforms': ['bad'], 'unknown': True}[mutation]
    value = request_value(node.access, node.device, 'publish', notice=candidate)
    before = state(node)
    with pytest.raises(ValueError):
        notices.device_request_repository(node.access, 'publish', value)
    assert state(node) == before


@pytest.mark.parametrize('table,operation', [('events', 'UPDATE'), ('events', 'DELETE'),
    ('edit_operations', 'UPDATE'), ('edit_operations', 'DELETE'), ('revisions', 'UPDATE'), ('revisions', 'DELETE')])
def test_schema_guards_v1_history_and_revision_floor(node, table, operation):
    import psycopg
    grant(node)
    submit(node)
    submit(node, 'edit', notice=edit())
    before = state(node)
    with pytest.raises((sqlite3.IntegrityError, psycopg.errors.CheckViolation)):
        with node.access.enrollment() as enrollment:
            enrollment.database.execute(('DELETE FROM ' + table) if operation == 'DELETE' else
                                         ('UPDATE ' + table + ' SET id=id'))
    assert state(node) == before


@pytest.mark.parametrize('damage', ['missing', 'wrong'])
def test_marker_gate_before_proof_use(node, damage):
    import psycopg
    value = request_value(node.access, node.device, 'role')
    with node.access.enrollment() as enrollment:
        enrollment.database.execute('DROP TABLE ha_notices_schema' if damage == 'missing'
                                    else "UPDATE ha_notices_schema SET purpose='wrong'")
    before = state(node)
    with pytest.raises((RuntimeError, sqlite3.OperationalError, psycopg.errors.UndefinedTable)):
        notices.device_request_repository(node.access, 'role', value)
    assert state(node) == before


def test_no_canonical_file_export_or_legacy_split_proof(node, tmp_path, monkeypatch):
    value = request_value(node.access, node.device, 'role')
    before = state(node)
    target = tmp_path / 'must-not-exist.json'
    registry = tmp_path / 'must-not-exist.sqlite'
    with node.access.enrollment() as enrollment:
        for method in ('export', 'export_all'):
            with pytest.raises(NotImplementedError):
                getattr(enrollment.notices(), method)(target)
    monkeypatch.setattr(node.access, 'complete', lambda *args, **kwargs: pytest.fail('No proof before refusal'))
    with pytest.raises(NotImplementedError):
        notices.device_request(node.access, registry, target, 'role', value)
    if node.access.path is not None:
        with pytest.raises(NotImplementedError):
            Notices(node.access.path)
    assert not registry.exists() and not target.exists() and state(node) == before


@pytest.mark.parametrize('method', ['save_event', 'save_edit'])
def test_backend_loss_preserves_atomic_notice_and_proof(postgres_node, monkeypatch, method):
    import psycopg
    node = postgres_node
    grant(node)
    if method == 'save_edit':
        submit(node)
    action = 'edit' if method == 'save_edit' else 'publish'
    value = request_value(node.access, node.device, action, notice=edit() if action == 'edit' else notice())
    before = state(node)
    original = getattr(NoticeTransaction, method)

    def kill(self, *args):
        original(self, *args)
        with node.access.enrollment_repository.connect() as killer:
            pid = self.db.execute('SELECT pg_backend_pid() AS pid').fetchone()['pid']
            assert killer.execute('SELECT pg_terminate_backend(%s,1000) AS stopped', (pid,)).fetchone()['stopped']
        self.db.execute('SELECT 1')

    with monkeypatch.context() as patch:
        patch.setattr(NoticeTransaction, method, kill)
        with pytest.raises(psycopg.OperationalError):
            notices.device_request_repository(node.access, action, value)
    assert state(node) == before
    notices.device_request_repository(node.access, action, value)


def test_legacy_export_failure_is_not_rolled_back_as_canonical(tmp_path, monkeypatch):
    access = Access(tmp_path / 'legacy.sqlite', clock=lambda: NOW)
    access.initialize()
    node = enroll(access)
    registry = tmp_path / 'notices.sqlite'
    store = Notices(registry)
    try:
        store.grant_device(access, node.device.reference, 'Synthetic operator')
        value = request_value(access, node.device, 'publish', notice=notice())

        def failed(*args):
            raise OSError('synthetic export failure')

        with monkeypatch.context() as patch:
            patch.setattr(Notices, 'export_all', failed)
            with pytest.raises(OSError):
                notices.device_request(access, registry, tmp_path / 'feed.json', 'publish', value)
        assert store.db.execute('SELECT COUNT(*) FROM events').fetchone()[0] == 1
        with pytest.raises(Rejected):
            notices.device_request(access, registry, tmp_path / 'feed.json', 'publish', value)
    finally:
        store.db.close()
