"""Build the readiness adapter exclusively from a committed Git export."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = Path('deploy/friends/restricted')
ARCHIVE = 'candidate-readiness.pyz'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()


def build(output, source, head, go):
    mapping = json.loads((source / CONTRACT / 'readiness-runtime-files.json').read_bytes())
    if not mapping or mapping.get('__main__.py') != 'scripts/friends_readiness_adapter.py':
        raise ValueError('Invalid entrypoint')
    files = {}
    for destination, original in mapping.items():
        for name in (destination, original):
            if (Path(name).is_absolute() or '..' in Path(name).parts
                    or Path(name).suffix != '.py' or 'tests' in Path(name).parts):
                raise ValueError('Invalid runtime manifest')
        path = source / original
        if not path.is_file() or any(parent.is_symlink() for parent in (path, *path.parents)):
            raise ValueError('Unsafe runtime source')
        files[destination] = path.read_bytes()
    environment = dict(os.environ, CGO_ENABLED='0', GOTOOLCHAIN='local', GOPROXY='off', GOSUMDB='off',
                       GOOS='linux', GOARCH='amd64', GOFLAGS='', GOVCS='*:off')
    toolchain = subprocess.check_output([str(go), 'version'], env=environment, text=True).strip()
    if toolchain != 'go version go1.26.0 linux/amd64':
        raise ValueError('Expected accepted Go 1.26.0 linux/amd64 toolchain')
    output.mkdir(parents=True, exist_ok=False)
    native = output / 'readiness-delivery-check'
    subprocess.run([str(go), 'build', '-mod=readonly', '-trimpath', '-buildvcs=false',
                    '-o', str(native.resolve()), './cmd/readiness-delivery-check'],
                   cwd=source / 'carrier', env=environment, check=True, timeout=180)
    dependencies = subprocess.check_output(
        [str(go), 'list', '-mod=readonly', '-buildvcs=false', '-deps', '-f', '{{if not .Standard}}{{.ImportPath}} {{join .GoFiles " "}}{{end}}',
         './cmd/readiness-delivery-check'], cwd=source / 'carrier', env=environment, text=True).splitlines()
    native_sources = {'carrier/go.mod', 'carrier/go.sum'}
    module = 'github.com/Joker20380/family_connect/carrier/'
    for dependency in dependencies:
        fields = dependency.split()
        if fields and fields[0].startswith(module):
            native_sources.update('carrier/' + fields[0][len(module):] + '/' + name for name in fields[1:])
    source_inventory = {name: digest((source / name).read_bytes()) for name in sorted(native_sources)}
    files['readiness.lock'] = (source / CONTRACT / 'readiness.lock').read_bytes()
    manifest = dict(version=1, source_head=head, sources=mapping,
                    files={name: digest(raw) for name, raw in files.items()},
                    native_sha256=digest(native.read_bytes()), native_sources=source_inventory,
                    native_dependencies=sorted(filter(None, dependencies)), go=toolchain)
    files['adapter-inventory.json'] = encode(manifest)
    directories = {str(parent) + '/' for name in files for parent in Path(name).parents if str(parent) != '.'}
    with zipfile.ZipFile(output / ARCHIVE, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(set(files) | directories):
            entry = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = (0o40755 if name in directories else 0o100644) << 16
            entry.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(entry, files.get(name, b''))
    (output / 'readiness.lock').write_bytes(files['readiness.lock'])
    report = dict(manifest, artifact_sha256=digest((output / ARCHIVE).read_bytes()),
                  python=sys.version.split()[0], builder_sha256=digest((source / 'scripts/package_friends_readiness.py').read_bytes()))
    (output / 'provenance.json').write_bytes(encode(report))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--go', type=Path, required=True)
    arguments = parser.parse_args()
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    if not re.fullmatch('[a-f0-9]{40}', arguments.revision) or arguments.revision != head:
        raise ValueError('Exact current committed HEAD required')
    raw = subprocess.check_output(['git', 'archive', head], cwd=ROOT)
    with tempfile.TemporaryDirectory(prefix='fc-readiness-source-') as temporary:
        source = Path(temporary)
        with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
            archive.extractall(source, filter='data')
        for relative in ('scripts/package_friends_readiness.py', 'deploy/friends/restricted/readiness-runtime-files.json'):
            if (source / relative).read_bytes() != (ROOT / relative).read_bytes():
                raise ValueError('Builder or manifest differs from committed source')
        report = build(arguments.output.resolve(), source, head, arguments.go.resolve())
    print(json.dumps(dict(artifact=str(arguments.output / ARCHIVE), sha256=report['artifact_sha256'], source_head=head)))


if __name__ == '__main__':
    main()
