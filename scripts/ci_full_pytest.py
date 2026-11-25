"""Run every collected test in its declared context, then audit complete coverage."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import pwd
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.ci_pytest_context import CONTEXTS, NATIVE314_FILES, SNAPSHOT_FILE
from scripts.ci_lifecycle import mark


def retain_collection(name, collection):
    destination = os.environ.get('FC_NATIVE_DIAGNOSTICS_DIR')
    if destination:
        folder = Path(destination) / 'collections'
        folder.mkdir(parents=True, exist_ok=True)
        (folder / (name + '.json')).write_text(json.dumps(collection, sort_keys=True) + '\n')


def audit_coverage(expected, collections):
    for name in CONTEXTS:
        if collections[name] != expected[name]:
            missing = list((Counter(expected[name]) - Counter(collections[name])).elements())
            extra = list((Counter(collections[name]) - Counter(expected[name])).elements())
            print(json.dumps(dict(context=name, missing=missing[:128], extra=extra[:128],
                missing_count=len(missing), extra_count=len(extra),
                incomplete=len(missing) > 128 or len(extra) > 128)), flush=True)
            raise ValueError('Fixture collection changed between contexts: ' + name)


def emit_native_failures():
    directory = os.environ.get('FC_NATIVE_DIAGNOSTICS_DIR')
    if not directory:
        return
    paths = sorted(Path(directory).glob('fc-ha-maintenance-error-*.log'))
    for path in paths[:16]:
        with path.open('rb') as source:
            raw = source.read(4097)
        print('NATIVE_FIXTURE_DIAGNOSTIC ' + json.dumps(dict(file=path.name,
            stderr=raw[:4096].decode('utf-8', errors='replace'), incomplete=len(raw) > 4096)), flush=True)
    if len(paths) > 16:
        print('NATIVE_FIXTURE_DIAGNOSTIC_INCOMPLETE: FILE_LIMIT', flush=True)


@contextmanager
def workspace():
    temporary = tempfile.TemporaryDirectory(prefix='fc-test-contexts-')
    try:
        yield temporary.name
    finally:
        emit_native_failures()
        mark('cleanup_start')
        temporary.cleanup()
        mark('cleanup_end')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--python314', type=Path, required=True)
    parser.add_argument('--unprivileged-user')
    args = parser.parse_args()
    privileged = os.geteuid() == 0
    if privileged and not args.unprivileged_user:
        parser.error('An explicit unprivileged test account is required')
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUNBUFFERED='1')
    environment['PATH'] = str(Path(sys.executable).parent) + os.pathsep + environment['PATH']
    os.umask(0o022)
    with workspace() as temporary:
        folder = Path(temporary)
        if privileged:
            account = pwd.getpwnam(args.unprivileged_user)
            if account.pw_uid == 0:
                parser.error('Test account must not be root')
            os.chown(folder, account.pw_uid, account.pw_gid)
        def command(name, output):
            python = str(args.python314) if name in ('snapshot314', 'native314') else sys.executable
            prefix = []
            if privileged and name != 'root':
                prefix = ['runuser', '-u', args.unprivileged_user, '--']
            elif not privileged and name == 'root':
                preserved = [key for key in environment if key.startswith('FC_TEST_')]
                preserved += ['PATH', 'PYTHONDONTWRITEBYTECODE', 'PYTHONUNBUFFERED', 'FC_CI_LIFECYCLE_LOG']
                prefix = ['sudo', '--preserve-env=' + ','.join(preserved)]
            if name == 'root':
                return prefix + [python, str(ROOT / 'scripts/ci_root_pytest.py'), '--collection', str(output)]
            selection = [SNAPSHOT_FILE] if name == 'snapshot314' else []
            if name == 'native314':
                selection = sorted(NATIVE314_FILES)
            return prefix + [python, '-m', 'pytest', '-p', 'scripts.ci_pytest_context',
                '--fixture-context=' + name, '--fixture-collection=' + str(output),
                '-o', 'faulthandler_timeout=180', '-q', '--tb=short', *selection]
        inventory = folder / 'inventory.json'
        mark('inventory_start')
        result = subprocess.run(command('inventory', inventory) + ['--collect-only'], cwd=ROOT,
                                env=environment, timeout=180)
        mark('inventory_end', returncode=result.returncode)
        result.check_returncode()
        expected = json.loads(inventory.read_text())
        retain_collection('inventory', expected)
        if set(expected) != set(CONTEXTS) or not all(expected.values()):
            raise ValueError('Incomplete fixture context inventory')
        failures = []
        collections = {}
        for name in CONTEXTS:
            print('FULL-SUITE CONTEXT: ' + name, flush=True)
            output = folder / (name + '.json')
            mark('context_start', context=name)
            result = subprocess.run(command(name, output), cwd=ROOT, env=environment)
            mark('context_end', context=name, returncode=result.returncode)
            actual = json.loads(output.read_text())
            retain_collection(name, actual)
            collections[name] = actual[name]
            print(json.dumps(dict(context=name, tests=len(actual[name]), returncode=result.returncode,
                collection_sha256=hashlib.sha256(json.dumps(actual[name]).encode()).hexdigest())), flush=True)
            if result.returncode:
                failures.append(name)
        mark('coverage_start')
        audit_coverage(expected, collections)
        if failures:
            raise SystemExit('Failed fixture contexts: ' + ', '.join(failures))
        print('Full-suite context coverage: PASS', flush=True)
        mark('coverage_end')
    mark('launcher_end')


if __name__ == '__main__':
    main()
