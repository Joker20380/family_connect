"""Exercise paid rollback/recovery on disposable synthetic stores, never production."""
import argparse
import json
from pathlib import Path
import signal

from control.friends import paid_beta, subscription
from control.friends.access import Access, Rejected
from control.friends.enrollment_postgres import PostgresEnrollment
from control.friends.paid_postgres import initialize_synthetic_paid
from device_identity.device import DeviceIdentity
from scripts.control_ha_rehearsal import private_file, require
from scripts.enrollment_postgres_rehearsal import Rehearsal

NOW = 1800000000


def snapshot(repository):
    from psycopg import sql
    with repository.transaction() as transaction:
        tables = transaction.database.execute('SELECT tablename FROM pg_catalog.pg_tables '
            'WHERE schemaname=current_schema() ORDER BY tablename').fetchall()
        return {row['tablename']: transaction.database.execute(sql.SQL('SELECT * FROM {} ORDER BY 1').format(
            sql.Identifier(row['tablename']))).fetchall() for row in tables}


def require_current_restore(expected, restored):
    require(restored == expected, 'RESTORE_WOULD_LOSE_OR_CHANGE_ACKNOWLEDGED_STATE')


def apply(transaction, support, kind='payment', event_id='synthetic-payment-0001', **values):
    if kind == 'payment':
        values = dict(period_start=NOW, paid_until=NOW + 3600,
                      apk_sha256=paid_beta.PAID_ANDROID_RELEASES[-1].apk_sha256) | values
    return paid_beta.apply_event(transaction, support, kind, event_id, 'synthetic-receipt', now=NOW, **values)


