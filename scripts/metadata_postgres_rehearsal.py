"""Disposable consent-floor recovery; never reads product metadata or client IPs."""
import argparse
import hashlib
import json
from pathlib import Path
import signal

from control.friends.access import Access
from control.friends import technical_metadata as metadata
from control.friends import support_ids
from control.friends.metadata_postgres import initialize_synthetic_metadata
from control.friends.paid_postgres import initialize_synthetic_paid
from control.friends.support_postgres import initialize_synthetic_support
from device_identity.device import DeviceIdentity
from scripts.chat_postgres_rehearsal import refused_value
from scripts.control_ha_rehearsal import private_file, require
from scripts.enrollment_postgres_rehearsal import Rehearsal
from scripts.paid_postgres_rehearsal import PaidRehearsal, apply, snapshot, require_current_restore
from scripts.referral_postgres_rehearsal import NOW, proof, refused

SQLITE_DDL = (
    'CREATE TABLE ha_metadata_schema(version INTEGER PRIMARY KEY, purpose TEXT NOT NULL)',
    'CREATE TABLE device_metadata(device TEXT PRIMARY KEY, '
    'epoch INTEGER NOT NULL CHECK(epoch>0 AND epoch<9007199254740992), '
    'sequence INTEGER NOT NULL CHECK(sequence>0 AND sequence<9007199254740992), '
    'digest TEXT NOT NULL, enabled INTEGER NOT NULL CHECK(enabled IN (0,1)), '
    'received INTEGER NOT NULL, payload TEXT NOT NULL CHECK(enabled=1 OR payload=\'{}\'))',
)


def initialize(access):
    if access.path is None:
        initialize_synthetic_metadata(access.enrollment_repository)
        return
    with access.enrollment() as enrollment:
        database = enrollment.database
        for statement in SQLITE_DDL:
            database.execute(statement)
        database.execute('INSERT INTO ha_metadata_schema VALUES (?,?)', (1, metadata.REPOSITORY_PURPOSE))
        database.execute('CREATE TRIGGER metadata_monotonic BEFORE UPDATE ON device_metadata '
            'WHEN NEW.device<>OLD.device OR NEW.epoch<OLD.epoch OR (NEW.epoch=OLD.epoch AND '
            '(NEW.sequence<OLD.sequence OR (OLD.enabled=0 AND NEW.enabled=1))) '
            "BEGIN SELECT RAISE(ABORT,'consent regression'); END")
        database.execute('CREATE TRIGGER metadata_version BEFORE UPDATE ON device_metadata '
            'WHEN NEW.epoch=OLD.epoch AND NEW.sequence=OLD.sequence AND '
            '(NEW.digest<>OLD.digest OR NEW.enabled<>OLD.enabled OR NEW.received<>OLD.received OR '
            'EXISTS (SELECT 1 FROM json_each(NEW.payload) fresh WHERE NOT EXISTS '
            '(SELECT 1 FROM json_each(OLD.payload) prior WHERE fresh.key=prior.key AND fresh.value=prior.value))) '
            "BEGIN SELECT RAISE(ABORT,'immutable metadata version'); END")
        database.execute('CREATE TRIGGER metadata_no_delete BEFORE DELETE ON device_metadata '
            "BEGIN SELECT RAISE(ABORT,'retain consent floor'); END")


def report(epoch=1, sequence=1, operation='sample', now=NOW):
    observations = {}
    if operation == 'sample':
        for group, fields in metadata.FIELDS.items():
            values = {field: None for field in fields}
            if group == 'mobile':
                values.update(sim_reason='not_observed', registered_reason='not_observed', radio_reason='not_observed')
            if group == 'profile':
                values.update(model='Synthetic device', android_version='15', version_code=126)
            observations[group] = dict(sampled_at_ms=now * 1000, age_ms=0,
                source=sorted(metadata.SOURCES[group])[0], status='unavailable', reason='not_observed', values=values)
    return dict(schema=1, report_id=f'{epoch:016x}{sequence:016x}', consent_epoch=epoch,
                sequence=sequence, operation=operation, observations=observations)


def request_value(access, device, value):
    raw = json.dumps(value, ensure_ascii=False, separators=(',', ':'))
    purpose = 'technical-metadata-v1:' + hashlib.sha256(raw.encode()).hexdigest()
    return dict(report=raw, proof=proof(access, device, purpose))


