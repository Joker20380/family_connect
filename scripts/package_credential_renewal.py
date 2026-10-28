"""Deterministic accepted renewal sources and pinned shared API, without fixed configuration."""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import tarfile
import tempfile

from scripts.package_restricted_maintenance import ROOT, SOURCES as API_SOURCES, build as build_api

DIRECTORY = 'deploy/friends/restricted/maintenance'
MODULES = ('credential_renewal.py', 'expired_recovery.py', 'grant_cutover.py', 'maintenance_policy.py',
           'node.py', 'offline_handoff.py', 'production_controller.py', 'production_node.py',
           'production_transport.py', 'renewal_cli.py', 'renewal_health.py', 'runtime_controller.py',
           'scheduled_evaluate.py')
SOURCES = tuple(sorted(set(API_SOURCES) | {DIRECTORY + '/' + name for name in MODULES}))


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def build(output, ref, *, repository=ROOT):
    source = subprocess.check_output(['git', 'rev-parse', '--verify', '--end-of-options', ref + '^{commit}'], cwd=repository).decode().strip()
    content = {}
    for name in MODULES:
        path = DIRECTORY + '/' + name
        entry = subprocess.check_output(['git', 'ls-tree', source, '--', path], cwd=repository).decode()
        if not entry.startswith(('100644 blob ', '100755 blob ')):
            raise ValueError('Missing committed renewal source')
        raw = subprocess.check_output(['git', 'show', source + ':' + path], cwd=repository)
        if re.search(rb'\b(?:\d{1,3}\.){3}\d{1,3}\b|/opt/apps/|/home/|FC-[A-Z0-9]{4}-[A-Z0-9]{4}|-----BEGIN [A-Z ]*PRIVATE KEY', raw):
            raise ValueError('Operational data forbidden in renewal capsule')
        content['renewal/' + name] = raw
    with tempfile.TemporaryDirectory() as temporary:
        api = Path(temporary) / 'api.pyz'
        api_receipt = build_api(api, source, repository=repository)
        content['api.pyz'] = api.read_bytes()
    for name in ('LICENSE', 'THIRD_PARTY_NOTICES.md'):
        content[name] = subprocess.check_output(['git', 'show', source + ':' + name], cwd=repository)
    source_files = {name: digest(content['renewal/' + name]) for name in MODULES}
    manifest = dict(schema=1, source_commit=source, production_configuration='absent', operation_permit=None,
        binding='unbound', source_files=source_files, source_sha256=digest(encode(source_files)),
        api_sha256=api_receipt['sha256'], api_manifest_sha256=api_receipt['manifest_sha256'],
        files={name: digest(raw) for name, raw in sorted(content.items())})
    content['source-manifest.json'] = encode(manifest)
    with output.open('xb') as target:
        with gzip.GzipFile(filename='', fileobj=target, mode='wb', mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode='w', format=tarfile.USTAR_FORMAT) as archive:
                for name, raw in sorted(content.items()):
                    member = tarfile.TarInfo(name)
                    member.size = len(raw)
                    member.mode = 0o400 if name == 'api.pyz' else 0o600
                    archive.addfile(member, io.BytesIO(raw))
    return dict(source_commit=source, binding='unbound', source_sha256=manifest['source_sha256'],
        api_sha256=manifest['api_sha256'], manifest_sha256=digest(content['source-manifest.json']),
        sha256=digest(output.read_bytes()), size=output.stat().st_size, members=len(content))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ref', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.output, args.ref), sort_keys=True, allow_nan=False))


if __name__ == '__main__':
    main()
