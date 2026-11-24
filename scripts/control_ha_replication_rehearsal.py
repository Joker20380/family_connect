"""Owned loopback PostgreSQL/Patroni quorum failures; synthetic inputs, never deployment."""
import argparse
import base64
import json
import os
from pathlib import Path
import re
import secrets
import signal
import socket
import subprocess
import sys
import time
import urllib.request
import uuid

import psycopg
from psycopg import sql
from psycopg.rows import dict_row

from control.friends.access import Access
from control.friends.enrollment_postgres import PostgresEnrollment
from scripts.control_ha_import import import_snapshot, ImportRejected
from scripts.control_ha_rehearsal import Rehearsal as EtcdRehearsal, private_file, require
from scripts.control_ha_sqlite_rehearsal import SQLiteImportRehearsal
from scripts.control_ha_sqlite_fixture import exercise_import
from scripts.enrollment_postgres_rehearsal import Rehearsal as PostgresRehearsal, ROOT
from scripts.paid_postgres_rehearsal import apply
from scripts.referral_postgres_rehearsal import NOW, refused

LABEL = 'family-connect.ha-replication-rehearsal'
IMAGE_LABEL = 'isolated-only-v1'
TTL = 20


def wait_for(action, timeout=60):
    deadline = time.monotonic() + timeout
    while True:
        try:
            return action()
        except (AssertionError, psycopg.Error, OSError, ValueError) as error:
            if time.monotonic() >= deadline:
                raise RuntimeError('Replication condition timed out; private evidence retained') from error
            time.sleep(0.25)


def configuration(token, index, ports, endpoints, password, replication_password):
    database_port, api_port = ports[index]
    return dict(scope='fc-ha-' + token, namespace='/family-connect-rehearsal/', name='node' + str(index),
        restapi=dict(listen='127.0.0.1:' + str(api_port), connect_address='127.0.0.1:' + str(api_port),
                     authentication=dict(username='rehearsal', password=password)),
        etcd3=dict(hosts=[endpoint.removeprefix('https://') for endpoint in endpoints], protocol='https',
                   cacert='/tmp/lab/ca.pem', cert='/tmp/lab/client.pem', key='/tmp/lab/client.key'),
        bootstrap=dict(dcs=dict(ttl=TTL, loop_wait=1, retry_timeout=3, maximum_lag_on_failover=0,
            check_timeline=True, failsafe_mode=False, synchronous_mode='quorum', synchronous_mode_strict=True,
            synchronous_node_count=1, postgresql=dict(use_pg_rewind=True, parameters=dict(
                fsync='on', full_page_writes='on', synchronous_commit='on', wal_level='replica',
                wal_log_hints='on', max_wal_senders=10, max_replication_slots=10, max_connections=40,
                hot_standby='on', log_statement='none', password_encryption='scram-sha-256'))),
            initdb=[dict(encoding='UTF8'), 'data-checksums'],
            pg_hba=['host replication replicator 127.0.0.1/32 scram-sha-256',
                    'host all fc_ha_synthetic 127.0.0.1/32 scram-sha-256', 'local all all trust']),
        postgresql=dict(listen='127.0.0.1:' + str(database_port),
            connect_address='127.0.0.1:' + str(database_port), data_dir='/tmp/lab/data', bin_dir='/usr/local/bin',
            authentication=dict(superuser=dict(username='fc_ha_synthetic', password=password),
                                replication=dict(username='replicator', password=replication_password)),
            parameters=dict(unix_socket_directories='/tmp', port=database_port)),
        watchdog=dict(mode='off'))


def read_snapshot(repository):
    with repository.connect() as database:
        database.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        database.execute(sql.SQL('SET LOCAL search_path TO {}, pg_catalog').format(sql.Identifier(repository.schema)))
        tables = database.execute('SELECT tablename FROM pg_tables WHERE schemaname=current_schema() ORDER BY tablename').fetchall()
        return {row['tablename']: database.execute(sql.SQL('SELECT * FROM {} ORDER BY 1').format(
            sql.Identifier(row['tablename']))).fetchall() for row in tables}


