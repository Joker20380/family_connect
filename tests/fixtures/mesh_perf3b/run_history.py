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
             'control.friends.access', 'device_identity.device'):
    module = importlib.import_module(name)
    if not Path(module.__file__).resolve().is_relative_to(api):
        raise RuntimeError('BLOCKED: historical import provenance mismatch: ' + name)
    print(name + ': verified isolated API', flush=True)
import pytest
raise SystemExit(pytest.main(['-c', str(root / 'pytest.ini'), '-q', *sys.argv[1:]]))
'''


def checked_bytes(path, expected, label):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError('HASH_MISMATCH: ' + label)
    return raw


def verified_inputs(manifest, source_root, api_archive):
    if source_root is None or api_archive is None:
        raise ValueError('MISSING_INPUTS: --source-root and --api-archive are required; no main/state fallback')
    raw = checked_bytes(api_archive, manifest['api_sha256'], 'sealed owner API archive')
    sources = {name: checked_bytes(source_root / name, expected, name)
               for name, expected in manifest['files'].items()}
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError('DUPLICATE_ARCHIVE_MEMBER')
        for entry in archive.infolist():
            path = PurePosixPath(entry.filename)
            if path.is_absolute() or '..' in path.parts or stat.S_ISLNK(entry.external_attr >> 16):
                raise ValueError('UNSAFE_ARCHIVE_MEMBER')
        for name, expected in manifest['api_modules'].items():
            if hashlib.sha256(archive.read(name)).hexdigest() != expected:
                raise ValueError('API_MODULE_MISMATCH: ' + name)
    return sources, raw


def run(manifest, sources, archive_bytes, selected):
    with tempfile.TemporaryDirectory(prefix='fc-mesh-history-') as temporary:
        root = Path(temporary)
        for name, raw in sources.items():
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
            archive.extractall(root / 'state-client-build/mesh-perf-3b/api')
        (root / 'pytest.ini').write_text('[pytest]\n')
        environment = {key: os.environ[key] for key in ('PATH', 'LANG', 'LC_ALL') if key in os.environ}
        environment.update(HOME=temporary, PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', PYTHONDONTWRITEBYTECODE='1')
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
    parser.add_argument('--test', choices=list(manifest['tests']), action='append')
    args = parser.parse_args(arguments)
    try:
        sources, raw = verified_inputs(manifest, args.source_root, args.api_archive)
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
        print('BLOCKED/NOT_RUN: ' + str(error), file=sys.stderr)
        return 2
    try:
        return run(manifest, sources, raw, args.test or list(manifest['tests']))
    except (OSError, subprocess.TimeoutExpired) as error:
        print('FAILED: historical child process: ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
