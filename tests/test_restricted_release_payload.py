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


@pytest.mark.parametrize('fault', ['', 'native', 'manifest', 'source', 'dex'])
def test_exact_native_and_diagnostic_contract(tmp_path, fault):
    native = tmp_path / 'native.so'
    native.write_bytes(b'synthetic native')
    manifest = dict(binary_sha256=hashlib.sha256(native.read_bytes()).hexdigest(), xray_revision='d2758a023cd7f4174a5a5fa4ff66e487d4342ba0')
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
            module.inspect(apk, native, metadata)
    else:
        assert module.inspect(apk, native, metadata) == manifest
