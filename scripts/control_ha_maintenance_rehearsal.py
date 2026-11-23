"""Owned canonical-maintenance archive/import recovery; no host resume or publication."""
import argparse
import json
from pathlib import Path
import signal

from scripts.control_ha_maintenance_fixture import artifacts_for_maintenance, retain_evidence
from scripts.control_ha_maintenance_v1 import preflight_maintenance
from scripts.control_ha_receiver_rehearsal import ReceiverRehearsal
from scripts.control_ha_rehearsal import private_file
from scripts.referral_postgres_rehearsal import NOW


class MaintenanceRehearsal(ReceiverRehearsal):
    CONTRACT_FILES = ('tests/test_control_ha_maintenance_v1.py', 'tests/test_control_ha_receiver_v1.py',
                      'tests/test_enrollment_repository.py')

    def fixture_artifacts(self, fixture):
        artifacts, capture = artifacts_for_maintenance(fixture)
        self.maintenance_behavior = capture['behavior']
        return artifacts

    def validate_bundle(self, bundle):
        return preflight_maintenance(bundle, self.bundle_key, self.checkpoint, self.anchor, now=NOW)

    def recover_fixture(self, fixture):
        fixture = super().recover_fixture(fixture)
        recovered = self.validate_bundle((self.root / 'recovery.bundle').read_bytes())
        self.maintenance_evidence = retain_evidence(recovered, self.root / 'recovered-maintenance')
        return fixture


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workdir', required=True, type=Path)
    args = parser.parse_args()
    with MaintenanceRehearsal(args.workdir) as rehearsal:
        contracts = rehearsal.contracts()
        result = rehearsal.joint_recovery()
        receipt = dict(schema=1, result='ISOLATED_BOUNDED_MAINTENANCE_PASS', contracts=contracts,
            postgres=rehearsal.manifest['version'], activation='FORBIDDEN', production_writes=0,
            original_fixture='REMOVED_BEFORE_RESTORE', crash_recovery='EXACT', current_restore='EXACT',
            stale_restore='REFUSED', opaque_probe_roles=[], full_external_recovery='NOT_QUALIFIED',
            maintenance_resume='NOT_QUALIFIED', renewal_ledgers='UNSUPPORTED_REFUSED',
            live_barrier='NOT_IMPLEMENTED', key_checkpoint_custody='RETAINED_IN_MEMORY',
            preflight=rehearsal.bundle_summary, external_behavior=rehearsal.external_behavior,
            receiver_behavior=rehearsal.receiver_behavior, maintenance_behavior=rehearsal.maintenance_behavior,
            maintenance_evidence=rehearsal.maintenance_evidence, **result)
    receipt['owned_container_cleanup'] = 'PASS'
    private_file(args.workdir / 'receipt.json', json.dumps(receipt, indent=2).encode())
    print(json.dumps(receipt, sort_keys=True))


if __name__ == '__main__':
    def terminate(signum, frame):
        raise SystemExit(128 + signum)
    signal.signal(signal.SIGTERM, terminate)
    main()
