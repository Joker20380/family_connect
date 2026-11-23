"""Disposable Support ID recovery; restricted rows are read-side fixtures, not migrated writers."""
import argparse
import json
from pathlib import Path
import signal

from control.friends import support_ids
from control.friends.access import Access
from control.friends.paid_postgres import initialize_synthetic_paid
from control.friends.support_postgres import initialize_synthetic_support
from device_identity.device import DeviceIdentity
from scripts.control_ha_rehearsal import private_file, require
from scripts.enrollment_postgres_rehearsal import Rehearsal
from scripts.paid_postgres_rehearsal import PaidRehearsal, apply, require_current_restore, snapshot
from scripts.referral_postgres_rehearsal import NOW, proof, refused

READSIDE_FIXTURE_DDL = (
    'CREATE TABLE restricted_readiness_results(correlation TEXT PRIMARY KEY, nonce TEXT UNIQUE NOT NULL, '
    'device TEXT NOT NULL, challenge_at BIGINT NOT NULL, fetch_id TEXT, fetch_at BIGINT, revision BIGINT, '
    'minimum_crl BIGINT, expires BIGINT, ack TEXT, ack_at BIGINT, gateway_binding TEXT NOT NULL DEFAULT \'\')',
    'CREATE TABLE restricted_grants(device TEXT PRIMARY KEY REFERENCES devices(device), family TEXT NOT NULL, '
    'revision BIGINT NOT NULL, expires BIGINT, revoked BIGINT NOT NULL DEFAULT 0)',
)


def observation(access, device):
    return dict(proof=proof(access, device, 'support'), platform='android', app_version='0.1.18-beta126', version_code=126)


