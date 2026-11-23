from contextlib import contextmanager

import pytest

from control.friends import restricted_admin, support_admin, support_ids
from control.friends.restricted import migrate
from control.friends.restricted_admin import MAX_INTEGER, RestrictedAdminTransaction, grant
from control.friends.restricted_admin_postgres import initialize_synthetic_restricted_admin
from control.friends.support_postgres import initialize_synthetic_support
from tests.test_enrollment_repository import access as enrollment_access, parallel, peer, postgres_access
from tests.test_support_repository import enroll


@pytest.fixture
def access(enrollment_access):
    if enrollment_access.path is None:
        initialize_synthetic_restricted_admin(enrollment_access.enrollment_repository)
        initialize_synthetic_support(enrollment_access.enrollment_repository)
    else:
        migrate(enrollment_access)
    return enrollment_access


@pytest.fixture
def postgres_admin(postgres_access):
    initialize_synthetic_restricted_admin(postgres_access.enrollment_repository)
    return postgres_access


def state(access):
    with access.enrollment() as transaction:
        return {table: [dict(row) for row in transaction.database.execute('SELECT * FROM ' + table + ' ORDER BY 1')]
                for table in ('devices', 'invites', 'challenges', 'device_support', 'restricted_grants', 'field_support_audit')}


def revoke(access, device):
    with access.enrollment() as transaction:
        transaction.restricted_admin().revoke_grant(device.reference)


def test_explicit_grants_renew_monotonically_and_leave_identity_unchanged(access):
    device, support = enroll(access)
    before = state(access)
    grant(access, device.reference, 'family-one', 2000, 5)
    grant(access, device.reference, 'family-two', 3000, 2)
    current = state(access)
    assert current['restricted_grants'] == [dict(device=device.reference, family='family-two', revision=6, expires=3000, revoked=0)]
    assert all(current[table] == rows for table, rows in before.items() if table != 'restricted_grants')
    assert support_ids.lookup(access, support, [device.reference])['family_state'] == 'ACTIVE'


def test_concurrent_renewals_have_no_lost_revision(access):
    device, support = enroll(access)
    assert parallel(lambda index: grant(peer(access), device.reference, 'family', 2000), 8) == [None] * 8
    assert state(access)['restricted_grants'][0]['revision'] == 8


def test_revoke_is_idempotent_but_explicit_regrant_is_a_new_revision(access):
    device, support = enroll(access)
    revoke(access, device)
    grant(access, device.reference, 'family', 2000)
    parallel(lambda index: revoke(peer(access), device), 8)
    assert state(access)['restricted_grants'][0]['revision'] == 2
    assert support_ids.lookup(access, support, [device.reference])['family_state'] == 'REVOKED'
    grant(access, device.reference, 'family', 3000)
    assert state(access)['restricted_grants'][0]['revision'] == 3
    assert support_ids.lookup(access, support, [device.reference])['family_state'] == 'ACTIVE'


@pytest.mark.parametrize('invalid', [dict(expires=1000), dict(expires=True), dict(expires=1001.5),
    dict(expires=MAX_INTEGER + 1), dict(minimum_revision=0), dict(minimum_revision=True),
    dict(minimum_revision=MAX_INTEGER + 1), dict(family=''), dict(family=None)])
def test_invalid_grant_does_not_mutate_any_state(access, invalid):
    device, support = enroll(access)
    before = state(access)
    with pytest.raises(ValueError, match='grant rejected'):
        grant(access, device.reference, **(dict(family='family', expires=2000, minimum_revision=1) | invalid))
    assert state(access) == before


@pytest.mark.parametrize('mutation', ['device', 'invite', 'missing-invite', 'unknown'])
def test_inactive_registration_cannot_receive_a_grant(access, mutation):
    device, support = enroll(access)
    if mutation == 'device':
        access.revoke_device(device.reference)
    else:
        with access.enrollment() as transaction:
            if mutation == 'invite':
                transaction.database.execute('UPDATE invites SET revoked=1')
            elif mutation == 'missing-invite':
                transaction.database.execute('DELETE FROM invites')
    before = state(access)
    with pytest.raises(ValueError, match='grant rejected'):
        grant(access, 'unknown' if mutation == 'unknown' else device.reference, 'family', 2000)
    assert state(access) == before


