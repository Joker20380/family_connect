"""Synthetic issuance/receipt storage; no replicated issuer or file publisher."""
from .restricted import RestrictedTransaction

PURPOSE = 'family-connect/ha-restricted-synthetic/v1'
DDL = (
    'CREATE TABLE ha_restricted_schema(version BIGINT PRIMARY KEY, purpose TEXT NOT NULL)',
    'CREATE TABLE restricted_challenges(nonce TEXT PRIMARY KEY, revision BIGINT NOT NULL CHECK(revision>=1), '
    'family TEXT NOT NULL, expires BIGINT NOT NULL)',
    'CREATE TABLE restricted_certificates(device TEXT NOT NULL REFERENCES devices(device), '
    'revision BIGINT NOT NULL CHECK(revision>=1), serial TEXT PRIMARY KEY, expires BIGINT NOT NULL, certificate TEXT NOT NULL)',
    'CREATE TABLE restricted_readiness_results(correlation TEXT PRIMARY KEY, nonce TEXT UNIQUE NOT NULL, '
    'device TEXT NOT NULL REFERENCES devices(device), challenge_at BIGINT NOT NULL, fetch_id TEXT, fetch_at BIGINT, '
    'revision BIGINT, minimum_crl BIGINT, expires BIGINT, ack TEXT, ack_at BIGINT, gateway_binding TEXT NOT NULL DEFAULT \'\')',
)


class PostgresRestrictedTransaction(RestrictedTransaction):
    def __init__(self, enrollment):
        super().__init__(enrollment)
        enrollment.restricted_admin()
        if not enrollment.paid().schema_present():
            raise RuntimeError('Restricted paid schema required')
        rows = self.database.execute('SELECT version,purpose FROM ha_restricted_schema').fetchall()
        if rows != [dict(version=1, purpose=PURPOSE)]:
            raise RuntimeError('Restricted rehearsal schema mismatch')


def initialize_synthetic_restricted(repository):
    with repository.transaction() as enrollment:
        enrollment.restricted_admin()
        if not enrollment.paid().schema_present():
            raise RuntimeError('Restricted paid schema required')
        for statement in DDL:
            enrollment.database.execute(statement)
        enrollment.database.execute('INSERT INTO ha_restricted_schema VALUES (%s,%s)', (1, PURPOSE))
