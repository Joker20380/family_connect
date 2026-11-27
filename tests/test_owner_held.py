import fcntl
import json
import sqlite3

import pytest

from test_control_ha_owner_runtime import source
from scripts.control_ha_owner_held import HeldSynthetic


@pytest.fixture
def store(source, tmp_path):
    root, aliases = source
    config = tmp_path / 'config'
    config.mkdir()
    copied = config / 'collector-aliases.json'
    copied.write_bytes(aliases.read_bytes())
    key = config / 'key'
    key.write_bytes(b'k' * 32)
    projections = {}
    for name in ('support-bindings', 'subscriptions'):
        path = config / (name + '.json')
        path.write_text(json.dumps(dict(expires_at=100, cursor='historical-not-fresh')))
        projections[name] = path
    return HeldSynthetic(root, aliases, copied, key, projections, 'isolated-owner')


def test_sqlite_and_seed_lifetime_cover_returned_snapshot_until_exit(store):
    with store:
        lease = store.check()
        assert store.projection_raw['subscriptions'] == b'{"expires_at": 100, "cursor": "historical-not-fresh"}'
        with (store.root / 'seed.lock').open() as stream:
            with pytest.raises(BlockingIOError):
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with sqlite3.connect(store.root / 'registry.sqlite3', timeout=0, isolation_level=None) as other:
            with pytest.raises(sqlite3.OperationalError, match='locked'):
                other.execute('BEGIN IMMEDIATE')
        assert store.check() == lease
    with sqlite3.connect(store.root / 'registry.sqlite3', timeout=0, isolation_level=None) as other:
        other.execute('BEGIN IMMEDIATE')
        other.rollback()
    assert store.key_raw is None


@pytest.mark.parametrize('filename', ['initializing.sqlite3', 'registry.sqlite3-wal',
                                     'registry.sqlite3-shm', 'registry.sqlite3-journal'])
def test_seed_and_sidecars_require_explicit_reconciliation(store, filename):
    (store.root / filename).touch()
    with pytest.raises(ValueError, match='OWNER_SIDECAR_OR_INCOMPLETE_SEED'):
        store.__enter__()
    assert (store.root / filename).exists()


def test_alias_key_generation_disagreement_refuses(store):
    value = json.loads(store.collector_aliases.read_bytes())
    value['generation'] += 1
    store.collector_aliases.write_text(json.dumps(value))
    with pytest.raises(ValueError, match='OWNER_ALIASES_DISAGREE'):
        store.__enter__()


def test_wrong_store_uid_refuses_before_lock(store):
    store.store_uid += 1
    with pytest.raises(ValueError, match='OWNER_PRIVATE_STORE'):
        store.__enter__()


def test_released_sqlite_cannot_be_reacquired_as_old_lease(store):
    with store:
        store.connection.rollback()
        with pytest.raises(ValueError, match='OWNER_SQLITE_LEASE_LOST'):
            store.check()
        store.connection.execute('BEGIN IMMEDIATE')
        with pytest.raises(ValueError, match='OWNER_SQLITE_LEASE_LOST'):
            store.check()
    with pytest.raises(ValueError, match='OWNER_NO_REACQUIRE'):
        store.__enter__()


@pytest.mark.parametrize('statement', ['ROLLBACK', '-- transaction\nROLLBACK'])
def test_sqlite_rollback_begin_between_checks_cannot_hide_lease_loss(store, statement):
    with store:
        store.connection.execute(statement)
        store.connection.execute('BEGIN IMMEDIATE')
        with pytest.raises(ValueError, match='OWNER_SQLITE_LEASE_LOST'):
            store.check()
