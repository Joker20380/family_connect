"""Build an immutable single-canary permit archive from explicit committed sources."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

from control.friends.paid_beta_canary import strict_json, validate_envelope

ROOT = Path(__file__).resolve().parents[1]
SOURCES = (
    'control/friends/__init__.py', 'control/friends/paid_beta_canary.py',
    'control/friends/paid_beta.py', 'control/friends/support_ids.py', 'control/friends/access.py',
    'device_identity/__init__.py', 'device_identity/device.py', 'device_identity/requirements.lock', 'LICENSE',
)


def build(output, ref, envelope=None, *, repository=ROOT):
    if envelope is not None:
        validate_envelope(envelope)
    commit = subprocess.check_output(['git', 'rev-parse', '--verify', '--end-of-options', ref + '^{commit}'], cwd=repository).decode().strip()
    content = {}
    for name in SOURCES:
        entry = subprocess.check_output(['git', 'ls-tree', commit, '--', name], cwd=repository).decode()
        if not entry.startswith(('100644 blob ', '100755 blob ')):
            raise ValueError('Missing committed regular source')
        content[name] = subprocess.check_output(['git', 'show', commit + ':' + name], cwd=repository)
    content['canary-envelope.json'] = json.dumps(envelope, sort_keys=True, allow_nan=False).encode()
    content['__main__.py'] = (
        'import sys, zipfile\n'
        'from control.friends.paid_beta_canary import main, strict_json\n'
        'with zipfile.ZipFile(sys.argv[0]) as archive:\n'
        '    envelope = strict_json(archive.read("canary-envelope.json"))\n'
        'raise SystemExit(main(envelope=envelope))\n').encode()
    for name in tuple(content):
        for parent in Path(name).parents:
            if parent != Path('.'):
                content[str(parent) + '/'] = b''
    manifest = dict(schema=1, source_commit=commit, binding='single_canary' if envelope else 'lookup_only',
                    python_minimum='3.13', dependencies='device_identity/requirements.lock',
                    files={name: hashlib.sha256(raw).hexdigest() for name, raw in sorted(content.items())})
    content['source-manifest.json'] = json.dumps(manifest, sort_keys=True, allow_nan=False).encode()
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_STORED) as archive:
        for name, raw in sorted(content.items()):
            entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = (0o40755 if name.endswith('/') else 0o100644) << 16
            archive.writestr(entry, raw)
    return dict(source_commit=commit, sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
                size=output.stat().st_size, members=len(content), binding=manifest['binding'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ref', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--envelope', type=Path)
    args = parser.parse_args()
    envelope = strict_json(args.envelope.read_bytes()) if args.envelope else None
    print(json.dumps(build(args.output, args.ref, envelope), sort_keys=True, allow_nan=False))


if __name__ == '__main__':
    main()
