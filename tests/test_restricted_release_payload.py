import hashlib
import importlib.util
import json
from pathlib import Path
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('restricted_ci', ROOT / 'pilot/android-restricted/package_ci.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


@pytest.mark.parametrize('fault', ['', 'native', 'manifest', 'source', 'dex', 'revision', 'tags', 'producer', 'patch'])
def test_exact_native_and_diagnostic_contract(tmp_path, fault):
    native = tmp_path / 'native.so'
    native.write_bytes(b'synthetic native')
    revision = 'a' * 40
    manifest = dict(binary_sha256=hashlib.sha256(native.read_bytes()).hexdigest(),
                    xray_revision='d2758a023cd7f4174a5a5fa4ff66e487d4342ba0',
                    metadata_schema=2, source_revision=revision, source_tree='b' * 40,
                    provider='telemost', abi='arm64-v8a', build_tags=[], diagnostic_only=False,
                    owner_diagnostic_fault_schema=0,
                    builder_sha256=module.digest((ROOT / 'pilot/android-restricted/build.py').read_bytes()),
                    patch_sha256=module.digest((ROOT / 'pilot/android-restricted/xray-packet-boundary.patch').read_bytes()))
    if fault == 'revision':
        manifest['source_revision'] = 'c' * 40
    if fault == 'tags':
        manifest['build_tags'] = ['fc_owner_diagnostic']
    if fault == 'producer':
        manifest['builder_sha256'] = '0' * 64
    if fault == 'patch':
        manifest['patch_sha256'] = '0' * 64
    if fault == 'source':
        manifest['xray_revision'] = 'foreign'
    metadata = tmp_path / 'build.json'
    metadata.write_text(json.dumps(manifest))
    apk = tmp_path / 'test.apk'
    with zipfile.ZipFile(apk, 'w') as archive:
        archive.writestr('lib/arm64-v8a/libfc_restricted.so', b'stale native' if fault == 'native' else native.read_bytes())
        archive.writestr('assets/restricted-build.json', '{}' if fault == 'manifest' else metadata.read_bytes())
        archive.writestr('classes.dex', b'old contract' if fault == 'dex' else b'restricted_session')
    if fault:
        with pytest.raises(ValueError):
            module.inspect(apk, native, metadata, revision)
    else:
        assert module.inspect(apk, native, metadata, revision) == manifest
