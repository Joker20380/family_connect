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
SNAPSHOT_SHA = '0120dad028ead353b8b83a600538f3e578b2b46ddf871bf16e97529f9449f450'
REQUIRED_COMMITS = (HISTORICAL, 'edca5447418141cb44c0706e26d1973d7defd397',
                    'efc13f1c7f2750cb7640dd2b8b90aed15c92c6e3',
                    '2077c271d43d3bbe09f76e70934947bcc3fb51c6')


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
    objects = set()
    for commit in REQUIRED_COMMITS:
        objects.add(commit)
        objects.add(git('rev-parse', commit + '^{tree}').decode().strip())
        for entry in git('ls-tree', '-rt', commit).decode().splitlines():
            objects.add(entry.split()[2])
    (output / 'fixture-objects.pack').write_bytes(git('-c', 'pack.threads=1', 'pack-objects', '--stdout',
        input=('\n'.join(sorted(objects)) + '\n').encode()))
    (output / 'inventory.json').write_text(json.dumps(dict(source_commit=head, historical_commit=HISTORICAL,
        files={path.name: digest(path) for path in sorted(output.iterdir())}), indent=2) + '\n')


def restore_git(commit_file, paths_file, objects_file=None):
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
    shallow = {head}
    if objects_file is not None:
        git('index-pack', '--stdin', input=objects_file.read_bytes())
        for expected in REQUIRED_COMMITS:
            if git('rev-parse', expected + '^{commit}').decode().strip() != expected:
                raise ValueError('Fixture commit mismatch')
            git('archive', expected)
            shallow.add(expected)
    (ROOT / '.git/shallow').write_text('\n'.join(sorted(shallow)) + '\n')


def normalize_zip(path):
    with zipfile.ZipFile(path) as archive:
        entries = [(entry, archive.read(entry)) for entry in archive.infolist()]
    with zipfile.ZipFile(path, 'w') as archive:
        for entry, raw in sorted(entries, key=lambda pair: pair[0].filename):
            entry.date_time = (1980, 1, 1, 0, 0, 0)
            entry.create_system = 3
            entry.external_attr = (0o40755 if entry.is_dir() else 0o100644) << 16
            archive.writestr(entry, raw)


def historical_http(output, source):
    subprocess.run([sys.executable, '-I', str((source / 'scripts/package_friends_http.py').resolve()),
                    '--output', str(output.resolve())], cwd=source, capture_output=True, check=True, timeout=30)
    if digest(output / 'friends-http.pyz') != HISTORICAL_SHA:
        raise ValueError('Historical fixture pin mismatch')


def historical_snapshot(output):
    fixture = ROOT / 'tests/fixtures/accepted_snapshot'
    members = json.loads((fixture / 'sources.json').read_text())
    content = {'__main__.py': b'# -*- coding: utf-8 -*-\nimport control.friends.restricted_sync\ncontrol.friends.restricted_sync.main()\n'}
    for name, contract in members.items():
        if Path(name).is_absolute() or '..' in Path(name).parts or not name.endswith('.py'):
            raise ValueError('Unsafe snapshot member')
        if 'commit' in contract:
            if contract['commit'] not in REQUIRED_COMMITS:
                raise ValueError('Unpinned snapshot commit')
            raw = git('show', contract['commit'] + ':' + name)
        else:
            if contract['fixture'] != Path(contract['fixture']).name:
                raise ValueError('Unsafe snapshot fixture')
            raw = (fixture / contract['fixture']).read_bytes()
        if hashlib.sha256(raw).hexdigest() != contract['sha256']:
            raise ValueError('Snapshot member mismatch: ' + name)
        content[name] = raw
    directories = {str(parent) + '/' for name in content for parent in Path(name).parents if str(parent) != '.'}
    with zipfile.ZipFile(output, 'x') as archive:
        for name in sorted(directories) + sorted(content):
            entry = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = ((0o40755 << 16) | 0x10) if name.endswith('/') else (0o100644 << 16)
            entry.compress_type = zipfile.ZIP_STORED if name.endswith('/') else zipfile.ZIP_DEFLATED
            archive.writestr(entry, content.get(name, b''), compresslevel=9)
    if digest(output) != SNAPSHOT_SHA:
        raise ValueError('Historical snapshot pin mismatch')


def prepare(output, go, historical_archive=None):
    sys.path.insert(0, str(ROOT))
    from scripts.package_friends_http import build as http
    from scripts.package_restricted_runtime import build as sync
    from scripts.package_friends_readiness import build as readiness
    from scripts.package_credential_renewal import build as renewal
    output.mkdir(parents=True, exist_ok=False)
    head = git('rev-parse', 'HEAD').decode().strip()
    renewal(output / 'credential-renewal.tar.gz', head, repository=ROOT)
    historical_snapshot(output / 'accepted-snapshot.pyz')
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
        historical_http(output / 'historical-http', historical)
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
    if digest(fixtures / 'accepted-snapshot.pyz') != SNAPSHOT_SHA:
        raise ValueError('Historical snapshot pin mismatch')
    return dict(FC_TEST_HTTP_ARTIFACT=str(fixtures / 'http'),
        FC_TEST_HTTP_SHA256=digest(fixtures / 'http/friends-http.pyz'),
        FC_TEST_SYNC_ARTIFACT=str(fixtures / 'sync'),
        FC_TEST_SYNC_SHA256=digest(fixtures / 'sync/restricted-sync.pyz'),
        FC_TEST_READINESS_ARTIFACT=str(fixtures / 'readiness'),
        FC_TEST_HISTORICAL_HTTP_ARTIFACT=str(fixtures / 'historical-http/friends-http.pyz'),
        FC_TEST_RENEWAL_PACKAGE=str(fixtures / 'credential-renewal.tar.gz'),
        FC_TEST_SNAPSHOT_ARCHIVE=str(fixtures / 'accepted-snapshot.pyz'),
        FC_TEST_GO=str(go), FC_TEST_NGINX=str(nginx))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest='action', required=True)
    exporting = actions.add_parser('export')
    exporting.add_argument('--output', type=Path, required=True)
    restoring = actions.add_parser('restore-git')
    restoring.add_argument('--commit-file', type=Path, required=True)
    restoring.add_argument('--paths-file', type=Path, required=True)
    restoring.add_argument('--objects-file', type=Path)
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
        restore_git(args.commit_file.resolve(), args.paths_file.resolve(), args.objects_file)
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
