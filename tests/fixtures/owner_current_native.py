"""Actual new image against disposable synthetic custody, never installed data."""
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests'))

from scripts import control_ha_owner_runtime_current as current
from scripts.control_ha_owner_qualify import qualify
from test_control_ha_owner_runtime import source, bundle
from test_control_ha_owner_runtime_current import current_bundle


def run():
    with tempfile.TemporaryDirectory(prefix='fc-owner-current-native-') as directory:
        root = Path(directory)
        synthetic = source.__wrapped__(root)
        previous = bundle.__wrapped__(synthetic)
        value = current_bundle.__wrapped__(previous)
        key = os.urandom(32)
        capsule, checkpoint = current.seal(value, key)
        verified = current.unseal(capsule, key, checkpoint)
        assert verified == value
        receipt = qualify(verified, root / 'restored', baseline=current.BASELINE)
        expected = current.manifest()['image_sources']
        assert receipt['source_sha256']['apps.console.backend'] == expected['control_plane/apps/console/backend.py']
        assert receipt['source_sha256']['apps.console.system_publisher'] == expected['control_plane/apps/console/system_publisher.py']
        assert receipt['dispatch_calls'] == 0 and receipt['database_unchanged'] is True
        return dict(result='CURRENT_OWNER_NATIVE_CUSTODY_PASS', native=receipt,
                    baseline=current.BASELINE, synthetic_only=True, installed_data_read=False,
                    historical_markers_changed=False, capture_permitted=False, external_work_settled=False)


if __name__ == '__main__':
    print(json.dumps(run(), sort_keys=True))
