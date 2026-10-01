"""Closed Friends HTTP artifact, including ordinary routes; no runtime state."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipapp
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = Path('deploy/friends/restricted')
ARCHIVE = 'friends-http.pyz'


def build(output, source=ROOT):
    paths = json.loads((source / CONTRACT / 'http-runtime-files.json').read_text())
    if not paths or len(paths) != len(set(paths)):
        raise ValueError('Invalid HTTP manifest')
    if any(Path(name).is_absolute() or '..' in Path(name).parts or Path(name).suffix != '.py' for name in paths):
        raise ValueError('Unsafe HTTP manifest')
    inputs = {'app/' + name: name for name in paths}
    inputs['app/friends_http.py'] = 'deploy/friends/access-api.py'
    inputs.update({name: str(CONTRACT / name) for name in ('http-runtime.conf', 'http-runtime-files.json', 'access.conf', 'nginx-location.conf')})
    inputs.update({'control.lock': 'control/requirements.lock', 'identity.lock': 'device_identity/requirements.lock',
                   'friends-http-acceptance.py': 'scripts/friends_http_acceptance.py'})
    for name in inputs.values():
        path = source / name
        if not path.is_file() or any(parent.is_symlink() for parent in (path, *path.parents)):
            raise ValueError('Missing or unsafe HTTP runtime source: ' + name)
    output.mkdir(parents=True, exist_ok=False)
    for destination, name in inputs.items():
        path = output / destination
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / name, path)
    with io.BytesIO() as buffer:
        zipapp.create_archive(output / 'app', buffer, main='friends_http:main', compressed=True)
        with zipfile.ZipFile(buffer) as original, zipfile.ZipFile(output / ARCHIVE, 'w') as archive:
            for entry in sorted(original.infolist(), key=lambda entry: entry.filename):
                entry.date_time = (1980, 1, 1, 0, 0, 0)
                entry.create_system = 3
                entry.external_attr = (0o40755 if entry.is_dir() else 0o100644) << 16
                archive.writestr(entry, original.read(entry))
    report = {name: hashlib.sha256((output / name).read_bytes()).hexdigest() for name in [*inputs, ARCHIVE]}
    (output / 'sha256.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--python', type=Path, default=Path(sys.executable))
    args = parser.parse_args()
    report = build(args.output)
    subprocess.run([str(args.python), '-I', str((args.output / ARCHIVE).resolve()), '--help'],
                   cwd=args.output.parent, capture_output=True, check=True, timeout=30)
    print(json.dumps({'artifact': str(args.output / ARCHIVE), 'sha256': report[ARCHIVE], 'isolated_import': 'PASS'}))


if __name__ == '__main__':
    main()
