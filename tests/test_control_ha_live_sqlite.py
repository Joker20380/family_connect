from contextlib import closing
import hashlib
import io
from pathlib import Path
import signal
import sqlite3
import subprocess
import sys
import tarfile

import pytest

from scripts import control_ha_live_sqlite as live


@pytest.fixture
def stores(tmp_path):
    for name in live.STORES.values():
        with closing(sqlite3.connect(tmp_path / name)) as connection:
            if name == live.STORES['metadata']:
                connection.execute(live.METADATA_SQL)
                connection.execute("INSERT INTO device_metadata VALUES ('device',3,4,?,0,100,?)",
                                   ('a' * 64, 'private-observation-must-not-be-archived'))
            else:
                connection.execute('CREATE TABLE sample(value TEXT)')
                connection.execute("INSERT INTO sample VALUES ('private-identity')")
            connection.commit()
    return tmp_path


def contents(root):
    return {item.name: item.read_bytes() for item in root.iterdir()}


def test_capture_all_images_unchanged_source_and_released_locks(stores):
    before = contents(stores)
    images, manifest = live.capture(stores)
    assert contents(stores) == before
    assert manifest['barrier_seconds'] < live.SECONDS
    assert manifest['common_locked_at_ns'] <= manifest['captured_at_ns']
    assert manifest['full_recovery'] is False
    assert manifest['fleet_barrier'] is False
    for store, name in live.STORES.items():
        assert manifest['stores'][store]['sha256'] == hashlib.sha256(images[store]).hexdigest()
        with closing(sqlite3.connect(':memory:')) as restored:
            restored.deserialize(images[store])
            if store == 'metadata':
                assert restored.execute('SELECT * FROM device_metadata').fetchall() == [('device', 3, 4, 'a' * 64, 0, 100, '{}')]
                assert b'private-observation' not in images[store]
            else:
                assert restored.execute('SELECT value FROM sample').fetchall() == [('private-identity',)]
        with closing(sqlite3.connect(stores / name, timeout=0)) as writer:
            writer.execute('BEGIN IMMEDIATE')
            writer.rollback()
    with tarfile.open(fileobj=io.BytesIO(live.archive(images, manifest))) as bundle:
        assert set(bundle.getnames()) == {store + '.sqlite' for store in live.STORES} | {'manifest.json'}
        assert all(member.mode == 0o600 and member.isfile() for member in bundle.getmembers())


@pytest.mark.parametrize('busy_store', live.STORES)
def test_busy_store_aborts_and_releases_preceding_locks(stores, busy_store):
    before = contents(stores)
    with closing(sqlite3.connect(stores / live.STORES[busy_store])) as busy:
        busy.execute('BEGIN IMMEDIATE')
        with pytest.raises(sqlite3.OperationalError, match='locked'):
            live.capture(stores)
    assert signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0)
    assert contents(stores) == before
    live.capture(stores)


def test_wal_capture_includes_uncheckpointed_commits_without_checkpoint(stores):
    path = stores / live.STORES['registry']
    with closing(sqlite3.connect(path)) as writer:
        writer.execute('PRAGMA journal_mode=WAL')
        writer.execute('PRAGMA wal_autocheckpoint=0')
        writer.execute("INSERT INTO sample VALUES ('wal-only')")
        writer.commit()
        before = contents(stores)
        images, _ = live.capture(stores)
        after = contents(stores)
        assert after.keys() == before.keys()
        for name in before:
            if not name.endswith('-shm'):
                assert after[name] == before[name]
        with closing(sqlite3.connect(':memory:')) as restored:
            restored.deserialize(images['registry'])
            assert restored.execute('SELECT count(*) FROM sample').fetchone() == (2,)


def test_every_store_is_write_locked_before_any_image_is_read(stores, monkeypatch):
    connect = sqlite3.connect
    checked = []

    class ObservedConnection(sqlite3.Connection):
        def serialize(self):
            for name in live.STORES.values():
                with closing(connect(stores / name, timeout=0)) as writer:
                    with pytest.raises(sqlite3.OperationalError, match='locked'):
                        writer.execute('BEGIN IMMEDIATE')
            checked.append(True)
            return super().serialize()

    def observed(*args, **kwargs):
        return connect(*args, **kwargs, factory=ObservedConnection)

    monkeypatch.setattr(live.sqlite3, 'connect', observed)
    live.capture(stores)
    assert len(checked) == 4


