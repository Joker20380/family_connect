"""Closed stdlib-only admission launcher; native artifacts and private bindings stay separate."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ('control/capture_gate.py', 'control/capture_receiver.py')


def build(output, source=ROOT):
    contents = {'control/': b'', '__main__.py':
                b'from control.capture_receiver import main\nraise SystemExit(main())\n'}
    for name in SOURCES:
        path = source / name
        if not path.is_file() or any(item.is_symlink() for item in (path, *path.parents)):
            raise ValueError('UNSAFE_RECEIVER_SOURCE')
        contents[name] = path.read_bytes()
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, raw in sorted(contents.items()):
            entry = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = (0o40755 if name.endswith('/') else 0o100644) << 16
            archive.writestr(entry, raw)
    return dict(schema=1, sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
                files={name: hashlib.sha256(raw).hexdigest() for name, raw in contents.items()},
                deployed=False, capture_permitted=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.output), sort_keys=True))


if __name__ == '__main__':
    main()
