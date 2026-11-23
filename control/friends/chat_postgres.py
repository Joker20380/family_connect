"""Synthetic chat/support DB only; no mailbox publisher or production selector."""
from .chat import ChatTransaction

PURPOSE = 'family-connect/ha-chat-synthetic/v1/db-only'
DDL = (
    'CREATE TABLE ha_chat_schema(version BIGINT PRIMARY KEY, purpose TEXT NOT NULL)',
    'CREATE TABLE chat_bindings(device TEXT PRIMARY KEY REFERENCES devices(device), '
    'public TEXT UNIQUE NOT NULL, support_sender TEXT)',
    'CREATE TABLE chat_challenges(nonce TEXT PRIMARY KEY, device TEXT NOT NULL REFERENCES devices(device), '
    'public TEXT NOT NULL, expires BIGINT NOT NULL, used BIGINT NOT NULL DEFAULT 0 CHECK(used IN (0,1)))',
    'CREATE TABLE chat_sequence(id BIGINT PRIMARY KEY CHECK(id=1), value BIGINT NOT NULL CHECK(value>=0))',
    'CREATE TABLE chat_service_senders(public TEXT PRIMARY KEY, enabled BIGINT NOT NULL CHECK(enabled IN (0,1)))',
)


class PostgresChatTransaction(ChatTransaction):
    def __init__(self, enrollment):
        super().__init__(enrollment)
        rows = self.database.execute('SELECT version,purpose FROM ha_chat_schema').fetchall()
        if rows != [dict(version=1, purpose=PURPOSE)]:
            raise RuntimeError('Chat rehearsal schema mismatch')


def initialize_synthetic_chat(repository):
    with repository.transaction() as enrollment:
        for statement in DDL:
            enrollment.database.execute(statement)
        enrollment.database.execute('INSERT INTO ha_chat_schema VALUES (%s,%s)', (1, PURPOSE))
        enrollment.database.execute('INSERT INTO chat_sequence VALUES (1,0)')
