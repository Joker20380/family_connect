"""Synthetic canonical consent transactions, not a live metadata import."""
from .technical_metadata import MetadataTransaction, REPOSITORY_PURPOSE

DDL = (
    'CREATE TABLE ha_metadata_schema(version BIGINT PRIMARY KEY, purpose TEXT NOT NULL)',
    'CREATE TABLE device_metadata(device TEXT PRIMARY KEY, '
    'epoch BIGINT NOT NULL CHECK(epoch>0 AND epoch<9007199254740992), '
    'sequence BIGINT NOT NULL CHECK(sequence>0 AND sequence<9007199254740992), '
    'digest TEXT NOT NULL, enabled BIGINT NOT NULL CHECK(enabled IN (0,1)), '
    'received BIGINT NOT NULL, payload TEXT NOT NULL CHECK(enabled=1 OR payload=\'{}\'))',
)


class PostgresMetadataTransaction(MetadataTransaction):
    def __init__(self, database):
        super().__init__(database, '%s')
        self.require_schema()

    def prepare_write(self):
        pass


def initialize_synthetic_metadata(repository):
    with repository.transaction() as enrollment:
        database = enrollment.database
        for statement in DDL:
            database.execute(statement)
        database.execute('INSERT INTO ha_metadata_schema VALUES (%s,%s)', (1, REPOSITORY_PURPOSE))
        database.execute("CREATE FUNCTION metadata_monotonic() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN "
            "IF TG_OP <> 'UPDATE' THEN RAISE EXCEPTION 'retain consent floor' USING ERRCODE='23514'; END IF; "
            "IF NEW.device<>OLD.device OR NEW.epoch<OLD.epoch OR (NEW.epoch=OLD.epoch AND "
            "(NEW.sequence<OLD.sequence OR (OLD.enabled=0 AND NEW.enabled=1))) THEN "
            "RAISE EXCEPTION 'consent regression' USING ERRCODE='23514'; END IF; "
            "IF NEW.epoch=OLD.epoch AND NEW.sequence=OLD.sequence AND "
            "((NEW.digest,NEW.enabled,NEW.received) IS DISTINCT FROM (OLD.digest,OLD.enabled,OLD.received) OR "
            "EXISTS (SELECT 1 FROM jsonb_each(NEW.payload::jsonb) AS fresh WHERE "
            "NOT EXISTS (SELECT 1 FROM jsonb_each(OLD.payload::jsonb) AS prior "
            "WHERE fresh.key=prior.key AND fresh.value=prior.value))) THEN "
            "RAISE EXCEPTION 'immutable metadata version' USING ERRCODE='23514'; END IF; RETURN NEW; END $$")
        database.execute('CREATE TRIGGER metadata_monotonic BEFORE UPDATE OR DELETE ON device_metadata '
            'FOR EACH ROW EXECUTE FUNCTION metadata_monotonic()')
        database.execute('CREATE TRIGGER metadata_no_truncate BEFORE TRUNCATE ON device_metadata '
            'FOR EACH STATEMENT EXECUTE FUNCTION metadata_monotonic()')
