"""Bounded logical PostgreSQL boundary; not a filesystem or fleet capture permit."""
import hashlib
import json
import time

from psycopg import sql
from psycopg.pq import TransactionStatus


INFORMATION_VIEWS = frozenset('''_pg_foreign_data_wrappers _pg_foreign_servers _pg_foreign_table_columns
_pg_foreign_tables _pg_user_mappings administrable_role_authorizations applicable_roles attributes
character_sets check_constraint_routine_usage check_constraints collation_character_set_applicability
collations column_column_usage column_domain_usage column_options column_privileges column_udt_usage
columns constraint_column_usage constraint_table_usage data_type_privileges domain_constraints
domain_udt_usage domains element_types enabled_roles foreign_data_wrapper_options foreign_data_wrappers
foreign_server_options foreign_servers foreign_table_options foreign_tables information_schema_catalog_name
key_column_usage parameters referential_constraints role_column_grants role_routine_grants role_table_grants
role_udt_grants role_usage_grants routine_column_usage routine_privileges routine_routine_usage
routine_sequence_usage routine_table_usage routines schemata sequences table_constraints table_privileges
tables transforms triggered_update_columns triggers udt_privileges usage_privileges user_defined_types
user_mapping_options user_mappings view_column_usage view_routine_usage view_table_usage views'''.split())
INFORMATION_TABLES = {
    'sql_features': ('feature_id', 'feature_name', 'sub_feature_id', 'sub_feature_name',
                     'is_supported', 'is_verified_by', 'comments'),
    'sql_implementation_info': ('implementation_info_id', 'implementation_info_name',
                                'integer_value', 'character_value', 'comments'),
    'sql_parts': ('feature_id', 'feature_name', 'is_supported', 'is_verified_by', 'comments'),
    'sql_sizing': ('sizing_id', 'sizing_name', 'supported_value', 'comments'),
}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def scope(connection):
    require(170000 <= connection.info.server_version < 180000, 'PG_BOUNDARY_VERSION')
    require(not connection.execute('SELECT oid FROM pg_catalog.pg_event_trigger').fetchall(),
            'PG_BOUNDARY_EVENT_TRIGGERS')
    binding = connection.execute('SELECT current_database(), oid, pg_postmaster_start_time()::text '
        'FROM pg_catalog.pg_database WHERE datname=current_database()').fetchone()
    relations = connection.execute("SELECT namespace.nspname, relation.relname, relation.oid, "
        'relation.relkind, relation.relpersistence, relation.relrowsecurity, relation.relowner '
        'FROM pg_catalog.pg_class relation JOIN pg_catalog.pg_namespace namespace '
        "ON namespace.oid=relation.relnamespace WHERE namespace.nspname NOT LIKE 'pg_toast%' "
        "AND namespace.nspname NOT LIKE 'pg_temp_%' "
        "AND relation.relkind NOT IN ('i','I') ORDER BY relation.oid").fetchall()
    information = [row for row in relations if row[0] == 'information_schema']
    require({row[1] for row in information} == INFORMATION_VIEWS | INFORMATION_TABLES.keys() and
            all(row[3] == ('r' if row[1] in INFORMATION_TABLES else 'v') and
                row[4] == 'p' and not row[5] and row[6] == 10 for row in information),
            'PG_BOUNDARY_INFORMATION_SCHEMA')
    information_attributes = connection.execute('SELECT relation.relname, attribute.attnum, attribute.attname, '
        'attribute.atttypid::regtype::text, attribute.attnotnull FROM pg_catalog.pg_attribute attribute '
        'JOIN pg_catalog.pg_class relation ON attribute.attrelid=relation.oid '
        "WHERE relation.relnamespace='information_schema'::regnamespace AND relation.relkind='r' "
        'AND attribute.attnum>0 ORDER BY relation.relname,attribute.attnum').fetchall()
    expected_attributes = [(table, index, name, 'information_schema.' +
        ('cardinal_number' if name in ('integer_value', 'sizing_id', 'supported_value') else
         'yes_or_no' if name == 'is_supported' else 'character_data'), False)
        for table, names in sorted(INFORMATION_TABLES.items()) for index, name in enumerate(names, 1)]
    require(information_attributes == expected_attributes, 'PG_BOUNDARY_INFORMATION_SCHEMA')
    catalogs = [row for row in relations if row[0] in ('pg_catalog', 'information_schema') and row[3] == 'r']
    user = [row for row in relations if row[0] not in ('pg_catalog', 'information_schema')]
    require(catalogs and user and all(row[0] == 'public' and row[3] in ('r', 'S') and
            row[4] == 'p' and not row[5] for row in user), 'PG_BOUNDARY_UNSUPPORTED_RELATION')
    sequences = connection.execute('SELECT sequence.* FROM pg_catalog.pg_sequence sequence '
        'JOIN pg_catalog.pg_class relation ON sequence.seqrelid=relation.oid '
        "WHERE relation.relnamespace='public'::regnamespace ORDER BY seqrelid").fetchall()
    attributes = connection.execute('SELECT attribute.attrelid, attribute.attnum, attribute.attname, '
        'attribute.atttypid, attribute.atttypmod, attribute.attnotnull, attribute.attidentity, '
        'attribute.attgenerated, attribute.attisdropped, pg_catalog.pg_get_expr(value.adbin,value.adrelid) '
        'FROM pg_catalog.pg_attribute attribute LEFT JOIN pg_catalog.pg_attrdef value '
        'ON attribute.attrelid=value.adrelid AND attribute.attnum=value.adnum '
        'WHERE attribute.attrelid=ANY(%s::oid[]) AND attribute.attnum>0 '
        'ORDER BY attribute.attrelid, attribute.attnum', ([row[2] for row in user],)).fetchall()
    return dict(binding=binding, catalogs=catalogs, relations=user, sequences=sequences, attributes=attributes,
                information_schema=information, information_attributes=information_attributes)


