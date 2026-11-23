"""Disposable support snapshot recovery; never reads live reports or raw logs."""
import argparse
import hashlib
import json
from pathlib import Path
import signal

from control.friends.access import Access
from control.friends import diagnostics, support_ids
from control.friends.diagnostics_postgres import initialize_synthetic_diagnostics
from control.friends.paid_postgres import initialize_synthetic_paid
from control.friends.support_postgres import initialize_synthetic_support
from device_identity.device import DeviceIdentity
from scripts.chat_postgres_rehearsal import refused_value
from scripts.control_ha_rehearsal import private_file, require
from scripts.enrollment_postgres_rehearsal import Rehearsal
from scripts.paid_postgres_rehearsal import PaidRehearsal, apply, snapshot, require_current_restore
from scripts.referral_postgres_rehearsal import NOW, proof, refused

SQLITE_DDL = (
    'CREATE TABLE ha_diagnostics_schema(version INTEGER PRIMARY KEY, purpose TEXT NOT NULL)',
    'CREATE TABLE snapshots(device TEXT PRIMARY KEY, support TEXT NOT NULL, '
    'received INTEGER NOT NULL, report TEXT NOT NULL)',
)


def initialize(access):
    if access.path is None:
        initialize_synthetic_diagnostics(access.enrollment_repository)
        return
    with access.enrollment() as enrollment:
        for statement in SQLITE_DDL:
            enrollment.database.execute(statement)
        enrollment.database.execute('INSERT INTO ha_diagnostics_schema VALUES (?,?)', (1, diagnostics.REPOSITORY_PURPOSE))


def report(sequence=1, now=NOW, **changes):
    return dict(schema=1, report_id=f'{sequence:032x}', platform='android', version_code=126,
        sampled_at_ms=now * 1000, consent=True, metrics=dict(state='CONNECTED', protocol_errors=0)) | changes


def request_value(access, device, value):
    raw = json.dumps(value, separators=(',', ':'))
    return dict(report=raw, proof=proof(access, device, 'diagnostics:' + hashlib.sha256(raw.encode()).hexdigest()))