class ReplicationRehearsal(PostgresRehearsal):
    def __init__(self, root, binary, image):
        require(type(image) is str and re.fullmatch(r'sha256:[0-9a-f]{64}', image), 'LOCAL_IMAGE_ID_REQUIRED')
        super().__init__(root)
        self.binary, self.image = Path(binary), image
        self.nodes, self.etcd, self.reservations = {}, None, []
        self.ports = []
        self.schema = 'ha_enrollment_' + uuid.uuid4().hex

    def owned_node(self, index):
        cidfile = self.root / ('node' + str(index) + '.id')
        if index not in self.nodes and cidfile.exists():
            self.nodes[index] = cidfile.read_text().strip()
        if index not in self.nodes:
            return False
        container = self.nodes[index]
        require(re.fullmatch('[0-9a-f]{64}', container), 'INVALID_REHEARSAL_CONTAINER')
        label = self.docker('inspect', '--format', '{{index .Config.Labels "' + LABEL + '"}}', container)
        require(label == self.token + ':' + str(index), 'REHEARSAL_CONTAINER_OWNERSHIP')
        return True

    def node_action(self, index, *action):
        require(self.owned_node(index), 'REHEARSAL_CONTAINER_MISSING')
        return self.docker(*action, self.nodes[index])

    def __enter__(self):
        try:
            label = self.docker('image', 'inspect', '--format',
                '{{index .Config.Labels "family-connect.ha-replication-image"}}', self.image)
            require(label == IMAGE_LABEL, 'REHEARSAL_IMAGE_REQUIRED')
            self.etcd = EtcdRehearsal(self.binary, self.root / 'etcd')
            self.etcd.__enter__()
            for index in range(3):
                pair = []
                for _ in range(2):
                    reservation = socket.socket()
                    reservation.bind(('127.0.0.1', 0))
                    self.reservations.append(reservation)
                    pair.append(reservation.getsockname()[1])
                self.ports.append(pair)
            replication_password = secrets.token_hex(32)
            for index in range(3):
                material = self.root / ('node' + str(index))
                material.mkdir(mode=0o700)
                config = configuration(self.token, index, self.ports, self.etcd.endpoints, self.password, replication_password)
                private_file(material / 'config.json', json.dumps(config).encode())
                for name in ('ca.pem', 'client.pem', 'client.key'):
                    private_file(material / name, (self.etcd.root / name).read_bytes())
                self.nodes[index] = self.docker('create', '--pull=never', '--network=host', '--memory=512m', '--cpus=1',
                    '--name', 'fc-ha-replication-' + self.token + '-' + str(index),
                    '--label', LABEL + '=' + self.token + ':' + str(index),
                    '--cidfile', str(self.root / ('node' + str(index) + '.id')), self.image)
                self.docker('cp', str(material), self.nodes[index] + ':/tmp/lab')
            for reservation in self.reservations:
                reservation.close()
            for index in range(3):
                self.node_action(index, 'start')
            primary = self.wait_cluster()
            with self.connect(primary, autocommit=True) as database:
                database.execute('CREATE DATABASE fc_ha_synthetic')
            self.wait_cluster()
            return self
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def connect(self, index, *, autocommit=False):
        return psycopg.connect(host='127.0.0.1', hostaddr='127.0.0.1', port=self.ports[index][0],
            dbname='postgres', user='fc_ha_synthetic', password=self.password, connect_timeout=2,
            sslmode='disable', row_factory=dict_row, autocommit=autocommit)

    def repository_at(self, index):
        return PostgresEnrollment(port=self.ports[index][0], schema=self.schema, password=self.password)

    def status(self, index, route='/patroni'):
        require(route in ('/patroni', '/config', '/cluster'), 'REHEARSAL_STATUS_ROUTE')
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        request = urllib.request.Request('http://127.0.0.1:' + str(self.ports[index][1]) + route,
            headers={'Authorization': 'Basic ' + base64.b64encode(('rehearsal:' + self.password).encode()).decode()})
        with opener.open(request, timeout=2) as response:
            return json.loads(response.read(65536))

    def primary(self, exclude=()):
        def elected():
            primaries = []
            for index in range(3):
                if index in exclude:
                    continue
                try:
                    status = self.status(index)
                    if status['state'] == 'running' and status['role'] == 'primary':
                        with self.connect(index) as database:
                            require(not database.execute('SELECT pg_is_in_recovery() AS recovery').fetchone()['recovery'],
                                    'PRIMARY_IS_RECOVERY')
                        primaries.append(index)
                except (OSError, psycopg.Error):
                    continue
            require(len(primaries) == 1, 'EXACTLY_ONE_PRIMARY_REQUIRED')
            return primaries[0]
        return wait_for(elected)

    def wait_cluster(self):
        primary = self.primary()
        def healthy():
            effective = self.status(primary, '/config')
            require(effective['synchronous_mode'] == 'quorum' and effective['synchronous_mode_strict'] is True and
                    effective['synchronous_node_count'] == 1 and effective['failsafe_mode'] is False and
                    effective['ttl'] == TTL and effective['maximum_lag_on_failover'] == 0 and
                    effective['check_timeline'] is True, 'EFFECTIVE_REPLICATION_CONFIG')
            cluster = self.status(primary, '/cluster')
            roles = sorted(member['role'] for member in cluster['members'])
            require(roles == ['leader', 'quorum_standby', 'quorum_standby'], 'DCS_SYNC_VOTERS_NOT_READY')
            with self.connect(primary) as database:
                require(database.execute('SHOW server_version').fetchone()['server_version'].split()[0] ==
                        self.manifest['version'], 'POSTGRES_VERSION_MISMATCH')
                for setting in ('fsync', 'full_page_writes', 'synchronous_commit'):
                    require(database.execute('SHOW ' + setting).fetchone()[setting] == 'on', 'DURABILITY_DISABLED')
                sync = database.execute('SHOW synchronous_standby_names').fetchone()['synchronous_standby_names']
                require(sync.startswith('ANY 1 (') and '*' not in sync, 'STRICT_QUORUM_NOT_READY')
                rows = database.execute('SELECT application_name,state,sync_state FROM pg_stat_replication').fetchall()
                require(len(rows) == 2 and all(row['state'] == 'streaming' and row['sync_state'] == 'quorum'
                        for row in rows), 'REPLICAS_NOT_STREAMING')
            for index in range(3):
                require(self.status(index)['patroni']['version'] == '4.1.5', 'PATRONI_VERSION_MISMATCH')
            return primary
        return wait_for(healthy)

    def assert_copies(self, expected):
        for index in range(3):
            def identical():
                require(read_snapshot(self.repository_at(index)) == expected, 'REPLICA_STATE_DIFFERS')
            wait_for(identical)

    def run(self):
        fixture, frozen = SQLiteImportRehearsal.capture_fixture(self)
        original_primary = primary = self.primary()
        repository = self.repository_at(primary)
        import_snapshot(repository, frozen)
        behavior = exercise_import(fixture, repository)
        access = Access(None, clock=lambda: NOW, enrollment_repository=repository)
        with access.enrollment() as transaction:
            support = transaction.registered(fixture.device.reference)
            apply(transaction.paid(), support, event_id='replication-payment')
            apply(transaction.paid(), support, 'revoke', 'replication-revoke')
        acknowledged = read_snapshot(repository)
        self.assert_copies(acknowledged)
        unfinished = repository.connect()
        try:
            repository.configure(unfinished)
            unfinished.execute('UPDATE devices SET revoked=1')
            self.node_action(primary, 'kill', '--signal', 'KILL')
        finally:
            unfinished.close()
        successor = self.primary(exclude=(primary,))
        require(successor != primary, 'PRIMARY_DID_NOT_CHANGE')
        recovered = self.repository_at(successor)
        require(read_snapshot(recovered) == acknowledged, 'ACKNOWLEDGED_STATE_LOST_OR_UNCOMMITTED_VISIBLE')
        access = Access(None, clock=lambda: NOW, enrollment_repository=recovered)
        refused(lambda: access.complete(fixture.pending['status'], 'status'))
        try:
            import_snapshot(recovered, frozen)
        except ImportRejected:
            pass
        else:
            raise ValueError('STALE_IMPORT_ACCEPTED')
        self.node_action(primary, 'start')
        self.wait_cluster()
        self.assert_copies(acknowledged)
        primary = self.primary()
        access = Access(None, clock=lambda: NOW, enrollment_repository=self.repository_at(primary))
        fresh = access.challenge(fixture.device.public_identity, fixture.device.wireguard_public_key, 'status')
        proof = fixture.device.prove_transport_key(fresh['challenge'])
        access.complete(proof, 'status')
        acknowledged = read_snapshot(self.repository_at(primary))
        self.assert_copies(acknowledged)
        self.etcd.stop(0)
        fresh = access.challenge(fixture.device.public_identity, fixture.device.wireguard_public_key, 'status')
        access.complete(fixture.device.prove_transport_key(fresh['challenge']), 'status')
        acknowledged = read_snapshot(self.repository_at(primary))
        self.assert_copies(acknowledged)
        self.etcd.start(0)
        for index in (0, 1):
            self.etcd.stop(index)
        time.sleep(TTL + 5)
        self.assert_no_writer()
        for index in (0, 1):
            self.etcd.start(index)
        self.wait_cluster()
        self.assert_copies(acknowledged)
        no_sync = self.without_standbys(fixture)
        canceled_sync = self.without_standbys(fixture, cancel=True)
        return dict(result='ISOLATED_PATRONI_RPO0_PASS', postgres=self.manifest['version'], patroni='4.1.5',
            etcd=self.etcd.manifest['version'], image=self.image, synchronous_mode='quorum', synchronous_node_count=1,
            synchronous_mode_strict=True, original_primary=original_primary, successor=successor,
            primary_loss='ACKNOWLEDGED_STATE_EXACT_UNCOMMITTED_ABSENT', primary_return='ALL_THREE_EXACT',
            dcs_minority_loss='PRODUCT_WRITES_CONTINUE', dcs_majority_loss='NO_WRITABLE_PRIMARY_AFTER_TTL',
            dcs_return='ALL_THREE_EXACT', no_synchronous_standbys=no_sync, canceled_sync_wait=canceled_sync,
            consumed_proof='REFUSED', old_import='REFUSED', rows={name: len(rows) for name, rows in acknowledged.items()},
            behavior=behavior, production_writes=0, activation='FORBIDDEN', independent_failure_domains='NOT_QUALIFIED')

    def without_standbys(self, fixture, *, cancel=False):
        primary = self.primary()
        repository = self.repository_at(primary)
        access = Access(None, clock=lambda: NOW, enrollment_repository=repository)
        fresh = access.challenge(fixture.device.public_identity, fixture.device.wireguard_public_key, 'status')
        proof = fixture.device.prove_transport_key(fresh['challenge'])
        before = read_snapshot(repository)
        self.assert_copies(before)
        standbys = [index for index in range(3) if index != primary]
        for index in standbys:
            self.node_action(index, 'kill', '--signal', 'KILL')
        code = '''import json,sys
sys.path.insert(0,sys.argv[1])
from control.friends.access import Access
from control.friends.enrollment_postgres import PostgresEnrollment
inputs=json.load(sys.stdin)
repository=PostgresEnrollment(port=inputs['port'],schema=inputs['schema'],password=inputs['password'])
original_connect=repository.connect
def connect():
    database=original_connect()
    database.execute("SET application_name='fc-ha-sync-probe'")
    database.add_notice_handler(lambda diagnostic: print('NOTICE '+str(diagnostic.sqlstate),flush=True))
    return database
repository.connect=connect
access=Access(None,clock=lambda: inputs['now'],enrollment_repository=repository)
access.complete(inputs['proof'],'status')
print('COMMIT_ACK',flush=True)
'''
        logfile = self.root / ('canceled-sync-client.log' if cancel else 'no-sync-client.log')
        descriptor = os.open(logfile, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, 'wb') as output:
            process = subprocess.Popen([sys.executable, '-I', '-B', '-c', code, str(ROOT)], stdin=subprocess.PIPE,
                stdout=output, stderr=output, env=self.environment)
            try:
                inputs = dict(port=repository.port, schema=repository.schema, password=self.password, now=NOW, proof=proof)
                process.stdin.write(json.dumps(inputs).encode())
                process.stdin.close()
                def waiting():
                    require(process.poll() is None, 'NO_SYNC_CLIENT_RETURNED')
                    with self.connect(primary) as database:
                        require(database.execute("SELECT count(*) AS waiting FROM pg_stat_activity WHERE wait_event='SyncRep' "
                                                 "AND application_name='fc-ha-sync-probe'")
                                .fetchone()['waiting'] >= 1, 'CLIENT_NOT_WAITING_FOR_SYNC')
                wait_for(waiting, timeout=15)
                time.sleep(TTL + 2)
                require(process.poll() is None and b'COMMIT_ACK' not in logfile.read_bytes(), 'NO_SYNC_COMMIT_ACKNOWLEDGED')
                if cancel:
                    with self.connect(primary, autocommit=True) as database:
                        canceled = database.execute("SELECT pg_cancel_backend(pid) AS canceled FROM pg_stat_activity "
                            "WHERE wait_event='SyncRep' AND application_name='fc-ha-sync-probe'").fetchall()
                        require(canceled == [dict(canceled=True)], 'SYNC_PROBE_CANCEL_REQUIRED')
                    process.wait(timeout=10)
                    raw = logfile.read_bytes()
                    require(b'NOTICE 01000' in raw, 'SYNC_CANCEL_WARNING_REQUIRED')
                    require(b'COMMIT_ACK' not in raw, 'CANCELED_SYNC_FALSE_ACK')
                    require(b'ReplicationAcknowledgementUncertain' in raw, 'SYNC_CANCEL_NOT_CLASSIFIED')
            finally:
                if process.poll() is None:
                    process.kill()
                process.wait(timeout=5)
                for index in standbys:
                    self.node_action(index, 'start')
        self.wait_cluster()
        after = read_snapshot(repository)
        self.assert_copies(after)
        refused(lambda: access.complete(proof, 'status'))
        return dict(commit_ack='WITHHELD', cancellation=cancel, ambiguous_outcome='RECONCILED_AS_COMMITTED_AFTER_REJOIN',
                    retry_consumed_proof='REFUSED', recovered_copies='ALL_THREE_EXACT')

    def assert_no_writer(self):
        for index in range(3):
            try:
                with self.connect(index, autocommit=True) as database:
                    require(database.execute('SELECT pg_is_in_recovery() AS recovery').fetchone()['recovery'],
                            'QUORUM_LOSS_WRITABLE_PRIMARY')
                    try:
                        database.execute('CREATE TABLE public.forbidden_quorum_write(value integer)')
                    except psycopg.errors.ReadOnlySqlTransaction:
                        pass
                    else:
                        raise ValueError('QUORUM_LOSS_ACCEPTED_WRITE')
            except psycopg.OperationalError:
                pass

    def __exit__(self, *_):
        errors = []
        for reservation in self.reservations:
            reservation.close()
        for index in range(3):
            try:
                if self.owned_node(index):
                    try:
                        raw = self.docker('logs', self.nodes[index], include_stderr=True, binary=True)
                        private_file(self.root / ('patroni' + str(index) + '.log'), raw)
                    finally:
                        self.node_action(index, 'rm', '--force', '--volumes')
            except Exception as error:
                errors.append(type(error).__name__)
        if self.etcd is not None:
            self.etcd.__exit__(None, None, None)
        require(not errors, 'OWNED_CLEANUP_FAILED_' + '_'.join(errors))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workdir', type=Path, required=True)
    parser.add_argument('--etcd', type=Path, required=True)
    parser.add_argument('--image', required=True)
    args = parser.parse_args()
    with ReplicationRehearsal(args.workdir, args.etcd, args.image) as rehearsal:
        receipt = rehearsal.run()
    receipt['owned_cleanup'] = 'PASS'
    private_file(args.workdir / 'receipt.json', json.dumps(receipt, indent=2).encode())
    print(json.dumps(receipt, sort_keys=True))


if __name__ == '__main__':
    def terminate(signum, frame):
        raise SystemExit(128 + signum)
    signal.signal(signal.SIGTERM, terminate)
    main()
