"""Disposable grant/audit durability rehearsal; never publishes FIELD or CRL files."""
import argparse
import json
from pathlib import Path
import signal

from control.friends import support_ids
from control.friends.access import Access
from control.friends.paid_postgres import initialize_synthetic_paid
from control.friends.restricted_admin import grant
from control.friends.restricted_admin_postgres import initialize_synthetic_restricted_admin
from control.friends.support_postgres import initialize_synthetic_support
from device_identity.device import DeviceIdentity
from scripts.control_ha_rehearsal import private_file, require
from scripts.enrollment_postgres_rehearsal import Rehearsal
from scripts.paid_postgres_rehearsal import PaidRehearsal, apply, snapshot, require_current_restore
from scripts.referral_postgres_rehearsal import NOW, proof, refused


class RestrictedAdminRehearsal(PaidRehearsal):
    CONTRACT_FILES = ('tests/test_enrollment_repository.py', 'tests/test_support_repository.py',
                      'tests/test_restricted_admin_repository.py')

    def admin_recovery(self):
        repository = self.repository()
        repository.initialize_synthetic()
        initialize_synthetic_restricted_admin(repository)
        initialize_synthetic_support(repository)
        initialize_synthetic_paid(repository)
        access = Access(None, clock=lambda: NOW, enrollment_repository=repository)
        device, revoked = DeviceIdentity.generate(), DeviceIdentity.generate()
        for identity in (device, revoked):
            access.complete(proof(access, identity, 'activate', access.invite()), 'activate')
            grant(access, identity.reference, 'synthetic-family', NOW + 3600, 3)
        with repository.transaction() as transaction:
            support = transaction.registered(device.reference)
            other_support = transaction.registered(revoked.reference)
        consumed = dict(proof=proof(access, device, 'support'), platform='android', app_version='0.1.18-beta126', version_code=126)
        response = support_ids.request(access, consumed)
        with repository.transaction() as transaction:
            apply(transaction.paid(), support)
        old_backup = self.dump(repository, 'before-admin-revoke.dump')
        pending = consumed | dict(proof=proof(access, device, 'support'))
        with repository.transaction() as transaction:
            admin = transaction.restricted_admin()
            audit_id = admin.begin_audit(NOW, support, 1, 0)
            admin.revoke_grant(device.reference)
            admin.finish_audit(audit_id, 'APPLIED')
            unfinished_audit = admin.begin_audit(NOW, other_support, 1, 0)
            admin.revoke_grant(revoked.reference)
        access.revoke_device(revoked.reference)
        committed = snapshot(repository)
        unfinished = repository.connect()
        try:
            repository.configure(unfinished)
            unfinished.execute('UPDATE restricted_grants SET revoked=0,revision=revision+1')
            unfinished.execute("UPDATE field_support_audit SET outcome='INCOMPLETE'")
            unfinished.execute('UPDATE challenges SET used=1 WHERE used=0')
            require(self.owned(), 'REHEARSAL_CONTAINER_MISSING')
            self.docker('kill', '--signal', 'KILL', self.container)
        finally:
            unfinished.close()
        self.docker('start', self.container)
        self.refresh_port()
        repository.port = self.port
        self.wait_ready()
        require_current_restore(committed, snapshot(repository))
        backup = self.dump(repository, 'current-admin.dump')
        with Rehearsal(self.root / 'stale-restore') as target:
            stale = self.restore(target, repository, old_backup)
            try:
                require_current_restore(committed, snapshot(stale))
            except ValueError as error:
                require(str(error) == 'RESTORE_WOULD_LOSE_OR_CHANGE_ACKNOWLEDGED_STATE', 'UNEXPECTED_RESTORE_ERROR')
            else:
                raise RuntimeError('Stale admin restore accepted')
        with Rehearsal(self.root / 'current-restore') as target:
            restored = self.restore(target, repository, backup)
            require_current_restore(committed, snapshot(restored))
            recovered = Access(None, clock=lambda: NOW, enrollment_repository=restored)
            refused(lambda: support_ids.request(recovered, consumed))
            with restored.transaction() as transaction:
                admin = transaction.restricted_admin()
                require(admin.grant_row(device.reference)['revoked'] == 1, 'RESTORED_REVOKE_LOST')
                require(admin.grant_row(device.reference)['revision'] == 4, 'RESTORED_REVISION_CHANGED')
                require(apply(transaction.paid(), support)['duplicate'], 'RESTORED_PAYMENT_REPLAYED')
            try:
                grant(recovered, revoked.reference, 'synthetic-family', NOW + 3600)
            except ValueError:
                pass
            else:
                raise RuntimeError('Revoked registration granted')
            require_current_restore(committed, snapshot(restored))
            require(support_ids.request(recovered, pending) == response, 'RESTORED_PENDING_PROOF_CHANGED')
            refused(lambda: support_ids.request(recovered, pending))
            with restored.transaction() as transaction:
                admin = transaction.restricted_admin()
                admin.finish_audit(unfinished_audit, 'INCOMPLETE')
                appended = admin.begin_audit(NOW + 1, support, 0, 0)
                require(appended > max(row['id'] for row in committed['field_support_audit']), 'RESTORED_SEQUENCE_REGRESSED')
                admin.finish_audit(appended, 'APPLIED')
                require(admin.grant_row(revoked.reference)['revoked'] == 1, 'RECOVERY_REOPENED_GRANT')
        return {table: len(records) for table, records in committed.items()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workdir', required=True, type=Path)
    args = parser.parse_args()
    with RestrictedAdminRehearsal(args.workdir) as rehearsal:
        tests = rehearsal.contracts()
        restored = rehearsal.admin_recovery()
        receipt = dict(schema=1, result='ISOLATED_RESTRICTED_ADMIN_POSTGRES_PASS', contracts=tests,
            postgres=rehearsal.manifest['version'], driver='psycopg3.3.9', synthetic_only=True,
            crash_recovery='PASS', uncommitted_grant_audit_proof='ROLLED_BACK', stale_restore='REFUSED',
            current_restore='EXACT_ALL_LAB_TABLES', restored_rows=restored, proof_replay='REFUSED',
            pending_proof='CONSUMED_ONCE', revocation='PRESERVED', payment_replay='IDEMPOTENT',
            pending_audit='PRESERVED_AND_EXPLICITLY_CLOSED', restored_audit_sequence='PASS', production_writes=0,
            field_admission='NOT_MIGRATED', certificate_readiness_writers='NOT_MIGRATED',
            replication='NOT_IMPLEMENTED', reverse_migration='NOT_IMPLEMENTED')
    receipt['owned_container_cleanup'] = 'PASS'
    private_file(args.workdir / 'receipt.json', json.dumps(receipt, indent=2).encode())
    print(json.dumps(receipt, sort_keys=True))


if __name__ == '__main__':
    def terminate(signum, frame):
        raise SystemExit(128 + signum)

    signal.signal(signal.SIGTERM, terminate)
    main()