class DiagnosticsRehearsal(PaidRehearsal):
    CONTRACT_FILES = ('tests/test_enrollment_repository.py', 'tests/test_diagnostics_repository.py')

    def diagnostics_recovery(self):
        repository = self.repository()
        repository.initialize_synthetic()
        initialize_synthetic_paid(repository)
        initialize_synthetic_support(repository)
        access = Access(None, clock=lambda: NOW, enrollment_repository=repository)
        initialize(access)
        first, expired, revoked_device = [DeviceIdentity.generate() for index in range(3)]
        for device in (first, expired, revoked_device):
            access.complete(proof(access, device, 'activate', access.invite()), 'activate')
        support = support_ids.request(access, dict(proof=proof(access, first, 'support'), platform='android',
            app_version='0.1.18-beta126', version_code=126))['device_support_id']
        with access.enrollment() as enrollment:
            apply(enrollment.paid(), support)
            expired_support = enrollment.registered(expired.reference)
        diagnostics.request_repository(access, request_value(access, first, report()))
        diagnostics.request_repository(access, request_value(access, expired, report()))
        old_backup = self.dump(repository, 'before-prune-revoke.dump')
        access.clock = lambda: NOW + 60
        consumed = request_value(access, first, report(sequence=2, now=NOW + 60))
        diagnostics.request_repository(access, consumed)
        restored_time = NOW + diagnostics.RETENTION + 1
        access.clock = lambda: restored_time
        diagnostics.prune_repository(access)
        require(diagnostics.read_repository(access, expired_support) is None, 'EXPIRED_REPORT_RETAINED')
        consumed = request_value(access, first, report(sequence=2, now=NOW + 60))
        diagnostics.request_repository(access, consumed)
        denied = request_value(access, revoked_device, report(now=restored_time))
        access.revoke_device(revoked_device.reference)
        pending_report = report(sequence=3, now=restored_time)
        pending = request_value(access, first, pending_report)
        expected = diagnostics.read_repository(access, support)
        require(expected is not None, 'CURRENT_REPORT_MISSING')
        committed = snapshot(repository)
        require(any(row['used'] for row in committed['challenges']), 'CONSUMED_PROOF_NOT_RETAINED')
        unfinished = repository.connect()
        try:
            repository.configure(unfinished)
            unfinished.execute('DELETE FROM snapshots')
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
        backup = self.dump(repository, 'current-diagnostics.dump')
        with Rehearsal(self.root / 'stale-restore') as target:
            stale = self.restore(target, repository, old_backup)
            refused_value(lambda: require_current_restore(committed, snapshot(stale)),
                          'RESTORE_WOULD_LOSE_OR_CHANGE_ACKNOWLEDGED_STATE')
        with Rehearsal(self.root / 'current-restore') as target:
            restored = self.restore(target, repository, backup)
            require_current_restore(committed, snapshot(restored))
            recovered = Access(None, clock=lambda: restored_time, enrollment_repository=restored)
            require(diagnostics.read_repository(recovered, support) == expected, 'RESTORED_REPORT_CHANGED')
            require(diagnostics.read_repository(recovered, expired_support) is None, 'EXPIRED_REPORT_RESURRECTED')
            refused(lambda: diagnostics.request_repository(recovered, consumed))
            refused(lambda: diagnostics.request_repository(recovered, denied))
            with recovered.enrollment() as enrollment:
                require(apply(enrollment.paid(), support)['duplicate'], 'PAYMENT_REPLAYED')
            require_current_restore(committed, snapshot(restored))
            response = diagnostics.request_repository(recovered, pending)
            refused(lambda: diagnostics.request_repository(recovered, pending))
            recovered.clock = lambda: restored_time + 10
            require(diagnostics.request_repository(recovered, request_value(recovered, first, pending_report)) == response,
                    'DUPLICATE_REFRESHED_REPORT')
            recovered.clock = lambda: restored_time + diagnostics.RETENTION
            require(diagnostics.read_repository(recovered, support) is not None, 'TTL_BOUNDARY_CHANGED')
            recovered.clock = lambda: restored_time + diagnostics.RETENTION + 1
            require(diagnostics.read_repository(recovered, support) is None, 'EXPIRED_REPORT_VISIBLE')
            diagnostics.prune_repository(recovered)
            require(snapshot(restored)['snapshots'] == [], 'RETENTION_FAILED')
        return {table: len(records) for table, records in committed.items()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workdir', required=True, type=Path)
    args = parser.parse_args()
    with DiagnosticsRehearsal(args.workdir) as rehearsal:
        tests = rehearsal.contracts()
        restored = rehearsal.diagnostics_recovery()
        result = dict(schema=1, result='ISOLATED_DIAGNOSTICS_POSTGRES_PASS', contracts=tests,
            postgres=rehearsal.manifest['version'], synthetic_only=True, crash_recovery='PASS',
            current_restore='EXACT_ALL_LAB_TABLES', stale_restore='REFUSED', restored_rows=restored,
            duplicate_within_retention='NO_REFRESH', expired_rows='NOT_RESTORED_FROM_CURRENT_BACKUP',
            pending_proof='CONSUMED_ONCE', production_writes=0, physical_erasure='NOT_QUALIFIED',
            cross_database_import='NOT_IMPLEMENTED', replication='NOT_IMPLEMENTED',
            reverse_migration='NOT_IMPLEMENTED', identity_keys='EPHEMERAL_RETAINED_NOT_RESTORED')
    result['owned_container_cleanup'] = 'PASS'
    private_file(args.workdir / 'receipt.json', json.dumps(result, indent=2).encode())
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    def terminate(signum, frame):
        raise SystemExit(128 + signum)

    signal.signal(signal.SIGTERM, terminate)
    main()
