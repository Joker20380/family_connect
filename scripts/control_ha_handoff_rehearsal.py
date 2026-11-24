"""Owned full-store import/recovery with retained handoff floors; never activation."""
import argparse
import json
from pathlib import Path
import signal

from scripts.control_ha_handoff_fixture import closed_handoff_fixture
from scripts.control_ha_import_fixture import CHECKPOINT
from scripts.control_ha_maintenance_rehearsal import MaintenanceRehearsal
from scripts.control_ha_maintenance_fixture import artifacts_for_maintenance
from scripts.control_ha_recovery_bundle import seal_handoff
from scripts.control_ha_rehearsal import private_file
from scripts.control_ha_sqlite_import import preflight_installed_sqlite
from scripts.control_ha_sqlite_rehearsal import SQLiteImportRehearsal
from scripts.referral_postgres_rehearsal import NOW


class HandoffImportRehearsal(SQLiteImportRehearsal):
    CONTRACT_FILES = ('tests/test_control_ha_handoff_import.py', 'tests/test_control_ha_sqlite_import.py',
                      'tests/test_control_ha_import.py', 'tests/test_control_ha_installed_census.py')
    CONTRACT_TIMEOUT = 300

    def capture_fixture(self):
        root = self.root / 'fixture'
        root.mkdir(mode=0o700)
        fixture = closed_handoff_fixture(root)
        frozen = preflight_installed_sqlite(fixture.stores, fixture.external, fixture.expected, CHECKPOINT,
                                           fixture.bootstrap, fixture.service.anchor, now=NOW)
        return fixture, frozen


class HandoffRecoveryRehearsal(MaintenanceRehearsal):
    CONTRACT_FILES = ('tests/test_control_ha_handoff_recovery.py', 'tests/test_control_ha_handoff_archive.py',
                      'tests/test_control_ha_recovery_bundle.py', 'tests/test_control_ha_handoff_import.py',
                      'tests/test_control_ha_current_audit.py', 'tests/test_control_ha_forward_checkpoint.py',
                      'tests/test_control_ha_forward_archive.py', 'tests/test_control_ha_external_v1.py',
                      'tests/test_control_ha_receiver_v1.py', 'tests/test_control_ha_maintenance_v1.py')
    CONTRACT_TIMEOUT = 300

    def make_fixture(self, root):
        return closed_handoff_fixture(root)

    def fixture_artifacts(self, fixture):
        artifacts, capture = artifacts_for_maintenance(fixture, sqlite_preflight=preflight_installed_sqlite)
        self.maintenance_behavior = capture['behavior']
        return artifacts

    def seal_bundle(self, fixture, artifacts):
        return seal_handoff(fixture.stores, fixture.external, artifacts, CHECKPOINT,
                            fixture.bootstrap, self.anchor, self.bundle_key, now=NOW)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workdir', required=True, type=Path)
    parser.add_argument('--encrypted', action='store_true')
    args = parser.parse_args()
    runner = HandoffRecoveryRehearsal if args.encrypted else HandoffImportRehearsal
    with runner(args.workdir) as rehearsal:
        contracts = rehearsal.contracts()
        result = rehearsal.joint_recovery()
        receipt = dict(schema=1, result='ISOLATED_HANDOFF_RECOVERY_PASS' if args.encrypted else
                       'ISOLATED_CLOSED_HANDOFF_RETENTION_PASS', contracts=contracts,
            postgres=rehearsal.manifest['version'], crash_recovery='EXACT', current_restore='EXACT',
            stale_restore='REFUSED', old_import_after_writes='REFUSED', activation='FORBIDDEN', production_writes=0,
            handoff_runtime='NOT_IMPLEMENTED_RETAINED_READ_ONLY', live_barrier='NOT_IMPLEMENTED',
            external_recovery='NOT_QUALIFIED_KEYS_RETAINED', **result)
        if args.encrypted:
            receipt.update(original_fixture='REMOVED_BEFORE_RESTORE',
                issuer_referral_authority='RECONSTRUCTED_FROM_BUNDLE',
                external_recovery='ISOLATED_BOUNDED_INPUTS_ONLY', full_dr='NOT_QUALIFIED',
                key_checkpoint_custody='RETAINED_IN_MEMORY', renewal_ledgers='UNSUPPORTED_REFUSED',
                preflight=rehearsal.bundle_summary, external_behavior=rehearsal.external_behavior,
                receiver_behavior=rehearsal.receiver_behavior, maintenance_behavior=rehearsal.maintenance_behavior,
                maintenance_evidence=rehearsal.maintenance_evidence)
    receipt['owned_container_cleanup'] = 'PASS'
    private_file(args.workdir / 'receipt.json', json.dumps(receipt, indent=2).encode())
    print(json.dumps(receipt, sort_keys=True))


if __name__ == '__main__':
    def terminate(signum, frame):
        raise SystemExit(128 + signum)
    signal.signal(signal.SIGTERM, terminate)
    main()