class SupportRehearsal(PaidRehearsal):
    CONTRACT_FILES = ('tests/test_enrollment_repository.py', 'tests/test_paid_repository.py',
                      'tests/test_support_repository.py')

    def support_recovery(self):
        repository = self.repository()
        repository.initialize_synthetic()
        initialize_synthetic_support(repository)
        initialize_synthetic_paid(repository)
        access = Access(None, clock=lambda: NOW, enrollment_repository=repository)
        device, revoked = DeviceIdentity.generate(), DeviceIdentity.generate()
        for identity in (device, revoked):
            access.complete(proof(access, identity, 'activate', access.invite()), 'activate')
        with repository.transaction() as transaction:
            for statement in READSIDE_FIXTURE_DDL:
                transaction.database.execute(statement)
            transaction.database.execute('INSERT INTO restricted_readiness_results'
                '(correlation,nonce,device,challenge_at,ack,ack_at,expires) VALUES (%s,%s,%s,%s,%s,%s,%s)',
                ('synthetic-receipt', 'synthetic-nonce', device.reference, NOW - 10,
                 json.dumps(dict(app_version='0.1.18-beta125', version_code=125, result='READY')), NOW - 5, NOW + 60))
            transaction.database.execute('INSERT INTO restricted_grants VALUES (%s,%s,%s,%s,%s)',
                (device.reference, 'synthetic-readside-only', 1, NOW + 60, 0))
        support_ids.backfill(access)
        old_backup = self.dump(repository, 'before-support-observation.dump')
        value = observation(access, device)
        response = support_ids.request(access, value)
        support = response['device_support_id']
        pending = observation(access, device)
        denied = observation(access, revoked)
        access.revoke_device(revoked.reference)
        with repository.transaction() as transaction:
            apply(transaction.paid(), support)
            transaction.database.execute('INSERT INTO field_support_audit'
                '(timestamp,support_id,previous_state,new_state,outcome) VALUES (%s,%s,%s,%s,%s)',
                (NOW, support, 0, 0, 'synthetic-readside-only'))
        expected = support_ids.lookup(access, support, [])
        counts = support_ids.inventory(access)
        committed = snapshot(repository)
        unfinished = repository.connect()
        try:
            repository.configure(unfinished)
            unfinished.execute('UPDATE device_support SET version_code=999,last_seen=%s WHERE device=%s',
                               (NOW + 1, device.reference))
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
        refused(lambda: support_ids.request(access, value))
        refused(lambda: support_ids.request(access, denied))
        require(support_ids.backfill(access) == counts, 'BACKFILL_COUNTS_CHANGED')
        require(support_ids.lookup(access, support, []) == expected, 'BACKFILL_DOWNGRADED_OBSERVATION')
        require_current_restore(committed, snapshot(repository))
        backup = self.dump(repository, 'current-support.dump')
        with Rehearsal(self.root / 'stale-restore') as target:
            stale = self.restore(target, repository, old_backup)
            try:
                require_current_restore(committed, snapshot(stale))
            except ValueError as error:
                require(str(error) == 'RESTORE_WOULD_LOSE_OR_CHANGE_ACKNOWLEDGED_STATE', 'UNEXPECTED_RESTORE_ERROR')
            else:
                raise RuntimeError('Stale support restore accepted')
        with Rehearsal(self.root / 'current-restore') as target:
            restored = self.restore(target, repository, backup)
            require_current_restore(committed, snapshot(restored))
            recovered = Access(None, clock=lambda: NOW, enrollment_repository=restored)
            require(support_ids.backfill(recovered) == counts, 'RESTORED_COUNTS_CHANGED')
            require(support_ids.lookup(recovered, support, []) == expected, 'RESTORED_SUPPORT_CHANGED')
            refused(lambda: support_ids.request(recovered, value))
            refused(lambda: support_ids.request(recovered, denied))
            with restored.transaction() as transaction:
                require(apply(transaction.paid(), support)['duplicate'], 'RESTORED_PAYMENT_REPLAYED')
            require_current_restore(committed, snapshot(restored))
            require(support_ids.request(recovered, pending) == response, 'PENDING_PROOF_OR_ALIAS_CHANGED')
            refused(lambda: support_ids.request(recovered, pending))
            with restored.transaction() as transaction:
                appended = transaction.database.execute('INSERT INTO field_support_audit'
                    '(timestamp,support_id,previous_state,new_state,outcome) VALUES (%s,%s,%s,%s,%s) RETURNING id',
                    (NOW + 1, support, 0, 0, 'synthetic-readside-only')).fetchone()
                require(appended['id'] > max(row['id'] for row in committed['field_support_audit']), 'RESTORED_SEQUENCE_REGRESSED')
        return {table: len(records) for table, records in committed.items()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workdir', required=True, type=Path)
    args = parser.parse_args()
    with SupportRehearsal(args.workdir) as rehearsal:
        tests = rehearsal.contracts()
        restored = rehearsal.support_recovery()
        receipt = dict(schema=1, result='ISOLATED_SUPPORT_POSTGRES_PASS', contracts=tests,
            postgres=rehearsal.manifest['version'], driver='psycopg3.3.9', synthetic_only=True,
            crash_recovery='PASS', uncommitted_observation_and_proof='ROLLED_BACK', stale_restore='REFUSED',
            current_restore='EXACT_ALL_LAB_TABLES', restored_rows=restored, proof_replay='REFUSED',
            pending_proof='CONSUMED_ONCE', stale_readiness='NO_DOWNGRADE', revocation='PRESERVED',
            payment_replay='IDEMPOTENT', restored_audit_sequence='PASS', production_writes=0,
            field_admission='NOT_MIGRATED', replication='NOT_IMPLEMENTED', reverse_migration='NOT_IMPLEMENTED')
    receipt['owned_container_cleanup'] = 'PASS'
    private_file(args.workdir / 'receipt.json', json.dumps(receipt, indent=2).encode())
    print(json.dumps(receipt, sort_keys=True))


if __name__ == '__main__':
    def terminate(signum, frame):
        raise SystemExit(128 + signum)

    signal.signal(signal.SIGTERM, terminate)
    main()
