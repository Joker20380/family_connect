"""Native paid contracts for the isolated HA store; no serving or transport selector."""
from .enrollment_postgres import LOCK_ID
from .paid_beta import COHORT_LIMIT, PaidTransaction, require

PURPOSE = 'family-connect/ha-paid-synthetic/v1/no-transports'
DDL = (
    'CREATE TABLE ha_paid_schema(version BIGINT PRIMARY KEY, purpose TEXT NOT NULL)',
    'CREATE TABLE paid_beta_subscriptions ('
    'device TEXT PRIMARY KEY REFERENCES devices(device), '
    "state TEXT NOT NULL CHECK(state IN ('trial','active','grace','expired','revoked')), "
    'period_start BIGINT NOT NULL CHECK(period_start>=0), paid_until BIGINT NOT NULL CHECK(paid_until>period_start), '
    'grace_until BIGINT CHECK(grace_until IS NULL OR grace_until>=paid_until), '
    'created_at BIGINT NOT NULL, updated_at BIGINT NOT NULL, version BIGINT NOT NULL CHECK(version>0), '
    'last_event_id TEXT NOT NULL, revoked_at BIGINT, '
    "CHECK(state!='grace' OR grace_until IS NOT NULL), CHECK((state='revoked')=(revoked_at IS NOT NULL)))",
    'CREATE TABLE paid_beta_events ('
    'event_id TEXT PRIMARY KEY, device TEXT NOT NULL REFERENCES devices(device), '
    "event_type TEXT NOT NULL CHECK(event_type IN ('payment','grace','expire','revoke')), "
    'occurred_at BIGINT NOT NULL, previous_state TEXT, new_state TEXT NOT NULL, '
    'period_start BIGINT NOT NULL, paid_until BIGINT NOT NULL, grace_until BIGINT, '
    'reference_hash TEXT NOT NULL, payload_hash TEXT NOT NULL, applied_at BIGINT NOT NULL, '
    "result TEXT NOT NULL CHECK(result='APPLIED'))",
    """CREATE FUNCTION paid_event_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN RAISE EXCEPTION 'PAID_EVENT_IMMUTABLE'; END $$""",
    'CREATE TRIGGER paid_event_immutable BEFORE UPDATE OR DELETE ON paid_beta_events '
    'FOR EACH ROW EXECUTE FUNCTION paid_event_immutable()',
    'CREATE TRIGGER paid_event_no_truncate BEFORE TRUNCATE ON paid_beta_events '
    'FOR EACH STATEMENT EXECUTE FUNCTION paid_event_immutable()',
    """CREATE FUNCTION paid_subscription_retained() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN RAISE EXCEPTION 'PAID_COHORT_RETAINED'; END $$""",
    'CREATE TRIGGER paid_subscription_retained BEFORE DELETE ON paid_beta_subscriptions '
    'FOR EACH ROW EXECUTE FUNCTION paid_subscription_retained()',
    'CREATE TRIGGER paid_subscription_no_truncate BEFORE TRUNCATE ON paid_beta_subscriptions '
    'FOR EACH STATEMENT EXECUTE FUNCTION paid_subscription_retained()',
    f"""CREATE FUNCTION paid_subscription_guard() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        PERFORM pg_advisory_xact_lock({LOCK_ID});
        IF TG_OP='INSERT' THEN
            IF NOT EXISTS (SELECT 1 FROM paid_beta_subscriptions WHERE device=NEW.device)
                AND (SELECT count(*) FROM paid_beta_subscriptions)>={COHORT_LIMIT} THEN
                RAISE EXCEPTION 'PAID_COHORT_LIMIT';
            END IF;
        ELSE
            IF NEW.device<>OLD.device THEN RAISE EXCEPTION 'PAID_DEVICE_IMMUTABLE'; END IF;
            IF OLD.state='revoked' THEN RAISE EXCEPTION 'PAID_REVOKED'; END IF;
        END IF;
        RETURN NEW;
    END $$""",
    'CREATE TRIGGER paid_subscription_guard BEFORE INSERT OR UPDATE ON paid_beta_subscriptions '
    'FOR EACH ROW EXECUTE FUNCTION paid_subscription_guard()',
)


class PostgresPaidTransaction(PaidTransaction):
    def __init__(self, database):
        super().__init__(database, '%s')

    @property
    def in_transaction(self):
        from psycopg.pq import TransactionStatus
        return self.database.info.transaction_status == TransactionStatus.INTRANS

    def table_exists(self, table):
        return self.database.execute('SELECT 1 FROM pg_catalog.pg_tables WHERE schemaname=current_schema() '
            'AND tablename=%s', (table,)).fetchone() is not None

    def schema_present(self):
        present = super().schema_present()
        if present:
            require(self.table_exists('ha_paid_schema'), 'PAID_REHEARSAL_MARKER_REQUIRED')
            require(self.database.execute('SELECT version,purpose FROM ha_paid_schema').fetchall() ==
                    [dict(version=1, purpose=PURPOSE)], 'PAID_REHEARSAL_SCHEMA_MISMATCH')
        return present

    def prepare_membership(self, device, token, now):
        require(self.schema_present(), 'PAID_REHEARSAL_MARKER_REQUIRED')


def initialize_synthetic_paid(repository):
    with repository.transaction() as transaction:
        for statement in DDL:
            transaction.database.execute(statement)
        transaction.database.execute('INSERT INTO ha_paid_schema VALUES (%s,%s)', (1, PURPOSE))
