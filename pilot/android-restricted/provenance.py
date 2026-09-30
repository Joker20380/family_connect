"""Reject cached normal JNI artifacts before physical acceptance starts."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]


def verify_normal(apk, root=ROOT):
    with zipfile.ZipFile(apk) as bundle:
        manifest = json.loads(bundle.read('assets/awg-build.json'))
        for field, filename in (
            ('tcp_source_sha256', 'pilot/android-tcp/tcp-android.go'),
            ('tcp_jni_sha256', 'pilot/android-tcp/tcp-jni.c'),
            ('builder_sha256', 'pilot/android-awg/build.py'),
        ):
            expected = hashlib.sha256((root / filename).read_bytes()).hexdigest()
            if manifest.get(field) != expected:
                raise RuntimeError('normal native source mismatch: ' + field)
        revision = manifest.get('source_revision', '')
        if len(revision) != 40 or any(char not in '0123456789abcdef' for char in revision):
            raise RuntimeError('normal native source revision missing')
        digest = hashlib.sha256(bundle.read('lib/arm64-v8a/libfc-awg.so')).hexdigest()
        if manifest['abis'].get('arm64-v8a') != digest:
            raise RuntimeError('normal native packaged binary mismatch')
        return {'source_revision': revision, 'native_sha256': digest,
                'apk_sha256': hashlib.sha256(Path(apk).read_bytes()).hexdigest(),
                'tcp_source_sha256': manifest['tcp_source_sha256'],
                'builder_sha256': manifest['builder_sha256']}
