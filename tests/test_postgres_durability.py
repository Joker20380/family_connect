from types import SimpleNamespace

import pytest

psycopg = pytest.importorskip('psycopg')

from control.friends.postgres_durability import DurableConnection, ReplicationAcknowledgementUncertain


@pytest.fixture
def connection(monkeypatch):
    monkeypatch.setattr(psycopg.Connection, '__init__', lambda *args, **kwargs: None)
    monkeypatch.setattr(DurableConnection, 'add_notice_handler', lambda self, handler: None)
    return DurableConnection()


@pytest.mark.parametrize('severity', ['NOTICE', 'INFO', 'DEBUG', 'LOG'])
def test_nonwarning_commit_notice_does_not_invent_uncertainty(connection, monkeypatch, severity):
    def commit(self):
        self._observe_commit(SimpleNamespace(severity_nonlocalized=severity))
    monkeypatch.setattr(psycopg.Connection, 'commit', commit)
    connection.commit()
    assert connection._committing is False


def test_warning_during_commit_refuses_ack_and_closes_connection(connection, monkeypatch):
    closed = []
    def commit(self):
        self._observe_commit(SimpleNamespace(severity_nonlocalized='WARNING', severity='ПРЕДУПРЕЖДЕНИЕ'))
    monkeypatch.setattr(psycopg.Connection, 'commit', commit)
    monkeypatch.setattr(DurableConnection, 'close', lambda self: closed.append(True))
    with pytest.raises(ReplicationAcknowledgementUncertain, match='reconcile the original operation'):
        connection.commit()
    assert closed == [True] and connection._committing is False


def test_normal_command_warning_does_not_poison_later_commit(connection, monkeypatch):
    connection._observe_commit(SimpleNamespace(severity_nonlocalized='WARNING'))
    monkeypatch.setattr(psycopg.Connection, 'commit', lambda self: None)
    connection.commit()
    assert connection._commit_warning is False


def test_failed_commit_remains_a_failure(connection, monkeypatch):
    def commit(self):
        raise psycopg.OperationalError('synthetic connection loss')
    monkeypatch.setattr(psycopg.Connection, 'commit', commit)
    with pytest.raises(psycopg.OperationalError):
        connection.commit()
    assert connection._committing is False
