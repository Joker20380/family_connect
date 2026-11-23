from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import sqlite3
import uuid

import pytest

from control.friends.access import Access, Rejected
from control.friends import transport_policy
from control.friends.enrollment_postgres import PostgresEnrollment
from scripts.control_ha_import import EXTERNAL_ROLES, TABLES, ImportRejected, digest, preflight, import_snapshot, verify
from scripts.control_ha_import_fixture import bundle, CHECKPOINT
from scripts.referral_postgres_rehearsal import NOW


@pytest.fixture
def inputs(tmp_path):
    return bundle(tmp_path)


def capture(inputs):
    return preflight(*inputs[:3], CHECKPOINT)


def mutate(inputs, store, statement, parameters=()):
    database = sqlite3.connect(':memory:')
    try:
        database.deserialize(inputs[0][store])
        database.execute(statement, parameters)
        database.commit()
        inputs[0][store] = database.serialize()
    finally:
        database.close()


def test_preflight_covers_all_families_without_changing_sources(inputs):
    before = {name: digest(raw) for name, raw in inputs[0].items()}
    snapshot = capture(inputs)
    assert len(snapshot.counts) == 30 and sum(snapshot.counts.values()) == 34
    assert all(snapshot.counts.values()) and len(snapshot.external_digests) == 8
    assert {name: digest(raw) for name, raw in inputs[0].items()} == before
    assert snapshot.fingerprint == capture(inputs).fingerprint
    assert inputs[3].reference not in repr(snapshot)
    events = snapshot.rows[[table.name for table in TABLES].index('events')]
    assert {row[-1] for row in events} == {3, 9}


@pytest.mark.parametrize('store', ['registry', 'metadata', 'diagnostics', 'notices'])
def test_missing_store_refuses_even_if_other_snapshots_are_valid(inputs, store):
    del inputs[0][store]
    with pytest.raises(ImportRejected, match='STORE_COVERAGE'):
        capture(inputs)


@pytest.mark.parametrize('role', sorted(EXTERNAL_ROLES))
def test_missing_external_role_refuses(inputs, role):
    del inputs[1][role]
    with pytest.raises(ImportRejected, match='EXTERNAL_COVERAGE'):
        capture(inputs)


@pytest.mark.parametrize('role', sorted(EXTERNAL_ROLES))
def test_unresolved_external_reference_refuses(inputs, role):
    envelope = json.loads(inputs[1][role])
    envelope['references'] = []
    inputs[1][role] = json.dumps(envelope).encode()
    inputs[2][role] = digest(inputs[1][role])
    with pytest.raises(ImportRejected, match='EXTERNAL_REFERENCES'):
        capture(inputs)


@pytest.mark.parametrize('statement,code', [
    ('CREATE TABLE unclassified(secret TEXT)', 'SOURCE_SCHEMA'),
    ('CREATE VIEW unclassified AS SELECT * FROM devices', 'SOURCE_SCHEMA'),
    ('CREATE TRIGGER extra AFTER INSERT ON devices BEGIN SELECT 1; END', 'SOURCE_SCHEMA'),
    ('ALTER TABLE devices ADD COLUMN unknown TEXT', 'SOURCE_SCHEMA'),
    ('DROP TABLE referral_claims', 'SOURCE_SCHEMA'),
    ('UPDATE ha_import_source SET version=2', 'SOURCE_CHECKPOINT'),
    ("UPDATE ha_import_source SET checkpoint='other'", 'SOURCE_CHECKPOINT'),
    ("UPDATE ha_import_source SET purpose='production'", 'SOURCE_CHECKPOINT'),
])
def test_unversioned_or_inconsistent_source_is_not_translated(inputs, statement, code):
    mutate(inputs, 'registry', statement)
    with pytest.raises(ImportRejected, match=code):
        capture(inputs)


@pytest.mark.parametrize('column,value', [('revoked', 'wrong'), ('revoked', 0.5), ('revoked', None),
                                         ('public', b'blob'), ('public', 'text\x00suffix'), ('public', None)])
