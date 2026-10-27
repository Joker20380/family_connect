"""Deterministic committed-source unbound CRL capsule, never an operational permit."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCES = (
    'control/friends/__init__.py', 'control/friends/paid_canary_crl.py',
    'control/friends/restricted_admin.py', 'control/friends/restricted.py', 'control/friends/readiness_receipts.py',
    'control/friends/paid_beta_canary.py', 'control/friends/paid_beta.py',
    'control/friends/support_ids.py', 'control/friends/access.py', 'control/requirements.lock',
    'device_identity/__init__.py', 'device_identity/device.py', 'device_identity/requirements.lock',
    'provisioning/__init__.py', 'provisioning/friends_catalog.py', 'clients/desktop/profile_config.py',
    'LICENSE', 'THIRD_PARTY_NOTICES.md',
)


def build(output, ref, *, repository=ROOT):
    source = subprocess.check_output(['git', 'rev-parse', '--verify', '--end-of-options', ref + '^{commit}'], cwd=repository).decode().strip()
    content = {}
    for name in SOURCES:
        entry = subprocess.check_output(['git', 'ls-tree', source, '--', name], cwd=repository).decode()
        if not entry.startswith(('100644 blob ', '100755 blob ')):
            raise ValueError('Missing committed regular source')
        content[name] = subprocess.check_output(['git', 'show', source + ':' + name], cwd=repository)
    content['operation-permit.json'] = b'null'
    content['__main__.py'] = b'from control.friends.paid_canary_crl import main\nraise SystemExit(main())\n'
    for name in tuple(content):
        for parent in Path(name).parents:
            if parent != Path('.'):
                content[str(parent) + '/'] = b''
    manifest = dict(schema=1, source_commit=source, binding='unbound', operation_permit=None,
        production_configuration='absent', python_minimum='3.13',
        dependencies=['control/requirements.lock', 'device_identity/requirements.lock'],
        files={name: hashlib.sha256(raw).hexdigest() for name, raw in sorted(content.items())})
    content['source-manifest.json'] = json.dumps(manifest, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_STORED) as archive:
        for name, raw in sorted(content.items()):
            entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = (0o40755 if name.endswith('/') else 0o100644) << 16
            archive.writestr(entry, raw)
    return dict(source_commit=source, binding='unbound', sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
                size=output.stat().st_size, members=len(content), manifest_sha256=hashlib.sha256(content['source-manifest.json']).hexdigest())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ref', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.output, args.ref), sort_keys=True, allow_nan=False))


if __name__ == '__main__':
    main()
