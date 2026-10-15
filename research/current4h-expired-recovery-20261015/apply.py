import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tarfile


ARCHIVE_SHA256 = '5fa24f5383e3f64c6ce7368e807972a6a4e4e9d832268feabefb9fea396c0e00'


def checksum(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def reconstruct(archive, destination, *, before=False):
    root = Path(__file__).resolve().parent
    manifest = json.loads((root/'source-manifest.json').read_bytes())
    assert checksum(archive.read_bytes()) == ARCHIVE_SHA256
    destination.mkdir(mode=0o700, parents=True, exist_ok=False)
    with tarfile.open(archive) as source:
        for member in source.getmembers():
            assert not member.name.startswith('/') and '..' not in Path(member.name).parts
            assert member.isfile() or member.isdir()
        source.extractall(destination, filter='data')
    for name, identity in manifest['changed'].items():
        path = destination/name
        assert (checksum(path.read_bytes()) if path.exists() else None) == identity['before']
        if before:
            continue
        replacement = root/'changed'/name
        assert checksum(replacement.read_bytes()) == identity['after']
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(replacement, path)
    if not before:
        actual = {str(path.relative_to(destination)): checksum(path.read_bytes())
                  for path in sorted(destination.rglob('*')) if path.is_file()}
        assert checksum(canonical(actual)) == manifest['cumulative_inventory_sha256']
    return destination


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--before', action='store_true')
    args = parser.parse_args()
    reconstruct(args.archive, args.out, before=args.before)
    print('BASE_RECONSTRUCTED' if args.before else 'CUMULATIVE_SOURCE_VERIFIED')


if __name__ == '__main__':
    main()
