from contextvars import copy_context
import os
from pathlib import Path
import select
import subprocess
import sys
import threading

from django.contrib.auth import get_user_model
from django.db import connection, transaction, ProgrammingError
from django.db.backends.postgresql.base import DatabaseWrapper as PostgreSQLWrapper
import pytest

from control.capture_gate import Busy, GateError, initialize
from fc_control_plane.capture import database_admission, operation
from fc_control_plane import capture


pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def gate(tmp_path, monkeypatch):
    connection.close()
    gate = initialize(tmp_path / 'admission')
    monkeypatch.setenv('FC_CONTROL_CAPTURE_GATE', str(gate.directory))
    yield gate
    connection.close()


def markers(gate):
    return {path.name: path.read_bytes() for path in (gate.directory / 'pending').iterdir()}


def child_environment():
    root = Path(__file__).resolve().parents[2]
    return dict(os.environ, PYTHONPATH=os.pathsep.join((str(root), str(root / 'control_plane'))))


def test_direct_orm_requires_admission_before_connect_even_when_closed(gate):
    with pytest.raises(GateError, match='CAPTURE_DATABASE_ADMISSION_REQUIRED'):
        get_user_model().objects.create(username='unadmitted')
    assert connection.connection is None and not markers(gate)
    with gate.drain(.1):
        with pytest.raises(GateError, match='CAPTURE_DATABASE_ADMISSION_REQUIRED'):
            get_user_model().objects.count()
        with pytest.raises(Busy, match='CAPTURE_ADMISSION_CLOSED'):
            with operation():
                pytest.fail('closed manual admission')
    with operation():
        assert not get_user_model().objects.filter(username='unadmitted').exists()


def test_nested_manual_orm_commit_and_close_inside_admission(gate):
    with operation():
        with transaction.atomic():
            get_user_model().objects.create(username='admitted')
            transaction.on_commit(database_admission)
        database = connection.connection
        with operation():
            assert get_user_model().objects.filter(username='admitted').exists()
            assert connection.connection is database
        assert connection.connection is database and len(markers(gate)) == 1
    assert database.closed and connection.connection is None and not markers(gate)
    with gate.drain(.1):
        pass


@pytest.mark.parametrize('raw_begin', [False, True])
def test_escaped_transaction_is_rolled_back_and_preserved_unknown(gate, raw_begin):
    with pytest.raises(GateError, match='CAPTURE_DATABASE_TRANSACTION_UNSETTLED'):
        with operation():
            if raw_begin:
                connection.cursor().execute('BEGIN')
            else:
                connection.set_autocommit(False)
            get_user_model().objects.create(username='never-committed')
    retained = markers(gate)
    assert len(retained) == 1 and connection.connection is None
    with operation():
        assert not get_user_model().objects.filter(username='never-committed').exists()
    assert markers(gate) == retained
    with pytest.raises(GateError, match='UNSETTLED_OPERATION'):
        with gate.drain(.1):
            pytest.fail('unfinished transaction settled')


def test_old_cursor_lazy_iteration_and_copied_context_cannot_write(gate):
    with operation():
        cursor = connection.cursor()
        cursor.execute('SELECT 1')
        copied = copy_context()
        execute = cursor.execute
    for action in (lambda: execute('SELECT 1'), lambda: next(iter(cursor)),
                   lambda: copied.run(database_admission), connection.commit):
        with pytest.raises(GateError, match='CAPTURE_DATABASE_ADMISSION_REQUIRED'):
            action()
    assert not markers(gate)


def test_copied_thread_cannot_reuse_process_admission(gate):
    with operation():
        copied = copy_context()
        outcomes = []
        def writer():
            try:
                copied.run(database_admission)
            except GateError as error:
                outcomes.append(str(error))
        thread = threading.Thread(target=writer)
        thread.start()
        thread.join(3)
        assert not thread.is_alive() and outcomes == ['CAPTURE_DATABASE_ADMISSION_REQUIRED']
    assert not markers(gate)


def test_fork_cannot_reuse_parent_admission(gate):
    code = '''import os
from control.capture_gate import GateError
from fc_control_plane.capture import database_admission, operation
with operation():
    child = os.fork()
    if child == 0:
        try:
            database_admission()
        except GateError:
            os._exit(0)
        os._exit(1)
    assert os.waitpid(child, 0)[1] == 0
'''
    completed = subprocess.run([sys.executable, '-c', code],
        cwd=Path(__file__).resolve().parents[1], env=child_environment(),
        capture_output=True, text=True, timeout=10)
    assert completed.returncode == 0, completed.stderr
    assert not markers(gate)