class PaidRehearsal(Rehearsal):
    CONTRACT_FILES = ('tests/test_enrollment_repository.py', 'tests/test_paid_repository.py')

    def dump(self, repository, name):
        backup = self.docker('exec', self.container, 'pg_dump', '--username=fc_ha_synthetic',
            '--dbname=fc_ha_synthetic', '--format=custom', '--no-owner', '--no-acl',
            '--schema=' + repository.schema, binary=True)
        private_file(self.root / name, backup)
        return backup

    def restore(self, target, repository, backup):
        target.docker('exec', '-i', target.container, 'pg_restore', '--username=fc_ha_synthetic',
            '--dbname=fc_ha_synthetic', '--no-owner', '--no-acl', '--exit-on-error', '--single-transaction',
            input_data=backup)
        return PostgresEnrollment(port=target.port, schema=repository.schema, password=target.password)

    def recovery(self):
        repository = self.repository()
        repository.initialize_synthetic()
        initialize_synthetic_paid(repository)
        access = Access(None, clock=lambda: NOW, enrollment_repository=repository)
        device = DeviceIdentity.generate()
        pending = access.challenge(device.public_identity, device.wireguard_public_key, 'activate', access.invite())
        access.complete(device.prove_transport_key(pending['challenge']), 'activate')
        with repository.transaction() as transaction:
            support = transaction.registered(device.reference)
            transaction.database.execute('UPDATE device_support SET platform=%s,app_version=%s,version_code=%s,last_seen=%s',
                ('android', '0.1.18-beta126', 126, NOW))
            transaction.database.execute('INSERT INTO field_support_audit(timestamp,support_id,previous_state,new_state,outcome) '
                'VALUES (%s,%s,%s,%s,%s)', (NOW, support, 0, 1, 'synthetic-only'))
        old_backup = self.dump(repository, 'before-payments.dump')
        with repository.transaction() as transaction:
            first = apply(transaction.paid(), support)
        with repository.transaction() as transaction:
            apply(transaction.paid(), support, 'grace', 'synthetic-grace-0001', grace_until=NOW + 7200)
        with repository.transaction() as transaction:
            apply(transaction.paid(), support, 'revoke', 'synthetic-revoke-0001')
        pending = access.challenge(device.public_identity, device.wireguard_public_key, 'subscription')
        consumed = device.prove_transport_key(pending['challenge'])
        require(subscription.request(access, consumed)['subscription']['effective_state'] == 'revoked', 'REVOKE_NOT_VISIBLE')
        committed = snapshot(repository)
        unfinished = repository.connect()
        try:
            repository.configure(unfinished)
            unfinished.execute('INSERT INTO invites(hash) VALUES (%s)', ('uncommitted-synthetic',))
            placeholders = ','.join(['%s'] * len(first['event']))
            unfinished.execute('INSERT INTO paid_beta_events (' + ','.join(first['event']) + f') VALUES ({placeholders})',
                tuple((first['event'] | dict(event_id='synthetic-uncommitted-event')).values()))
            require(self.owned(), 'REHEARSAL_CONTAINER_MISSING')
            self.docker('kill', '--signal', 'KILL', self.container)
        finally:
            unfinished.close()
        self.docker('start', self.container)
        self.refresh_port()
        repository.port = self.port
        self.wait_ready()
        require_current_restore(committed, snapshot(repository))
        with repository.transaction() as transaction:
            duplicate = apply(transaction.paid(), support)
            require(duplicate['duplicate'] and duplicate['event'] == first['event'], 'ACK_LOSS_REPLAY_CHANGED_PAYMENT')
        latest_backup = self.dump(repository, 'after-acknowledged-writes.dump')
        with Rehearsal(self.root / 'stale-restore') as target:
            restored = self.restore(target, repository, old_backup)
            try:
                require_current_restore(committed, snapshot(restored))
            except ValueError as error:
                require(str(error) == 'RESTORE_WOULD_LOSE_OR_CHANGE_ACKNOWLEDGED_STATE', 'UNEXPECTED_RESTORE_FAILURE')
            else:
                raise RuntimeError('Stale rollback incorrectly accepted')
        with Rehearsal(self.root / 'current-restore') as target:
            restored = self.restore(target, repository, latest_backup)
            require_current_restore(committed, snapshot(restored))
            recovered = Access(None, clock=lambda: NOW, enrollment_repository=restored)
            try:
                subscription.request(recovered, consumed)
            except Rejected:
                pass
            else:
                raise RuntimeError('Consumed subscription proof replayed after restore')
            with restored.transaction() as transaction:
                duplicate = apply(transaction.paid(), support)
                require(duplicate['duplicate'] and duplicate['event'] == first['event'], 'RESTORED_PAYMENT_CHANGED')
                require(paid_beta.effective_subscription_state(transaction.paid(), device.reference, NOW).state ==
                        'revoked', 'RESTORED_REVOCATION_LOST')
            from psycopg import errors
            for statement, reason in (
                ("UPDATE paid_beta_events SET new_state='active'", 'PAID_EVENT_IMMUTABLE'),
                ("UPDATE paid_beta_subscriptions SET state='active',revoked_at=NULL", 'PAID_REVOKED'),
            ):
                try:
                    with restored.transaction() as transaction:
                        transaction.database.execute(statement)
                except errors.RaiseException as error:
                    require(reason in str(error), 'RESTORED_TRIGGER_MISMATCH')
                else:
                    raise RuntimeError('Restored immutable state accepted modification')
            require_current_restore(committed, snapshot(restored))
            with restored.transaction() as transaction:
                appended = transaction.database.execute('INSERT INTO field_support_audit'
                    '(timestamp,support_id,previous_state,new_state,outcome) VALUES (%s,%s,%s,%s,%s) RETURNING id',
                    (NOW + 1, support, 1, 0, 'synthetic-only')).fetchone()
                require(appended['id'] > max(row['id'] for row in committed['field_support_audit']), 'RESTORED_SEQUENCE_REGRESSED')
        return {table: len(records) for table, records in committed.items()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workdir', required=True, type=Path)
    args = parser.parse_args()
    with PaidRehearsal(args.workdir) as rehearsal:
        tests = rehearsal.contracts()
        restored = rehearsal.recovery()
        receipt = dict(schema=1, result='ISOLATED_PAID_POSTGRES_PASS', contracts=tests,
            postgres=rehearsal.manifest['version'], driver='psycopg3.3.9', synthetic_only=True,
            crash_recovery='PASS', uncommitted_ledger='ROLLED_BACK', stale_restore='REFUSED',
            current_restore='EXACT_ALL_LAB_TABLES', restored_rows=restored, proof_replay='REFUSED',
            restored_triggers='PASS', restored_audit_sequence='PASS',
            payment_ack_loss='IDEMPOTENT', production_writes=0, reverse_migration='NOT_IMPLEMENTED',
            transport_membership='NOT_MIGRATED', replication='NOT_IMPLEMENTED')
    receipt['owned_container_cleanup'] = 'PASS'
    private_file(args.workdir / 'receipt.json', json.dumps(receipt, indent=2).encode())
    print(json.dumps(receipt, sort_keys=True))


if __name__ == '__main__':
    def terminate(signum, frame):
        raise SystemExit(128 + signum)

    signal.signal(signal.SIGTERM, terminate)
    main()
