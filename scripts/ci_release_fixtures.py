"""Provision closed, source-pinned release artifacts for unprivileged tests; never production state."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
HISTORICAL = '4bb53b0605c2c898b6a3feca6ee15fd34b943a94'
HISTORICAL_SHA = '460e75205eb9baff313dc7dd963cdb7bceddf2d1e13405a71686f9ec6c976d71'


def git(*arguments, source=None, **kwargs):
    return subprocess.check_output(['git', *arguments], cwd=ROOT if source is None else source, **kwargs)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract(raw, destination):
    destination.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        archive.extractall(destination, filter='data')


def export(output):
    output.mkdir(parents=True, exist_ok=False)
    head = git('rev-parse', 'HEAD').decode().strip()
    (output / 'current.tar').write_bytes(git('archive', head))
    (output / 'historical.tar').write_bytes(git('archive', HISTORICAL))
    (output / 'current.commit').write_bytes(git('cat-file', 'commit', head))
    (output / 'tracked.paths').write_bytes(git('ls-tree', '-rz', '--name-only', head))
    (output / 'inventory.json').write_text(json.dumps(dict(source_commit=head, historical_commit=HISTORICAL,
        files={path.name: digest(path) for path in sorted(output.iterdir())}), indent=2) + '\n')


def restore_git(commit_file, paths_file):
    if (ROOT / '.git').exists():
        raise ValueError('Refuse to replace Git metadata')
    commit = commit_file.read_bytes()
    expected_tree = commit.splitlines()[0].decode().removeprefix('tree ')
    git('init', '--quiet', '--initial-branch=ci-fixture')
    git('add', '--force', '--pathspec-from-file=' + str(paths_file), '--pathspec-file-nul')
    if git('write-tree').decode().strip() != expected_tree:
        raise ValueError('Exported source tree mismatch')
    head = git('hash-object', '-w', '-t', 'commit', '--stdin', input=commit).decode().strip()
    git('update-ref', 'refs/heads/ci-fixture', head)
    (ROOT / '.git/shallow').write_text(head + '\n')


def normalize_zip(path):
    with zipfile.ZipFile(path) as archive:
        entries = [(entry, archive.read(entry)) for entry in archive.infolist()]
    with zipfile.ZipFile(path, 'w') as archive:
        for entry, raw in sorted(entries, key=lambda pair: pair[0].filename):
            entry.date_time = (1980, 1, 1, 0, 0, 0)
            entry.create_system = 3
            entry.external_attr = (0o40755 if entry.is_dir() else 0o100644) << 16
            archive.writestr(entry, raw)


def prepare(output, go, historical_archive=None):
    sys.path.insert(0, str(ROOT))
    from scripts.package_friends_http import build as http
    from scripts.package_restricted_runtime import build as sync
    from scripts.package_friends_readiness import build as readiness
    output.mkdir(parents=True, exist_ok=False)
    head = git('rev-parse', 'HEAD').decode().strip()
    with tempfile.TemporaryDirectory(prefix='fc-ci-source-') as temporary:
        source = Path(temporary) / 'current'
        historical = Path(temporary) / 'historical'
        extract(git('archive', head), source)
        extract(historical_archive.read_bytes() if historical_archive else git('archive', HISTORICAL), historical)
        http(output / 'http', source)
        sync(output / 'sync', source)
        normalize_zip(output / 'sync/restricted-sync.pyz')
        hashes = json.loads((output / 'sync/sha256.json').read_text())
        hashes['restricted-sync.pyz'] = digest(output / 'sync/restricted-sync.pyz')
        (output / 'sync/sha256.json').write_text(json.dumps(hashes, indent=2) + '\n')
        readiness(output / 'readiness', source, head, go)
        http(output / 'historical-http', historical)
    if digest(output / 'historical-http/friends-http.pyz') != HISTORICAL_SHA:
        raise ValueError('Historical fixture pin mismatch')
    files = {str(path.relative_to(output)): digest(path) for path in sorted(output.rglob('*')) if path.is_file()}
    (output / 'inventory.json').write_text(json.dumps(dict(source_commit=head, historical_commit=HISTORICAL,
        files=files), indent=2) + '\n')
    print(json.dumps(dict(source_commit=head, fixtures=str(output), files=len(files))))


def environment(fixtures, go, nginx):
    inventory = json.loads((fixtures / 'inventory.json').read_text())
    if inventory['source_commit'] != git('rev-parse', 'HEAD').decode().strip():
        raise ValueError('Fixture source commit mismatch')
    for name, expected in inventory['files'].items():
        if Path(name).is_absolute() or '..' in Path(name).parts or digest(fixtures / name) != expected:
            raise ValueError('Fixture inventory mismatch')
    if digest(fixtures / 'historical-http/friends-http.pyz') != HISTORICAL_SHA:
        raise ValueError('Historical fixture pin mismatch')
    return dict(FC_TEST_HTTP_ARTIFACT=str(fixtures / 'http'),
        FC_TEST_HTTP_SHA256=digest(fixtures / 'http/friends-http.pyz'),
        FC_TEST_SYNC_ARTIFACT=str(fixtures / 'sync'),
        FC_TEST_SYNC_SHA256=digest(fixtures / 'sync/restricted-sync.pyz'),
        FC_TEST_READINESS_ARTIFACT=str(fixtures / 'readiness'),
        FC_TEST_HISTORICAL_HTTP_ARTIFACT=str(fixtures / 'historical-http/friends-http.pyz'),
        FC_TEST_GO=str(go), FC_TEST_NGINX=str(nginx))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest='action', required=True)
    exporting = actions.add_parser('export')
    exporting.add_argument('--output', type=Path, required=True)
    restoring = actions.add_parser('restore-git')
    restoring.add_argument('--commit-file', type=Path, required=True)
    restoring.add_argument('--paths-file', type=Path, required=True)
    preparing = actions.add_parser('prepare')
    preparing.add_argument('--output', type=Path, required=True)
    preparing.add_argument('--go', type=Path, required=True)
    preparing.add_argument('--historical-archive', type=Path)
    running = actions.add_parser('run')
    running.add_argument('--fixtures', type=Path, required=True)
    running.add_argument('--go', type=Path, required=True)
    running.add_argument('--nginx', type=Path, required=True)
    running.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.action == 'export':
        export(args.output.resolve())
    elif args.action == 'restore-git':
        restore_git(args.commit_file.resolve(), args.paths_file.resolve())
    elif args.action == 'prepare':
        prepare(args.output.resolve(), args.go.resolve(), args.historical_archive)
    else:
        command = args.command[1:] if args.command[:1] == ['--'] else args.command
        if not command:
            parser.error('Test command required')
        values = environment(args.fixtures.resolve(), args.go.resolve(), args.nginx.resolve())
        raise SystemExit(subprocess.call(command, cwd=ROOT, env=dict(os.environ, **values)))


if __name__ == '__main__':
    main()
