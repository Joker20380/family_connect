"""Synthetic grant/audit storage only; no certificate or fenced file publication."""
from .restricted_admin import RestrictedAdminTransaction

PURPOSE = 'family-connect/ha-restricted-admin-synthetic/v1/db-only'
DDL = (
    'CREATE TABLE ha_restricted_admin_schema(version BIGINT PRIMARY KEY, purpose TEXT NOT NULL)',
    'CREATE TABLE restricted_grants(device TEXT PRIMARY KEY REFERENCES devices(device), '
    "family TEXT NOT NULL CHECK(length(family)>0), revision BIGINT NOT NULL CHECK(revision>=1), "
    'expires BIGINT CHECK(expires>=0), revoked BIGINT NOT NULL DEFAULT 0 CHECK(revoked IN (0,1)))',
)


class PostgresRestrictedAdminTransaction(RestrictedAdminTransaction):
    def __init__(self, enrollment):
        super().__init__(enrollment)
        rows = self.database.execute('SELECT version,purpose FROM ha_restricted_admin_schema').fetchall()
        if rows != [dict(version=1, purpose=PURPOSE)]:
            raise RuntimeError('Restricted admin rehearsal schema mismatch')

    def insert_audit(self, statement, values):
        return self.database.execute(statement + ' RETURNING id', values).fetchone()['id']


def initialize_synthetic_restricted_admin(repository):
    with repository.transaction() as transaction:
        for statement in DDL:
            transaction.database.execute(statement)
        transaction.database.execute('INSERT INTO ha_restricted_admin_schema VALUES (%s,%s)', (1, PURPOSE))
