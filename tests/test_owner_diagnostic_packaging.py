import importlib.util
import json
from pathlib import Path
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('owner_package', ROOT / 'pilot/android-restricted/owner_package.py')
package = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package)


def fixture(tmp_path, defect=None):
    generated = tmp_path / 'generated'
    native = generated / 'jniLibs/arm64-v8a/libfc_restricted.so'
    native.parent.mkdir(parents=True)
    native.write_bytes(b'accepted-native')
    assets = generated / 'assets'
    assets.mkdir()
    metadata = dict(source_revision='a' * 40, owner_diagnostic_fault_schema=1,
                    binary_sha256=package.digest(native.read_bytes()))
    (assets / 'restricted-build.json').write_text(json.dumps(metadata))
    owner_entries = {'lib/arm64-v8a/libfc_restricted.so': native.read_bytes(),
                     'assets/restricted-build.json': (assets / 'restricted-build.json').read_bytes(),
                     'classes.dex': b'OwnerFaultReceiver'}
    public_entries = owner_entries | {'classes.dex': b'ordinary', 'assets/restricted-build.json': b'{"owner_diagnostic_fault_schema":0}'}
    if defect == 'hash':
        owner_entries['lib/arm64-v8a/libfc_restricted.so'] = b'stale'
    if defect == 'abi':
        owner_entries['lib/x86/libfc_restricted.so'] = b'other'
    if defect == 'asset':
        owner_entries['assets/restricted-secret.json'] = b'not-allowed'
    if defect == 'public':
        public_entries['classes.dex'] = b'OwnerFaultReceiver'
    for name, entries in [('owner', owner_entries), ('friends', public_entries)]:
        with zipfile.ZipFile(tmp_path / (name + '.apk'), 'w') as archive:
            for entry, raw in entries.items():
                archive.writestr(entry, raw)
    return (tmp_path / 'owner.apk', tmp_path / 'friends.apk', generated,
            'b' * 40 if defect == 'revision' else 'a' * 40,
            '-tags=fc_owner_diagnostic\nvcs.revision=' + 'a' * 40 + ('\nvcs.modified=true' if defect == 'dirty' else ''),
            'com.familyconnect.app.OwnerFaultReceiver android.permission.DUMP', 'ordinary')


def test_exact_owner_package(tmp_path):
    assert package.inspect(*fixture(tmp_path))['result'] == 'PASS'


@pytest.mark.parametrize('defect', ['hash', 'abi', 'asset', 'public', 'revision', 'dirty'])
def test_owner_package_rejects_drift(tmp_path, defect):
    with pytest.raises(ValueError):
        package.inspect(*fixture(tmp_path, defect))


def test_source_set_isolation():
    gradle = (ROOT / 'clients/android/app/build.gradle').read_text()
    assert "fcOwnerRestrictedDirectory" in gradle
    assert "sourceSets { friends { jniLibs.srcDir '../restricted-generated/jniLibs'" in gradle
    assert "sourceSets { ownerDiagnostic {" in gradle
    owner_manifest = ROOT / 'clients/android/app/src/ownerDiagnostic/AndroidManifest.xml'
    assert 'android.permission.DUMP' in owner_manifest.read_text()
    for manifest in (ROOT / 'clients/android/app/src').glob('*/AndroidManifest.xml'):
        if manifest != owner_manifest:
            assert 'OwnerFaultReceiver' not in manifest.read_text()
