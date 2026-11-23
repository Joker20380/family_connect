from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import sqlite3
import uuid

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from control.friends import restricted_admin
from control.friends.access import Access
from control.friends.enrollment_postgres import PostgresEnrollment
from scripts.control_ha_import import ImportRejected, TABLES, digest, import_snapshot
from scripts.control_ha_import_fixture import CHECKPOINT
from scripts.control_ha_sqlite_fixture import joint_fixture, exercise_import
from scripts.control_ha_sqlite_import import preflight_sqlite
from scripts.referral_postgres_rehearsal import NOW


@pytest.fixture
def joint(tmp_path):
    return joint_fixture(tmp_path)


def capture(joint):
    return preflight_sqlite(joint.stores, joint.external, joint.expected, CHECKPOINT,
                            joint.bootstrap, joint.service.anchor, now=NOW)


def mutate(joint, store, statement, values=()):
    database = sqlite3.connect(':memory:')
    try:
        database.deserialize(joint.stores[store])
        database.execute(statement, values)
        database.commit()
        joint.stores[store] = database.serialize()
    finally:
        database.close()


def test_actual_application_schemas_and_29_tables_are_preserved(joint):
    before = {name: digest(raw) for name, raw in joint.stores.items()}
    frozen = capture(joint)
    assert len(frozen.counts) == 30
    assert [name for name, count in frozen.counts.items() if count == 0] == ['restricted_crl_publications']
    assert {name: digest(raw) for name, raw in joint.stores.items()} == before
    assert frozen.crl_anchor[3] == 2
    assert frozen.fingerprint == capture(joint).fingerprint
    assert 'SYNTHETIC_STORAGE_SENTINEL' not in str(frozen.rows)


@pytest.mark.parametrize('store', ['registry', 'metadata', 'diagnostics', 'notices'])
@pytest.mark.parametrize('change', ['missing', 'corrupt', 'extra', 'version', 'application', 'index'])
def test_unknown_incomplete_or_changed_sources_refuse(joint, store, change):
    if change == 'missing':
        del joint.stores[store]
    elif change == 'corrupt':
        joint.stores[store] = b'not a SQLite image'
    else:
        table = next(table for table in TABLES if table.store == store)
        statement = dict(extra='CREATE TABLE unknown(value TEXT)', version='PRAGMA user_version=2',
                         application='PRAGMA application_id=9',
                         index='CREATE INDEX unknown ON ' + table.name + '(' + table.columns[0] + ')')[change]
        mutate(joint, store, statement)
    with pytest.raises(ImportRejected):
        capture(joint)


@pytest.mark.parametrize('statement', [
    'DROP TABLE restricted_crl_sequence',
    'CREATE TABLE restricted_crl_publications(operation_id TEXT)',
    'DROP TRIGGER paid_beta_event_no_update',
    'ALTER TABLE invites ADD COLUMN unknown TEXT',
])
def test_unknown_migration_history_is_not_silently_accepted(joint, statement):
    mutate(joint, 'registry', statement)
    with pytest.raises(ImportRejected, match='SOURCE_SCHEMA_UNSUPPORTED'):
        capture(joint)


@pytest.mark.parametrize('store,statement', [
    ('metadata', "UPDATE device_metadata SET device='unknown'"),
    ('diagnostics', "UPDATE snapshots SET device='unknown'"),
    ('diagnostics', "UPDATE snapshots SET support='FC-2222-2222'"),
    ('notices', "UPDATE device_admins SET device='unknown'"),
])
def test_cross_store_binding_refuses_orphans(joint, store, statement):
    if store == 'metadata':
        statement += ' WHERE enabled=0'
    mutate(joint, store, statement)
    with pytest.raises(ImportRejected, match='SOURCE_(DEVICE|SUPPORT)_BINDING'):
        capture(joint)


@pytest.mark.parametrize('change', ['missing', 'corrupt', 'checkpoint', 'crl', 'anchor', 'floor', 'certificate'])
def test_signed_crl_bootstrap_and_certificate_binding_fail_closed(joint, change):
    if change in ('checkpoint', 'crl'):
        envelope = json.loads(joint.bootstrap)
        envelope[change] = 'bad'
        joint.bootstrap = json.dumps(envelope).encode()
    elif change == 'missing':
        joint.bootstrap = b''
    elif change == 'corrupt':
        joint.bootstrap = b'not json'
    elif change == 'anchor':
        joint.service.anchor = Ed25519PrivateKey.generate().public_key().public_bytes_raw()
    elif change == 'floor':
        mutate(joint, 'registry', 'UPDATE restricted_crl_sequence SET sequence=100')
    else:
        mutate(joint, 'registry', "UPDATE restricted_certificates SET certificate='not a certificate'")
    with pytest.raises(ImportRejected):
        capture(joint)