def test_device_revocation_serializes_with_admin_renewals(access):
    device, support = enroll(access)

    def attempt(index):
        if index == 0:
            peer(access).revoke_device(device.reference)
            return 'revoked'
        try:
            grant(peer(access), device.reference, 'family', 2000)
            return 'granted'
        except ValueError:
            return 'refused'

    assert 'revoked' in parallel(attempt, 8)
    assert not support_ids.lookup(access, support, [device.reference])['active']
    with pytest.raises(ValueError, match='grant rejected'):
        grant(access, device.reference, 'family', 2000)


def test_clock_is_checked_inside_the_write_transaction(access, monkeypatch):
    device, support = enroll(access)
    before = state(access)
    original = access.enrollment

    @contextmanager
    def delayed():
        with original() as transaction:
            monkeypatch.setattr(access, 'clock', lambda: 2000)
            yield transaction

    monkeypatch.setattr(access, 'enrollment', delayed)
    with pytest.raises(ValueError, match='grant rejected'):
        grant(access, device.reference, 'family', 2000)
    assert state(access) == before


def test_revision_exhaustion_never_wraps_or_becomes_a_float(access):
    device, support = enroll(access)
    grant(access, device.reference, 'family', 2000, MAX_INTEGER)
    before = state(access)
    for attempt in (lambda: grant(access, device.reference, 'family', 2000), lambda: revoke(access, device)):
        with pytest.raises(ValueError, match='revision exhausted'):
            attempt()
        assert state(access) == before
    access.revoke_device(device.reference)
    assert not support_ids.lookup(access, support, [device.reference])['active']


def test_audit_and_grant_changes_rollback_together(access):
    device, support = enroll(access)
    grant(access, device.reference, 'family', 2000)
    before = state(access)
    with pytest.raises(RuntimeError, match='synthetic failure'):
        with access.enrollment() as transaction:
            admin = transaction.restricted_admin()
            audit_id = admin.begin_audit(1000, support, 1, 0)
            admin.revoke_grant(device.reference)
            admin.finish_audit(audit_id, 'APPLIED')
            raise RuntimeError('synthetic failure')
    assert state(access) == before
    with access.enrollment() as transaction:
        admin = transaction.restricted_admin()
        audit_id = admin.begin_audit(1000, support, 1, 0)
        admin.revoke_grant(device.reference)
    assert state(access)['field_support_audit'][0]['outcome'] == 'PENDING'
    assert state(access)['restricted_grants'][0]['revoked'] == 1


def test_audit_compensation_after_applied_ack_loss_cannot_reopen(access):
    device, support = enroll(access)
    grant(access, device.reference, 'family', 2000)
    with access.enrollment() as transaction:
        admin = transaction.restricted_admin()
        audit_id = admin.begin_audit(1000, support, 0, 1)
        admin.finish_audit(audit_id, 'APPLIED')
    with peer(access).enrollment() as transaction:
        admin = transaction.restricted_admin()
        admin.revoke_grant(device.reference)
        admin.finish_audit(audit_id, 'INCOMPLETE')
        admin.finish_audit(audit_id, 'INCOMPLETE')
    before = state(access)
    with pytest.raises(ValueError, match='audit completion rejected'):
        with access.enrollment() as transaction:
            transaction.restricted_admin().finish_audit(audit_id, 'APPLIED')
    assert state(access) == before
    assert before['restricted_grants'][0]['revoked'] == 1
    assert before['field_support_audit'][0]['outcome'] == 'INCOMPLETE'
    assert device.reference not in str(before['field_support_audit'])


@pytest.mark.parametrize('invalid', [dict(timestamp=-1), dict(timestamp=True), dict(support='unknown'),
    dict(previous_state=2), dict(new_state=True)])
def test_invalid_audit_cannot_leave_partial_rows(access, invalid):
    device, support = enroll(access)
    before = state(access)
    with pytest.raises(ValueError, match='audit rejected'):
        with access.enrollment() as transaction:
            transaction.restricted_admin().begin_audit(**(dict(timestamp=1000, support=support, previous_state=0, new_state=1) | invalid))
    assert state(access) == before


@pytest.mark.parametrize('outcome', ['PENDING', 'unknown', 'APPLIED'])
def test_audit_completion_requires_an_existing_row_and_known_outcome(access, outcome):
    with pytest.raises(ValueError, match='audit completion rejected'):
        with access.enrollment() as transaction:
            transaction.restricted_admin().finish_audit(123, outcome)


