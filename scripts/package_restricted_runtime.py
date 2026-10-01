"""Build the explicit source-only Friends sync runtime; never read runtime secrets."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipapp

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = Path('deploy/friends/restricted')
ARCHIVE = 'restricted-sync.pyz'
TEMPLATES = ('family-connect-restricted-sync.service', 'family-connect-restricted-sync.timer',
             'restricted-sync-command')


def build(output, source=ROOT):
    paths = json.loads((source / CONTRACT / 'runtime-files.json').read_text())
    if not paths or len(paths) != len(set(paths)):
        raise ValueError('Invalid runtime manifest')
    for name in paths:
        path = Path(name)
        if path.is_absolute() or '..' in path.parts or path.suffix != '.py':
            raise ValueError('Unsafe runtime manifest')
    inputs = {str(Path('app') / name): name for name in paths}
    inputs.update({name: str(CONTRACT / name) for name in TEMPLATES})
    inputs.update({'control.lock': 'control/requirements.lock',
                   'identity.lock': 'device_identity/requirements.lock',
                   'runtime-files.json': str(CONTRACT / 'runtime-files.json')})
    for name in inputs.values():
        path = source / name
        if not path.is_file() or any(parent.is_symlink() for parent in (path, *path.parents)):
            raise ValueError('Missing or unsafe runtime source: ' + name)
    output.mkdir(parents=True, exist_ok=False)
    for destination, name in inputs.items():
        path = output / destination
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / name, path)
    zipapp.create_archive(output / 'app', output / ARCHIVE,
                          main='control.friends.restricted_sync:main', compressed=True)
    report = {name: hashlib.sha256((output / name).read_bytes()).hexdigest()
              for name in [*inputs, ARCHIVE]}
    (output / 'sha256.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def smoke(output, python):
    for arguments in (['--help'], ['sync', '--help'], ['gateway', '--help']):
        subprocess.run([str(python), '-I', str((output / ARCHIVE).resolve()), *arguments],
                       cwd=output.parent, check=True, capture_output=True, timeout=30)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--python', type=Path, default=Path(sys.executable))
    args = parser.parse_args()
    report = build(args.output)
    smoke(args.output, args.python)
    print(json.dumps({'artifact': str(args.output / ARCHIVE), 'sha256': report[ARCHIVE],
                      'isolated_cli_imports': 'PASS'}))


if __name__ == '__main__':
    main()
