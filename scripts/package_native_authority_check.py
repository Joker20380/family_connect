"""Build the offline checker from an exact Git export, never a dirty overlay."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
INPUTS = ('carrier/go.mod', 'carrier/go.sum', 'carrier/cmd/native-authority-check',
          'carrier/familysession', 'carrier/reliablestream', 'scripts/native_authority_acceptance.py')


def build(output, revision, go, *, repository=ROOT):
    if not re.fullmatch(r'[a-f0-9]{40}', revision):
        raise ValueError('Exact full source commit required')
    output, go = Path(output).resolve(), Path(go).resolve()
    if output.exists():
        raise ValueError('Output already exists')
    resolved = subprocess.check_output(['git', 'rev-parse', revision + '^{commit}'], cwd=repository).decode().strip()
    if resolved != revision:
        raise ValueError('Source revision mismatch')
    archive = subprocess.check_output(['git', 'archive', '--format=tar', revision, *INPUTS], cwd=repository)
    environment = dict(os.environ, GOENV='off', GOWORK='off', GOTOOLCHAIN='local',
                       CGO_ENABLED='0', GOOS='linux', GOARCH='amd64', GOAMD64='v1',
                       GOFLAGS='', GOEXPERIMENT='', GO111MODULE='on', GOPROXY='off', GOSUMDB='off')
    environment.pop('GOROOT', None)
    toolchain = subprocess.check_output([str(go), 'version'], env=environment).decode().strip()
    if toolchain != 'go version go1.26.0 linux/amd64':
        raise ValueError('Locked Go 1.26.0 linux/amd64 required')
    tool_directory = Path(subprocess.check_output([str(go), 'env', 'GOTOOLDIR'], env=environment).decode().strip())
    tool_hashes = {name:hashlib.sha256((tool_directory / name).read_bytes()).hexdigest()
                   for name in ('compile', 'asm', 'link')}
    with tempfile.TemporaryDirectory(prefix='fc-native-authority-source-') as directory:
        source = Path(directory)
        inventory = {}
        with tarfile.open(fileobj=io.BytesIO(archive)) as exported:
            for member in exported.getmembers():
                relative = Path(member.name)
                if relative.is_absolute() or '..' in relative.parts or not (member.isdir() or member.isfile()):
                    raise ValueError('Unsafe source archive member')
                target = source / relative
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    raw = exported.extractfile(member).read()
                    target.write_bytes(raw)
                    inventory[member.name] = hashlib.sha256(raw).hexdigest()
        if not (source / 'carrier/cmd/native-authority-check/main.go').is_file():
            raise ValueError('Checker missing from exact source revision')
        binary = source / 'native-authority-check'
        command = [str(go), 'build', '-trimpath', '-buildvcs=false', '-o', str(binary), './cmd/native-authority-check']
        subprocess.run(command, cwd=source / 'carrier', env=environment, check=True, capture_output=True, timeout=180)
        raw = binary.read_bytes()
        operator = (source / 'scripts/native_authority_acceptance.py').read_bytes()
        version = subprocess.check_output([str(go), 'version', '-m', str(binary)], env=environment).decode().splitlines()
    output.mkdir(mode=0o700, parents=True)
    (output / 'native-authority-check').write_bytes(raw)
    (output / 'native-authority-check').chmod(0o700)
    (output / 'native_authority_acceptance.py').write_bytes(operator)
    manifest = dict(source_head=revision, source_archive_sha256=hashlib.sha256(archive).hexdigest(),
                    toolchain=toolchain, go_sha256=hashlib.sha256(go.read_bytes()).hexdigest(),
                    build_tool_sha256=tool_hashes,
                    build_flags=['-trimpath', '-buildvcs=false'], cgo_enabled=False,
                    target='linux/amd64/v1', source_inventory=inventory,
                    binary_build_info=version[1:],
                    artifacts={'native-authority-check':hashlib.sha256(raw).hexdigest(),
                               'native_authority_acceptance.py':hashlib.sha256(operator).hexdigest()})
    (output / 'provenance.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--revision', required=True)
    parser.add_argument('--go', type=Path, required=True)
    arguments = parser.parse_args()
    result = build(arguments.output, arguments.revision, arguments.go)
    print(json.dumps(dict(source_head=result['source_head'], artifacts=result['artifacts']), indent=2))


if __name__ == '__main__':
    main()
