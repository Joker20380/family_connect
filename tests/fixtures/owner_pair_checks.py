import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import uuid

import psycopg
import pytest

from control.capture_native import ReadOnlyTrees
from control_plane.fc_control_plane.capture_pg_boundary import PostgresBoundary, scope
from test_control_ha_owner_runtime import source
from test_owner_held import store


@pytest.fixture
def database():
    assert os.geteuid() == 0 and os.environ.get('FC_NATIVE_PRIVATE_NAMESPACE') == '1'
    assert os.readlink('/proc/self/ns/mnt') != os.readlink('/proc/1/ns/mnt')
    assert psycopg.__version__ == '3.3.6'
    name = 'fc-ha02-pair-lab-' + uuid.uuid4().hex
    image = os.environ.get('FC_OWNER_LAB_POSTGRES',
        'sha256:18cfe3ef5e6815560c98237d6216d1e5119702fb0f3894c8785dd58b8bbe5d73')
    def docker(*args):
        return subprocess.run(['docker', *args], check=True, capture_output=True, timeout=30).stdout
    docker('create', '--name', name, '--label', 'family-connect.owner-pair-lab=' + name,
        '--read-only', '--tmpfs', '/var/lib/postgresql/data:rw', '--tmpfs', '/var/run/postgresql:rw',
        '--publish', '127.0.0.1::5432', '--env', 'POSTGRES_PASSWORD=synthetic-owner-lab',
        '--env', 'POSTGRES_DB=fc_owner_lab', image)
    try:
        docker('start', name)
        port = docker('port', name, '5432/tcp').decode().strip().split(':')[1]
        options = dict(host='127.0.0.1', port=int(port), user='postgres', password='synthetic-owner-lab',
                       dbname='fc_owner_lab', autocommit=True, connect_timeout=2)
        deadline = time.monotonic() + 20
        while True:
            try:
                connection = psycopg.connect(**options)
                break
            except psycopg.OperationalError:
                assert time.monotonic() < deadline, 'LAB_POSTGRES_NOT_READY'
                time.sleep(.1)
        with connection:
            connection.execute('CREATE TABLE console_operationrequest(id uuid PRIMARY KEY, status text, payload_hash text)')
            connection.execute('CREATE SEQUENCE operation_sequence')
            connection.execute('INSERT INTO console_operationrequest VALUES (%s, %s, %s)',
                               (uuid.UUID(int=1), 'UNKNOWN', 'a' * 64))
        yield options
    finally:
        docker('rm', '-f', name)


@pytest.mark.parametrize('store_uid', [0, 10001])
def test_pg_sqlite_native_lifetime_preserves_unknown_and_expired_projections(database, store, tmp_path, store_uid):
    for path in (store.root, store.root / 'registry.sqlite3', store.root / 'seed.lock'):
        os.chown(path, store_uid, store_uid)
    store.store_uid = store_uid
    before = hashlib.sha256((store.root / 'registry.sqlite3').read_bytes()).hexdigest()
    journal = tmp_path.parent / ('pair-journal-' + uuid.uuid4().hex)
    connection = psycopg.connect(**database)
    with PostgresBoundary(connection, scope(connection), milliseconds=10000) as postgres, store:
        with ReadOnlyTrees([tmp_path], journal, 'isolated-owner') as native:
            files, receipt = store.snapshot(postgres, native, support_snapshot_sha256='b' * 64)
            assert receipt['pg_pair_fence'] and not receipt['fleet_capture']
            assert json.loads(files['pg-operation-history.json'])[0]['status'] == 'UNKNOWN'
            assert json.loads(files['subscriptions.json'])['expires_at'] == 100
            assert receipt['leases'] == dict(sqlite=store.check(), postgres=postgres.check(), native=native.check())
            with psycopg.connect(**database) as late:
                late.execute("SET statement_timeout='100ms'")
                with pytest.raises(psycopg.errors.QueryCanceled):
                    late.execute("UPDATE console_operationrequest SET status='DONE'")
            with pytest.raises(OSError):
                (store.root / 'initializing.sqlite3').write_bytes(b'late seed')
    assert hashlib.sha256((store.root / 'registry.sqlite3').read_bytes()).hexdigest() == before
    with psycopg.connect(**database) as reader:
        assert reader.execute('SELECT status FROM console_operationrequest').fetchone() == ('UNKNOWN',)
        reader.execute("UPDATE console_operationrequest SET status='RECONCILIATION_REQUIRED' WHERE status='UNKNOWN'")
        assert reader.execute('SELECT status FROM console_operationrequest').fetchone() == ('RECONCILIATION_REQUIRED',)


def test_pg_lease_loss_never_returns_a_new_pair(database, store, tmp_path):
    connection = psycopg.connect(**database)
    journal = tmp_path.parent / ('pair-loss-' + uuid.uuid4().hex)
    with PostgresBoundary(connection, scope(connection), milliseconds=10000) as postgres, store:
        with ReadOnlyTrees([tmp_path], journal, 'isolated-owner') as native:
            connection.rollback()
            with pytest.raises(ValueError):
                store.snapshot(postgres, native, support_snapshot_sha256='b' * 64)
