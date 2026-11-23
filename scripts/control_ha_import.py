"""Versioned synthetic four-store import. No live paths, activation or DDL translation."""
from contextlib import contextmanager
from dataclasses import dataclass, field
import hashlib
import json
import sqlite3

from control.friends import enrollment_postgres

VERSION = 1
PURPOSE = 'family-connect/ha-all-store-synthetic/v1/not-for-activation'
MAX_BYTES = 16 * 1024 * 1024
MAX_ROWS = 20000
EXTERNAL_ROLES = frozenset(('aliases', 'admission', 'sender_policy', 'routing_files',
                           'issuer_material', 'maintenance_state', 'node_allocations', 'receiver_state'))


@dataclass(frozen=True)
class Table:
    store: str
    name: str
    fields: str

    @property
    def columns(self):
        return tuple(part.split(':')[0] for part in self.fields.split())

    @property
    def types(self):
        return tuple(part.split(':')[1] for part in self.fields.split())


TABLES = (
    Table('registry', 'invites', 'hash:text device:text? revoked:int'),
    Table('registry', 'devices', 'device:text public:text wg:text tcp:text revoked:int'),
    Table('registry', 'challenges', 'nonce:text device:text public:text wg:text purpose:text invite:text? expires:int used:int'),
    Table('registry', 'device_support', 'device:text support_id:text platform:text? app_version:text? version_code:int? last_seen:int? observation_source:text?'),
    Table('registry', 'field_support_audit', 'id:int timestamp:int support_id:text previous_state:int new_state:int outcome:text'),
    Table('registry', 'paid_beta_subscriptions', 'device:text state:text period_start:int paid_until:int grace_until:int? created_at:int updated_at:int version:int last_event_id:text revoked_at:int?'),
    Table('registry', 'paid_beta_events', 'event_id:text device:text event_type:text occurred_at:int previous_state:text? new_state:text period_start:int paid_until:int grace_until:int? reference_hash:text payload_hash:text applied_at:int result:text'),
    Table('registry', 'referral_links', 'token:text sponsor:text'),
    Table('registry', 'referral_claims', 'request:text sponsor:text invite:text created:int'),
    Table('registry', 'restricted_grants', 'device:text family:text revision:int expires:int? revoked:int'),
    Table('registry', 'restricted_challenges', 'nonce:text revision:int family:text expires:int'),
    Table('registry', 'restricted_certificates', 'device:text revision:int serial:text expires:int certificate:text'),
    Table('registry', 'restricted_readiness_results', 'correlation:text nonce:text device:text challenge_at:int fetch_id:text? fetch_at:int? revision:int? minimum_crl:int? expires:int? ack:text? ack_at:int? gateway_binding:text'),
    Table('registry', 'chat_bindings', 'device:text public:text support_sender:text?'),
    Table('registry', 'chat_challenges', 'nonce:text device:text public:text expires:int used:int'),
    Table('registry', 'chat_sequence', 'id:int value:int'),
    Table('registry', 'chat_service_senders', 'public:text enabled:int'),
    Table('registry', 'gateway_routing_state', 'singleton:int policy_sha256:text generation:int'),
    Table('registry', 'gateway_assignments', 'device:text catalog_sha256:text node:text sequence:int'),
    Table('registry', 'gateway_assignment_events', 'operation_id:text request_sha256:text device:text previous_sha256:text catalog_sha256:text'),
    Table('registry', 'gateway_selection_events', 'operation_id:text request_sha256:text catalog_sha256:text policy_sha256:text sequence:int'),
    Table('registry', 'restricted_crl_sequence', 'singleton:int sequence:int'),
    Table('registry', 'restricted_crl_publications', 'operation_id:text request_sha256:text sequence:int payload:text payload_sha256:text issued_at:int expires_at:int local_receipt:int'),
    Table('metadata', 'device_metadata', 'device:text epoch:int sequence:int digest:text enabled:int received:int payload:text'),
    Table('diagnostics', 'snapshots', 'device:text support:text received:int report:text'),
    Table('notices', 'admins', 'name:text digest:text active:int'),
    Table('notices', 'device_admins', 'device:text name:text active:int'),
    Table('notices', 'events', 'id:text value:text position:int'),
    Table('notices', 'revisions', 'id:text value:text'),
    Table('notices', 'edit_operations', 'id:text request:text result:text device:text before_value:text after_value:text'),
)
STORES = frozenset(table.store for table in TABLES)
MARKERS = frozenset('ha_' + family + '_schema' for family in (
    'enrollment', 'paid', 'referrals', 'support', 'restricted_admin', 'restricted',
    'chat', 'routing', 'crl', 'metadata', 'diagnostics', 'notices'))
