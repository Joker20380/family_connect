import copy
import json
import os
import subprocess
import sys
import threading
import time
import uuid

import psycopg
from psycopg import sql
import pytest

from fc_control_plane.capture_pg_boundary import PostgresBoundary, fingerprint, scope


@pytest.fixture
def database():
    options = dict(host=os.environ.get('POSTGRES_HOST', '127.0.0.1'),
        port=os.environ.get('POSTGRES_PORT', '5432'), user='fc_control_plane',
        password=os.environ['POSTGRES_PASSWORD'], autocommit=True, connect_timeout=5)
    name = 'fc_capture_lab_' + uuid.uuid4().hex
    with psycopg.connect(dbname='fc_control_plane', **options) as administrator:
        administrator.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name)))
        try:
            with psycopg.connect(dbname=name, **options) as connection:
                connection.execute('CREATE TABLE effects (id bigint GENERATED ALWAYS AS IDENTITY, '
                                   'operation text UNIQUE, value text)')
                connection.execute("INSERT INTO effects(operation,value) VALUES ('history','unchanged')")
            yield dict(dbname=name, **options)
        finally:
            administrator.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(name)))


def boundary(options, **settings):
    connection = psycopg.connect(**options)
    return PostgresBoundary(connection, scope(connection), **settings)


@pytest.mark.parametrize('statement', [
    "INSERT INTO effects(operation,value) VALUES ('late','one')",
    "UPDATE effects SET value='changed'", 'DELETE FROM effects', 'TRUNCATE effects',
    "SELECT nextval('effects_id_seq')", "SELECT setval('effects_id_seq',100)",
    'CREATE TABLE late_table (id int)', 'ALTER TABLE effects ADD COLUMN late int',
    'DROP TABLE effects', 'CREATE SCHEMA late_schema', "SELECT lo_create(0)",
])
def test_every_logical_write_waits_for_boundary(database, statement):
    with boundary(database) as held, psycopg.connect(**database) as late:
        late.execute("SET lock_timeout='80ms'")
        with pytest.raises(psycopg.errors.LockNotAvailable):
            late.execute(statement)
        assert len(held.check()) == 64
        assert late.execute('SELECT operation,value FROM effects').fetchall() == [('history', 'unchanged')]
        assert late.execute('SELECT last_value FROM effects_id_seq').fetchone() == (1,)


def test_existing_accepted_transaction_refuses_without_mutation(database):
    with psycopg.connect(**database) as prior:
        prior.execute('BEGIN')
        prior.execute("UPDATE effects SET value='accepted'")
        held = boundary(database)
        with pytest.raises(psycopg.errors.LockNotAvailable):
            held.__enter__()
        assert held.connection.closed and not held.active
        prior.rollback()
        assert prior.execute('SELECT value FROM effects').fetchone() == ('unchanged',)


def test_coverage_change_and_incomplete_coverage_refuse(database):
    for mutate in ('omit', 'ddl'):
        connection = psycopg.connect(**database)
        expected = copy.deepcopy(scope(connection))
        if mutate == 'omit':
            expected['relations'] = []
        else:
            connection.execute('ALTER TABLE effects ADD COLUMN new_column int')
        with pytest.raises(ValueError, match='PG_BOUNDARY_COVERAGE_CHANGED'):
            PostgresBoundary(connection, expected).__enter__()
        assert connection.closed


def test_reacquired_transaction_is_not_same_barrier(database):
    with boundary(database) as held:
        held.connection.rollback()
        held.connection.execute('BEGIN')
        with pytest.raises(ValueError, match='PG_BOUNDARY_LOST'):
            held.check()
    with psycopg.connect(**database) as normal:
        normal.execute("INSERT INTO effects(operation,value) VALUES ('normal','resumed')")


def test_event_trigger_setval_refuses_before_sequence_ddl(database):
    held = boundary(database)
    with psycopg.connect(**database) as administrator:
        administrator.execute("CREATE FUNCTION ddl_sequence_effect() RETURNS event_trigger LANGUAGE plpgsql "
            "AS $$ BEGIN PERFORM setval('public.effects_id_seq',777); END $$")
        administrator.execute("CREATE EVENT TRIGGER capture_ddl ON ddl_command_start "
            "WHEN TAG IN ('ALTER SEQUENCE') EXECUTE FUNCTION ddl_sequence_effect()")
        original = administrator.execute('SELECT last_value,is_called FROM effects_id_seq').fetchone()
        try:
            with pytest.raises(ValueError, match='PG_BOUNDARY_EVENT_TRIGGERS'):
                held.__enter__()
        finally:
            held.release()
        assert administrator.execute('SELECT last_value,is_called FROM effects_id_seq').fetchone() == original
        assert administrator.execute('SELECT operation,value FROM effects').fetchall() == [('history','unchanged')]
        administrator.execute('ALTER SEQUENCE effects_id_seq CACHE 1')
        assert administrator.execute('SELECT last_value FROM effects_id_seq').fetchone() == (777,)


@pytest.mark.parametrize('statement', [
    'CREATE TABLE information_schema.unexpected (value int)',
    'CREATE SEQUENCE information_schema.unexpected',
    'ALTER TABLE information_schema.sql_features ADD COLUMN unexpected int',
])
def test_unknown_information_schema_persistent_scope_refuses(database, statement):
    with psycopg.connect(**database) as administrator:
        administrator.execute(statement)
        with pytest.raises(ValueError, match='PG_BOUNDARY_INFORMATION_SCHEMA'):
            scope(administrator)


