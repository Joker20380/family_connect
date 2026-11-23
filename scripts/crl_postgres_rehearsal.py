"""Synthetic CRL outbox/file-boundary rehearsal, never a distributed publisher."""
import argparse
from copy import copy
import hashlib
import json
from pathlib import Path
import signal
import tempfile

from cryptography import x509

from control.friends.access import Access
from control.friends import restricted_admin as crl, restricted_sync, support_ids
from control.friends.crl_postgres import initialize_synthetic_crl
from control.friends.restricted import migrate
from scripts.chat_postgres_rehearsal import refused_value
from scripts.control_ha_rehearsal import private_file, require
from scripts.enrollment_postgres_rehearsal import Rehearsal
from scripts.paid_postgres_rehearsal import PaidRehearsal, apply, snapshot, require_current_restore
from scripts.restricted_postgres_rehearsal import initialize as initialize_restricted, synthetic_service, issue_proof
from scripts.referral_postgres_rehearsal import NOW, proof, refused

SQLITE_DDL = (
    'CREATE TABLE ha_crl_schema(version INTEGER PRIMARY KEY, purpose TEXT NOT NULL)',
    'CREATE TABLE restricted_crl_sequence(singleton INTEGER PRIMARY KEY CHECK(singleton=1), '
    'sequence INTEGER NOT NULL CHECK(sequence>=0 AND sequence<9007199254740992))',
    'CREATE TABLE restricted_crl_publications(operation_id TEXT PRIMARY KEY, request_sha256 TEXT NOT NULL, '
    'sequence INTEGER UNIQUE NOT NULL CHECK(sequence>0 AND sequence<9007199254740992), '
    'payload TEXT NOT NULL, payload_sha256 TEXT NOT NULL, issued_at INTEGER NOT NULL, expires_at INTEGER NOT NULL, '
    'local_receipt INTEGER NOT NULL DEFAULT 0 CHECK(local_receipt IN (0,1)), CHECK(expires_at>issued_at))',
)


def initialize(access):
    if access.path is None:
        initialize_restricted(access.enrollment_repository)
        initialize_synthetic_crl(access.enrollment_repository)
    else:
        migrate(access)
        with access.enrollment() as enrollment:
            for statement in SQLITE_DDL:
                enrollment.database.execute(statement)
            enrollment.database.execute('INSERT INTO ha_crl_schema VALUES (?,?)', (1, crl.CRL_PURPOSE))
            enrollment.database.execute('INSERT INTO restricted_crl_sequence VALUES (1,0)')
            fields = ('operation_id', 'request_sha256', 'sequence', 'payload', 'payload_sha256', 'issued_at', 'expires_at')
            changes = ' OR '.join('NEW.' + field + ' IS NOT OLD.' + field for field in fields)
            enrollment.database.execute('CREATE TRIGGER crl_immutable BEFORE UPDATE ON restricted_crl_publications '
                'WHEN ' + changes + " OR NEW.local_receipt<OLD.local_receipt BEGIN SELECT RAISE(ABORT,'immutable CRL candidate'); END")
            enrollment.database.execute('CREATE TRIGGER crl_no_delete BEFORE DELETE ON restricted_crl_publications '
                "BEGIN SELECT RAISE(ABORT,'immutable CRL candidate'); END")


def publish_local_for_rehearsal(access, operation_id, target):
    target = Path(target)
    require(target.is_absolute() and target.parent.resolve().is_relative_to(Path(tempfile.gettempdir()).resolve())
            and not target.is_symlink() and target.parent.is_dir(), 'TEMPORARY_REHEARSAL_ONLY')
    candidate = crl.pending_crl(access, operation_id)
    restricted_sync.atomic(target, candidate['payload'].encode())
    require(hashlib.sha256(target.read_bytes()).hexdigest() == candidate['payload_sha256'], 'LOCAL_CRL_READBACK_MISMATCH')
    return crl.acknowledge_crl(access, operation_id, candidate['payload_sha256'])


