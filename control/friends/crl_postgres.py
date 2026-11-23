"""Synthetic durable CRL preparation, not a fenced file or gateway publisher."""
from .restricted_admin import CRLTransaction, CRL_PURPOSE

DDL = (
    'CREATE TABLE ha_crl_schema(version BIGINT PRIMARY KEY, purpose TEXT NOT NULL)',
    'CREATE TABLE restricted_crl_sequence(singleton BIGINT PRIMARY KEY CHECK(singleton=1), '
    'sequence BIGINT NOT NULL CHECK(sequence>=0 AND sequence<9007199254740992))',
    'CREATE TABLE restricted_crl_publications(operation_id TEXT PRIMARY KEY, request_sha256 TEXT NOT NULL, '
    'sequence BIGINT UNIQUE NOT NULL CHECK(sequence>0 AND sequence<9007199254740992), '
    'payload TEXT NOT NULL, payload_sha256 TEXT NOT NULL, issued_at BIGINT NOT NULL, expires_at BIGINT NOT NULL, '
    'local_receipt BIGINT NOT NULL DEFAULT 0 CHECK(local_receipt IN (0,1)), CHECK(expires_at>issued_at))',
)


class PostgresCRLTransaction(CRLTransaction):
    def __init__(self, enrollment):
        super().__init__(enrollment)
        enrollment.restricted()
        self.require_outbox()

    def exists(self, table):
        return self.database.execute('SELECT to_regclass(%s) AS name', (table,)).fetchone()['name'] is not None

    def reserve(self, number):
        if type(number) is not int or not self.sequence() < number < 2**53:
            raise ValueError('invalid CRL sequence advance')
        self.database.execute('UPDATE restricted_crl_sequence SET sequence=%s WHERE singleton=1', (number,))


def initialize_synthetic_crl(repository):
    with repository.transaction() as enrollment:
        enrollment.restricted()
        for statement in DDL:
            enrollment.database.execute(statement)
        enrollment.database.execute('INSERT INTO ha_crl_schema VALUES (%s,%s)', (1, CRL_PURPOSE))
        enrollment.database.execute('INSERT INTO restricted_crl_sequence VALUES (1,0)')
        enrollment.database.execute("CREATE FUNCTION crl_immutable() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN "
            "IF TG_OP <> 'UPDATE' THEN RAISE EXCEPTION 'immutable CRL candidate' USING ERRCODE='23514'; END IF; "
            "IF (NEW.operation_id,NEW.request_sha256,NEW.sequence,NEW.payload,NEW.payload_sha256,NEW.issued_at,NEW.expires_at) "
            "IS DISTINCT FROM (OLD.operation_id,OLD.request_sha256,OLD.sequence,OLD.payload,OLD.payload_sha256,OLD.issued_at,OLD.expires_at) "
            "OR NEW.local_receipt<OLD.local_receipt THEN RAISE EXCEPTION 'immutable CRL candidate' USING ERRCODE='23514'; "
            "END IF; RETURN NEW; END $$")
        enrollment.database.execute('CREATE TRIGGER crl_immutable BEFORE UPDATE OR DELETE ON restricted_crl_publications '
            'FOR EACH ROW EXECUTE FUNCTION crl_immutable()')
        enrollment.database.execute('CREATE TRIGGER crl_no_truncate BEFORE TRUNCATE ON restricted_crl_publications '
            'FOR EACH STATEMENT EXECUTE FUNCTION crl_immutable()')
