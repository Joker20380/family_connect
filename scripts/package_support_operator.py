"""Deterministic source-only, local operator CLI; no secrets or public listener."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def build(output, source=ROOT):
    paths = json.loads((source / 'deploy/friends/restricted/runtime-files.json').read_text())
    paths = sorted(set(paths + ['control/friends/support_admin.py', 'control/friends/restricted_admin.py']))
    content = {'__main__.py': b'from control.friends.support_admin import main\nmain()\n'}
    for name in paths:
        path = source / name
        if (Path(name).is_absolute() or '..' in Path(name).parts or path.suffix != '.py'
                or not path.is_file() or any(parent.is_symlink() for parent in (path, *path.parents))):
            raise ValueError('Unsafe operator source')
        content[name] = path.read_bytes()
        for parent in Path(name).parents:
            if parent != Path('.'):
                content[str(parent) + '/'] = b''
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, raw in sorted(content.items()):
            entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = (0o40755 if name.endswith('/') else 0o100644) << 16
            archive.writestr(entry, raw)
    return dict(sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
                files={name: hashlib.sha256(raw).hexdigest() for name, raw in content.items()})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.output), sort_keys=True))


if __name__ == '__main__':
    main()
