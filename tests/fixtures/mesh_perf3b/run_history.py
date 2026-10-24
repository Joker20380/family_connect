"""Run only the six historical overlay tests with byte-verified, explicit inputs."""

import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import sys
import tempfile
import zipfile


MANIFEST = Path(__file__).with_name('historical-suite.json')
TEST_DIRECTORY = Path('tests/fixtures/mesh_perf3b')
CHILD = '''
from pathlib import Path
import importlib
import sys

root = Path.cwd()
api = root / 'state-client-build/mesh-perf-3b/api'
sys.path.insert(0, str(api))
for name in ('control.friends.owner_handoff', 'control.friends.restricted',
             'control.friends.access', 'device_identity.device', 'provisioning.friends_catalog'):
    module = importlib.import_module(name)
    if not Path(module.__file__).resolve().is_relative_to(api):
        raise RuntimeError('BLOCKED: historical import provenance mismatch: ' + name)
    print(name + ': verified isolated API', flush=True)
import pytest
raise SystemExit(pytest.main(['-c', str(root / 'pytest.ini'), '-q', *sys.argv[1:]]))
'''
IMPORT_PREFLIGHT = CHILD.split('import pytest\n')[0] + '''
import pytest
import importlib.util
spec = importlib.util.spec_from_file_location('baseline_fixtures', root / 'tests/test_friends_restricted.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
assert module.TIME_CONTRACT['valid']
'''


def checked_bytes(path, expected, label):
    if not expected:
        raise ValueError('UNPINNED_INPUT: ' + label)
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError('HASH_MISMATCH: ' + label)
    return raw


def validate_archive(raw, members=()):
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError('DUPLICATE_ARCHIVE_MEMBER')
        for entry in archive.infolist():
            path = PurePosixPath(entry.filename)
            if path.is_absolute() or '..' in path.parts or stat.S_ISLNK(entry.external_attr >> 16):
                raise ValueError('UNSAFE_ARCHIVE_MEMBER')
        if archive.testzip() is not None:
            raise ValueError('CORRUPT_ARCHIVE')
        for name in members:
            archive.read(name)


def verified_retained(manifest, paths, selected):
    snapshot = {}
    errors = []
    for name, entry in manifest.get('retained_inputs', {}).items():
        if not set(selected).intersection(entry['required_by']):
            continue
        try:
            path = paths.get(name)
            if path is None:
                raise ValueError('MISSING_INPUT: --' + name)
            if entry['kind'] in ('tree', 'classes'):
                pins = entry['files']
                if not pins:
                    raise ValueError('UNPINNED_INPUT: ' + name + ': ' + entry['provenance'])
                if not path.is_dir() or path.is_symlink():
                    raise ValueError('MISSING_TREE: ' + name)
                members = list(path.rglob('*'))
                if any(member.is_symlink() or not (member.is_file() or member.is_dir()) for member in members):
                    raise ValueError('UNSAFE_TREE: ' + name)
                if {str(member.relative_to(path)) for member in members if member.is_file()} != set(pins):
                    raise ValueError('TREE_INVENTORY_MISMATCH: ' + name)
                if not set(entry['required_files']).issubset(pins):
                    raise ValueError('INCOMPLETE_INVENTORY: ' + name)
                for relative, expected in pins.items():
                    raw = checked_bytes(path / relative, expected, name + '/' + relative)
                    mode = (path / relative).stat().st_mode & 0o777
                    if relative in entry.get('executables', ()) and not mode & 0o111:
                        raise ValueError('NOT_EXECUTABLE: ' + name + '/' + relative)
                    if entry['kind'] == 'classes' and not raw.startswith(b'\xca\xfe\xba\xbe'):
                        raise ValueError('INVALID_CLASS: ' + relative)
                    snapshot[str(Path(entry['destination']) / relative)] = (raw, mode)
            else:
                raw = checked_bytes(path, entry['sha256'], name)
                mode = path.stat().st_mode & 0o777
                if entry['kind'] == 'executable' and not mode & 0o111:
                    raise ValueError('NOT_EXECUTABLE: ' + name)
                if entry['kind'] == 'zip':
                    validate_archive(raw, entry['members'])
                snapshot[entry['destination']] = (raw, mode)
        except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
            errors.append(name + ': ' + str(error))
    if errors:
        raise ValueError('; '.join(errors))
    return snapshot