class PostgresBoundary:
    def __init__(self, connection, expected, *, milliseconds=30000):
        require(type(milliseconds) is int and 200 <= milliseconds <= 120000, 'PG_BOUNDARY_DEADLINE')
        require(connection.autocommit and connection.info.transaction_status == TransactionStatus.IDLE,
                'PG_BOUNDARY_FRESH_CONNECTION')
        require(type(expected) is dict and set(expected) == {
            'binding', 'catalogs', 'relations', 'sequences', 'attributes',
            'information_schema', 'information_attributes'}, 'PG_BOUNDARY_COVERAGE')
        self.connection = connection
        self.expected = json.loads(json.dumps(expected))
        self.coverage = fingerprint(self.expected)
        self.milliseconds = milliseconds
        self.attempted = self.active = False

    def lock(self, relations):
        require(bool(relations), 'PG_BOUNDARY_EMPTY_LOCK_SET')
        names = sql.SQL(', ').join(sql.Identifier(row[0], row[1]) for row in relations)
        self.connection.execute(sql.SQL('LOCK TABLE {} IN SHARE MODE NOWAIT').format(names))

    def __enter__(self):
        require(not self.attempted, 'PG_BOUNDARY_NO_RETRY')
        self.attempted = True
        try:
            connection = self.connection
            for name, value in (('transaction_timeout', f'{self.milliseconds}ms'),
                                ('idle_in_transaction_session_timeout', f'{self.milliseconds}ms'),
                                ('statement_timeout', '2000ms'), ('lock_timeout', '1ms')):
                connection.execute('SELECT pg_catalog.set_config(%s,%s,false)', (name, value))
            require(connection.execute('SELECT rolsuper FROM pg_catalog.pg_roles '
                'WHERE rolname=current_user').fetchone() == (True,), 'PG_BOUNDARY_PRIVILEGE')
            self.deadline = time.monotonic() + self.milliseconds / 1000
            connection.execute('BEGIN ISOLATION LEVEL READ COMMITTED')
            self.lock([('pg_catalog', name) for name in ('pg_class', 'pg_namespace', 'pg_event_trigger')])
            observed = scope(connection)
            require(fingerprint(observed) == self.coverage, 'PG_BOUNDARY_COVERAGE_CHANGED')
            self.lock(observed['catalogs'])
            self.lock([row for row in observed['relations'] if row[3] == 'r'])
            caches = {row[0]: row[6] for row in observed['sequences']}
            for relation in observed['relations']:
                if relation[3] == 'S':
                    connection.execute(sql.SQL('ALTER SEQUENCE {} CACHE {}').format(
                        sql.Identifier(relation[0], relation[1]), sql.Literal(caches[relation[2]])))
            self.identity = connection.execute('SELECT pg_backend_pid(), backend_start::text, '
                'pg_current_xact_id()::text FROM pg_catalog.pg_stat_activity WHERE pid=pg_backend_pid()').fetchone()
            self.locks = {(row[2], 'ShareLock') for row in observed['catalogs']}
            self.locks.update((row[2], 'ShareRowExclusiveLock' if row[3] == 'S' else 'ShareLock')
                              for row in observed['relations'])
            self.lease = fingerprint(dict(identity=self.identity, coverage=self.coverage))
            self.active = True
            self.check()
            return self
        except BaseException as error:
            try:
                self.release()
            except Exception as cleanup:
                error.add_note('PG_BOUNDARY_CLEANUP_' + type(cleanup).__name__)
            raise

    def check(self):
        connection = self.connection
        require(self.active and time.monotonic() < self.deadline and not connection.closed and
                connection.info.transaction_status == TransactionStatus.INTRANS, 'PG_BOUNDARY_LOST')
        identity = connection.execute('SELECT pg_backend_pid(), backend_start::text, pg_current_xact_id()::text '
            'FROM pg_catalog.pg_stat_activity WHERE pid=pg_backend_pid()').fetchone()
        held = set(connection.execute('SELECT relation, mode FROM pg_catalog.pg_locks '
            'WHERE pid=pg_backend_pid() AND granted AND locktype=\'relation\'').fetchall())
        bounded = connection.execute("SELECT current_setting('transaction_timeout')::interval=%s::interval, "
            "current_setting('idle_in_transaction_session_timeout')::interval=%s::interval",
            (f'{self.milliseconds}ms', f'{self.milliseconds}ms')).fetchone()
        require(identity == self.identity and self.locks <= held and bounded == (True, True) and
                fingerprint(scope(connection)) == self.coverage and time.monotonic() < self.deadline,
                'PG_BOUNDARY_LOST')
        return self.lease

    def release(self):
        try:
            if not self.connection.closed:
                self.connection.rollback()
        finally:
            self.active = False
            self.connection.close()

    def __exit__(self, error_type, error, traceback):
        try:
            self.release()
        except Exception as cleanup:
            if error is None:
                raise
            error.add_note('PG_BOUNDARY_CLEANUP_' + type(cleanup).__name__)
