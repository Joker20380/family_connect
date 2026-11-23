"""Synthetic Support ID repository; restricted grants and file writers are not migrated."""
from .support_ids import SupportTransaction

PURPOSE = 'family-connect/ha-support-synthetic/v1'


class PostgresSupportTransaction(SupportTransaction):
    def __init__(self, enrollment):
        super().__init__(enrollment)
        self.ensure_schema()

    def ensure_schema(self):
        rows = self.database.execute('SELECT version,purpose FROM ha_support_schema').fetchall()
        if rows != [dict(version=1, purpose=PURPOSE)]:
            raise RuntimeError('Support rehearsal schema mismatch')

    def table_exists(self, table):
        return self.database.execute('SELECT 1 FROM pg_catalog.pg_tables WHERE schemaname=current_schema() '
                                     'AND tablename=%s', (table,)).fetchone() is not None


def initialize_synthetic_support(repository):
    with repository.transaction() as transaction:
        transaction.database.execute('CREATE TABLE ha_support_schema(version BIGINT PRIMARY KEY, purpose TEXT NOT NULL)')
        transaction.database.execute('INSERT INTO ha_support_schema VALUES (%s,%s)', (1, PURPOSE))