SOURCE_MARKER = 'CREATE TABLE ha_import_source(version INTEGER, purpose TEXT, store TEXT, checkpoint TEXT)'


class ImportRejected(ValueError):
    pass


def require(condition, code):
    if not condition:
        raise ImportRejected(code)


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def reference_sets(collected, checkpoint):
    records = {table.name: [dict(zip(table.columns, row, strict=True)) for row in collected[table.name]] for table in TABLES}
    result = {role: set() for role in EXTERNAL_ROLES}
    for row in records['devices']:
        result['aliases'].add('device:' + row['device'])
        result['node_allocations'].add('public:' + row['wg'])
    for row in records['paid_beta_events']:
        result['aliases'].add('event:' + row['event_id'])
    for name in ('gateway_routing_state', 'gateway_assignments', 'gateway_assignment_events', 'gateway_selection_events'):
        for row in records[name]:
            for column, prefix in (('catalog_sha256', 'catalog:'), ('previous_sha256', 'catalog:'), ('policy_sha256', 'policy:')):
                if row.get(column):
                    result['routing_files'].add(prefix + row[column])
    for row in records['restricted_grants']:
        result['issuer_material'].add('family:' + row['family'])
        result['admission'].add('device:' + row['device'])
    for row in records['restricted_certificates']:
        result['issuer_material'].add('serial:' + row['serial'])
    for row in records['restricted_crl_publications']:
        result['issuer_material'].add('crl:' + row['payload_sha256'])
    for row in records['chat_service_senders']:
        result['sender_policy'].add('sender:' + row['public'])
    for row in records['chat_bindings']:
        if row['support_sender'] is not None:
            result['sender_policy'].add('sender:' + row['support_sender'])
    for role in ('maintenance_state', 'receiver_state'):
        result[role].add('checkpoint:' + checkpoint)
    return result


def unique(pairs):
    result = {}
    for name, value in pairs:
        require(name not in result, 'DUPLICATE_EXTERNAL_FIELD')
        result[name] = value
    return result


def source_ddl(table):
    columns = [name + ' ' + ('INTEGER' if kind.rstrip('?') == 'int' else 'TEXT')
               for name, kind in zip(table.columns, table.types, strict=True)]
    if table.name == 'events':
        columns = columns[:-1]
    return 'CREATE TABLE ' + table.name + '(' + ','.join(columns) + ')'


@dataclass(frozen=True, repr=False)
class Snapshot:
    checkpoint: str
    rows: tuple = field(repr=False)
    external_digests: tuple = field(repr=False)
    crl_anchor: tuple = field(default=(), repr=False)

    @property
    def fingerprint(self):
        values = (VERSION, PURPOSE, self.checkpoint, self.rows, self.external_digests)
        return digest(encoded(values + (self.crl_anchor,) if self.crl_anchor else values))

    @property
    def counts(self):
        return {table.name: len(rows) for table, rows in zip(TABLES, self.rows, strict=True)}


