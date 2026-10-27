"""Build a pinned API overlay and management capsule, without deployment or keys."""

import argparse
import hashlib
import json
from pathlib import Path
import tarfile
import zipfile


BASE_API_SHA256 = '12ca0c72a89ff20c1b3c70a1182a2d5d98d4d78d25e7a079bb4d75bdf34060ed'
OVERLAYS = ('control/friends/restricted.py', 'control/friends/support_ids.py')
ADDITIONS = ('control/friends/paid_beta.py',)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    repository = Path(__file__).resolve().parents[1]
    assert digest(args.baseline.read_bytes()) == BASE_API_SHA256, 'Unexpected deployed API baseline'
    args.output.mkdir(mode=0o700, parents=True, exist_ok=False)
    target = args.output / 'bridge-access-v2.pyz'
    with zipfile.ZipFile(args.baseline) as source, zipfile.ZipFile(target, 'w') as destination:
        assert len(source.namelist()) == len(set(source.namelist()))
        assert set(OVERLAYS) <= set(source.namelist())
        assert not set(ADDITIONS) & set(source.namelist())
        for item in source.infolist():
            content = (repository / item.filename).read_bytes() if item.filename in OVERLAYS else source.read(item)
            if item.filename.endswith('.py'):
                compile(content, item.filename, 'exec')
            destination.writestr(item, content)
        for name in ADDITIONS:
            content = (repository / name).read_bytes()
            compile(content, name, 'exec')
            entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            destination.writestr(entry, content)
    target.chmod(0o600)
    with zipfile.ZipFile(args.baseline) as source, zipfile.ZipFile(target) as destination:
        assert destination.namelist() == source.namelist() + list(ADDITIONS)
        changed = sorted(name for name in source.namelist() if source.read(name) != destination.read(name))
        assert changed == sorted(OVERLAYS)
    management = repository / 'deploy/friends/restricted/maintenance'
    files = {path.name: digest(path.read_bytes()) for path in sorted(management.glob('*.py'))}
    for name in files:
        compile((management / name).read_bytes(), name, 'exec')
    source_hash = digest(json.dumps(files, sort_keys=True, separators=(',', ':')).encode())
    receipt = dict(schema=1, baseline_api_sha256=BASE_API_SHA256, api_sha256=digest(target.read_bytes()),
        source_files=files, source_sha256=source_hash, overlays=changed, additions=list(ADDITIONS), admission_mode='all_activated',
        authority_days=90, credential_seconds=14400, contains_keys=False)
    manifest = args.output / 'manifest.json'
    manifest.write_text(json.dumps(receipt, sort_keys=True, separators=(',', ':')))
    with tarfile.open(args.output / 'bridge-access-v2.tar.gz', 'w:gz') as archive:
        archive.add(target, arcname=target.name)
        archive.add(manifest, arcname=manifest.name)
        for name in files:
            archive.add(management / name, arcname='management/' + name)
    print(json.dumps(receipt, sort_keys=True))


if __name__ == '__main__':
    main()