def test_sqlite_dynamic_typing_is_not_silently_coerced(inputs, column, value):
    mutate(inputs, 'registry', 'UPDATE devices SET ' + column + '=?', (value,))
    with pytest.raises(ImportRejected, match='SOURCE_VALUE_TYPE'):
        capture(inputs)


@pytest.mark.parametrize('change', ['digest', 'checkpoint', 'duplicate', 'corrupt', 'references'])
def test_external_manifest_drift_is_rejected(inputs, change):
    role = 'aliases'
    value = json.loads(inputs[1][role])
    if change == 'checkpoint':
        value['checkpoint'] = '2' * 32
    elif change == 'references':
        value['references'] = [None]
    raw = json.dumps(value).encode()
    if change == 'duplicate':
        raw = raw[:-1] + b',"role":"aliases"}'
    elif change == 'corrupt':
        raw = b'{not json}'
    elif change == 'digest':
        raw += b' '
    inputs[1][role] = raw
    if change != 'digest':
        inputs[2][role] = digest(raw)
    with pytest.raises(ImportRejected):
        capture(inputs)


@pytest.fixture
def repository():
    if not os.environ.get('FC_HA_PG_PORT'):
        pytest.skip('Run scripts.control_ha_import_rehearsal for real PostgreSQL import contracts')
    return PostgresEnrollment(port=int(os.environ['FC_HA_PG_PORT']), schema='ha_enrollment_' + uuid.uuid4().hex,
        password=Path(os.environ['FC_HA_PG_PASSWORD_FILE']).read_text().strip())


def absent(repository):
    with repository.connect() as database:
        return database.execute('SELECT 1 FROM pg_namespace WHERE nspname=%s', (repository.schema,)).fetchone() is None


def test_atomic_import_retry_projections_and_one_use_proof(inputs, repository, tmp_path):
    snapshot = capture(inputs)
    assert import_snapshot(repository, snapshot)['result'] == 'IMPORTED'
    assert import_snapshot(repository, snapshot)['result'] == 'EXACT_RETRY'
    source = Access(tmp_path / 'source.sqlite', clock=lambda: NOW)
    target = Access(None, clock=lambda: NOW, enrollment_repository=repository)
    with source.read_enrollment() as previous, target.read_enrollment() as current:
        for node in transport_policy.NODES:
            assert transport_policy.read_snapshot(previous.paid(), node, NOW) == transport_policy.read_snapshot(current.paid(), node, NOW)
    target.complete(inputs[4], 'status')
    with pytest.raises(Rejected):
        target.complete(inputs[4], 'status')
    with pytest.raises(ImportRejected, match='TARGET_CHANGED'):
        import_snapshot(repository, snapshot)


@pytest.mark.parametrize('point', ['schema', 'devices', 'restricted_grants', 'device_metadata', 'edit_operations', 'before_commit'])
def test_failure_rolls_back_schema_rows_and_receipt(inputs, repository, point):
    def fault(stage):
        if stage == point:
            raise OSError('synthetic interruption')
    snapshot = capture(inputs)
    with pytest.raises(ImportRejected, match='IMPORT_OUTCOME_REQUIRES_READBACK'):
        import_snapshot(repository, snapshot, fault=fault)
    assert absent(repository)
    assert import_snapshot(repository, snapshot)['result'] == 'IMPORTED'


def test_lost_commit_reply_recovers_by_exact_readback(inputs, repository):
    def fault(stage):
        if stage == 'after_commit':
            raise ConnectionError('synthetic reply loss')
    snapshot = capture(inputs)
    with pytest.raises(ImportRejected, match='IMPORT_OUTCOME_REQUIRES_READBACK'):
        import_snapshot(repository, snapshot, fault=fault)
    assert not absent(repository)
    assert import_snapshot(repository, snapshot)['result'] == 'EXACT_RETRY'


def test_concurrent_import_has_one_creator(inputs, repository):
    snapshot = capture(inputs)
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: import_snapshot(repository, snapshot)['result'], range(2)))
    assert sorted(results) == ['EXACT_RETRY', 'IMPORTED']


