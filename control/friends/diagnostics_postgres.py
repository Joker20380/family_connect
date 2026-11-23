"""Synthetic canonical support snapshots, not a production database import."""
from .diagnostics import DiagnosticsTransaction, REPOSITORY_PURPOSE

DDL = (
    'CREATE TABLE ha_diagnostics_schema(version BIGINT PRIMARY KEY, purpose TEXT NOT NULL)',
    'CREATE TABLE snapshots(device TEXT PRIMARY KEY, support TEXT NOT NULL, '
    'received BIGINT NOT NULL, report TEXT NOT NULL)',
)


class PostgresDiagnosticsTransaction(DiagnosticsTransaction):
    def __init__(self, database):
        super().__init__(database, '%s')
        self.require_schema()

    def prepare_write(self):
        pass


def initialize_synthetic_diagnostics(repository):
    with repository.transaction() as enrollment:
        for statement in DDL:
            enrollment.database.execute(statement)
        enrollment.database.execute('INSERT INTO ha_diagnostics_schema VALUES (%s,%s)', (1, REPOSITORY_PURPOSE))