class CRLRehearsal(PaidRehearsal):
    CONTRACT_FILES = ('tests/test_enrollment_repository.py', 'tests/test_crl_repository.py')

    def crl_recovery(self):
        repository = self.repository()
        repository.initialize_synthetic()
        access = Access(None, clock=lambda: NOW, enrollment_repository=repository)
        initialize(access)
        service, device = synthetic_service(access)
        alias = support_ids.request(access, dict(proof=proof(access, device, 'support'), platform='android',
            app_version='0.1.18-beta126', version_code=126))['device_support_id']
        with access.enrollment() as enrollment:
            apply(enrollment.paid(), alias, paid_until=NOW + 600)
        consumed = issue_proof(service, device)
        issued = service.fetch(consumed)
        pending_proof = issue_proof(service, device)
        with access.enrollment() as enrollment:
            enrollment.restricted_admin().revoke_grant(device.reference)
        old_backup = self.dump(repository, 'before-crl.dump')
        previous = service.crl_source()
        first = crl.prepare_crl(service, 'synthetic-crl-first', previous)
        target = self.root / 'synthetic-revocations.pem'
        publish_local_for_rehearsal(access, first['operation_id'], target)
        second = crl.prepare_crl(service, 'synthetic-crl-second', first['payload'].encode())
        restricted_sync.atomic(target, second['payload'].encode())
        committed = snapshot(repository)
        unfinished = repository.connect()
        try:
            repository.configure(unfinished)
            unfinished.execute('UPDATE restricted_crl_sequence SET sequence=sequence+100')
            unfinished.execute('UPDATE restricted_crl_publications SET local_receipt=1')
            unfinished.execute('UPDATE restricted_grants SET revoked=0')
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
        backup = self.dump(repository, 'current-crl.dump')
        with Rehearsal(self.root / 'stale-restore') as restored_lab:
            stale = self.restore(restored_lab, repository, old_backup)
            refused_value(lambda: require_current_restore(committed, snapshot(stale)),
                          'RESTORE_WOULD_LOSE_OR_CHANGE_ACKNOWLEDGED_STATE')
        with Rehearsal(self.root / 'current-restore') as restored_lab:
            restored = self.restore(restored_lab, repository, backup)
            require_current_restore(committed, snapshot(restored))
            recovered = Access(None, clock=lambda: NOW, enrollment_repository=restored)
            current = copy(service)
            current.access = recovered
            refused(lambda: current.fetch(consumed))
            refused(lambda: current.fetch(pending_proof))
            require(crl.prepare_crl(current, second['operation_id'], first['payload'].encode()) == second,
                    'CRL_CANDIDATE_CHANGED')
            require(crl.pending_crl(recovered, second['operation_id'])['local_receipt'] == 0, 'CRL_RECEIPT_INVENTED')
            refused_value(lambda: crl.pending_crl(recovered, first['operation_id']), 'CRL candidate is stale or inconsistent')
            with recovered.enrollment() as enrollment:
                require(apply(enrollment.paid(), alias, paid_until=NOW + 600)['duplicate'], 'PAYMENT_REPLAYED')
            require_current_restore(committed, snapshot(restored))
            raw = second['payload'].encode()
            import psycopg
            for query in ("UPDATE restricted_crl_publications SET payload='changed'", 'TRUNCATE restricted_crl_publications'):
                try:
                    with recovered.enrollment() as enrollment:
                        enrollment.database.execute(query)
                except psycopg.errors.CheckViolation:
                    pass
                else:
                    raise ValueError('RESTORED_CRL_IMMUTABILITY_MISSING')
            require_current_restore(committed, snapshot(restored))
            certificate = x509.load_pem_x509_certificate(issued['certificate'].encode())
            require(x509.load_pem_x509_crl(raw).get_revoked_certificate_by_serial_number(certificate.serial_number) is not None,
                    'RESTORED_REVOCATION_MISSING')
            require(target.read_bytes() == raw, 'CRL_FILE_AHEAD_CHANGED')
            repaired = publish_local_for_rehearsal(recovered, second['operation_id'], target)
            require(repaired['local_receipt'] == 1 and target.read_bytes() == raw, 'CRL_RECONCILIATION_FAILED')
            require(publish_local_for_rehearsal(recovered, second['operation_id'], target) == repaired, 'CRL_RECEIPT_REPLAY_FAILED')
            third = crl.prepare_crl(current, 'synthetic-crl-third', raw)
            require(third['sequence'] == second['sequence'] + 1, 'CRL_SEQUENCE_REWOUND')
            publish_local_for_rehearsal(recovered, third['operation_id'], self.root / 'rebuilt-from-db.pem')
        return {table: len(records) for table, records in committed.items()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workdir', required=True, type=Path)
    args = parser.parse_args()
    with CRLRehearsal(args.workdir) as rehearsal:
        tests = rehearsal.contracts()
        restored = rehearsal.crl_recovery()
        result = dict(schema=1, result='ISOLATED_CRL_POSTGRES_PASS', contracts=tests, postgres=rehearsal.manifest['version'],
            synthetic_only=True, crash_recovery='PASS', current_restore='EXACT_ALL_LAB_TABLES', stale_restore='REFUSED',
            restored_rows=restored, pending_payload='EXACT_BYTES', local_file_ahead='RECONCILED', sequence='CONTINUES',
            production_writes=0, authority_keys='EPHEMERAL_RETAINED_NOT_RESTORED', distributed_publication='FORBIDDEN',
            replication='NOT_IMPLEMENTED', reverse_migration='NOT_IMPLEMENTED')
    result['owned_container_cleanup'] = 'PASS'
    private_file(args.workdir / 'receipt.json', json.dumps(result, indent=2).encode())
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    def terminate(signum, frame):
        raise SystemExit(128 + signum)

    signal.signal(signal.SIGTERM, terminate)
    main()
