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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.ci_pytest_context import CONTEXTS, ROOT_CLASS, ROOT_FILES, SNAPSHOT_FILE


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--python314', type=Path, required=True)
    parser.add_argument('--unprivileged-user')
    args = parser.parse_args()
    privileged = os.geteuid() == 0
    if privileged and not args.unprivileged_user:
        parser.error('An explicit unprivileged test account is required')
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUNBUFFERED='1')
    os.umask(0o022)
    with tempfile.TemporaryDirectory(prefix='fc-test-contexts-') as temporary:
        folder = Path(temporary)
        if privileged:
            account = pwd.getpwnam(args.unprivileged_user)
            if account.pw_uid == 0:
                parser.error('Test account must not be root')
            os.chown(folder, account.pw_uid, account.pw_gid)
        def command(name, output):
            python = str(args.python314) if name == 'snapshot314' else sys.executable
            prefix = []
            if privileged and name != 'root':
                prefix = ['runuser', '-u', args.unprivileged_user, '--']
            elif not privileged and name == 'root':
                preserved = [key for key in environment if key.startswith('FC_TEST_')]
                preserved += ['PATH', 'PYTHONDONTWRITEBYTECODE', 'PYTHONUNBUFFERED']
                prefix = ['sudo', '--preserve-env=' + ','.join(preserved)]
            selection = sorted(ROOT_FILES) + [ROOT_CLASS.removesuffix('::')] if name == 'root' else (
                [SNAPSHOT_FILE] if name == 'snapshot314' else [])
            return prefix + [python, '-m', 'pytest', '-p', 'scripts.ci_pytest_context',
                '--fixture-context=' + name, '--fixture-collection=' + str(output),
                '-o', 'faulthandler_timeout=180', '-q', '--tb=short', *selection]
        inventory = folder / 'inventory.json'
        subprocess.run(command('inventory', inventory) + ['--collect-only'], cwd=ROOT,
                       env=environment, stdout=subprocess.DEVNULL, check=True, timeout=180)
        expected = json.loads(inventory.read_text())
        if set(expected) != set(CONTEXTS) or not all(expected.values()):
            raise ValueError('Incomplete fixture context inventory')
        failures = []
        for name in CONTEXTS:
            print('FULL-SUITE CONTEXT: ' + name, flush=True)
            output = folder / (name + '.json')
            result = subprocess.run(command(name, output), cwd=ROOT, env=environment)
            actual = json.loads(output.read_text())
            if actual[name] != expected[name]:
                raise ValueError('Fixture collection changed between contexts: ' + name)
            print(json.dumps(dict(context=name, tests=len(actual[name]), returncode=result.returncode,
                collection_sha256=hashlib.sha256(json.dumps(actual[name]).encode()).hexdigest())), flush=True)
            if result.returncode:
                failures.append(name)
        if failures:
            raise SystemExit('Failed fixture contexts: ' + ', '.join(failures))
        print('Full-suite context coverage: PASS', flush=True)


if __name__ == '__main__':
    main()
