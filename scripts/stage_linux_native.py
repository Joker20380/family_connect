"""Stage and verify the complete accepted native closure, not the current frontend."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile
import types

ROOT = Path(__file__).resolve().parents[1]


def inventory_digest(inventory):
    return hashlib.sha256(json.dumps(inventory, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def reference():
    policy = json.loads((ROOT / 'packaging/linux/native-reference.json').read_text())
    system = json.loads((ROOT / 'packaging/linux/system-reference.json').read_text())
    if policy['schema'] != 1 or policy['native_source_digest'] != system['native_source_digest']:
        raise ValueError('Native reference disagrees with accepted system reference')
    return policy


def load_helper(root, name):
    path = root / 'scripts' / (name + '.py')
    module = types.ModuleType(name)
    module.__file__ = str(path)
    exec(compile(path.read_bytes(), str(path), 'exec'), module.__dict__)
    return module


def verify(root):
    root = root.resolve()
    policy = reference()
    closure = {}
    for path in sorted(root.rglob('*')):
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ValueError('Native closure contains a non-regular entry')
        if path.is_file():
            closure[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    if inventory_digest(closure) != policy['closure_sha256']:
        raise ValueError('Native closure mismatch: changed, missing or additional input')
    builder = load_helper(root, 'build_desktop_mesh')
    inventory = builder.sources(root / 'clients/mesh')
    if inventory_digest(inventory) != policy['native_source_digest']:
        raise ValueError('Native inventory mismatch')
    if load_helper(root, 'verify_desktop_reference').verify(root)['result'] != 'PASS':
        raise ValueError('Accepted desktop reference mismatch')
    return inventory


def stage(destination, repository=ROOT):
    policy = reference()
    if destination.exists():
        raise ValueError('Use a fresh native source directory')
    archive = subprocess.run(['git', '-C', str(repository), 'archive', policy['commit'], '--', *policy['paths']],
                             check=True, capture_output=True).stdout
    destination.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(archive)) as source:
        for member in source.getmembers():
            relative = Path(member.name)
            if (relative.is_absolute() or '..' in relative.parts or
                    not (member.isfile() or member.isdir())):
                raise ValueError('Unsafe native source archive')
        source.extractall(destination, filter='data')
    verify(destination)
    return dict(native_source_commit=policy['commit'], closure_sha256=policy['closure_sha256'],
                native_source_digest=policy['native_source_digest'])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(stage(args.out.resolve()), indent=2))


if __name__ == '__main__':
    main()