def test_live_manual_writer_blocks_other_process_drain(gate):
    with operation():
        get_user_model().objects.count()
        code = ('import sys; from control.capture_gate import Gate, Busy; '
                '\ntry:\n with Gate(sys.argv[1]).drain(.05): sys.exit(2)'
                '\nexcept Busy as error:\n print(str(error)); sys.exit(0)')
        completed = subprocess.run([sys.executable, '-c', code, str(gate.directory)],
            cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True, timeout=5)
        assert completed.returncode == 0 and completed.stdout.strip() == 'DRAIN_TIMEOUT'
    with gate.drain(.1):
        pass


def test_subprocess_manual_entry_closes_before_django_setup(gate):
    command = [sys.executable, 'manage.py', 'shell', '-c',
               "raise RuntimeError('must not execute')"]
    with gate.drain(.1):
        completed = subprocess.run(command, cwd=Path(__file__).resolve().parents[1],
                                   capture_output=True, text=True, timeout=10)
    assert completed.returncode == 75 and completed.stderr.strip() == 'CAPTURE_BUSY'
    assert not markers(gate)


def test_installed_mount_cannot_be_disabled_or_redirected_by_environment(gate, monkeypatch):
    monkeypatch.setattr(capture, 'MOUNTED_GATE', gate.directory)
    monkeypatch.delenv('FC_CONTROL_CAPTURE_GATE')
    with gate.drain(.1):
        with pytest.raises(Busy):
            with operation():
                pytest.fail('unset environment bypassed installed gate')
        with pytest.raises(GateError, match='CAPTURE_DATABASE_ADMISSION_REQUIRED'):
            get_user_model().objects.count()
    monkeypatch.setenv('FC_CONTROL_CAPTURE_GATE', '/tmp/different-admission')
    with pytest.raises(GateError, match='CAPTURE_GATE_CONFIGURATION_CHANGED'):
        get_user_model().objects.count()


def test_caught_driver_failure_keeps_unknown(gate):
    with operation():
        with pytest.raises(ProgrammingError, match='synthetic_missing_table'):
            connection.cursor().execute('SELECT * FROM synthetic_missing_table')
    assert len(markers(gate)) == 1
    with pytest.raises(GateError, match='UNSETTLED_OPERATION'):
        with gate.drain(.1):
            pytest.fail('caught database refusal erased uncertainty')


def test_lost_commit_response_keeps_committed_row_and_unknown(gate, monkeypatch):
    commit = PostgreSQLWrapper._commit
    def lost_response(database):
        commit(database)
        raise OSError('synthetic lost commit reply')
    with monkeypatch.context() as patched:
        patched.setattr(PostgreSQLWrapper, '_commit', lost_response)
        with operation():
            with pytest.raises(OSError, match='synthetic lost commit reply'):
                with transaction.atomic():
                    get_user_model().objects.create(username='commit-reply-lost')
    retained = markers(gate)
    assert len(retained) == 1
    with operation():
        assert get_user_model().objects.filter(username='commit-reply-lost').exists()
    assert markers(gate) == retained


def test_killed_manual_writer_preserves_data_and_marker(gate):
    assert connection.settings_dict['NAME'].startswith('test_')
    code = '''import os, sys, django
django.setup()
from django.conf import settings
settings.DATABASES['default']['NAME'] = sys.argv[1]
from django.contrib.auth import get_user_model
from fc_control_plane.capture import operation
with operation():
    get_user_model().objects.create(username='committed-before-kill')
    print('COMMITTED', flush=True)
    os.read(0, 1)
'''
    process = subprocess.Popen([sys.executable, '-c', code, connection.settings_dict['NAME']],
        cwd=Path(__file__).resolve().parents[1], env=child_environment(), stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        assert select.select([process.stdout], [], [], 10)[0]
        assert process.stdout.readline().strip() == 'COMMITTED'
        process.kill()
        process.communicate(timeout=5)
        retained = markers(gate)
        assert len(retained) == 1
        with operation():
            assert get_user_model().objects.filter(username='committed-before-kill').exists()
        assert markers(gate) == retained
        with pytest.raises(GateError, match='UNSETTLED_OPERATION'):
            with gate.drain(.1):
                pytest.fail('killed writer was settled')
    finally:
        if process.poll() is None:
            process.kill()
        process.communicate(timeout=5)
