"""Deterministic, committed-source paid boundary; never deploys or opens a registry."""
import argparse
import ast
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile
import zipfile

from scripts.package_friends_http import build as build_http
from scripts.package_support_operator import build as build_operator

ROOT = Path(__file__).resolve().parents[1]
MANIFESTS = ('http-runtime-files.json', 'runtime-files.json', 'readiness-runtime-files.json')
RUNTIME = dict(python='3.14.4', distributions={
    'cffi': '2.1.1', 'cryptography': '46.0.7', 'pycparser': '3.0', 'pyserial': '3.5', 'rns': '1.5.1'})
PAID_DELTA = frozenset({'control/friends/restricted.py', 'control/friends/paid_beta.py'})


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def committed(ref, name):
    path = Path(name)
    if path.is_absolute() or '..' in path.parts:
        raise ValueError('Unsafe source path')
    entry = subprocess.check_output(['git', 'ls-tree', ref, '--', name], cwd=ROOT).decode()
    if not entry.startswith('100644 blob ') and not entry.startswith('100755 blob '):
        raise ValueError('Source must be a committed regular file: ' + name)
    return subprocess.check_output(['git', 'show', f'{ref}:{name}'], cwd=ROOT)


def normalized_zip(raw):
    output = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(raw)) as original, zipfile.ZipFile(output, 'w') as archive:
        for entry in sorted(original.infolist(), key=lambda item: item.filename):
            entry.date_time = (1980, 1, 1, 0, 0, 0)
            entry.create_system = 3
            entry.external_attr = (0o40755 if entry.is_dir() else 0o100644) << 16
            archive.writestr(entry, original.read(entry))
    return output.getvalue()


def imports(raw):
    result = set()
    for node in ast.walk(ast.parse(raw)):
        if isinstance(node, ast.Import):
            result.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            result.add('.' * node.level + (node.module or '') + ':' + ','.join(alias.name for alias in node.names))
    return sorted(result)


def archive_hashes(path):
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError('Duplicate runtime member')
        if any(Path(name).is_absolute() or '..' in Path(name).parts for name in names):
            raise ValueError('Unsafe runtime member')
        return {name: digest(archive.read(name)) for name in sorted(names) if not name.endswith('/')}


def unique_fields(items):
    result = {}
    for name, value in items:
        if name in result:
            raise ValueError('Duplicate baseline field')
        result[name] = value
    return result


