"""Separate default-off online runtime, built only from one committed source export."""
import argparse
import gzip
import io
import json
import os
from pathlib import Path
import re
import subprocess
import tarfile
import tempfile
import zipfile

from scripts.package_credential_renewal import ROOT, DIRECTORY, MODULES, API_MEMBERS, API_ADDITIONS, committed, digest, encode


CONTRACT = 'MESH_SAME_HOLDER_ONLINE_V1'
PACKAGE = 'MESH_ONLINE_RUNTIME_V1'
ONLINE_MODULES = (*MODULES, 'online_runtime.py', 'online_cli.py')
API_SOURCES = tuple(sorted(set(API_MEMBERS) | set(API_ADDITIONS) | {
    'control/friends/paid_beta.py', 'clients/desktop/profile_config.py'}))
SOURCES = (*API_SOURCES, *(DIRECTORY+'/'+name for name in ONLINE_MODULES))


def library(repository, source):
    content = {name: committed(repository, source, name) for name in API_SOURCES}
    content['__main__.py'] = b'print("Online renewal API library; external opt-in configuration required")\n'
    return archive_library(content, source)


def archive_library(content, source):
    for name in tuple(content):
        for parent in Path(name).parents:
            if parent != Path('.'):
                content[str(parent)+'/'] = b''
    manifest = dict(package_contract=PACKAGE, online_contract=CONTRACT, source_commit=source,
                    files={name: digest(raw) for name, raw in sorted(content.items())})
    content['source-manifest.json'] = encode(manifest)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_STORED) as archive:
        for name, raw in sorted(content.items()):
            entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = (0o40755 if name.endswith('/') else 0o100644) << 16
            archive.writestr(entry, raw)
    return buffer.getvalue()


def http_runtime(repository, source):
    mapping = json.loads(committed(repository, source, 'deploy/friends/restricted/http-runtime-files.json'))
    if type(mapping) is not list or len(mapping) != len(set(mapping)):
        raise ValueError('Invalid HTTP inventory')
    content = {}
    for name in mapping:
        if type(name) is not str or Path(name).is_absolute() or '..' in Path(name).parts or not name.endswith('.py'):
            raise ValueError('Invalid HTTP source')
        content[name] = committed(repository, source, name)
    content['friends_http.py'] = committed(repository, source, 'deploy/friends/access-api.py')
    content['__main__.py'] = b'from friends_http import main\nmain()\n'
    return archive_library(content, source)


def build(output, ref, *, go, repository=ROOT):
    if output.exists():
        raise FileExistsError(output)
    source = subprocess.check_output(['git', 'rev-parse', '--verify', '--end-of-options', ref+'^{commit}'],
                                     cwd=repository, text=True).strip()
    content = {'renewal/'+name: committed(repository, source, DIRECTORY+'/'+name) for name in ONLINE_MODULES}
    content['api.pyz'] = library(repository, source)
    content['http.pyz'] = http_runtime(repository, source)
    native = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', source, '--', 'carrier'],
                                     cwd=repository, text=True).splitlines()
    native = [name for name in native if name.endswith(('.go', '/go.mod', '/go.sum'))]
    inventory = {}
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        for name in native:
            raw = committed(repository, source, name)
            inventory[name] = digest(raw)
            path = root/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        environment = dict(os.environ, CGO_ENABLED='0', GOTOOLCHAIN='local', GOOS='linux', GOARCH='amd64', GOFLAGS='')
        subprocess.run([str(go), 'build', '-mod=readonly', '-trimpath', '-buildvcs=false', '-ldflags=-buildid=',
                        '-o', str(root/'gateway'), './cmd/bootstrap-broker'], cwd=root/'carrier', env=environment, check=True)
        content['gateway'] = (root/'gateway').read_bytes()
        toolchain = subprocess.check_output([str(go), 'version'], text=True, env=environment).strip()
    for name in ('LICENSE', 'THIRD_PARTY_NOTICES.md', 'control/requirements.lock', 'device_identity/requirements.lock'):
        content[name] = committed(repository, source, name)
    for name, raw in content.items():
        if name.startswith('renewal/') and re.search(rb'-----BEGIN [A-Z ]*PRIVATE KEY|/opt/apps/|FC-[A-Z0-9]{4}-[A-Z0-9]{4}', raw):
            raise ValueError('Operational data forbidden in online runtime')
    sources = {name: digest(content['renewal/'+name]) for name in ONLINE_MODULES}
    manifest = dict(schema=1, package_contract=PACKAGE, online_contract=CONTRACT, source_commit=source,
        binding='unbound', production_configuration='absent', operation_permit=None, default_online=False,
        source_files=sources, source_sha256=digest(encode(sources)), api_sha256=digest(content['api.pyz']),
        http_sha256=digest(content['http.pyz']),
        gateway_sha256=digest(content['gateway']), gateway_target='linux/amd64', go=toolchain,
        native_sources=inventory, files={name: digest(raw) for name, raw in sorted(content.items())})
    content['source-manifest.json'] = encode(manifest)
    with output.open('xb') as target:
        with gzip.GzipFile(filename='', fileobj=target, mode='wb', mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode='w', format=tarfile.USTAR_FORMAT) as archive:
                for name, raw in sorted(content.items()):
                    member = tarfile.TarInfo(name)
                    member.size = len(raw)
                    member.mode = 0o700 if name == 'gateway' else 0o600
                    archive.addfile(member, io.BytesIO(raw))
    return {name: manifest[name] for name in ('source_commit', 'source_sha256', 'api_sha256', 'http_sha256', 'gateway_sha256')} | dict(
        sha256=digest(output.read_bytes()), manifest_sha256=digest(content['source-manifest.json']))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ref', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--go', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.output, args.ref, go=args.go), sort_keys=True))


if __name__ == '__main__':
    main()