def verified_inputs(manifest, source_root, api_archive, retained_paths=None, selected=None):
    if source_root is None or api_archive is None:
        raise ValueError('MISSING_INPUTS: --source-root and --api-archive are required; no main/state fallback')
    raw = checked_bytes(api_archive, manifest['api_sha256'], 'sealed owner API archive')
    sources = {name: checked_bytes(source_root / name, expected, name)
               for name, expected in manifest['files'].items()}
    validate_archive(raw)
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        for name, expected in manifest['api_modules'].items():
            if hashlib.sha256(archive.read(name)).hexdigest() != expected:
                raise ValueError('API_MODULE_MISMATCH: ' + name)
    retained = verified_retained(manifest, retained_paths or {}, selected or list(manifest.get('tests', {})))
    return sources, raw, retained


def write_snapshot(root, sources, archive_bytes, retained):
    for name, (raw, mode) in {**{name: (raw, 0o600) for name, raw in sources.items()}, **retained}.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        target.chmod(mode)
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        archive.extractall(root / 'state-client-build/mesh-perf-3b/api')
    (root / 'pytest.ini').write_text('[pytest]\n')


def snapshot_preflight(manifest, root, environment, retained):
    result = subprocess.run([sys.executable, '-I', '-B', '-c', IMPORT_PREFLIGHT],
                            cwd=root, env=environment, timeout=30)
    if result.returncode:
        raise ValueError('HISTORICAL_PYTHON_IMPORTS: exit ' + str(result.returncode))
    retained_preflight(manifest, root, environment, retained)


def retained_preflight(manifest, root, environment, retained):
    entries = manifest.get('retained_inputs', {})
    if 'delivery-check' not in entries or entries['delivery-check']['destination'] not in retained:
        return
    delivery = root / entries['delivery-check']['destination']
    result = subprocess.run([str(delivery)], input=b'{}', capture_output=True,
                            cwd=root, env=environment, timeout=15)
    if result.returncode != 1 or result.stderr.strip() != b'delivery compatibility failed':
        raise ValueError('DELIVERY_CHECK_NOT_USABLE')
    runtime = root / entries['java-runtime']['destination']
    classes = root / entries['java-classes']['destination']
    jars = [root / entries[name]['destination'] for name in ('gson-jar', 'junit-jar', 'hamcrest-jar')]
    result = subprocess.run([str(runtime / 'bin/java'), '--dry-run', '-cp',
                             os.pathsep.join(map(str, [classes, *jars])), 'com.familyconnect.app.FloorRoundtrip'],
                            cwd=root, env=environment, capture_output=True, timeout=30)
    if result.returncode:
        raise ValueError('JAVA_NOT_USABLE: ' + result.stderr.decode(errors='replace'))


def run(manifest, sources, archive_bytes, selected, retained=None):
    retained = retained or {}
    with tempfile.TemporaryDirectory(prefix='fc-mesh-history-') as temporary:
        root = Path(temporary)
        write_snapshot(root, sources, archive_bytes, retained)
        environment = {key: os.environ[key] for key in ('PATH', 'LANG', 'LC_ALL') if key in os.environ}
        environment.update(HOME=temporary, PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', PYTHONDONTWRITEBYTECODE='1')
        try:
            snapshot_preflight(manifest, root, environment, retained)
        except (OSError, ValueError, subprocess.TimeoutExpired) as error:
            print('BLOCKED/NOT_RUN: ' + str(error), file=sys.stderr)
            return 2
        command = [sys.executable, '-I', '-B', '-c', CHILD,
                   *(str(root / TEST_DIRECTORY / name) for name in selected)]
        print(json.dumps(dict(status='VERIFIED_INPUTS', source_commit=manifest['source_commit'],
                              api_sha256=manifest['api_sha256'], tests=selected)), flush=True)
        return subprocess.run(command, cwd=root, env=environment, timeout=180).returncode


def main(arguments=None):
    manifest = json.loads(MANIFEST.read_text())
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path)
    parser.add_argument('--api-archive', type=Path)
    for name in manifest['retained_inputs']:
        parser.add_argument('--' + name, type=Path)
    parser.add_argument('--test', choices=list(manifest['tests']), action='append')
    args = parser.parse_args(arguments)
    selected = args.test or list(manifest['tests'])
    try:
        sources, raw, retained = verified_inputs(manifest, args.source_root, args.api_archive,
            {name: getattr(args, name.replace('-', '_')) for name in manifest['retained_inputs']}, selected)
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
        print('BLOCKED/NOT_RUN: ' + str(error), file=sys.stderr)
        return 2
    try:
        return run(manifest, sources, raw, selected, retained)
    except (OSError, subprocess.TimeoutExpired) as error:
        print('FAILED: historical child process: ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
