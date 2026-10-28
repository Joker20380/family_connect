"""Package one immutable maintenance operation or an inert unbound source capsule."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import zipfile

from scripts.package_paid_canary_crl import ROOT, SOURCES as HELPER_SOURCES, PARSER_SOURCE, parser_projection
from control.friends.restricted_maintenance import encode, strict, validate_permit

SOURCES = (*HELPER_SOURCES, 'control/friends/restricted_maintenance.py', 'control/friends/profile_store.py')


def build(output, ref, *, permit=None, repository=ROOT):
    if permit is not None:
        validate_permit(permit)
    source = subprocess.check_output(['git', 'rev-parse', '--verify', '--end-of-options', ref + '^{commit}'], cwd=repository).decode().strip()
    content, projections = {}, {}
    for name in SOURCES:
        entry = subprocess.check_output(['git', 'ls-tree', source, '--', name], cwd=repository).decode()
        if not entry.startswith(('100644 blob ', '100755 blob ')):
            raise ValueError('Missing committed regular source')
        content[name] = subprocess.check_output(['git', 'show', source + ':' + name], cwd=repository)
        if name == PARSER_SOURCE:
            content[name], projections[name] = parser_projection(content[name])
    content['operation-permit.json'] = encode(permit)
    content['__main__.py'] = b'from control.friends.restricted_maintenance import main\nraise SystemExit(main())\n'
    for raw in content.values():
        if re.search(rb'\b(?:\d{1,3}\.){3}\d{1,3}\b|FC-[A-Z0-9]{4}-[A-Z0-9]{4}|-----BEGIN [A-Z ]*PRIVATE KEY|/opt/apps/', raw):
            raise ValueError('Operational data forbidden in capsule')
    for name in tuple(content):
        for parent in Path(name).parents:
            if parent != Path('.'):
                content[str(parent) + '/'] = b''
    manifest = dict(schema=1, source_commit=source, binding='unbound' if permit is None else 'single_operation',
        operation_permit=permit, production_configuration='absent', python_minimum='3.13',
        dependencies=['control/requirements.lock', 'device_identity/requirements.lock'],
        fixed_config_convention='root_owned_external_only', source_projections=projections,
        files={name: hashlib.sha256(raw).hexdigest() for name, raw in sorted(content.items())})
    content['source-manifest.json'] = encode(manifest)
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_STORED) as archive:
        for name, raw in sorted(content.items()):
            entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = (0o40755 if name.endswith('/') else 0o100644) << 16
            archive.writestr(entry, raw)
    return dict(source_commit=source, binding=manifest['binding'], sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
                size=output.stat().st_size, members=len(content), manifest_sha256=hashlib.sha256(content['source-manifest.json']).hexdigest())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ref', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--permit', type=Path)
    args = parser.parse_args()
    permit = strict(args.permit.read_bytes(), 8192, 'INVALID_PERMIT') if args.permit else None
    print(json.dumps(build(args.output, args.ref, permit=permit), sort_keys=True, allow_nan=False))


if __name__ == '__main__':
    main()
