import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument('--retained', required=True, type=Path)
parser.add_argument('--out', required=True, type=Path)
args = parser.parse_args()
root = Path(__file__).resolve().parent
identity = json.loads((root/'base-identity.json').read_text())
inventory = json.loads((root/'source-manifest.json').read_text())
for row in inventory['files']:
    if row['before_sha256']:
        assert hashlib.sha256((args.retained/row['path']).read_bytes()).hexdigest() == row['before_sha256'], row['path']
for path, digest in identity['files'].items():
    assert hashlib.sha256((args.retained/path).read_bytes()).hexdigest() == digest, path
args.out.mkdir(parents=True, exist_ok=False)
with tempfile.TemporaryDirectory() as directory:
    archive = Path(directory)/'source.tar'
    subprocess.run(['git', '-C', str(args.retained), 'archive', '--format=tar', '-o', str(archive), identity['base']], check=True)
    with tarfile.open(archive) as bundle:
        bundle.extractall(args.out, filter='data')
for path in identity['files']:
    target = args.out/path
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(args.retained/path, target)
for row in inventory['files']:
    target = args.out/row['path']
    target.parent.mkdir(parents=True, exist_ok=True)
    raw = (root/'changed'/row['path']).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == row['after_sha256'], row['path']
    target.write_bytes(raw)
print('Isolated research84 derivative written; no build, runtime, or release action')
