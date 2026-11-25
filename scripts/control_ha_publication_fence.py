"""Bounded PostgreSQL publication boundary, not proof of external work settlement."""
import json
import os
import time

import psycopg
from psycopg.pq import TransactionStatus


PURPOSE = 'family-connect/owner-publication-pg-boundary/v1'
TABLES = ('console_auditrecord', 'console_systemmessage')
STATUSES = ('draft', 'queued', 'unknown', 'refused', 'published')


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


class PublicationFence:
    def __init__(self, connection, *, database, milliseconds=2000):
        require(type(milliseconds) is int and 200 <= milliseconds <= 5000, 'FENCE_DEADLINE')
        require(type(database) is str and bool(database) and connection.info.dbname == database, 'FENCE_DATABASE')
        require(connection.autocommit and connection.info.transaction_status == TransactionStatus.IDLE,
                'FRESH_CONNECTION_REQUIRED')
        self.connection, self.database, self.milliseconds = connection, database, milliseconds
        self.attempted = self.active = self.released = False

    def __enter__(self):
        require(not self.attempted, 'NO_FENCE_RETRY')
        self.attempted = True
        try:
            connection = self.connection
            version = connection.info.server_version
            require(170000 <= version < 180000, 'POSTGRES_17_REQUIRED')
            for name, value in (('transaction_timeout', f'{self.milliseconds}ms'),
                                ('idle_in_transaction_session_timeout', f'{self.milliseconds}ms'),
                                ('statement_timeout', '200ms'), ('lock_timeout', '1ms')):
                connection.execute('SELECT pg_catalog.set_config(%s, %s, false)', (name, value))
            self.deadline = time.monotonic() + self.milliseconds / 1000
            connection.execute('BEGIN ISOLATION LEVEL READ COMMITTED')
            binding = connection.execute('SELECT current_database(), pg_backend_pid(), backend_start::text '
                'FROM pg_catalog.pg_stat_activity WHERE pid=pg_backend_pid()').fetchone()
            require(binding is not None and binding[0] == self.database, 'FENCE_BACKEND')
            self.backend_pid, self.backend_start = binding[1:]
            rows = connection.execute("SELECT relname, oid, relkind, relpersistence, relrowsecurity "
                "FROM pg_catalog.pg_class WHERE relnamespace='public'::regnamespace AND relname=ANY(%s) "
                'ORDER BY relname', (list(TABLES),)).fetchall()
            require(tuple(row[0] for row in rows) == TABLES and
                    all(row[2:] == ('r', 'p', False) for row in rows), 'PUBLICATION_TABLE_SHAPE')
            self.relations = [row[1] for row in rows]
            connection.execute('LOCK TABLE public.console_auditrecord, public.console_systemmessage '
                               'IN EXCLUSIVE MODE NOWAIT')
            self.locked_at_ns = time.time_ns()
            self.active = True
            self.check()
            counts = dict(connection.execute('SELECT status, count(*) FROM public.console_systemmessage '
                                             'GROUP BY status').fetchall())
            require(set(counts) <= set(STATUSES) and not counts.get('unknown', 0), 'UNRESOLVED_PUBLICATION')
            self.observation = dict(purpose=PURPOSE, server_version=version, backend_pid=self.backend_pid,
                backend_start=self.backend_start, timeout_ms=self.milliseconds,
                message_counts={status: counts.get(status, 0) for status in STATUSES},
                locked_at_ns=self.locked_at_ns, observed_at_ns=time.time_ns(),
                external_settlement_proven=False, capture_permitted=False)
            self.check()
            return self
        except BaseException:
            self.release()
            raise

    def check(self):
        connection = self.connection
        require(self.active and time.monotonic() < self.deadline and not connection.closed and
                connection.info.transaction_status == TransactionStatus.INTRANS and
                connection.info.backend_pid == self.backend_pid, 'PUBLICATION_FENCE_EXPIRED')
        row = connection.execute("SELECT count(DISTINCT relation), "
            "current_setting('transaction_timeout')::interval = %s::interval "
            "FROM pg_catalog.pg_locks WHERE pid=pg_backend_pid() AND granted AND mode='ExclusiveLock' "
            'AND relation=ANY(%s::oid[])', (f'{self.milliseconds}ms', self.relations)).fetchone()
        require(row == (2, True) and time.monotonic() < self.deadline, 'PUBLICATION_FENCE_LOST')

    def release(self):
        try:
            if not self.connection.closed:
                self.connection.rollback()
                self.released = True
                self.released_at_ns = time.time_ns()
        finally:
            self.active = False
            self.connection.close()

    def __exit__(self, *_):
        self.release()


def main():
    require(os.getuid() != 0, 'NONROOT_CONSOLE_REQUIRED')
    require(os.environ.get('POSTGRES_HOST') == 'postgres' and os.environ.get('POSTGRES_PORT', '5432') == '5432',
            'OWNER_POSTGRES_ENDPOINT')
    password = os.environ['POSTGRES_PASSWORD']
    require(len(password) >= 20, 'OWNER_POSTGRES_CREDENTIAL')
    connection = psycopg.connect(host='postgres', port=5432, dbname='fc_control_plane', user='fc_control_plane',
        password=password, autocommit=True, connect_timeout=2, application_name='fc-ha-publication-boundary')
    with PublicationFence(connection, database='fc_control_plane') as fence:
        fence.check()
        receipt = dict(fence.observation)
    receipt.update(rollback_acknowledged=fence.released, released_at_ns=fence.released_at_ns,
                   finished_at_ns=time.time_ns())
    print(json.dumps(receipt, sort_keys=True))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        raise SystemExit('Publication boundary refused or unconfirmed; no capture permission. Do not retry blindly.') from None