def test_missing_wal_sidecars_refused_before_sqlite_opens(stores):
    path = stores / live.STORES['registry']
    with closing(sqlite3.connect(path)) as writer:
        writer.execute('PRAGMA journal_mode=WAL')
    before = contents(stores)
    with pytest.raises(ValueError, match='WAL_SIDECARS_REQUIRED'):
        live.capture(stores)
    assert contents(stores) == before


@pytest.mark.parametrize('fault', ['missing', 'link', 'hardlink', 'hot-journal', 'sidecar-link', 'large'])
def test_preflight_refuses_unsafe_sources_without_partial_capture(stores, fault, monkeypatch):
    path = stores / live.STORES['registry']
    if fault == 'missing':
        path.unlink()
    elif fault == 'link':
        path.unlink()
        path.symlink_to(stores / live.STORES['metadata'])
    elif fault == 'hardlink':
        (stores / 'extra').hardlink_to(path)
    elif fault == 'hot-journal':
        Path(str(path) + '-journal').write_bytes(b'possibly-hot')
    elif fault == 'sidecar-link':
        Path(str(path) + '-wal').symlink_to(path)
    else:
        monkeypatch.setattr(live, 'LIMIT', 512)
    before = contents(stores)
    with pytest.raises((ValueError, FileNotFoundError)):
        live.capture(stores)
    assert contents(stores) == before


def test_replaced_database_aborts_and_releases(stores, monkeypatch):
    original = live.identity
    calls = 0

    def replaced(path):
        nonlocal calls
        calls += 1
        return original(path) if calls <= 4 else (0, 0)

    monkeypatch.setattr(live, 'identity', replaced)
    with pytest.raises(ValueError, match='DATABASE_REPLACED'):
        live.capture(stores)
    assert signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0)


def test_kernel_deadline_kills_stalled_capturer_and_releases_lock(stores):
    code = '''from pathlib import Path
import sqlite3,time
from scripts import control_ha_live_sqlite as live
original = live.identity
calls = 0
def stalled(path):
    global calls
    calls += 1
    if calls > 4:
        time.sleep(10)
    return original(path)
live.identity = stalled
live.capture(Path(__import__('sys').argv[1]))
'''
    result = subprocess.run([sys.executable, '-c', code, str(stores)], capture_output=True, timeout=4)
    assert result.returncode == -signal.SIGALRM
    assert result.stdout == b''
    live.capture(stores)


def test_preexisting_alarm_is_not_overwritten(stores):
    signal.setitimer(signal.ITIMER_REAL, 30)
    try:
        with pytest.raises(ValueError, match='ALARM_NOT_EXCLUSIVE'):
            live.capture(stores)
        assert signal.getitimer(signal.ITIMER_REAL)[0] > 20
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


@pytest.mark.parametrize('enabled', [0, 1])
def test_metadata_projection_preserves_floor_and_replay_does_not_restore_observations(stores, enabled):
    from control.friends import technical_metadata
    with closing(sqlite3.connect(stores / live.STORES['metadata'])) as database:
        database.execute('UPDATE device_metadata SET enabled=?', (enabled,))
        database.commit()
    images, manifest = live.capture(stores)
    assert manifest['metadata_projection'] == 'consent-floors-only'
    with closing(sqlite3.connect(':memory:')) as restored:
        restored.deserialize(images['metadata'])
        transaction = technical_metadata.MetadataTransaction(restored)
        previous = transaction.previous('device')
        assert previous['enabled'] == enabled and previous['payload'] == '{}'
        report = dict(schema=1, consent_epoch=3, sequence=4, operation='sample' if enabled else 'revoke',
                      report_id='00000000000000030000000000000004', observations={})
        technical_metadata.record(transaction, 'device', report, 'a' * 64, 200)
        assert transaction.previous('device') == previous
        if not enabled:
            report.update(sequence=5, operation='sample')
            with pytest.raises(technical_metadata.Rejected):
                technical_metadata.record(transaction, 'device', report, 'b' * 64, 200)
