"""One shared contract gate and three owned stopped-variant recovery rehearsals."""
import argparse
import json
from pathlib import Path
import signal
import tempfile

from scripts.control_ha_online_rehearsal import OnlineRehearsal
from scripts.control_ha_rehearsal import private_file, require
from scripts.control_ha_stopped_capsule import inspect_stopped_inputs, preflight_stopped
from scripts.control_ha_stopped_fixture import stopped_fixture
from scripts.referral_postgres_rehearsal import NOW


class StoppedRehearsal(OnlineRehearsal):
    CONTRACT_FILES = ('tests/test_control_ha_stopped_capsule.py', 'tests/test_control_ha_online_capsule.py',
                      'tests/test_control_ha_renewal_history.py', 'tests/test_control_ha_maintenance_v1.py',
                      'tests/test_enrollment_repository.py')
    CONTRACT_TIMEOUT = 300
    mode = 'stopped'

    def contracts(self):
        files, total = self.CONTRACT_FILES, 0
        try:
            for source in files:
                self.CONTRACT_FILES = (source,)
                total += super().contracts()
                for extension in ('log', 'xml'):
                    (self.root / ('contracts.' + extension)).rename(self.root / (Path(source).stem + '.' + extension))
        finally:
            self.CONTRACT_FILES = files
        return total

    def make_fixture(self, root):
        fixture, self.captured_artifacts, bounded = stopped_fixture(root, mode=self.mode)
        self.bounded_behavior = bounded['behavior']
        return fixture

    def validate_bundle(self, bundle):
        return preflight_stopped(bundle, self.bundle_key, self.checkpoint, self.anchor, now=NOW)

    def inspect_journals(self, recovered):
        return inspect_stopped_inputs(recovered, self.checkpoint.checkpoint, self.anchor, now=NOW)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workdir', type=Path, required=True)
    args = parser.parse_args()
    require(not any(parent.is_symlink() for parent in (args.workdir, *args.workdir.parents)), 'REHEARSAL_SYMLINK')
    require(args.workdir.resolve().is_relative_to(Path(tempfile.gettempdir()).resolve()), 'TEMPORARY_REHEARSAL_ONLY')
    args.workdir.mkdir(mode=0o700)
    results = {}
    for mode in ('stopped', 'offline', 'emergency'):
        with StoppedRehearsal(args.workdir / mode) as rehearsal:
            rehearsal.mode = mode
            if mode == 'stopped':
                contracts = rehearsal.contracts()
            result = rehearsal.joint_recovery()
            results[mode] = dict(result='ISOLATED_STOPPED_RECOVERY_PASS', postgres=rehearsal.manifest['version'],
                original_fixture='REMOVED_BEFORE_RESTORE', crash_recovery='EXACT', current_restore='EXACT',
                stale_restore='REFUSED', activation='FORBIDDEN', host_resume='NOT_AUTHORIZED',
                full_dr='NOT_QUALIFIED', key_checkpoint_custody='RETAINED_IN_MEMORY', live_barrier='NOT_IMPLEMENTED',
                journal_behavior=rehearsal.journal_behavior, preflight=rehearsal.bundle_summary, **result)
        results[mode]['owned_container_cleanup'] = 'PASS'
        private_file(args.workdir / mode / 'receipt.json', json.dumps(results[mode], indent=2).encode())
    receipt = dict(schema=1, shared_contracts=contracts, contract_runs=1,
                   contract_processes=len(StoppedRehearsal.CONTRACT_FILES), recovery_variants=results, production_writes=0)
    private_file(args.workdir / 'receipt.json', json.dumps(receipt, indent=2).encode())
    print(json.dumps(dict(result='ISOLATED_THREE_VARIANT_RECOVERY_PASS', contracts=contracts,
                         variants=sorted(results), activation='FORBIDDEN')))


if __name__ == '__main__':
    def terminate(signum, frame):
        raise SystemExit(128 + signum)
    signal.signal(signal.SIGTERM, terminate)
    main()
