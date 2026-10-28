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
import zipfile

from scripts.package_paid_canary_crl import ROOT, PARSER_SOURCE, parser_projection

DIRECTORY = 'deploy/friends/restricted/maintenance'
ACCEPTED_API_SOURCE = 'edca5447418141cb44c0706e26d1973d7defd397'
ACCEPTED_API_ARCHIVE = 'e986f98e70ff7f1abc2678566dd360bb6555583f2e1744ea985c63699bcb3ef7'
API_MEMBERS = {
    'control/friends/__init__.py': 'efb76720b2ad1c9594aee9488b342e3311ed01a4bff3082c2fa3999663354cc8',
    'control/friends/restricted.py': '3f8613a92d1b26e6dc4d7d9e2f05ff6e87d4a8e3482580db0a7745058b48ae09',
    'control/friends/access.py': '081a7c5a8f8880f13f6ce7b23b32b77de2c50af13654c9a9530de935af5b0c87',
    'control/friends/readiness_receipts.py': '16e4556af6d914e7411b3563bef44efebd2a8ba2d7dda1d0faa4f4e100ceb660',
    'control/friends/support_ids.py': 'cab3cef66085ac11253d3ce8a41d636769f040841fe839a96e03e536939aa169',
    'device_identity/__init__.py': '3cd56edaf5fbfde9c88df7078dc55be15bf23cfc830727ee410bc8f31dc9990f',
    'device_identity/device.py': '38e29e640c913c1331164aa36fde0ca95b1d13ee057ae92c3d31ec7b993151d3',
    'provisioning/__init__.py': 'a8d11b35f8be63395d505bcf0cf7774aa5c0dbffa5eee905eef911a8d3fdb905',
    'provisioning/friends_catalog.py': 'add970991089003c7b4589e8dbb135d56e63a601b5530c939f4b6ab8b964bebe',
}
API_ADDITIONS = ('control/friends/profile_store.py', 'control/requirements.lock', 'device_identity/requirements.lock',
                 'LICENSE', 'THIRD_PARTY_NOTICES.md')
MODULES = ('credential_renewal.py', 'expired_recovery.py', 'grant_cutover.py', 'maintenance_policy.py',
           'node.py', 'offline_handoff.py', 'production_controller.py', 'production_node.py',
           'production_transport.py', 'renewal_cli.py', 'renewal_health.py', 'runtime_controller.py',
           'scheduled_evaluate.py')
SOURCES = tuple(sorted(set(API_MEMBERS) | set(API_ADDITIONS) | {DIRECTORY + '/' + name for name in MODULES}))


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def committed(repository, source, path):
    entry = subprocess.check_output(['git', 'ls-tree', source, '--', path], cwd=repository).decode()
    if not entry.startswith(('100644 blob ', '100755 blob ')):
        raise ValueError('Missing committed renewal source')
    return subprocess.check_output(['git', 'show', source + ':' + path], cwd=repository)


def profile_api(repository, source, api_source):
    content, projections = {}, {}
    for name, expected in API_MEMBERS.items():
        raw = committed(repository, api_source, name)
        if digest(raw) != expected:
            raise ValueError('Accepted renewal API source mismatch')
        if name == PARSER_SOURCE:
            raw, projections[name] = parser_projection(raw)
        content[name] = raw
    for name in API_ADDITIONS:
        content[name] = committed(repository, source, name)
    content['__main__.py'] = b'print("Pinned renewal API library; no runtime commands or production configuration")\n'
    for raw in content.values():
        if re.search(rb'\b(?:\d{1,3}\.){3}\d{1,3}\b|/opt/apps/|/home/|FC-[A-Z0-9]{4}-[A-Z0-9]{4}|-----BEGIN [A-Z ]*PRIVATE KEY', raw):
            raise ValueError('Operational data forbidden in renewal API')
    for name in tuple(content):
        for parent in Path(name).parents:
            if parent != Path('.'):
                content[str(parent) + '/'] = b''
    manifest = dict(schema=1, source_commit=source, accepted_api_source_commit=api_source,
        accepted_api_archive_sha256=ACCEPTED_API_ARCHIVE, accepted_members=API_MEMBERS,
        source_projections=projections, production_configuration='absent', operation_permit=None,
        files={name: digest(raw) for name, raw in sorted(content.items())})
    content['source-manifest.json'] = encode(manifest)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_STORED) as archive:
        for name, raw in sorted(content.items()):
            entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = (0o40755 if name.endswith('/') else 0o100644) << 16
            archive.writestr(entry, raw)
    return buffer.getvalue(), digest(content['source-manifest.json'])


def build(output, ref, *, repository=ROOT, api_ref=ACCEPTED_API_SOURCE):
    source = subprocess.check_output(['git', 'rev-parse', '--verify', '--end-of-options', ref + '^{commit}'], cwd=repository).decode().strip()
    api_source = subprocess.check_output(['git', 'rev-parse', '--verify', '--end-of-options', api_ref + '^{commit}'], cwd=repository).decode().strip()
    content = {}
    for name in MODULES:
        path = DIRECTORY + '/' + name
        raw = committed(repository, source, path)
        if re.search(rb'\b(?:\d{1,3}\.){3}\d{1,3}\b|/opt/apps/|/home/|FC-[A-Z0-9]{4}-[A-Z0-9]{4}|-----BEGIN [A-Z ]*PRIVATE KEY', raw):
            raise ValueError('Operational data forbidden in renewal capsule')
        content['renewal/' + name] = raw
    content['api.pyz'], api_manifest_sha256 = profile_api(repository, source, api_source)
    for name in ('LICENSE', 'THIRD_PARTY_NOTICES.md'):
        content[name] = subprocess.check_output(['git', 'show', source + ':' + name], cwd=repository)
    source_files = {name: digest(content['renewal/' + name]) for name in MODULES}
    manifest = dict(schema=1, source_commit=source, production_configuration='absent', operation_permit=None,
        binding='unbound', source_files=source_files, source_sha256=digest(encode(source_files)),
        api_sha256=digest(content['api.pyz']), api_manifest_sha256=api_manifest_sha256,
        accepted_api_source_commit=api_source, accepted_api_archive_sha256=ACCEPTED_API_ARCHIVE,
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