def preflight(stores, external, expected_external, checkpoint):
    require(type(checkpoint) is str and len(checkpoint) == 32 and
            all(char in '0123456789abcdef' for char in checkpoint), 'CHECKPOINT_REQUIRED')
    require(type(stores) is dict and set(stores) == STORES, 'STORE_COVERAGE')
    require(type(external) is dict and type(expected_external) is dict and
            set(external) == set(expected_external) == EXTERNAL_ROLES, 'EXTERNAL_COVERAGE')
    references = []
    for role in sorted(EXTERNAL_ROLES):
        raw = external[role]
        require(type(raw) is bytes and 0 < len(raw) <= MAX_BYTES, 'EXTERNAL_BOUNDS')
        require(digest(raw) == expected_external[role], 'EXTERNAL_CHANGED')
        references.append((role, digest(raw)))
    collected = {}
    for store in sorted(STORES):
        raw = stores[store]
        require(type(raw) is bytes and 0 < len(raw) <= MAX_BYTES, 'STORE_BOUNDS')
        database = sqlite3.connect(':memory:')
        try:
            database.deserialize(raw)
            database.execute('PRAGMA trusted_schema=OFF')
            database.execute('PRAGMA query_only=ON')
            database.set_progress_handler(lambda: 1, 2000000)
            require(database.execute('PRAGMA quick_check').fetchall() == [('ok',)], 'SOURCE_INTEGRITY')
            tables = [table for table in TABLES if table.store == store]
            expected = {table.name: source_ddl(table) for table in tables} | {'ha_import_source': SOURCE_MARKER}
            actual = database.execute('SELECT type,name,sql FROM sqlite_master ORDER BY name').fetchall()
            require(actual == [('table', name, expected[name]) for name in sorted(expected)], 'SOURCE_SCHEMA')
            marker = database.execute('SELECT * FROM ha_import_source').fetchall()
            require(marker == [(VERSION, PURPOSE, store, checkpoint)], 'SOURCE_CHECKPOINT')
            for table in tables:
                columns = ['rowid' if table.name == 'events' and name == 'position' else name for name in table.columns]
                rows = database.execute('SELECT ' + ','.join(columns) + ' FROM ' + table.name).fetchmany(MAX_ROWS + 1)
                require(len(rows) <= MAX_ROWS, 'ROW_LIMIT')
                for row in rows:
                    for value, kind in zip(row, table.types, strict=True):
                        valid = value is None and kind.endswith('?')
                        if kind.rstrip('?') == 'int':
                            valid |= type(value) is int and -(2**63) <= value < 2**63
                        else:
                            valid |= type(value) is str and '\x00' not in value and len(value.encode()) <= MAX_BYTES
                        require(valid, 'SOURCE_VALUE_TYPE')
                collected[table.name] = tuple(sorted((tuple(row) for row in rows), key=encoded))
        except ImportRejected:
            raise
        except (sqlite3.Error, UnicodeError, ValueError, OverflowError):
            raise ImportRejected('SOURCE_UNREADABLE') from None
        finally:
            database.close()
    required = reference_sets(collected, checkpoint)
    for role in sorted(EXTERNAL_ROLES):
        try:
            envelope = json.loads(external[role], object_pairs_hook=unique)
            require(type(envelope) is dict and set(envelope) == {'schema', 'purpose', 'checkpoint', 'role', 'references'},
                    'EXTERNAL_SCHEMA')
            require(type(envelope['schema']) is int and envelope['schema'] == VERSION and envelope['purpose'] == PURPOSE
                    and envelope['checkpoint'] == checkpoint and envelope['role'] == role, 'EXTERNAL_CHECKPOINT')
            values = envelope['references']
            require(type(values) is list and len(values) <= MAX_ROWS and all(type(value) is str for value in values),
                    'EXTERNAL_REFERENCES')
            require(len(values) == len(set(values)) and required[role] <= set(values), 'EXTERNAL_REFERENCES')
        except (UnicodeError, json.JSONDecodeError, RecursionError):
            raise ImportRejected('EXTERNAL_UNREADABLE') from None
    return Snapshot(checkpoint, tuple(collected[table.name] for table in TABLES), tuple(references))


class JoinedRepository:
    def __init__(self, database):
        self.enrollment = enrollment_postgres.PostgresEnrollmentTransaction(database)

    @contextmanager
    def transaction(self):
        yield self.enrollment


