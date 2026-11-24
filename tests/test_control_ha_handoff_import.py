from dataclasses import replace
import json
import os
from pathlib import Path
import sqlite3
import uuid

import pytest

from control.friends.enrollment_postgres import PostgresEnrollment
from scripts.control_ha_handoff_fixture import closed_handoff_fixture
from scripts.control_ha_handoff_import import TABLES
from scripts.control_ha_import import ImportRejected, digest, import_snapshot, encoded
from scripts.control_ha_import_fixture import CHECKPOINT
from scripts.control_ha_sqlite_import import preflight_installed_sqlite, preflight_sqlite
from scripts.referral_postgres_rehearsal import NOW


@pytest.fixture
def fixture(tmp_path):
    return closed_handoff_fixture(tmp_path)


def capture(fixture, legacy=False):
    method = preflight_sqlite if legacy else preflight_installed_sqlite
    return method(fixture.stores, fixture.external, fixture.expected, CHECKPOINT,
                  fixture.bootstrap, fixture.service.anchor, now=NOW)


def mutate(fixture, statement, parameters=()):
    with sqlite3.connect(':memory:') as database:
        database.deserialize(fixture.stores['registry'])
        triggers = database.execute("SELECT name,sql FROM sqlite_master WHERE type='trigger' AND name LIKE 'restricted_owner_handoff_%'").fetchall()
        for name, declaration in triggers:
            database.execute('DROP TRIGGER ' + name)
        database.execute(statement, parameters)
        for name, declaration in triggers:
            database.execute(declaration)
        database.commit()
        fixture.stores['registry'] = database.serialize()


def test_installed_overlay_preserves_every_row_and_never_relaxes_v1(fixture):
    before = {name: digest(raw) for name, raw in fixture.stores.items()}
    with pytest.raises(ImportRejected, match='SOURCE_SCHEMA_UNSUPPORTED'):
        capture(fixture, legacy=True)
    result = capture(fixture)
    assert len(result.counts) == 35
    assert [result.counts[table.name] for table in TABLES] == [1, 2, 1, 1, 1]
    assert result.handoff == capture(fixture).handoff
    assert result.fingerprint != replace(result, handoff=()).fingerprint
    assert fixture.device.reference not in repr(result)
    assert before == {name: digest(raw) for name, raw in fixture.stores.items()}


@pytest.mark.parametrize('statement,reason', [
    ("UPDATE restricted_owner_handoff_operations SET phase='RETURN' WHERE generation=2", 'HANDOFF_UNSETTLED_OPERATION'),
    ("UPDATE restricted_owner_handoff_operations SET predecessor='missing' WHERE generation=2", 'HANDOFF_PREDECESSOR'),
    ("UPDATE restricted_owner_handoff_current SET generation=1", 'HANDOFF_CURRENT_BINDING'),
    ("UPDATE restricted_owner_handoff_schema SET legacy_sha256='changed'", 'HANDOFF_LEGACY_BINDING'),
    ("DELETE FROM restricted_owner_handoff_security", 'HANDOFF_SECURITY_MISSING'),
    ("UPDATE restricted_owner_handoff_security SET operation='missing'", 'HANDOFF_SECURITY_BINDING'),
    ("UPDATE restricted_owner_handoff_security SET gateway='changed'", 'HANDOFF_SECURITY_BINDING'),
    ("UPDATE restricted_owner_handoff_operations SET prepare_inputs='{}' WHERE generation=2", 'HANDOFF_INPUT_BINDING'),
    ("UPDATE restricted_owner_handoff_operations SET device='unknown' WHERE generation=2", 'HANDOFF_INPUT_BINDING'),
    ("UPDATE restricted_owner_handoff_operations SET generation=3 WHERE generation=2", 'HANDOFF_GENERATION_CHAIN'),
    ("UPDATE restricted_owner_handoff_operations SET floor='{}' WHERE generation=2", 'HANDOFF_FLOOR_SHAPE'),
    ("UPDATE restricted_owner_handoff_operations SET floor=NULL WHERE generation=1", 'HANDOFF_CLOSED_FLOOR_MISSING'),
    ("CREATE TABLE unknown(value TEXT)", 'SOURCE_SCHEMA_UNSUPPORTED'),
    ("CREATE INDEX unknown ON restricted_owner_handoff(phase)", 'SOURCE_SCHEMA_UNSUPPORTED'),
])
def test_unknown_unsettled_or_unbound_handoff_refuses(fixture, statement, reason):
    mutate(fixture, statement)
    with pytest.raises(ImportRejected, match=reason):
        capture(fixture)


