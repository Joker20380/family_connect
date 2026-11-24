"""Build a closed, source-only guardian package; no bindings, installation or approval."""
import argparse
import hashlib
import os
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ('control/capture_gate.py', 'control/capture_group.py', 'control/capture_launch.py', 'control/capture_renewal.py')
MAIN = b'from control.capture_launch import guardian_main\nraise SystemExit(guardian_main())\n'


def build(output, source=ROOT):
    contents = {'control/': b'', '__main__.py': MAIN}
    for name in SOURCES:
        path = source / name
        if not path.is_file() or any(item.is_symlink() for item in (path, *path.parents)):
            raise ValueError('UNSAFE_GUARDIAN_SOURCE')
        contents[name] = path.read_bytes()
    with output.open('xb') as target:
        os.fchmod(target.fileno(), 0o600)
        with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_STORED) as archive:
            for name, raw in sorted(contents.items()):
                entry = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
                entry.create_system = 3
                entry.external_attr = (0o40755 if name.endswith('/') else 0o100644) << 16
                archive.writestr(entry, raw)
    return hashlib.sha256(output.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    print(build(parser.parse_args().output))


if __name__ == '__main__':
    main()
