"""Owned combined online/bounded journal recovery; no production activation."""
import argparse
import json
from pathlib import Path
import signal

from scripts.control_ha_online_capsule import inspect_online_inputs, preflight_online
from scripts.control_ha_online_fixture import online_fixture
from scripts.control_ha_receiver_rehearsal import ReceiverRehearsal
from scripts.control_ha_rehearsal import private_file, require
from scripts.referral_postgres_rehearsal import NOW


class OnlineRehearsal(ReceiverRehearsal):
    CONTRACT_FILES = ('tests/test_control_ha_online_capsule.py', 'tests/test_control_ha_maintenance_v1.py',
                      'tests/test_enrollment_repository.py', 'tests/test_control_ha_renewal_history.py')
    history = False

    def make_fixture(self, root):
        fixture, self.captured_artifacts, bounded = online_fixture(root, history=self.history)
        self.bounded_behavior = bounded['behavior']
        return fixture

    def fixture_artifacts(self, fixture):
        artifacts = self.captured_artifacts
        del self.captured_artifacts
        return artifacts

    def validate_bundle(self, bundle):
        return preflight_online(bundle, self.bundle_key, self.checkpoint, self.anchor, now=NOW, history=self.history)

    def recover_fixture(self, fixture):
        fixture = super().recover_fixture(fixture)
        fixture.service.all_activated = True
        recovered = self.validate_bundle((self.root / 'recovery.bundle').read_bytes())
        destination = self.root / 'recovered-journals'
        destination.mkdir(mode=0o700)
        parts = recovered.artifacts['maintenance_state']
        for name, raw in parts.items():
            private_file(destination / name, raw)
        retained = {name: (destination / name).read_bytes() for name in parts}
        require(retained == parts, 'ONLINE_RETAINED_EVIDENCE_CHANGED')
        recovered.artifacts['maintenance_state'] = retained
        self.journal_behavior = inspect_online_inputs(recovered, self.checkpoint.checkpoint, self.anchor,
                                                     now=NOW, history=self.history)
        return fixture


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workdir', required=True, type=Path)
    parser.add_argument('--history', action='store_true')
    args = parser.parse_args()
    with OnlineRehearsal(args.workdir) as rehearsal:
        rehearsal.history = args.history
        contracts = rehearsal.contracts()
        result = rehearsal.joint_recovery()
        receipt = dict(schema=1, result='ISOLATED_ONLINE_CAPSULE_PASS', contracts=contracts,
            postgres=rehearsal.manifest['version'], activation='FORBIDDEN', production_writes=0,
            original_fixture='REMOVED_BEFORE_RESTORE', crash_recovery='EXACT', current_restore='EXACT',
            stale_restore='REFUSED', full_dr='NOT_QUALIFIED', live_barrier='NOT_IMPLEMENTED',
            key_checkpoint_custody='RETAINED_IN_MEMORY', host_resume='NOT_AUTHORIZED',
            history='RETAINED_ONLINE_CHAIN' if args.history else 'UNSUPPORTED_REFUSED',
            offline_emergency='UNSUPPORTED_REFUSED', preflight=rehearsal.bundle_summary,
            bounded_behavior=rehearsal.bounded_behavior, journal_behavior=rehearsal.journal_behavior,
            external_behavior=rehearsal.external_behavior, receiver_behavior=rehearsal.receiver_behavior, **result)
    receipt['owned_container_cleanup'] = 'PASS'
    private_file(args.workdir / 'receipt.json', json.dumps(receipt, indent=2).encode())
    print(json.dumps(receipt, sort_keys=True))


if __name__ == '__main__':
    def terminate(signum, frame):
        raise SystemExit(128 + signum)
    signal.signal(signal.SIGTERM, terminate)
    main()