def test_security_floor_cannot_regress_even_after_cleaned(fixture):
    frozen = capture(fixture)
    raw = frozen.handoff[3][0][3]
    changed = json.loads(raw)
    changed['minimum_crl'] -= 1
    mutate(fixture, 'UPDATE restricted_owner_handoff_security SET floor=?', (encoded(changed).decode(),))
    with pytest.raises(ImportRejected, match='HANDOFF_SECURITY_REGRESSION'):
        capture(fixture)


def test_changed_retained_history_changes_fingerprint(fixture):
    before = capture(fixture)
    mutate(fixture, "UPDATE restricted_owner_handoff_security SET fetch_id='another-receipt'")
    after = capture(fixture)
    assert before.rows == after.rows and before.handoff != after.handoff
    assert before.fingerprint != after.fingerprint


@pytest.fixture
def repository():
    if not os.environ.get('FC_HA_PG_PORT'):
        pytest.skip('isolated PostgreSQL rehearsal required')
    return PostgresEnrollment(port=int(os.environ['FC_HA_PG_PORT']), schema='ha_enrollment_' + uuid.uuid4().hex,
        password=Path(os.environ['FC_HA_PG_PASSWORD_FILE']).read_text().strip())


def test_exact_pg_retention_retry_and_no_activation(fixture, repository):
    frozen = capture(fixture)
    result = import_snapshot(repository, frozen)
    assert result['result'] == 'IMPORTED' and result['activation'] == 'FORBIDDEN'
    assert import_snapshot(repository, frozen)['result'] == 'EXACT_RETRY'
    with repository.transaction() as transaction:
        assert transaction.database.execute('SELECT count(*) AS count FROM pg_tables WHERE schemaname=current_schema()').fetchone()['count'] == 49
    mutate(fixture, "UPDATE restricted_owner_handoff_security SET fetch_id='another-receipt'")
    with pytest.raises(ImportRejected, match='TARGET_NOT_SAME_IMPORT'):
        import_snapshot(repository, capture(fixture))


@pytest.mark.parametrize('table', TABLES, ids=lambda table: table.name)
@pytest.mark.parametrize('verb', ['DELETE FROM', 'TRUNCATE', 'INSERT INTO', 'UPDATE'])
def test_pg_retained_domain_is_read_only(fixture, repository, table, verb):
    import psycopg
    frozen = capture(fixture)
    import_snapshot(repository, frozen)
    statement = verb + ' ' + table.name
    if verb == 'INSERT INTO':
        statement += ' SELECT * FROM ' + table.name + ' WHERE false'
    elif verb == 'TRUNCATE':
        statement += ' CASCADE'
    elif verb == 'UPDATE':
        statement += ' SET ' + table.columns[0] + '=' + table.columns[0]
    with pytest.raises(psycopg.errors.CheckViolation):
        with repository.transaction() as transaction:
            transaction.database.execute(statement)
    assert import_snapshot(repository, frozen)['result'] == 'EXACT_RETRY'


def test_pg_retained_security_update_is_forbidden(fixture, repository):
    import psycopg
    frozen = capture(fixture)
    import_snapshot(repository, frozen)
    with pytest.raises(psycopg.errors.CheckViolation):
        with repository.transaction() as transaction:
            transaction.database.execute("UPDATE restricted_owner_handoff_security SET floor='{}'")
    assert import_snapshot(repository, frozen)['result'] == 'EXACT_RETRY'


@pytest.mark.parametrize('stage', [table.name for table in TABLES] + ['before_commit', 'after_commit'])
def test_all_handoff_rows_share_atomic_import_and_readback(fixture, repository, stage):
    frozen = capture(fixture)
    def fault(point):
        if point == stage:
            raise ConnectionError('synthetic import interruption')
    with pytest.raises(ImportRejected, match='IMPORT_OUTCOME_REQUIRES_READBACK'):
        import_snapshot(repository, frozen, fault=fault)
    assert import_snapshot(repository, frozen)['result'] == ('EXACT_RETRY' if stage == 'after_commit' else 'IMPORTED')