@pytest.mark.parametrize('limit', ['MAX_ROWS', 'MAX_BYTES'])
def test_source_bounds_are_enforced(joint, monkeypatch, limit):
    monkeypatch.setattr('scripts.control_ha_sqlite_import.' + limit, 1)
    with pytest.raises(ImportRejected, match='ROW_LIMIT|STORE_BOUNDS'):
        capture(joint)


@pytest.fixture
def repository():
    if not os.environ.get('FC_HA_PG_PORT'):
        pytest.skip('Run scripts.control_ha_sqlite_rehearsal for real PostgreSQL qualification')
    return PostgresEnrollment(port=int(os.environ['FC_HA_PG_PORT']), schema='ha_enrollment_' + uuid.uuid4().hex,
        password=Path(os.environ['FC_HA_PG_PASSWORD_FILE']).read_text().strip())


def test_joint_business_operations_continue_after_import(joint, repository):
    frozen = capture(joint)
    assert import_snapshot(repository, frozen)['result'] == 'IMPORTED'
    assert import_snapshot(repository, frozen)['result'] == 'EXACT_RETRY'
    assert all(exercise_import(joint, repository).values())
    with pytest.raises(ImportRejected):
        import_snapshot(repository, frozen)


@pytest.mark.parametrize('stage', ['schema', 'restricted_certificates', 'device_metadata', 'before_commit', 'after_commit'])
def test_bootstrap_is_atomic_with_data_and_receipt(joint, repository, stage):
    frozen = capture(joint)
    def fault(point):
        if point == stage:
            raise ConnectionError('synthetic lost import connection')
    with pytest.raises(ImportRejected, match='IMPORT_OUTCOME_REQUIRES_READBACK'):
        import_snapshot(repository, frozen, fault=fault)
    assert import_snapshot(repository, frozen)['result'] == ('EXACT_RETRY' if stage == 'after_commit' else 'IMPORTED')


@pytest.mark.parametrize('statement', [
    'DELETE FROM ha_import_crl_anchor', 'TRUNCATE ha_import_crl_anchor',
    'UPDATE ha_import_crl_anchor SET sequence=1',
])
def test_crl_import_anchor_is_immutable(joint, repository, statement):
    import psycopg
    frozen = capture(joint)
    import_snapshot(repository, frozen)
    with pytest.raises(psycopg.errors.CheckViolation):
        with repository.transaction() as transaction:
            transaction.database.execute(statement)
    assert import_snapshot(repository, frozen)['result'] == 'EXACT_RETRY'


def test_import_anchor_only_allows_exact_first_predecessor(joint, repository):
    from copy import copy
    import_snapshot(repository, capture(joint))
    service = copy(joint.service)
    service.access = Access(None, clock=lambda: NOW, enrollment_repository=repository)
    previous = joint.service.crl_source()
    with pytest.raises(ValueError, match='CRL predecessor mismatch'):
        restricted_admin.prepare_crl(service, 'changed-predecessor', previous + b'\n')
    first = restricted_admin.prepare_crl(service, 'first-after-import', previous)
    assert first['sequence'] == 3 and first['local_receipt'] == 0
    assert restricted_admin.prepare_crl(service, 'first-after-import', previous) == first
    with pytest.raises(ValueError, match='CRL predecessor mismatch'):
        restricted_admin.prepare_crl(service, 'stale-after-import', previous)
    second = restricted_admin.prepare_crl(service, 'second-after-import', first['payload'].encode())
    assert second['sequence'] == 4


def test_source_image_provenance_is_bound_to_import_receipt(joint, repository):
    first = capture(joint)
    import_snapshot(repository, first)
    mutate(joint, 'registry', 'PRAGMA schema_version=999')
    second = capture(joint)
    assert first.rows == second.rows and first.fingerprint != second.fingerprint
    with pytest.raises(ImportRejected, match='TARGET_NOT_SAME_IMPORT'):
        import_snapshot(repository, second)


def test_concurrent_application_import_is_not_two_writers(joint, repository):
    frozen = capture(joint)
    with ThreadPoolExecutor(max_workers=2) as executor:
        values = list(executor.map(lambda _: import_snapshot(repository, frozen)['result'], range(2)))
    assert sorted(values) == ['EXACT_RETRY', 'IMPORTED']
