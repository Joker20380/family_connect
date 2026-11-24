"""Owned full-store import/recovery with retained handoff floors; never activation."""
import argparse
import json
from pathlib import Path
import signal

from scripts.control_ha_handoff_fixture import closed_handoff_fixture
from scripts.control_ha_import_fixture import CHECKPOINT
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workdir', required=True, type=Path)
    args = parser.parse_args()
    with HandoffImportRehearsal(args.workdir) as rehearsal:
        contracts = rehearsal.contracts()
        result = rehearsal.joint_recovery()
        receipt = dict(schema=1, result='ISOLATED_CLOSED_HANDOFF_RETENTION_PASS', contracts=contracts,
            postgres=rehearsal.manifest['version'], crash_recovery='EXACT', current_restore='EXACT',
            stale_restore='REFUSED', old_import_after_writes='REFUSED', activation='FORBIDDEN', production_writes=0,
            handoff_runtime='NOT_IMPLEMENTED_RETAINED_READ_ONLY', live_barrier='NOT_IMPLEMENTED',
            external_recovery='NOT_QUALIFIED_KEYS_RETAINED', **result)
    receipt['owned_container_cleanup'] = 'PASS'
    private_file(args.workdir / 'receipt.json', json.dumps(receipt, indent=2).encode())
    print(json.dumps(receipt, sort_keys=True))


if __name__ == '__main__':
    def terminate(signum, frame):
        raise SystemExit(128 + signum)
    signal.signal(signal.SIGTERM, terminate)
    main()
