"""Synthetic routing DB only; signed files and production wiring remain separate."""
from .gateway_routing import RoutingTransaction

PURPOSE = 'family-connect/ha-routing-synthetic/v1/db-only'
ROUTING_DDL = (
    'CREATE TABLE gateway_routing_state(singleton BIGINT PRIMARY KEY CHECK(singleton=1), '
    'policy_sha256 TEXT NOT NULL, generation BIGINT NOT NULL)',
    'CREATE TABLE gateway_assignments(device TEXT PRIMARY KEY REFERENCES devices(device), '
    'catalog_sha256 TEXT NOT NULL, node TEXT NOT NULL, sequence BIGINT NOT NULL)',
    'CREATE TABLE gateway_assignment_events(operation_id TEXT PRIMARY KEY, request_sha256 TEXT NOT NULL, '
    'device TEXT NOT NULL, previous_sha256 TEXT NOT NULL, catalog_sha256 TEXT NOT NULL)',
)


class PostgresRoutingTransaction(RoutingTransaction):
    def __init__(self, enrollment):
        super().__init__(enrollment)
        rows = self.database.execute('SELECT version,purpose FROM ha_routing_schema').fetchall()
        if rows != [dict(version=1, purpose=PURPOSE)]:
            raise RuntimeError('Routing rehearsal schema mismatch')

    def exists(self, table):
        return self.database.execute('SELECT to_regclass(%s) AS name', (table,)).fetchone()['name'] is not None

    def immutable(self, table):
        self.database.execute('CREATE TRIGGER ' + table + '_immutable BEFORE UPDATE OR DELETE OR TRUNCATE ON ' +
            table + ' FOR EACH STATEMENT EXECUTE FUNCTION routing_append_only()')

    def initialize_routing(self):
        for statement in ROUTING_DDL:
            self.database.execute(statement)
        self.immutable('gateway_assignment_events')

    def initialize_selection(self):
        self.database.execute('CREATE TABLE gateway_selection_events(operation_id TEXT PRIMARY KEY, '
            'request_sha256 TEXT NOT NULL, catalog_sha256 TEXT NOT NULL, policy_sha256 TEXT NOT NULL, '
            'sequence BIGINT NOT NULL UNIQUE)')
        self.immutable('gateway_selection_events')


def initialize_synthetic_routing(repository):
    with repository.transaction() as enrollment:
        enrollment.database.execute('CREATE TABLE ha_routing_schema(version BIGINT PRIMARY KEY, purpose TEXT NOT NULL)')
        enrollment.database.execute('INSERT INTO ha_routing_schema VALUES (%s,%s)', (1, PURPOSE))
        enrollment.database.execute("CREATE FUNCTION routing_append_only() RETURNS trigger LANGUAGE plpgsql AS $$ "
            "BEGIN RAISE EXCEPTION 'append-only routing evidence' USING ERRCODE='23514'; END $$")