def source_gate(served, candidate, baseline=None):
    before, after = archive_hashes(served), archive_hashes(candidate)
    changed = sorted(name for name in before.keys() | after.keys() if before.get(name) != after.get(name))
    unexpected = [name for name in changed if name not in PAID_DELTA]
    removed = sorted(before.keys() - after.keys())
    valid = not unexpected and not removed and 'control/friends/paid_beta.py' in after
    baseline_hash = None
    if baseline is not None:
        raw = Path(baseline).read_bytes()
        contract = json.loads(raw, object_pairs_hook=unique_fields,
            parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Nonfinite baseline field')))
        if (type(contract) is not dict or set(contract) != {'schema', 'review', 'input_commit', 'served', 'candidate', 'resolutions'}
                or type(contract['schema']) is not int or contract['schema'] != 1):
            raise ValueError('Invalid served baseline contract')
        baseline_hash = digest(raw)
        valid = (contract['served'] == dict(sha256=digest(Path(served).read_bytes()), size=Path(served).stat().st_size, members=before)
            and contract['candidate'] == dict(sha256=digest(Path(candidate).read_bytes()), size=Path(candidate).stat().st_size, members=after)
            and not removed and 'control/friends/paid_beta.py' in after)
        unexpected = [] if valid else unexpected
    return dict(result='PASS' if valid else 'BLOCKED_SERVED_SOURCE_DRIFT',
        served_sha256=digest(Path(served).read_bytes()), candidate_sha256=digest(Path(candidate).read_bytes()),
        changed=changed, unexpected=unexpected, removed=removed, baseline_sha256=baseline_hash,
        boundary='Necessary source delta gate only; not deployment or behavioral acceptance')


def build(output, ref='HEAD'):
    ref = subprocess.check_output(['git', 'rev-parse', '--verify', ref + '^{commit}'], cwd=ROOT).decode().strip()
    contract = 'deploy/friends/restricted/'
    sources = {}
    for name in MANIFESTS:
        location = contract + name
        sources[location] = committed(ref, location)
        manifest = json.loads(sources[location])
        names = manifest.values() if isinstance(manifest, dict) else manifest
        for member in names:
            if Path(member).suffix != '.py':
                raise ValueError('Runtime manifests may contain Python source only')
            sources[member] = committed(ref, member)
    for name in ('deploy/friends/access-api.py', 'control/friends/support_admin.py',
                 'control/friends/restricted_admin.py', 'control/requirements.lock',
                 'device_identity/requirements.lock', 'scripts/friends_http_acceptance.py',
                 'control_plane/apps/console/collector.py', 'LICENSE', 'THIRD_PARTY_NOTICES.md',
                 'deploy/friends/restricted/served-baseline.json',
                 'clients/android/app/src/main/assets/control-licenses/Reticulum.txt',
                 'clients/android/app/src/main/assets/control-licenses/PySerial.txt'):
        sources[name] = committed(ref, name)
    templates = {contract + name: committed(ref, contract + name) for name in
                 ('http-runtime.conf', 'access.conf', 'nginx-location.conf')}
    with tempfile.TemporaryDirectory() as directory:
        temporary = Path(directory)
        source = temporary / 'source'
        for name, raw in (sources | templates).items():
            destination = source / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(raw)
        http = temporary / 'http'
        build_http(http, source=source)
        operator = temporary / 'paid-beta.pyz'
        build_operator(operator, source=source, operator='paid-beta')
        with zipfile.ZipFile(operator) as original:
            sync = io.BytesIO()
            with zipfile.ZipFile(sync, 'w') as archive:
                for entry in original.infolist():
                    raw = (b'from control.friends.restricted_sync import main\nmain()\n'
                           if entry.filename == '__main__.py' else original.read(entry))
                    archive.writestr(entry, raw)
        payload = {'artifacts/friends-http.pyz': (http / 'friends-http.pyz').read_bytes(),
            'artifacts/paid-beta.pyz': operator.read_bytes(), 'artifacts/restricted-sync.pyz': normalized_zip(sync.getvalue())}
    payload.update({'source/' + name: raw for name, raw in sources.items()})
    payload['runtime.json'] = encoded(dict(**RUNTIME, dependency_install='NOT_PERFORMED',
        closure='Existing host runtime, not vendored; verify versions and isolated imports before deployment'))
    payload['imports.json'] = encoded({name: imports(raw) for name, raw in sources.items() if name.endswith('.py')})
    payload['inventory.json'] = encoded(dict(schema=1, source_commit=ref,
        builder_sha256=digest(Path(__file__).read_bytes()),
        files={name: dict(size=len(raw), sha256=digest(raw)) for name, raw in sorted(payload.items())}))
    output = Path(output)
    with output.open('xb') as handle, tarfile.open(fileobj=handle, mode='w', format=tarfile.USTAR_FORMAT) as archive:
        for name, raw in sorted(payload.items()):
            entry = tarfile.TarInfo(name)
            entry.size, entry.mode = len(raw), 0o644
            archive.addfile(entry, io.BytesIO(raw))
    checksum = digest(output.read_bytes())
    return dict(schema=1, bundle_id='paid-boundary-' + checksum, source_commit=ref,
        member_count=len(payload), size=output.stat().st_size, sha256=checksum, runtime=RUNTIME)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    package = commands.add_parser('build')
    package.add_argument('--output', type=Path, required=True)
    package.add_argument('--ref', default='HEAD')
    check = commands.add_parser('source-gate')
    check.add_argument('--served', type=Path, required=True)
    check.add_argument('--candidate', type=Path, required=True)
    check.add_argument('--baseline', type=Path)
    args = parser.parse_args()
    result = build(args.output, args.ref) if args.command == 'build' else source_gate(args.served, args.candidate, args.baseline)
    print(encoded(result).decode(), end='')
    return int(result.get('result', 'PASS') != 'PASS')


if __name__ == '__main__':
    raise SystemExit(main())