def initialize(database):
    from control.friends.paid_postgres import initialize_synthetic_paid
    from control.friends.support_postgres import initialize_synthetic_support
    from control.friends.referrals_postgres import initialize_synthetic_referrals
    from control.friends.restricted_admin_postgres import initialize_synthetic_restricted_admin
    from control.friends.restricted_postgres import initialize_synthetic_restricted
    from control.friends.chat_postgres import initialize_synthetic_chat
    from control.friends.gateway_routing_postgres import initialize_synthetic_routing
    from control.friends.crl_postgres import initialize_synthetic_crl
    from control.friends.metadata_postgres import initialize_synthetic_metadata
    from control.friends.diagnostics_postgres import initialize_synthetic_diagnostics
    from control.friends.notices_postgres import initialize_synthetic_notices
    for statement in enrollment_postgres.DDL:
        database.execute(statement)
    database.execute('INSERT INTO ha_enrollment_schema VALUES (%s,%s)',
                     (enrollment_postgres.SCHEMA_VERSION, enrollment_postgres.PURPOSE))
    joined = JoinedRepository(database)
    for factory in (initialize_synthetic_paid, initialize_synthetic_support, initialize_synthetic_referrals,
                    initialize_synthetic_restricted_admin, initialize_synthetic_restricted, initialize_synthetic_chat,
                    initialize_synthetic_routing, initialize_synthetic_crl, initialize_synthetic_metadata,
                    initialize_synthetic_diagnostics, initialize_synthetic_notices):
        factory(joined)
    joined.enrollment.routing().initialize_routing()
    joined.enrollment.routing().initialize_selection()
    database.execute('DELETE FROM chat_sequence')
    database.execute('DELETE FROM restricted_crl_sequence')
    database.execute('CREATE TABLE ha_import_receipt(singleton BIGINT PRIMARY KEY CHECK(singleton=1), '
                     'version BIGINT NOT NULL, purpose TEXT NOT NULL, checkpoint TEXT NOT NULL, fingerprint TEXT NOT NULL, '
                     'structure TEXT NOT NULL)')


def structure(database):
    schema = database.execute('SELECT current_schema() AS name').fetchone()['name']
    queries = (
        "SELECT table_name,column_name,ordinal_position,data_type,is_nullable,column_default,is_identity "
        "FROM information_schema.columns WHERE table_schema=current_schema() ORDER BY table_name,ordinal_position",
        "SELECT conrelid::regclass::text AS relation,conname,pg_get_constraintdef(oid) AS definition "
        "FROM pg_constraint WHERE connamespace=current_schema()::regnamespace ORDER BY relation,conname",
        "SELECT tablename,indexname,indexdef FROM pg_indexes WHERE schemaname=current_schema() ORDER BY tablename,indexname",
        "SELECT tgrelid::regclass::text AS relation,tgname,tgenabled,pg_get_triggerdef(oid) AS definition FROM pg_trigger "
        "WHERE tgrelid IN (SELECT oid FROM pg_class WHERE relnamespace=current_schema()::regnamespace) "
        "AND NOT tgisinternal ORDER BY relation,tgname",
        "SELECT proname,pg_get_functiondef(oid) AS definition FROM pg_proc "
        "WHERE pronamespace=current_schema()::regnamespace ORDER BY proname",
        "SELECT relation.relname,sequence.seqstart,sequence.seqincrement,sequence.seqmax,sequence.seqmin,"
        "sequence.seqcache,sequence.seqcycle FROM pg_sequence AS sequence JOIN pg_class AS relation "
        "ON relation.oid=sequence.seqrelid WHERE relation.relnamespace=current_schema()::regnamespace ORDER BY relation.relname",
        "SELECT tgrelid::regclass::text AS relation,tgfoid::regproc::text AS function,tgenabled,"
        "pg_get_constraintdef(tgconstraint) AS definition FROM pg_trigger WHERE tgisinternal "
        "AND tgrelid IN (SELECT oid FROM pg_class WHERE relnamespace=current_schema()::regnamespace) "
        "ORDER BY relation,function,definition",
    )
    values = [database.execute(query).fetchall() for query in queries]
    values.extend(database.execute('SELECT * FROM ' + marker + ' ORDER BY 1').fetchall() for marker in sorted(MARKERS))
    return digest(encoded(values).replace(schema.encode(), b'<synthetic-schema>'))


def verify(database, snapshot):
    tables = {row['tablename'] for row in database.execute(
        'SELECT tablename FROM pg_tables WHERE schemaname=current_schema()')}
    extra = {'ha_import_crl_anchor'} if snapshot.crl_anchor else set()
    require(tables == {table.name for table in TABLES} | MARKERS | {'ha_import_receipt'} | extra, 'TARGET_COVERAGE')
    if snapshot.crl_anchor:
        require(database.execute('SELECT * FROM ha_import_crl_anchor').fetchall() == [dict(zip(
            ('singleton', 'version', 'purpose', 'sequence', 'payload_sha256'), snapshot.crl_anchor, strict=True))], 'TARGET_CRL_ANCHOR_CHANGED')
    for table, expected in zip(TABLES, snapshot.rows, strict=True):
        rows = database.execute('SELECT ' + ','.join(table.columns) + ' FROM ' + table.name).fetchmany(MAX_ROWS + 1)
        actual = tuple(sorted((tuple(row[name] for name in table.columns) for row in rows), key=encoded))
        require(actual == expected, 'TARGET_CHANGED')
    maximum = database.execute('SELECT max(id) AS value FROM field_support_audit').fetchone()['value']
    sequence = database.execute('SELECT last_value,is_called FROM field_support_audit_id_seq').fetchone()
    require(sequence == dict(last_value=max(1, maximum or 0), is_called=maximum is not None), 'TARGET_SEQUENCE_CHANGED')


