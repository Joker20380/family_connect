import sqlite3

import pytest

from scripts.backup_paid_registry import backup


def test_readonly_backup_restore_is_consistent_and_private(tmp_path):
    source = tmp_path / 'source.db'
    with sqlite3.connect(source) as database:
        database.execute('CREATE TABLE devices(device TEXT PRIMARY KEY, secret BLOB)')
        database.execute('INSERT INTO devices VALUES (?,?)', ('synthetic', b'synthetic-secret'))
    before = source.read_bytes()
    destination = tmp_path / 'backup'
    receipt = backup(source, destination)
    assert receipt['result'] == 'BACKUP_AND_ISOLATED_SQLITE_RESTORE_PASS'
    assert receipt['live_database_writes'] == receipt['service_restarts'] == 0
    assert source.read_bytes() == before
    assert 'synthetic-secret' not in (destination / 'receipt.json').read_text()
    assert destination.stat().st_mode & 0o777 == 0o700
    assert (destination / 'registry.sqlite3').stat().st_mode & 0o777 == 0o600
    assert not (destination / 'restore-rehearsal.sqlite3').exists()
    with pytest.raises(ValueError):
        backup(source, destination)


def test_nonempty_cohort_refuses_prepaid_recovery_procedure(tmp_path):
    source = tmp_path / 'source.db'
    with sqlite3.connect(source) as database:
        database.execute('CREATE TABLE paid_beta_subscriptions(device TEXT)')
        database.execute("INSERT INTO paid_beta_subscriptions VALUES ('synthetic')")
    with pytest.raises(ValueError, match='Nonempty'):
        backup(source, tmp_path / 'backup')
    assert not (tmp_path / 'backup').exists()


def test_source_symlink_is_not_followed(tmp_path):
    source = tmp_path / 'source.db'
    sqlite3.connect(source).close()
    link = tmp_path / 'link.db'
    link.symlink_to(source)
    with pytest.raises(ValueError, match='Symlink'):
        backup(link, tmp_path / 'backup')
