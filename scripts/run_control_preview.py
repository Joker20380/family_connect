"""Run the paired preview from its extracted directory, without installing it.

Use system Python for `gui`, and the pinned control virtualenv for `control`.
Never run an older installed GUI concurrently. State paths remain explicit.
The manifest detects corruption/mixed copies; it is not a signing trust boundary.
"""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parents[1]


def verify():
    manifest = json.loads((ROOT / 'manifest.json').read_text())
    if manifest.get('schema_version') != 1 or manifest.get('preview') is not True:
        raise ValueError('invalid preview manifest')
    files = manifest['files']
    for name, digest in files.items():
        path = Path(name)
        if path.is_absolute() or '..' in path.parts or (ROOT / path).is_symlink():
            raise ValueError('invalid preview member')
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != digest:
            raise ValueError('preview member mismatch')
    expected = hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()
    if manifest['bundle_id'] != expected:
        raise ValueError('preview manifest mismatch')
    return expected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('verify', 'gui', 'control'))
    parser.add_argument('arguments', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    rest = args.arguments
    digest = verify()
    if args.mode == 'verify':
        print(digest)
        return
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / 'clients/desktop'))
    sys.argv = [args.mode] + rest
    if args.mode == 'gui':
        runpy.run_path(str(ROOT / 'clients/desktop/app.py'), run_name='__main__')
    else:
        runpy.run_module('provisioning.runtime', run_name='__main__')


if __name__ == '__main__':
    main()
