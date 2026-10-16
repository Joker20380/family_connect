import argparse
import hashlib
import json
from pathlib import Path
import shutil

parser = argparse.ArgumentParser()
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parent
manifest = json.loads((root/'source-manifest.json').read_text())
inventory = json.loads((root.parent/'mixed-peer-burst-20261015/results/cumulative-source.json').read_text())
assert inventory['source_delta_sha256'] == manifest['input_cumulative']
for name, expected in inventory['files'].items():
    if hashlib.sha256((args.source/name).read_bytes()).hexdigest() != expected:
        raise SystemExit('Retained cumulative input mismatch: '+name)
for name, item in manifest['files'].items():
    before = args.source/name
    actual = hashlib.sha256(before.read_bytes()).hexdigest() if before.is_file() else None
    if actual != item['before']:
        raise SystemExit('Not retained C_NEW: '+name)
    if hashlib.sha256((root/'changed'/name).read_bytes()).hexdigest() != item['after']:
        raise SystemExit('Corrupt delta: '+name)
shutil.copytree(args.source, args.out, ignore=shutil.ignore_patterns('.git'))
for name in manifest['files']:
    target = args.out/name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(root/'changed'/name, target)
print('Applied verified diagnostic delta; no build, signing, device or server operation')
