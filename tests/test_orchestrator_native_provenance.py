import hashlib
import importlib.util
import json
from pathlib import Path
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('provenance', ROOT / 'pilot/android-restricted/provenance.py')
PROVENANCE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROVENANCE)


@pytest.mark.parametrize('mismatch', [None, 'tcp_source_sha256', 'tcp_jni_sha256', 'builder_sha256', 'source_revision', 'binary'])
def test_physical_acceptance_requires_current_sources_and_exact_binary(tmp_path, mismatch):
    manifest = {'source_revision': 'a' * 40, 'abis': {'arm64-v8a': hashlib.sha256(b'native').hexdigest()}}
    for field, filename in (
        ('tcp_source_sha256', 'pilot/android-tcp/tcp-android.go'),
        ('tcp_jni_sha256', 'pilot/android-tcp/tcp-jni.c'),
        ('builder_sha256', 'pilot/android-awg/build.py'),
    ):
        manifest[field] = hashlib.sha256((ROOT / filename).read_bytes()).hexdigest()
    if mismatch and mismatch != 'binary':
        manifest[mismatch] = 'stale'
    apk = tmp_path / 'test.apk'
    with zipfile.ZipFile(apk, 'w') as bundle:
        bundle.writestr('assets/awg-build.json', json.dumps(manifest))
        bundle.writestr('lib/arm64-v8a/libfc-awg.so', b'stale' if mismatch == 'binary' else b'native')
    if mismatch:
        with pytest.raises(RuntimeError):
            PROVENANCE.verify_normal(apk)
    else:
        assert PROVENANCE.verify_normal(apk)['source_revision'] == 'a' * 40
