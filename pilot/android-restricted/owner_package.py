"""Inspect owner-only packaging without installing or invoking fault control."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def inspect(owner, friends, generated, revision, native_build_info, owner_manifest, friends_manifest):
    metadata = json.loads((generated / 'assets/restricted-build.json').read_bytes())
    if metadata['source_revision'] != revision or metadata['owner_diagnostic_fault_schema'] != 1:
        raise ValueError('P6: source revision/schema mismatch')
    if '-tags=fc_owner_diagnostic' not in native_build_info:
        raise ValueError('P3: missing diagnostic native build tag')
    if 'vcs.modified=true' in native_build_info:
        raise ValueError('P6: native source was dirty')
    if f'vcs.revision={revision}' not in native_build_info:
        raise ValueError('P6: native VCS revision mismatch')
    if 'com.familyconnect.app.OwnerFaultReceiver' not in owner_manifest or 'android.permission.DUMP' not in owner_manifest:
        raise ValueError('P3: protected owner receiver missing')
    if 'OwnerFaultReceiver' in friends_manifest:
        raise ValueError('P2: public receiver leaked')
    native = generated / 'jniLibs/arm64-v8a/libfc_restricted.so'
    expected_assets = {'assets/' + str(path.relative_to(generated / 'assets')): path.read_bytes()
                       for path in (generated / 'assets').rglob('*') if path.is_file()}
    with zipfile.ZipFile(owner) as owner_zip, zipfile.ZipFile(friends) as friends_zip:
        names = owner_zip.namelist()
        if len(names) != len(set(names)):
            raise ValueError('Duplicate APK entries')
        libraries = sorted(name for name in names if name.startswith('lib/') and name.endswith('.so'))
        if {name.split('/')[1] for name in libraries} != {'arm64-v8a'}:
            raise ValueError('P5: unexpected ABI')
        expected_libraries = {name for name in friends_zip.namelist() if name.startswith('lib/') and name.endswith('.so')}
        if set(libraries) != expected_libraries:
            raise ValueError('P5: native library surface differs from Friends')
        packaged = owner_zip.read('lib/arm64-v8a/libfc_restricted.so')
        if packaged != native.read_bytes() or digest(packaged) != metadata['binary_sha256']:
            raise ValueError('P4: JNI mismatch')
        for name in libraries:
            if not name.endswith('/libfc_restricted.so') and owner_zip.read(name) != friends_zip.read(name):
                raise ValueError('P5: unrelated native library drift')
        actual_assets = {name for name in names if name.startswith('assets/restricted') and not name.endswith('/')}
        if actual_assets != set(expected_assets):
            raise ValueError('P7: restricted asset surface mismatch')
        for name, raw in expected_assets.items():
            if owner_zip.read(name) != raw:
                raise ValueError('P7: restricted asset byte mismatch')
        public_metadata = json.loads(friends_zip.read('assets/restricted-build.json'))
        if public_metadata.get('owner_diagnostic_fault_schema', 0) != 0:
            raise ValueError('P2: diagnostic JNI metadata leaked into Friends')
        if any(b'OwnerFaultReceiver' in friends_zip.read(name) for name in friends_zip.namelist() if name.endswith('.dex')):
            raise ValueError('P2: diagnostic class leaked into Friends')
        if not any(b'OwnerFaultReceiver' in owner_zip.read(name) for name in names if name.endswith('.dex')):
            raise ValueError('P3: owner class missing')
    return dict(result='PASS', gates={f'P{number}': 'PASS' for number in range(1, 8)},
                source_revision=revision, jni_sha256=digest(packaged), libraries=libraries,
                assets={name: digest(raw) for name, raw in expected_assets.items()},
                apk_sha256=digest(owner.read_bytes()))


def main():
    parser = argparse.ArgumentParser()
    for name in ('owner', 'friends', 'generated', 'aapt', 'go', 'report'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--revision', required=True)
    args = parser.parse_args()
    def manifest(apk):
        return subprocess.check_output([str(args.aapt), 'dump', 'xmltree', str(apk), 'AndroidManifest.xml'], text=True)
    native_info = subprocess.check_output([str(args.go), 'version', '-m', str(args.generated / 'jniLibs/arm64-v8a/libfc_restricted.so')], text=True)
    result = inspect(args.owner, args.friends, args.generated, args.revision, native_info,
                     manifest(args.owner), manifest(args.friends))
    args.report.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
