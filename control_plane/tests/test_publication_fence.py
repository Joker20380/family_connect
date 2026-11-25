import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time

from django.contrib.auth import get_user_model
from django.db import connection
import psycopg
import pytest

from apps.console.models import SystemMessage
from scripts.control_ha_publication_fence import PublicationFence


def database_connection():
    settings = connection.settings_dict
    return psycopg.connect(host=settings['HOST'], port=settings['PORT'], dbname=settings['NAME'],
                           user=settings['USER'], password=settings['PASSWORD'], autocommit=True,
                           connect_timeout=2)


def fence(**kwargs):
    return PublicationFence(database_connection(), database=connection.settings_dict['NAME'], **kwargs)


@pytest.fixture
def message(transactional_db):
    actor = get_user_model().objects.create_user(username='synthetic-fence')
    return SystemMessage.objects.create(created_by=actor, title='Synthetic', body='Not production',
                                       kind='information', platforms=['android'], days=1, status='queued')


def test_fence_conflicts_with_select_for_update_but_allows_reads(message):
    with fence() as held, database_connection() as contender:
        assert held.observation['message_counts']['queued'] == 1
        assert not held.observation['capture_permitted'] and not held.observation['external_settlement_proven']
        assert contender.execute('SELECT count(*) FROM public.console_systemmessage').fetchone() == (1,)
        with pytest.raises(psycopg.errors.LockNotAvailable), contender.transaction():
            contender.execute('LOCK TABLE public.console_systemmessage IN ROW SHARE MODE NOWAIT')
        with pytest.raises(psycopg.errors.LockNotAvailable), contender.transaction():
            contender.execute('LOCK TABLE public.console_auditrecord IN ROW EXCLUSIVE MODE NOWAIT')
        held.check()
    assert held.released and held.connection.closed
    with database_connection() as contender, contender.transaction():
        contender.execute('LOCK TABLE public.console_systemmessage IN ROW SHARE MODE NOWAIT')
    message.refresh_from_db()
    assert message.status == 'queued'


@pytest.mark.parametrize('table,mode', [('console_systemmessage', 'ROW SHARE'), ('console_auditrecord', 'ROW EXCLUSIVE')])
def test_old_database_work_refuses_fence_without_waiting_or_canceling(message, table, mode):
    with database_connection() as writer, writer.transaction():
        writer.execute('LOCK TABLE public.' + table + ' IN ' + mode + ' MODE')
        rejected = fence()
        started = time.monotonic()
        with pytest.raises(psycopg.errors.LockNotAvailable), rejected:
            pytest.fail('old work was not fenced')
        assert time.monotonic() - started < 1 and rejected.connection.closed
        assert writer.execute('SELECT 1').fetchone() == (1,)
    with fence() as held:
        held.check()


@pytest.mark.parametrize('status', ['unknown', 'unrecognized'])
def test_uncertain_or_unrecognized_status_is_not_settled(message, status):
    SystemMessage.objects.filter(pk=message.pk).update(status=status)
    rejected = fence()
    with pytest.raises(ValueError, match='UNRESOLVED_PUBLICATION'), rejected:
        pytest.fail('unknown publication accepted')
    message.refresh_from_db()
    assert message.status == status and rejected.connection.closed


@pytest.mark.parametrize('milliseconds', [0, 199, 5001, True, 500.0, '500'])
def test_deadline_is_explicit_and_bounded(transactional_db, milliseconds):
    with database_connection() as database:
        with pytest.raises(ValueError, match='FENCE_DEADLINE'):
            PublicationFence(database, database=connection.settings_dict['NAME'], milliseconds=milliseconds)
        assert not database.closed


def test_existing_transaction_and_other_database_are_not_adopted(transactional_db):
    with database_connection() as database:
        with pytest.raises(ValueError, match='FENCE_DATABASE'):
            PublicationFence(database, database='another-database')
        with database.transaction():
            with pytest.raises(ValueError, match='FRESH_CONNECTION_REQUIRED'):
                PublicationFence(database, database=connection.settings_dict['NAME'])
            assert database.execute('SELECT 1').fetchone() == (1,)


def test_rollback_is_not_silently_reacquired(message):
    held = fence()
    with held:
        held.connection.rollback()
        with pytest.raises(ValueError, match='PUBLICATION_FENCE_EXPIRED'):
            held.check()
    with pytest.raises(ValueError, match='NO_FENCE_RETRY'), held:
        pytest.fail('lease was implicitly recreated')


def test_busy_client_queries_do_not_renew_server_transaction_deadline(message):
    held = fence(milliseconds=500)
    with pytest.raises(psycopg.errors.TransactionTimeout):
        with held:
            deadline = time.monotonic() + 2
            while time.monotonic() < deadline:
                held.connection.execute('SELECT 1')
                time.sleep(.03)
            pytest.fail('server total transaction timeout was renewed')
    assert held.connection.closed
    with fence() as after:
        after.check()


@pytest.mark.parametrize('failure', ['stopped', 'killed'])
def test_server_releases_locks_without_controller_progress(message, failure):
    settings = connection.settings_dict
    environment = {key: value for key, value in os.environ.items() if not key.startswith('PG')}
    environment.update(PGHOST=settings['HOST'], PGPORT=str(settings['PORT']), PGDATABASE=settings['NAME'],
                       PGUSER=settings['USER'], PGPASSWORD=settings['PASSWORD'])
    code = '''import json,time,psycopg
from scripts.control_ha_publication_fence import PublicationFence
database=psycopg.connect(autocommit=True,connect_timeout=2)
with PublicationFence(database,database=database.info.dbname,milliseconds=800) as held:
    print(json.dumps({'backend_pid':held.backend_pid}),flush=True)
    time.sleep(3)
    held.check()
'''
    child = subprocess.Popen([sys.executable, '-c', code], env=environment,
                             cwd=Path(__file__).resolve().parents[2], stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL, text=True)
    try:
        assert select.select([child.stdout], [], [], 5)[0]
        pid = json.loads(child.stdout.readline())['backend_pid']
        with database_connection() as observer:
            assert observer.execute("SELECT count(*) FROM pg_catalog.pg_locks WHERE pid=%s "
                "AND locktype='relation' AND mode='ExclusiveLock' AND granted", (pid,)).fetchone()[0] == 2
            os.kill(child.pid, signal.SIGSTOP if failure == 'stopped' else signal.SIGKILL)
            deadline = time.monotonic() + 3
            while observer.execute('SELECT count(*) FROM pg_catalog.pg_stat_activity WHERE pid=%s', (pid,)).fetchone()[0]:
                assert time.monotonic() < deadline
                time.sleep(.03)
            with observer.transaction():
                observer.execute('LOCK TABLE public.console_systemmessage, public.console_auditrecord '
                                 'IN EXCLUSIVE MODE NOWAIT')
            if failure == 'stopped':
                assert child.poll() is None
                os.kill(child.pid, signal.SIGCONT)
        assert child.wait(timeout=5) != 0
    finally:
        if child.poll() is None:
            child.kill()
        child.wait(timeout=5)
        child.stdout.close()
