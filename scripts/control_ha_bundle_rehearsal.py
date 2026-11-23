"""Owned bundle/SQLite recovery rehearsal; no live reader or publication."""
import argparse
import json
from pathlib import Path
import secrets
import shutil
import signal

from scripts.control_ha_bundle_fixture import OPAQUE_PROBES, artifacts_for, reconstruct
from scripts.control_ha_import_fixture import CHECKPOINT
from scripts.control_ha_recovery_bundle import seal, preflight_bundle
from scripts.control_ha_rehearsal import private_file, require
from scripts.control_ha_sqlite_fixture import joint_fixture
from scripts.control_ha_sqlite_rehearsal import SQLiteImportRehearsal
from scripts.referral_postgres_rehearsal import NOW


class BundleRehearsal(SQLiteImportRehearsal):
    CONTRACT_FILES = ('tests/test_control_ha_recovery_bundle.py', 'tests/test_control_ha_sqlite_import.py',
                      'tests/test_enrollment_repository.py')

    def fixture_artifacts(self, fixture):
        return artifacts_for(fixture)

    def validate_bundle(self, bundle):
        return preflight_bundle(bundle, self.bundle_key, self.checkpoint, self.anchor, now=NOW)

    def capture_fixture(self):
        root = self.root / 'fixture'
        root.mkdir(mode=0o700)
        fixture = joint_fixture(root)
        self.bundle_key, self.anchor = secrets.token_bytes(32), fixture.service.anchor
        bundle, self.checkpoint = seal(fixture.stores, fixture.external, self.fixture_artifacts(fixture), CHECKPOINT,
            fixture.bootstrap, self.anchor, self.bundle_key, now=NOW)
        private_file(self.root / 'recovery.bundle', bundle)
        recovered = self.validate_bundle(bundle)
        self.bundle_summary = recovered.summary()
        fixture.service, fixture.access, fixture.referral_secret = None, None, b''
        fixture.stores, fixture.external, fixture.expected, fixture.paths = {}, {}, {}, {}
        fixture.bootstrap, fixture.pending['routing'] = b'', None
        shutil.rmtree(root)
        require(not root.exists(), 'SOURCE_FIXTURE_NOT_REMOVED')
        return fixture, recovered.snapshot

    def recover_fixture(self, fixture):
        recovered = self.validate_bundle((self.root / 'recovery.bundle').read_bytes())
        return reconstruct(fixture, recovered, self.anchor, self.root / 'recovered-external')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workdir', required=True, type=Path)
    args = parser.parse_args()
    with BundleRehearsal(args.workdir) as rehearsal:
        contracts = rehearsal.contracts()
        result = rehearsal.joint_recovery()
        receipt = dict(schema=1, result='ISOLATED_RECOVERY_BUNDLE_PASS', contracts=contracts,
            postgres=rehearsal.manifest['version'], crash_recovery='EXACT', current_restore='EXACT',
            stale_restore='REFUSED', activation='FORBIDDEN', production_writes=0,
            original_fixture='REMOVED_BEFORE_RESTORE', issuer_referral_authority='RECONSTRUCTED_FROM_BUNDLE',
            wrapping_key_and_trusted_checkpoint='RETAINED_IN_MEMORY_NOT_OFFHOST_RECOVERED',
            opaque_probe_roles=sorted(OPAQUE_PROBES), preflight=rehearsal.bundle_summary, **result)
    receipt['owned_container_cleanup'] = 'PASS'
    private_file(args.workdir / 'receipt.json', json.dumps(receipt, indent=2).encode())
    print(json.dumps(receipt, sort_keys=True))


if __name__ == '__main__':
    def terminate(signum, frame):
        raise SystemExit(128 + signum)
    signal.signal(signal.SIGTERM, terminate)
    main()
