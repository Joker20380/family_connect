import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--retained', type=Path, required=True)
parser.add_argument('--out', type=Path, required=True)
parser.add_argument('--before', action='store_true')
args = parser.parse_args()
root = Path(__file__).resolve().parent
manifest = json.loads((root / 'source-manifest.json').read_text())
subprocess.run([sys.executable, str(root.parent / 'startup-cause-fidelity-20261015/apply.py'), '--retained', str(args.retained.resolve()), '--out', str(args.out.resolve())], check=True)
for name, expected in manifest['base_files'].items():
    assert hashlib.sha256((args.out / name).read_bytes()).hexdigest() == expected, name
assert hashlib.sha256((root / 'source.patch').read_bytes()).hexdigest() == manifest['patch_sha256']
for item in manifest['files']:
    target = args.out / item['path']
    if item['before_sha256']:
        assert hashlib.sha256(target.read_bytes()).hexdigest() == item['before_sha256'], item['path']
    else:
        assert not target.exists(), item['path']
    raw = (root / 'changed' / item['path']).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == item['after_sha256'], item['path']
    if args.before and item['scope'] == 'product':
        continue
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
print('Exact cumulative derivative materialized; before product preserved' if args.before else 'Exact cumulative derivative plus bounded writer correction materialized')
