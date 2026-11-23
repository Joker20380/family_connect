"""Explicit synthetic referral schema; no production backend selection or import."""
from .referrals import ReferralTransaction

PURPOSE = 'family-connect/ha-referrals-synthetic/v1'
DDL = (
    'CREATE TABLE ha_referrals_schema(version BIGINT PRIMARY KEY, purpose TEXT NOT NULL)',
    'CREATE TABLE referral_links(token TEXT PRIMARY KEY, sponsor TEXT UNIQUE NOT NULL REFERENCES devices(device))',
    'CREATE TABLE referral_claims(request TEXT PRIMARY KEY, sponsor TEXT NOT NULL REFERENCES devices(device), '
    'invite TEXT UNIQUE NOT NULL REFERENCES invites(hash), created BIGINT NOT NULL)',
    'CREATE INDEX referral_daily ON referral_claims(sponsor,created)',
)


class PostgresReferralTransaction(ReferralTransaction):
    def __init__(self, enrollment):
        super().__init__(enrollment)
        rows = self.database.execute('SELECT version,purpose FROM ha_referrals_schema').fetchall()
        if rows != [dict(version=1, purpose=PURPOSE)]:
            raise RuntimeError('Referral rehearsal schema mismatch')


def initialize_synthetic_referrals(repository):
    with repository.transaction() as transaction:
        for statement in DDL:
            transaction.database.execute(statement)
        transaction.database.execute('INSERT INTO ha_referrals_schema VALUES (%s,%s)', (1, PURPOSE))
