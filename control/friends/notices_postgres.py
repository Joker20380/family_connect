"""Synthetic notice authority only; public file export still requires fencing."""
from scripts.service_notices import NoticeTransaction, REPOSITORY_PURPOSE

DDL = (
    'CREATE TABLE ha_notices_schema(version BIGINT PRIMARY KEY, purpose TEXT NOT NULL)',
    'CREATE TABLE admins(name TEXT PRIMARY KEY, digest TEXT NOT NULL, active BIGINT NOT NULL CHECK(active IN (0,1)))',
    'CREATE TABLE device_admins(device TEXT PRIMARY KEY, name TEXT NOT NULL, active BIGINT NOT NULL CHECK(active IN (0,1)))',
    'CREATE TABLE events(id TEXT PRIMARY KEY, value TEXT NOT NULL, position BIGINT NOT NULL UNIQUE CHECK(position>0))',
    'CREATE TABLE revisions(id TEXT PRIMARY KEY, value TEXT NOT NULL)',
    'CREATE TABLE edit_operations(id TEXT PRIMARY KEY, request TEXT NOT NULL, result TEXT NOT NULL, '
    'device TEXT NOT NULL, before_value TEXT NOT NULL, after_value TEXT NOT NULL)',
)


class PostgresNoticeTransaction(NoticeTransaction):
    def __init__(self, database):
        super().__init__(database, '%s')
        self.require_schema()


def initialize_synthetic_notices(repository):
    with repository.transaction() as enrollment:
        database = enrollment.database
        for statement in DDL:
            database.execute(statement)
        database.execute('INSERT INTO ha_notices_schema VALUES (%s,%s)', (1, REPOSITORY_PURPOSE))
        database.execute("CREATE FUNCTION notice_immutable() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN "
            "RAISE EXCEPTION 'immutable notice history' USING ERRCODE='23514'; END $$")
        for table in ('events', 'edit_operations'):
            database.execute('CREATE TRIGGER notice_immutable BEFORE UPDATE OR DELETE ON ' + table +
                             ' FOR EACH ROW EXECUTE FUNCTION notice_immutable()')
            database.execute('CREATE TRIGGER notice_no_truncate BEFORE TRUNCATE ON ' + table +
                             ' FOR EACH STATEMENT EXECUTE FUNCTION notice_immutable()')
        database.execute("CREATE FUNCTION notice_revision() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN "
            "IF TG_OP<>'UPDATE' THEN RAISE EXCEPTION 'retain notice revision' USING ERRCODE='23514'; END IF; "
            "IF NEW.id<>OLD.id OR (NEW.value::jsonb->>'revision')::bigint IS DISTINCT FROM (OLD.value::jsonb->>'revision')::bigint+1 "
            "OR (NEW.value::jsonb->>'updated') IS NULL OR (NEW.value::jsonb->>'updated')::bigint<(OLD.value::jsonb->>'updated')::bigint "
            "OR (NEW.value::jsonb-ARRAY['title','body','revision','updated','editor']) IS DISTINCT FROM "
            "(OLD.value::jsonb-ARRAY['title','body','revision','updated','editor']) THEN "
            "RAISE EXCEPTION 'invalid notice revision' USING ERRCODE='23514'; END IF; RETURN NEW; END $$")
        database.execute('CREATE TRIGGER notice_revision BEFORE UPDATE OR DELETE ON revisions '
                         'FOR EACH ROW EXECUTE FUNCTION notice_revision()')
        database.execute('CREATE TRIGGER notice_no_truncate BEFORE TRUNCATE ON revisions '
                         'FOR EACH STATEMENT EXECUTE FUNCTION notice_immutable()')