def import_snapshot(repository, snapshot, *, fault=lambda stage: None):
    from psycopg import sql
    require(type(repository) is enrollment_postgres.PostgresEnrollment, 'SYNTHETIC_TARGET_REQUIRED')
    require(type(snapshot) is Snapshot, 'PREFLIGHT_REQUIRED')
    try:
        with repository.connect() as database:
            repository.configure(database)
            database.execute('SELECT pg_advisory_xact_lock(%s)', (enrollment_postgres.LOCK_ID,))
            exists = database.execute('SELECT 1 FROM pg_namespace WHERE nspname=%s', (repository.schema,)).fetchone()
            if exists:
                present = database.execute('SELECT 1 FROM pg_tables WHERE schemaname=current_schema() '
                                           "AND tablename='ha_import_receipt'").fetchone()
                require(present is not None, 'TARGET_NOT_SAME_IMPORT')
                record = database.execute('SELECT * FROM ha_import_receipt').fetchall()
                require(record == [dict(singleton=1, version=VERSION, purpose=PURPOSE, checkpoint=snapshot.checkpoint,
                                        fingerprint=snapshot.fingerprint, structure=structure(database))], 'TARGET_NOT_SAME_IMPORT')
                verify(database, snapshot)
                return dict(result='EXACT_RETRY', activation='FORBIDDEN', tables=snapshot.counts)
            database.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(repository.schema)))
            initialize(database)
            if snapshot.crl_anchor:
                database.execute('CREATE TABLE ha_import_crl_anchor(singleton BIGINT PRIMARY KEY CHECK(singleton=1), '
                    'version BIGINT NOT NULL, purpose TEXT NOT NULL, sequence BIGINT NOT NULL CHECK(sequence>0 AND sequence<9007199254740992), '
                    'payload_sha256 TEXT NOT NULL)')
                database.execute('INSERT INTO ha_import_crl_anchor VALUES (%s,%s,%s,%s,%s)', snapshot.crl_anchor)
                database.execute("CREATE FUNCTION import_crl_immutable() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN "
                    "RAISE EXCEPTION 'immutable CRL import anchor' USING ERRCODE='23514'; END $$")
                database.execute('CREATE TRIGGER import_crl_immutable BEFORE UPDATE OR DELETE OR TRUNCATE ON ha_import_crl_anchor '
                    'FOR EACH STATEMENT EXECUTE FUNCTION import_crl_immutable()')
            fault('schema')
            for table, rows in zip(TABLES, snapshot.rows, strict=True):
                statement = 'INSERT INTO ' + table.name + '(' + ','.join(table.columns) + ') VALUES (' + ','.join(['%s'] * len(table.columns)) + ')'
                with database.cursor() as cursor:
                    cursor.executemany(statement, rows)
                fault(table.name)
            maximum = database.execute('SELECT max(id) AS value FROM field_support_audit').fetchone()['value']
            database.execute("SELECT setval(pg_get_serial_sequence('field_support_audit','id'),%s,%s)",
                             (max(1, maximum or 0), maximum is not None))
            database.execute('INSERT INTO ha_import_receipt VALUES (1,%s,%s,%s,%s,%s)',
                             (VERSION, PURPOSE, snapshot.checkpoint, snapshot.fingerprint, structure(database)))
            verify(database, snapshot)
            fault('before_commit')
        fault('after_commit')
        return dict(result='IMPORTED', activation='FORBIDDEN', tables=snapshot.counts)
    except ImportRejected:
        raise
    except Exception:
        raise ImportRejected('IMPORT_OUTCOME_REQUIRES_READBACK') from None