def test_grant_ack_loss_requires_readback_not_blind_renewal(access, monkeypatch):
    device, support = enroll(access)
    original = access.enrollment

    @contextmanager
    def lost_ack():
        with original() as transaction:
            yield transaction
        raise ConnectionError('synthetic commit ACK loss')

    with monkeypatch.context() as patch:
        patch.setattr(access, 'enrollment', lost_ack)
        with pytest.raises(ConnectionError):
            grant(access, device.reference, 'family', 2000)
    with peer(access).enrollment() as transaction:
        row = dict(transaction.restricted_admin().grant_row(device.reference))
    assert row['revision'] == 1 and row['revoked'] == 0 and row['expires'] == 2000


@pytest.mark.parametrize('marker', ['missing', 'wrong', 'version'])
def test_postgres_marker_is_mandatory_and_never_implicitly_created(postgres_admin, marker):
    import psycopg
    device, support = enroll(postgres_admin)
    with postgres_admin.enrollment() as transaction:
        if marker == 'missing':
            transaction.database.execute('DROP TABLE ha_restricted_admin_schema')
        elif marker == 'wrong':
            transaction.database.execute("UPDATE ha_restricted_admin_schema SET purpose='wrong'")
        else:
            transaction.database.execute('UPDATE ha_restricted_admin_schema SET version=2')
    before = state(postgres_admin)
    with pytest.raises((psycopg.errors.UndefinedTable, RuntimeError)):
        grant(postgres_admin, device.reference, 'family', 2000)
    assert state(postgres_admin) == before


@pytest.mark.parametrize('values', [('unknown', 'family', 1, 2000, 0),
    (None, '', 1, 2000, 0), (None, 'family', 0, 2000, 0),
    (None, 'family', 1, -1, 0), (None, 'family', 1, 2000, 2)])
def test_postgres_native_grant_constraints(postgres_admin, values):
    import psycopg
    device, support = enroll(postgres_admin)
    with pytest.raises(psycopg.IntegrityError):
        with postgres_admin.enrollment() as transaction:
            transaction.database.execute('INSERT INTO restricted_grants VALUES (%s,%s,%s,%s,%s)',
                (values[0] or device.reference, *values[1:]))
    assert state(postgres_admin)['restricted_grants'] == []


def test_postgres_backend_loss_rolls_back_audit_and_revoke(postgres_admin, monkeypatch):
    import psycopg
    device, support = enroll(postgres_admin)
    grant(postgres_admin, device.reference, 'family', 2000)
    before = state(postgres_admin)
    original = RestrictedAdminTransaction.finish_audit

    def terminate_after(self, *args):
        original(self, *args)
        with postgres_admin.enrollment_repository.connect() as killer:
            pid = self.database.execute('SELECT pg_backend_pid() AS pid').fetchone()['pid']
            assert killer.execute('SELECT pg_terminate_backend(%s,1000) AS stopped', (pid,)).fetchone()['stopped']
        self.database.execute('SELECT 1')

    with monkeypatch.context() as patch:
        patch.setattr(RestrictedAdminTransaction, 'finish_audit', terminate_after)
        with pytest.raises(psycopg.OperationalError):
            with postgres_admin.enrollment() as transaction:
                admin = transaction.restricted_admin()
                audit_id = admin.begin_audit(1000, support, 1, 0)
                admin.revoke_grant(device.reference)
                admin.finish_audit(audit_id, 'APPLIED')
    assert state(postgres_admin) == before
    revoke(postgres_admin, device)
    assert state(postgres_admin)['restricted_grants'][0]['revoked'] == 1


def test_postgres_grants_do_not_enable_field_or_crl_publication(postgres_admin, tmp_path, monkeypatch):
    from types import SimpleNamespace
    device, support = enroll(postgres_admin)
    grant(postgres_admin, device.reference, 'family', 2000)
    before = state(postgres_admin)
    monkeypatch.setattr(support_admin.os, 'open', lambda *args, **kwargs: pytest.fail('No FIELD filesystem access allowed'))
    with pytest.raises(NotImplementedError, match='fenced file/grant migration'):
        support_admin.change(postgres_admin, tmp_path / 'absent.json', support, True, 2000)
    service = SimpleNamespace(access=postgres_admin, crl_source=lambda: pytest.fail('No CRL read allowed'))
    with pytest.raises(NotImplementedError, match='Legacy SQLite writers'):
        restricted_admin.publish_crl(service, tmp_path / 'absent.pem')
    assert state(postgres_admin) == before
