"""Verify an unsigned source-bound ARM64 payload for later offline signing."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def inspect(apk, native, metadata):
    manifest = json.loads(metadata.read_bytes())
    with zipfile.ZipFile(apk) as archive:
        packaged = archive.read('lib/arm64-v8a/libfc_restricted.so')
        if packaged != native.read_bytes() or digest(packaged) != manifest['binary_sha256']:
            raise ValueError('Restricted native mismatch')
        if json.loads(archive.read('assets/restricted-build.json')) != manifest:
            raise ValueError('Restricted manifest mismatch')
        if manifest['xray_revision'] != 'd2758a023cd7f4174a5a5fa4ff66e487d4342ba0':
            raise ValueError('Unexpected Xray source')
        if not any(b'restricted_session' in archive.read(name) for name in archive.namelist() if name.endswith('.dex')):
            raise ValueError('Missing Android diagnostic contract')
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-commit', required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--apksigner', type=Path, required=True)
    args = parser.parse_args()
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    if not re.fullmatch('[0-9a-f]{40}', args.source_commit) or head != args.source_commit:
        raise ValueError('Source commit mismatch')
    subprocess.run(['git', 'diff', '--exit-code', 'HEAD', '--', 'carrier', 'clients/android', 'pilot/android-restricted'], cwd=ROOT, check=True)
    apk = ROOT / 'clients/android/app/build/outputs/apk/friends/app-friends-unsigned.apk'
    native = ROOT / 'clients/android/restricted-generated/jniLibs/arm64-v8a/libfc_restricted.so'
    native_manifest = inspect(apk, native, ROOT / 'clients/android/restricted-generated/assets/restricted-build.json')
    listing = json.loads((apk.parent / 'output-metadata.json').read_bytes())
    entry, = listing['elements']
    if listing['applicationId'] != 'com.familyconnect.app.friends' or entry['versionCode'] < 61:
        raise ValueError('Unexpected package/version')
    version = entry['versionName']
    if not re.fullmatch(r'0\.1\.18-beta[0-9]+', version) or int(version.split('beta')[1]) != entry['versionCode']:
        raise ValueError('Unexpected version name')
    verified = subprocess.run([str(args.apksigner), 'verify', str(apk)], capture_output=True, text=True)
    if verified.returncode == 0 or 'DOES NOT VERIFY' not in verified.stdout + verified.stderr:
        raise ValueError('Expected unsigned Friends APK')
    args.out.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, str(ROOT / 'pilot/android-awg/verify-apk.py'), '--apk', str(apk), '--abis', 'arm64-v8a', '--report', str(args.out / 'normal-native.json')], check=True)
    gateway = args.out / 'bootstrap-broker'
    if not gateway.is_file():
        raise ValueError('Gateway build missing')
    target = args.out / ('FamilyConnect-Test-' + version + '-unsigned.apk')
    if target.exists():
        raise ValueError('Immutable output exists')
    shutil.copyfile(apk, target)
    receipt = dict(source_commit=head, version=version, version_code=entry['versionCode'], package=listing['applicationId'],
                   apk_sha256=digest(target.read_bytes()), size=target.stat().st_size, unsigned=True,
                   restricted_native=native_manifest, gateway_sha256=digest(gateway.read_bytes()))
    (args.out / 'verification.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
