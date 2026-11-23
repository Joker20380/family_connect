"""Disposable notice DB recovery; no real publishers, token files or public feeds."""
import argparse
import hashlib
import json
from pathlib import Path
import secrets
import signal

from control.friends.access import Access
from control.friends import notices, support_ids
from control.friends.notices_postgres import PostgresNoticeTransaction, initialize_synthetic_notices
from control.friends.paid_postgres import initialize_synthetic_paid
from control.friends.support_postgres import initialize_synthetic_support
from device_identity.device import DeviceIdentity
from scripts.chat_postgres_rehearsal import refused_value
from scripts.control_ha_rehearsal import private_file, require
from scripts.enrollment_postgres_rehearsal import Rehearsal
from scripts.paid_postgres_rehearsal import PaidRehearsal, apply, snapshot, require_current_restore
from scripts.referral_postgres_rehearsal import NOW, proof, refused
from scripts.service_notices import REPOSITORY_PURPOSE

SQLITE_DDL = (
    'CREATE TABLE ha_notices_schema(version INTEGER PRIMARY KEY, purpose TEXT NOT NULL)',
    'CREATE TABLE admins(name TEXT PRIMARY KEY, digest TEXT NOT NULL, active INTEGER NOT NULL CHECK(active IN (0,1)))',
    'CREATE TABLE device_admins(device TEXT PRIMARY KEY, name TEXT NOT NULL, active INTEGER NOT NULL CHECK(active IN (0,1)))',
    'CREATE TABLE events(id TEXT PRIMARY KEY, value TEXT NOT NULL, position INTEGER NOT NULL UNIQUE CHECK(position>0))',
    'CREATE TABLE revisions(id TEXT PRIMARY KEY, value TEXT NOT NULL)',
    'CREATE TABLE edit_operations(id TEXT PRIMARY KEY, request TEXT NOT NULL, result TEXT NOT NULL, '
    'device TEXT NOT NULL, before_value TEXT NOT NULL, after_value TEXT NOT NULL)',
)


def initialize(access):
    if access.path is None:
        initialize_synthetic_notices(access.enrollment_repository)
        return
    with access.enrollment() as enrollment:
        database = enrollment.database
        for statement in SQLITE_DDL:
            database.execute(statement)
        database.execute('INSERT INTO ha_notices_schema VALUES (?,?)', (1, REPOSITORY_PURPOSE))
        for table in ('events', 'edit_operations'):
            for operation in ('UPDATE', 'DELETE'):
                database.execute('CREATE TRIGGER notice_' + operation.lower() + '_' + table +
                    ' BEFORE ' + operation + ' ON ' + table + " BEGIN SELECT RAISE(ABORT,'immutable notice history'); END")
        database.execute('CREATE TRIGGER notice_revision BEFORE UPDATE ON revisions WHEN NEW.id<>OLD.id OR '
            "json_extract(NEW.value,'$.revision') IS NOT json_extract(OLD.value,'$.revision')+1 OR "
            "json_extract(NEW.value,'$.updated') IS NULL OR json_extract(NEW.value,'$.updated')<json_extract(OLD.value,'$.updated') OR "
            "EXISTS (SELECT 1 FROM json_each(NEW.value) fresh WHERE fresh.key NOT IN ('title','body','revision','updated','editor') "
            'AND NOT EXISTS (SELECT 1 FROM json_each(OLD.value) prior WHERE prior.key=fresh.key AND prior.value=fresh.value)) OR '
            "EXISTS (SELECT 1 FROM json_each(OLD.value) prior WHERE prior.key NOT IN ('title','body','revision','updated','editor') "
            'AND NOT EXISTS (SELECT 1 FROM json_each(NEW.value) fresh WHERE prior.key=fresh.key AND prior.value=fresh.value)) '
            "BEGIN SELECT RAISE(ABORT,'invalid notice revision'); END")
        database.execute("CREATE TRIGGER notice_no_delete BEFORE DELETE ON revisions "
                         "BEGIN SELECT RAISE(ABORT,'retain notice revision'); END")


def notice(sequence=1, **changes):
    return dict(id=f'{sequence:032x}', kind='information', title='Synthetic notice',
                body='Synthetic body', platforms=['android'], days=1) | changes


def edit(sequence=1, revision=1, **changes):
    return dict(id=notice()['id'], request_id=f'{sequence:032x}', revision=revision,
                title='Synthetic correction', body='Corrected synthetic text') | changes


def request_value(access, device, action, **values):
    return dict(proof=proof(access, device, 'notices-' + action), **values)


