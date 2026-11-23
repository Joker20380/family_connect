"""Owned SQLite-adapter/semantic fixture recovery; not production activation."""
import argparse
import json
from pathlib import Path
import signal

from control.friends.access import Access
from scripts.chat_postgres_rehearsal import refused_value
from scripts.control_ha_import import ImportRejected, import_snapshot
from scripts.control_ha_import_fixture import CHECKPOINT
from scripts.control_ha_rehearsal import private_file, require
from scripts.control_ha_sqlite_import import preflight_sqlite
from scripts.control_ha_sqlite_fixture import joint_fixture, exercise_import
from scripts.paid_postgres_rehearsal import PaidRehearsal, snapshot, require_current_restore
from scripts.referral_postgres_rehearsal import NOW, refused


class SQLiteImportRehearsal(PaidRehearsal):
    CONTRACT_FILES = ('tests/test_control_ha_sqlite_import.py', 'tests/test_control_ha_import.py',
                      'tests/test_enrollment_repository.py')

    def capture_fixture(self):
        root = self.root / 'fixture'
        root.mkdir(mode=0o700)
        fixture = joint_fixture(root)
        frozen = preflight_sqlite(fixture.stores, fixture.external, fixture.expected, CHECKPOINT,
                                 fixture.bootstrap, fixture.service.anchor, now=NOW)
        return fixture, frozen

    def recover_fixture(self, fixture):
        return fixture

    def joint_recovery(self):
        fixture, frozen = self.capture_fixture()
        repository = self.repository()
        import_snapshot(repository, frozen)
        imported = snapshot(repository)
        backup = self.dump(repository, 'application-import.dump')
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
        require_current_restore(imported, snapshot(repository))
        require(import_snapshot(repository, frozen)['result'] == 'EXACT_RETRY', 'IMPORT_READBACK_CHANGED')
        with PaidRehearsal(self.root / 'import-restore') as target:
            restored = self.restore(target, repository, backup)
            require_current_restore(imported, snapshot(restored))
            require(import_snapshot(restored, frozen)['result'] == 'EXACT_RETRY', 'RESTORE_READBACK_CHANGED')
            behavior = exercise_import(self.recover_fixture(fixture), restored)
            acknowledged = snapshot(restored)
            current = target.dump(restored, 'after-new-writes.dump')
        with PaidRehearsal(self.root / 'stale-restore') as target:
            restored = self.restore(target, repository, backup)
            refused_value(lambda: require_current_restore(acknowledged, snapshot(restored)),
                          'RESTORE_WOULD_LOSE_OR_CHANGE_ACKNOWLEDGED_STATE')
        with PaidRehearsal(self.root / 'current-restore') as target:
            restored = self.restore(target, repository, current)
            require_current_restore(acknowledged, snapshot(restored))
            recovered = Access(None, clock=lambda: NOW, enrollment_repository=restored)
            refused(lambda: recovered.complete(fixture.pending['status'], 'status'))
            try:
                import_snapshot(restored, frozen)
            except ImportRejected:
                pass
            else:
                raise ValueError('OLD_IMPORT_OVERWROTE_NEW_WRITES')
            require_current_restore(acknowledged, snapshot(restored))
        return dict(imported_rows={name: len(rows) for name, rows in imported.items()},
                    current_rows={name: len(rows) for name, rows in acknowledged.items()}, behavior=behavior)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workdir', required=True, type=Path)
    args = parser.parse_args()
    with SQLiteImportRehearsal(args.workdir) as rehearsal:
        contracts = rehearsal.contracts()
        result = rehearsal.joint_recovery()
        receipt = dict(schema=1, result='ISOLATED_APPLICATION_SQLITE_IMPORT_PASS', contracts=contracts,
            postgres=rehearsal.manifest['version'], crash_recovery='EXACT', current_restore='EXACT',
            stale_restore='REFUSED', old_import_after_writes='REFUSED', activation='FORBIDDEN', production_writes=0,
            live_schema_census='NOT_PERFORMED', live_barrier='NOT_IMPLEMENTED', replication='NOT_IMPLEMENTED',
            external_recovery='NOT_QUALIFIED_KEYS_RETAINED', **result)
    receipt['owned_container_cleanup'] = 'PASS'
    private_file(args.workdir / 'receipt.json', json.dumps(receipt, indent=2).encode())
    print(json.dumps(receipt, sort_keys=True))


if __name__ == '__main__':
    def terminate(signum, frame):
        raise SystemExit(128 + signum)
    signal.signal(signal.SIGTERM, terminate)
    main()
