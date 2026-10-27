"""Deterministic committed-source unbound CRL capsule, never an operational permit."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCES = (
    'control/friends/__init__.py', 'control/friends/paid_canary_crl.py',
    'control/friends/restricted_admin.py', 'control/friends/restricted.py', 'control/friends/readiness_receipts.py',
    'control/friends/paid_beta_canary.py', 'control/friends/paid_beta.py',
    'control/friends/support_ids.py', 'control/friends/access.py', 'control/requirements.lock',
    'device_identity/__init__.py', 'device_identity/device.py', 'device_identity/requirements.lock',
    'provisioning/__init__.py', 'provisioning/friends_catalog.py',
    'LICENSE', 'THIRD_PARTY_NOTICES.md',
)
PARSER_SOURCE = 'provisioning/friends_catalog.py'
PARSER_DEFINITIONS = ('require', 'unique', 'parse', 'fields', 'key')


def parser_projection(raw):
    text = raw.decode()
    tree = ast.parse(text)
    imports = [node for node in tree.body if isinstance(node, ast.Import) and
               len(node.names) == 1 and node.names[0].name in ('base64', 'json') and node.names[0].asname is None]
    definitions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in PARSER_DEFINITIONS]
    if len(imports) != 2 or tuple(node.name for node in definitions) != PARSER_DEFINITIONS:
        raise ValueError('Parser projection source contract changed')
    segments = [ast.get_source_segment(text, node) for node in imports + definitions]
    return ('\n\n'.join(segments) + '\n').encode(), dict(source_sha256=hashlib.sha256(raw).hexdigest(),
        imports=['base64', 'json'], definitions=list(PARSER_DEFINITIONS),
        segment_sha256=[hashlib.sha256(segment.encode()).hexdigest() for segment in segments])


def build(output, ref, *, repository=ROOT):
    source = subprocess.check_output(['git', 'rev-parse', '--verify', '--end-of-options', ref + '^{commit}'], cwd=repository).decode().strip()
    content = {}
    projections = {}
    for name in SOURCES:
        entry = subprocess.check_output(['git', 'ls-tree', source, '--', name], cwd=repository).decode()
        if not entry.startswith(('100644 blob ', '100755 blob ')):
            raise ValueError('Missing committed regular source')
        content[name] = subprocess.check_output(['git', 'show', source + ':' + name], cwd=repository)
        if name == PARSER_SOURCE:
            content[name], projections[name] = parser_projection(content[name])
    content['operation-permit.json'] = b'null'
    content['__main__.py'] = b'from control.friends.paid_canary_crl import main\nraise SystemExit(main())\n'
    for raw in content.values():
        if re.search(rb'\b(?:\d{1,3}\.){3}\d{1,3}\b|FC-[A-Z0-9]{4}-[A-Z0-9]{4}|-----BEGIN [A-Z ]*PRIVATE KEY|/opt/apps/|/etc/family', raw):
            raise ValueError('Operational data forbidden in unbound capsule')
    for name in tuple(content):
        for parent in Path(name).parents:
            if parent != Path('.'):
                content[str(parent) + '/'] = b''
    manifest = dict(schema=1, source_commit=source, binding='unbound', operation_permit=None,
        production_configuration='absent', python_minimum='3.13',
        dependencies=['control/requirements.lock', 'device_identity/requirements.lock'],
        source_projections=projections,
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