class NoticesRehearsal(PaidRehearsal):
    CONTRACT_FILES = ('tests/test_enrollment_repository.py', 'tests/test_notices_repository.py')

    def notices_recovery(self):
        repository = self.repository()
        repository.initialize_synthetic()
        initialize_synthetic_paid(repository)
        initialize_synthetic_support(repository)
        access = Access(None, clock=lambda: NOW, enrollment_repository=repository)
        initialize(access)
        first, removed = [DeviceIdentity.generate() for index in range(2)]
        for device in (first, removed):
            access.complete(proof(access, device, 'activate', access.invite()), 'activate')
            notices.grant_device_repository(access, device.reference, 'Synthetic operator')
        support = support_ids.request(access, dict(proof=proof(access, first, 'support'), platform='android',
            app_version='0.1.18-beta126', version_code=126))['device_support_id']
        token = secrets.token_hex(32)
        with access.enrollment() as enrollment:
            apply(enrollment.paid(), support)
            enrollment.notices().grant_digest('Synthetic token', hashlib.sha256(token.encode()).hexdigest())
        notices.publish_repository(access, 'Bearer ' + token, notice(sequence=2))
        notices.device_request_repository(access, 'publish', request_value(access, first, 'publish', notice=notice()))
        old_backup = self.dump(repository, 'before-notice-edit-revoke.dump')
        consumed = request_value(access, first, 'edit', notice=edit())
        notices.device_request_repository(access, 'edit', consumed)
        pending = request_value(access, first, 'edit', notice=edit(sequence=2, revision=2))
        denied = request_value(access, removed, 'publish', notice=notice(sequence=3))
        with access.enrollment() as enrollment:
            enrollment.notices().revoke_device(removed.reference)
            enrollment.notices().revoke('Synthetic token')
        expected = [notices.feed_repository(access, version) for version in (1, 2)]
        committed = snapshot(repository)
        unfinished = repository.connect()
        try:
            repository.configure(unfinished)
            PostgresNoticeTransaction(unfinished).edit_device(first.reference, edit(sequence=2, revision=2), now=NOW)
            unfinished.execute('UPDATE device_admins SET active=1')
            unfinished.execute('UPDATE challenges SET used=1')
            require(self.owned(), 'REHEARSAL_CONTAINER_MISSING')
            self.docker('kill', '--signal', 'KILL', self.container)
        finally:
            unfinished.close()
        self.docker('start', self.container)
        self.refresh_port()
        repository.port = self.port
        self.wait_ready()
        require_current_restore(committed, snapshot(repository))
        backup = self.dump(repository, 'current-notices.dump')
        with Rehearsal(self.root / 'stale-restore') as target:
            stale = self.restore(target, repository, old_backup)
            refused_value(lambda: require_current_restore(committed, snapshot(stale)),
                          'RESTORE_WOULD_LOSE_OR_CHANGE_ACKNOWLEDGED_STATE')
        with Rehearsal(self.root / 'current-restore') as target:
            restored = self.restore(target, repository, backup)
            require_current_restore(committed, snapshot(restored))
            recovered = Access(None, clock=lambda: NOW, enrollment_repository=restored)
            require([notices.feed_repository(recovered, version) for version in (1, 2)] == expected, 'NOTICE_FEEDS_CHANGED')
            refused(lambda: notices.device_request_repository(recovered, 'edit', consumed))
            for attempt in (lambda: notices.device_request_repository(recovered, 'publish', denied),
                            lambda: notices.publish_repository(recovered, 'Bearer ' + token, notice(sequence=3))):
                try:
                    attempt()
                except notices.NoticeDenied:
                    pass
                else:
                    raise ValueError('RESTORED_PUBLISHER_REVOKE_LOST')
            with recovered.enrollment() as enrollment:
                require(apply(enrollment.paid(), support)['duplicate'], 'PAYMENT_REPLAYED')
            import psycopg
            for table in ('events', 'edit_operations', 'revisions'):
                for query in ('UPDATE ' + table + ' SET id=id', 'TRUNCATE ' + table):
                    try:
                        with recovered.enrollment() as enrollment:
                            enrollment.database.execute(query)
                    except psycopg.errors.CheckViolation:
                        pass
                    else:
                        raise ValueError('RESTORED_NOTICE_GUARD_MISSING')
            require_current_restore(committed, snapshot(restored))
            response = notices.device_request_repository(recovered, 'edit', pending)
            refused(lambda: notices.device_request_repository(recovered, 'edit', pending))
            require(notices.device_request_repository(recovered, 'edit',
                request_value(recovered, first, 'edit', notice=edit(sequence=2, revision=2))) == response, 'EDIT_REPLAYED')
            require(notices.feed_repository(recovered)['events'] == expected[0]['events'], 'LEGACY_FEED_MUTATED')
            require(len(snapshot(restored)['edit_operations']) == 2, 'EDIT_HISTORY_LOST')
            recovered.clock = lambda: NOW + 86400
            require(notices.feed_repository(recovered, 2)['events'] == [], 'NOTICE_EXPIRY_FAILED')
        return {table: len(records) for table, records in committed.items()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workdir', required=True, type=Path)
    args = parser.parse_args()
    with NoticesRehearsal(args.workdir) as rehearsal:
        tests = rehearsal.contracts()
        restored = rehearsal.notices_recovery()
        result = dict(schema=1, result='ISOLATED_NOTICES_POSTGRES_PASS', contracts=tests,
            postgres=rehearsal.manifest['version'], synthetic_only=True, crash_recovery='PASS',
            current_restore='EXACT_ALL_LAB_TABLES', stale_restore='REFUSED', restored_rows=restored,
            production_writes=0, file_publication='NOT_IMPLEMENTED', cross_database_import='NOT_IMPLEMENTED',
            replication='NOT_IMPLEMENTED', reverse_migration='NOT_IMPLEMENTED',
            identity_keys_and_token='EPHEMERAL_RETAINED_NOT_RESTORED')
    result['owned_container_cleanup'] = 'PASS'
    private_file(args.workdir / 'receipt.json', json.dumps(result, indent=2).encode())
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    def terminate(signum, frame):
        raise SystemExit(128 + signum)

    signal.signal(signal.SIGTERM, terminate)
    main()