class MetadataRehearsal(PaidRehearsal):
    CONTRACT_FILES = ('tests/test_enrollment_repository.py', 'tests/test_metadata_repository.py')

    def metadata_recovery(self):
        repository = self.repository()
        repository.initialize_synthetic()
        initialize_synthetic_paid(repository)
        initialize_synthetic_support(repository)
        access = Access(None, clock=lambda: NOW, enrollment_repository=repository)
        initialize(access)
        first, withdrawn, revoked_device = [DeviceIdentity.generate() for index in range(3)]
        for device in (first, withdrawn, revoked_device):
            access.complete(proof(access, device, 'activate', access.invite()), 'activate')
        support = support_ids.request(access, dict(proof=proof(access, first, 'support'), platform='android',
            app_version='0.1.18-beta126', version_code=126))['device_support_id']
        with access.enrollment() as enrollment:
            apply(enrollment.paid(), support)
        consumed = request_value(access, first, report())
        metadata.request_repository(access, consumed)
        metadata.request_repository(access, request_value(access, withdrawn, report()))
        old_backup = self.dump(repository, 'before-consent-revoke.dump')
        metadata.request_repository(access, request_value(access, withdrawn, report(epoch=2, operation='revoke')))
        denied = request_value(access, revoked_device, report())
        access.revoke_device(revoked_device.reference)
        pending_report = report(sequence=2, now=NOW + 60)
        pending = request_value(access, first, pending_report)
        expected = metadata.read_repository(access)
        committed = snapshot(repository)
        unfinished = repository.connect()
        try:
            repository.configure(unfinished)
            unfinished.execute("UPDATE device_metadata SET payload='{}' WHERE enabled=1")
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
        backup = self.dump(repository, 'current-metadata.dump')
        with Rehearsal(self.root / 'stale-restore') as target:
            stale = self.restore(target, repository, old_backup)
            refused_value(lambda: require_current_restore(committed, snapshot(stale)),
                          'RESTORE_WOULD_LOSE_OR_CHANGE_ACKNOWLEDGED_STATE')
        with Rehearsal(self.root / 'current-restore') as target:
            restored = self.restore(target, repository, backup)
            require_current_restore(committed, snapshot(restored))
            recovered = Access(None, clock=lambda: NOW, enrollment_repository=restored)
            require(metadata.read_repository(recovered) == expected, 'RESTORED_METADATA_CHANGED')
            refused(lambda: metadata.request_repository(recovered, consumed))
            refused(lambda: metadata.request_repository(recovered, denied))
            with recovered.enrollment() as enrollment:
                require(apply(enrollment.paid(), support)['duplicate'], 'PAYMENT_REPLAYED')
            import psycopg
            for query in ('DELETE FROM device_metadata', 'TRUNCATE device_metadata',
                          'UPDATE device_metadata SET enabled=1 WHERE enabled=0'):
                try:
                    with recovered.enrollment() as enrollment:
                        enrollment.database.execute(query)
                except psycopg.errors.CheckViolation:
                    pass
                else:
                    raise ValueError('RESTORED_CONSENT_FLOOR_MISSING')
            require_current_restore(committed, snapshot(restored))
            recovered.clock = lambda: NOW + 60
            response = metadata.request_repository(recovered, pending)
            refused(lambda: metadata.request_repository(recovered, pending))
            recovered.clock = lambda: NOW + 60 + metadata.RETENTION
            metadata.prune_repository(recovered)
            require(all(not row['observations'] for row in metadata.read_repository(recovered)), 'RETENTION_FAILED')
            require(metadata.request_repository(recovered, request_value(recovered, first, pending_report)) == response,
                    'OLD_REPORT_REFRESHED')
            for delayed in (report(), report(epoch=2, sequence=2)):
                value = request_value(recovered, withdrawn, delayed)
                before = snapshot(restored)
                refused(lambda: metadata.request_repository(recovered, value))
                require_current_restore(before, snapshot(restored))
            values = metadata.read_repository(recovered)
            require(next(row for row in values if row['device'] == withdrawn.reference)['consent'] == 'revoked',
                    'CONSENT_RESURRECTED')
            renewed = request_value(recovered, withdrawn, report(epoch=3, now=int(recovered.clock())))
            require(metadata.request_repository(recovered, renewed)['consent'] == 'enabled', 'NEW_CONSENT_REFUSED')
        return {table: len(records) for table, records in committed.items()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workdir', required=True, type=Path)
    args = parser.parse_args()
    with MetadataRehearsal(args.workdir) as rehearsal:
        tests = rehearsal.contracts()
        restored = rehearsal.metadata_recovery()
        result = dict(schema=1, result='ISOLATED_METADATA_POSTGRES_PASS', contracts=tests,
            postgres=rehearsal.manifest['version'], synthetic_only=True, crash_recovery='PASS',
            current_restore='EXACT_ALL_LAB_TABLES', stale_restore='REFUSED', restored_rows=restored,
            consent_tombstone='PRESERVED', expired_replay='NO_REFRESH', pending_proof='CONSUMED_ONCE',
            production_writes=0, physical_erasure='NOT_QUALIFIED', cross_database_import='NOT_IMPLEMENTED',
            replication='NOT_IMPLEMENTED', reverse_migration='NOT_IMPLEMENTED', identity_keys='EPHEMERAL_RETAINED_NOT_RESTORED')
    result['owned_container_cleanup'] = 'PASS'
    private_file(args.workdir / 'receipt.json', json.dumps(result, indent=2).encode())
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    def terminate(signum, frame):
        raise SystemExit(128 + signum)

    signal.signal(signal.SIGTERM, terminate)
    main()
