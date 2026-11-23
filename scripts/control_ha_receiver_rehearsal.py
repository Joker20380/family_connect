"""Owned receiver safety crash/restore rehearsal; no production publication."""
import argparse
import json
from pathlib import Path
import signal

from scripts.control_ha_bundle_fixture import reconstruct
from scripts.control_ha_external_fixture import exercise_external_files
from scripts.control_ha_external_rehearsal import ExternalRehearsal
from scripts.control_ha_receiver_fixture import artifacts_for_receivers, exercise_receiver_files
from scripts.control_ha_receiver_v1 import preflight_receivers
from scripts.control_ha_rehearsal import private_file
from scripts.referral_postgres_rehearsal import NOW


class ReceiverRehearsal(ExternalRehearsal):
    CONTRACT_FILES = ('tests/test_control_ha_receiver_v1.py', 'tests/test_control_ha_external_v1.py',
                      'tests/test_enrollment_repository.py')

    def fixture_artifacts(self, fixture):
        return artifacts_for_receivers(fixture)

    def validate_bundle(self, bundle):
        return preflight_receivers(bundle, self.bundle_key, self.checkpoint, self.anchor, now=NOW)

    def recover_fixture(self, fixture):
        recovered = self.validate_bundle((self.root / 'recovery.bundle').read_bytes())
        root = self.root / 'recovered-external'
        fixture = reconstruct(fixture, recovered, self.anchor, root)
        self.external_behavior = exercise_external_files(fixture, recovered, root)
        self.receiver_behavior = exercise_receiver_files(recovered, root / 'receivers')
        return fixture


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workdir', required=True, type=Path)
    args = parser.parse_args()
    with ReceiverRehearsal(args.workdir) as rehearsal:
        contracts = rehearsal.contracts()
        result = rehearsal.joint_recovery()
        receipt = dict(schema=1, result='ISOLATED_RECEIVER_SAFETY_PASS', contracts=contracts,
            postgres=rehearsal.manifest['version'], activation='FORBIDDEN', production_writes=0,
            original_fixture='REMOVED_BEFORE_RESTORE', crash_recovery='EXACT', current_restore='EXACT',
            stale_restore='REFUSED', opaque_probe_roles=['maintenance_state'],
            full_external_recovery='NOT_QUALIFIED', live_barrier='NOT_IMPLEMENTED',
            key_checkpoint_custody='RETAINED_IN_MEMORY', preflight=rehearsal.bundle_summary,
            external_behavior=rehearsal.external_behavior, receiver_behavior=rehearsal.receiver_behavior, **result)
    receipt['owned_container_cleanup'] = 'PASS'
    private_file(args.workdir / 'receipt.json', json.dumps(receipt, indent=2).encode())
    print(json.dumps(receipt, sort_keys=True))


if __name__ == '__main__':
    def terminate(signum, frame):
        raise SystemExit(128 + signum)
    signal.signal(signal.SIGTERM, terminate)
    main()
