"""Owned disposable PostgreSQL container; synthetic enrollment contracts and crash recovery."""
import argparse
import json
import os
from pathlib import Path
import re
import secrets
import signal
import subprocess
import sys
import tempfile
import time
import uuid

from control.friends.access import Access, Rejected
from control.friends.enrollment_postgres import PostgresEnrollment
from device_identity.device import DeviceIdentity
from scripts.control_ha_rehearsal import private_file, require

ROOT = Path(__file__).resolve().parents[1]
LABEL = 'family-connect.ha-enrollment-rehearsal'


class Rehearsal:
    def __init__(self, root):
        self.root = Path(root)
        require(not any(parent.is_symlink() for parent in (self.root, *self.root.parents)), 'REHEARSAL_SYMLINK')
        require(self.root.resolve().is_relative_to(Path(tempfile.gettempdir()).resolve()), 'TEMPORARY_REHEARSAL_ONLY')
        self.manifest = json.loads((ROOT / 'deploy/control-ha/rehearsal-postgres.json').read_text())
        require(re.fullmatch(r'postgres@sha256:[0-9a-f]{64}', self.manifest['image']), 'POSTGRES_PIN_REQUIRED')
        self.root.mkdir(mode=0o700)
        self.token = uuid.uuid4().hex
        self.container = None
        self.password = secrets.token_hex(32)
        self.password_file = self.root / 'password'
        self.environment = {key: value for key, value in os.environ.items()
                            if not key.startswith(('PG', 'FC_HA_', 'DOCKER_'))}

    def docker(self, *arguments, timeout=30, include_stderr=False, binary=False, input_data=None):
        result = subprocess.run(['docker', '--host', 'unix:///var/run/docker.sock', *arguments], capture_output=True, input=input_data,
                                timeout=timeout, env=self.environment)
        if result.returncode:
            private_file(self.root / ('docker-error-' + uuid.uuid4().hex + '.log'), result.stderr)
            raise RuntimeError('Rehearsal Docker command failed; private evidence retained')
        output = result.stdout + (result.stderr if include_stderr else b'')
        return output if binary else output.decode().strip()

    def owned(self):
        if self.container is None:
            cidfile = self.root / 'container.id'
            if not cidfile.exists():
                return False
            self.container = cidfile.read_text().strip()
        require(re.fullmatch('[0-9a-f]{64}', self.container), 'INVALID_REHEARSAL_CONTAINER')
        label = self.docker('inspect', '--format', '{{index .Config.Labels "' + LABEL + '"}}', self.container)
        require(label == self.token, 'REHEARSAL_CONTAINER_OWNERSHIP')
        return True

    def __enter__(self):
        try:
            from importlib.metadata import version
            require(all(version(package) == '3.3.9' for package in ('psycopg', 'psycopg-binary')),
                    'POSTGRES_DRIVER_PIN_MISMATCH')
            private_file(self.password_file, self.password.encode())
            private_file(self.root / 'container.env', ('POSTGRES_DB=fc_ha_synthetic\nPOSTGRES_USER=fc_ha_synthetic\n'
                'POSTGRES_PASSWORD=' + self.password + '\nPOSTGRES_INITDB_ARGS=--auth-host=scram-sha-256\n').encode())
            self.container = self.docker('run', '--detach', '--pull=never', '--name', 'fc-ha-enrollment-' + self.token,
                '--label', LABEL + '=' + self.token, '--cidfile', str(self.root / 'container.id'),
                '--memory', '512m', '--cpus', '1', '--publish', '127.0.0.1::5432',
                '--env-file', str(self.root / 'container.env'), self.manifest['image'],
                'postgres', '-c', 'fsync=on', '-c', 'full_page_writes=on', '-c', 'synchronous_commit=on',
                '-c', 'max_connections=40', '-c', 'log_statement=none')
            self.refresh_port()
            self.wait_ready()
            return self
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def refresh_port(self):
        self.port = int(self.docker('inspect', '--format',
            '{{(index (index .NetworkSettings.Ports "5432/tcp") 0).HostPort}}', self.container))

    def repository(self):
        return PostgresEnrollment(port=self.port, schema='ha_enrollment_' + uuid.uuid4().hex, password=self.password)

    def wait_ready(self):
        import psycopg
        deadline = time.monotonic() + 30
        while True:
            try:
                with self.repository().connect() as database:
                    version = database.execute('SHOW server_version').fetchone()['server_version'].split()[0]
                    require(version == self.manifest['version'], 'POSTGRES_VERSION_MISMATCH')
                    for setting in ('fsync', 'full_page_writes', 'synchronous_commit'):
                        require(database.execute('SHOW ' + setting).fetchone()[setting] == 'on', 'DURABILITY_DISABLED')
                return
            except psycopg.OperationalError:
                if time.monotonic() >= deadline:
                    raise RuntimeError('PostgreSQL rehearsal did not become ready') from None
                time.sleep(0.2)

    def contracts(self):
        environment = self.environment | {'FC_HA_PG_PORT': str(self.port),
            'FC_HA_PG_PASSWORD_FILE': str(self.password_file)}
        result = subprocess.run([sys.executable, '-m', 'pytest', '-q', '-ra',
            'tests/test_enrollment_repository.py', '--junitxml=' + str(self.root / 'contracts.xml')],
            cwd=ROOT, env=environment, capture_output=True, timeout=120)
        private_file(self.root / 'contracts.log', result.stdout + result.stderr)
        require(result.returncode == 0, 'ENROLLMENT_CONTRACTS_FAILED')
        from xml.etree import ElementTree
        suites = ElementTree.parse(self.root / 'contracts.xml').getroot().findall('testsuite')
        require(suites and all(int(suite.get('skipped', '0')) == 0 for suite in suites), 'CONTRACTS_SKIPPED')
        return sum(int(suite.attrib['tests']) for suite in suites)

    def crash_recovery(self):
        repository = self.repository()
        repository.initialize_synthetic()
        access = Access(None, clock=lambda: 1000, enrollment_repository=repository)
        device = DeviceIdentity.generate()
        challenge = access.challenge(device.public_identity, device.wireguard_public_key, 'activate', access.invite())
        proof = device.prove_transport_key(challenge['challenge'])
        record = access.complete(proof, 'activate')
        unused = access.invite()
        revoked_device = DeviceIdentity.generate()
        revoke_challenge = access.challenge(revoked_device.public_identity, revoked_device.wireguard_public_key,
            'activate', access.invite())
        access.complete(revoked_device.prove_transport_key(revoke_challenge['challenge']), 'activate')
        access.revoke_device(revoked_device.reference)
        with access.enrollment() as transaction:
            transaction.database.execute('INSERT INTO field_support_audit(timestamp,support_id,previous_state,new_state,outcome) '
                'VALUES (%s,%s,%s,%s,%s)', (1000, transaction.registered(device.reference), 0, 1, 'synthetic-only'))
        unfinished = repository.connect()
        try:
            repository.configure(unfinished)
            unfinished.execute('INSERT INTO invites(hash) VALUES (%s)', ('uncommitted-synthetic',))
            require(self.owned(), 'REHEARSAL_CONTAINER_MISSING')
            self.docker('kill', '--signal', 'KILL', self.container)
        finally:
            unfinished.close()
        self.docker('start', self.container)
        self.refresh_port()
        repository.port = self.port
        self.wait_ready()
        try:
            access.complete(proof, 'activate')
        except Rejected:
            pass
        else:
            raise RuntimeError('Consumed proof replayed after crash')
        with access.enrollment() as transaction:
            require(transaction.invitation('uncommitted-synthetic') is None, 'UNCOMMITTED_WRITE_SURVIVED')
            require(transaction.invitation(access.code_hash(unused))['device'] is None, 'COMMITTED_INVITATION_LOST')
            require(transaction.device(device.reference)['tcp'] == record['tcp_id'], 'COMMITTED_IDENTITY_LOST')
            require(transaction.device(revoked_device.reference)['revoked'] == 1, 'COMMITTED_REVOCATION_LOST')
        fresh = access.challenge(device.public_identity, device.wireguard_public_key, 'nl')
        require(access.complete(device.prove_transport_key(fresh['challenge']), 'nl') == record, 'RECONNECT_CHANGED_IDENTITY')
        return repository

    @staticmethod
    def snapshot(repository):
        from psycopg import sql
        tables = ('invites', 'devices', 'challenges', 'device_support', 'field_support_audit')
        with repository.transaction() as transaction:
            return {table: transaction.database.execute(sql.SQL('SELECT * FROM {} ORDER BY 1').format(
                sql.Identifier(table))).fetchall() for table in tables}

    def backup_restore(self, repository):
        before = self.snapshot(repository)
        require(all(before.values()), 'BACKUP_REQUIRES_NONEMPTY_TABLES')
        backup = self.docker('exec', self.container, 'pg_dump', '--username=fc_ha_synthetic',
            '--dbname=fc_ha_synthetic', '--format=custom', '--no-owner', '--no-acl',
            '--schema=' + repository.schema, binary=True)
        private_file(self.root / 'enrollment.dump', backup)
        with Rehearsal(self.root / 'restore') as restored:
            restored.docker('exec', '-i', restored.container, 'pg_restore', '--username=fc_ha_synthetic',
                '--dbname=fc_ha_synthetic', '--no-owner', '--no-acl', '--exit-on-error', '--single-transaction',
                input_data=backup)
            recovered = PostgresEnrollment(port=restored.port, schema=repository.schema, password=restored.password)
            require(self.snapshot(recovered) == before, 'ISOLATED_RESTORE_ROWS_DIFFER')
            with recovered.transaction() as transaction:
                appended = transaction.database.execute('INSERT INTO field_support_audit(timestamp,support_id,previous_state,new_state,outcome) '
                    'VALUES (%s,%s,%s,%s,%s) RETURNING id', (1001, before['device_support'][0]['support_id'], 1, 0, 'synthetic-only')).fetchone()
                require(appended['id'] > max(row['id'] for row in before['field_support_audit']), 'RESTORED_SEQUENCE_REGRESSED')
        return {table: len(rows) for table, rows in before.items()}

    def __exit__(self, *exception):
        if self.owned():
            try:
                private_file(self.root / 'postgres.log', self.docker('logs', self.container, include_stderr=True).encode())
            finally:
                self.docker('rm', '--force', '--volumes', self.container)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workdir', required=True, type=Path)
    args = parser.parse_args()
    with Rehearsal(args.workdir) as rehearsal:
        tests = rehearsal.contracts()
        repository = rehearsal.crash_recovery()
        restored_rows = rehearsal.backup_restore(repository)
        receipt = dict(schema=1, result='ISOLATED_ENROLLMENT_POSTGRES_PASS', contracts=tests,
            postgres=rehearsal.manifest['version'], driver='psycopg3.3.9', synthetic_only=True,
            crash_recovery='PASS', uncommitted_write='ROLLED_BACK', replay='REFUSED',
            production_writes=0, replication='NOT_IMPLEMENTED', canonical_migration='INCOMPLETE')
        receipt.update(isolated_backup_restore='PASS', restored_enrollment_rows=restored_rows)
    receipt['owned_container_cleanup'] = 'PASS'
    private_file(args.workdir / 'receipt.json', json.dumps(receipt, indent=2).encode())
    print(json.dumps(receipt, sort_keys=True))


if __name__ == '__main__':
    def terminate(signum, frame):
        raise SystemExit(128 + signum)

    signal.signal(signal.SIGTERM, terminate)
    main()