@pytest.mark.parametrize('statement', [
    "UPDATE referral_links SET sponsor='missing'",
    "UPDATE paid_beta_subscriptions SET state='unknown'",
    'UPDATE device_metadata SET epoch=0',
    'INSERT INTO devices SELECT * FROM devices',
])
def test_native_constraints_reject_bad_rows_without_partial_import(inputs, repository, statement):
    mutate(inputs, 'metadata' if 'device_metadata' in statement else 'registry', statement)
    snapshot = capture(inputs)
    with pytest.raises(ImportRejected, match='IMPORT_OUTCOME_REQUIRES_READBACK'):
        import_snapshot(repository, snapshot)
    assert absent(repository)


@pytest.mark.parametrize('statement', [
    'DROP TRIGGER metadata_monotonic ON device_metadata',
    'ALTER TABLE devices ALTER COLUMN public DROP NOT NULL',
    "UPDATE ha_notices_schema SET purpose='changed'",
    'CREATE TABLE extra(id INTEGER)',
    'UPDATE devices SET revoked=1',
    'ALTER TABLE devices DISABLE TRIGGER ALL',
    'ALTER SEQUENCE field_support_audit_id_seq CYCLE',
    "SELECT setval('field_support_audit_id_seq',1,false)",
    "SELECT nextval('field_support_audit_id_seq')",
])
def test_retry_refuses_changed_target_data_or_guards(inputs, repository, statement):
    snapshot = capture(inputs)
    import_snapshot(repository, snapshot)
    with repository.transaction() as enrollment:
        enrollment.database.execute(statement)
    with pytest.raises(ImportRejected):
        import_snapshot(repository, snapshot)


def test_existing_enrollment_store_is_not_overwritten(inputs, repository):
    repository.initialize_synthetic()
    with pytest.raises(ImportRejected, match='TARGET_NOT_SAME_IMPORT'):
        import_snapshot(repository, capture(inputs))


def test_identity_sequence_is_reseeded_after_import(inputs, repository):
    import_snapshot(repository, capture(inputs))
    with repository.transaction() as enrollment:
        row = enrollment.database.execute("INSERT INTO field_support_audit(timestamp,support_id,previous_state,new_state,outcome) "
            "VALUES (%s,'synthetic',0,1,'synthetic') RETURNING id", (NOW,)).fetchone()
        assert row['id'] == 42


def test_empty_audit_sequence_starts_at_one(inputs, repository):
    mutate(inputs, 'registry', 'DELETE FROM field_support_audit')
    snapshot = capture(inputs)
    import_snapshot(repository, snapshot)
    assert import_snapshot(repository, snapshot)['result'] == 'EXACT_RETRY'
    with repository.transaction() as enrollment:
        assert enrollment.database.execute("SELECT nextval('field_support_audit_id_seq') AS value").fetchone()['value'] == 1


def test_types_null_unicode_and_rowid_order_survive_import(inputs, repository):
    mutate(inputs, 'registry', 'UPDATE device_support SET platform=?,last_seen=?', ('Синтетика 🧪', -(2**63)))
    snapshot = capture(inputs)
    import_snapshot(repository, snapshot)
    with repository.transaction() as enrollment:
        verify(enrollment.database, snapshot)
        enrollment.notices().save_event(dict(id='c' * 32, title='Synthetic storage probe'))
        assert enrollment.database.execute("SELECT position FROM events WHERE id=%s", ('c' * 32,)).fetchone()['position'] == 10


@pytest.mark.parametrize('statement', [
    "UPDATE paid_beta_events SET event_type='revoke'",
    'DELETE FROM restricted_crl_publications',
    'TRUNCATE gateway_selection_events',
    'DELETE FROM events',
    'UPDATE device_metadata SET epoch=2',
])
def test_import_keeps_native_immutability_and_consent_guards(inputs, repository, statement):
    import psycopg
    snapshot = capture(inputs)
    import_snapshot(repository, snapshot)
    with pytest.raises(psycopg.Error):
        with repository.transaction() as enrollment:
            enrollment.database.execute(statement)
    with repository.transaction() as enrollment:
        verify(enrollment.database, snapshot)
