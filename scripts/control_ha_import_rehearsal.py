"""Import and recover the full synthetic storage-shape fixture on owned local PG."""
import argparse
import json
from pathlib import Path
import signal

from control.friends.access import Access, Rejected
from scripts.control_ha_import import import_snapshot, preflight
from scripts.control_ha_import_fixture import bundle, CHECKPOINT
from scripts.control_ha_rehearsal import private_file, require
from scripts.enrollment_postgres_rehearsal import Rehearsal
from scripts.paid_postgres_rehearsal import PaidRehearsal, snapshot, require_current_restore
from scripts.referral_postgres_rehearsal import NOW


class ImportRehearsal(PaidRehearsal):
    CONTRACT_FILES = ('tests/test_control_ha_import.py', 'tests/test_enrollment_repository.py')

    def import_recovery(self):
        source = self.root / 'fixture'
        source.mkdir(mode=0o700)
        stores, external, expected, _identity, pending = bundle(source)
        frozen = preflight(stores, external, expected, CHECKPOINT)
        repository = self.repository()
        require(import_snapshot(repository, frozen)['result'] == 'IMPORTED', 'IMPORT_REQUIRED')
        committed = snapshot(repository)
        require(len(committed) == 43 and all(committed.values()), 'ALL_TABLES_MUST_BE_NONEMPTY')
        backup = self.dump(repository, 'synthetic-import.dump')
        unfinished = repository.connect()
        try:
            repository.configure(unfinished)
            unfinished.execute('UPDATE devices SET revoked=1')
            require(self.owned(), 'REHEARSAL_CONTAINER_MISSING')
            self.docker('kill', '--signal', 'KILL', self.container)
        finally:
            unfinished.close()
        self.docker('start', self.container)
        self.refresh_port()
        repository.port = self.port
        self.wait_ready()
        require_current_restore(committed, snapshot(repository))
        require(import_snapshot(repository, frozen)['result'] == 'EXACT_RETRY', 'RESTART_READBACK')
        with Rehearsal(self.root / 'current-restore') as target:
            restored = self.restore(target, repository, backup)
            require_current_restore(committed, snapshot(restored))
            require(import_snapshot(restored, frozen)['result'] == 'EXACT_RETRY', 'RESTORE_READBACK')
            access = Access(None, clock=lambda: NOW, enrollment_repository=restored)
            access.complete(pending, 'status')
            try:
                access.complete(pending, 'status')
            except Rejected:
                pass
            else:
                raise ValueError('RESTORE_REUSED_PROOF')
            with restored.transaction() as enrollment:
                row = enrollment.database.execute("INSERT INTO field_support_audit(timestamp,support_id,previous_state,new_state,outcome) "
                    "VALUES (%s,'synthetic',0,1,'synthetic') RETURNING id", (NOW,)).fetchone()
                require(row['id'] == 42, 'RESTORE_AUDIT_SEQUENCE')
        return {name: len(rows) for name, rows in committed.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workdir', required=True, type=Path)
    args = parser.parse_args()
    with ImportRehearsal(args.workdir) as rehearsal:
        contracts = rehearsal.contracts()
        rows = rehearsal.import_recovery()
        receipt = dict(schema=1, result='ISOLATED_ALL_STORE_SHAPE_IMPORT_PASS', contracts=contracts,
            postgres=rehearsal.manifest['version'], sources=4, data_tables=30, restored_rows=rows,
            crash_recovery='EXACT', current_restore='EXACT', production_writes=0, activation='FORBIDDEN',
            restored_pending_proof='ONCE', restored_audit_next_id=42,
            source_contract='SYNTHETIC_SHAPE_NOT_DEPLOYED_SQLITE', external_inputs='DECLARED_REFERENCES_ONLY',
            live_barrier='NOT_IMPLEMENTED', production_import='NOT_IMPLEMENTED', replication='NOT_IMPLEMENTED')
    receipt['owned_container_cleanup'] = 'PASS'
    private_file(args.workdir / 'receipt.json', json.dumps(receipt, indent=2).encode())
    print(json.dumps(receipt, sort_keys=True))


if __name__ == '__main__':
    def terminate(signum, frame):
        raise SystemExit(128 + signum)
    signal.signal(signal.SIGTERM, terminate)
    main()