def test_stock_information_schema_tables_are_physically_held(database):
    with boundary(database) as held, psycopg.connect(**database) as late:
        late.execute("SET lock_timeout='80ms'")
        for name in ('sql_features', 'sql_implementation_info', 'sql_parts', 'sql_sizing'):
            with pytest.raises(psycopg.errors.LockNotAvailable):
                late.execute(sql.SQL('DELETE FROM information_schema.{}').format(sql.Identifier(name)))
        held.check()


def test_event_trigger_installation_is_blocked_while_held(database):
    with psycopg.connect(**database) as administrator:
        administrator.execute('CREATE FUNCTION empty_ddl() RETURNS event_trigger LANGUAGE plpgsql '
                              'AS $$ BEGIN END $$')
    with boundary(database) as held, psycopg.connect(**database) as late:
        late.execute("SET lock_timeout='80ms'")
        with pytest.raises(psycopg.errors.LockNotAvailable):
            late.execute('CREATE EVENT TRIGGER late_ddl ON ddl_command_start EXECUTE FUNCTION empty_ddl()')
        held.check()


def test_deadline_releases_locks_without_controller_cleanup(database):
    held = boundary(database, milliseconds=300)
    held.__enter__()
    time.sleep(.4)
    with psycopg.connect(**database) as late:
        late.execute("SET lock_timeout='150ms'")
        late.execute("INSERT INTO effects(operation,value) VALUES ('late','resumed')")
    with pytest.raises(ValueError, match='PG_BOUNDARY_LOST'):
        held.check()
    with pytest.raises(psycopg.errors.TransactionTimeout):
        held.release()
    assert held.connection.closed


def test_queued_effect_and_lost_response_replay_once(database):
    held = boundary(database)
    before = fingerprint(held.expected)
    errors = []
    ready = threading.Event()
    finished = threading.Event()
    def writer():
        try:
            with psycopg.connect(**database) as connection:
                ready.set()
                connection.execute("INSERT INTO effects(operation,value) VALUES ('queued','one') "
                                   'ON CONFLICT (operation) DO NOTHING')
                finished.set()
        except Exception as error:
            errors.append(type(error).__name__)
    with held:
        thread = threading.Thread(target=writer)
        thread.start()
        assert ready.wait(3) and not finished.wait(.1)
        assert held.check() and not errors
    thread.join(3)
    assert finished.is_set() and not errors and not thread.is_alive()
    with psycopg.connect(**database) as normal:
        normal.execute("INSERT INTO effects(operation,value) VALUES ('queued','one') ON CONFLICT (operation) DO NOTHING")
        assert normal.execute("SELECT count(*) FROM effects WHERE operation='queued'").fetchone() == (1,)
        assert fingerprint(scope(normal)) == before
    with pytest.raises(ValueError, match='PG_BOUNDARY_NO_RETRY'):
        held.__enter__()


def test_killed_controller_rolls_back_boundary(database):
    code = """import json,sys,time,psycopg
from fc_control_plane.capture_pg_boundary import PostgresBoundary,scope
connection=psycopg.connect(**json.loads(sys.stdin.readline()))
with PostgresBoundary(connection,scope(connection),milliseconds=2500):
    print('HELD',flush=True)
    time.sleep(30)
"""
    child = subprocess.Popen([sys.executable, '-B', '-c', code], stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        child.stdin.write(json.dumps(database) + '\n')
        child.stdin.flush()
        assert child.stdout.readline().strip() == 'HELD'
        child.kill()
        child.wait(timeout=3)
        with psycopg.connect(**database) as late:
            late.execute("SET lock_timeout='3s'")
            late.execute("INSERT INTO effects(operation,value) VALUES ('after-death','one')")
        assert child.stderr.read() == ''
    finally:
        if child.poll() is None:
            child.kill()
            child.wait(timeout=3)
        for stream in (child.stdin, child.stdout, child.stderr):
            stream.close()


def test_non_public_persistent_state_is_not_silently_omitted(database):
    with psycopg.connect(**database) as connection:
        connection.execute('CREATE SCHEMA unseen')
        connection.execute('CREATE TABLE unseen.effects (id int)')
        with pytest.raises(ValueError, match='PG_BOUNDARY_UNSUPPORTED_RELATION'):
            scope(connection)


def test_first_failure_survives_cleanup_timeout(database):
    held = boundary(database, milliseconds=300)
    with pytest.raises(ValueError, match='ORIGINAL_FAILURE') as failure:
        with held:
            time.sleep(.4)
            raise ValueError('ORIGINAL_FAILURE')
    assert held.connection.closed
    assert failure.value.__notes__ == ['PG_BOUNDARY_CLEANUP_TransactionTimeout']


def test_preexisting_sequence_cache_cannot_bypass_boundary(database):
    with psycopg.connect(**database) as prior:
        prior.execute('ALTER SEQUENCE effects_id_seq CACHE 32')
        prior.execute("SELECT nextval('effects_id_seq')")
        sequence_before = prior.execute('SELECT last_value,is_called FROM effects_id_seq').fetchone()
        with boundary(database) as held:
            prior.execute("SET lock_timeout='80ms'")
            with pytest.raises(psycopg.errors.LockNotAvailable):
                prior.execute("SELECT nextval('effects_id_seq')")
            assert held.check()
        assert prior.execute('SELECT last_value,is_called FROM effects_id_seq').fetchone() == sequence_before
        assert prior.execute("SELECT seqcache FROM pg_sequence WHERE seqrelid='effects_id_seq'::regclass").fetchone() == (32,)
